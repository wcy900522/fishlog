from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import CatchLogCreate, CatchLogResponse, CatchLogUpdate
from app.services import RecordService


router = APIRouter(prefix="/api/records", tags=["records"])


@router.get("", response_model=list[CatchLogResponse])
async def list_records(
    spot_id: int | None = None,
    species: str | None = None,
    bait: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    user: User = Depends(get_current_user),
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
async def create_record(
    record_data: CatchLogCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    try:
        return await RecordService.create_record(session, user, record_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/{record_id}", response_model=CatchLogResponse)
async def get_record(
    record_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    record = await RecordService.get_record(session, user, record_id)
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record


@router.put("/{record_id}", response_model=CatchLogResponse)
async def update_record(
    record_id: int,
    record_data: CatchLogUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    try:
        record = await RecordService.update_record(session, user, record_id, record_data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return record


@router.delete("/{record_id}")
async def delete_record(
    record_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    deleted = await RecordService.delete_record(session, user, record_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    return {"detail": "Record deleted successfully"}
