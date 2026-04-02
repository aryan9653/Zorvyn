"""
Authentication service for user registration, login, and token management.
"""

from datetime import timedelta
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.core.config import settings


class AuthService:
    """Service class for authentication operations."""
    
    @staticmethod
    def register_user(db: Session, user_data: UserCreate) -> User:
        """
        Register a new user.
        
        Args:
            db: Database session
            user_data: User registration data
            
        Returns:
            Created User object
            
        Raises:
            HTTPException: If username or email already exists
        """
        # Check if username exists
        if db.query(User).filter(User.username == user_data.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # Check if email exists
        if db.query(User).filter(User.email == user_data.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = hash_password(user_data.password)
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            role=UserRole.VIEWER,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        return new_user
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> dict:
        """
        Authenticate a user and return an access token.
        
        Args:
            db: Database session
            username: Username to authenticate
            password: Plain text password
            
        Returns:
            Dictionary with access token and user info
            
        Raises:
            HTTPException: If credentials are invalid
        """
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deactivated"
            )
        
        # Create access token
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role.value},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": UserResponse.model_validate(user)
        }
    
    @staticmethod
    def get_user_by_username(db: Session, username: str) -> Optional[User]:
        """
        Get a user by username.
        
        Args:
            db: Database session
            username: Username to search for
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.username == username).first()
    
    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
        """
        Get a user by ID.
        
        Args:
            db: Database session
            user_id: User ID to search for
            
        Returns:
            User object if found, None otherwise
        """
        return db.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def create_admin_user(db: Session) -> Optional[User]:
        """
        Create the initial admin user if it doesn't exist.
        
        Args:
            db: Database session
            
        Returns:
            Created User object or None if already exists
        """
        # Check if admin exists
        existing_admin = db.query(User).filter(
            User.username == settings.admin_username
        ).first()
        
        if existing_admin:
            return None
        
        # Create admin user
        hashed_password = hash_password(settings.admin_password)
        admin_user = User(
            username=settings.admin_username,
            email=settings.admin_email,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        return admin_user
