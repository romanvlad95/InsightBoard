"""
API endpoints for metric ingestion and management.

This module provides the main endpoint for high-throughput metric ingestion
via Kafka, as well as standard CRUD endpoints for direct metric management.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.metric import (
    MetricCreate,
    MetricDetailResponse,
    MetricIngest,
    MetricResponse,
    MetricUpdate,
)
from app.services.dashboard_service import DashboardService
from app.services.kafka_producer import KafkaProducerService
from app.services.metric_service import MetricService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/ingest", status_code=status.HTTP_202_ACCEPTED)
async def ingest_metrics(
    metrics: list[MetricIngest],
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """
    Accepts a batch of metrics for asynchronous processing via Kafka.

    This endpoint immediately returns a 202 Accepted response. It performs a
    quick ownership check on each metric's dashboard and then forwards valid
    metrics to a Kafka topic for ingestion by a background consumer.

    Args:
        metrics: A list of metrics to be ingested.
        request: The FastAPI request object, used to access the Kafka producer.
        db: The SQLAlchemy `AsyncSession` dependency.
        current_user: The authenticated user, injected by dependency.

    Returns:
        A confirmation message indicating how many metrics were accepted.
    """
    kafka_producer: KafkaProducerService = request.app.state.kafka_producer
    dashboard_service = DashboardService(db)

    processed_count = 0
    for metric in metrics:
        try:
            # Verify dashboard ownership for each metric
            dashboard = await dashboard_service.get_dashboard_by_id(metric.dashboard_id)
            if not dashboard or dashboard.owner_id != current_user.id:
                logger.warning(
                    f"User {current_user.id} attempted to ingest metric "
                    f"for unauthorized dashboard {metric.dashboard_id}"
                )
                continue  # Skip unauthorized metrics

            await kafka_producer.send_metric(
                dashboard_id=metric.dashboard_id,
                name=metric.name,
                value=metric.value,
                metric_type=metric.metric_type,
                timestamp=metric.timestamp,
                metadata=metric.metadata,
            )
            processed_count += 1
        except Exception as e:
            logger.error(
                f"Failed to send metric to Kafka for dashboard {metric.dashboard_id}: {e}",
                exc_info=True,
            )

    logger.info(
        f"Accepted {processed_count}/{len(metrics)} metrics for async processing."
    )
    return {
        "message": f"Accepted {processed_count}/{len(metrics)} metrics for processing"
    }


@router.post("/", response_model=MetricResponse, status_code=status.HTTP_201_CREATED)
async def create_metric(
    metric_in: MetricCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MetricResponse:
    """
    Creates a single new metric directly.

    This provides a way to create a metric synchronously, bypassing the
    Kafka queue. Ownership of the target dashboard is required.

    Args:
        metric_in: The data for the new metric from the request body.
        db: The SQLAlchemy `AsyncSession` dependency.
        current_user: The authenticated user, injected by dependency.

    Returns:
        The newly created metric.
    """
    service = MetricService(db)
    return await service.create_metric(user_id=current_user.id, data=metric_in)


@router.get("/{metric_id}", response_model=MetricDetailResponse)
async def get_metric(
    metric_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MetricDetailResponse:
    """
    Retrieves a single metric by its ID.

    Ensures that the metric belongs to a dashboard owned by the current user.

    Args:
        metric_id: The ID of the metric to retrieve.
        db: The SQLAlchemy `AsyncSession` dependency.
        current_user: The authenticated user, injected by dependency.

    Returns:
        The requested metric.

    Raises:
        HTTPException: If the metric is not found or not owned by the user.
    """
    service = MetricService(db)
    metric = await service.get_metric_by_id(
        metric_id=metric_id, user_id=current_user.id
    )
    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found"
        )
    return metric


@router.put("/{metric_id}", response_model=MetricResponse)
async def update_metric(
    metric_id: int,
    metric_in: MetricUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MetricResponse:
    """
    Updates an existing metric.

    Ensures that the metric belongs to a dashboard owned by the current user.

    Args:
        metric_id: The ID of the metric to update.
        metric_in: The new data for the metric from the request body.
        db: The SQLAlchemy `AsyncSession` dependency.
        current_user: The authenticated user, injected by dependency.

    Returns:
        The updated metric.

    Raises:
        HTTPException: If the metric is not found or not owned by the user.
    """
    service = MetricService(db)
    metric = await service.update_metric(
        metric_id=metric_id, user_id=current_user.id, data=metric_in
    )
    if not metric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found"
        )
    return metric


@router.delete("/{metric_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_metric(
    metric_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Deletes a metric.

    Ensures that the metric belongs to a dashboard owned by the current user.

    Args:
        metric_id: The ID of the metric to delete.
        db: The SQLAlchemy `AsyncSession` dependency.
        current_user: The authenticated user, injected by dependency.

    Raises:
        HTTPException: If the metric is not found or not owned by the user.
    """
    service = MetricService(db)
    if not await service.delete_metric(metric_id=metric_id, user_id=current_user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found"
        )
