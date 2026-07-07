from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_db
from app.core.security import SecurityService
from app.models import User
from app.repositories import UserRepository

SUPER_ADMIN_PHONE = "18610137321"


async def get_current_user(
    authorization: Optional[str] = Header(None),
    session: AsyncSession = Depends(get_db),
):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")

    payload = SecurityService.decode_token(parts[1])
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user_id = payload.get("uid")
    subject = payload.get("sub")
    if not user_id and not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = None
    if user_id:
        try:
            user = await UserRepository.get_user_by_id(session, int(user_id))
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    elif subject and not str(subject).startswith("wechat:"):
        user = await UserRepository.get_user_by_phone(session, subject)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Login expired or user not found")
    if getattr(user, "is_disabled", False):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="该账号已被禁用，请等待管理员审核")

    return user


def is_admin_user(user: User) -> bool:
    return bool(getattr(user, "is_admin", False))


def is_super_admin_user(user: User) -> bool:
    return getattr(user, "phone", None) == SUPER_ADMIN_PHONE


def can_manage_user_content(user: User, owner_id: int | None) -> bool:
    return is_admin_user(user) or owner_id == user.id


def can_post_content(user: User) -> bool:
    return not getattr(user, "is_disabled", False) and bool(getattr(user, "can_post", True))


async def require_admin_user(user: User = Depends(get_current_user)) -> User:
    if not is_admin_user(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user


async def require_can_post_user(user: User = Depends(get_current_user)) -> User:
    if not can_post_content(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="该账号已被禁言，请等待管理员审核")
    return user
