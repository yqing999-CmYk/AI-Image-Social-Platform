from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.topic import Topic
from app.models.post import Post, PostLike, VoteType
from app.models.user import User
from app.schemas.post import PostCreate, PostPublic, PostList, VoteRequest
from app.core.security import get_current_user

router = APIRouter(prefix="/topics/{topic_id}/posts", tags=["posts"])


def _post_query():
    """Base query with eagerly loaded author and image relationships."""
    return select(Post).options(selectinload(Post.author), selectinload(Post.image))


@router.get("", response_model=PostList)
async def list_posts(
    topic_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    total_result = await db.execute(
        select(func.count(Post.id)).where(Post.topic_id == topic_id)
    )
    total = total_result.scalar_one()

    result = await db.execute(
        _post_query()
        .where(Post.topic_id == topic_id)
        .order_by(Post.created_at.asc())
        .offset(offset)
        .limit(per_page)
    )
    posts = result.scalars().all()
    return PostList(items=posts, total=total, page=page, per_page=per_page)


@router.post("", response_model=PostPublic, status_code=status.HTTP_201_CREATED)
async def create_post(
    topic_id: int,
    body: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verify topic exists
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    post = Post(
        topic_id=topic_id,
        author_id=current_user.id,
        content=body.content,
        image_id=body.image_id,
    )
    db.add(post)

    # Increment topic post_count
    await db.execute(
        update(Topic).where(Topic.id == topic_id).values(post_count=Topic.post_count + 1)
    )
    await db.commit()
    # Re-fetch with eagerly loaded relationships (refresh() doesn't load them)
    result = await db.execute(_post_query().where(Post.id == post.id))
    return result.scalar_one()


@router.post("/{post_id}/vote", response_model=PostPublic)
async def vote_post(
    topic_id: int,
    post_id: int,
    body: VoteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(_post_query().where(Post.id == post_id, Post.topic_id == topic_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # Check existing vote
    existing = await db.execute(
        select(PostLike).where(PostLike.post_id == post_id, PostLike.user_id == current_user.id)
    )
    existing_vote = existing.scalar_one_or_none()

    new_vote = VoteType(body.vote)

    if existing_vote:
        if existing_vote.vote == new_vote:
            # Remove vote (toggle off)
            if new_vote == VoteType.like:
                post.like_count = max(0, post.like_count - 1)
            else:
                post.dislike_count = max(0, post.dislike_count - 1)
            await db.delete(existing_vote)
        else:
            # Switch vote
            if new_vote == VoteType.like:
                post.like_count += 1
                post.dislike_count = max(0, post.dislike_count - 1)
            else:
                post.dislike_count += 1
                post.like_count = max(0, post.like_count - 1)
            existing_vote.vote = new_vote
    else:
        # New vote
        vote_record = PostLike(post_id=post_id, user_id=current_user.id, vote=new_vote)
        db.add(vote_record)
        if new_vote == VoteType.like:
            post.like_count += 1
        else:
            post.dislike_count += 1

    await db.commit()
    # Re-fetch with eagerly loaded relationships
    result = await db.execute(_post_query().where(Post.id == post.id))
    return result.scalar_one()


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    topic_id: int,
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Post).where(Post.id == post_id, Post.topic_id == topic_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")

    await db.delete(post)
    await db.execute(
        update(Topic).where(Topic.id == topic_id).values(post_count=func.greatest(Topic.post_count - 1, 0))
    )
    await db.commit()
