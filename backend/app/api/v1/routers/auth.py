"""
API router for user authentication and authorization.

This module provides endpoints for user registration and login,
issuing JWT access tokens upon successful authentication.
"""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import deps
from app.core import security
from app.core.config import settings
from app.schemas.user import User, UserCreate
from app.services import auth_service

router = APIRouter()


class Token(BaseModel):
    """
    Schema for the OAuth2 token response.

    Attributes:
        access_token: The JWT access token.
        token_type: The type of the token (e.g., 'bearer').
    """

    access_token: str
    token_type: str


@router.post("/register", response_model=User, status_code=status.HTTP_201_CREATED)
async def register(
    *, db: AsyncSession = Depends(deps.get_db), user_in: UserCreate
) -> User:
    """
    Registers a new user in the system.

    Args:
        db: The SQLAlchemy `AsyncSession` dependency.
        user_in: The user creation data from the request body, containing a
                 unique email and a password.

    Returns:
        The newly created user object.

    Raises:
        HTTPException: If a user with the same email already exists.
    """
    user = await auth_service.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )
    user = await auth_service.create_user(db, user=user_in)
    return user


@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    db: AsyncSession = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends(),
) -> Token:
    """
    Provides an OAuth2 compatible token login endpoint.

    Authenticates a user with email and password and returns an access token.

    Args:
        db: The SQLAlchemy `AsyncSession` dependency.
        form_data: The OAuth2 password request form data, containing
                   username (email) and password.

    Returns:
        An access token and token type.

    Raises:
        HTTPException: If the authentication fails due to incorrect credentials.
    """
    user = await auth_service.authenticate_user(
        db, email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        user.email, expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")
