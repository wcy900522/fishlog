from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import DashboardRepository


class DashboardService:
    @staticmethod
    async def get_user_dashboard(session: AsyncSession, user_id: int) -> dict[str, Any]:
        latest_log = await DashboardRepository.get_latest_log(session, user_id)
        return {
            "trip_count": await DashboardRepository.get_trip_count(session, user_id),
            "total_quantity": await DashboardRepository.get_total_quantity(session, user_id),
            "common_spots": await DashboardRepository.get_common_spots(session, user_id),
            "common_species": await DashboardRepository.get_common_species(session, user_id),
            "common_baits": await DashboardRepository.get_common_baits(session, user_id),
            "latest_log": latest_log,
        }
