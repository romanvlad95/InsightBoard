"""Kafka consumer service for processing metric stream."""

import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError, KafkaError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_maker
from app.schemas.metric import MetricCreate
from app.services.metric_service import MetricService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KafkaConsumerService:
    """
    Service for consuming and processing metric messages from a Kafka topic.

    This service runs as a background task, continuously fetching messages,
    validating them, storing them in the database, and publishing them to
    Redis for real-time distribution to clients via WebSockets.

    Attributes:
        _bootstrap_servers: The Kafka broker addresses.
        _topic: The Kafka topic to consume from.
        _group_id: The consumer group ID.
        _consumer: The `AIOKafkaConsumer` instance.
        _task: The asyncio Task running the message processing loop.
        _running: A flag to control the running state of the consumer loop.
    """

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
    ):
        """
        Initializes the KafkaConsumerService.

        Args:
            bootstrap_servers: The bootstrap servers for the Kafka cluster.
            topic: The Kafka topic to subscribe to.
            group_id: The ID of the consumer group.
        """
        self._bootstrap_servers = bootstrap_servers
        self._topic = topic
        self._group_id = group_id
        self._consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None
        self._running = False

    async def start(self, retry_interval: int = 5, max_retries: int = 3) -> None:
        """
        Starts the Kafka consumer and begins processing messages.

        Establishes a connection to Kafka with a retry mechanism and creates a
        background task to process incoming messages.

        Args:
            retry_interval: The interval in seconds between connection retries.
            max_retries: The maximum number of connection attempts.

        Raises:
            KafkaConnectionError: If the consumer fails to connect after the
                                  maximum number of retries.
        """
        if self._consumer is not None:
            logger.warning("Kafka consumer already started.")
            return

        retries = 0
        while self._consumer is None and retries < max_retries:
            try:
                self._consumer = AIOKafkaConsumer(
                    self._topic,
                    bootstrap_servers=self._bootstrap_servers,
                    group_id=self._group_id,
                    auto_offset_reset="earliest",
                    enable_auto_commit=False,  # Manual commit after processing
                    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                    session_timeout_ms=30000,
                    request_timeout_ms=40000,
                )
                await self._consumer.start()
                self._running = True
                logger.info(
                    f"Kafka consumer started successfully "
                    f"(topic: {self._topic}, group: {self._group_id})"
                )
                # Start background processing task
                self._task = asyncio.create_task(self._process_messages())
            except KafkaConnectionError as e:
                retries += 1
                logger.warning(
                    f"Failed to connect to Kafka: {e}. "
                    f"Retrying in {retry_interval}s... ({retries}/{max_retries})"
                )
                if retries >= max_retries:
                    logger.error("Max retries reached. Could not connect to Kafka.")
                    raise
                await asyncio.sleep(retry_interval)

    async def stop(self) -> None:
        """
        Stops the Kafka consumer and the message processing task gracefully.
        """
        self._running = False

        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logger.info("Message processing task cancelled.")
            self._task = None

        if self._consumer:
            await self._consumer.stop()
            logger.info("Kafka consumer stopped.")
            self._consumer = None

    async def _process_messages(self) -> None:
        """
        Continuously fetches and processes messages from the Kafka topic.

        This method runs in a loop, handling message deserialization,
        validation, processing via `_process_single_metric`, and manual
        offset committing.

        Raises:
            asyncio.CancelledError: If the processing task is cancelled.
            KafkaError: If a non-recoverable Kafka error occurs.
        """
        if not self._consumer:
            logger.error("Consumer not initialized, cannot process messages.")
            return

        processed_count = 0
        error_count = 0

        try:
            async for msg in self._consumer:
                if not self._running:
                    break

                try:
                    logger.debug(
                        f"Consumed message from {msg.topic} "
                        f"(partition={msg.partition}, offset={msg.offset})"
                    )

                    metric_data = msg.value

                    # Validate required fields
                    if "dashboard_id" not in metric_data:
                        logger.error(
                            f"Missing 'dashboard_id' in message: {metric_data}"
                        )
                        await self._consumer.commit()
                        error_count += 1
                        continue

                    # Process metric using database session
                    async with async_session_maker() as db:
                        await self._process_single_metric(db, metric_data)

                    # Commit offset after successful processing
                    await self._consumer.commit()
                    processed_count += 1

                    if processed_count % 100 == 0:
                        logger.info(
                            f"Processed {processed_count} messages (errors: {error_count})"
                        )

                except Exception as e:
                    logger.error(
                        f"Error processing message: {e}. Message: {msg.value}",
                        exc_info=True,
                    )
                    error_count += 1
                    # Commit to avoid reprocessing the same bad message
                    await self._consumer.commit()

        except asyncio.CancelledError:
            logger.info("Message processing was cancelled.")
            raise
        except KafkaError as e:
            logger.error(f"Kafka error during message processing: {e}")
            raise
        finally:
            logger.info(
                f"Consumer stopped. Total processed: {processed_count}, Total errors: {error_count}"
            )

    async def _process_single_metric(self, db: AsyncSession, metric_data: dict) -> None:
        """
        Processes a single metric by storing it and publishing it.

        This involves creating a database record for the metric and then
        publishing an update to a Redis Pub/Sub channel for real-time
        distribution.

        Args:
            db: The SQLAlchemy `AsyncSession` to use for database operations.
            metric_data: A dictionary containing the deserialized metric data
                         from the Kafka message.
        """
        metric_service = MetricService(db)

        # Create metric schema from Kafka message
        metric_create = MetricCreate(
            name=metric_data["name"],
            value=metric_data["value"],
            metric_type=metric_data.get("metric_type", "gauge"),
            dashboard_id=metric_data["dashboard_id"],
        )

        # Store metric in database (no auth check)
        created_metric = await metric_service.create_metric_internal(metric_create)

        # Get Redis service from app.state and publish update
        try:
            # Import here to avoid circular dependency at the module level.
            from app.main import app

            if hasattr(app.state, "redis_service") and app.state.redis_service:
                redis_service = app.state.redis_service
                await redis_service.publish_metric_update(
                    dashboard_id=created_metric.dashboard_id,
                    metric_data={
                        "id": created_metric.id,
                        "name": created_metric.name,
                        "value": created_metric.value,
                        "metric_type": created_metric.metric_type,
                        "dashboard_id": created_metric.dashboard_id,
                        "created_at": created_metric.created_at.isoformat()
                        if created_metric.created_at
                        else None,
                    },
                )
        except Exception as e:
            # If Redis publish fails, just log it - metric is already in DB
            logger.warning(f"Failed to publish to Redis: {e}")

        logger.debug(
            f"Processed metric '{created_metric.name}' "
            f"for dashboard {created_metric.dashboard_id}"
        )
