"""
Social Feed Endpoints
- Team posts (photos, videos, text from captains)
- Home feed scoped to followed teams
- Reactions (fire/clap/heart/trophy) — one per user per post, changeable
- Comments
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import (
    Team, Post, Reaction, Comment, Follow, User, UserRole,
    ReactionType, PostType
)
from app.schemas.schemas import (
    CreatePostRequest, PostPublic, ReactRequest,
    CreateCommentRequest, CommentPublic, UserPublic
)
from app.api.v1.deps import get_current_user

router = APIRouter(tags=["feed"])


# ─────────────────────────────────────────────────────────────────
# HOME FEED — posts from followed teams, paginated
# ─────────────────────────────────────────────────────────────────

@router.get("/feed/", response_model=List[PostPublic])
async def get_home_feed(
    limit: int = Query(20, le=50),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get team IDs the user follows
    follows_result = await db.execute(
        select(Follow.team_id).where(
            Follow.follower_id == current_user.id,
            Follow.team_id.isnot(None),
        )
    )
    followed_team_ids = [row[0] for row in follows_result.fetchall()]

    # Also include teams the user is a member of
    from app.models.models import TeamMember, MembershipStatus
    member_result = await db.execute(
        select(TeamMember.team_id).where(
            TeamMember.user_id == current_user.id,
            TeamMember.status == MembershipStatus.APPROVED,
        )
    )
    member_team_ids = [row[0] for row in member_result.fetchall()]

    all_team_ids = list(set(followed_team_ids + member_team_ids))
    if not all_team_ids:
        return []

    result = await db.execute(
        select(Post)
        .where(Post.team_id.in_(all_team_ids), Post.is_deleted == False)
        .options(selectinload(Post.author))
        .order_by(Post.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    posts = result.scalars().all()
    return [await _enrich_post(p, current_user.id, db) for p in posts]


# ─────────────────────────────────────────────────────────────────
# TEAM POSTS
# ─────────────────────────────────────────────────────────────────

@router.post("/teams/{slug}/posts/", response_model=PostPublic, status_code=status.HTTP_201_CREATED)
async def create_post(
    slug: str,
    payload: CreatePostRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Team).where(Team.slug == slug, Team.is_active == True))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    if team.captain_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only captain can post on behalf of the team")

    post = Post(
        team_id=team.id,
        author_id=current_user.id,
        post_type=payload.post_type,
        caption=payload.caption,
        media_url=payload.media_url,
        match_id=payload.match_id,
    )
    db.add(post)
    await db.flush()
    await db.refresh(post)

    # Eager load author
    await db.execute(select(Post).where(Post.id == post.id).options(selectinload(Post.author)))
    result2 = await db.execute(
        select(Post).where(Post.id == post.id).options(selectinload(Post.author))
    )
    post = result2.scalar_one()
    return await _enrich_post(post, current_user.id, db)


@router.get("/teams/{slug}/posts/", response_model=List[PostPublic])
async def get_team_posts(
    slug: str,
    limit: int = Query(20, le=50),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Team).where(Team.slug == slug, Team.is_active == True))
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    result = await db.execute(
        select(Post)
        .where(Post.team_id == team.id, Post.is_deleted == False)
        .options(selectinload(Post.author))
        .order_by(Post.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    posts = result.scalars().all()
    return [await _enrich_post(p, current_user.id, db) for p in posts]


@router.get("/posts/{post_id}", response_model=PostPublic)
async def get_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Post)
        .where(Post.id == post_id, Post.is_deleted == False)
        .options(selectinload(Post.author))
    )
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return await _enrich_post(post, current_user.id, db)


@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your post")
    post.is_deleted = True
    db.add(post)
    return {"message": "Post deleted"}


# ─────────────────────────────────────────────────────────────────
# REACTIONS
# ─────────────────────────────────────────────────────────────────

@router.post("/posts/{post_id}/react")
async def react_to_post(
    post_id: int,
    payload: ReactRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Post).where(Post.id == post_id, Post.is_deleted == False))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    existing = await db.execute(
        select(Reaction).where(Reaction.post_id == post_id, Reaction.user_id == current_user.id)
    )
    reaction = existing.scalar_one_or_none()
    if reaction:
        if reaction.reaction_type == payload.reaction_type:
            # Toggle off
            await db.delete(reaction)
            return {"message": "Reaction removed"}
        reaction.reaction_type = payload.reaction_type
    else:
        reaction = Reaction(
            post_id=post_id,
            user_id=current_user.id,
            reaction_type=payload.reaction_type,
        )
        db.add(reaction)
    return {"message": "Reaction saved", "type": payload.reaction_type}


# ─────────────────────────────────────────────────────────────────
# COMMENTS
# ─────────────────────────────────────────────────────────────────

@router.post("/posts/{post_id}/comments/", response_model=CommentPublic, status_code=201)
async def add_comment(
    post_id: int,
    payload: CreateCommentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Post).where(Post.id == post_id, Post.is_deleted == False))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Post not found")

    comment = Comment(
        post_id=post_id,
        author_id=current_user.id,
        content=payload.content,
    )
    db.add(comment)
    await db.flush()

    result = await db.execute(
        select(Comment)
        .where(Comment.id == comment.id)
        .options(selectinload(Comment.author))
    )
    comment = result.scalar_one()
    return CommentPublic(
        id=comment.id,
        author=UserPublic.model_validate(comment.author),
        content=comment.content,
        created_at=comment.created_at,
    )


@router.get("/posts/{post_id}/comments/", response_model=List[CommentPublic])
async def get_comments(
    post_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Comment)
        .where(Comment.post_id == post_id, Comment.is_deleted == False)
        .options(selectinload(Comment.author))
        .order_by(Comment.created_at.asc())
    )
    comments = result.scalars().all()
    return [
        CommentPublic(
            id=c.id,
            author=UserPublic.model_validate(c.author),
            content=c.content,
            created_at=c.created_at,
        )
        for c in comments
    ]


# ─────────────────────────────────────────────────────────────────
# NOTIFICATIONS
# ─────────────────────────────────────────────────────────────────

@router.get("/notifications/", response_model=List[dict])
async def get_notifications(
    limit: int = Query(20, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.models import Notification
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    notifs = result.scalars().all()
    return [
        {
            "id": n.id,
            "type": n.notification_type,
            "title": n.title,
            "body": n.body,
            "data": n.data,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat(),
        }
        for n in notifs
    ]


@router.post("/notifications/{notif_id}/read")
async def mark_read(
    notif_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.models import Notification
    result = await db.execute(
        select(Notification).where(
            Notification.id == notif_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if notif:
        notif.is_read = True
        db.add(notif)
    return {"message": "Marked as read"}


# ─────────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────────

async def _enrich_post(post: Post, user_id: int, db: AsyncSession) -> PostPublic:
    # Reaction counts
    reactions_result = await db.execute(
        select(Reaction).where(Reaction.post_id == post.id)
    )
    all_reactions = reactions_result.scalars().all()

    reaction_counts = {}
    my_reaction = None
    for r in all_reactions:
        key = r.reaction_type.value if hasattr(r.reaction_type, "value") else r.reaction_type
        reaction_counts[key] = reaction_counts.get(key, 0) + 1
        if r.user_id == user_id:
            my_reaction = r.reaction_type

    # Comment count
    comment_count_result = await db.execute(
        select(func.count(Comment.id)).where(
            Comment.post_id == post.id,
            Comment.is_deleted == False,
        )
    )
    comment_count = comment_count_result.scalar() or 0

    return PostPublic(
        id=post.id,
        team_id=post.team_id,
        author=UserPublic.model_validate(post.author),
        post_type=post.post_type,
        caption=post.caption,
        media_url=post.media_url,
        media_thumbnail_url=post.media_thumbnail_url,
        match_id=post.match_id,
        reaction_counts=reaction_counts,
        comment_count=comment_count,
        my_reaction=my_reaction,
        created_at=post.created_at,
    )
