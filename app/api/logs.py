from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from app.core.config import get_db
from app.core.security import SecurityService
from app.schemas import CatchLogResponse, CatchLogCreate, CatchLogUpdate
from app.repositories import CatchLogRepository, UserRepository, FishingSpotRepository
from app.services import WeatherService

router = APIRouter(prefix="/api/logs", tags=["logs"])

async def get_current_user(authorization: Optional[str] = Header(None), session: AsyncSession = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token format")

    token = parts[1]
    payload = SecurityService.decode_token(token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    phone = payload.get("sub")
    user = await UserRepository.get_user_by_phone(session, phone)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    return user

@router.get("", response_model=List[CatchLogResponse])
async def get_user_logs(user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    logs = await CatchLogRepository.get_logs_by_user(session, user.id)
    return logs

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
    return catch_log

@router.get("/{log_id}", response_model=CatchLogResponse)
async def get_log(log_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    log = await CatchLogRepository.get_log_by_id(session, log_id, user.id)
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
    log = await CatchLogRepository.get_log_by_id(session, log_id, user.id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")

    spot = await FishingSpotRepository.get_spot_by_id(session, log.spot_id)
    weather = await WeatherService.get_current_weather(float(spot.latitude), float(spot.longitude))

    updated_log = await CatchLogRepository.update_log(session, log, log_data, weather)
    return updated_log

@router.delete("/{log_id}")
async def delete_log(log_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    log = await CatchLogRepository.get_log_by_id(session, log_id, user.id)
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")

    await CatchLogRepository.delete_log(session, log)
    return {"detail": "Log deleted successfully"}
