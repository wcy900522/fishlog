from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.deps import is_admin_user
from app.models import CatchLog, User
from app.repositories import CatchLogRepository, FishingSpotRepository
from app.schemas import CatchLogCreate, CatchLogUpdate
from app.services.badge_service import BadgeService
from app.services.experience_service import ExperienceService
from app.services.weather_service import WeatherService


class RecordService:
    @staticmethod
    async def list_public_records(
        session: AsyncSession,
        spot_id: int | None = None,
        species: str | None = None,
        bait: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[CatchLog]:
        return await CatchLogRepository.get_all_logs(
            session,
            spot_id=spot_id,
            species=species,
            bait=bait,
            date_from=date_from,
            date_to=date_to,
        )

    @staticmethod
    async def list_records(
        session: AsyncSession,
        user: User,
        spot_id: int | None = None,
        species: str | None = None,
        bait: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
    ) -> list[CatchLog]:
        if is_admin_user(user):
            return await CatchLogRepository.get_all_logs(
                session,
                spot_id=spot_id,
                species=species,
                bait=bait,
                date_from=date_from,
                date_to=date_to,
            )
        return await CatchLogRepository.get_logs_by_user(
            session,
            user.id,
            spot_id=spot_id,
            species=species,
            bait=bait,
            date_from=date_from,
            date_to=date_to,
        )

    @staticmethod
    async def create_record(session: AsyncSession, user: User, record_data: CatchLogCreate) -> CatchLog:
        spot = await FishingSpotRepository.get_spot_by_id(session, record_data.spot_id)
        if not spot:
            raise ValueError("Spot not found")

        weather = await WeatherService.get_current_weather(float(spot.latitude), float(spot.longitude))
        record = await CatchLogRepository.create_log(session, user.id, record_data, weather)
        await ExperienceService.award_catch_log(session, user, record)
        await BadgeService.unlock_eligible_badges(session, user.id)
        return record

    @staticmethod
    async def get_record(session: AsyncSession, user: User, record_id: int) -> CatchLog | None:
        return await CatchLogRepository.get_log_by_id(
            session,
            record_id,
            None if is_admin_user(user) else user.id,
        )

    @staticmethod
    async def update_record(
        session: AsyncSession,
        user: User,
        record_id: int,
        record_data: CatchLogUpdate,
    ) -> CatchLog | None:
        record = await RecordService.get_record(session, user, record_id)
        if not record:
            return None

        next_spot_id = record_data.spot_id or record.spot_id
        spot = await FishingSpotRepository.get_spot_by_id(session, next_spot_id)
        if not spot:
            raise ValueError("Spot not found")
        weather = await WeatherService.get_current_weather(float(spot.latitude), float(spot.longitude)) if spot else {}
        return await CatchLogRepository.update_log(session, record, record_data, weather)

    @staticmethod
    async def delete_record(session: AsyncSession, user: User, record_id: int) -> bool:
        record = await RecordService.get_record(session, user, record_id)
        if not record:
            return False
        await CatchLogRepository.delete_log(session, record)
        return True
