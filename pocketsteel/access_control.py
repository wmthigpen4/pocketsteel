"""Access-role scaffold for the Steel Guitar RAG private beta."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

AccessRole = Literal["anonymous", "beta_user", "admin"]
AnswerAuthMode = Literal["production", "local_dev"]

ANONYMOUS: AccessRole = "anonymous"
BETA_USER: AccessRole = "beta_user"
ADMIN: AccessRole = "admin"

ACCESS_ROLES: tuple[AccessRole, ...] = (ANONYMOUS, BETA_USER, ADMIN)
LIVE_ANSWER_ROLES: frozenset[AccessRole] = frozenset((BETA_USER, ADMIN))

PRODUCTION_AUTH_MODE: AnswerAuthMode = "production"
LOCAL_DEV_AUTH_MODE: AnswerAuthMode = "local_dev"
ANSWER_AUTH_MODES: tuple[AnswerAuthMode, ...] = (PRODUCTION_AUTH_MODE, LOCAL_DEV_AUTH_MODE)
ANSWER_AUTH_MODE_ENV = "STEEL_RAG_ANSWER_AUTH_MODE"

TRUSTED_AUTH_ROLE_HEADER = "X-Steel-Rag-Access-Role"
DEV_ACCESS_ROLE_HEADER = "X-Steel-Rag-Dev-Access-Role"
TRUSTED_AUTH_ROLE_ENVIRON = "HTTP_X_STEEL_RAG_ACCESS_ROLE"
DEV_ACCESS_ROLE_ENVIRON = "HTTP_X_STEEL_RAG_DEV_ACCESS_ROLE"


@dataclass(frozen=True)
class AnswerAccessDecision:
    allowed: bool
    role: AccessRole
    status: str = "200 OK"
    error: str = ""


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


def authorize_answer_request(environ: dict[str, object], auth_mode: object = None) -> AnswerAccessDecision:
    """Authorize POST /api/answer without depending on a real provider yet.

    Production mode reads only the trusted-auth placeholder header. Local-dev
    mode may also read the explicit dev mock header used by tests and local UI.
    """

    mode = normalize_answer_auth_mode(auth_mode or configured_answer_auth_mode())
    trusted_role_value = environ.get(TRUSTED_AUTH_ROLE_ENVIRON)
    dev_role_value = environ.get(DEV_ACCESS_ROLE_ENVIRON) if mode == LOCAL_DEV_AUTH_MODE else None
    raw_role = trusted_role_value or dev_role_value
    role = normalize_access_role(raw_role)
    if can_call_live_answer(role):
        return AnswerAccessDecision(allowed=True, role=role)
    if raw_role:
        return AnswerAccessDecision(
            allowed=False,
            role=role,
            status="403 Forbidden",
            error="/api/answer requires beta_user or admin access",
        )
    return AnswerAccessDecision(
        allowed=False,
        role=ANONYMOUS,
        status="401 Unauthorized",
        error="/api/answer requires authenticated beta_user or admin access",
    )
