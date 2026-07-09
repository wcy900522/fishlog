from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BadgeRule:
    code: str
    name: str
    icon: str
    description: str


class BadgeService:
    BADGE_RULES: tuple[BadgeRule, ...] = (
        BadgeRule("first_catch_log", "第一条鱼", "🎣", "首次记录出钓"),
        BadgeRule("hundred_trips", "百次出钓", "🏕️", "累计100次出钓"),
        BadgeRule("thousand_fish", "千尾渔获", "🐟", "累计记录1000尾鱼"),
        BadgeRule("sea_master", "海钓达人", "🌊", "海钓50次"),
        BadgeRule("night_master", "夜钓高手", "🌙", "夜钓30次"),
        BadgeRule("rain_master", "雨战大师", "🌧️", "雨天出钓20次"),
        BadgeRule("big_catch_king", "爆护王", "🏆", "单次记录渔获100尾以上"),
        BadgeRule("lure_master", "路亚高手", "🎯", "路亚记录达到100次"),
        BadgeRule("tech_author", "技术分享达人", "📖", "累计发布100篇技术分享"),
    )

    @classmethod
    async def unlock_eligible_badges(cls, session: Any, user_id: int) -> list[str]:
        unlocked: list[str] = []
        for rule in cls.BADGE_RULES:
            if await cls._has_badge(session, user_id, rule.code):
                continue
            if await cls._is_eligible(session, user_id, rule.code):
                await cls._unlock_badge(session, user_id, rule.code)
                unlocked.append(rule.code)
        if unlocked:
            await session.commit()
        return unlocked

    @classmethod
    async def get_user_badges(cls, session: Any, user_id: int) -> list[dict[str, str]]:
        from sqlalchemy import select
        from app.models import UserBadge

        result = await session.execute(
            select(UserBadge.badge_code)
            .where(UserBadge.user_id == user_id)
            .order_by(UserBadge.created_at.desc())
        )
        codes = set(result.scalars().all())
        return [
            {
                "code": rule.code,
                "name": rule.name,
                "icon": rule.icon,
                "description": rule.description,
            }
            for rule in cls.BADGE_RULES
            if rule.code in codes
        ]

    @classmethod
    async def seed_badges(cls, session: Any) -> None:
        from sqlalchemy import select
        from app.models import Badge

        result = await session.execute(select(Badge.code))
        existing_codes = set(result.scalars().all())
        for rule in cls.BADGE_RULES:
            if rule.code in existing_codes:
                continue
            session.add(Badge(
                code=rule.code,
                name=rule.name,
                icon=rule.icon,
                description=rule.description,
            ))
        await session.commit()

    @classmethod
    async def _has_badge(cls, session: Any, user_id: int, badge_code: str) -> bool:
        from sqlalchemy import select
        from app.models import UserBadge

        result = await session.execute(
            select(UserBadge.id).where(
                UserBadge.user_id == user_id,
                UserBadge.badge_code == badge_code,
            )
        )
        return result.scalar_one_or_none() is not None

    @classmethod
    async def _unlock_badge(cls, session: Any, user_id: int, badge_code: str) -> None:
        from app.models import UserBadge

        session.add(UserBadge(user_id=user_id, badge_code=badge_code))

    @classmethod
    async def _is_eligible(cls, session: Any, user_id: int, badge_code: str) -> bool:
        from sqlalchemy import cast, extract, func, or_, select, String
        from app.models import CatchLog, FishingSpot, Post

        if badge_code == "first_catch_log":
            result = await session.execute(select(func.count(CatchLog.id)).where(CatchLog.user_id == user_id))
            return int(result.scalar() or 0) >= 1
        if badge_code == "hundred_trips":
            result = await session.execute(select(func.count(CatchLog.id)).where(CatchLog.user_id == user_id))
            return int(result.scalar() or 0) >= 100
        if badge_code == "thousand_fish":
            result = await session.execute(select(func.coalesce(func.sum(CatchLog.quantity), 0)).where(CatchLog.user_id == user_id))
            return int(result.scalar() or 0) >= 1000
        if badge_code == "sea_master":
            result = await session.execute(
                select(func.count(CatchLog.id))
                .join(CatchLog.spot)
                .where(CatchLog.user_id == user_id, CatchLog.spot.has(water_type="sea"))
            )
            return int(result.scalar() or 0) >= 50
        if badge_code == "night_master":
            result = await session.execute(
                select(func.count(CatchLog.id)).where(
                    CatchLog.user_id == user_id,
                    extract("hour", CatchLog.fishing_at) >= 18,
                )
            )
            return int(result.scalar() or 0) >= 30
        if badge_code == "rain_master":
            weather_text = cast(CatchLog.weather_snapshot, String)
            result = await session.execute(
                select(func.count(CatchLog.id)).where(
                    CatchLog.user_id == user_id,
                    or_(
                        weather_text.ilike("%rain%"),
                        weather_text.ilike("%雨%"),
                        weather_text.ilike("%drizzle%"),
                        weather_text.ilike("%shower%"),
                    ),
                )
            )
            return int(result.scalar() or 0) >= 20
        if badge_code == "big_catch_king":
            result = await session.execute(
                select(func.count(CatchLog.id)).where(
                    CatchLog.user_id == user_id,
                    CatchLog.quantity >= 100,
                )
            )
            return int(result.scalar() or 0) >= 1
        if badge_code == "lure_master":
            keyword = "%路亚%"
            result = await session.execute(
                select(func.count(CatchLog.id))
                .outerjoin(FishingSpot, FishingSpot.id == CatchLog.spot_id)
                .where(
                    CatchLog.user_id == user_id,
                    or_(
                        CatchLog.bait.ilike(keyword),
                        CatchLog.equipment.ilike(keyword),
                        CatchLog.rod.ilike(keyword),
                        CatchLog.line_group.ilike(keyword),
                        CatchLog.note.ilike(keyword),
                        FishingSpot.tags.ilike(keyword),
                        FishingSpot.description.ilike(keyword),
                    ),
                )
            )
            return int(result.scalar() or 0) >= 100
        if badge_code == "tech_author":
            result = await session.execute(
                select(func.count(Post.id)).where(
                    Post.user_id == user_id,
                    Post.tag == "技术分享",
                )
            )
            return int(result.scalar() or 0) >= 100
        return False
