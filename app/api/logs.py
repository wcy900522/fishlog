from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.config import get_db
from app.core.deps import get_current_user, is_admin_user
from app.schemas import CatchLogResponse, CatchLogCreate, CatchLogUpdate
from app.repositories import CatchLogRepository, FishingSpotRepository
from app.services import BadgeService, ExperienceService, WeatherService

router = APIRouter(prefix="/api/logs", tags=["logs"])


def build_log_response(log) -> dict:
    return {
        "id": log.id,
        "user_id": log.user_id,
        "spot_id": log.spot_id,
        "fishing_at": log.fishing_at,
        "duration": log.duration,
        "bait": log.bait,
        "species": log.species,
        "quantity": log.quantity,
        "note": log.note,
        "temperature": log.temperature,
        "pressure": log.pressure,
        "wind_speed": log.wind_speed,
        "weather_snapshot": log.weather_snapshot,
        "created_at": log.created_at,
        "user_nickname": log.user.nickname if getattr(log, "user", None) else None,
    }


@router.get("/public", response_model=List[CatchLogResponse])
async def get_public_logs(session: AsyncSession = Depends(get_db)):
    return [
        build_log_response(log)
        for log in await CatchLogRepository.get_all_logs(session)
    ]

@router.get("", response_model=List[CatchLogResponse])
async def get_user_logs(user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    if is_admin_user(user):
        return [
            build_log_response(log)
            for log in await CatchLogRepository.get_all_logs(session)
        ]
    return await CatchLogRepository.get_logs_by_user(session, user.id)

@router.post("", response_model=CatchLogResponse)
async def create_log(
    log_data: CatchLogCreate,
    user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    spot = await FishingSpotRepository.get_spot_by_id(session, log_data.spot_id)
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")

    weather = await WeatherService.get_current_weather(float(spot.latitude), float(spot.longitude))
    catch_log = await CatchLogRepository.create_log(session, user.id, log_data, weather)
    await ExperienceService.award_catch_log(session, user, catch_log)
    await BadgeService.unlock_eligible_badges(session, user.id)
    return catch_log

@router.get("/{log_id}", response_model=CatchLogResponse)
async def get_log(log_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    log = await CatchLogRepository.get_log_by_id(session, log_id, None if is_admin_user(user) else user.id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")

    return log

@router.put("/{log_id}", response_model=CatchLogResponse)
async def update_log(
    log_id: int,
    log_data: CatchLogUpdate,
    user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    log = await CatchLogRepository.get_log_by_id(session, log_id, None if is_admin_user(user) else user.id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")

    spot = await FishingSpotRepository.get_spot_by_id(session, log.spot_id)
    weather = await WeatherService.get_current_weather(float(spot.latitude), float(spot.longitude))

    updated_log = await CatchLogRepository.update_log(session, log, log_data, weather)
    return updated_log

@router.delete("/{log_id}")
async def delete_log(log_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    log = await CatchLogRepository.get_log_by_id(session, log_id, None if is_admin_user(user) else user.id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")

    await CatchLogRepository.delete_log(session, log)
    return {"detail": "Log deleted successfully"}
