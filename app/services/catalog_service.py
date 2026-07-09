from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import is_admin_user
from app.models import Bait, Equipment, FishSpecies, User
from app.repositories import BaitRepository, EquipmentRepository, FishSpeciesRepository
from app.schemas import (
    BaitCreate,
    BaitUpdate,
    EquipmentCreate,
    EquipmentUpdate,
    FishSpeciesCreate,
    FishSpeciesUpdate,
)


class CatalogService:
    @staticmethod
    async def list_species(session: AsyncSession, keyword: str | None = None, category: str | None = None) -> list[FishSpecies]:
        return await FishSpeciesRepository.list_species(session, keyword=keyword, category=category)

    @staticmethod
    async def get_species(session: AsyncSession, species_id: int) -> FishSpecies | None:
        return await FishSpeciesRepository.get_by_id(session, species_id)

    @staticmethod
    async def create_species(session: AsyncSession, data: FishSpeciesCreate) -> FishSpecies:
        return await FishSpeciesRepository.create(session, data)

    @staticmethod
    async def update_species(session: AsyncSession, species_id: int, data: FishSpeciesUpdate) -> FishSpecies | None:
        item = await FishSpeciesRepository.get_by_id(session, species_id)
        if not item:
            return None
        return await FishSpeciesRepository.update(session, item, data)

    @staticmethod
    async def delete_species(session: AsyncSession, species_id: int) -> bool:
        item = await FishSpeciesRepository.get_by_id(session, species_id)
        if not item:
            return False
        await FishSpeciesRepository.delete(session, item)
        return True

    @staticmethod
    async def list_baits(session: AsyncSession, keyword: str | None = None, bait_type: str | None = None) -> list[Bait]:
        return await BaitRepository.list_baits(session, keyword=keyword, bait_type=bait_type)

    @staticmethod
    async def get_bait(session: AsyncSession, bait_id: int) -> Bait | None:
        return await BaitRepository.get_by_id(session, bait_id)

    @staticmethod
    async def create_bait(session: AsyncSession, data: BaitCreate) -> Bait:
        return await BaitRepository.create(session, data)

    @staticmethod
    async def update_bait(session: AsyncSession, bait_id: int, data: BaitUpdate) -> Bait | None:
        item = await BaitRepository.get_by_id(session, bait_id)
        if not item:
            return None
        return await BaitRepository.update(session, item, data)

    @staticmethod
    async def delete_bait(session: AsyncSession, bait_id: int) -> bool:
        item = await BaitRepository.get_by_id(session, bait_id)
        if not item:
            return False
        await BaitRepository.delete(session, item)
        return True

    @staticmethod
    async def list_equipment(
        session: AsyncSession,
        user: User,
        keyword: str | None = None,
        equipment_type: str | None = None,
    ) -> list[Equipment]:
        return await EquipmentRepository.list_equipment(
            session,
            user_id=user.id,
            keyword=keyword,
            equipment_type=equipment_type,
        )

    @staticmethod
    async def get_equipment(session: AsyncSession, user: User, equipment_id: int) -> Equipment | None:
        return await EquipmentRepository.get_by_id(session, equipment_id, None if is_admin_user(user) else user.id)

    @staticmethod
    async def create_equipment(session: AsyncSession, user: User, data: EquipmentCreate) -> Equipment:
        return await EquipmentRepository.create(session, user.id, data)

    @staticmethod
    async def update_equipment(session: AsyncSession, user: User, equipment_id: int, data: EquipmentUpdate) -> Equipment | None:
        item = await EquipmentRepository.get_by_id(session, equipment_id, None if is_admin_user(user) else user.id)
        if not item:
            return None
        return await EquipmentRepository.update(session, item, data)

    @staticmethod
    async def delete_equipment(session: AsyncSession, user: User, equipment_id: int) -> bool:
        item = await EquipmentRepository.get_by_id(session, equipment_id, None if is_admin_user(user) else user.id)
        if not item:
            return False
        await EquipmentRepository.delete(session, item)
        return True
