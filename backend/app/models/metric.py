"""
SQLAlchemy model for the Metric entity.

This module defines the Metric model, which represents a single data point
or measurement associated with a dashboard.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from .dashboard import Dashboard


class Metric(Base):
    """
    Represents a single metric data point in the system.

    Metrics are the core data elements of a dashboard, representing a named,
    typed value at a specific point in time.

    Attributes:
        id: The unique integer identifier for the metric.
        name: The name of the metric (e.g., 'cpu_usage').
        value: The numerical value of the metric.
        metric_type: The type of the metric (e.g., 'gauge', 'counter').
        dashboard_id: The foreign key linking to the parent dashboard.
        created_at: The timestamp when the metric was recorded.
        updated_at: The timestamp when the metric was last updated.
        dashboard: A relationship to the parent Dashboard model.
    """

    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    metric_type: Mapped[str] = mapped_column(String, nullable=False)
    dashboard_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    dashboard: Mapped["Dashboard"] = relationship("Dashboard", back_populates="metrics")

    def __repr__(self) -> str:
        """
        Provides a developer-friendly representation of the Metric instance.

        Returns:
            A string representation of the metric.
        """
        return f"<Metric(id={self.id}, name='{self.name}', value={self.value}, type='{self.metric_type}')>"
