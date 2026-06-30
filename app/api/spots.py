from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.config import get_db
from app.core.security import SecurityService
from app.schemas import FishingSpotResponse, FishingSpotCreate, CatchLogResponse
from app.repositories import FishingSpotRepository, CatchLogRepository, UserRepository
from app.services import WeatherService
from app.models import CatchLog, FishingSpot

router = APIRouter(prefix="/api/spots", tags=["spots"])

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

@router.get("", response_model=List[FishingSpotResponse])
async def get_all_spots(session: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(FishingSpot)
        .options(selectinload(FishingSpot.user))
        .order_by(FishingSpot.created_at.desc())
    )
    spots = result.scalars().all()

    spots_data = []
    for spot in spots:
        spots_data.append({
            "id": spot.id,
            "user_id": spot.user_id,
            "name": spot.name,
            "province": spot.province,
            "city": spot.city,
            "latitude": float(spot.latitude),
            "longitude": float(spot.longitude),
            "water_type": spot.water_type,
            "description": spot.description,
            "created_at": spot.created_at,
            "user_nickname": spot.user.nickname if spot.user else None
        })
    return spots_data

@router.get("/{spot_id}", response_model=FishingSpotResponse)
async def get_spot(spot_id: int, session: AsyncSession = Depends(get_db)):
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(FishingSpot)
        .where(FishingSpot.id == spot_id)
        .options(selectinload(FishingSpot.user))
    )
    spot = result.scalar_one_or_none()
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")

    return {
        "id": spot.id,
        "user_id": spot.user_id,
        "name": spot.name,
        "province": spot.province,
        "city": spot.city,
        "latitude": float(spot.latitude),
        "longitude": float(spot.longitude),
        "water_type": spot.water_type,
        "description": spot.description,
        "created_at": spot.created_at,
        "user_nickname": spot.user.nickname if spot.user else None
    }

@router.post("", response_model=FishingSpotResponse)
async def create_spot(spot_data: FishingSpotCreate, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    """创建用户自定义钓点"""
    spot = await FishingSpotRepository.create_spot(session, user.id, spot_data)
    return {
        "id": spot.id,
        "user_id": spot.user_id,
        "name": spot.name,
        "province": spot.province,
        "city": spot.city,
        "latitude": float(spot.latitude),
        "longitude": float(spot.longitude),
        "water_type": spot.water_type,
        "description": spot.description,
        "created_at": spot.created_at,
        "user_nickname": user.nickname
    }

@router.put("/{spot_id}", response_model=FishingSpotResponse)
async def update_spot(spot_id: int, spot_data: FishingSpotCreate, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    """更新用户自定义钓点"""
    spot = await FishingSpotRepository.get_spot_by_id(session, spot_id)
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")
    if spot.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this spot")

    updated_spot = await FishingSpotRepository.update_spot(session, spot, spot_data)
    return {
        "id": updated_spot.id,
        "user_id": updated_spot.user_id,
        "name": updated_spot.name,
        "province": updated_spot.province,
        "city": updated_spot.city,
        "latitude": float(updated_spot.latitude),
        "longitude": float(updated_spot.longitude),
        "water_type": updated_spot.water_type,
        "description": updated_spot.description,
        "created_at": updated_spot.created_at,
        "user_nickname": user.nickname
    }

@router.delete("/{spot_id}")
async def delete_spot(spot_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    """删除用户自定义钓点"""
    spot = await FishingSpotRepository.get_spot_by_id(session, spot_id)
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")
    if spot.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this spot")

    await FishingSpotRepository.delete_spot(session, spot)
    return {"message": "Spot deleted successfully"}

@router.get("/{spot_id}/weather")
async def get_spot_weather(spot_id: int, session: AsyncSession = Depends(get_db)):
    spot = await FishingSpotRepository.get_spot_by_id(session, spot_id)
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")

    weather = await WeatherService.get_current_weather(float(spot.latitude), float(spot.longitude))
    return weather

@router.get("/{spot_id}/catch-logs")
async def get_spot_logs(spot_id: int, session: AsyncSession = Depends(get_db)):
    """获取该钓点的所有记录（所有人都可以看）"""
    spot = await FishingSpotRepository.get_spot_by_id(session, spot_id)
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")

    # 获取该钓点的所有记录，按时间倒序排列
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(CatchLog)
        .where(CatchLog.spot_id == spot_id)
        .options(selectinload(CatchLog.user))
        .order_by(CatchLog.fishing_at.desc())
    )
    logs = result.scalars().all()

    # 返回包含用户昵称的记录
    logs_data = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "user_id": log.user_id,
            "user_nickname": log.user.nickname if log.user else "未知用户",
            "spot_id": log.spot_id,
            "fishing_at": log.fishing_at.isoformat() if log.fishing_at else None,
            "duration": log.duration,
            "bait": log.bait,
            "species": log.species,
            "quantity": log.quantity,
            "note": log.note,
            "temperature": float(log.temperature) if log.temperature else None,
            "pressure": float(log.pressure) if log.pressure else None,
            "wind_speed": float(log.wind_speed) if log.wind_speed else None,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        logs_data.append(log_dict)

    return logs_data
