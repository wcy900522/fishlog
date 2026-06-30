from __future__ import annotations
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User, FishingSpot, CatchLog, Post, Comment
from app.core.security import SecurityService
from app.schemas import UserRegister, CatchLogCreate, CatchLogUpdate, PostCreate, PostUpdate, CommentCreate, FishingSpotCreate
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
    async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
        result = await session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

class FishingSpotRepository:
    @staticmethod
    async def get_all_spots(session: AsyncSession) -> List[FishingSpot]:
        result = await session.execute(select(FishingSpot))
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
        if spot_data.latitude:
            spot.latitude = spot_data.latitude
        if spot_data.longitude:
            spot.longitude = spot_data.longitude
        if spot_data.water_type:
            spot.water_type = spot_data.water_type
        if spot_data.description:
            spot.description = spot_data.description
        await session.commit()
        await session.refresh(spot)
        return spot

    @staticmethod
    async def delete_spot(session: AsyncSession, spot: FishingSpot) -> None:
        session.delete(spot)
        await session.commit()

class CatchLogRepository:
    @staticmethod
    async def create_log(session: AsyncSession, user_id: int, log_data: CatchLogCreate, weather: dict) -> CatchLog:
        catch_log = CatchLog(
            user_id=user_id,
            spot_id=log_data.spot_id,
            fishing_at=log_data.fishing_at,
            duration=log_data.duration,
            bait=log_data.bait,
            species=log_data.species,
            quantity=log_data.quantity,
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
    async def get_logs_by_user(session: AsyncSession, user_id: int) -> List[CatchLog]:
        result = await session.execute(
            select(CatchLog).where(CatchLog.user_id == user_id).order_by(CatchLog.fishing_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_log_by_id(session: AsyncSession, log_id: int, user_id: int) -> Optional[CatchLog]:
        result = await session.execute(
            select(CatchLog).where((CatchLog.id == log_id) & (CatchLog.user_id == user_id))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_log(session: AsyncSession, log: CatchLog, log_data: CatchLogUpdate, weather: dict) -> CatchLog:
        if log_data.fishing_at:
            log.fishing_at = log_data.fishing_at
        if log_data.duration:
            log.duration = log_data.duration
        if log_data.bait:
            log.bait = log_data.bait
        if log_data.species:
            log.species = log_data.species
        if log_data.quantity is not None:
            log.quantity = log_data.quantity
        if log_data.note:
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
        session.delete(log)
        await session.commit()

class PostRepository:
    @staticmethod
    async def create_post(session: AsyncSession, user_id: int, post_data: PostCreate) -> Post:
        post = Post(
            user_id=user_id,
            title=post_data.title,
            content=post_data.content
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
        if post_data.content:
            post.content = post_data.content
        await session.commit()
        await session.refresh(post)
        return post

    @staticmethod
    async def delete_post(session: AsyncSession, post: Post) -> None:
        session.delete(post)
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
    async def delete_comment(session: AsyncSession, comment: Comment) -> None:
        session.delete(comment)
        await session.commit()

