from unittest.mock import AsyncMock, MagicMock  # Add MagicMock

import pytest

from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate
from app.services import auth_service


@pytest.mark.asyncio
async def test_create_user():
    db_session = AsyncMock()
    db_session.add = MagicMock()  # <-- Add this line

    user_in = UserCreate(email="test@example.com", password="password")

    user = await auth_service.create_user(db_session, user_in)

    assert user.email == user_in.email
    assert verify_password("password", user.password_hash)


def test_password_hashing():
    password = "password"
    hashed_password = get_password_hash(password)
    assert verify_password(password, hashed_password)
    assert not verify_password("wrongpassword", hashed_password)
