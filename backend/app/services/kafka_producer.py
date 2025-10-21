"""Kafka producer service for sending metrics to Kafka stream."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KafkaProducerService:
    """
    A service for producing messages to a Kafka topic.

    This class encapsulates the logic for connecting to Kafka, sending messages,
    and handling the producer's lifecycle.

    Attributes:
        _bootstrap_servers: The comma-separated list of Kafka broker addresses.
        _producer: The `AIOKafkaProducer` instance, or None if not started.
    """

    def __init__(self, bootstrap_servers: str):
        """
        Initializes the KafkaProducerService.

        Args:
            bootstrap_servers: The bootstrap servers for the Kafka cluster.
        """
        self._bootstrap_servers = bootstrap_servers
        self._producer: AIOKafkaProducer | None = None

    async def start(self, retry_interval: int = 5, max_retries: int = 3):
        """
        Starts the Kafka producer and establishes a connection.

        This method attempts to connect to the Kafka brokers with a retry
        mechanism in case of connection failures.

        Args:
            retry_interval: The interval in seconds between connection retries.
            max_retries: The maximum number of connection attempts.

        Raises:
            KafkaConnectionError: If the producer fails to connect after the
                                  maximum number of retries.
        """
        retries = 0
        while self._producer is None and retries < max_retries:
            try:
                self._producer = AIOKafkaProducer(
                    bootstrap_servers=self._bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                )
                await self._producer.start()
                logger.info("Kafka producer started successfully.")
            except KafkaConnectionError:
                retries += 1
                logger.warning(
                    f"Failed to connect to Kafka. Retrying in {retry_interval}s... ({retries}/{max_retries})"
                )
                if retries >= max_retries:
                    logger.error("Max retries reached. Could not connect to Kafka.")
                    raise
                await asyncio.sleep(retry_interval)

    async def stop(self):
        """Stops the Kafka producer and closes the connection."""
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped.")
            self._producer = None

    async def send_metric(
        self,
        dashboard_id: int,
        name: str,
        value: float,
        metric_type: str = "gauge",
        timestamp: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """
        Serializes and sends a single metric message to the Kafka topic.

        Args:
            dashboard_id: The ID of the dashboard this metric belongs to.
            name: The name of the metric.
            value: The numerical value of the metric.
            metric_type: The type of the metric (e.g., 'gauge', 'counter').
            timestamp: The ISO format timestamp of the metric. Defaults to now.
            metadata: Additional key-value metadata for the metric.

        Raises:
            RuntimeError: If the producer has not been started.
            Exception: If the message fails to be sent.
        """
        if not self._producer:
            logger.error("Kafka producer is not started.")
            raise RuntimeError("Producer not started. Call start() first.")

        message = {
            "dashboard_id": dashboard_id,
            "name": name,
            "value": value,
            "metric_type": metric_type,
            "timestamp": timestamp or datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        try:
            await self._producer.send_and_wait(settings.KAFKA_TOPIC, message)
            logger.debug(f"Metric {name} sent to Kafka topic {settings.KAFKA_TOPIC}")
        except Exception as e:
            logger.error(f"Failed to send metric to Kafka: {e}")
            raise


from fastapi import Request


# Dependency for FastAPI
def get_kafka_producer(request: Request) -> "KafkaProducerService":
    """
    FastAPI dependency to get the Kafka producer from the app state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The singleton instance of the KafkaProducerService.

    Raises:
        RuntimeError: If the Kafka producer is not available in the app state.
    """
    if (
        not hasattr(request.app.state, "kafka_producer")
        or not request.app.state.kafka_producer
    ):
        raise RuntimeError("Kafka producer not available")
    return request.app.state.kafka_producer
