"""
Security-related utilities for the InsightBoard application.

This module provides functions for password hashing and verification,
as well as for creating and managing JSON Web Tokens (JWTs) for
user authentication and authorization.
"""

from datetime import datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# CryptContext for password hashing using bcrypt.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_access_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    """
    Creates a new JWT access token.

    The token includes the subject (typically the user's ID or email) and an
    expiration timestamp. The expiration can be specified or defaults to the
    value from the application settings.

    Args:
        subject: The subject of the token, which can be any string or object.
        expires_delta: An optional timedelta to set the token's expiration.
                       If None, defaults to ACCESS_TOKEN_EXPIRE_MINUTES.

    Returns:
        A signed JWT access token as a string.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain-text password against a hashed password.

    Args:
        plain_password: The plain-text password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Computes the hash of a plain-text password.

    Args:
        password: The plain-text password to hash.

    Returns:
        The resulting hashed password as a string.
    """
    return pwd_context.hash(password)
