"""
Service layer for dashboard-related business logic.

This module provides the DashboardService class, which encapsulates the logic
for creating, retrieving, updating, and deleting dashboards.
"""


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.dashboard import Dashboard
from app.schemas.dashboard import DashboardCreate, DashboardUpdate


class DashboardService:
    """
    Encapsulates business logic for dashboard operations.

    Attributes:
        db: The SQLAlchemy `AsyncSession` instance for database access.
    """

    def __init__(self, db: AsyncSession):
        """
        Initializes the DashboardService.

        Args:
            db: The SQLAlchemy `AsyncSession` to use for database operations.
        """
        self.db = db

    async def get_user_dashboards(self, user_id: int) -> list[Dashboard]:
        """
        Retrieves all dashboards owned by a specific user.

        Args:
            user_id: The ID of the user whose dashboards are to be retrieved.

        Returns:
            A list of Dashboard objects owned by the user, ordered by creation date.
        """
        result = await self.db.execute(
            select(Dashboard)
            .where(Dashboard.owner_id == user_id)
            .order_by(Dashboard.created_at.desc())
        )
        return result.scalars().all()

    async def get_dashboard_by_id(self, dashboard_id: int) -> Dashboard | None:
        """
        Retrieves a single dashboard by its ID, including its metrics.

        Args:
            dashboard_id: The ID of the dashboard to retrieve.

        Returns:
            The Dashboard object if found, otherwise None. The dashboard's
            metrics are eager-loaded.
        """
        result = await self.db.execute(
            select(Dashboard)
            .where(Dashboard.id == dashboard_id)
            .options(joinedload(Dashboard.metrics))
        )
        return result.scalars().first()

    async def create_dashboard(
        self, dashboard_in: DashboardCreate, owner_id: int
    ) -> Dashboard:
        """
        Creates a new dashboard for a given user.

        Args:
            dashboard_in: The Pydantic schema containing the new dashboard's data.
            owner_id: The ID of the user who will own the new dashboard.

        Returns:
            The newly created Dashboard object.
        """
        db_dashboard = Dashboard(**dashboard_in.model_dump(), owner_id=owner_id)
        self.db.add(db_dashboard)
        await self.db.commit()
        await self.db.refresh(db_dashboard)
        return db_dashboard

    async def update_dashboard(
        self, dashboard: Dashboard, dashboard_in: DashboardUpdate
    ) -> Dashboard:
        """
        Updates an existing dashboard's data.

        Args:
            dashboard: The existing Dashboard object to update.
            dashboard_in: The Pydantic schema containing the updated data.

        Returns:
            The updated Dashboard object.
        """
        update_data = dashboard_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(dashboard, key, value)

        await self.db.commit()
        await self.db.refresh(dashboard)
        return dashboard

    async def delete_dashboard(self, dashboard: Dashboard):
        """
        Deletes a dashboard from the database.

        Args:
            dashboard: The Dashboard object to delete.
        """
        await self.db.delete(dashboard)
        await self.db.commit()
