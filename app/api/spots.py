from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.orm import selectinload
from typing import List
from pathlib import Path
from uuid import uuid4
from app.core.config import get_db
from app.core.deps import can_manage_user_content, get_current_user, is_admin_user, is_root_admin_user
from app.schemas import FishingSpotResponse, FishingSpotCreate
from app.repositories import FishingSpotRepository
from app.services import WeatherService
from app.models import CatchLog, FishingSpot

router = APIRouter(prefix="/api/spots", tags=["spots"])
PUBLISHER_DISPLAY_NAME = "管理员发布"
ALLOWED_SPOT_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_SPOT_IMAGE_SIZE = 5 * 1024 * 1024


def public_user_nickname(user) -> str:
    if not user:
        return PUBLISHER_DISPLAY_NAME
    if is_root_admin_user(user):
        return PUBLISHER_DISPLAY_NAME
    return user.nickname


def build_spot_response(spot: FishingSpot) -> dict:
    user = None
    if "user" not in sa_inspect(spot).unloaded:
        user = spot.user

    return {
        "id": spot.id,
        "user_id": spot.user_id,
        "name": spot.name,
        "province": spot.province,
        "city": spot.city,
        "latitude": float(spot.latitude),
        "longitude": float(spot.longitude),
        "water_type": spot.water_type,
        "target_species": spot.target_species,
        "best_season": spot.best_season,
        "image_url": spot.image_url,
        "tags": spot.tags,
        "description": spot.description,
        "created_at": spot.created_at,
        "user_nickname": public_user_nickname(user),
    }

@router.get("", response_model=List[FishingSpotResponse])
async def get_all_spots(
    keyword: str | None = None,
    water_type: str | None = None,
    tag: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    query = (
        select(FishingSpot)
        .options(selectinload(FishingSpot.user))
        .order_by(FishingSpot.created_at.desc(), FishingSpot.id.desc())
    )
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
    spots = result.scalars().all()

    return [build_spot_response(spot) for spot in spots]

@router.get("/mine", response_model=List[FishingSpotResponse])
async def get_my_spots(user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    query = (
        select(FishingSpot)
        .options(selectinload(FishingSpot.user))
        .order_by(FishingSpot.created_at.desc())
    )
    if not is_admin_user(user):
        query = query.where(FishingSpot.user_id == user.id)
    result = await session.execute(query)
    spots = result.scalars().all()

    return [build_spot_response(spot) for spot in spots]

@router.get("/{spot_id}", response_model=FishingSpotResponse)
async def get_spot(spot_id: int, session: AsyncSession = Depends(get_db)):
    result = await session.execute(
        select(FishingSpot)
        .where(FishingSpot.id == spot_id)
        .options(selectinload(FishingSpot.user))
    )
    spot = result.scalar_one_or_none()
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")

    return build_spot_response(spot)

@router.post("", response_model=FishingSpotResponse)
async def create_spot(spot_data: FishingSpotCreate, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    """创建用户自定义钓点"""
    spot = await FishingSpotRepository.create_spot(session, user.id, spot_data)
    spot.user = user
    return build_spot_response(spot)


@router.post("/image")
async def upload_spot_image(
    image: UploadFile = File(...),
    user = Depends(get_current_user),
):
    suffix = ALLOWED_SPOT_IMAGE_TYPES.get(image.content_type or "")
    if not suffix:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PNG, and WebP images are supported",
        )

    content = await image.read()
    if len(content) > MAX_SPOT_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must be 5MB or smaller",
        )

    upload_dir = Path(__file__).resolve().parents[1] / "static" / "uploads" / "spots"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{user.id}_{uuid4().hex}{suffix}"
    file_path = upload_dir / filename
    file_path.write_bytes(content)

    return {"url": f"/static/uploads/spots/{filename}"}

@router.put("/{spot_id}", response_model=FishingSpotResponse)
async def update_spot(spot_id: int, spot_data: FishingSpotCreate, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    """更新用户自定义钓点"""
    result = await session.execute(
        select(FishingSpot)
        .where(FishingSpot.id == spot_id)
        .options(selectinload(FishingSpot.user))
    )
    spot = result.scalar_one_or_none()
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")
    if not can_manage_user_content(user, spot.user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this spot")

    updated_spot = await FishingSpotRepository.update_spot(session, spot, spot_data)
    return build_spot_response(updated_spot)

@router.delete("/{spot_id}")
async def delete_spot(spot_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    """删除用户自定义钓点"""
    spot = await FishingSpotRepository.get_spot_by_id(session, spot_id)
    if not spot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")
    if not can_manage_user_content(user, spot.user_id):
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
            "user_nickname": public_user_nickname(log.user) if log.user else "未知用户",
            "spot_id": log.spot_id,
            "fishing_at": log.fishing_at.isoformat() if log.fishing_at else None,
            "duration": log.duration,
            "bait": log.bait,
            "species": log.species,
            "quantity": log.quantity,
            "weight": float(log.weight) if log.weight is not None else None,
            "tide": log.tide,
            "equipment": log.equipment,
            "rod": log.rod,
            "line_group": log.line_group,
            "photo_urls": log.photo_urls,
            "note": log.note,
            "temperature": float(log.temperature) if log.temperature else None,
            "pressure": float(log.pressure) if log.pressure else None,
            "wind_speed": float(log.wind_speed) if log.wind_speed else None,
            "created_at": log.created_at.isoformat() if log.created_at else None
        }
        logs_data.append(log_dict)

    return logs_data
