"""
Dependency functions for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.core.security import decode_token

# Bearer token scheme
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and validate the current user from the JWT token.
    
    Args:
        credentials: The bearer token from the request header
        db: Database session
        
    Returns:
        The authenticated User object
        
    Raises:
        HTTPException: If the token is invalid or user not found
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Verify the current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


def require_role(required_role: str):
    """
    Create a dependency that requires a minimum role level.
    
    Args:
        required_role: The minimum required role (viewer, analyst, admin)
        
    Returns:
        A dependency function that validates the user's role
    """
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not current_user.has_permission(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role} role or higher"
            )
        return current_user
    
    return role_checker


# Pre-defined role checkers for convenience
require_viewer = require_role("viewer")
require_analyst = require_role("analyst")
require_admin = require_role("admin")


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.
    Useful for endpoints that behave differently for authenticated users.
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = decode_token(token)
        username: str = payload.get("sub")
        if username is None:
            return None
        
        user = db.query(User).filter(User.username == username).first()
        return user if user and user.is_active else None
    except HTTPException:
        return None
