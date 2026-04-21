"""
Gully Stars — Database Models
Full relational schema for a grassroots sports management & social platform.
Sports: Cricket · Football · Basketball
Roles: Player · Captain · Organiser · Fan
"""

from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint, CheckConstraint,
    JSON, func
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.db.session import Base


def utcnow():
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class UserRole(str, PyEnum):
    PLAYER = "player"
    CAPTAIN = "captain"
    ORGANISER = "organiser"
    FAN = "fan"


class Sport(str, PyEnum):
    CRICKET = "cricket"
    FOOTBALL = "football"
    BASKETBALL = "basketball"


class TeamVisibility(str, PyEnum):
    PUBLIC = "public"
    INVITE_ONLY = "invite_only"


class MembershipStatus(str, PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RSVPStatus(str, PyEnum):
    GOING = "going"
    NOT_GOING = "not_going"
    MAYBE = "maybe"


class TournamentFormat(str, PyEnum):
    ROUND_ROBIN = "round_robin"
    BRACKET = "bracket"


class TournamentStatus(str, PyEnum):
    DRAFT = "draft"
    REGISTRATION = "registration"
    ACTIVE = "active"
    COMPLETED = "completed"


class TeamApplyStatus(str, PyEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class MatchStatus(str, PyEnum):
    SCHEDULED = "scheduled"
    LIVE = "live"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PostType(str, PyEnum):
    TEXT = "text"
    PHOTO = "photo"
    VIDEO = "video"


class ReactionType(str, PyEnum):
    FIRE = "fire"
    CLAP = "clap"
    HEART = "heart"
    TROPHY = "trophy"


class NotificationType(str, PyEnum):
    MATCH_RESULT = "match_result"
    TRAINING_REMINDER = "training_reminder"
    NEW_POST = "new_post"
    JOIN_REQUEST = "join_request"
    TEAM_APPROVED = "team_approved"
    TOURNAMENT_UPDATE = "tournament_update"


# ─────────────────────────────────────────────
# USERS
# ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.PLAYER)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500))
    bio: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    team_memberships: Mapped[List["TeamMember"]] = relationship("TeamMember", back_populates="user", foreign_keys="TeamMember.user_id")
    captained_teams: Mapped[List["Team"]] = relationship("Team", back_populates="captain", foreign_keys="Team.captain_id")
    training_rsvps: Mapped[List["TrainingRSVP"]] = relationship("TrainingRSVP", back_populates="user")
    match_rsvps: Mapped[List["MatchRSVP"]] = relationship("MatchRSVP", back_populates="user")
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="author")
    reactions: Mapped[List["Reaction"]] = relationship("Reaction", back_populates="user")
    notifications: Mapped[List["Notification"]] = relationship("Notification", back_populates="user")
    follows: Mapped[List["Follow"]] = relationship("Follow", back_populates="follower", foreign_keys="Follow.follower_id")
    player_stats: Mapped[List["PlayerStats"]] = relationship("PlayerStats", back_populates="user")
    organised_tournaments: Mapped[List["Tournament"]] = relationship("Tournament", back_populates="organiser")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="author")


# ─────────────────────────────────────────────
# TEAMS
# ─────────────────────────────────────────────

class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    sport: Mapped[Sport] = mapped_column(Enum(Sport), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))
    cover_url: Mapped[Optional[str]] = mapped_column(String(500))
    location: Mapped[Optional[str]] = mapped_column(String(100))
    visibility: Mapped[TeamVisibility] = mapped_column(Enum(TeamVisibility), default=TeamVisibility.PUBLIC)
    captain_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    captain: Mapped["User"] = relationship("User", back_populates="captained_teams", foreign_keys=[captain_id])
    members: Mapped[List["TeamMember"]] = relationship("TeamMember", back_populates="team")
    training_sessions: Mapped[List["TrainingSession"]] = relationship("TrainingSession", back_populates="team")
    matches: Mapped[List["Match"]] = relationship("Match", back_populates="team", foreign_keys="Match.team_id")
    posts: Mapped[List["Post"]] = relationship("Post", back_populates="team")
    follows: Mapped[List["Follow"]] = relationship("Follow", back_populates="team", foreign_keys="Follow.team_id")
    tournament_entries: Mapped[List["TournamentTeam"]] = relationship("TournamentTeam", back_populates="team")
    player_stats: Mapped[List["PlayerStats"]] = relationship("PlayerStats", back_populates="team")


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status: Mapped[MembershipStatus] = mapped_column(Enum(MembershipStatus), default=MembershipStatus.PENDING)
    jersey_number: Mapped[Optional[int]] = mapped_column(Integer)
    position: Mapped[Optional[str]] = mapped_column(String(50))
    joined_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="team_memberships", foreign_keys=[user_id])


# ─────────────────────────────────────────────
# TRAINING SESSIONS
# ─────────────────────────────────────────────

class TrainingSession(Base):
    __tablename__ = "training_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=90)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    team: Mapped["Team"] = relationship("Team", back_populates="training_sessions")
    rsvps: Mapped[List["TrainingRSVP"]] = relationship("TrainingRSVP", back_populates="session")


class TrainingRSVP(Base):
    __tablename__ = "training_rsvps"
    __table_args__ = (UniqueConstraint("session_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("training_sessions.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status: Mapped[RSVPStatus] = mapped_column(Enum(RSVPStatus), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    session: Mapped["TrainingSession"] = relationship("TrainingSession", back_populates="rsvps")
    user: Mapped["User"] = relationship("User", back_populates="training_rsvps")


# ─────────────────────────────────────────────
# MATCHES
# ─────────────────────────────────────────────

class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    opponent_name: Mapped[str] = mapped_column(String(100), nullable=False)
    opponent_team_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("teams.id"))
    sport: Mapped[Sport] = mapped_column(Enum(Sport), nullable=False)
    venue: Mapped[str] = mapped_column(String(200), nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), default=MatchStatus.SCHEDULED)

    # Result
    home_score: Mapped[Optional[int]] = mapped_column(Integer)
    away_score: Mapped[Optional[int]] = mapped_column(Integer)
    result_notes: Mapped[Optional[str]] = mapped_column(Text)
    result_submitted_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))

    tournament_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tournaments.id"))
    tournament_round: Mapped[Optional[int]] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    team: Mapped["Team"] = relationship("Team", back_populates="matches", foreign_keys=[team_id])
    rsvps: Mapped[List["MatchRSVP"]] = relationship("MatchRSVP", back_populates="match")
    tournament: Mapped[Optional["Tournament"]] = relationship("Tournament", back_populates="matches")


class MatchRSVP(Base):
    __tablename__ = "match_rsvps"
    __table_args__ = (UniqueConstraint("match_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    match_id: Mapped[int] = mapped_column(Integer, ForeignKey("matches.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    status: Mapped[RSVPStatus] = mapped_column(Enum(RSVPStatus), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    match: Mapped["Match"] = relationship("Match", back_populates="rsvps")
    user: Mapped["User"] = relationship("User", back_populates="match_rsvps")


# ─────────────────────────────────────────────
# TOURNAMENTS
# ─────────────────────────────────────────────

class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    sport: Mapped[Sport] = mapped_column(Enum(Sport), nullable=False)
    format: Mapped[TournamentFormat] = mapped_column(Enum(TournamentFormat), nullable=False)
    status: Mapped[TournamentStatus] = mapped_column(Enum(TournamentStatus), default=TournamentStatus.DRAFT)
    organiser_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[Optional[str]] = mapped_column(String(200))
    banner_url: Mapped[Optional[str]] = mapped_column(String(500))
    max_teams: Mapped[int] = mapped_column(Integer, default=16)
    registration_deadline: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    prize_info: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    organiser: Mapped["User"] = relationship("User", back_populates="organised_tournaments")
    participating_teams: Mapped[List["TournamentTeam"]] = relationship("TournamentTeam", back_populates="tournament")
    matches: Mapped[List["Match"]] = relationship("Match", back_populates="tournament")
    follows: Mapped[List["Follow"]] = relationship("Follow", back_populates="tournament", foreign_keys="Follow.tournament_id")


class TournamentTeam(Base):
    __tablename__ = "tournament_teams"
    __table_args__ = (UniqueConstraint("tournament_id", "team_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tournament_id: Mapped[int] = mapped_column(Integer, ForeignKey("tournaments.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    status: Mapped[TeamApplyStatus] = mapped_column(Enum(TeamApplyStatus), default=TeamApplyStatus.PENDING)

    # Round-robin standings
    played: Mapped[int] = mapped_column(Integer, default=0)
    won: Mapped[int] = mapped_column(Integer, default=0)
    drawn: Mapped[int] = mapped_column(Integer, default=0)
    lost: Mapped[int] = mapped_column(Integer, default=0)
    goals_for: Mapped[int] = mapped_column(Integer, default=0)
    goals_against: Mapped[int] = mapped_column(Integer, default=0)
    points: Mapped[int] = mapped_column(Integer, default=0)

    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    tournament: Mapped["Tournament"] = relationship("Tournament", back_populates="participating_teams")
    team: Mapped["Team"] = relationship("Team", back_populates="tournament_entries")


# ─────────────────────────────────────────────
# SOCIAL FEED
# ─────────────────────────────────────────────

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    post_type: Mapped[PostType] = mapped_column(Enum(PostType), default=PostType.TEXT)
    caption: Mapped[Optional[str]] = mapped_column(Text)
    media_url: Mapped[Optional[str]] = mapped_column(String(500))
    media_thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500))
    match_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("matches.id"))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    team: Mapped["Team"] = relationship("Team", back_populates="posts")
    author: Mapped["User"] = relationship("User", back_populates="posts")
    reactions: Mapped[List["Reaction"]] = relationship("Reaction", back_populates="post")
    comments: Mapped[List["Comment"]] = relationship("Comment", back_populates="post")


class Reaction(Base):
    __tablename__ = "reactions"
    __table_args__ = (UniqueConstraint("post_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    reaction_type: Mapped[ReactionType] = mapped_column(Enum(ReactionType), default=ReactionType.FIRE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    post: Mapped["Post"] = relationship("Post", back_populates="reactions")
    user: Mapped["User"] = relationship("User", back_populates="reactions")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(Integer, ForeignKey("posts.id"), nullable=False)
    author_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    post: Mapped["Post"] = relationship("Post", back_populates="comments")
    author: Mapped["User"] = relationship("User", back_populates="comments")


# ─────────────────────────────────────────────
# FOLLOWS
# ─────────────────────────────────────────────

class Follow(Base):
    """Polymorphic follow: user can follow a Team or Tournament."""
    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "team_id"),
        UniqueConstraint("follower_id", "tournament_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    follower_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    team_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("teams.id"))
    tournament_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("tournaments.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    follower: Mapped["User"] = relationship("User", back_populates="follows", foreign_keys=[follower_id])
    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="follows", foreign_keys=[team_id])
    tournament: Mapped[Optional["Tournament"]] = relationship("Tournament", back_populates="follows", foreign_keys=[tournament_id])


# ─────────────────────────────────────────────
# PLAYER STATS
# ─────────────────────────────────────────────

class PlayerStats(Base):
    """
    Sport-specific stats stored as a flexible JSONB column
    alongside strongly-typed common stats.

    Cricket:  wickets, runs, catches, matches_played, not_outs, batting_avg
    Football: goals, assists, clean_sheets, yellow_cards, red_cards
    Basketball: points, rebounds, assists, steals, blocks, three_pointers
    """
    __tablename__ = "player_stats"
    __table_args__ = (UniqueConstraint("user_id", "team_id", "sport"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    team_id: Mapped[int] = mapped_column(Integer, ForeignKey("teams.id"), nullable=False)
    sport: Mapped[Sport] = mapped_column(Enum(Sport), nullable=False)
    matches_played: Mapped[int] = mapped_column(Integer, default=0)

    # Sport-specific stats in JSONB for flexibility
    stats: Mapped[dict] = mapped_column(JSON, default=dict)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="player_stats")
    team: Mapped["Team"] = relationship("Team", back_populates="player_stats")


# ─────────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────────

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    notification_type: Mapped[NotificationType] = mapped_column(Enum(NotificationType), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[Optional[dict]] = mapped_column(JSON)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user: Mapped["User"] = relationship("User", back_populates="notifications")
