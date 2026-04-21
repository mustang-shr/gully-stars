from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import Team, Match, MatchRSVP, User, MatchStatus, RSVPStatus, PlayerStats
from app.schemas.schemas import (
    CreateMatchRequest, MatchPublic, SubmitResultRequest, RSVPRequest, UpdateStatsRequest
)
from app.api.v1.deps import get_current_user

router = APIRouter(prefix="/teams/{slug}/matches", tags=["matches"])


async def _get_team_or_404(slug: str, db: AsyncSession) -> Team:
    result = await db.execute(select(Team).where(Team.slug == slug, Team.is_active == True))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


async def _enrich_match(match: Match, user_id: Optional[int], db: AsyncSession) -> MatchPublic:
    rsvps = await db.execute(
        select(MatchRSVP).where(MatchRSVP.match_id == match.id)
    )
    all_rsvps = rsvps.scalars().all()
    going = sum(1 for r in all_rsvps if r.status == RSVPStatus.GOING)
    my_rsvp = None
    if user_id:
        for r in all_rsvps:
            if r.user_id == user_id:
                my_rsvp = r.status
                break

    return MatchPublic(
        **{k: v for k, v in match.__dict__.items() if not k.startswith("_")},
        going_count=going,
        my_rsvp=my_rsvp,
    )


@router.post("/", response_model=MatchPublic, status_code=status.HTTP_201_CREATED)
async def create_match(
    slug: str,
    payload: CreateMatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_team_or_404(slug, db)
    if team.captain_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only captain can create matches")

    match = Match(
        team_id=team.id,
        opponent_name=payload.opponent_name,
        sport=payload.sport,
        venue=payload.venue,
        scheduled_at=payload.scheduled_at,
        tournament_id=payload.tournament_id,
        status=MatchStatus.SCHEDULED,
    )
    db.add(match)
    await db.flush()
    return await _enrich_match(match, current_user.id, db)


@router.get("/", response_model=List[MatchPublic])
async def list_matches(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_team_or_404(slug, db)
    result = await db.execute(
        select(Match)
        .where(Match.team_id == team.id)
        .order_by(Match.scheduled_at.desc())
    )
    matches = result.scalars().all()
    return [await _enrich_match(m, current_user.id, db) for m in matches]


@router.get("/{match_id}", response_model=MatchPublic)
async def get_match(
    slug: str,
    match_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_team_or_404(slug, db)
    result = await db.execute(
        select(Match).where(Match.id == match_id, Match.team_id == team.id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return await _enrich_match(match, current_user.id, db)


@router.post("/{match_id}/rsvp", response_model=MatchPublic)
async def rsvp_match(
    slug: str,
    match_id: int,
    payload: RSVPRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_team_or_404(slug, db)
    result = await db.execute(
        select(Match).where(Match.id == match_id, Match.team_id == team.id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    existing = await db.execute(
        select(MatchRSVP).where(MatchRSVP.match_id == match_id, MatchRSVP.user_id == current_user.id)
    )
    rsvp = existing.scalar_one_or_none()
    if rsvp:
        rsvp.status = payload.status
    else:
        rsvp = MatchRSVP(match_id=match_id, user_id=current_user.id, status=payload.status)
        db.add(rsvp)

    await db.flush()
    return await _enrich_match(match, current_user.id, db)


@router.post("/{match_id}/result", response_model=MatchPublic)
async def submit_result(
    slug: str,
    match_id: int,
    payload: SubmitResultRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_team_or_404(slug, db)
    if team.captain_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only captain can submit results")

    result = await db.execute(
        select(Match).where(Match.id == match_id, Match.team_id == team.id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    if match.status == MatchStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Result already submitted")

    match.home_score = payload.home_score
    match.away_score = payload.away_score
    match.result_notes = payload.result_notes
    match.status = MatchStatus.COMPLETED
    match.result_submitted_by = current_user.id
    db.add(match)
    await db.flush()
    return await _enrich_match(match, current_user.id, db)


@router.put("/{match_id}/stats/{user_id}", response_model=dict)
async def update_player_stats(
    slug: str,
    match_id: int,
    user_id: int,
    payload: UpdateStatsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    team = await _get_team_or_404(slug, db)
    if team.captain_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only captain can update stats")

    result = await db.execute(
        select(Match).where(Match.id == match_id, Match.team_id == team.id)
    )
    match = result.scalar_one_or_none()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    # Upsert player stats
    result = await db.execute(
        select(PlayerStats).where(
            PlayerStats.user_id == user_id,
            PlayerStats.team_id == team.id,
            PlayerStats.sport == match.sport,
        )
    )
    stats = result.scalar_one_or_none()
    if stats:
        # Merge new stats into existing
        for key, value in payload.stats.items():
            if isinstance(value, (int, float)):
                stats.stats[key] = stats.stats.get(key, 0) + value
            else:
                stats.stats[key] = value
        stats.matches_played += 1
    else:
        stats = PlayerStats(
            user_id=user_id,
            team_id=team.id,
            sport=match.sport,
            matches_played=1,
            stats=payload.stats,
        )
        db.add(stats)

    db.add(stats)
    await db.flush()
    return {"message": "Stats updated"}
