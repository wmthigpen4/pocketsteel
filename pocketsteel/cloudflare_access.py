"""Cloudflare Access JWT validation for the application API."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse
from urllib.request import urlopen

import jwt


CLOUDFLARE_ACCESS_JWT_HEADER = "Cf-Access-Jwt-Assertion"
CLOUDFLARE_ACCESS_JWT_ENVIRON = "HTTP_CF_ACCESS_JWT_ASSERTION"
CLOUDFLARE_ACCESS_AUTHORIZATION_COOKIE = "CF_Authorization"
CLOUDFLARE_ACCESS_ISSUER_ENV = "STEEL_RAG_CF_ACCESS_ISSUER"
CLOUDFLARE_ACCESS_AUD_ENV = "STEEL_RAG_CF_ACCESS_AUD"
CLOUDFLARE_ACCESS_JWKS_URL_ENV = "STEEL_RAG_CF_ACCESS_JWKS_URL"
BETA_USER_EMAILS_ENV = "STEEL_RAG_BETA_USER_EMAILS"
ADMIN_EMAILS_ENV = "STEEL_RAG_ADMIN_EMAILS"

DEFAULT_JWKS_TTL_SECONDS = 300
MAX_JWKS_BYTES = 1_048_576
MAX_JWKS_KEYS = 32


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


def _normalize_audience(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, list):
        return tuple(str(item) for item in value)
    return ()


class CloudflareAccessJwtVerifier:
    """Verify Access JWTs with a fixed RS256 allow-list and bounded JWKS cache."""

    def __init__(
        self,
        *,
        jwks: dict[str, Any] | None = None,
        http_timeout_seconds: float = 5.0,
        jwks_ttl_seconds: int = DEFAULT_JWKS_TTL_SECONDS,
        now_func: Any = time.monotonic,
        jwks_loader: Any = None,
    ) -> None:
        self._jwks = self._validate_jwks(jwks) if jwks is not None else None
        self._jwks_loaded_at = float(now_func()) if jwks is not None else 0.0
        self._static_jwks = jwks is not None and jwks_loader is None
        self.http_timeout_seconds = max(0.25, min(float(http_timeout_seconds), 15.0))
        self.jwks_ttl_seconds = max(30, min(int(jwks_ttl_seconds), 3600))
        self.now_func = now_func
        self.jwks_loader = jwks_loader
        self._jwks_lock = threading.Lock()

    def validate(self, token: str, config: CloudflareAccessConfig) -> CloudflareAccessClaims:
        if not token:
            raise CloudflareAccessError("missing access jwt")
        if not config.issuer or not config.audience:
            raise CloudflareAccessError("cloudflare access issuer and audience are required")
        issuer_url = urlparse(config.issuer)
        if issuer_url.scheme != "https" or not issuer_url.netloc:
            raise CloudflareAccessError("cloudflare access issuer must be an https url")

        try:
            header = jwt.get_unverified_header(token)
        except jwt.PyJWTError as exc:
            raise CloudflareAccessError("invalid access jwt") from exc
        if header.get("alg") != "RS256":
            raise CloudflareAccessError("unsupported access jwt algorithm")
        if not str(header.get("kid") or "").strip():
            raise CloudflareAccessError("access jwt signing key id is required")

        jwk = self._find_jwk(header, config)
        try:
            signing_key = jwt.PyJWK.from_dict(jwk, algorithm="RS256")
            payload = jwt.decode(
                token,
                key=signing_key,
                algorithms=["RS256"],
                audience=config.audience,
                issuer=config.issuer.rstrip("/"),
                leeway=5,
                options={"require": ["exp", "iss", "aud"]},
            )
        except jwt.ExpiredSignatureError as exc:
            raise CloudflareAccessError("expired access jwt") from exc
        except jwt.ImmatureSignatureError as exc:
            raise CloudflareAccessError("access jwt not yet valid") from exc
        except (jwt.PyJWTError, TypeError, ValueError) as exc:
            raise CloudflareAccessError("invalid access jwt") from exc

        issuer = str(payload.get("iss") or "").rstrip("/")
        audience = _normalize_audience(payload.get("aud"))
        email = str(payload.get("email") or payload.get("identity_email") or "").strip().lower()
        if not email:
            raise CloudflareAccessError("access jwt missing email")
        return CloudflareAccessClaims(email=email, issuer=issuer, audience=audience, raw=payload)

    def _find_jwk(self, header: dict[str, Any], config: CloudflareAccessConfig) -> dict[str, Any]:
        kid = str(header.get("kid") or "")
        for force_refresh in (False, True):
            jwks = self._get_jwks(config.jwks_url, force_refresh=force_refresh)
            for key in jwks["keys"]:
                if key.get("kid") != kid:
                    continue
                if key.get("kty") == "RSA" and key.get("n") and key.get("e"):
                    return key
            if self._static_jwks:
                break
        raise CloudflareAccessError("access jwt signing key not found")

    def _get_jwks(self, jwks_url: str, *, force_refresh: bool) -> dict[str, Any]:
        now = float(self.now_func())
        with self._jwks_lock:
            cache_fresh = (
                self._jwks is not None
                and (self._static_jwks or now - self._jwks_loaded_at < self.jwks_ttl_seconds)
            )
            if cache_fresh and not force_refresh:
                return self._jwks
            if self._static_jwks:
                return self._jwks or {"keys": []}
            payload = self._load_jwks(jwks_url)
            self._jwks = self._validate_jwks(payload)
            self._jwks_loaded_at = now
            return self._jwks

    def _load_jwks(self, jwks_url: str) -> dict[str, Any]:
        if not jwks_url:
            raise CloudflareAccessError("cloudflare access jwks url is required")
        parsed_url = urlparse(jwks_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise CloudflareAccessError("cloudflare access jwks url must use http or https")
        if self.jwks_loader is not None:
            try:
                return self.jwks_loader(jwks_url, self.http_timeout_seconds)
            except CloudflareAccessError:
                raise
            except Exception as exc:
                raise CloudflareAccessError("could not load access jwks") from exc
        try:
            with urlopen(jwks_url, timeout=self.http_timeout_seconds) as response:
                raw_payload = response.read(MAX_JWKS_BYTES + 1)
                if len(raw_payload) > MAX_JWKS_BYTES:
                    raise CloudflareAccessError("access jwks is too large")
                payload = json.loads(raw_payload.decode("utf-8"))
        except CloudflareAccessError:
            raise
        except (OSError, ValueError, UnicodeDecodeError) as exc:
            raise CloudflareAccessError("could not load access jwks") from exc
        return payload

    @staticmethod
    def _validate_jwks(payload: Any) -> dict[str, Any]:
        if not isinstance(payload, dict) or not isinstance(payload.get("keys"), list):
            raise CloudflareAccessError("invalid access jwks")
        keys = payload["keys"]
        if not keys or len(keys) > MAX_JWKS_KEYS or not all(isinstance(key, dict) for key in keys):
            raise CloudflareAccessError("invalid access jwks")
        return payload
