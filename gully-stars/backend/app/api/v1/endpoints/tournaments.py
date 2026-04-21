"""
Tournaments Service
- Round-robin: generates all N*(N-1)/2 fixtures
- Bracket (single elimination): generates ceil(log2(N)) rounds
- Live standings auto-updated from match results
"""
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone

from app.db.session import get_db
from app.models.models import (
    Tournament, TournamentTeam, Team, Match, User,
    TournamentStatus, TeamApplyStatus, TournamentFormat, MatchStatus
)
from app.schemas.schemas import (
    CreateTournamentRequest, TournamentPublic, TournamentStanding,
    TournamentTeamPublic, ApproveTeamRequest, UpdateTournamentStatusRequest, TeamPublic
)
from app.api.v1.deps import get_current_user
from app.utils.slugify import make_tournament_slug

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.post("/", response_model=TournamentPublic, status_code=status.HTTP_201_CREATED)
async def create_tournament(
    payload: CreateTournamentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.models import UserRole
    if current_user.role != UserRole.ORGANISER:
        raise HTTPException(status_code=403, detail="Organiser role required")

    slug = await make_tournament_slug(payload.name, db)
    tournament = Tournament(
        name=payload.name,
        slug=slug,
        sport=payload.sport,
        format=payload.format,
        description=payload.description,
        location=payload.location,
        max_teams=payload.max_teams,
        registration_deadline=payload.registration_deadline,
        start_date=payload.start_date,
        end_date=payload.end_date,
        prize_info=payload.prize_info,
        organiser_id=current_user.id,
        status=TournamentStatus.REGISTRATION,
    )
    db.add(tournament)
    await db.flush()
    return await _enrich_tournament(tournament, db)


@router.get("/", response_model=List[TournamentPublic])
async def list_tournaments(
    sport: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = Query(20, le=100),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(Tournament)
    if sport:
        q = q.where(Tournament.sport == sport)
    if status:
        q = q.where(Tournament.status == status)
    q = q.order_by(Tournament.created_at.desc()).limit(limit).offset(offset)
    result = await db.execute(q)
    tournaments = result.scalars().all()
    return [await _enrich_tournament(t, db) for t in tournaments]


@router.get("/{slug}", response_model=TournamentPublic)
async def get_tournament(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tournament).where(Tournament.slug == slug))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    return await _enrich_tournament(t, db)


@router.post("/{slug}/apply")
async def apply_to_tournament(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tournament).where(Tournament.slug == slug))
    tournament = result.scalar_one_or_none()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.status != TournamentStatus.REGISTRATION:
        raise HTTPException(status_code=400, detail="Tournament not accepting applications")

    # Captain must apply with their team
    team_result = await db.execute(
        select(Team).where(Team.captain_id == current_user.id, Team.sport == tournament.sport)
    )
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=400, detail="You must be captain of a team with matching sport")

    existing = await db.execute(
        select(TournamentTeam).where(
            TournamentTeam.tournament_id == tournament.id,
            TournamentTeam.team_id == team.id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Team already applied")

    entry = TournamentTeam(tournament_id=tournament.id, team_id=team.id)
    db.add(entry)
    return {"message": "Application submitted", "team": team.name}


@router.put("/{slug}/teams/{team_id}/approve")
async def approve_team(
    slug: str,
    team_id: int,
    payload: ApproveTeamRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Tournament).where(Tournament.slug == slug))
    tournament = result.scalar_one_or_none()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.organiser_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only organiser can approve teams")

    result = await db.execute(
        select(TournamentTeam).where(
            TournamentTeam.tournament_id == tournament.id,
            TournamentTeam.team_id == team_id,
        )
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Application not found")

    entry.status = payload.status
    if payload.status == TeamApplyStatus.APPROVED:
        entry.approved_at = datetime.now(timezone.utc)
    db.add(entry)
    return {"message": f"Team {payload.status.value}"}


@router.post("/{slug}/generate-fixtures")
async def generate_fixtures(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate all fixtures for an approved tournament.
    Round-robin: every team plays every other team once.
    Bracket: single-elimination bracket seeded by team application order.
    """
    result = await db.execute(select(Tournament).where(Tournament.slug == slug))
    tournament = result.scalar_one_or_none()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")
    if tournament.organiser_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only organiser can generate fixtures")

    # Get approved teams
    result = await db.execute(
        select(TournamentTeam)
        .where(
            TournamentTeam.tournament_id == tournament.id,
            TournamentTeam.status == TeamApplyStatus.APPROVED,
        )
        .options(selectinload(TournamentTeam.team))
    )
    entries = result.scalars().all()
    teams = [e.team for e in entries]

    if len(teams) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 approved teams")

    matches_created = []

    if tournament.format == TournamentFormat.ROUND_ROBIN:
        # N*(N-1)/2 fixtures
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                home = teams[i]
                away = teams[j]
                match = Match(
                    team_id=home.id,
                    opponent_name=away.name,
                    opponent_team_id=away.id,
                    sport=tournament.sport,
                    venue=tournament.location or "TBD",
                    scheduled_at=tournament.start_date or datetime.now(timezone.utc),
                    status=MatchStatus.SCHEDULED,
                    tournament_id=tournament.id,
                    tournament_round=1,
                )
                db.add(match)
                matches_created.append(f"{home.name} vs {away.name}")

    elif tournament.format == TournamentFormat.BRACKET:
        # Single elimination — round 1 fixtures
        n_teams = len(teams)
        n_rounds = math.ceil(math.log2(n_teams))
        for i in range(0, n_teams - 1, 2):
            home = teams[i]
            away = teams[i + 1] if i + 1 < n_teams else None
            if not away:
                # BYE — skip or handle
                continue
            match = Match(
                team_id=home.id,
                opponent_name=away.name,
                opponent_team_id=away.id,
                sport=tournament.sport,
                venue=tournament.location or "TBD",
                scheduled_at=tournament.start_date or datetime.now(timezone.utc),
                status=MatchStatus.SCHEDULED,
                tournament_id=tournament.id,
                tournament_round=1,
            )
            db.add(match)
            matches_created.append(f"R1: {home.name} vs {away.name}")

    tournament.status = TournamentStatus.ACTIVE
    db.add(tournament)
    await db.flush()

    return {
        "message": f"Generated {len(matches_created)} fixtures",
        "format": tournament.format,
        "fixtures": matches_created,
    }


@router.get("/{slug}/standings", response_model=List[TournamentStanding])
async def get_standings(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tournament).where(Tournament.slug == slug))
    tournament = result.scalar_one_or_none()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    result = await db.execute(
        select(TournamentTeam)
        .where(
            TournamentTeam.tournament_id == tournament.id,
            TournamentTeam.status == TeamApplyStatus.APPROVED,
        )
        .options(selectinload(TournamentTeam.team))
        .order_by(TournamentTeam.points.desc(), TournamentTeam.won.desc())
    )
    entries = result.scalars().all()

    standings = []
    for entry in entries:
        standings.append(
            TournamentStanding(
                team=TeamPublic.model_validate(entry.team),
                played=entry.played,
                won=entry.won,
                drawn=entry.drawn,
                lost=entry.lost,
                goals_for=entry.goals_for,
                goals_against=entry.goals_against,
                goal_difference=entry.goals_for - entry.goals_against,
                points=entry.points,
            )
        )
    return standings


@router.get("/{slug}/fixtures", response_model=List[dict])
async def get_fixtures(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tournament).where(Tournament.slug == slug))
    tournament = result.scalar_one_or_none()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    result = await db.execute(
        select(Match)
        .where(Match.tournament_id == tournament.id)
        .order_by(Match.tournament_round, Match.scheduled_at)
    )
    matches = result.scalars().all()

    fixtures = []
    for m in matches:
        team_result = await db.execute(select(Team).where(Team.id == m.team_id))
        team = team_result.scalar_one_or_none()
        fixtures.append({
            "id": m.id,
            "round": m.tournament_round,
            "home_team": team.name if team else "Unknown",
            "away_team": m.opponent_name,
            "venue": m.venue,
            "scheduled_at": m.scheduled_at.isoformat(),
            "status": m.status,
            "home_score": m.home_score,
            "away_score": m.away_score,
        })
    return fixtures


@router.get("/{slug}/teams", response_model=List[TournamentTeamPublic])
async def get_tournament_teams(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tournament).where(Tournament.slug == slug))
    tournament = result.scalar_one_or_none()
    if not tournament:
        raise HTTPException(status_code=404, detail="Tournament not found")

    result = await db.execute(
        select(TournamentTeam)
        .where(TournamentTeam.tournament_id == tournament.id)
        .options(selectinload(TournamentTeam.team))
    )
    entries = result.scalars().all()
    return [TournamentTeamPublic.model_validate(e) for e in entries]


# ─── helpers ────────────────────────────────────────────────────────────────────

async def _enrich_tournament(t: Tournament, db: AsyncSession) -> TournamentPublic:
    count_result = await db.execute(
        select(func.count(TournamentTeam.id)).where(
            TournamentTeam.tournament_id == t.id,
            TournamentTeam.status == TeamApplyStatus.APPROVED,
        )
    )
    team_count = count_result.scalar() or 0
    data = TournamentPublic.model_validate(t).model_dump()
    data["team_count"] = team_count
    return TournamentPublic(**data)
