from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool
from app.database import get_db
from app.models.image import GeneratedImage
from app.models.user import User
from app.schemas.image import ImageGenerateRequest, ImagePublic
from app.core.security import get_current_user
from app.core.redis import get_redis, check_rate_limit
from app.services.image_gen import generate_image_bytes
from app.services.storage import upload_image_bytes
import redis.asyncio as aioredis

router = APIRouter(prefix="/images", tags=["images"])

# Rate limit: max 10 image generations per user per hour
IMAGE_GEN_LIMIT = 10
IMAGE_GEN_WINDOW = 3600  # seconds


@router.post("/generate", response_model=ImagePublic, status_code=status.HTTP_201_CREATED)
async def generate_image(
    body: ImageGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
):
    # Enforce rate limit
    rate_key = f"imggen:{current_user.id}"
    allowed = await check_rate_limit(redis, rate_key, IMAGE_GEN_LIMIT, IMAGE_GEN_WINDOW)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Image generation limit reached ({IMAGE_GEN_LIMIT}/hour). Try again later.",
        )

    # Clamp dimensions to safe range
    width = max(256, min(body.width, 1024))
    height = max(256, min(body.height, 1024))

    # Generate image via Hugging Face
    try:
        image_bytes = await generate_image_bytes(body.prompt, width, height)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Image generation failed: {str(e)}")

    # Upload to Cloudinary — sync SDK wrapped in threadpool to avoid blocking the event loop
    try:
        upload_result = await run_in_threadpool(upload_image_bytes, image_bytes)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Image storage failed: {str(e)}")

    # Save record to DB
    record = GeneratedImage(
        author_id=current_user.id,
        prompt=body.prompt,
        image_url=upload_result["url"],
        cloudinary_public_id=upload_result["public_id"],
        width=width,
        height=height,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/my", response_model=list[ImagePublic])
async def my_images(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GeneratedImage)
        .where(GeneratedImage.author_id == current_user.id)
        .order_by(GeneratedImage.created_at.desc())
        .limit(50)
    )
    return result.scalars().all()
