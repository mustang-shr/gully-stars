"""
Gully Stars — Pydantic V2 Schemas
All request/response models with strict validation.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from app.models.models import (
    UserRole, Sport, TeamVisibility, MembershipStatus,
    RSVPStatus, TournamentFormat, TournamentStatus, TeamApplyStatus,
    MatchStatus, PostType, ReactionType, NotificationType
)


# ─── SHARED ────────────────────────────────────────────────────────────────────

class TimestampMixin(BaseModel):
    created_at: datetime
    updated_at: Optional[datetime] = None


# ─── AUTH ──────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=6, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRole = UserRole.PLAYER


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserPublic"


# ─── USERS ─────────────────────────────────────────────────────────────────────

class UserPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: UserRole
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    created_at: datetime


class UserProfile(UserPublic):
    email: str
    is_active: bool
    is_verified: bool


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None


# ─── TEAMS ─────────────────────────────────────────────────────────────────────

class CreateTeamRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    sport: Sport
    description: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=100)
    visibility: TeamVisibility = TeamVisibility.PUBLIC


class TeamPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    sport: Sport
    description: Optional[str] = None
    logo_url: Optional[str] = None
    cover_url: Optional[str] = None
    location: Optional[str] = None
    visibility: TeamVisibility
    captain_id: int
    created_at: datetime


class TeamDetail(TeamPublic):
    captain: UserPublic
    member_count: int = 0
    follower_count: int = 0


class TeamMemberPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user: UserPublic
    status: MembershipStatus
    jersey_number: Optional[int] = None
    position: Optional[str] = None
    joined_at: Optional[datetime] = None


class JoinTeamRequest(BaseModel):
    message: Optional[str] = None


class UpdateMembershipRequest(BaseModel):
    status: MembershipStatus


# ─── TRAINING ──────────────────────────────────────────────────────────────────

class CreateTrainingRequest(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = None
    location: str = Field(..., min_length=2, max_length=200)
    scheduled_at: datetime
    duration_minutes: int = Field(90, ge=15, le=480)


class TrainingSessionPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    title: str
    description: Optional[str] = None
    location: str
    scheduled_at: datetime
    duration_minutes: int
    is_cancelled: bool
    going_count: int = 0
    not_going_count: int = 0
    maybe_count: int = 0
    my_rsvp: Optional[RSVPStatus] = None
    created_at: datetime


class RSVPRequest(BaseModel):
    status: RSVPStatus


# ─── MATCHES ───────────────────────────────────────────────────────────────────

class CreateMatchRequest(BaseModel):
    opponent_name: str = Field(..., min_length=2, max_length=100)
    sport: Sport
    venue: str = Field(..., min_length=2, max_length=200)
    scheduled_at: datetime
    tournament_id: Optional[int] = None


class SubmitResultRequest(BaseModel):
    home_score: int = Field(..., ge=0)
    away_score: int = Field(..., ge=0)
    result_notes: Optional[str] = None


class MatchPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    opponent_name: str
    sport: Sport
    venue: str
    scheduled_at: datetime
    status: MatchStatus
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    result_notes: Optional[str] = None
    tournament_id: Optional[int] = None
    tournament_round: Optional[int] = None
    going_count: int = 0
    my_rsvp: Optional[RSVPStatus] = None
    created_at: datetime


# ─── TOURNAMENTS ───────────────────────────────────────────────────────────────

class CreateTournamentRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    sport: Sport
    format: TournamentFormat
    description: Optional[str] = None
    location: Optional[str] = None
    max_teams: int = Field(16, ge=2, le=64)
    registration_deadline: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    prize_info: Optional[str] = None


class TournamentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    sport: Sport
    format: TournamentFormat
    status: TournamentStatus
    organiser_id: int
    description: Optional[str] = None
    location: Optional[str] = None
    banner_url: Optional[str] = None
    max_teams: int
    registration_deadline: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    prize_info: Optional[str] = None
    team_count: int = 0
    created_at: datetime


class TournamentStanding(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team: TeamPublic
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int


class TournamentTeamPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team: TeamPublic
    status: TeamApplyStatus
    played: int
    won: int
    drawn: int
    lost: int
    points: int
    applied_at: datetime


class UpdateTournamentStatusRequest(BaseModel):
    status: TournamentStatus


class ApproveTeamRequest(BaseModel):
    status: TeamApplyStatus


# ─── SOCIAL FEED ───────────────────────────────────────────────────────────────

class CreatePostRequest(BaseModel):
    caption: Optional[str] = Field(None, max_length=2000)
    post_type: PostType = PostType.TEXT
    media_url: Optional[str] = None
    match_id: Optional[int] = None


class PostPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    author: UserPublic
    post_type: PostType
    caption: Optional[str] = None
    media_url: Optional[str] = None
    media_thumbnail_url: Optional[str] = None
    match_id: Optional[int] = None
    reaction_counts: Dict[str, int] = {}
    comment_count: int = 0
    my_reaction: Optional[ReactionType] = None
    created_at: datetime


class ReactRequest(BaseModel):
    reaction_type: ReactionType


class CreateCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)


class CommentPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author: UserPublic
    content: str
    created_at: datetime


# ─── PLAYER STATS ──────────────────────────────────────────────────────────────

class UpdateStatsRequest(BaseModel):
    stats: Dict[str, Any]


class PlayerStatsPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user: UserPublic
    team: TeamPublic
    sport: Sport
    matches_played: int
    stats: Dict[str, Any]
    updated_at: datetime


# ─── NOTIFICATIONS ─────────────────────────────────────────────────────────────

class NotificationPublic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    notification_type: NotificationType
    title: str
    body: str
    data: Optional[Dict[str, Any]] = None
    is_read: bool
    created_at: datetime


# ─── PAGINATION ────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
