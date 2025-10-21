import asyncio
import logging
import math
import random
from datetime import UTC, datetime
from typing import Any

from app.services.kafka_producer import KafkaProducerService

logger = logging.getLogger(__name__)


class DataGenerator:
    """Generate synthetic metric data for testing and demonstration."""

    def __init__(self, kafka_producer: KafkaProducerService):
        self._producer = kafka_producer
        self._counter_values: dict[str, float] = {}

    async def generate_metrics(
        self,
        dashboard_id: int,
        duration_seconds: int = 60,
        rate_per_second: float = 1.0,
        metric_specs: list[dict[str, Any]] | None = None,
    ):
        """
        Generates and sends metrics to Kafka for a specified duration and rate.

        Args:
            dashboard_id: The dashboard ID to associate with the metrics.
            duration_seconds: How long to generate metrics for.
            rate_per_second: The number of metrics to generate per second.
            metric_specs: A list of specifications for metrics to generate.
                          If None, a default set of metrics is used.
        """
        if rate_per_second <= 0:
            raise ValueError("Rate must be positive")

        if metric_specs is None:
            metric_specs = [
                {"name": "cpu_usage", "type": "gauge"},
                {"name": "memory_mb", "type": "gauge"},
                {"name": "request_count", "type": "counter"},
                {"name": "response_time_ms", "type": "histogram"},
            ]

        interval = 1.0 / rate_per_second
        end_time = asyncio.get_event_loop().time() + duration_seconds
        iteration = 0

        logger.info(
            f"Starting data generation for dashboard {dashboard_id} for {duration_seconds}s "
            f"at {rate_per_second} metrics/sec."
        )

        while asyncio.get_event_loop().time() < end_time:
            start_loop_time = asyncio.get_event_loop().time()

            for spec in metric_specs:
                await self._generate_and_send(dashboard_id, spec, iteration)

            iteration += 1

            # Sleep to maintain the desired rate
            elapsed = asyncio.get_event_loop().time() - start_loop_time
            sleep_duration = max(0, interval - elapsed)
            await asyncio.sleep(sleep_duration)

        logger.info(f"Finished data generation for dashboard {dashboard_id}")

    async def _generate_and_send(
        self, dashboard_id: int, spec: dict[str, Any], iteration: int
    ):
        """Generate a single metric based on its spec and send it."""
        metric_type = spec.get("type", "gauge")
        name = spec["name"]
        value = 0.0

        if metric_type == "counter":
            value = self._generate_counter(name)
        elif metric_type == "gauge":
            value = self._generate_gauge(name, iteration, **spec.get("params", {}))
        elif metric_type == "histogram":
            value = self._generate_histogram(name, **spec.get("params", {}))
        else:
            logger.warning(f"Unknown metric type: {metric_type}")
            return

        try:
            await self._producer.send_metric(
                dashboard_id=dashboard_id,
                name=name,
                value=value,
                metric_type=metric_type,
                timestamp=datetime.now(UTC).isoformat(),
                metadata={"source": "data_generator"},
            )
        except Exception as e:
            logger.error(f"Failed to send generated metric to Kafka: {e}")

    def _generate_counter(self, name: str) -> float:
        """Generates a monotonically increasing counter value."""
        current_value = self._counter_values.get(name, 0)
        new_value = current_value + random.uniform(1, 10)
        self._counter_values[name] = new_value
        return new_value

    def _generate_gauge(
        self, name: str, iteration: int, base=50, amplitude=40, freq=20
    ) -> float:
        """Generates a fluctuating gauge value, often using a sine wave."""
        noise = random.uniform(-amplitude / 10, amplitude / 10)
        # Sine wave to simulate periodic patterns (e.g., daily traffic)
        return base + amplitude * math.sin(iteration / freq) + noise

    def _generate_histogram(self, name: str, mean=100, std_dev=20) -> float:
        """Generates a value from a normal distribution, for histograms."""
        return max(0, random.gauss(mean, std_dev))
