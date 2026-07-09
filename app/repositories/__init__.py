from __future__ import annotations
from datetime import datetime, timezone

from sqlalchemy import delete, func, select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, FishingSpot, CatchLog, Post, Comment, XPLog, PostLike, CommentLike, FishSpecies, Bait, Equipment
from app.core.security import SecurityService
from app.schemas import (
    BaitCreate,
    BaitUpdate,
    EquipmentCreate,
    EquipmentUpdate,
    FishSpeciesCreate,
    FishSpeciesUpdate,
    UserRegister,
    CatchLogCreate,
    CatchLogUpdate,
    PostCreate,
    PostUpdate,
    CommentCreate,
    CommentUpdate,
    FishingSpotCreate,
)
from typing import Optional, List

class UserRepository:
    @staticmethod
    async def create_user(session: AsyncSession, user_data: UserRegister) -> User:
        user = User(
            nickname=user_data.nickname,
            phone=user_data.phone,
            password_hash=SecurityService.get_password_hash(user_data.password)
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @staticmethod
    async def get_user_by_phone(session: AsyncSession, phone: str) -> Optional[User]:
        result = await session.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_wechat_openid(session: AsyncSession, openid: str) -> Optional[User]:
        result = await session.execute(select(User).where(User.wechat_openid == openid))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

class FishingSpotRepository:
    @staticmethod
    async def get_all_spots(
        session: AsyncSession,
        keyword: str | None = None,
        water_type: str | None = None,
        tag: str | None = None,
    ) -> List[FishingSpot]:
        query = select(FishingSpot).order_by(FishingSpot.created_at.desc(), FishingSpot.id.desc())
        if keyword:
            like = f"%{keyword}%"
            query = query.where(
                (FishingSpot.name.ilike(like))
                | (FishingSpot.city.ilike(like))
                | (FishingSpot.target_species.ilike(like))
                | (FishingSpot.description.ilike(like))
            )
        if water_type:
            query = query.where(FishingSpot.water_type == water_type)
        if tag:
            query = query.where(FishingSpot.tags.ilike(f"%{tag}%"))
        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_spots_by_user(session: AsyncSession, user_id: int) -> List[FishingSpot]:
        result = await session.execute(
            select(FishingSpot)
            .where(FishingSpot.user_id == user_id)
            .order_by(FishingSpot.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_spot_by_id(session: AsyncSession, spot_id: int) -> Optional[FishingSpot]:
        result = await session.execute(select(FishingSpot).where(FishingSpot.id == spot_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_spot(session: AsyncSession, user_id: int, spot_data: FishingSpotCreate) -> FishingSpot:
        spot = FishingSpot(
            user_id=user_id,
            name=spot_data.name,
            province=spot_data.province,
            city=spot_data.city,
            latitude=spot_data.latitude,
            longitude=spot_data.longitude,
            water_type=spot_data.water_type,
            target_species=spot_data.target_species,
            best_season=spot_data.best_season,
            image_url=spot_data.image_url,
            tags=spot_data.tags,
            description=spot_data.description
        )
        session.add(spot)
        await session.commit()
        await session.refresh(spot)
        return spot

    @staticmethod
    async def update_spot(session: AsyncSession, spot: FishingSpot, spot_data: FishingSpotCreate) -> FishingSpot:
        if spot_data.name:
            spot.name = spot_data.name
        if spot_data.province:
            spot.province = spot_data.province
        if spot_data.city:
            spot.city = spot_data.city
        if spot_data.latitude is not None:
            spot.latitude = spot_data.latitude
        if spot_data.longitude is not None:
            spot.longitude = spot_data.longitude
        if spot_data.water_type:
            spot.water_type = spot_data.water_type
        if spot_data.target_species is not None:
            spot.target_species = spot_data.target_species
        if spot_data.best_season is not None:
            spot.best_season = spot_data.best_season
        if spot_data.image_url is not None:
            spot.image_url = spot_data.image_url
        if spot_data.tags is not None:
            spot.tags = spot_data.tags
        if spot_data.description is not None:
            spot.description = spot_data.description
        await session.commit()
        await session.refresh(spot)
        return spot

    @staticmethod
    async def delete_spot(session: AsyncSession, spot: FishingSpot) -> None:
        await session.delete(spot)
        await session.commit()

class CatchLogRepository:
    @staticmethod
    def _naive_utc(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value
        return value.astimezone(timezone.utc).replace(tzinfo=None)

    @staticmethod
    async def create_log(session: AsyncSession, user_id: int, log_data: CatchLogCreate, weather: dict) -> CatchLog:
        catch_log = CatchLog(
            user_id=user_id,
            spot_id=log_data.spot_id,
            fishing_at=CatchLogRepository._naive_utc(log_data.fishing_at),
            duration=log_data.duration,
            bait=log_data.bait,
            species=log_data.species,
            quantity=log_data.quantity,
            weight=log_data.weight,
            tide=log_data.tide,
            equipment=log_data.equipment,
            rod=log_data.rod,
            line_group=log_data.line_group,
            photo_urls=log_data.photo_urls,
            note=log_data.note,
            temperature=weather.get("temperature"),
            pressure=weather.get("pressure"),
            wind_speed=weather.get("wind_speed"),
            weather_snapshot=weather.get("raw_json")
        )
        session.add(catch_log)
        await session.commit()
        await session.refresh(catch_log)
        return catch_log

    @staticmethod
    async def get_logs_by_user(
        session: AsyncSession,
        user_id: int,
        spot_id: int | None = None,
        species: str | None = None,
        bait: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> List[CatchLog]:
        query = select(CatchLog).where(CatchLog.user_id == user_id)
        query = CatchLogRepository._apply_log_filters(query, spot_id, species, bait, date_from, date_to)
        result = await session.execute(query.order_by(CatchLog.fishing_at.desc(), CatchLog.id.desc()))
        return result.scalars().all()

    @staticmethod
    async def get_all_logs(
        session: AsyncSession,
        spot_id: int | None = None,
        species: str | None = None,
        bait: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> List[CatchLog]:
        query = select(CatchLog).options(selectinload(CatchLog.user))
        query = CatchLogRepository._apply_log_filters(query, spot_id, species, bait, date_from, date_to)
        result = await session.execute(query.order_by(CatchLog.fishing_at.desc(), CatchLog.id.desc()))
        return result.scalars().all()

    @staticmethod
    def _apply_log_filters(query, spot_id, species, bait, date_from, date_to):
        if spot_id is not None:
            query = query.where(CatchLog.spot_id == spot_id)
        if species:
            query = query.where(CatchLog.species.ilike(f"%{species}%"))
        if bait:
            query = query.where(CatchLog.bait.ilike(f"%{bait}%"))
        if date_from:
            query = query.where(CatchLog.fishing_at >= CatchLogRepository._naive_utc(date_from))
        if date_to:
            query = query.where(CatchLog.fishing_at <= CatchLogRepository._naive_utc(date_to))
        return query

    @staticmethod
    async def get_log_by_id(session: AsyncSession, log_id: int, user_id: Optional[int] = None) -> Optional[CatchLog]:
        query = select(CatchLog).where(CatchLog.id == log_id)
        if user_id is not None:
            query = query.where(CatchLog.user_id == user_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_log(session: AsyncSession, log: CatchLog, log_data: CatchLogUpdate, weather: dict) -> CatchLog:
        if log_data.spot_id is not None:
            log.spot_id = log_data.spot_id
        if log_data.fishing_at:
            log.fishing_at = CatchLogRepository._naive_utc(log_data.fishing_at)
        if log_data.duration:
            log.duration = log_data.duration
        if log_data.bait is not None:
            log.bait = log_data.bait
        if log_data.species is not None:
            log.species = log_data.species
        if log_data.quantity is not None:
            log.quantity = log_data.quantity
        if log_data.weight is not None:
            log.weight = log_data.weight
        if log_data.tide is not None:
            log.tide = log_data.tide
        if log_data.equipment is not None:
            log.equipment = log_data.equipment
        if log_data.rod is not None:
            log.rod = log_data.rod
        if log_data.line_group is not None:
            log.line_group = log_data.line_group
        if log_data.photo_urls is not None:
            log.photo_urls = log_data.photo_urls
        if log_data.note is not None:
            log.note = log_data.note

        if weather:
            log.temperature = weather.get("temperature")
            log.pressure = weather.get("pressure")
            log.wind_speed = weather.get("wind_speed")
            log.weather_snapshot = weather.get("raw_json")

        await session.commit()
        await session.refresh(log)
        return log

    @staticmethod
    async def delete_log(session: AsyncSession, log: CatchLog) -> None:
        await session.delete(log)
        await session.commit()

class PostRepository:
    @staticmethod
    async def create_post(session: AsyncSession, user_id: int, post_data: PostCreate) -> Post:
        post = Post(
            user_id=user_id,
            title=post_data.title,
            tag=post_data.tag,
            content=post_data.content,
            image_urls=post_data.image_urls,
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)
        return post

    @staticmethod
    async def get_all_posts(session: AsyncSession, skip: int = 0, limit: int = 10) -> List[Post]:
        result = await session.execute(
            select(Post).order_by(desc(Post.created_at)).offset(skip).limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def search_posts(session: AsyncSession, keyword: str, skip: int = 0, limit: int = 10) -> List[Post]:
        result = await session.execute(
            select(Post).where(
                (Post.title.ilike(f"%{keyword}%")) | (Post.content.ilike(f"%{keyword}%"))
            ).order_by(desc(Post.created_at)).offset(skip).limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_post_by_id(session: AsyncSession, post_id: int) -> Optional[Post]:
        result = await session.execute(select(Post).where(Post.id == post_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_post(session: AsyncSession, post: Post, post_data: PostUpdate) -> Post:
        if post_data.title:
            post.title = post_data.title
        if post_data.tag:
            post.tag = post_data.tag
        if post_data.content:
            post.content = post_data.content
        if post_data.image_urls is not None:
            post.image_urls = post_data.image_urls
        await session.commit()
        await session.refresh(post)
        return post

    @staticmethod
    async def delete_post(session: AsyncSession, post: Post) -> None:
        comment_ids = select(Comment.id).where(Comment.post_id == post.id)
        await session.execute(delete(CommentLike).where(CommentLike.comment_id.in_(comment_ids)))
        await session.execute(delete(PostLike).where(PostLike.post_id == post.id))
        await session.delete(post)
        await session.commit()

class CommentRepository:
    @staticmethod
    async def create_comment(session: AsyncSession, post_id: int, user_id: int, comment_data: CommentCreate) -> Comment:
        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            content=comment_data.content
        )
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        return comment

    @staticmethod
    async def get_comments_by_post(session: AsyncSession, post_id: int) -> List[Comment]:
        result = await session.execute(
            select(Comment).where(Comment.post_id == post_id).order_by(Comment.created_at)
        )
        return result.scalars().all()

    @staticmethod
    async def get_comment_by_id(session: AsyncSession, comment_id: int) -> Optional[Comment]:
        result = await session.execute(select(Comment).where(Comment.id == comment_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_comment(session: AsyncSession, comment: Comment, comment_data: CommentUpdate) -> Comment:
        comment.content = comment_data.content
        await session.commit()
        await session.refresh(comment)
        return comment

    @staticmethod
    async def delete_comment(session: AsyncSession, comment: Comment) -> None:
        await session.execute(delete(CommentLike).where(CommentLike.comment_id == comment.id))
        await session.delete(comment)
        await session.commit()


class XPLogRepository:
    @staticmethod
    async def get_logs_by_user(session: AsyncSession, user_id: int, skip: int = 0, limit: int = 20) -> List[XPLog]:
        result = await session.execute(
            select(XPLog)
            .where(XPLog.user_id == user_id)
            .order_by(XPLog.created_at.desc(), XPLog.id.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class LikeRepository:
    @staticmethod
    async def create_post_like(session: AsyncSession, post_id: int, user_id: int) -> Optional[PostLike]:
        existing = await session.execute(
            select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            return None
        like = PostLike(post_id=post_id, user_id=user_id)
        session.add(like)
        await session.flush()
        return like

    @staticmethod
    async def create_comment_like(session: AsyncSession, comment_id: int, user_id: int) -> Optional[CommentLike]:
        existing = await session.execute(
            select(CommentLike).where(CommentLike.comment_id == comment_id, CommentLike.user_id == user_id)
        )
        if existing.scalar_one_or_none():
            return None
        like = CommentLike(comment_id=comment_id, user_id=user_id)
        session.add(like)
        await session.flush()
        return like


class DashboardRepository:
    @staticmethod
    async def get_trip_count(session: AsyncSession, user_id: int) -> int:
        result = await session.execute(
            select(func.count(CatchLog.id)).where(CatchLog.user_id == user_id)
        )
        return int(result.scalar() or 0)

    @staticmethod
    async def get_total_quantity(session: AsyncSession, user_id: int) -> int:
        result = await session.execute(
            select(func.coalesce(func.sum(CatchLog.quantity), 0)).where(CatchLog.user_id == user_id)
        )
        return int(result.scalar() or 0)

    @staticmethod
    async def get_common_spots(session: AsyncSession, user_id: int, limit: int = 5) -> list[dict]:
        count_expr = func.count(CatchLog.id).label("count")
        result = await session.execute(
            select(FishingSpot.name, count_expr)
            .join(CatchLog, CatchLog.spot_id == FishingSpot.id)
            .where(CatchLog.user_id == user_id)
            .group_by(FishingSpot.id, FishingSpot.name)
            .order_by(count_expr.desc())
            .limit(limit)
        )
        return [{"name": name or "未知钓点", "count": int(count or 0)} for name, count in result.all()]

    @staticmethod
    async def get_common_species(session: AsyncSession, user_id: int, limit: int = 5) -> list[dict]:
        count_expr = func.count(CatchLog.id).label("count")
        result = await session.execute(
            select(CatchLog.species, count_expr)
            .where(CatchLog.user_id == user_id, CatchLog.species.is_not(None), CatchLog.species != "")
            .group_by(CatchLog.species)
            .order_by(count_expr.desc())
            .limit(limit)
        )
        return [{"name": species or "未知鱼种", "count": int(count or 0)} for species, count in result.all()]

    @staticmethod
    async def get_common_baits(session: AsyncSession, user_id: int, limit: int = 5) -> list[dict]:
        count_expr = func.count(CatchLog.id).label("count")
        result = await session.execute(
            select(CatchLog.bait, count_expr)
            .where(CatchLog.user_id == user_id, CatchLog.bait.is_not(None), CatchLog.bait != "")
            .group_by(CatchLog.bait)
            .order_by(count_expr.desc())
            .limit(limit)
        )
        return [{"name": bait or "未知饵料", "count": int(count or 0)} for bait, count in result.all()]

    @staticmethod
    async def get_latest_log(session: AsyncSession, user_id: int) -> Optional[CatchLog]:
        result = await session.execute(
            select(CatchLog)
            .where(CatchLog.user_id == user_id)
            .order_by(CatchLog.fishing_at.desc(), CatchLog.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class FishSpeciesRepository:
    @staticmethod
    async def list_species(session: AsyncSession, keyword: str | None = None, category: str | None = None) -> list[FishSpecies]:
        query = select(FishSpecies).order_by(FishSpecies.created_at.desc(), FishSpecies.id.desc())
        if keyword:
            like = f"%{keyword}%"
            query = query.where(
                (FishSpecies.name.ilike(like))
                | (FishSpecies.category.ilike(like))
                | (FishSpecies.description.ilike(like))
                | (FishSpecies.common_methods.ilike(like))
                | (FishSpecies.common_baits.ilike(like))
            )
        if category:
            query = query.where(FishSpecies.category == category)
        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(session: AsyncSession, species_id: int) -> Optional[FishSpecies]:
        result = await session.execute(select(FishSpecies).where(FishSpecies.id == species_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, data: FishSpeciesCreate) -> FishSpecies:
        item = FishSpecies(**data.model_dump())
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def update(session: AsyncSession, item: FishSpecies, data: FishSpeciesUpdate) -> FishSpecies:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def delete(session: AsyncSession, item: FishSpecies) -> None:
        await session.delete(item)
        await session.commit()


class BaitRepository:
    @staticmethod
    async def list_baits(session: AsyncSession, keyword: str | None = None, bait_type: str | None = None) -> list[Bait]:
        query = select(Bait).order_by(Bait.created_at.desc(), Bait.id.desc())
        if keyword:
            like = f"%{keyword}%"
            query = query.where(
                (Bait.name.ilike(like))
                | (Bait.brand.ilike(like))
                | (Bait.target_species.ilike(like))
                | (Bait.water_type.ilike(like))
                | (Bait.note.ilike(like))
            )
        if bait_type:
            query = query.where(Bait.bait_type == bait_type)
        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(session: AsyncSession, bait_id: int) -> Optional[Bait]:
        result = await session.execute(select(Bait).where(Bait.id == bait_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, data: BaitCreate) -> Bait:
        item = Bait(**data.model_dump())
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def update(session: AsyncSession, item: Bait, data: BaitUpdate) -> Bait:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def delete(session: AsyncSession, item: Bait) -> None:
        await session.delete(item)
        await session.commit()


class EquipmentRepository:
    @staticmethod
    async def list_equipment(session: AsyncSession, user_id: int, keyword: str | None = None, equipment_type: str | None = None) -> list[Equipment]:
        query = select(Equipment).where(Equipment.user_id == user_id).order_by(Equipment.created_at.desc(), Equipment.id.desc())
        if keyword:
            like = f"%{keyword}%"
            query = query.where(
                (Equipment.name.ilike(like))
                | (Equipment.brand.ilike(like))
                | (Equipment.model.ilike(like))
                | (Equipment.parameters.ilike(like))
                | (Equipment.note.ilike(like))
            )
        if equipment_type:
            query = query.where(Equipment.equipment_type == equipment_type)
        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_by_id(session: AsyncSession, equipment_id: int, user_id: int | None = None) -> Optional[Equipment]:
        query = select(Equipment).where(Equipment.id == equipment_id)
        if user_id is not None:
            query = query.where(Equipment.user_id == user_id)
        result = await session.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(session: AsyncSession, user_id: int, data: EquipmentCreate) -> Equipment:
        item = Equipment(user_id=user_id, **data.model_dump())
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def update(session: AsyncSession, item: Equipment, data: EquipmentUpdate) -> Equipment:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(item, field, value)
        await session.commit()
        await session.refresh(item)
        return item

    @staticmethod
    async def delete(session: AsyncSession, item: Equipment) -> None:
        await session.delete(item)
        await session.commit()
