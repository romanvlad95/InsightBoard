import asyncio
from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from aiokafka.errors import KafkaConnectionError

from app.core.config import settings
from app.models.metric import Metric
from app.services.kafka_consumer import KafkaConsumerService
from app.services.kafka_producer import KafkaProducerService

pytestmark = pytest.mark.asyncio

BOOTSTRAP_SERVERS = "mock_kafka:9092"
TEST_TOPIC = "test_topic"
TEST_GROUP_ID = "test_group"

# --------------------------------------------------------------------
# KafkaProducerService Tests
# --------------------------------------------------------------------


@patch("app.services.kafka_producer.AIOKafkaProducer")
async def test_producer_start_stop(MockAIOProducer):
    mock_instance = AsyncMock()
    MockAIOProducer.return_value = mock_instance
    service = KafkaProducerService(BOOTSTRAP_SERVERS)

    await service.start()
    await service.stop()

    mock_instance.start.assert_awaited_once()
    mock_instance.stop.assert_awaited_once()


@patch("app.services.kafka_producer.AIOKafkaProducer")
async def test_producer_send_metric_success(MockAIOProducer):
    mock_instance = AsyncMock()
    MockAIOProducer.return_value = mock_instance
    service = KafkaProducerService(BOOTSTRAP_SERVERS)
    await service.start()

    data = {"dashboard_id": 1, "name": "test_metric", "value": 123.45}
    await service.send_metric(**data)

    mock_instance.send_and_wait.assert_awaited_once_with(settings.KAFKA_TOPIC, ANY)
    sent = mock_instance.send_and_wait.call_args[0][1]
    assert sent["name"] == "test_metric"

    await service.stop()


async def test_producer_send_metric_not_started():
    service = KafkaProducerService(BOOTSTRAP_SERVERS)
    with pytest.raises(RuntimeError, match="Producer not started"):
        await service.send_metric(dashboard_id=1, name="cpu", value=1.0)


@patch("asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.kafka_producer.AIOKafkaProducer")
async def test_producer_start_retry_behavior(MockAIOProducer, mock_sleep):
    mock_start = AsyncMock(side_effect=KafkaConnectionError("fail"))
    MockAIOProducer.return_value.start = mock_start
    service = KafkaProducerService(BOOTSTRAP_SERVERS)

    await service.start(retry_interval=0.1, max_retries=3)
    mock_start.assert_awaited_once()
    mock_sleep.assert_awaited_once()


@patch("asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.kafka_producer.AIOKafkaProducer")
async def test_producer_start_raises_on_max_retry(MockAIOProducer, mock_sleep):
    mock_start = AsyncMock(side_effect=KafkaConnectionError("fail"))
    MockAIOProducer.return_value.start = mock_start
    service = KafkaProducerService(BOOTSTRAP_SERVERS)

    with pytest.raises(KafkaConnectionError):
        await service.start(retry_interval=0.1, max_retries=1)

    mock_start.assert_awaited_once()
    mock_sleep.assert_not_awaited()


# --------------------------------------------------------------------
# KafkaConsumerService Tests
# --------------------------------------------------------------------


def create_mock_kafka_message(value: dict) -> MagicMock:
    msg = MagicMock()
    msg.value = value
    return msg


@patch("app.services.kafka_consumer.AIOKafkaConsumer")
async def test_consumer_start_stop(MockAIOConsumer):
    mock_consumer = AsyncMock()
    MockAIOConsumer.return_value = mock_consumer
    service = KafkaConsumerService(BOOTSTRAP_SERVERS, TEST_TOPIC, TEST_GROUP_ID)

    async def dummy_process():
        await asyncio.sleep(0)

    real_task = asyncio.create_task(dummy_process())
    real_task.cancel = MagicMock()

    with patch(
        "asyncio.create_task", return_value=real_task
    ) as mock_create_task, patch.object(service, "_process_messages", dummy_process):
        await service.start()
        mock_consumer.start.assert_awaited_once()
        mock_create_task.assert_called_once()

        await service.stop()
        mock_consumer.stop.assert_awaited_once()
        real_task.cancel.assert_called_once()
        await asyncio.sleep(0)


@patch("asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.kafka_consumer.AIOKafkaConsumer")
async def test_consumer_start_retry(MockAIOConsumer, mock_sleep):
    MockAIOConsumer.side_effect = KafkaConnectionError("conn fail")
    service = KafkaConsumerService(BOOTSTRAP_SERVERS, TEST_TOPIC, TEST_GROUP_ID)

    with pytest.raises(KafkaConnectionError):
        await service.start(retry_interval=0.1, max_retries=3)

    assert MockAIOConsumer.call_count == 3
    assert mock_sleep.call_count == 2


@patch("app.services.kafka_consumer.async_session_maker")
@patch("app.services.kafka_consumer.MetricService")
@patch("app.main.app.state")
@patch("app.services.kafka_consumer.AIOKafkaConsumer")
async def test_consumer_process_message_success(
    MockAIOConsumer, mock_app_state, MockMetricService, mock_session_maker
):
    mock_consumer = AsyncMock()
    valid_data = {
        "dashboard_id": 1,
        "name": "cpu_usage",
        "value": 0.75,
        "metric_type": "gauge",
    }
    msg = create_mock_kafka_message(valid_data)
    mock_consumer.__aiter__.return_value = iter([msg])
    MockAIOConsumer.return_value = mock_consumer

    mock_metric = AsyncMock()
    mock_metric.create_metric_internal.return_value = Metric(**valid_data, id=1)
    MockMetricService.return_value = mock_metric
    mock_app_state.redis_service.publish_metric_update = AsyncMock()
    mock_session_maker.return_value.__aenter__.return_value = AsyncMock()

    service = KafkaConsumerService(BOOTSTRAP_SERVERS, TEST_TOPIC, TEST_GROUP_ID)
    service._consumer = mock_consumer
    service._running = True

    await service._process_messages()

    mock_metric.create_metric_internal.assert_awaited_once()
    mock_app_state.redis_service.publish_metric_update.assert_awaited_once()
    mock_consumer.commit.assert_awaited_once()


@patch("app.services.kafka_consumer.AIOKafkaConsumer")
async def test_consumer_process_invalid_message(MockAIOConsumer):
    mock_consumer = AsyncMock()
    invalid_data = {"name": "cpu", "value": 0.5}
    msg = create_mock_kafka_message(invalid_data)
    mock_consumer.__aiter__.return_value = iter([msg])
    MockAIOConsumer.return_value = mock_consumer

    with patch("app.services.kafka_consumer.MetricService") as MockMetricService, patch(
        "app.services.kafka_consumer.async_session_maker"
    ) as mock_session_maker:
        mock_session_maker.return_value.__aenter__.return_value = AsyncMock()
        async_metric_mock = AsyncMock()
        MockMetricService.return_value.create_metric_internal = async_metric_mock

        service = KafkaConsumerService(BOOTSTRAP_SERVERS, TEST_TOPIC, TEST_GROUP_ID)
        service._consumer = mock_consumer
        service._running = True
        await service._process_messages()

        async_metric_mock.assert_not_awaited()
        mock_consumer.commit.assert_awaited_once()


@patch("app.services.kafka_consumer.AIOKafkaConsumer")
async def test_consumer_process_db_exception(MockAIOConsumer):
    mock_consumer = AsyncMock()
    valid_data = {"dashboard_id": 1, "name": "cpu_usage", "value": 0.75}
    msg = create_mock_kafka_message(valid_data)
    mock_consumer.__aiter__.return_value = iter([msg])
    MockAIOConsumer.return_value = mock_consumer

    with patch("app.services.kafka_consumer.async_session_maker") as mock_maker:
        mock_maker.return_value.__aenter__.side_effect = Exception("DB fail")

        service = KafkaConsumerService(BOOTSTRAP_SERVERS, TEST_TOPIC, TEST_GROUP_ID)
        service._consumer = mock_consumer
        service._running = True

        await service._process_messages()
        mock_consumer.commit.assert_awaited_once()


@patch("app.main.app.state")
@patch("app.services.kafka_consumer.MetricService")
async def test_process_single_metric_redis_failure(MockMetricService, mock_app_state):
    mock_db = AsyncMock()
    service = KafkaConsumerService(BOOTSTRAP_SERVERS, TEST_TOPIC, TEST_GROUP_ID)
    metric = {"dashboard_id": 1, "name": "test", "value": 1.0, "metric_type": "gauge"}

    mock_metric = AsyncMock()
    mock_metric.create_metric_internal.return_value = Metric(**metric, id=1)
    MockMetricService.return_value = mock_metric

    mock_app_state.redis_service.publish_metric_update.side_effect = Exception(
        "Redis down"
    )

    with patch("app.services.kafka_consumer.logger.warning") as mock_log:
        await service._process_single_metric(mock_db, metric)
        mock_log.assert_called_with("Failed to publish to Redis: Redis down")
