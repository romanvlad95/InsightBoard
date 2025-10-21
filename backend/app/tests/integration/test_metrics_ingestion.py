from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

# Import the app instance to allow patching its state
from app.main import app
from app.models.dashboard import Dashboard
from app.schemas.user import UserCreate
from app.services.auth_service import create_user

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


async def test_ingest_metrics_success(
    authenticated_client: AsyncClient,
    test_dashboard: Dashboard,
):
    """Test successful ingestion of a valid metric payload."""
    # Arrange
    metrics_payload = [
        {
            "dashboard_id": test_dashboard.id,
            "name": "test_metric_1",
            "value": 123.45,
            "metric_type": "gauge",
        }
    ]

    mock_producer = AsyncMock()
    # Add create=True to handle the attribute not existing in the test app state
    with patch.object(app.state, "kafka_producer", mock_producer, create=True):
        # Act
        response = await authenticated_client.post(
            "/api/v1/metrics/ingest", json=metrics_payload
        )

    # Assert
    assert response.status_code == 202
    assert response.json() == {"message": "Accepted 1/1 metrics for processing"}

    # Verify the mock was called correctly
    mock_producer.send_metric.assert_awaited_once()
    call_args = mock_producer.send_metric.call_args[1]
    assert call_args["dashboard_id"] == test_dashboard.id
    assert call_args["name"] == "test_metric_1"
    assert call_args["value"] == 123.45


async def test_ingest_metrics_unauthorized_dashboard(
    authenticated_client: AsyncClient,
    test_dashboard: Dashboard,  # This dashboard belongs to the test_user
    db_session,  # To create another user and dashboard
):
    """Test that metrics for dashboards not owned by the user are skipped."""
    # Arrange: Create another user and a dashboard for them using the service
    other_user_in = UserCreate(email="other@user.com", password="password")
    other_user = await create_user(db_session, other_user_in)

    other_dashboard = Dashboard(name="Other Dashboard", owner_id=other_user.id)
    db_session.add(other_dashboard)
    await db_session.commit()

    metrics_payload = [
        {
            "dashboard_id": other_dashboard.id,  # Belongs to other_user
            "name": "unauthorized_metric",
            "value": 99,
            "metric_type": "counter",
        },
        {
            "dashboard_id": test_dashboard.id,  # Belongs to authenticated_client's user
            "name": "authorized_metric",
            "value": 100,
            "metric_type": "counter",
        },
    ]

    mock_producer = AsyncMock()
    # Add create=True to handle the attribute not existing in the test app state
    with patch.object(app.state, "kafka_producer", mock_producer, create=True):
        # Act
        response = await authenticated_client.post(
            "/api/v1/metrics/ingest", json=metrics_payload
        )

    # Assert
    assert response.status_code == 202
    # Only the authorized metric should be processed
    assert response.json() == {"message": "Accepted 1/2 metrics for processing"}

    # Verify mock was called only once with the authorized metric
    mock_producer.send_metric.assert_awaited_once()
    call_args = mock_producer.send_metric.call_args[1]
    assert call_args["dashboard_id"] == test_dashboard.id
    assert call_args["name"] == "authorized_metric"


async def test_ingest_metrics_validation_error(
    authenticated_client: AsyncClient,
):
    """Test ingestion with a payload that fails Pydantic validation."""
    # Arrange: Payload missing required 'value' field
    bad_payload = [
        {
            "dashboard_id": 1,
            "name": "metric_with_no_value",
            "metric_type": "gauge",
        }
    ]

    mock_producer = AsyncMock()
    with patch.object(app.state, "kafka_producer", mock_producer, create=True):
        # Act
        response = await authenticated_client.post(
            "/api/v1/metrics/ingest", json=bad_payload
        )

    # Assert
    assert response.status_code == 422  # Unprocessable Entity
    response_data = response.json()
    assert "detail" in response_data
    assert response_data["detail"][0]["msg"] == "Field required"
    assert "value" in response_data["detail"][0]["loc"]

    # Ensure producer was not called
    mock_producer.send_metric.assert_not_awaited()


async def test_ingest_metrics_empty_payload(
    authenticated_client: AsyncClient,
):
    """Test ingestion with an empty list of metrics."""
    mock_producer = AsyncMock()
    with patch.object(app.state, "kafka_producer", mock_producer, create=True):
        # Act
        response = await authenticated_client.post("/api/v1/metrics/ingest", json=[])

    # Assert
    assert response.status_code == 202
    assert response.json() == {"message": "Accepted 0/0 metrics for processing"}

    # Ensure producer was not called
    mock_producer.send_metric.assert_not_awaited()
