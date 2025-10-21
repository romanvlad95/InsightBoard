import os
import sys
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add the project root to the sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.core.database import Base, get_db
from app.main import app
from app.models.dashboard import Dashboard
from app.models.metric import Metric
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.auth_service import create_user

# ======================================
# FORCE SQLITE FOR TESTS - IGNORE .env
# ======================================
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Creates a clean database session for each test.
    Creates and drops tables for isolation.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Creates an httpx AsyncClient with the database dependency overridden.
    """

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    # Use ASGITransport for modern httpx
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def test_user(db_session: AsyncSession) -> User:
    """
    Creates a test user using the auth service.
    """
    user_in = UserCreate(email="test@example.com", password="testpassword")
    user = await create_user(db_session, user_in)
    return user


@pytest.fixture(scope="function")
async def authenticated_client(client: AsyncClient, test_user: User) -> AsyncClient:
    """
    Creates an authenticated client by logging in the test_user.
    """
    login_data = {"username": test_user.email, "password": "testpassword"}
    response = await client.post("/api/v1/auth/login/access-token", data=login_data)

    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json().get("access_token")
    assert token, "No access_token returned"

    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture(scope="function")
async def test_dashboard(db_session: AsyncSession, test_user: User) -> Dashboard:
    """
    Creates a test dashboard for test_user.
    """
    dashboard = Dashboard(
        name="Test Dashboard", description="Test Description", owner_id=test_user.id
    )
    db_session.add(dashboard)
    await db_session.commit()
    await db_session.refresh(dashboard)
    return dashboard


@pytest.fixture(scope="function")
async def test_metric(db_session: AsyncSession, test_dashboard: Dashboard) -> Metric:
    """
    Creates a test metric for test_dashboard.
    """
    metric = Metric(
        name="Test Metric",
        value=100.0,
        metric_type="counter",
        dashboard_id=test_dashboard.id,
    )
    db_session.add(metric)
    await db_session.commit()
    await db_session.refresh(metric)
    return metric
