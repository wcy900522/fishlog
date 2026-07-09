from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_db
from app.core.deps import get_current_user
from app.models import User
from app.schemas import UserDashboardResponse
from app.services import DashboardService


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/me", response_model=UserDashboardResponse)
async def get_my_dashboard(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await DashboardService.get_user_dashboard(session, user.id)
