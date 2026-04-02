"""
Authentication routes for user registration and login.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account. New users are assigned the 'viewer' role by default."
)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - **username**: Unique username (3-50 characters)
    - **email**: Valid email address
    - **password**: Password (6-100 characters, must contain letters and numbers)
    """
    user = AuthService.register_user(db, user_data)
    return UserResponse.model_validate(user)


@router.post(
    "/login",
    summary="User login",
    description="Authenticate with username and password to receive an access token."
)
def login(login_data: dict, db: Session = Depends(get_db)):
    """
    Login to receive an access token.
    
    - **username**: Your username
    - **password**: Your password
    
    Returns a bearer token for API authentication.
    """
    return AuthService.authenticate_user(
        db, 
        login_data.get("username"), 
        login_data.get("password")
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
    description="Get information about the currently authenticated user."
)
def get_current_user_info(current_user = Depends(get_current_user)):
    """
    Get the current authenticated user's information.
    
    Requires a valid Bearer token in the Authorization header.
    """
    return UserResponse.model_validate(current_user)
