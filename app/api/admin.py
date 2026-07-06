from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_db
from app.core.deps import require_admin_user
from app.core.security import SecurityService
from app.models import CatchLog, Comment, FishingSpot, Post, User
from app.schemas import (
    AdminPasswordReset,
    AdminUserListResponse,
    AdminUserResponse,
    AdminUserUpdate,
)

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _user_response(row) -> AdminUserResponse:
    user, post_count, comment_count, spot_count, log_count = row
    return AdminUserResponse(
        id=user.id,
        nickname=user.nickname,
        avatar=user.avatar,
        phone=user.phone,
        wechat_openid=user.wechat_openid,
        wechat_unionid=user.wechat_unionid,
        is_admin=user.is_admin,
        is_disabled=user.is_disabled,
        can_post=user.can_post,
        created_at=user.created_at,
        post_count=post_count or 0,
        comment_count=comment_count or 0,
        spot_count=spot_count or 0,
        log_count=log_count or 0,
    )


async def _get_user_or_404(session: AsyncSession, user_id: int) -> User:
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    admin: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db),
):
    post_counts = (
        select(Post.user_id, func.count(Post.id).label("post_count"))
        .group_by(Post.user_id)
        .subquery()
    )
    comment_counts = (
        select(Comment.user_id, func.count(Comment.id).label("comment_count"))
        .group_by(Comment.user_id)
        .subquery()
    )
    spot_counts = (
        select(FishingSpot.user_id, func.count(FishingSpot.id).label("spot_count"))
        .where(FishingSpot.user_id.is_not(None))
        .group_by(FishingSpot.user_id)
        .subquery()
    )
    log_counts = (
        select(CatchLog.user_id, func.count(CatchLog.id).label("log_count"))
        .group_by(CatchLog.user_id)
        .subquery()
    )

    total_result = await session.execute(select(func.count(User.id)))
    result = await session.execute(
        select(
            User,
            func.coalesce(post_counts.c.post_count, 0),
            func.coalesce(comment_counts.c.comment_count, 0),
            func.coalesce(spot_counts.c.spot_count, 0),
            func.coalesce(log_counts.c.log_count, 0),
        )
        .outerjoin(post_counts, post_counts.c.user_id == User.id)
        .outerjoin(comment_counts, comment_counts.c.user_id == User.id)
        .outerjoin(spot_counts, spot_counts.c.user_id == User.id)
        .outerjoin(log_counts, log_counts.c.user_id == User.id)
        .order_by(User.created_at.desc(), User.id.desc())
    )

    return AdminUserListResponse(
        total=total_result.scalar_one(),
        users=[_user_response(row) for row in result.all()],
    )


@router.patch("/users/{user_id}", response_model=AdminUserResponse)
async def update_user_status(
    user_id: int,
    update: AdminUserUpdate,
    admin: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db),
):
    user = await _get_user_or_404(session, user_id)
    if user.id == admin.id:
        if update.is_disabled is True:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot disable your own account")
        if update.is_admin is False:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove your own admin role")

    if update.is_admin is not None:
        user.is_admin = update.is_admin
    if update.is_disabled is not None:
        user.is_disabled = update.is_disabled
    if update.can_post is not None:
        user.can_post = update.can_post

    await session.commit()
    await session.refresh(user)
    return AdminUserResponse(
        id=user.id,
        nickname=user.nickname,
        avatar=user.avatar,
        phone=user.phone,
        wechat_openid=user.wechat_openid,
        wechat_unionid=user.wechat_unionid,
        is_admin=user.is_admin,
        is_disabled=user.is_disabled,
        can_post=user.can_post,
        created_at=user.created_at,
    )


@router.post("/users/{user_id}/reset-password", response_model=AdminUserResponse)
async def reset_user_password(
    user_id: int,
    payload: AdminPasswordReset,
    admin: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db),
):
    user = await _get_user_or_404(session, user_id)
    user.password_hash = SecurityService.get_password_hash(payload.password)
    await session.commit()
    await session.refresh(user)
    return AdminUserResponse(
        id=user.id,
        nickname=user.nickname,
        avatar=user.avatar,
        phone=user.phone,
        wechat_openid=user.wechat_openid,
        wechat_unionid=user.wechat_unionid,
        is_admin=user.is_admin,
        is_disabled=user.is_disabled,
        can_post=user.can_post,
        created_at=user.created_at,
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db),
):
    if user_id == admin.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot delete your own account")

    user = await _get_user_or_404(session, user_id)
    user_spot_ids = select(FishingSpot.id).where(FishingSpot.user_id == user.id)
    user_post_ids = select(Post.id).where(Post.user_id == user.id)

    await session.execute(delete(Comment).where(Comment.post_id.in_(user_post_ids)))
    await session.execute(delete(Comment).where(Comment.user_id == user.id))
    await session.execute(delete(CatchLog).where(CatchLog.spot_id.in_(user_spot_ids)))
    await session.execute(delete(CatchLog).where(CatchLog.user_id == user.id))
    await session.execute(delete(Post).where(Post.user_id == user.id))
    await session.execute(delete(FishingSpot).where(FishingSpot.user_id == user.id))
    await session.delete(user)
    await session.commit()

    return {"message": "User deleted successfully"}
