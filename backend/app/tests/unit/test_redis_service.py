import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from redis.exceptions import RedisError

from app.services.redis_service import RedisService, get_redis_service


@pytest.fixture
def mock_redis_pool():
    with patch("app.services.redis_service.ConnectionPool") as mock_pool_cls:
        mock_pool = mock_pool_cls.from_url.return_value
        mock_pool.disconnect = AsyncMock()
        yield mock_pool


@pytest.fixture
def mock_redis_client():
    with patch("app.services.redis_service.Redis") as mock_redis_cls:
        mock_redis = mock_redis_cls.return_value
        mock_redis.ping = AsyncMock()
        mock_redis.close = AsyncMock()
        mock_redis.publish = AsyncMock()
        mock_redis.pubsub = MagicMock()
        yield mock_redis


@pytest.fixture
def redis_service(mock_redis_pool, mock_redis_client):
    return RedisService(redis_url="redis://localhost")


@pytest.mark.asyncio
async def test_start_and_close(redis_service, mock_redis_pool, mock_redis_client):
    await redis_service.start()
    mock_redis_client.ping.assert_awaited_once()
    assert redis_service._redis is not None

    # Calling start again should do nothing
    await redis_service.start()
    mock_redis_client.ping.assert_awaited_once()  # Still once

    await redis_service.close()
    mock_redis_client.close.assert_awaited_once()
    mock_redis_pool.disconnect.assert_awaited_once()


@pytest.mark.asyncio
async def test_publish_metric_update(redis_service, mock_redis_client):
    await redis_service.start()
    metric_data = {"name": "cpu", "value": 0.5}
    await redis_service.publish_metric_update(1, metric_data)

    expected_channel = "dashboard:1:metrics"
    expected_message = json.dumps(metric_data)
    mock_redis_client.publish.assert_awaited_once_with(
        expected_channel, expected_message
    )


@pytest.mark.asyncio
async def test_publish_metric_redis_error(redis_service, mock_redis_client):
    await redis_service.start()
    mock_redis_client.publish.side_effect = RedisError("Publish failed")

    with pytest.raises(RedisError):
        await redis_service.publish_metric_update(1, {})


@pytest.mark.asyncio
async def test_subscribe_to_dashboard(redis_service, mock_redis_client):
    await redis_service.start()

    mock_pubsub = MagicMock()
    mock_pubsub.subscribe = AsyncMock()
    mock_pubsub.unsubscribe = AsyncMock()
    mock_pubsub.close = AsyncMock()

    async def message_generator():
        yield {"type": "message", "data": '{"value": 1}'}
        yield {"type": "message", "data": "not json"}

    mock_pubsub.listen.return_value = message_generator()
    mock_redis_client.pubsub.return_value = mock_pubsub

    results = []
    async for data in redis_service.subscribe_to_dashboard(1):
        results.append(data)

    assert len(results) == 1
    assert results[0] == {"value": 1}
    mock_pubsub.subscribe.assert_awaited_once_with("dashboard:1:metrics")
    mock_pubsub.unsubscribe.assert_awaited_once()
    mock_pubsub.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_methods_raise_if_not_started(redis_service):
    with pytest.raises(RuntimeError, match="Redis service is not started."):
        await redis_service.publish_metric_update(1, {})

    with pytest.raises(RuntimeError, match="Redis service is not started."):
        async for _ in redis_service.subscribe_to_dashboard(1):
            pass


def test_get_redis_service_dependency():
    mock_request = MagicMock()
    mock_request.app.state.redis_service = "a service"
    assert get_redis_service(mock_request) == "a service"

    mock_request_fail = MagicMock()
    del mock_request_fail.app.state.redis_service
    with pytest.raises(RuntimeError, match="Redis service not available"):
        get_redis_service(mock_request_fail)
