from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import List
from pathlib import Path
from uuid import uuid4
from app.core.config import get_db
from app.core.deps import get_current_user, is_root_admin_user
from app.schemas import CatchLogResponse, CatchLogCreate, CatchLogUpdate
from app.services import RecordService

router = APIRouter(prefix="/api/logs", tags=["logs"])
ALLOWED_LOG_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
MAX_LOG_IMAGE_SIZE = 5 * 1024 * 1024


def public_user_nickname(user) -> str | None:
    if not user:
        return None
    if is_root_admin_user(user):
        return "管理员发布"
    return user.nickname


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
        "weight": log.weight,
        "tide": log.tide,
        "equipment": log.equipment,
        "rod": log.rod,
        "line_group": log.line_group,
        "photo_urls": log.photo_urls,
        "note": log.note,
        "temperature": log.temperature,
        "pressure": log.pressure,
        "wind_speed": log.wind_speed,
        "weather_snapshot": log.weather_snapshot,
        "created_at": log.created_at,
        "user_nickname": public_user_nickname(getattr(log, "user", None)),
    }


@router.get("/public", response_model=List[CatchLogResponse])
async def get_public_logs(
    spot_id: int | None = None,
    species: str | None = None,
    bait: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    session: AsyncSession = Depends(get_db),
):
    return [
        build_log_response(log)
        for log in await RecordService.list_public_records(
            session,
            spot_id=spot_id,
            species=species,
            bait=bait,
            date_from=date_from,
            date_to=date_to,
        )
    ]

@router.get("", response_model=List[CatchLogResponse])
async def get_user_logs(
    spot_id: int | None = None,
    species: str | None = None,
    bait: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await RecordService.list_records(
        session,
        user,
        spot_id=spot_id,
        species=species,
        bait=bait,
        date_from=date_from,
        date_to=date_to,
    )

@router.post("", response_model=CatchLogResponse)
async def create_log(
    log_data: CatchLogCreate,
    user = Depends(get_current_user),
    session: AsyncSession = Depends(get_db)
):
    try:
        return await RecordService.create_record(session, user, log_data)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spot not found")


@router.post("/images")
async def upload_log_image(
    image: UploadFile = File(...),
    user = Depends(get_current_user),
):
    suffix = ALLOWED_LOG_IMAGE_TYPES.get(image.content_type or "")
    if not suffix:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPG, PNG, and WebP images are supported",
        )

    content = await image.read()
    if len(content) > MAX_LOG_IMAGE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image must be 5MB or smaller",
        )

    upload_dir = Path(__file__).resolve().parents[1] / "static" / "uploads" / "logs"
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{user.id}_{uuid4().hex}{suffix}"
    file_path = upload_dir / filename
    file_path.write_bytes(content)

    return {"url": f"/static/uploads/logs/{filename}"}


@router.get("/{log_id}", response_model=CatchLogResponse)
async def get_log(log_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    log = await RecordService.get_record(session, user, log_id)
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
    try:
        updated_log = await RecordService.update_record(session, user, log_id, log_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if not updated_log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return updated_log

@router.delete("/{log_id}")
async def delete_log(log_id: int, user = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    deleted = await RecordService.delete_record(session, user, log_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return {"detail": "Log deleted successfully"}
