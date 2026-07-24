"""Access-role scaffold for the Steel Guitar RAG private beta."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from dataclasses import field
from http.cookies import SimpleCookie
from typing import Any, Literal
from urllib.parse import parse_qs

from steel_guitar_rag.cloudflare_access import (
    CLOUDFLARE_ACCESS_AUTHORIZATION_COOKIE,
    CLOUDFLARE_ACCESS_JWT_ENVIRON,
    CloudflareAccessConfig,
    CloudflareAccessError,
    CloudflareAccessJwtVerifier,
)

AccessRole = Literal["anonymous", "beta_user", "admin"]
AnswerAuthMode = Literal["production", "local_dev"]
AuthProvider = Literal["scaffold", "cloudflare_access"]

ANONYMOUS: AccessRole = "anonymous"
BETA_USER: AccessRole = "beta_user"
ADMIN: AccessRole = "admin"

ACCESS_ROLES: tuple[AccessRole, ...] = (ANONYMOUS, BETA_USER, ADMIN)
LIVE_ANSWER_ROLES: frozenset[AccessRole] = frozenset((BETA_USER, ADMIN))

PRODUCTION_AUTH_MODE: AnswerAuthMode = "production"
LOCAL_DEV_AUTH_MODE: AnswerAuthMode = "local_dev"
ANSWER_AUTH_MODES: tuple[AnswerAuthMode, ...] = (PRODUCTION_AUTH_MODE, LOCAL_DEV_AUTH_MODE)
ANSWER_AUTH_MODE_ENV = "STEEL_RAG_ANSWER_AUTH_MODE"
AUTH_PROVIDER_ENV = "STEEL_RAG_AUTH_PROVIDER"
SCAFFOLD_AUTH_PROVIDER: AuthProvider = "scaffold"
CLOUDFLARE_ACCESS_AUTH_PROVIDER: AuthProvider = "cloudflare_access"
AUTH_PROVIDERS: tuple[AuthProvider, ...] = (SCAFFOLD_AUTH_PROVIDER, CLOUDFLARE_ACCESS_AUTH_PROVIDER)

TRUSTED_AUTH_ROLE_HEADER = "X-Steel-Rag-Access-Role"
DEV_ACCESS_ROLE_HEADER = "X-Steel-Rag-Dev-Access-Role"
TRUSTED_AUTH_ROLE_ENVIRON = "HTTP_X_STEEL_RAG_ACCESS_ROLE"
DEV_ACCESS_ROLE_ENVIRON = "HTTP_X_STEEL_RAG_DEV_ACCESS_ROLE"
LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class AnswerAccessDecision:
    allowed: bool
    role: AccessRole
    status: str = "200 OK"
    error: str = ""
    identity_email: str = ""
    identity_subject: str = ""
    identity_issuer: str = ""
    identity_provider: str = ""
    diagnostics: dict[str, object] = field(default_factory=dict)


class AuthConfigurationError(RuntimeError):
    """Raised when a production process is not configured to fail closed."""


def normalize_access_role(value: object) -> AccessRole:
    """Return a known access role, preserving old local mock labels."""

    text = str(value or "").strip().lower()
    if text == "member":
        return BETA_USER
    if text in ACCESS_ROLES:
        return text  # type: ignore[return-value]
    return ANONYMOUS


def can_call_live_answer(role: object) -> bool:
    """Whether this scaffold role may call the live answer endpoint."""

    return normalize_access_role(role) in LIVE_ANSWER_ROLES


def normalize_answer_auth_mode(value: object) -> AnswerAuthMode:
    text = str(value or "").strip().lower().replace("-", "_")
    if text in ANSWER_AUTH_MODES:
        return text  # type: ignore[return-value]
    return PRODUCTION_AUTH_MODE


def configured_answer_auth_mode() -> AnswerAuthMode:
    return normalize_answer_auth_mode(os.environ.get(ANSWER_AUTH_MODE_ENV))


def normalize_auth_provider(value: object) -> AuthProvider:
    text = str(value or "").strip().lower().replace("-", "_")
    if text in AUTH_PROVIDERS:
        return text  # type: ignore[return-value]
    return SCAFFOLD_AUTH_PROVIDER


def configured_auth_provider() -> AuthProvider:
    return normalize_auth_provider(os.environ.get(AUTH_PROVIDER_ENV))


def resolve_auth_provider(auth_mode: object, auth_provider: object = None) -> AuthProvider:
    """Resolve the provider while refusing scaffold identity in production.

    The scaffold provider and role headers are intentionally limited to an
    explicitly selected local-development process. Production must name the
    Cloudflare Access provider either in the constructor or environment.
    """

    mode = normalize_answer_auth_mode(auth_mode)
    raw_provider = auth_provider if auth_provider is not None else os.environ.get(AUTH_PROVIDER_ENV)
    if mode == PRODUCTION_AUTH_MODE:
        if not str(raw_provider or "").strip():
            raise AuthConfigurationError(
                f"{AUTH_PROVIDER_ENV}=cloudflare_access is required in production"
            )
        provider = normalize_auth_provider(raw_provider)
        if provider != CLOUDFLARE_ACCESS_AUTH_PROVIDER:
            raise AuthConfigurationError("production auth must use cloudflare_access")
        return provider
    return normalize_auth_provider(raw_provider or SCAFFOLD_AUTH_PROVIDER)


def _authorize_with_cloudflare_access(
    environ: dict[str, object],
    cloudflare_verifier: Any,
) -> AnswerAccessDecision:
    token, diagnostics = _access_jwt_from_environ(environ)
    if not token:
        return AnswerAccessDecision(
            allowed=False,
            role=ANONYMOUS,
            status="401 Unauthorized",
            error="request requires Cloudflare Access identity",
            diagnostics={
                **diagnostics,
                "accessIdentityVerified": False,
                "emailPresent": False,
                "emailAllowlisted": False,
                "betaAllowed": False,
            },
        )

    config = CloudflareAccessConfig.from_env()
    diagnostics = {
        **diagnostics,
        "accessIssuerConfigured": bool(config.issuer),
        "accessAudienceConfigured": bool(config.audience),
        "accessJwksConfigured": bool(config.jwks_url),
        "accessAllowlistConfigured": bool(config.beta_user_emails or config.admin_emails),
    }
    verifier = cloudflare_verifier or CloudflareAccessJwtVerifier()
    try:
        claims = verifier.validate(token, config)
    except CloudflareAccessError as exc:
        validation_error = {
            "expired access jwt": "expired",
            "access jwt not yet valid": "not_yet_valid",
            "invalid access jwt issuer": "issuer",
            "invalid access jwt audience": "audience",
            "access jwt missing required claim": "missing_claim",
            "access jwt missing subject": "missing_subject",
            "invalid access jwt signature": "signature",
            "access jwt signing key not found": "signing_key",
            "could not load access jwks": "jwks_load",
            "invalid access jwks": "jwks_format",
        }.get(str(exc), "token")
        LOGGER.warning("Cloudflare Access JWT validation failed: %s", validation_error)
        return AnswerAccessDecision(
            allowed=False,
            role=ANONYMOUS,
            status="401 Unauthorized",
            error="request requires valid Cloudflare Access identity",
            diagnostics={
                **diagnostics,
                "accessIdentityVerified": False,
                "accessValidationError": validation_error,
                "emailPresent": False,
                "emailAllowlisted": False,
                "betaAllowed": False,
            },
        )

    email = claims.email.strip().lower()
    subject = str(claims.subject or claims.raw.get("sub") or "").strip()
    if not subject:
        return AnswerAccessDecision(
            allowed=False,
            role=ANONYMOUS,
            status="401 Unauthorized",
            error="request requires valid Cloudflare Access identity",
            diagnostics={
                **diagnostics,
                "accessIdentityVerified": False,
                "accessValidationError": "missing_subject",
                "emailPresent": True,
                "emailAllowlisted": False,
                "betaAllowed": False,
            },
        )
    identity_fields = {
        "identity_email": email,
        "identity_subject": subject,
        "identity_issuer": claims.issuer,
        "identity_provider": CLOUDFLARE_ACCESS_AUTH_PROVIDER,
    }
    if email in config.admin_emails:
        return AnswerAccessDecision(
            allowed=True,
            role=ADMIN,
            **identity_fields,
            diagnostics={
                **diagnostics,
                "accessIdentityVerified": True,
                "emailPresent": True,
                "emailAllowlisted": True,
                "betaAllowed": True,
            },
        )
    if email in config.beta_user_emails:
        return AnswerAccessDecision(
            allowed=True,
            role=BETA_USER,
            **identity_fields,
            diagnostics={
                **diagnostics,
                "accessIdentityVerified": True,
                "emailPresent": True,
                "emailAllowlisted": True,
                "betaAllowed": True,
            },
        )
    return AnswerAccessDecision(
        allowed=False,
        role=ANONYMOUS,
        status="403 Forbidden",
        error="request requires beta_user or admin access",
        **identity_fields,
        diagnostics={
            **diagnostics,
            "accessIdentityVerified": True,
            "emailPresent": True,
            "emailAllowlisted": False,
            "betaAllowed": False,
        },
    )


def _access_jwt_from_environ(environ: dict[str, object]) -> tuple[str, dict[str, object]]:
    header_token = str(environ.get(CLOUDFLARE_ACCESS_JWT_ENVIRON) or "").strip()
    cookie_token = ""
    cookie_parse_error = False
    cookie_header = str(environ.get("HTTP_COOKIE") or "")
    if cookie_header:
        cookie = SimpleCookie()
        try:
            cookie.load(cookie_header)
            morsel = cookie.get(CLOUDFLARE_ACCESS_AUTHORIZATION_COOKIE)
            cookie_token = str(morsel.value).strip() if morsel else ""
        except Exception:
            cookie_parse_error = True
    diagnostics = {
        "accessHeaderPresent": bool(header_token),
        "accessCookiePresent": bool(cookie_token),
        "accessCookieParseError": cookie_parse_error,
        "accessTokenSource": "header" if header_token else "cookie" if cookie_token else "none",
    }
    if header_token:
        return header_token, diagnostics
    return cookie_token, diagnostics


def authorize_answer_request(
    environ: dict[str, object],
    auth_mode: object = None,
    auth_provider: object = None,
    cloudflare_verifier: Any = None,
) -> AnswerAccessDecision:
    """Authorize POST /api/answer without depending on a real provider yet.

    Local-dev mode may read the explicit dev mock header used by tests and local
    UI. In production mode, `cloudflare_access` derives roles only from a
    verified Access JWT and configured email allowlists.
    """

    mode = normalize_answer_auth_mode(auth_mode or configured_answer_auth_mode())
    resolve_auth_provider(mode, auth_provider)
    if mode == PRODUCTION_AUTH_MODE:
        return _authorize_with_cloudflare_access(environ, cloudflare_verifier)

    trusted_role_value = environ.get(TRUSTED_AUTH_ROLE_ENVIRON)
    dev_role_value = environ.get(DEV_ACCESS_ROLE_ENVIRON)
    raw_role = trusted_role_value or dev_role_value
    role = normalize_access_role(raw_role)
    if can_call_live_answer(role):
        return AnswerAccessDecision(
            allowed=True,
            role=role,
            identity_subject=f"local-dev:{role}",
            identity_issuer="local_dev",
            identity_provider="local_dev",
        )
    if raw_role:
        return AnswerAccessDecision(
            allowed=False,
            role=role,
            status="403 Forbidden",
            error="request requires beta_user or admin access",
        )
    return AnswerAccessDecision(
        allowed=False,
        role=ANONYMOUS,
        status="401 Unauthorized",
        error="request requires authenticated beta_user or admin access",
    )


def authorize_local_dev_request(
    environ: dict[str, object],
    auth_mode: object = None,
    auth_provider: object = None,
    cloudflare_verifier: Any = None,
) -> AnswerAccessDecision:
    """Authorize non-answer local-dev helpers without weakening production auth.

    This supports explicit smoke-test roles such as `?access=beta_user` for
    local `/api/session` and `/api/search` checks. Production Cloudflare Access
    mode still derives identity only from the verified Access JWT path and
    ignores query-string/mock dev roles.
    """

    mode = normalize_answer_auth_mode(auth_mode or configured_answer_auth_mode())
    resolve_auth_provider(mode, auth_provider)
    if mode == PRODUCTION_AUTH_MODE:
        return _authorize_with_cloudflare_access(environ, cloudflare_verifier)

    trusted_role_value = environ.get(TRUSTED_AUTH_ROLE_ENVIRON)
    dev_role_value = environ.get(DEV_ACCESS_ROLE_ENVIRON) if mode == LOCAL_DEV_AUTH_MODE else None
    query_role_value = None
    if mode == LOCAL_DEV_AUTH_MODE:
        query_params = parse_qs(str(environ.get("QUERY_STRING") or ""), keep_blank_values=True)
        query_role_value = (query_params.get("access") or [""])[0]

    raw_role = trusted_role_value or dev_role_value or query_role_value
    role = normalize_access_role(raw_role)
    if can_call_live_answer(role):
        return AnswerAccessDecision(
            allowed=True,
            role=role,
            identity_subject=f"local-dev:{role}",
            identity_issuer="local_dev",
            identity_provider="local_dev",
        )
    if raw_role:
        return AnswerAccessDecision(
            allowed=False,
            role=role,
            status="403 Forbidden",
            error="request requires beta_user or admin access",
        )
    return AnswerAccessDecision(
        allowed=False,
        role=ANONYMOUS,
        status="401 Unauthorized",
        error="request requires authenticated beta_user or admin access",
    )
