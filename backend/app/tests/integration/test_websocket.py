from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from starlette import status
from starlette.websockets import WebSocketDisconnect

from app.main import app
from app.models.dashboard import Dashboard

client = TestClient(app)

USER_ID = 1
OTHER_USER_ID = 2
DASHBOARD_ID = 1


@patch("app.api.v1.endpoints.websocket.verify_token", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.websocket.DashboardService")
@patch("app.main.app.state")
def test_websocket_connection_success(
    mock_app_state, MockDashboardService, mock_verify_token
):
    """Successful WebSocket connect and one metric forwarded."""
    mock_verify_token.return_value = USER_ID
    MockDashboardService.return_value.get_dashboard_by_id = AsyncMock(
        return_value=Dashboard(id=DASHBOARD_ID, owner_id=USER_ID)
    )

    test_metric = {"name": "cpu", "value": 0.99}

    class OneShotStream:
        async def __aiter__(self):
            yield test_metric  # после первого сообщения генератор сам завершится

    # Важно: не AsyncMock! Возвращаем сразу async-итерируемый объект
    def subscribe_to_dashboard(_dashboard_id: int):
        return OneShotStream()

    mock_app_state.redis_service = SimpleNamespace(
        subscribe_to_dashboard=subscribe_to_dashboard
    )

    with client.websocket_connect(
        f"/api/v1/ws/dashboard/{DASHBOARD_ID}?token=valid_token"
    ) as ws:
        data = ws.receive_json()
        assert data == {"type": "metric_update", "data": test_metric}

    mock_verify_token.assert_awaited_once_with("valid_token")
    MockDashboardService.return_value.get_dashboard_by_id.assert_awaited_once_with(
        DASHBOARD_ID
    )


@patch("app.api.v1.endpoints.websocket.verify_token", new_callable=AsyncMock)
def test_websocket_connection_invalid_token(mock_verify_token):
    """Reject when token invalid."""
    mock_verify_token.side_effect = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED
    )

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            f"/api/v1/ws/dashboard/{DASHBOARD_ID}?token=invalid_token"
        ):
            pass

    assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION


@patch("app.api.v1.endpoints.websocket.verify_token", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.websocket.DashboardService")
def test_websocket_connection_not_owner(MockDashboardService, mock_verify_token):
    """Reject when user is not the owner."""
    mock_verify_token.return_value = USER_ID
    MockDashboardService.return_value.get_dashboard_by_id = AsyncMock(
        return_value=Dashboard(id=DASHBOARD_ID, owner_id=OTHER_USER_ID)
    )

    with pytest.raises(WebSocketDisconnect) as exc_info:
        with client.websocket_connect(
            f"/api/v1/ws/dashboard/{DASHBOARD_ID}?token=valid_token"
        ):
            pass

    assert exc_info.value.code == status.WS_1008_POLICY_VIOLATION


@patch("app.api.v1.endpoints.websocket.verify_token", new_callable=AsyncMock)
@patch("app.api.v1.endpoints.websocket.DashboardService")
@patch("app.main.app.state")
def test_websocket_no_redis_service(
    mock_app_state, MockDashboardService, mock_verify_token
):
    """Verify graceful close (1011) when redis service is unavailable."""
    mock_verify_token.return_value = USER_ID
    MockDashboardService.return_value.get_dashboard_by_id = AsyncMock(
        return_value=Dashboard(id=DASHBOARD_ID, owner_id=USER_ID)
    )

    if hasattr(mock_app_state, "redis_service"):
        del mock_app_state.redis_service

    with client.websocket_connect(
        f"/api/v1/ws/dashboard/{DASHBOARD_ID}?token=valid_token"
    ) as ws:
        # попробуем получить хоть что-то (ожидаем закрытие)
        close_msg = ws.receive()
        assert close_msg["type"] == "websocket.close"
        assert close_msg["code"] == status.WS_1011_INTERNAL_ERROR
