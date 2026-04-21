from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import Team, TrainingSession, TrainingRSVP, TeamMember, MembershipStatus, User, RSVPStatus
from app.schemas.schemas import CreateTrainingRequest, TrainingSessionPublic, RSVPRequest
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/teams/{slug}/training", tags=["training"])


async def _get_team_or_404(slug: str, db: AsyncSession) -> Team:
    result = await db.execute(select(Team).where(Team.slug == slug, Team.is_active == True))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


async def _assert_captain(team: Team, user: User):
    if team.captain_id != user.id:
        raise HTTPException(status_code=403, detail="Only the captain can manage training sessions")


async def _enrich_session(session: TrainingSession, user_id: Optional[int], db: AsyncSession) -> TrainingSessionPublic:
    rsvps = await db.execute(
        select(TrainingRSVP).where(TrainingRSVP.session_id == session.id)
    )
    all_rsvps = rsvps.scalars().all()

    going = sum(1 for r in all_rsvps if r.status == RSVPStatus.GOING)
    not_going = sum(1 for r in all_rsvps if r.status == RSVPStatus.NOT_GOING)
    maybe = sum(1 for r in all_rsvps if r.status == RSVPStatus.MAYBE)

    my_rsvp = None
    if user_id:
        for r in all_rsvps:
            if r.user_id == user_id:
                my_rsvp = r.status
                break

    return TrainingSessionPublic(
        **{k: v for k, v in session.__dict__.items() if not k.startswith("_")},
        going_count=going,
        not_going_count=not_going,
        maybe_count=maybe,
        my_rsvp=my_rsvp,
    )


@router.post("/", response_model=TrainingSessionPublic, status_code=status.HTTP_201_CREATED)
async def create_training_session(
    slug: str,
    payload: CreateTrainingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_team_or_404(slug, db)
    await _assert_captain(team, current_user)

    session = TrainingSession(
        team_id=team.id,
        title=payload.title,
        description=payload.description,
        location=payload.location,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
    )
    db.add(session)
    await db.flush()
    return await _enrich_session(session, current_user.id, db)


@router.get("/", response_model=List[TrainingSessionPublic])
async def list_training_sessions(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_team_or_404(slug, db)
    result = await db.execute(
        select(TrainingSession)
        .where(TrainingSession.team_id == team.id)
        .order_by(TrainingSession.scheduled_at.desc())
    )
    sessions = result.scalars().all()
    return [await _enrich_session(s, current_user.id, db) for s in sessions]


@router.get("/{session_id}", response_model=TrainingSessionPublic)
async def get_training_session(
    slug: str,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_team_or_404(slug, db)
    result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.team_id == team.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await _enrich_session(session, current_user.id, db)


@router.post("/{session_id}/rsvp", response_model=TrainingSessionPublic)
async def rsvp_training(
    slug: str,
    session_id: int,
    payload: RSVPRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_team_or_404(slug, db)
    result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.team_id == team.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Upsert RSVP
    existing = await db.execute(
        select(TrainingRSVP).where(
            TrainingRSVP.session_id == session_id,
            TrainingRSVP.user_id == current_user.id,
        )
    )
    rsvp = existing.scalar_one_or_none()
    if rsvp:
        rsvp.status = payload.status
    else:
        rsvp = TrainingRSVP(session_id=session_id, user_id=current_user.id, status=payload.status)
        db.add(rsvp)

    await db.flush()
    return await _enrich_session(session, current_user.id, db)


@router.delete("/{session_id}")
async def cancel_session(
    slug: str,
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_team_or_404(slug, db)
    await _assert_captain(team, current_user)

    result = await db.execute(
        select(TrainingSession).where(
            TrainingSession.id == session_id,
            TrainingSession.team_id == team.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.is_cancelled = True
    db.add(session)
    return {"message": "Session cancelled"}
