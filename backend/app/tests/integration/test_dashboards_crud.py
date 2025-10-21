import asyncio

import pytest
from httpx import AsyncClient

from app.schemas.dashboard import DashboardCreate
from app.services.dashboard_service import DashboardService


@pytest.mark.asyncio
async def test_create_dashboard(authenticated_client: AsyncClient, test_user):
    response = await authenticated_client.post(
        "/api/v1/dashboards/",
        json={"name": "Test Dashboard", "description": "Test Description"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Dashboard"
    assert data["description"] == "Test Description"


@pytest.mark.asyncio
async def test_get_user_dashboards(
    authenticated_client: AsyncClient, test_user, db_session
):
    service = DashboardService(db_session)
    await service.create_dashboard(
        DashboardCreate(name="Test Dashboard 1", description="Test Description 1"),
        owner_id=test_user.id,
    )
    await asyncio.sleep(0.1)
    await service.create_dashboard(
        DashboardCreate(name="Test Dashboard 2", description="Test Description 2"),
        owner_id=test_user.id,
    )

    response = await authenticated_client.get("/api/v1/dashboards/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    names = {d["name"] for d in data}
    assert names == {"Test Dashboard 1", "Test Dashboard 2"}


@pytest.mark.asyncio
async def test_get_dashboard(authenticated_client: AsyncClient, test_user, db_session):
    service = DashboardService(db_session)
    dashboard = await service.create_dashboard(
        DashboardCreate(name="Test Dashboard", description="Test Description"),
        owner_id=test_user.id,
    )

    response = await authenticated_client.get(f"/api/v1/dashboards/{dashboard.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Dashboard"


@pytest.mark.asyncio
async def test_get_dashboard_not_found(authenticated_client: AsyncClient):
    response = await authenticated_client.get("/api/v1/dashboards/999")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_other_user_dashboard(authenticated_client: AsyncClient, db_session):
    # This test requires another user
    from app.schemas.user import UserCreate
    from app.services.auth_service import create_user

    other_user = await create_user(
        db_session,
        UserCreate(email="other@example.com", password="password"),
    )

    service = DashboardService(db_session)
    dashboard = await service.create_dashboard(
        DashboardCreate(name="Other User Dashboard", description=""),
        owner_id=other_user.id,
    )

    response = await authenticated_client.get(f"/api/v1/dashboards/{dashboard.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_dashboard(
    authenticated_client: AsyncClient, test_user, db_session
):
    service = DashboardService(db_session)
    dashboard = await service.create_dashboard(
        DashboardCreate(name="Test Dashboard", description="Test Description"),
        owner_id=test_user.id,
    )

    response = await authenticated_client.put(
        f"/api/v1/dashboards/{dashboard.id}",
        json={"name": "Updated Dashboard"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Dashboard"


@pytest.mark.asyncio
async def test_update_other_user_dashboard(
    authenticated_client: AsyncClient, db_session
):
    from app.schemas.user import UserCreate
    from app.services.auth_service import create_user

    other_user = await create_user(
        db_session,
        UserCreate(email="other@example.com", password="password"),
    )

    service = DashboardService(db_session)
    dashboard = await service.create_dashboard(
        DashboardCreate(name="Other User Dashboard", description=""),
        owner_id=other_user.id,
    )

    response = await authenticated_client.put(
        f"/api/v1/dashboards/{dashboard.id}",
        json={"name": "Updated Dashboard"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_dashboard(
    authenticated_client: AsyncClient, test_user, db_session
):
    service = DashboardService(db_session)
    dashboard = await service.create_dashboard(
        DashboardCreate(name="Test Dashboard", description="Test Description"),
        owner_id=test_user.id,
    )

    response = await authenticated_client.delete(f"/api/v1/dashboards/{dashboard.id}")
    assert response.status_code == 204

    # Verify it's deleted
    response = await authenticated_client.get(f"/api/v1/dashboards/{dashboard.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_other_user_dashboard(
    authenticated_client: AsyncClient, db_session
):
    from app.schemas.user import UserCreate
    from app.services.auth_service import create_user

    other_user = await create_user(
        db_session,
        UserCreate(email="other@example.com", password="password"),
    )

    service = DashboardService(db_session)
    dashboard = await service.create_dashboard(
        DashboardCreate(name="Other User Dashboard", description=""),
        owner_id=other_user.id,
    )

    response = await authenticated_client.delete(f"/api/v1/dashboards/{dashboard.id}")
    assert response.status_code == 404
