"""
WebSocket endpoint for real-time dashboard metric updates.

This module handles the WebSocket lifecycle for clients subscribing to
real-time updates for a specific dashboard.
"""

import logging
from typing import Annotated

from fastapi import (
    APIRouter,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import async_session_maker
from app.services import auth_service
from app.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)
router = APIRouter()


async def verify_token(token: str) -> int:
    """
    Verifies a JWT token and extracts the user ID.

    This function decodes the JWT, retrieves the user's email from the
    subject field, and fetches the corresponding user ID from the database.

    Args:
        token: The JWT token string provided by the client.

    Returns:
        The integer user ID associated with the token.

    Raises:
        HTTPException: If the token is invalid, expired, or the user
                       cannot be found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.ALGORITHM]
        )
        user_email: str | None = payload.get("sub")
        if user_email is None:
            raise credentials_exception

        # Get user_id from database by email
        async with async_session_maker() as db:
            user = await auth_service.get_user_by_email(db, user_email)
            if not user:
                raise credentials_exception
            return user.id

    except JWTError:
        raise credentials_exception


@router.websocket("/ws/dashboard/{dashboard_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    dashboard_id: int,
    token: Annotated[str, Query()],
):
    """
    Handles WebSocket connections for real-time dashboard updates.

    This endpoint manages the lifecycle of a WebSocket connection. It first
    authenticates the user via a JWT token from the query parameters, then
    verifies that the user owns the requested dashboard. Upon successful
    verification, it subscribes to a Redis Pub/Sub channel specific to the
    dashboard and forwards any received metric updates to the client.

    The connection is closed if authentication or authorization fails.

    Args:
        websocket: The WebSocket connection instance provided by FastAPI.
        dashboard_id: The ID of the dashboard to subscribe to for updates.
        token: The JWT token for authentication, passed as a query parameter.
    """
    try:
        # 1. Verify token and get user_id
        try:
            user_id = await verify_token(token)
        except HTTPException as e:
            logger.error(f"Authentication failed: {e.detail}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        logger.info(
            f"WebSocket connection attempt for user {user_id} to dashboard {dashboard_id}"
        )

        # 2. Get DB session and verify dashboard ownership
        async with async_session_maker() as db:
            dashboard_service = DashboardService(db)
            dashboard = await dashboard_service.get_dashboard_by_id(dashboard_id)

            if not dashboard or dashboard.owner_id != user_id:
                logger.warning(f"User {user_id} does not own dashboard {dashboard_id}")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return

        # 3. Accept WebSocket connection (AFTER verification)
        await websocket.accept()
        logger.info(
            f"WebSocket connection accepted for user {user_id} to dashboard {dashboard_id}"
        )

        # 4. Get Redis service from app state
        if (
            not hasattr(websocket.app.state, "redis_service")
            or not websocket.app.state.redis_service
        ):
            logger.error("Redis service not available")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return

        redis_service = websocket.app.state.redis_service

        # 5. Subscribe to dashboard channel and forward messages
        try:
            async for message in redis_service.subscribe_to_dashboard(dashboard_id):
                try:
                    await websocket.send_json(
                        {"type": "metric_update", "data": message}
                    )
                except Exception as e:
                    logger.error(f"Error sending message to WebSocket: {e}")
                    break
        except Exception as e:
            logger.error(
                f"Error in Redis subscription for dashboard {dashboard_id}: {e}",
                exc_info=True,
            )

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from dashboard {dashboard_id}")
    except Exception as e:
        logger.error(
            f"Unexpected error in WebSocket for dashboard {dashboard_id}: {e}",
            exc_info=True,
        )
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except:
            pass
    finally:
        logger.info(f"WebSocket connection closed for dashboard {dashboard_id}")
