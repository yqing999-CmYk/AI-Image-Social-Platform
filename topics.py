from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.topic import Topic
from app.models.user import User
from app.schemas.topic import TopicCreate, TopicPublic, TopicList
from app.core.security import get_current_user

router = APIRouter(prefix="/topics", tags=["topics"])


def _topic_query():
    """Base query with eagerly loaded author relationship."""
    return select(Topic).options(selectinload(Topic.author))


@router.get("", response_model=TopicList)
async def list_topics(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * per_page
    total_result = await db.execute(select(func.count(Topic.id)))
    total = total_result.scalar_one()

    result = await db.execute(
        _topic_query().order_by(Topic.created_at.desc()).offset(offset).limit(per_page)
    )
    topics = result.scalars().all()
    return TopicList(items=topics, total=total, page=page, per_page=per_page)


@router.post("", response_model=TopicPublic, status_code=status.HTTP_201_CREATED)
async def create_topic(
    body: TopicCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    topic = Topic(title=body.title, description=body.description, author_id=current_user.id)
    db.add(topic)
    await db.commit()
    # Re-fetch with eagerly loaded author
    result = await db.execute(_topic_query().where(Topic.id == topic.id))
    return result.scalar_one()


@router.get("/{topic_id}", response_model=TopicPublic)
async def get_topic(topic_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(_topic_query().where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return topic


@router.delete("/{topic_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_topic(
    topic_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Topic).where(Topic.id == topic_id))
    topic = result.scalar_one_or_none()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    if topic.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed")
    await db.delete(topic)
    await db.commit()
