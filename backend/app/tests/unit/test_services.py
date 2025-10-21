from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.models.dashboard import Dashboard
from app.models.metric import Metric
from app.schemas.metric import MetricCreate, MetricUpdate
from app.services.metric_service import MetricService

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio

USER_ID = 1
OTHER_USER_ID = 2
DASHBOARD_ID = 1
METRIC_ID = 1


@pytest.fixture
def mock_db_session() -> AsyncMock:
    """Fixture for a mocked async database session."""
    return AsyncMock()


# --- Tests for create_metric ---


async def test_create_metric_success(mock_db_session: AsyncMock):
    """Test successful creation of a metric for an authorized dashboard."""
    service = MetricService(mock_db_session)
    metric_data = MetricCreate(
        dashboard_id=DASHBOARD_ID, name="Test", value=1.0, metric_type="gauge"
    )

    mock_dashboard = Dashboard(id=DASHBOARD_ID, owner_id=USER_ID)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_dashboard
    mock_db_session.execute.return_value = mock_result

    new_metric = await service.create_metric(user_id=USER_ID, data=metric_data)

    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_awaited_once()
    mock_db_session.refresh.assert_awaited_once()
    assert new_metric.name == metric_data.name
    assert new_metric.value == metric_data.value


async def test_create_metric_dashboard_not_found(mock_db_session: AsyncMock):
    """Test create_metric raises 404 if dashboard not found."""
    service = MetricService(mock_db_session)
    metric_data = MetricCreate(
        dashboard_id=DASHBOARD_ID, name="Test", value=1.0, metric_type="gauge"
    )

    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await service.create_metric(user_id=USER_ID, data=metric_data)
    assert exc_info.value.status_code == 404


async def test_create_metric_forbidden(mock_db_session: AsyncMock):
    """Test create_metric raises 403 for an unauthorized dashboard."""
    service = MetricService(mock_db_session)
    metric_data = MetricCreate(
        dashboard_id=DASHBOARD_ID, name="Test", value=1.0, metric_type="gauge"
    )

    mock_dashboard = Dashboard(id=DASHBOARD_ID, owner_id=OTHER_USER_ID)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_dashboard
    mock_db_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await service.create_metric(user_id=USER_ID, data=metric_data)
    assert exc_info.value.status_code == 403


# --- Tests for get_metric_by_id ---


async def test_get_metric_by_id_success(mock_db_session: AsyncMock):
    """Test successful retrieval of an authorized metric."""
    service = MetricService(mock_db_session)
    mock_metric = Metric(id=METRIC_ID, dashboard=Dashboard(owner_id=USER_ID))
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_metric
    mock_db_session.execute.return_value = mock_result

    metric = await service.get_metric_by_id(metric_id=METRIC_ID, user_id=USER_ID)

    assert metric is not None
    assert metric.id == METRIC_ID


async def test_get_metric_by_id_not_found(mock_db_session: AsyncMock):
    """Test get_metric_by_id returns None if metric not found."""
    service = MetricService(mock_db_session)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db_session.execute.return_value = mock_result

    metric = await service.get_metric_by_id(metric_id=METRIC_ID, user_id=USER_ID)

    assert metric is None


async def test_get_metric_by_id_forbidden(mock_db_session: AsyncMock):
    """Test get_metric_by_id returns None for an unauthorized metric."""
    service = MetricService(mock_db_session)
    mock_metric = Metric(id=METRIC_ID, dashboard=Dashboard(owner_id=OTHER_USER_ID))
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_metric
    mock_db_session.execute.return_value = mock_result

    metric = await service.get_metric_by_id(metric_id=METRIC_ID, user_id=USER_ID)

    assert metric is None


# --- Tests for update_metric ---


async def test_update_metric_success(mock_db_session: AsyncMock):
    """Test successful update of an authorized metric."""
    service = MetricService(mock_db_session)
    update_data = MetricUpdate(name="Updated Name", value=99.9)
    mock_metric = Metric(
        id=METRIC_ID, name="Old", value=1.0, dashboard=Dashboard(owner_id=USER_ID)
    )

    with patch.object(
        service, "get_metric_by_id", new_callable=AsyncMock, return_value=mock_metric
    ) as mock_get:
        updated_metric = await service.update_metric(
            METRIC_ID, USER_ID, data=update_data
        )

        mock_get.assert_awaited_once_with(METRIC_ID, USER_ID)
        assert updated_metric is not None
        assert updated_metric.name == "Updated Name"
        assert updated_metric.value == 99.9
        mock_db_session.commit.assert_awaited_once()
        mock_db_session.refresh.assert_awaited_once()


async def test_update_metric_not_found(mock_db_session: AsyncMock):
    """Test update_metric returns None if metric not found."""
    service = MetricService(mock_db_session)
    update_data = MetricUpdate(name="Updated Name")

    with patch.object(
        service, "get_metric_by_id", new_callable=AsyncMock, return_value=None
    ) as mock_get:
        result = await service.update_metric(METRIC_ID, USER_ID, data=update_data)

        mock_get.assert_awaited_once_with(METRIC_ID, USER_ID)
        assert result is None
        mock_db_session.commit.assert_not_awaited()


# --- Tests for delete_metric ---


async def test_delete_metric_success(mock_db_session: AsyncMock):
    """Test successful deletion of an authorized metric."""
    service = MetricService(mock_db_session)
    mock_metric = Metric(id=METRIC_ID, dashboard=Dashboard(owner_id=USER_ID))

    with patch.object(
        service, "get_metric_by_id", new_callable=AsyncMock, return_value=mock_metric
    ) as mock_get:
        result = await service.delete_metric(METRIC_ID, USER_ID)

        mock_get.assert_awaited_once_with(METRIC_ID, USER_ID)
        assert result is True
        mock_db_session.delete.assert_awaited_once_with(mock_metric)
        mock_db_session.commit.assert_awaited_once()


async def test_delete_metric_not_found(mock_db_session: AsyncMock):
    """Test delete_metric returns False if metric not found."""
    service = MetricService(mock_db_session)
    with patch.object(
        service, "get_metric_by_id", new_callable=AsyncMock, return_value=None
    ) as mock_get:
        result = await service.delete_metric(METRIC_ID, USER_ID)

        mock_get.assert_awaited_once_with(METRIC_ID, USER_ID)
        assert result is False
        mock_db_session.delete.assert_not_awaited()


# --- Tests for get_dashboard_metrics ---


async def test_get_dashboard_metrics_success(mock_db_session: AsyncMock):
    """Test successful retrieval of all metrics for an authorized dashboard."""
    service = MetricService(mock_db_session)
    mock_dashboard = Dashboard(id=DASHBOARD_ID, owner_id=USER_ID)
    mock_metrics_list = [Metric(id=1), Metric(id=2)]

    mock_dashboard_result = MagicMock()
    mock_dashboard_result.scalars.return_value.first.return_value = mock_dashboard

    mock_metrics_result = MagicMock()
    # This mocks the result.scalars().all() chain
    mock_metrics_result.scalars.return_value.all.return_value = mock_metrics_list

    mock_db_session.execute.side_effect = [mock_dashboard_result, mock_metrics_result]

    metrics = await service.get_dashboard_metrics(
        dashboard_id=DASHBOARD_ID, user_id=USER_ID
    )

    assert len(metrics) == 2
    assert metrics == mock_metrics_list
    assert mock_db_session.execute.call_count == 2


async def test_get_dashboard_metrics_dashboard_not_found(mock_db_session: AsyncMock):
    """Test get_dashboard_metrics raises 404 if dashboard not found."""
    service = MetricService(mock_db_session)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None
    mock_db_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await service.get_dashboard_metrics(dashboard_id=DASHBOARD_ID, user_id=USER_ID)

    assert exc_info.value.status_code == 404
    mock_db_session.execute.assert_awaited_once()


async def test_get_dashboard_metrics_forbidden(mock_db_session: AsyncMock):
    """Test get_dashboard_metrics raises 403 for an unauthorized dashboard."""
    service = MetricService(mock_db_session)
    mock_dashboard = Dashboard(id=DASHBOARD_ID, owner_id=OTHER_USER_ID)
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_dashboard
    mock_db_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await service.get_dashboard_metrics(dashboard_id=DASHBOARD_ID, user_id=USER_ID)

    assert exc_info.value.status_code == 403
    mock_db_session.execute.assert_awaited_once()
