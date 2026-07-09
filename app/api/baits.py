from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_db
from app.core.deps import require_admin_user
from app.models import User
from app.schemas import BaitCreate, BaitResponse, BaitUpdate
from app.services import CatalogService


router = APIRouter(prefix="/api/baits", tags=["baits"])


@router.get("", response_model=list[BaitResponse])
async def list_baits(
    keyword: str | None = None,
    bait_type: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    return await CatalogService.list_baits(session, keyword=keyword, bait_type=bait_type)


@router.get("/{bait_id}", response_model=BaitResponse)
async def get_bait(
    bait_id: int,
    session: AsyncSession = Depends(get_db),
):
    item = await CatalogService.get_bait(session, bait_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bait not found")
    return item


@router.post("", response_model=BaitResponse)
async def create_bait(
    payload: BaitCreate,
    admin: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await CatalogService.create_bait(session, payload)


@router.put("/{bait_id}", response_model=BaitResponse)
async def update_bait(
    bait_id: int,
    payload: BaitUpdate,
    admin: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db),
):
    item = await CatalogService.update_bait(session, bait_id, payload)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bait not found")
    return item


@router.delete("/{bait_id}")
async def delete_bait(
    bait_id: int,
    admin: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db),
):
    deleted = await CatalogService.delete_bait(session, bait_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bait not found")
    return {"message": "Bait deleted successfully"}
