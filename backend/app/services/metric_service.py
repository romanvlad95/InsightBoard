"""
Service layer for metric-related business logic.

This module provides the MetricService class, which encapsulates the logic
for creating, retrieving, updating, and deleting metrics, including
ownership verification.
"""


from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.dashboard import Dashboard
from app.models.metric import Metric
from app.schemas.metric import MetricCreate, MetricUpdate


class MetricService:
    """
    Encapsulates business logic for metric operations.

    Attributes:
        db: The SQLAlchemy `AsyncSession` instance for database access.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the MetricService.

        Args:
            db: The SQLAlchemy `AsyncSession` to use for database operations.
        """
        self.db = db

    async def create_metric(self, user_id: int, data: MetricCreate) -> Metric:
        """
        Creates a new metric after verifying dashboard ownership.

        Args:
            user_id: The ID of the user attempting to create the metric.
            data: The data for the new metric.

        Returns:
            The newly created Metric object.

        Raises:
            HTTPException: If the dashboard is not found or the user does not
                           have permission to access it.
        """
        dashboard_result = await self.db.execute(
            select(Dashboard).where(Dashboard.id == data.dashboard_id)
        )
        dashboard = dashboard_result.scalars().first()

        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found",
            )

        if dashboard.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        new_metric = Metric(**data.model_dump())
        self.db.add(new_metric)
        await self.db.commit()
        await self.db.refresh(new_metric)
        return new_metric

    async def create_metric_internal(self, data: MetricCreate) -> Metric:
        """
        Creates a new metric without ownership checks.

        This method is intended for internal use by services like the Kafka
        consumer, where ownership has been implicitly verified or is not
        required.

        Args:
            data: The data for the new metric.

        Returns:
            The newly created Metric object.
        """
        new_metric = Metric(**data.model_dump())
        self.db.add(new_metric)
        await self.db.commit()
        await self.db.refresh(new_metric)
        return new_metric

    async def get_metric_by_id(self, metric_id: int, user_id: int) -> Metric | None:
        """
        Retrieves a single metric by its ID, ensuring user ownership.

        Ownership is checked by verifying that the user owns the dashboard
        to which the metric belongs.

        Args:
            metric_id: The ID of the metric to retrieve.
            user_id: The ID of the user requesting the metric.

        Returns:
            The Metric object if found and owned by the user, otherwise None.
        """
        result = await self.db.execute(
            select(Metric)
            .options(joinedload(Metric.dashboard))
            .where(Metric.id == metric_id)
        )
        metric = result.scalars().first()

        if metric and metric.dashboard.owner_id == user_id:
            return metric
        return None

    async def update_metric(
        self, metric_id: int, user_id: int, data: MetricUpdate
    ) -> Metric | None:
        """
        Updates a metric's data after verifying ownership.

        Args:
            metric_id: The ID of the metric to update.
            user_id: The ID of the user requesting the update.
            data: The new data for the metric.

        Returns:
            The updated Metric object, or None if the metric was not found
            or the user does not have permission.
        """
        metric = await self.get_metric_by_id(metric_id, user_id)
        if not metric:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(metric, key, value)

        await self.db.commit()
        await self.db.refresh(metric)
        return metric

    async def delete_metric(self, metric_id: int, user_id: int) -> bool:
        """
        Deletes a metric after verifying ownership.

        Args:
            metric_id: The ID of the metric to delete.
            user_id: The ID of the user requesting the deletion.

        Returns:
            True if the metric was successfully deleted, False otherwise.
        """
        metric = await self.get_metric_by_id(metric_id, user_id)
        if not metric:
            return False

        await self.db.delete(metric)
        await self.db.commit()
        return True

    async def get_dashboard_metrics(
        self, dashboard_id: int, user_id: int
    ) -> list[Metric]:
        """
        Retrieves all metrics for a specific dashboard, verifying ownership.

        Args:
            dashboard_id: The ID of the dashboard whose metrics are to be retrieved.
            user_id: The ID of the user making the request.

        Returns:
            A list of Metric objects belonging to the dashboard.

        Raises:
            HTTPException: If the dashboard is not found or the user does not
                           have permission to access it.
        """
        dashboard_result = await self.db.execute(
            select(Dashboard).where(Dashboard.id == dashboard_id)
        )
        dashboard = dashboard_result.scalars().first()

        if not dashboard:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dashboard not found",
            )

        if dashboard.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )

        result = await self.db.execute(
            select(Metric).where(Metric.dashboard_id == dashboard_id)
        )
        return result.scalars().all()
