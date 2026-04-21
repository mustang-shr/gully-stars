from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import Team, TeamMember, User, Follow, MembershipStatus, UserRole
from app.schemas.schemas import (
    CreateTeamRequest, TeamPublic, TeamDetail, TeamMemberPublic,
    JoinTeamRequest, UpdateMembershipRequest
)
from app.api.v1.deps import get_current_user
from app.utils.slugify import make_team_slug

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("/", response_model=TeamDetail, status_code=status.HTTP_201_CREATED)
async def create_team(
    payload: CreateTeamRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in (UserRole.CAPTAIN, UserRole.ORGANISER):
        # Promote to captain when creating first team
        current_user.role = UserRole.CAPTAIN
        db.add(current_user)

    slug = await make_team_slug(payload.name, db)
    team = Team(
        name=payload.name,
        slug=slug,
        sport=payload.sport,
        description=payload.description,
        location=payload.location,
        visibility=payload.visibility,
        captain_id=current_user.id,
    )
    db.add(team)
    await db.flush()

    # Auto-approve captain as first member
    member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        status=MembershipStatus.APPROVED,
    )
    db.add(member)
    await db.flush()
    await db.refresh(team)

    return await _team_detail(team, current_user.id, db)


@router.get("/", response_model=List[TeamPublic])
async def list_teams(
    sport: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(Team).where(Team.is_active == True)
    if sport:
        q = q.where(Team.sport == sport)
    if search:
        q = q.where(Team.name.ilike(f"%{search}%"))
    q = q.limit(limit).offset(offset).order_by(Team.created_at.desc())
    result = await db.execute(q)
    teams = result.scalars().all()
    return [TeamPublic.model_validate(t) for t in teams]


@router.get("/{slug}", response_model=TeamDetail)
async def get_team(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Team)
        .where(Team.slug == slug, Team.is_active == True)
        .options(selectinload(Team.captain))
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return await _team_detail(team, None, db)


@router.get("/{slug}/members", response_model=List[TeamMemberPublic])
async def get_team_members(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Team).where(Team.slug == slug, Team.is_active == True)
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    result = await db.execute(
        select(TeamMember)
        .where(TeamMember.team_id == team.id, TeamMember.status == MembershipStatus.APPROVED)
        .options(selectinload(TeamMember.user))
    )
    members = result.scalars().all()
    return [TeamMemberPublic.model_validate(m) for m in members]


@router.post("/{slug}/join", status_code=status.HTTP_201_CREATED)
async def request_to_join(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Team).where(Team.slug == slug, Team.is_active == True))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    existing = await db.execute(
        select(TeamMember).where(TeamMember.team_id == team.id, TeamMember.user_id == current_user.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already a member or request pending")

    membership = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        status=MembershipStatus.APPROVED if team.visibility.value == "public" else MembershipStatus.PENDING,
    )
    db.add(membership)
    return {"message": "Join request submitted", "status": membership.status}


@router.put("/{slug}/members/{user_id}", response_model=TeamMemberPublic)
async def update_membership(
    slug: str,
    user_id: int,
    payload: UpdateMembershipRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Team).where(Team.slug == slug))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.captain_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the captain can manage members")

    result = await db.execute(
        select(TeamMember)
        .where(TeamMember.team_id == team.id, TeamMember.user_id == user_id)
        .options(selectinload(TeamMember.user))
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    member.status = payload.status
    db.add(member)
    await db.flush()
    return TeamMemberPublic.model_validate(member)


@router.post("/{slug}/follow")
async def follow_team(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Team).where(Team.slug == slug))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    existing = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id, Follow.team_id == team.id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already following")

    follow = Follow(follower_id=current_user.id, team_id=team.id)
    db.add(follow)
    return {"message": "Now following team"}


@router.delete("/{slug}/follow")
async def unfollow_team(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Team).where(Team.slug == slug))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    result = await db.execute(
        select(Follow).where(Follow.follower_id == current_user.id, Follow.team_id == team.id)
    )
    follow = result.scalar_one_or_none()
    if follow:
        await db.delete(follow)
    return {"message": "Unfollowed"}


# ─── Helpers ────────────────────────────────────────────────────────────────────

async def _team_detail(team: Team, user_id: Optional[int], db: AsyncSession) -> TeamDetail:
    member_count_result = await db.execute(
        select(func.count(TeamMember.id)).where(
            TeamMember.team_id == team.id,
            TeamMember.status == MembershipStatus.APPROVED,
        )
    )
    member_count = member_count_result.scalar() or 0

    follower_count_result = await db.execute(
        select(func.count(Follow.id)).where(Follow.team_id == team.id)
    )
    follower_count = follower_count_result.scalar() or 0

    # Load captain if not loaded
    if not hasattr(team, '_captain_loaded') or team.captain is None:
        captain_result = await db.execute(select(User).where(User.id == team.captain_id))
        captain = captain_result.scalar_one()
    else:
        captain = team.captain

    from app.schemas.schemas import UserPublic
    detail = TeamDetail(
        **TeamPublic.model_validate(team).model_dump(),
        captain=UserPublic.model_validate(captain),
        member_count=member_count,
        follower_count=follower_count,
    )
    return detail
