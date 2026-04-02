"""
User management routes.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserUpdate, UserListResponse, UserRoleUpdate
from app.core.dependencies import get_current_user, require_admin
from app.core.security import hash_password
from app.utils.validators import validate_pagination, calculate_pagination

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get(
    "",
    response_model=UserListResponse,
    summary="List all users",
    description="Get a paginated list of all users. Admin only."
)
def list_users(
    page: int = 1,
    page_size: int = 10,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    List all users with pagination.
    
    Requires admin role.
    """
    page, page_size = validate_pagination(page, page_size)
    offset = (page - 1) * page_size
    
    query = db.query(User)
    total = query.count()
    users = query.offset(offset).limit(page_size).all()
    
    pagination = calculate_pagination(total, page, page_size)
    
    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        **pagination
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID",
    description="Get a specific user's information."
)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a user by ID.
    
    - Regular users can only view their own profile
    - Admins can view any user's profile
    """
    # Non-admin users can only view their own profile
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user",
    description="Update user information."
)
def update_user(
    user_id: int,
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a user's information.
    
    - Regular users can only update their own profile
    - Admins can update any user's profile
    """
    # Non-admin users can only update their own profile
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update fields
    update_dict = update_data.model_dump(exclude_unset=True)
    
    # Hash password if provided
    if "password" in update_dict:
        update_dict["hashed_password"] = hash_password(update_dict.pop("password"))
    
    # Check email uniqueness if email is being updated
    if "email" in update_dict:
        existing = db.query(User).filter(
            User.email == update_dict["email"],
            User.id != user_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    for field, value in update_dict.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Update user role",
    description="Change a user's role. Admin only."
)
def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Update a user's role.
    
    Requires admin role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from demoting themselves
    if user.id == current_user.id and role_data.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own admin role"
        )
    
    user.role = role_data.role
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete a user account. Admin only."
)
def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a user.
    
    Requires admin role.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent admin from deleting themselves
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    db.delete(user)
    db.commit()
    
    return None
