"""Redis service for pub/sub messaging."""

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from redis.asyncio import ConnectionPool, Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


class RedisService:
    """
    A service for interacting with Redis, primarily for Pub/Sub messaging.

    This class manages the Redis connection pool and provides methods for
    publishing messages to channels and subscribing to them.

    Attributes:
        _redis_url: The connection URL for the Redis server.
        _pool: The `ConnectionPool` instance for managing Redis connections.
        _redis: The `Redis` client instance.
    """

    def __init__(self, redis_url: str):
        """
        Initializes the RedisService.

        Args:
            redis_url: The connection URL for the Redis server.
        """
        self._redis_url = redis_url
        self._pool: ConnectionPool | None = None
        self._redis: Redis | None = None

    async def start(self):
        """Initializes the Redis connection pool and client."""
        if self._redis:
            return

        self._pool = ConnectionPool.from_url(
            self._redis_url,
            decode_responses=True,
            max_connections=10,
        )
        self._redis = Redis(connection_pool=self._pool)
        await self._redis.ping()
        logger.info("Redis service started and connection confirmed.")

    async def close(self):
        """Closes the Redis client and connection pool gracefully."""
        if self._redis:
            await self._redis.close()
        if self._pool:
            await self._pool.disconnect()
        logger.info("Redis connection closed.")

    async def publish_metric_update(
        self, dashboard_id: int, metric_data: dict[str, Any]
    ):
        """
        Publishes a metric update to a dashboard-specific Redis channel.

        Args:
            dashboard_id: The ID of the dashboard to which the metric belongs.
            metric_data: A dictionary containing the metric data to be published.

        Raises:
            RuntimeError: If the Redis service has not been started.
            RedisError: If the publish command fails.
        """
        if not self._redis:
            raise RuntimeError("Redis service is not started.")

        channel = f"dashboard:{dashboard_id}:metrics"
        message = json.dumps(metric_data)
        try:
            await self._redis.publish(channel, message)
            logger.debug(f"Published metric to Redis channel {channel}")
        except RedisError as e:
            logger.error(f"Failed to publish to Redis: {e}")
            raise

    async def subscribe_to_dashboard(
        self, dashboard_id: int
    ) -> AsyncGenerator[dict[str, Any], None]:
        """
        Subscribes to a dashboard's metric updates channel and yields messages.

        This method creates a new Redis connection to handle the subscription,
        listens for messages, and yields them as they arrive. It ensures
        proper cleanup of the subscription and connection.

        Args:
            dashboard_id: The ID of the dashboard to subscribe to.

        Yields:
            A dictionary containing the JSON-decoded metric data from a message.

        Raises:
            RuntimeError: If the Redis service has not been started.
        """
        if not self._pool:
            raise RuntimeError("Redis service is not started.")

        channel = f"dashboard:{dashboard_id}:metrics"

        # Create separate connection for pubsub
        pubsub_redis = Redis(connection_pool=self._pool)
        pubsub = pubsub_redis.pubsub()

        try:
            await pubsub.subscribe(channel)
            logger.info(f"Subscribed to Redis channel {channel}")

            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        yield json.loads(message["data"])
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to decode message: {e}")
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
            await pubsub_redis.close()
            logger.info(f"Unsubscribed from Redis channel {channel}")


from fastapi import Request


# Dependency for FastAPI
def get_redis_service(request: Request) -> "RedisService":
    """
    FastAPI dependency to get the Redis service from the app state.

    Args:
        request: The incoming FastAPI request.

    Returns:
        The singleton instance of the RedisService.

    Raises:
        RuntimeError: If the Redis service is not available in the app state.
    """
    if (
        not hasattr(request.app.state, "redis_service")
        or not request.app.state.redis_service
    ):
        raise RuntimeError("Redis service not available")
    return request.app.state.redis_service
