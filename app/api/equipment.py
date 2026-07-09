from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import EquipmentCreate, EquipmentResponse, EquipmentUpdate
from app.services import CatalogService


router = APIRouter(prefix="/api/equipment", tags=["equipment"])


@router.get("", response_model=list[EquipmentResponse])
async def list_equipment(
    keyword: str | None = None,
    equipment_type: str | None = None,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await CatalogService.list_equipment(session, user, keyword=keyword, equipment_type=equipment_type)


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    item = await CatalogService.get_equipment(session, user, equipment_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return item


@router.post("", response_model=EquipmentResponse)
async def create_equipment(
    payload: EquipmentCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await CatalogService.create_equipment(session, user, payload)


@router.put("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    item = await CatalogService.update_equipment(session, user, equipment_id, payload)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return item


@router.delete("/{equipment_id}")
async def delete_equipment(
    equipment_id: int,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    deleted = await CatalogService.delete_equipment(session, user, equipment_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Equipment not found")
    return {"message": "Equipment deleted successfully"}
