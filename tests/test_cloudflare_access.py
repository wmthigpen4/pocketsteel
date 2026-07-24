from __future__ import annotations

import base64
import time
from typing import Any

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from steel_guitar_rag.cloudflare_access import (
    CloudflareAccessConfig,
    CloudflareAccessError,
    CloudflareAccessJwtVerifier,
)


ISSUER = "https://steel.cloudflareaccess.com"
AUDIENCE = "access-audience"


def _base64url_uint(value: int) -> str:
    raw = value.to_bytes((value.bit_length() + 7) // 8, "big")
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _keypair(kid: str) -> tuple[Any, dict[str, str]]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    numbers = private_key.public_key().public_numbers()
    return private_key, {
        "kid": kid,
        "kty": "RSA",
        "alg": "RS256",
        "use": "sig",
        "n": _base64url_uint(numbers.n),
        "e": _base64url_uint(numbers.e),
    }


def _config() -> CloudflareAccessConfig:
    return CloudflareAccessConfig(
        issuer=ISSUER,
        audience=AUDIENCE,
        beta_user_emails=frozenset({"beta@example.test"}),
        admin_emails=frozenset(),
        jwks_url="https://steel.cloudflareaccess.com/cdn-cgi/access/certs",
    )


def _token(private_key: Any, kid: str, **overrides: Any) -> str:
    payload = {
        "iss": ISSUER,
        "aud": [AUDIENCE],
        "email": "Beta@Example.Test",
        "sub": "access-user-123",
        "iat": int(time.time()) - 5,
        "exp": int(time.time()) + 300,
        **overrides,
    }
    return jwt.encode(payload, private_key, algorithm="RS256", headers={"kid": kid})


def test_access_verifier_validates_signature_issuer_audience_expiry_and_email() -> None:
    private_key, public_jwk = _keypair("current")
    verifier = CloudflareAccessJwtVerifier(jwks={"keys": [public_jwk]})

    claims = verifier.validate(_token(private_key, "current"), _config())

    assert claims.email == "beta@example.test"
    assert claims.issuer == ISSUER
    assert claims.audience == (AUDIENCE,)
    assert claims.subject == "access-user-123"


@pytest.mark.parametrize(
    ("overrides", "expected_error"),
    [
        ({"iss": "https://attacker.example"}, "invalid access jwt issuer"),
        ({"aud": ["wrong-audience"]}, "invalid access jwt audience"),
        ({"exp": int(time.time()) - 30}, "expired access jwt"),
        ({"exp": None}, "access jwt missing required claim"),
        ({"sub": ""}, "access jwt missing subject"),
    ],
)
def test_access_verifier_rejects_invalid_required_claims(
    overrides: dict[str, Any], expected_error: str
) -> None:
    private_key, public_jwk = _keypair("current")
    token = _token(private_key, "current", **overrides)
    verifier = CloudflareAccessJwtVerifier(jwks={"keys": [public_jwk]})

    with pytest.raises(CloudflareAccessError, match=expected_error):
        verifier.validate(token, _config())


def test_access_verifier_refreshes_jwks_once_for_rotated_key_and_then_caches() -> None:
    _old_private, old_public = _keypair("old")
    new_private, new_public = _keypair("new")
    responses = [{"keys": [old_public]}, {"keys": [new_public]}]
    calls: list[str] = []

    def load_jwks(url: str, timeout: float) -> dict[str, Any]:
        calls.append(f"{url}:{timeout}")
        return responses[min(len(calls) - 1, len(responses) - 1)]

    verifier = CloudflareAccessJwtVerifier(jwks_loader=load_jwks, jwks_ttl_seconds=300)
    token = _token(new_private, "new")

    assert verifier.validate(token, _config()).email == "beta@example.test"
    assert verifier.validate(token, _config()).email == "beta@example.test"
    assert len(calls) == 2


def test_access_verifier_accepts_cloudflare_issuer_with_trailing_slash() -> None:
    private_key, public_jwk = _keypair("current")
    verifier = CloudflareAccessJwtVerifier(jwks={"keys": [public_jwk]})

    claims = verifier.validate(_token(private_key, "current", iss=f"{ISSUER}/"), _config())

    assert claims.issuer == ISSUER


def test_access_verifier_rejects_algorithm_outside_fixed_rs256_allowlist() -> None:
    _private_key, public_jwk = _keypair("current")
    token = jwt.encode(
        {"iss": ISSUER, "aud": AUDIENCE, "email": "beta@example.test", "exp": int(time.time()) + 60},
        "not-an-rsa-key-but-long-enough-for-hs256",
        algorithm="HS256",
        headers={"kid": "current"},
    )

    with pytest.raises(CloudflareAccessError, match="unsupported access jwt algorithm"):
        CloudflareAccessJwtVerifier(jwks={"keys": [public_jwk]}).validate(token, _config())


def test_access_verifier_rejects_non_http_jwks_location() -> None:
    private_key, _public_jwk = _keypair("current")
    config = CloudflareAccessConfig(
        issuer=ISSUER,
        audience=AUDIENCE,
        beta_user_emails=frozenset(),
        admin_emails=frozenset(),
        jwks_url="file:///tmp/access-jwks.json",
    )

    with pytest.raises(CloudflareAccessError, match="must use http or https"):
        CloudflareAccessJwtVerifier().validate(_token(private_key, "current"), config)
