"""
Gully Stars — Seed Script
Creates demo accounts and sample data for all 4 roles.

Default accounts:
  captain@gully.dev  / gully123  (Captain)
  player@gully.dev   / gully123  (Player)
  org@gully.dev      / gully123  (Organiser)
  fan@gully.dev      / gully123  (Fan)
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, ".")

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import Base
from app.models.models import (
    User, Team, TeamMember, TrainingSession, TrainingRSVP, Match,
    MatchRSVP, Tournament, TournamentTeam, Post, PlayerStats, Follow,
    UserRole, Sport, TeamVisibility, MembershipStatus, RSVPStatus,
    TournamentFormat, TournamentStatus, TeamApplyStatus, MatchStatus,
    PostType,
)

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


def now():
    return datetime.now(timezone.utc)


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        print("🌱 Seeding Gully Stars...")

        # ─── Users ────────────────────────────────────────────────
        captain = User(
            email="captain@gully.dev",
            username="rohit_captain",
            full_name="Rohit Sharma",
            hashed_password=get_password_hash("gully123"),
            role=UserRole.CAPTAIN,
            bio="Captain of Gully Tigers FC 🏏",
            location="Mumbai",
            is_active=True,
        )
        player = User(
            email="player@gully.dev",
            username="virat_player",
            full_name="Virat Kohli",
            hashed_password=get_password_hash("gully123"),
            role=UserRole.PLAYER,
            bio="Striker. Goals = everything.",
            location="Delhi",
            is_active=True,
        )
        organiser = User(
            email="org@gully.dev",
            username="msd_organiser",
            full_name="MS Dhoni",
            hashed_password=get_password_hash("gully123"),
            role=UserRole.ORGANISER,
            bio="Organiser · Finisher · Legend",
            location="Ranchi",
            is_active=True,
            is_verified=True,
        )
        fan = User(
            email="fan@gully.dev",
            username="sachin_fan",
            full_name="Sachin Fan",
            hashed_password=get_password_hash("gully123"),
            role=UserRole.FAN,
            bio="Cricket fan since 1989 🏏",
            location="Pune",
            is_active=True,
        )

        for u in [captain, player, organiser, fan]:
            db.add(u)
        await db.flush()
        print(f"  ✓ 4 users created")

        # ─── Teams ────────────────────────────────────────────────
        cricket_team = Team(
            name="Gully Tigers",
            slug="gully-tigers",
            sport=Sport.CRICKET,
            description="Street cricket warriors from Mumbai's lanes.",
            location="Mumbai",
            visibility=TeamVisibility.PUBLIC,
            captain_id=captain.id,
        )
        football_team = Team(
            name="Street Kings FC",
            slug="street-kings-fc",
            sport=Sport.FOOTBALL,
            description="We play hard, we play fair.",
            location="Delhi",
            visibility=TeamVisibility.PUBLIC,
            captain_id=captain.id,
        )
        basketball_team = Team(
            name="Court Hustlers",
            slug="court-hustlers",
            sport=Sport.BASKETBALL,
            description="Hoops all day, every day.",
            location="Bangalore",
            visibility=TeamVisibility.PUBLIC,
            captain_id=captain.id,
        )
        for t in [cricket_team, football_team, basketball_team]:
            db.add(t)
        await db.flush()
        print(f"  ✓ 3 teams created (cricket, football, basketball)")

        # ─── Team members ─────────────────────────────────────────
        members = [
            TeamMember(team_id=cricket_team.id, user_id=captain.id, status=MembershipStatus.APPROVED, jersey_number=7, position="Batsman"),
            TeamMember(team_id=cricket_team.id, user_id=player.id, status=MembershipStatus.APPROVED, jersey_number=18, position="All-rounder"),
            TeamMember(team_id=football_team.id, user_id=captain.id, status=MembershipStatus.APPROVED, jersey_number=10, position="Midfielder"),
            TeamMember(team_id=football_team.id, user_id=player.id, status=MembershipStatus.APPROVED, jersey_number=9, position="Striker"),
            TeamMember(team_id=basketball_team.id, user_id=captain.id, status=MembershipStatus.APPROVED, jersey_number=23, position="Point Guard"),
        ]
        for m in members:
            db.add(m)
        await db.flush()

        # Fan follows teams
        fan_follows = [
            Follow(follower_id=fan.id, team_id=cricket_team.id),
            Follow(follower_id=fan.id, team_id=football_team.id),
            Follow(follower_id=player.id, team_id=cricket_team.id),
        ]
        for f in fan_follows:
            db.add(f)
        await db.flush()
        print(f"  ✓ Team memberships & follows seeded")

        # ─── Training sessions ────────────────────────────────────
        t1 = TrainingSession(
            team_id=cricket_team.id,
            title="Pre-match nets session",
            description="Focus on batting and fielding drills",
            location="Shivaji Park, Mumbai",
            scheduled_at=now() + timedelta(days=2, hours=6),
            duration_minutes=120,
        )
        t2 = TrainingSession(
            team_id=football_team.id,
            title="Tactical Friday",
            description="Set pieces + defensive shape",
            location="Nehru Stadium, Delhi",
            scheduled_at=now() + timedelta(days=3, hours=7),
            duration_minutes=90,
        )
        for t in [t1, t2]:
            db.add(t)
        await db.flush()

        # RSVPs for training
        rsvps = [
            TrainingRSVP(session_id=t1.id, user_id=captain.id, status=RSVPStatus.GOING),
            TrainingRSVP(session_id=t1.id, user_id=player.id, status=RSVPStatus.GOING),
            TrainingRSVP(session_id=t2.id, user_id=captain.id, status=RSVPStatus.GOING),
            TrainingRSVP(session_id=t2.id, user_id=player.id, status=RSVPStatus.MAYBE),
        ]
        for r in rsvps:
            db.add(r)
        await db.flush()
        print(f"  ✓ Training sessions & RSVPs seeded")

        # ─── Matches ──────────────────────────────────────────────
        m1 = Match(
            team_id=cricket_team.id,
            opponent_name="Bandra Blasters",
            sport=Sport.CRICKET,
            venue="Azad Maidan, Mumbai",
            scheduled_at=now() + timedelta(days=5),
            status=MatchStatus.SCHEDULED,
        )
        m2 = Match(
            team_id=cricket_team.id,
            opponent_name="Dadar Dragons",
            sport=Sport.CRICKET,
            venue="Shivaji Park",
            scheduled_at=now() - timedelta(days=7),
            status=MatchStatus.COMPLETED,
            home_score=187,
            away_score=162,
            result_notes="Won by 25 runs. Virat top scored with 76*",
            result_submitted_by=captain.id,
        )
        m3 = Match(
            team_id=football_team.id,
            opponent_name="Paschim Vihar Pumas",
            sport=Sport.FOOTBALL,
            venue="Yamuna Sports Complex",
            scheduled_at=now() + timedelta(days=4),
            status=MatchStatus.SCHEDULED,
        )
        for m in [m1, m2, m3]:
            db.add(m)
        await db.flush()

        match_rsvps = [
            MatchRSVP(match_id=m1.id, user_id=captain.id, status=RSVPStatus.GOING),
            MatchRSVP(match_id=m1.id, user_id=player.id, status=RSVPStatus.GOING),
            MatchRSVP(match_id=m3.id, user_id=player.id, status=RSVPStatus.MAYBE),
        ]
        for r in match_rsvps:
            db.add(r)
        await db.flush()
        print(f"  ✓ Matches & RSVPs seeded")

        # ─── Player stats ─────────────────────────────────────────
        cricket_stats = PlayerStats(
            user_id=player.id,
            team_id=cricket_team.id,
            sport=Sport.CRICKET,
            matches_played=12,
            stats={
                "runs": 540,
                "wickets": 8,
                "catches": 11,
                "batting_avg": 45.0,
                "economy": 7.2,
                "not_outs": 3,
                "highest_score": 76,
            },
        )
        football_stats = PlayerStats(
            user_id=player.id,
            team_id=football_team.id,
            sport=Sport.FOOTBALL,
            matches_played=10,
            stats={
                "goals": 12,
                "assists": 5,
                "yellow_cards": 1,
                "red_cards": 0,
                "shots_on_target": 28,
            },
        )
        for s in [cricket_stats, football_stats]:
            db.add(s)
        await db.flush()
        print(f"  ✓ Player stats seeded")

        # ─── Tournament ───────────────────────────────────────────
        tournament = Tournament(
            name="Diwali Cup 2024",
            slug="diwali-cup-2024",
            sport=Sport.CRICKET,
            format=TournamentFormat.ROUND_ROBIN,
            status=TournamentStatus.REGISTRATION,
            organiser_id=organiser.id,
            description="Annual street cricket championship. 8 teams. Winner takes all.",
            location="Azad Maidan, Mumbai",
            max_teams=8,
            start_date=now() + timedelta(days=14),
            end_date=now() + timedelta(days=21),
            prize_info="Trophy + ₹25,000 cash prize for winners",
        )
        db.add(tournament)
        await db.flush()

        # Two teams applied & approved
        tt1 = TournamentTeam(
            tournament_id=tournament.id,
            team_id=cricket_team.id,
            status=TeamApplyStatus.APPROVED,
            played=2, won=1, drawn=1, lost=0,
            goals_for=320, goals_against=285, points=4,
        )
        db.add(tt1)
        await db.flush()

        # Tournament follow
        t_follow = Follow(follower_id=fan.id, tournament_id=tournament.id)
        db.add(t_follow)
        await db.flush()
        print(f"  ✓ Tournament seeded")

        # ─── Social posts ─────────────────────────────────────────
        post1 = Post(
            team_id=cricket_team.id,
            author_id=captain.id,
            post_type=PostType.TEXT,
            caption="🔥 What a win yesterday! Virat played an absolute blinder. 76 not out! Next match on Sunday — everyone confirm availability 👇",
        )
        post2 = Post(
            team_id=cricket_team.id,
            author_id=captain.id,
            post_type=PostType.TEXT,
            caption="Training at Shivaji Park this Thursday 6am. Mandatory for everyone. We have the Diwali Cup coming up — let's be ready 💪🏏",
        )
        post3 = Post(
            team_id=football_team.id,
            author_id=captain.id,
            post_type=PostType.TEXT,
            caption="Street Kings FC vs Paschim Vihar Pumas this Saturday! Come support the boys at Yamuna Sports Complex ⚽🔥",
        )
        for p in [post1, post2, post3]:
            db.add(p)
        await db.flush()

        # Reactions
        from app.models.models import Reaction, ReactionType
        reactions = [
            Reaction(post_id=post1.id, user_id=player.id, reaction_type=ReactionType.FIRE),
            Reaction(post_id=post1.id, user_id=fan.id, reaction_type=ReactionType.TROPHY),
            Reaction(post_id=post2.id, user_id=player.id, reaction_type=ReactionType.CLAP),
            Reaction(post_id=post3.id, user_id=fan.id, reaction_type=ReactionType.FIRE),
        ]
        for r in reactions:
            db.add(r)
        await db.flush()
        print(f"  ✓ Posts & reactions seeded")

        await db.commit()

    print("\n✅ Seed complete!")
    print("\n📋 Demo Accounts:")
    print("  captain@gully.dev  / gully123  →  Captain (Rohit Sharma)")
    print("  player@gully.dev   / gully123  →  Player  (Virat Kohli)")
    print("  org@gully.dev      / gully123  →  Organiser (MS Dhoni)")
    print("  fan@gully.dev      / gully123  →  Fan (Sachin Fan)")
    print("\n🏏 Teams:  gully-tigers · street-kings-fc · court-hustlers")
    print("🏆 Tournament: diwali-cup-2024")


if __name__ == "__main__":
    asyncio.run(seed())
