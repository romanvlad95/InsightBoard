"""
Main application module for the InsightBoard FastAPI service.

This module initializes the FastAPI application, sets up middleware,
defines the application lifespan for managing background services,
and includes the main API router.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.responses import Response

from app.api.v1 import api_router
from app.core.config import settings
from app.services.kafka_consumer import KafkaConsumerService
from app.services.kafka_producer import KafkaProducerService
from app.services.redis_service import RedisService

# Configure logging for the application.
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Manages the startup and shutdown of background services.

    This asynchronous context manager is used by FastAPI to handle application
    lifespan events. It initializes and starts the Kafka producer, Kafka consumer,
    and Redis service on startup, and gracefully stops them on shutdown.

    Args:
        app: The FastAPI application instance.

    Yields:
        None. The application runs while the context is active.
    """
    logger.info("Initializing InsightBoard services...")

    # Initialize and start Kafka Producer
    kafka_producer = KafkaProducerService(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
    )
    try:
        await kafka_producer.start()
        app.state.kafka_producer = kafka_producer
        logger.info("Kafka Producer started successfully.")
    except Exception as e:
        logger.error(f"Failed to start Kafka Producer: {e}")
        app.state.kafka_producer = None

    # Initialize and start Redis Service
    redis_service = RedisService(redis_url=settings.REDIS_URL)
    try:
        await redis_service.start()
        app.state.redis_service = redis_service
        logger.info("Redis Service started successfully.")
    except Exception as e:
        logger.error(f"Failed to start Redis Service: {e}")
        app.state.redis_service = None

    # Initialize and start Kafka Consumer
    kafka_consumer = KafkaConsumerService(
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        topic=settings.KAFKA_TOPIC,
        group_id=settings.KAFKA_CONSUMER_GROUP,
    )
    try:
        await kafka_consumer.start()
        app.state.kafka_consumer = kafka_consumer
        logger.info("Kafka Consumer started successfully.")
    except Exception as e:
        logger.error(f"Failed to start Kafka Consumer: {e}")
        app.state.kafka_consumer = None

    logger.info("All services initialized.")

    yield

    logger.info("Shutting down InsightBoard services...")

    # Stop Kafka Consumer
    if getattr(app.state, "kafka_consumer", None):
        try:
            await app.state.kafka_consumer.stop()
            logger.info("Kafka Consumer stopped.")
        except Exception as e:
            logger.error(f"Error stopping Kafka Consumer: {e}")

    # Stop Kafka Producer
    if getattr(app.state, "kafka_producer", None):
        try:
            await app.state.kafka_producer.stop()
            logger.info("Kafka Producer stopped.")
        except Exception as e:
            logger.error(f"Error stopping Kafka Producer: {e}")

    # Close Redis Service
    if getattr(app.state, "redis_service", None):
        try:
            await app.state.redis_service.close()
            logger.info("Redis Service closed.")
        except Exception as e:
            logger.error(f"Error closing Redis Service: {e}")

    logger.info("All services shut down gracefully.")


# Initialize the FastAPI application.
app = FastAPI(
    title="InsightBoard API",
    description="Real-time analytics dashboard with Kafka streaming",
    version=settings.VERSION,
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS) middleware.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict:
    """
    Provides a health check of the API and its background services.

    This endpoint can be used for monitoring and to verify that the main
    application and its critical services (Kafka, Redis) are running.

    Returns:
        A dictionary containing the overall status and the status
        of each individual service.
    """
    services_status = {
        "api": "healthy",
        "kafka_producer": "healthy"
        if getattr(app.state, "kafka_producer", None)
        else "unavailable",
        "kafka_consumer": "healthy"
        if getattr(app.state, "kafka_consumer", None)
        else "unavailable",
        "redis": "healthy"
        if getattr(app.state, "redis_service", None)
        else "unavailable",
    }

    return {"status": "ok", "services": services_status}


@app.get("/metrics")
def metrics() -> Response:
    """
    Exposes application metrics in Prometheus format.

    This endpoint is scraped by a Prometheus server to collect metrics
    about the application's performance and behavior.

    Returns:
        A Starlette Response object containing the metrics data in a
        Prometheus-compatible format.
    """
    return Response(media_type=CONTENT_TYPE_LATEST, content=generate_latest())


# Include the main API router.
app.include_router(api_router, prefix=settings.API_V1_STR)
