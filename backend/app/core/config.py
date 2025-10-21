"""
Core application configuration module.

This module defines the configuration settings for the InsightBoard application.
It uses Pydantic's BaseSettings to load settings from environment variables
and .env files, providing a structured and type-safe way to manage configuration.
"""
import os
from collections.abc import Callable
from typing import Any

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Manages application-wide configuration settings.

    This class loads settings from environment variables and/or a .env file.
    It provides centralized access to all configuration parameters required
    by the application, such as database URLs, JWT secrets, and service addresses.

    Attributes:
        PROJECT_NAME: The name of the project.
        VERSION: The version of the application.
        API_V1_STR: The prefix for the v1 API routes.
        DATABASE_URL: The connection URL for the primary database.
        JWT_SECRET: The secret key used for signing JWTs.
        ALGORITHM: The algorithm used for JWT signing.
        ACCESS_TOKEN_EXPIRE_MINUTES: The expiration time for access tokens in minutes.
        ENVIRONMENT: The application's running environment (e.g., 'development', 'testing').
        REDIS_URL: The connection URL for Redis.
        REDIS_PUBSUB_CHANNEL_PATTERN: The pattern for Redis Pub/Sub channels.
        KAFKA_BOOTSTRAP_SERVERS: The bootstrap servers for the Kafka cluster.
        KAFKA_TOPIC: The default Kafka topic for metric streams.
        KAFKA_CONSUMER_GROUP: The consumer group ID for Kafka consumers.
    """

    PROJECT_NAME: str = "InsightBoard"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./test.db", description="Database connection URL"
    )

    JWT_SECRET: str = Field(
        default="your-secret-key-change-in-production", description="Secret key for JWT"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    ENVIRONMENT: str = Field(
        default="development",
        description="Environment: development, testing, production",
    )

    REDIS_URL: str = Field(
        default="redis://localhost:6379/0", description="Redis connection URL"
    )
    REDIS_PUBSUB_CHANNEL_PATTERN: str = "dashboard:*:metrics"

    KAFKA_BOOTSTRAP_SERVERS: str = "kafka:9092"
    KAFKA_TOPIC: str = "metrics-stream"
    KAFKA_CONSUMER_GROUP: str = "insightboard-consumers"

    class Config:
        """Pydantic model configuration for the Settings class."""

        case_sensitive = True
        env_file = ".env"

        @classmethod
        def customise_sources(
            cls,
            init_settings: Callable[..., Any],
            env_settings: Callable[..., Any],
            file_secret_settings: Callable[..., Any],
        ) -> tuple[Callable[..., Any], ...]:
            """
            Customizes the settings sources to load the correct .env file.

            This method dynamically selects the .env file based on the `ENVIRONMENT`
            environment variable. It loads from `.env.test` if `ENVIRONMENT` is
            'testing', otherwise it defaults to `.env`.

            Args:
                init_settings: The source for settings from model initialization.
                env_settings: The source for settings from environment variables.
                file_secret_settings: The source for settings from secrets files.

            Returns:
                A tuple of customized settings sources.
            """
            if os.getenv("ENVIRONMENT") == "testing":
                return (
                    init_settings,
                    env_settings,
                    lambda s: load_dotenv(dotenv_path=".env.test", override=True),
                    file_secret_settings,
                )
            return (
                init_settings,
                env_settings,
                lambda s: load_dotenv(dotenv_path=".env", override=True),
                file_secret_settings,
            )


settings = Settings()
