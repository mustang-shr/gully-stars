from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import User, PlayerStats
from app.schemas.schemas import UserProfile, UpdateProfileRequest, PlayerStatsPublic
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserProfile.model_validate(current_user)


@router.put("/me", response_model=UserProfile)
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(current_user, field, value)
    db.add(current_user)
    await db.flush()
    await db.refresh(current_user)
    return UserProfile.model_validate(current_user)


@router.get("/{username}", response_model=UserProfile)
async def get_user_by_username(username: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfile.model_validate(user)


@router.get("/{user_id}/stats", response_model=list[PlayerStatsPublic])
async def get_user_stats(
    user_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(PlayerStats)
        .where(PlayerStats.user_id == user_id)
        .options(selectinload(PlayerStats.user), selectinload(PlayerStats.team))
    )
    stats = result.scalars().all()
    return [PlayerStatsPublic.model_validate(s) for s in stats]
