from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException

from app.domain.enums import Role
from app.domain.models import Actor
from app.settings import AppSettings, get_settings


def get_actor(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    x_role: str | None = Header(default=None, alias="X-Role"),
    settings: AppSettings = Depends(get_settings),
) -> Actor:
    if not x_user_id:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")
    if x_user_id not in settings.allowed_operator_ids:
        raise HTTPException(status_code=401, detail="User is not allowed")
    try:
        role = Role(x_role or "")
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Invalid or missing role") from exc
    return Actor(user_id=x_user_id, role=role)


def require_roles(*allowed_roles: Role) -> Callable:
    def dependency(actor: Actor = Depends(get_actor)) -> Actor:
        if actor.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Role is not authorized")
        return actor

    return dependency

