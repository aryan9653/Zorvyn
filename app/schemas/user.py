"""
Pydantic schemas for User model validation and serialization.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: EmailStr = Field(..., description="Email address")


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=6, max_length=100, description="Password")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Ensure password has at least one letter and one number."""
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    email: Optional[EmailStr] = Field(None, description="New email address")
    password: Optional[str] = Field(None, min_length=6, max_length=100, description="New password")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: Optional[str]) -> Optional[str]:
        """Ensure password has at least one letter and one number if provided."""
        if v is not None:
            if not any(c.isalpha() for c in v):
                raise ValueError('Password must contain at least one letter')
            if not any(c.isdigit() for c in v):
                raise ValueError('Password must contain at least one number')
        return v


class UserRoleUpdate(BaseModel):
    """Schema for updating user role."""
    role: UserRole = Field(..., description="New role for the user")


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""
    users: list[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
