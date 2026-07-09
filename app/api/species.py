from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_db
from app.core.deps import require_admin_user
from app.models import User
from app.schemas import FishSpeciesCreate, FishSpeciesResponse, FishSpeciesUpdate
from app.services import CatalogService


router = APIRouter(prefix="/api/species", tags=["species"])


@router.get("", response_model=list[FishSpeciesResponse])
async def list_species(
    keyword: str | None = None,
    category: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    return await CatalogService.list_species(session, keyword=keyword, category=category)


@router.get("/{species_id}", response_model=FishSpeciesResponse)
async def get_species(
    species_id: int,
    session: AsyncSession = Depends(get_db),
):
    item = await CatalogService.get_species(session, species_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Species not found")
    return item


@router.post("", response_model=FishSpeciesResponse)
async def create_species(
    payload: FishSpeciesCreate,
    admin: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db),
):
    return await CatalogService.create_species(session, payload)


@router.put("/{species_id}", response_model=FishSpeciesResponse)
async def update_species(
    species_id: int,
    payload: FishSpeciesUpdate,
    admin: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db),
):
    item = await CatalogService.update_species(session, species_id, payload)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Species not found")
    return item


@router.delete("/{species_id}")
async def delete_species(
    species_id: int,
    admin: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db),
):
    deleted = await CatalogService.delete_species(session, species_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Species not found")
    return {"message": "Species deleted successfully"}
