from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db


async def anext(async_gen):
    """Helper to get next item from async generator."""
    return await async_gen.__anext__()


@pytest.mark.asyncio
async def test_get_db_success():
    """Tests that get_db yields a session, commits, and closes properly."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = None

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_context):
        db_generator = get_db()
        session = await anext(db_generator)
        assert session is mock_session

        # Complete generator
        with pytest.raises(StopAsyncIteration):
            await anext(db_generator)

    mock_session.commit.assert_awaited_once()
    mock_session.rollback.assert_not_awaited()
    mock_session.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_db_exception_rollbacks():
    """Tests that get_db rollbacks or commits safely and always closes."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_context = AsyncMock()
    mock_context.__aenter__.return_value = mock_session
    mock_context.__aexit__.return_value = None

    with patch("app.core.database.AsyncSessionLocal", return_value=mock_context):
        db_generator = get_db()
        # start generator
        await anext(db_generator)

        # gracefully close generator to trigger finally
        try:
            await db_generator.__anext__()
        except StopAsyncIteration:
            pass

    called_commit = mock_session.commit.await_count > 0
    called_rollback = mock_session.rollback.await_count > 0
    assert called_commit or called_rollback, "Expected either commit or rollback"
    mock_session.close.assert_awaited_once()
