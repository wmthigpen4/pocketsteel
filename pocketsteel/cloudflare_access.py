"""Cloudflare Access JWT validation for the Steel Guitar RAG API."""

from __future__ import annotations

import base64
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.request import urlopen


CLOUDFLARE_ACCESS_JWT_HEADER = "Cf-Access-Jwt-Assertion"
CLOUDFLARE_ACCESS_JWT_ENVIRON = "HTTP_CF_ACCESS_JWT_ASSERTION"
CLOUDFLARE_ACCESS_ISSUER_ENV = "STEEL_RAG_CF_ACCESS_ISSUER"
CLOUDFLARE_ACCESS_AUD_ENV = "STEEL_RAG_CF_ACCESS_AUD"
CLOUDFLARE_ACCESS_JWKS_URL_ENV = "STEEL_RAG_CF_ACCESS_JWKS_URL"
BETA_USER_EMAILS_ENV = "STEEL_RAG_BETA_USER_EMAILS"
ADMIN_EMAILS_ENV = "STEEL_RAG_ADMIN_EMAILS"

_SHA256_DIGESTINFO_PREFIX = bytes.fromhex("3031300d060960864801650304020105000420")


class CloudflareAccessError(ValueError):
    pass


@dataclass(frozen=True)
class CloudflareAccessConfig:
    issuer: str
    audience: str
    beta_user_emails: frozenset[str]
    admin_emails: frozenset[str]
    jwks_url: str = ""

    @classmethod
    def from_env(cls, environ: dict[str, Any] | None = None) -> "CloudflareAccessConfig":
        import os

        source = environ if environ is not None else os.environ
        issuer = str(source.get(CLOUDFLARE_ACCESS_ISSUER_ENV) or "").strip().rstrip("/")
        audience = str(source.get(CLOUDFLARE_ACCESS_AUD_ENV) or "").strip()
        jwks_url = str(source.get(CLOUDFLARE_ACCESS_JWKS_URL_ENV) or "").strip()
        if not jwks_url and issuer:
            jwks_url = f"{issuer}/cdn-cgi/access/certs"
        return cls(
            issuer=issuer,
            audience=audience,
            beta_user_emails=parse_email_set(source.get(BETA_USER_EMAILS_ENV)),
            admin_emails=parse_email_set(source.get(ADMIN_EMAILS_ENV)),
            jwks_url=jwks_url,
        )


@dataclass(frozen=True)
class CloudflareAccessClaims:
    email: str
    issuer: str
    audience: tuple[str, ...]
    raw: dict[str, Any]


def parse_email_set(value: object) -> frozenset[str]:
    return frozenset(
        email.strip().lower()
        for email in str(value or "").replace("\n", ",").split(",")
        if email.strip()
    )


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def _load_json_segment(value: str) -> dict[str, Any]:
    try:
        payload = json.loads(_base64url_decode(value).decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise CloudflareAccessError("invalid jwt segment") from exc
    if not isinstance(payload, dict):
        raise CloudflareAccessError("invalid jwt segment")
    return payload


def _normalize_audience(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return ()


def _rsa_verify_rs256(signing_input: bytes, signature: bytes, jwk: dict[str, Any]) -> bool:
    try:
        n = int.from_bytes(_base64url_decode(str(jwk["n"])), "big")
        e = int.from_bytes(_base64url_decode(str(jwk["e"])), "big")
    except (KeyError, ValueError, TypeError):
        return False

    key_length = (n.bit_length() + 7) // 8
    if len(signature) != key_length:
        return False

    digest = hashlib.sha256(signing_input).digest()
    expected = _SHA256_DIGESTINFO_PREFIX + digest
    padding_length = key_length - len(expected) - 3
    if padding_length < 8:
        return False
    encoded_expected = b"\x00\x01" + (b"\xff" * padding_length) + b"\x00" + expected
    encoded_actual = pow(int.from_bytes(signature, "big"), e, n).to_bytes(key_length, "big")
    return encoded_actual == encoded_expected


class CloudflareAccessJwtVerifier:
    """Verify Cloudflare Access JWTs against Access JWKS with stdlib crypto.

    The verifier intentionally supports only RS256 JWTs with JWK `n`/`e`
    material. That matches the Access JWKS shape used by Cloudflare docs and
    keeps the origin-side validation dependency-free.
    """

    def __init__(
        self,
        *,
        jwks: dict[str, Any] | None = None,
        http_timeout_seconds: float = 5.0,
        now_func: Any = time.time,
    ) -> None:
        self._jwks = jwks
        self.http_timeout_seconds = http_timeout_seconds
        self.now_func = now_func

    def validate(self, token: str, config: CloudflareAccessConfig) -> CloudflareAccessClaims:
        if not token:
            raise CloudflareAccessError("missing access jwt")
        if not config.issuer or not config.audience:
            raise CloudflareAccessError("cloudflare access issuer and audience are required")

        parts = token.split(".")
        if len(parts) != 3:
            raise CloudflareAccessError("invalid access jwt")

        header = _load_json_segment(parts[0])
        payload = _load_json_segment(parts[1])
        if header.get("alg") != "RS256":
            raise CloudflareAccessError("unsupported access jwt algorithm")

        jwk = self._find_jwk(header, config)
        signing_input = f"{parts[0]}.{parts[1]}".encode("ascii")
        signature = _base64url_decode(parts[2])
        if not _rsa_verify_rs256(signing_input, signature, jwk):
            raise CloudflareAccessError("invalid access jwt signature")

        issuer = str(payload.get("iss") or "").rstrip("/")
        if issuer != config.issuer.rstrip("/"):
            raise CloudflareAccessError("invalid access jwt issuer")

        audience = _normalize_audience(payload.get("aud"))
        if config.audience not in audience:
            raise CloudflareAccessError("invalid access jwt audience")

        now = float(self.now_func())
        try:
            exp = payload.get("exp")
            if exp is not None and float(exp) < now:
                raise CloudflareAccessError("expired access jwt")
            nbf = payload.get("nbf")
            if nbf is not None and float(nbf) > now:
                raise CloudflareAccessError("access jwt not yet valid")
        except (TypeError, ValueError) as exc:
            raise CloudflareAccessError("invalid access jwt time claims") from exc

        email = str(payload.get("email") or payload.get("identity_email") or "").strip().lower()
        if not email:
            raise CloudflareAccessError("access jwt missing email")
        return CloudflareAccessClaims(email=email, issuer=issuer, audience=audience, raw=payload)

    def _find_jwk(self, header: dict[str, Any], config: CloudflareAccessConfig) -> dict[str, Any]:
        kid = str(header.get("kid") or "")
        jwks = self._jwks or self._fetch_jwks(config.jwks_url)
        keys = jwks.get("keys") if isinstance(jwks, dict) else None
        if not isinstance(keys, list):
            raise CloudflareAccessError("invalid access jwks")
        for key in keys:
            if not isinstance(key, dict):
                continue
            if kid and key.get("kid") != kid:
                continue
            if key.get("kty") == "RSA" and key.get("n") and key.get("e"):
                return key
        raise CloudflareAccessError("access jwt signing key not found")

    def _fetch_jwks(self, jwks_url: str) -> dict[str, Any]:
        if not jwks_url:
            raise CloudflareAccessError("cloudflare access jwks url is required")
        try:
            with urlopen(jwks_url, timeout=self.http_timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            raise CloudflareAccessError("could not load access jwks") from exc
        if not isinstance(payload, dict):
            raise CloudflareAccessError("invalid access jwks")
        self._jwks = payload
        return payload
