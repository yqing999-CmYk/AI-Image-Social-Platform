from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserSignUp, UserSignIn, TokenResponse, UserPublic
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/sign-up", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(body: UserSignUp, db: AsyncSession = Depends(get_db)):
    # Check for duplicate email
    if body.email:
        existing = await db.execute(select(User).where(User.email == body.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Email already registered")

    # Check for duplicate phone
    if body.phone:
        existing = await db.execute(select(User).where(User.phone == body.phone))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Phone number already registered")

    # Check for duplicate username
    existing = await db.execute(select(User).where(User.username == body.username))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already taken")

    user = User(
        email=body.email,
        phone=body.phone,
        username=body.username,
        hashed_password=hash_password(body.password),
        display_name=body.display_name or body.username,
        is_agent=body.is_agent,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    token = create_access_token(subject=user.id)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))


@router.post("/sign-in", response_model=TokenResponse)
async def sign_in(body: UserSignIn, db: AsyncSession = Depends(get_db)):
    identifier = body.identifier.strip()

    # Look up by email or phone
    result = await db.execute(
        select(User).where(or_(User.email == identifier, User.phone == identifier))
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token(subject=user.id)
    return TokenResponse(access_token=token, user=UserPublic.model_validate(user))
