"""
Service layer for authentication and user management logic.

This module provides functions for user registration, authentication,
and retrieval from the database.
"""


from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Retrieves a user from the database by their email address.

    Args:
        db: The SQLAlchemy `AsyncSession` to use for database operations.
        email: The email address of the user to retrieve.

    Returns:
        The User object if found, otherwise None.
    """
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, user: UserCreate, role: str = "user") -> User:
    """
    Creates a new user in the database.

    This function hashes the user's password before creating the new User record.

    Args:
        db: The SQLAlchemy `AsyncSession` to use for database operations.
        user: The Pydantic schema containing the new user's data.
        role: The role to assign to the new user.

    Returns:
        The newly created User object.
    """
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, password_hash=hashed_password, role=role)
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """
    Authenticates a user based on email and password.

    It retrieves the user by email and then verifies the provided password
    against the stored hash.

    Args:
        db: The SQLAlchemy `AsyncSession` to use for database operations.
        email: The user's email address.
        password: The user's plain-text password.

    Returns:
        The authenticated User object if the credentials are valid,
        otherwise None.
    """
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
