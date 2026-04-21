import re
import random
import string
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select


def _base_slug(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:80]


def _suffix() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=5))


async def make_team_slug(name: str, db: AsyncSession) -> str:
    from app.models.models import Team
    base = _base_slug(name)
    slug = base
    result = await db.execute(select(Team).where(Team.slug == slug))
    if result.scalar_one_or_none():
        slug = f"{base}-{_suffix()}"
    return slug


async def make_tournament_slug(name: str, db: AsyncSession) -> str:
    from app.models.models import Tournament
    base = _base_slug(name)
    slug = base
    result = await db.execute(select(Tournament).where(Tournament.slug == slug))
    if result.scalar_one_or_none():
        slug = f"{base}-{_suffix()}"
    return slug


def slugify(text: str) -> str:
    return _base_slug(text)
