from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any

from app.services.level_service import LevelInfo, LevelService


class XPReason:
    CATCH_LOG = "catch_log"
    POST = "post"
    COMMENT = "comment"
    POST_LIKE = "post_like"
    COMMENT_LIKE = "comment_like"
    FEATURED_POST = "featured_post"
    STREAK = "catch_log_streak"


class TargetType:
    CATCH_LOG = "catch_log"
    POST = "post"
    COMMENT = "comment"


class ExperienceService:
    COMMENT_DAILY_LIMIT = 30
    LIKE_DAILY_LIMIT = 50
    POST_REWARDS = {
        "技术分享": 20,
        "装备评测": 20,
        "钓点攻略": 25,
    }

    @classmethod
    async def add_xp(
        cls,
        session: Any,
        user: Any,
        score: int,
        reason: str,
        target_type: str | None = None,
        target_id: int | None = None,
    ) -> LevelInfo:
        from app.models import XPLog

        xp_delta = max(0, int(score or 0))
        if xp_delta <= 0:
            return LevelService.get_level_info(
                xp=int(getattr(user, "xp", 0) or 0),
                current_level=int(getattr(user, "level", 1) or 1),
            )

        session.add(XPLog(
            user_id=user.id,
            xp_delta=xp_delta,
            reason=reason,
            target_type=target_type,
            target_id=target_id,
        ))
        user.xp = int(getattr(user, "xp", 0) or 0) + xp_delta
        info = LevelService.apply_level_to_user(user)
        await session.commit()
        await session.refresh(user)
        return info

    @classmethod
    async def award_catch_log(cls, session: Any, user: Any, catch_log: Any) -> None:
        if await cls._has_daily_catch_log_xp(session, user.id):
            return
        score = cls.calculate_catch_log_xp(catch_log)
        await cls.add_xp(session, user, score, XPReason.CATCH_LOG, TargetType.CATCH_LOG, catch_log.id)
        await cls.award_catch_log_streak(session, user, catch_log)

    @staticmethod
    def calculate_catch_log_xp(catch_log: Any) -> int:
        score = 20
        if getattr(catch_log, "image_count", 0):
            score += 5
        if ExperienceService._weather_collected(catch_log):
            score += 5
        if getattr(catch_log, "species", None):
            score += 5
        if getattr(catch_log, "quantity", None) is not None:
            score += 5
        return min(score, 40)

    @classmethod
    async def award_post(cls, session: Any, user: Any, post: Any) -> None:
        score = cls.calculate_post_xp(getattr(post, "tag", None))
        await cls.add_xp(session, user, score, XPReason.POST, TargetType.POST, post.id)

    @classmethod
    def calculate_post_xp(cls, tag: str | None) -> int:
        return cls.POST_REWARDS.get(tag or "", 15)

    @classmethod
    async def award_comment(cls, session: Any, user: Any, comment: Any) -> None:
        score = await cls._remaining_daily_score(
            session=session,
            user_id=user.id,
            reasons={XPReason.COMMENT},
            daily_limit=cls.COMMENT_DAILY_LIMIT,
            requested_score=3,
        )
        await cls.add_xp(session, user, score, XPReason.COMMENT, TargetType.COMMENT, comment.id)

    @classmethod
    async def award_post_like(cls, session: Any, owner: Any, post_id: int) -> None:
        score = await cls._remaining_daily_score(
            session=session,
            user_id=owner.id,
            reasons={XPReason.POST_LIKE, XPReason.COMMENT_LIKE},
            daily_limit=cls.LIKE_DAILY_LIMIT,
            requested_score=2,
        )
        await cls.add_xp(session, owner, score, XPReason.POST_LIKE, TargetType.POST, post_id)

    @classmethod
    async def award_comment_like(cls, session: Any, owner: Any, comment_id: int) -> None:
        score = await cls._remaining_daily_score(
            session=session,
            user_id=owner.id,
            reasons={XPReason.POST_LIKE, XPReason.COMMENT_LIKE},
            daily_limit=cls.LIKE_DAILY_LIMIT,
            requested_score=1,
        )
        await cls.add_xp(session, owner, score, XPReason.COMMENT_LIKE, TargetType.COMMENT, comment_id)

    @classmethod
    async def award_featured_post(cls, session: Any, owner: Any, post_id: int) -> None:
        await cls.add_xp(session, owner, 100, XPReason.FEATURED_POST, TargetType.POST, post_id)

    @classmethod
    async def award_catch_log_streak(cls, session: Any, user: Any, catch_log: Any) -> None:
        streak_days = await cls._calculate_catch_log_streak_days(session, user.id, catch_log)
        rewards = {3: 20, 7: 50, 30: 300}
        score = rewards.get(streak_days)
        if not score:
            return
        await cls.add_xp(session, user, score, XPReason.STREAK, TargetType.CATCH_LOG, catch_log.id)

    @classmethod
    async def _remaining_daily_score(
        cls,
        session: Any,
        user_id: int,
        reasons: set[str],
        daily_limit: int,
        requested_score: int,
        on_date: date | None = None,
    ) -> int:
        from sqlalchemy import func, select
        from app.models import XPLog

        day = on_date or datetime.utcnow().date()
        start = datetime.combine(day, time.min)
        end = start + timedelta(days=1)
        result = await session.execute(
            select(func.coalesce(func.sum(XPLog.xp_delta), 0))
            .where(
                XPLog.user_id == user_id,
                XPLog.reason.in_(reasons),
                XPLog.created_at >= start,
                XPLog.created_at < end,
            )
        )
        used = int(result.scalar() or 0)
        return max(0, min(requested_score, daily_limit - used))

    @classmethod
    async def _has_daily_catch_log_xp(cls, session: Any, user_id: int, on_date: date | None = None) -> bool:
        from sqlalchemy import select
        from app.models import XPLog

        day = on_date or datetime.utcnow().date()
        start = datetime.combine(day, time.min)
        end = start + timedelta(days=1)
        result = await session.execute(
            select(XPLog.id).where(
                XPLog.user_id == user_id,
                XPLog.reason == XPReason.CATCH_LOG,
                XPLog.created_at >= start,
                XPLog.created_at < end,
            )
        )
        return result.scalar_one_or_none() is not None

    @classmethod
    async def _calculate_catch_log_streak_days(cls, session: Any, user_id: int, catch_log: Any) -> int:
        from sqlalchemy import select
        from app.models import CatchLog

        current_day = getattr(catch_log, "fishing_at").date()
        earliest = current_day - timedelta(days=29)
        result = await session.execute(
            select(CatchLog.fishing_at)
            .where(
                CatchLog.user_id == user_id,
                CatchLog.fishing_at >= datetime.combine(earliest, time.min),
                CatchLog.fishing_at <= datetime.combine(current_day, time.max),
            )
        )
        fishing_days = {item.date() for item in result.scalars().all()}

        streak = 0
        cursor = current_day
        while cursor in fishing_days:
            streak += 1
            cursor -= timedelta(days=1)
        return streak

    @staticmethod
    def _weather_collected(catch_log: Any) -> bool:
        snapshot = getattr(catch_log, "weather_snapshot", None)
        if isinstance(snapshot, dict) and snapshot.get("error"):
            return False
        return any(
            getattr(catch_log, field, None) is not None
            for field in ("temperature", "pressure", "wind_speed")
        )
