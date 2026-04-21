from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_token
from app.db.session import get_db
from app.models.models import User, UserRole

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


async def get_current_captain(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.CAPTAIN, UserRole.ORGANISER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Captain or Organiser role required",
        )
    return current_user


async def get_current_organiser(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ORGANISER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organiser role required",
        )
    return current_user


def optional_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
):
    """Returns user if authenticated, None if not (for public endpoints)."""
    return credentials
