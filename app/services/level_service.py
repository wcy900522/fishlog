from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LevelRule:
    level: int
    title: str
    required_xp: int


@dataclass(frozen=True)
class LevelInfo:
    level: int
    title: str
    xp: int
    current_level_xp: int
    next_level_xp: int | None
    xp_to_next: int
    progress_percent: int


class LevelService:
    LEVEL_RULES: tuple[LevelRule, ...] = (
        LevelRule(1, "初学钓手", 0),
        LevelRule(2, "钓鱼新人", 100),
        LevelRule(3, "路亚新兵", 300),
        LevelRule(4, "出钓达人", 700),
        LevelRule(5, "野钓老手", 1500),
        LevelRule(6, "江河钓客", 3000),
        LevelRule(7, "湖库高手", 6000),
        LevelRule(8, "海钓达人", 12000),
        LevelRule(9, "钓王", 25000),
        LevelRule(10, "传奇钓圣", 50000),
    )
    LEVEL_BENEFITS: dict[int, tuple[str, ...]] = {
        1: ("发布帖子", "回复帖子", "创建出钓记录"),
        2: ("上传更多图片",),
        3: ("自定义头像",),
        4: ("修改用户名（一次）",),
        5: ("创建专题合集", "收藏夹"),
        6: ("成为钓点贡献者", "新增公共钓点"),
        7: ("发布装备评测专区",),
        8: ("投稿首页推荐",),
        9: ("官方认证：资深钓友",),
        10: ("传奇钓圣特殊称号", "头像金色边框",),
    }

    @classmethod
    def get_rule_for_xp(cls, xp: int) -> LevelRule:
        normalized_xp = max(0, int(xp or 0))
        current = cls.LEVEL_RULES[0]
        for rule in cls.LEVEL_RULES:
            if normalized_xp >= rule.required_xp:
                current = rule
            else:
                break
        return current

    @classmethod
    def get_next_rule(cls, level: int) -> LevelRule | None:
        for rule in cls.LEVEL_RULES:
            if rule.level > level:
                return rule
        return None

    @classmethod
    def get_level_info(cls, xp: int, current_level: int = 1) -> LevelInfo:
        normalized_xp = max(0, int(xp or 0))
        calculated_rule = cls.get_rule_for_xp(normalized_xp)
        effective_level = max(int(current_level or 1), calculated_rule.level)
        effective_rule = next(
            (rule for rule in cls.LEVEL_RULES if rule.level == effective_level),
            calculated_rule,
        )
        next_rule = cls.get_next_rule(effective_rule.level)

        if not next_rule:
            return LevelInfo(
                level=effective_rule.level,
                title=effective_rule.title,
                xp=normalized_xp,
                current_level_xp=effective_rule.required_xp,
                next_level_xp=None,
                xp_to_next=0,
                progress_percent=100,
            )

        span = max(1, next_rule.required_xp - effective_rule.required_xp)
        gained = max(0, normalized_xp - effective_rule.required_xp)
        progress = min(100, int(gained / span * 100))
        return LevelInfo(
            level=effective_rule.level,
            title=effective_rule.title,
            xp=normalized_xp,
            current_level_xp=effective_rule.required_xp,
            next_level_xp=next_rule.required_xp,
            xp_to_next=max(0, next_rule.required_xp - normalized_xp),
            progress_percent=progress,
        )

    @classmethod
    def apply_level_to_user(cls, user: object) -> LevelInfo:
        info = cls.get_level_info(
            xp=int(getattr(user, "xp", 0) or 0),
            current_level=int(getattr(user, "level", 1) or 1),
        )
        if info.level > int(getattr(user, "level", 1) or 1):
            setattr(user, "level", info.level)
            setattr(user, "title", info.title)
        elif not getattr(user, "title", None):
            setattr(user, "title", info.title)
        return info

    @classmethod
    def get_benefits(cls, level: int) -> list[str]:
        benefits: list[str] = []
        for required_level, items in sorted(cls.LEVEL_BENEFITS.items()):
            if level >= required_level:
                benefits.extend(items)
        return benefits
