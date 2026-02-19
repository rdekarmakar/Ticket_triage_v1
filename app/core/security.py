"""
Security utilities including basic authentication.
"""

import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from config.settings import get_settings

security = HTTPBasic()


def verify_credentials(
    credentials: HTTPBasicCredentials = Depends(security)
) -> str:
    """
    Verify HTTP Basic Auth credentials.

    Args:
        credentials: HTTP Basic credentials from request

    Returns:
        Username if valid

    Raises:
        HTTPException: If credentials are invalid
    """
    settings = get_settings()

    correct_username = secrets.compare_digest(
        credentials.username.encode("utf-8"),
        settings.dashboard_username.encode("utf-8")
    )
    correct_password = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        settings.dashboard_password.encode("utf-8")
    )

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials.username


def get_current_user(username: str = Depends(verify_credentials)) -> str:
    """
    Get the current authenticated user.

    Args:
        username: Verified username

    Returns:
        Username
    """
    return username
