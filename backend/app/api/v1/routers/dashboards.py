"""
API router for dashboard management.

This module provides endpoints for creating, retrieving, updating, and
deleting dashboards, as well as listing metrics associated with a dashboard.
All endpoints require user authentication and perform ownership checks.
"""


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.dashboard import (
    DashboardCreate,
    DashboardDetailResponse,
    DashboardResponse,
    DashboardUpdate,
)
from app.schemas.metric import MetricResponse
from app.services.dashboard_service import DashboardService
from app.services.metric_service import MetricService

router = APIRouter()


@router.post("/", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    dashboard_in: DashboardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """
    Creates a new dashboard for the current authenticated user.

    Args:
        dashboard_in: The data for the new dashboard from the request body.
        db: The SQLAlchemy `AsyncSession` dependency.
        current_user: The authenticated user, injected by dependency.

    Returns:
        The newly created dashboard.
    """
    service = DashboardService(db)
    return await service.create_dashboard(dashboard_in, owner_id=current_user.id)


@router.get("/", response_model=list[DashboardResponse])
async def get_user_dashboards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DashboardResponse]:
    """
    Retrieves all dashboards owned by the current authenticated user.

    Args:
        db: The SQLAlchemy `AsyncSession` dependency.
        current_user: The authenticated user, injected by dependency.

    Returns:
        A list of dashboards belonging to the user.
    """
    service = DashboardService(db)
    return await service.get_user_dashboards(user_id=current_user.id)


@router.get("/{dashboard_id}", response_model=DashboardDetailResponse)
async def get_dashboard(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardDetailResponse:
    """
    Retrieves a single dashboard by its ID.

    Ensures that the dashboard is owned by the current authenticated user.

    Args:
        dashboard_id: The ID of the dashboard to retrieve.
        db: The SQLAlchemy `AsyncSession` dependency.
        current_user: The authenticated user, injected by dependency.

    Returns:
        The requested dashboard, including its associated metrics.

    Raises:
        HTTPException: If the dashboard is not found or not owned by the user.
    """
    service = DashboardService(db)
    dashboard = await service.get_dashboard_by_id(dashboard_id)
    if not dashboard or dashboard.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found"
        )
    return dashboard


@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: int,
    dashboard_in: DashboardUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """
    Updates an existing dashboard.

    Ensures that the dashboard is owned by the current authenticated user.

    Args:
        dashboard_id: The ID of the dashboard to update.
        dashboard_in: The new data for the dashboard from the request body.
        db: The SQLAlchemy `AsyncSession` dependency.
        current_user: The authenticated user, injected by dependency.

    Returns:
        The updated dashboard.

    Raises:
        HTTPException: If the dashboard is not found or not owned by the user.
    """
    service = DashboardService(db)
    dashboard = await service.get_dashboard_by_id(dashboard_id)
    if not dashboard or dashboard.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found"
        )
    return await service.update_dashboard(dashboard, dashboard_in)


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Deletes a dashboard.

    Ensures that the dashboard is owned by the current authenticated user.

    Args:
        dashboard_id: The ID of the dashboard to delete.
        db: The SQLAlchemy `AsyncSession` dependency.
        current_user: The authenticated user, injected by dependency.

    Raises:
        HTTPException: If the dashboard is not found or not owned by the user.
    """
    service = DashboardService(db)
    dashboard = await service.get_dashboard_by_id(dashboard_id)
    if not dashboard or dashboard.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Dashboard not found"
        )
    await service.delete_dashboard(dashboard)


@router.get("/{dashboard_id}/metrics", response_model=list[MetricResponse])
async def get_dashboard_metrics(
    dashboard_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[MetricResponse]:
    """
    Retrieves all metrics associated with a specific dashboard.

    Ensures that the dashboard is owned by the current authenticated user.

    Args:
        dashboard_id: The ID of the dashboard whose metrics are to be retrieved.
        db: The SQLAlchemy `AsyncSession` dependency.
        current_user: The authenticated user, injected by dependency.

    Returns:
        A list of metrics for the specified dashboard.
    """
    metric_service = MetricService(db)
    return await metric_service.get_dashboard_metrics(
        dashboard_id=dashboard_id, user_id=current_user.id
    )
