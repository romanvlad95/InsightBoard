"""
SQLAlchemy model for the User entity.

This module defines the User model, which corresponds to the `users` table
in the database. It includes fields for user identification, authentication,
and metadata.
"""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """
    Represents a user in the system.

    This model maps to the `users` table and stores information about each user,
    including their credentials and role.

    Attributes:
        id: The unique integer identifier for the user.
        email: The user's unique email address, used for login.
        password_hash: The hashed password for user authentication.
        role: The role assigned to the user (e.g., 'user', 'admin').
        created_at: The timestamp when the user account was created.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
