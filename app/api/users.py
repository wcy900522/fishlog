from __future__ import annotations

from datetime import datetime, time, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_db
from app.core.deps import (
    ROOT_ADMIN_NICKNAMES,
    ROOT_ADMIN_PHONES,
    SUPER_ADMIN_NICKNAMES,
    get_current_user,
    is_root_admin_user,
)
from app.core.nickname_validator import NicknameValidationError, NicknameValidator
from app.models import CatchLog, FishingSpot, Post, User, XPLog
from app.repositories import XPLogRepository
from app.schemas import LeaderboardUserResponse, UserLevelResponse, UserProfileUpdate, UserResponse, XPLogResponse
from app.services import BadgeService, LevelService


router = APIRouter(prefix="/api/users", tags=["users"])
ALLOWED_AVATAR_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_AVATAR_IMAGE_SIZE = 3 * 1024 * 1024


def _is_protected_nickname(nickname: str | None) -> bool:
    return bool(nickname and nickname in SUPER_ADMIN_NICKNAMES)


@router.get("/me/level", response_model=UserLevelResponse)
async def get_my_level(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    info = LevelService.get_level_info(user.xp, user.level)
    badges = await BadgeService.get_user_badges(session, user.id)
    return UserLevelResponse(
        level=info.level,
        title=info.title,
        xp=info.xp,
        current_level_xp=info.current_level_xp,
        next_level_xp=info.next_level_xp,
        xp_to_next=info.xp_to_next,
        progress_percent=info.progress_percent,
        badges=badges,
        benefits=LevelService.get_benefits(info.level),
    )


@router.get("/me/xp-logs", response_model=list[XPLogResponse])
async def get_my_xp_logs(
    skip: int = 0,
    limit: int = 20,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await XPLogRepository.get_logs_by_user(session, user.id, skip=skip, limit=min(limit, 100))


@router.patch("/me", response_model=UserResponse)
async def update_my_profile(
    profile: UserProfileUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    nickname = profile.nickname.strip()
    if not nickname:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="昵称不能为空")
    try:
        NicknameValidator.validate(nickname)
    except NicknameValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if _is_protected_nickname(nickname) and nickname != user.nickname:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该昵称为系统保留昵称")

    if (is_root_admin_user(user) or _is_protected_nickname(user.nickname)) and nickname != user.nickname:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="受保护管理账号不可修改昵称")

    user.nickname = nickname
    await session.commit()
    await session.refresh(user)
    return user


@router.post("/me/avatar", response_model=UserResponse)
async def upload_my_avatar(
    avatar: UploadFile = File(...),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    suffix = ALLOWED_AVATAR_IMAGE_TYPES.get(avatar.content_type or "")
    if not suffix:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PNG, and WebP images are supported",
        )

    content = await avatar.read()
    if len(content) > MAX_AVATAR_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Avatar image must be 3MB or smaller",
        )

    upload_dir = Path(__file__).resolve().parents[1] / "static" / "uploads" / "avatars"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{user.id}_{uuid4().hex}{suffix}"
    file_path = upload_dir / filename
    file_path.write_bytes(content)

    user.avatar = f"/static/uploads/avatars/{filename}"
    await session.commit()
    await session.refresh(user)
    return user


@router.get("/leaderboards")
async def get_leaderboards(session: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    today_start = datetime.combine(now.date(), time.min)
    month_start = datetime(now.year, now.month, 1)
    year_start = datetime(now.year, 1, 1)

    return {
        "today_active": await _xp_leaderboard(session, today_start, limit=5),
        "month_xp": await _xp_leaderboard(session, month_start, limit=5),
        "year_king": await _xp_leaderboard(session, year_start, limit=5),
        "catch_streak": await _catch_streak_leaderboard(session, limit=5),
        "tech_authors": await _technical_author_leaderboard(session, limit=5),
        "spot_contributors": await _spot_contributor_leaderboard(session, limit=5),
    }


async def _xp_leaderboard(session: AsyncSession, start_at: datetime, limit: int) -> list[LeaderboardUserResponse]:
    score_expr = func.coalesce(func.sum(XPLog.xp_delta), 0).label("score")
    result = await session.execute(
        select(User, score_expr)
        .join(XPLog, XPLog.user_id == User.id)
        .where(XPLog.created_at >= start_at, _public_user_condition())
        .group_by(User.id)
        .order_by(score_expr.desc(), User.xp.desc())
        .limit(limit)
    )
    return [_leaderboard_user(user, int(score or 0)) for user, score in result.all()]


async def _technical_author_leaderboard(session: AsyncSession, limit: int) -> list[LeaderboardUserResponse]:
    score_expr = func.count(Post.id).label("score")
    result = await session.execute(
        select(User, score_expr)
        .join(Post, Post.user_id == User.id)
        .where(Post.tag == "技术分享", _public_user_condition())
        .group_by(User.id)
        .order_by(score_expr.desc(), User.xp.desc())
        .limit(limit)
    )
    return [_leaderboard_user(user, int(score or 0)) for user, score in result.all()]


async def _spot_contributor_leaderboard(session: AsyncSession, limit: int) -> list[LeaderboardUserResponse]:
    score_expr = func.count(FishingSpot.id).label("score")
    result = await session.execute(
        select(User, score_expr)
        .join(FishingSpot, FishingSpot.user_id == User.id)
        .where(_public_user_condition())
        .group_by(User.id)
        .order_by(score_expr.desc(), User.xp.desc())
        .limit(limit)
    )
    return [_leaderboard_user(user, int(score or 0)) for user, score in result.all()]


async def _catch_streak_leaderboard(session: AsyncSession, limit: int) -> list[LeaderboardUserResponse]:
    since = datetime.utcnow() - timedelta(days=30)
    result = await session.execute(
        select(User, CatchLog.fishing_at)
        .join(CatchLog, CatchLog.user_id == User.id)
        .where(CatchLog.fishing_at >= since, _public_user_condition())
        .order_by(User.id, CatchLog.fishing_at.desc())
    )

    by_user: dict[int, tuple[User, set]] = {}
    for user, fishing_at in result.all():
        by_user.setdefault(user.id, (user, set()))[1].add(fishing_at.date())

    rows: list[tuple[User, int]] = []
    today = datetime.utcnow().date()
    for user, fishing_days in by_user.values():
        streak = 0
        cursor = today
        while cursor in fishing_days:
            streak += 1
            cursor -= timedelta(days=1)
        if streak:
            rows.append((user, streak))

    rows.sort(key=lambda item: (item[1], item[0].xp), reverse=True)
    return [_leaderboard_user(user, streak) for user, streak in rows[:limit]]


def _leaderboard_user(user: User, score: int) -> LeaderboardUserResponse:
    return LeaderboardUserResponse(
        user_id=user.id,
        nickname=user.nickname,
        level=user.level,
        title=user.title,
        xp=user.xp,
        score=score,
    )


def _public_user_condition():
    return ~((User.phone.in_(ROOT_ADMIN_PHONES)) | (User.nickname.in_(ROOT_ADMIN_NICKNAMES)))
