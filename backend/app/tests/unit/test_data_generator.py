from unittest.mock import AsyncMock, patch

import pytest

from app.services.data_generator import DataGenerator


@pytest.fixture
def mock_kafka_producer():
    return AsyncMock()


@pytest.fixture
def generator(mock_kafka_producer):
    return DataGenerator(kafka_producer=mock_kafka_producer)


@pytest.mark.asyncio
async def test_generate_metrics_invalid_rate_raises_error(generator):
    with pytest.raises(ValueError, match="Rate must be positive"):
        await generator.generate_metrics(dashboard_id=1, rate_per_second=0)


@pytest.mark.asyncio
@patch("asyncio.sleep", new_callable=AsyncMock)
async def test_generate_metrics_runs_with_defaults(
    mock_sleep, generator, mock_kafka_producer
):
    """Smoke test to ensure generator runs and calls producer."""
    with patch.object(
        generator, "_generate_and_send", new_callable=AsyncMock
    ) as mock_gen_send:
        await generator.generate_metrics(
            dashboard_id=1, duration_seconds=1, rate_per_second=1
        )
        assert mock_gen_send.call_count >= 1
        # Expect 4 default metrics
        assert mock_gen_send.call_args_list[0][0][1]["name"] == "cpu_usage"


@pytest.mark.asyncio
async def test_generate_and_send_known_types(generator, mock_kafka_producer):
    with (
        patch.object(generator, "_generate_counter", return_value=1.0) as mock_counter,
        patch.object(generator, "_generate_gauge", return_value=2.0) as mock_gauge,
        patch.object(generator, "_generate_histogram", return_value=3.0) as mock_hist,
    ):
        await generator._generate_and_send(1, {"name": "m1", "type": "counter"}, 0)
        mock_counter.assert_called_once_with("m1")
        mock_kafka_producer.send_metric.assert_awaited()

        await generator._generate_and_send(1, {"name": "m2", "type": "gauge"}, 0)
        mock_gauge.assert_called_once_with("m2", 0, **{})

        await generator._generate_and_send(1, {"name": "m3", "type": "histogram"}, 0)
        mock_hist.assert_called_once_with("m3", **{})


@pytest.mark.asyncio
async def test_generate_and_send_unknown_type(generator, mock_kafka_producer):
    await generator._generate_and_send(1, {"name": "m4", "type": "unknown"}, 0)
    mock_kafka_producer.send_metric.assert_not_awaited()


@pytest.mark.asyncio
async def test_generate_and_send_kafka_error(generator, mock_kafka_producer):
    mock_kafka_producer.send_metric.side_effect = Exception("Kafka is down")
    # The exception should be caught and logged, not raised
    await generator._generate_and_send(1, {"name": "m1", "type": "counter"}, 0)
    assert mock_kafka_producer.send_metric.call_count == 1


def test_private_generator_functions(generator):
    # Set a seed for deterministic results
    import random

    random.seed(0)

    # Test counter
    assert generator._generate_counter("c1") > 0
    assert generator._generate_counter("c1") > 1

    # Test gauge
    assert isinstance(generator._generate_gauge("g1", 0), float)

    # Test histogram
    assert isinstance(generator._generate_histogram("h1"), float)
