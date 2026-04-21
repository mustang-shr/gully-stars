# 🏆 Gully Stars

> **Grassroots sports teams finally have a home.**
> Team management · Tournaments · Social feed · Player stats
> Built for cricket, football & basketball — designed for the streets.

---

## Demo

| Role | Email | Password |
|------|-------|----------|
| Captain (Rohit Sharma) | `captain@gully.dev` | `gully123` |
| Player (Virat Kohli) | `player@gully.dev` | `gully123` |
| Organiser (MS Dhoni) | `org@gully.dev` | `gully123` |
| Fan | `fan@gully.dev` | `gully123` |

Pre-seeded: **Gully Tigers** (cricket) · **Street Kings FC** (football) · **Court Hustlers** (basketball)
Pre-seeded tournament: **Diwali Cup 2024** at `/league/diwali-cup-2024`

---

## ⚡ 5-Minute Local Setup

### Prerequisites
- **Docker & Docker Compose** (v2.20+) — [install](https://docs.docker.com/get-docker/)
- OR: Python 3.12+, Node 20+, PostgreSQL 16+

---

### Option A — Docker (Recommended, one command)

```bash
git clone <repo-url> gully-stars
cd gully-stars

# Copy env (already configured for Docker)
cp backend/.env.example backend/.env

# Start everything — DB + backend (auto-seeds) + frontend
docker compose up --build

# App is live at:
#   Frontend:  http://localhost:5173
#   API docs:  http://localhost:8000/docs
#   API:       http://localhost:8000/api/v1
```

That's it. Docker starts Postgres, runs the seed script automatically, and boots both services. Wait ~30 seconds for the first build.

---

### Option B — Local (without Docker)

#### 1. Prerequisites
```bash
# Verify versions
python --version   # 3.12+
node --version     # 20+
psql --version     # 16+
```

#### 2. Database
```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE USER gullyuser WITH PASSWORD 'gullypass';"
psql -U postgres -c "CREATE DATABASE gullydb OWNER gullyuser;"
```

#### 3. Backend
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# Install dependencies (single command)
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env if your DB credentials differ

# Seed database (creates tables + 4 demo accounts + sample data)
python seed.py

# Start API server
uvicorn app.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

#### 4. Frontend
```bash
# In a new terminal
cd frontend

# Install dependencies (single command)
npm install

# Start dev server
npm run dev
# App: http://localhost:5173
```

---

## Architecture & Stack

### Why this stack?

**Backend: FastAPI + Python 3.12**
FastAPI is async-native, delivers Node.js/Go-comparable performance through Python's asyncio event loop, and generates OpenAPI docs automatically — ideal for a time-constrained build where correctness needs to be verifiable instantly. Pydantic V2 gives compile-time-like schema validation on every request.

**Database: PostgreSQL 16 + async SQLAlchemy 2.0**
Relational integrity is essential here — tournament standings, team rosters, RSVP uniqueness constraints. The `postgresql+asyncpg://` driver (never `postgresql://`) ensures every DB operation is truly non-blocking. `selectinload` prevents N+1 queries on relationship traversal. Player stats use a JSONB column per `(user, team, sport)` tuple — sport-specific fields (wickets vs goals vs rebounds) without three separate tables or schema migrations for every stat category.

**Frontend: React 18 + Vite + Zustand + Tailwind**
Vite's HMR is instant. Zustand keeps auth state in <20 lines. Tailwind + a custom design system built around an 390px max-width constraint makes every screen genuinely mobile-first, not just mobile-responsive.

**Auth: JWT (HS256) + bcrypt**
Stateless, no Redis dependency for MVP. Tokens expire in 7 days. The mock-auth approach means zero OAuth complexity while still being production-portable (swap `create_access_token` for a real provider later).

---

## System Architecture

```
┌────────────────────────────────────────────────────────────┐
│  React 18 + Vite  (390px mobile-first)                     │
│  Zustand auth · Axios + JWT interceptor · Tailwind CSS     │
└──────────────────────┬─────────────────────────────────────┘
                       │  HTTP / REST
┌──────────────────────▼─────────────────────────────────────┐
│  FastAPI 0.115  (async, 50 routes)                         │
│  Pydantic V2 validation · JWT Bearer auth                  │
│  Routers: auth · users · teams · training · matches        │
│           tournaments · feed · notifications               │
└──────────────────────┬─────────────────────────────────────┘
                       │  asyncpg (non-blocking)
┌──────────────────────▼─────────────────────────────────────┐
│  PostgreSQL 16                                              │
│  16 tables · JSONB player stats · UUID slugs               │
│  Foreign key integrity · UniqueConstraints on RSVPs        │
└────────────────────────────────────────────────────────────┘
```

### Data Model (16 tables)
```
users ──── team_members ──── teams
                │                └── training_sessions ── training_rsvps
                │                └── matches ──────────── match_rsvps
                │                └── posts ─────────────── reactions
                │                                      └── comments
                │                └── player_stats (JSONB)
                │                └── tournament_teams ── tournaments
follows (user→team or user→tournament)
notifications
```

### Tournament Fixture Algorithm
- **Round-robin**: Generates exactly `N*(N-1)/2` fixtures — every team plays every other team once. Same algorithm as FIFA/ICC group stages.
- **Single-elimination bracket**: Generates `⌈log₂(N)⌉` rounds, pairs teams by seed for Round 1. Subsequent rounds are added as match results are submitted.
- Live standings recalculated from match results — points, goal difference, wins.

---

## API Reference

Full interactive docs at **`http://localhost:8000/docs`** (Swagger UI).

Key endpoints:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/v1/auth/register` | Create account (player/captain/organiser/fan) |
| POST | `/api/v1/auth/login` | Get JWT token |
| GET | `/api/v1/feed/` | Home feed (followed teams' posts) |
| POST | `/api/v1/teams/` | Create team (captain role) |
| POST | `/api/v1/teams/{slug}/join` | Join request |
| POST | `/api/v1/teams/{slug}/training/` | Schedule training session |
| POST | `/api/v1/teams/{slug}/training/{id}/rsvp` | Going/Maybe/Not going |
| POST | `/api/v1/teams/{slug}/matches/{id}/rsvp` | Availability for match |
| POST | `/api/v1/teams/{slug}/matches/{id}/result` | Submit final score |
| POST | `/api/v1/tournaments/` | Create tournament (organiser) |
| POST | `/api/v1/tournaments/{slug}/generate-fixtures` | Auto-generate all fixtures |
| GET | `/api/v1/tournaments/{slug}/standings` | Live standings table |
| GET | `/api/v1/tournaments/{slug}/fixtures` | All fixtures by round |
| POST | `/api/v1/posts/{id}/react` | React (🔥/👏/❤️/🏆), toggleable |

---

## Key Screens

| Screen | Route | Notes |
|--------|-------|-------|
| Home Feed | `/` | Posts from followed teams, reactions, comments |
| Team Profile | `/teams/:slug` | Squad, fixtures, training, feed tabs |
| Training Session | `/teams/:slug/training/:id` | Live RSVP counts |
| Match Detail | `/teams/:slug/matches/:id` | RSVP + captain score entry |
| Tournament | `/tournaments/:slug` | Overview, standings, fixtures, teams |
| Tournament Bracket | `/tournaments/:slug/bracket` | Visual bracket / round-robin table |
| Player Profile | `/players/:username` | Sport-specific stats cards |
| Public League | `/league/:slug` | Zero-auth shareable standings URL |
| Create Team | `/teams/new` | Sport selection + visibility |
| Onboarding | `/register` | 2-step: role selection → details |

---

## Project Structure

```
gully-stars/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── deps.py              # JWT dependency injection
│   │   │   └── endpoints/
│   │   │       ├── auth.py          # register + login
│   │   │       ├── users.py         # profile, stats
│   │   │       ├── teams.py         # CRUD + roster + follow
│   │   │       ├── training.py      # sessions + RSVP
│   │   │       ├── matches.py       # RSVP + results + player stats
│   │   │       ├── tournaments.py   # full lifecycle + fixture gen
│   │   │       └── feed.py          # home feed + posts + reactions
│   │   ├── core/
│   │   │   ├── config.py            # pydantic-settings env config
│   │   │   └── security.py          # JWT + bcrypt
│   │   ├── db/session.py            # async engine + session factory
│   │   ├── models/models.py         # 16 SQLAlchemy ORM models
│   │   ├── schemas/schemas.py       # all Pydantic V2 request/response
│   │   └── main.py                  # FastAPI app entrypoint
│   ├── alembic/                     # database migrations
│   ├── seed.py                      # demo data seeder
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── pages/                   # all page components
│       ├── components/              # feed, team, tournament UI
│       ├── stores/authStore.ts      # Zustand auth state
│       └── utils/api.ts             # axios + JWT interceptor
├── docker-compose.yml
└── README.md
```

---

## Sport-Specific Stats (JSONB)

Stats are stored as flexible JSON per `(user, team, sport)`:

```json
// Cricket
{ "runs": 540, "wickets": 23, "catches": 12, "batting_avg": 33.75, "economy": 6.2 }

// Football
{ "goals": 12, "assists": 8, "yellow_cards": 2, "shots_on_target": 34 }

// Basketball
{ "points": 280, "rebounds": 120, "assists": 45, "steals": 30, "three_pointers": 42 }
```

---

## What's Next

1. **Real-time presence** — WebSocket layer for live training RSVP counts and match score updates (FastAPI WebSockets + Redis pub/sub)
2. **Push notifications** — Firebase Cloud Messaging for training reminders, match results
3. **Media uploads** — Direct-to-S3 presigned URLs for post photos/videos
4. **AI match summary** — Auto-generate post-match recap from score + player stats using Claude API
5. **Double-elimination bracket** — Second chance rounds for tournament losers
6. **Geo search** — PostGIS extension for "find teams near me"
7. **Rate limiting** — Redis-backed sliding window on auth endpoints

---

## How AI Was Used

Claude (claude-sonnet-4) was used to architect the complete database schema (16 tables, relationship mapping, JSONB stats design), generate the production-grade async FastAPI backend including all endpoint logic, dependency injection patterns, and the tournament fixture generation algorithm. Claude also wrote all Pydantic V2 schemas and the full React/TypeScript frontend. Every output was reviewed, debugged, and adapted — particularly the tournament standings auto-update logic, the UPSERT RSVP pattern, and the async SQLAlchemy session management. AI accelerated the build by approximately 75%; engineering judgment was applied throughout to make correctness and architectural decisions.

---

*Gully Stars · Built for Flavar Founding Engineer Challenge · 72 hours*
