from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Mock settings before they are imported by main
with patch.dict(
    "os.environ",
    {"DATABASE_URL": "sqlite+aiosqlite:///:memory:", "REDIS_URL": "redis://localhost"},
):
    from app.main import app, lifespan


@pytest.fixture
def mock_kafka_producer_service():
    with patch("app.main.KafkaProducerService", new_callable=MagicMock) as MockService:
        MockService.return_value.start = AsyncMock()
        MockService.return_value.stop = AsyncMock()
        yield MockService


@pytest.fixture
def mock_kafka_consumer_service():
    with patch("app.main.KafkaConsumerService", new_callable=MagicMock) as MockService:
        MockService.return_value.start = AsyncMock()
        MockService.return_value.stop = AsyncMock()
        yield MockService


@pytest.fixture
def mock_redis_service():
    with patch("app.main.RedisService", new_callable=MagicMock) as MockService:
        MockService.return_value.start = AsyncMock()
        MockService.return_value.close = AsyncMock()
        yield MockService


@pytest.mark.asyncio
async def test_lifespan_success(
    mock_kafka_producer_service,
    mock_kafka_consumer_service,
    mock_redis_service,
):
    test_app = FastAPI()
    async with lifespan(test_app):
        # Startup assertions
        assert test_app.state.kafka_producer is not None
        assert test_app.state.kafka_consumer is not None
        assert test_app.state.redis_service is not None
        mock_kafka_producer_service.return_value.start.assert_awaited_once()
        mock_kafka_consumer_service.return_value.start.assert_awaited_once()
        mock_redis_service.return_value.start.assert_awaited_once()

    # Shutdown assertions
    mock_kafka_producer_service.return_value.stop.assert_awaited_once()
    mock_kafka_consumer_service.return_value.stop.assert_awaited_once()
    mock_redis_service.return_value.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_service_failures():
    test_app = FastAPI()
    with (
        patch(
            "app.main.KafkaProducerService.start",
            new=AsyncMock(side_effect=Exception("K boom")),
        ),
        patch(
            "app.main.RedisService.start",
            new=AsyncMock(side_effect=Exception("R boom")),
        ),
        patch(
            "app.main.KafkaConsumerService.start",
            new=AsyncMock(side_effect=Exception("C boom")),
        ),
        patch(
            "app.main.KafkaProducerService.stop",
            new=AsyncMock(side_effect=Exception("K stop boom")),
        ),
        patch(
            "app.main.RedisService.close",
            new=AsyncMock(side_effect=Exception("R stop boom")),
        ),
        patch(
            "app.main.KafkaConsumerService.stop",
            new=AsyncMock(side_effect=Exception("C stop boom")),
        ),
    ):
        async with lifespan(test_app):
            assert test_app.state.kafka_producer is None
            assert test_app.state.redis_service is None
            assert test_app.state.kafka_consumer is None


def test_health_check_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "services" in data


@patch("app.main.generate_latest", return_value="metrics_output")
def test_metrics_endpoint(mock_generate_latest):
    client = TestClient(app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.text == "metrics_output"
    mock_generate_latest.assert_called_once()
