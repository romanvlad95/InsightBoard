"""
SQLAlchemy model for the Dashboard entity.

This module defines the Dashboard model, which represents a dashboard
containing a collection of metrics. It is associated with a user (owner).
"""

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Dashboard(Base):
    """
    Represents a dashboard in the system.

    A dashboard is a collection of metrics owned by a user. It serves as a
    container for organizing and displaying related analytics data.

    Attributes:
        id: The unique integer identifier for the dashboard.
        name: The name of the dashboard.
        description: An optional description of the dashboard.
        owner_id: The foreign key linking to the user who owns the dashboard.
        created_at: The timestamp when the dashboard was created.
        updated_at: The timestamp when the dashboard was last updated.
        metrics: A relationship to the Metric models associated with this
                 dashboard. The `cascade` option ensures that metrics are
                 deleted when their parent dashboard is deleted.
    """

    __tablename__ = "dashboards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    metrics = relationship(
        "Metric", back_populates="dashboard", cascade="all, delete-orphan"
    )
