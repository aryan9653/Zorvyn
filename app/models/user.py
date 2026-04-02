"""
User model for the Finance System.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    """User roles for role-based access control."""
    VIEWER = "viewer"
    ANALYST = "analyst"
    ADMIN = "admin"


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship to transactions
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role={self.role})>"
    
    def has_permission(self, required_role: str) -> bool:
        """Check if user has required role or higher."""
        role_hierarchy = {
            UserRole.VIEWER: 1,
            UserRole.ANALYST: 2,
            UserRole.ADMIN: 3
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(UserRole(required_role), 0)
