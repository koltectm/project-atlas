"""
app/dependencies.py
===================
Shared FastAPI dependency functions injected via Depends().

Pattern:
    All route handlers receive typed dependencies (session, current_user, repos)
    via FastAPI's dependency injection. No global state or service locator.
"""

from __future__ import annotations

import uuid
from typing import Annotated

import structlog
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientRoleError
from app.core.security import decode_access_token, extract_token_from_header
from app.db.connection import get_db
from app.db.models import UserRoleEnum
from app.db.repositories.node_repo import NodeRepository
from app.db.repositories.link_repo import LinkRepository
from app.db.repositories.scenario_repo import ScenarioRepository
from app.db.repositories.simulation_repo import SimulationRepository
from app.db.repositories.result_repo import ResultRepository

logger = structlog.get_logger(__name__)

# ─── Type aliases for injection ───────────────────────────────────────────────
DbSession = Annotated[AsyncSession, Depends(get_db)]


# ─── Auth dependencies ────────────────────────────────────────────────────────

async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict:
    """
    Decode the Bearer JWT and return the token payload.

    Returns dict with keys: sub (user_id str), role (str), exp, jti.
    Raises AuthenticationError / TokenExpiredError / InvalidTokenError.
    """
    token = extract_token_from_header(authorization)
    payload = decode_access_token(token)
    logger.debug("auth.token_validated", user_id=payload.get("sub"))
    return payload


CurrentUser = Annotated[dict, Depends(get_current_user)]


def require_role(*roles: UserRoleEnum):
    """
    Factory for role-checking dependencies.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(
            _: None = Depends(require_role(UserRoleEnum.admin))
        ): ...
    """
    async def _check_role(user: CurrentUser) -> None:
        user_role = UserRoleEnum(user.get("role", "viewer"))
        if user_role not in roles:
            raise InsufficientRoleError(
                detail={
                    "required_roles": [r.value for r in roles],
                    "current_role":   user_role.value,
                }
            )
    return Depends(_check_role)


AdminRequired   = require_role(UserRoleEnum.admin)
AnalystRequired = require_role(UserRoleEnum.admin, UserRoleEnum.analyst)


def get_current_user_id(user: CurrentUser) -> uuid.UUID:
    """Extract the UUID from the current user's JWT payload."""
    return uuid.UUID(user["sub"])


CurrentUserId = Annotated[uuid.UUID, Depends(get_current_user_id)]


# ─── Repository dependencies ──────────────────────────────────────────────────

def get_node_repo(db: DbSession) -> NodeRepository:
    return NodeRepository(db)

def get_link_repo(db: DbSession) -> LinkRepository:
    return LinkRepository(db)

def get_scenario_repo(db: DbSession) -> ScenarioRepository:
    return ScenarioRepository(db)

def get_simulation_repo(db: DbSession) -> SimulationRepository:
    return SimulationRepository(db)

def get_result_repo(db: DbSession) -> ResultRepository:
    return ResultRepository(db)


NodeRepo       = Annotated[NodeRepository,       Depends(get_node_repo)]
LinkRepo       = Annotated[LinkRepository,       Depends(get_link_repo)]
ScenarioRepo   = Annotated[ScenarioRepository,   Depends(get_scenario_repo)]
SimulationRepo = Annotated[SimulationRepository, Depends(get_simulation_repo)]
ResultRepo     = Annotated[ResultRepository,     Depends(get_result_repo)]
