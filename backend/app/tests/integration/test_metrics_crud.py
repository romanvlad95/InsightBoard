import pytest
from httpx import AsyncClient

from app.models.dashboard import Dashboard
from app.schemas.dashboard import DashboardCreate
from app.schemas.metric import MetricCreate
from app.services.dashboard_service import DashboardService
from app.services.metric_service import MetricService


@pytest.fixture
async def test_dashboard(db_session, test_user) -> Dashboard:
    service = DashboardService(db_session)
    dashboard = await service.create_dashboard(
        DashboardCreate(name="Test Dashboard", description="Test Description"),
        owner_id=test_user.id,
    )
    return dashboard


@pytest.fixture
async def test_metric(db_session, test_dashboard):
    service = MetricService(db_session)
    metric = await service.create_metric(
        user_id=test_dashboard.owner_id,
        data=MetricCreate(
            name="Test Metric",
            value=1.0,
            metric_type="gauge",
            dashboard_id=test_dashboard.id,
        ),
    )
    return metric


@pytest.mark.asyncio
async def test_create_metric(authenticated_client: AsyncClient, test_dashboard):
    response = await authenticated_client.post(
        "/api/v1/metrics/",
        json={
            "name": "New Metric",
            "value": 123.45,
            "metric_type": "counter",
            "dashboard_id": test_dashboard.id,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "New Metric"


@pytest.mark.asyncio
async def test_create_metric_for_other_user_dashboard(
    authenticated_client: AsyncClient, db_session
):
    from app.schemas.user import UserCreate
    from app.services.auth_service import create_user

    other_user = await create_user(
        db_session,
        UserCreate(email="other@example.com", password="password"),
    )
    other_dashboard = await DashboardService(db_session).create_dashboard(
        DashboardCreate(name="Other User Dashboard", description=""),
        owner_id=other_user.id,
    )

    response = await authenticated_client.post(
        "/api/v1/metrics/",
        json={
            "name": "New Metric",
            "value": 123.45,
            "metric_type": "counter",
            "dashboard_id": other_dashboard.id,
        },
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_metric(authenticated_client: AsyncClient, test_metric):
    response = await authenticated_client.get(f"/api/v1/metrics/{test_metric.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Metric"


@pytest.mark.asyncio
async def test_get_other_user_metric(authenticated_client: AsyncClient, db_session):
    from app.schemas.user import UserCreate
    from app.services.auth_service import create_user

    other_user = await create_user(
        db_session,
        UserCreate(email="other@example.com", password="password"),
    )
    other_dashboard = await DashboardService(db_session).create_dashboard(
        DashboardCreate(name="Other User Dashboard", description=""),
        owner_id=other_user.id,
    )
    other_metric = await MetricService(db_session).create_metric(
        user_id=other_user.id,
        data=MetricCreate(
            name="Other Metric",
            value=1.0,
            metric_type="gauge",
            dashboard_id=other_dashboard.id,
        ),
    )

    response = await authenticated_client.get(f"/api/v1/metrics/{other_metric.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_metric(authenticated_client: AsyncClient, test_metric):
    response = await authenticated_client.put(
        f"/api/v1/metrics/{test_metric.id}",
        json={"name": "Updated Metric"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Metric"


@pytest.mark.asyncio
async def test_delete_metric(authenticated_client: AsyncClient, test_metric):
    response = await authenticated_client.delete(f"/api/v1/metrics/{test_metric.id}")
    assert response.status_code == 204

    response = await authenticated_client.get(f"/api/v1/metrics/{test_metric.id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_dashboard_metrics(
    authenticated_client: AsyncClient, test_dashboard, test_metric
):
    response = await authenticated_client.get(
        f"/api/v1/dashboards/{test_dashboard.id}/metrics"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Test Metric"
