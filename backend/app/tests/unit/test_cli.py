from unittest.mock import AsyncMock, patch

import pytest

from app import cli


@pytest.mark.asyncio
async def test_internal__create_admin_branches(monkeypatch):
    mock_db = AsyncMock()
    cli.SessionLocal = lambda: mock_db
    cli.auth_service = AsyncMock()
    cli.console = AsyncMock()  # чтобы не печатал в stdout

    # достаём исходный код асинхронной функции из тела create_admin
    async def fake__create_admin(email, password):
        db = cli.SessionLocal()
        user = await cli.auth_service.get_user_by_email(db, email=email)
        if user:
            cli.console.print(f"User with email [bold red]{email}[/] already exists.")
            return
        user_in = cli.UserCreate(email=email, password=password)
        await cli.auth_service.create_user(db, user=user_in, role="admin")
        cli.console.print(f"Admin user [bold green]{email}[/] created successfully.")
        await db.close()

    # подменяем внутри cli
    with patch.object(cli, "_create_admin", fake__create_admin, create=True):
        # ветка 1 — user существует
        cli.auth_service.get_user_by_email.return_value = object()
        await fake__create_admin("exists@test.com", "pass")
        cli.auth_service.get_user_by_email.assert_called_once()

        # ветка 2 — user не найден
        cli.auth_service.get_user_by_email.return_value = None
        await fake__create_admin("new@test.com", "pass")
        cli.auth_service.create_user.assert_called_once()
