import asyncio
import sys

import typer

sys.modules["app.core.database"].SessionLocal = None
from rich.console import Console

from app.core.database import async_session_maker
from app.schemas.user import UserCreate
from app.services import auth_service

app = typer.Typer()
console = Console()


async def _create_admin(email: str, password: str):
    """Internal coroutine to create admin."""
    async with async_session_maker() as db:
        user = await auth_service.get_user_by_email(db, email=email)
        if user:
            console.print(f"User with email [bold red]{email}[/] already exists.")
            return
        user_in = UserCreate(email=email, password=password)
        await auth_service.create_user(db, user=user_in, role="admin")
        console.print(f"Admin user [bold green]{email}[/] created successfully.")


@app.command()
def create_admin(
    email: str = typer.Option(..., "--email", "-e"),
    password: str = typer.Option(..., "--password", "-p", hide_input=True),
):
    """Creates an admin user."""
    asyncio.run(_create_admin(email, password))


if __name__ == "__main__":
    app()
