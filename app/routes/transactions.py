"""
Transaction management routes.
"""

from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.transaction import TransactionType
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
    TransactionFilter
)
from app.services.transaction_service import TransactionService
from app.core.dependencies import get_current_user, require_analyst, require_admin

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.post(
    "",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a transaction",
    description="Create a new financial transaction. Requires analyst or admin role."
)
def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db)
):
    """
    Create a new transaction.
    
    - **amount**: Transaction amount (must be positive)
    - **type**: 'income' or 'expense'
    - **category**: Category name (e.g., 'Salary', 'Food', 'Transport')
    - **date**: Transaction date
    - **notes**: Optional additional notes
    
    Requires analyst or admin role.
    """
    transaction = TransactionService.create_transaction(
        db, current_user.id, transaction_data
    )
    return TransactionResponse.model_validate(transaction)


@router.get(
    "",
    response_model=TransactionListResponse,
    summary="List transactions",
    description="Get a paginated list of transactions with optional filtering."
)
def list_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    category: Optional[str] = Query(None, description="Filter by category"),
    transaction_type: Optional[TransactionType] = Query(None, alias="type", description="Filter by type"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum amount"),
    search: Optional[str] = Query(None, description="Search in notes"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List transactions with pagination and filtering.
    
    - Regular users see only their own transactions
    - Admins see all transactions
    
    Supports filtering by:
    - Date range (date_from, date_to)
    - Category
    - Type (income/expense)
    - Amount range (min_amount, max_amount)
    - Search in notes
    """
    # Build filter object
    filters = TransactionFilter(
        date_from=date_from,
        date_to=date_to,
        category=category,
        transaction_type=transaction_type,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search
    ) if any([date_from, date_to, category, transaction_type, min_amount, max_amount, search]) else None
    
    # Non-admin users can only see their own transactions
    user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    
    return TransactionService.get_transactions(
        db, user_id, page, page_size, filters
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get transaction by ID",
    description="Get a specific transaction's details."
)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a transaction by ID.
    
    - Regular users can only view their own transactions
    - Admins can view any transaction
    """
    user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    transaction = TransactionService.get_transaction(db, transaction_id, user_id)
    return TransactionResponse.model_validate(transaction)


@router.put(
    "/{transaction_id}",
    response_model=TransactionResponse,
    summary="Update transaction",
    description="Update a transaction. Requires analyst or admin role."
)
def update_transaction(
    transaction_id: int,
    update_data: TransactionUpdate,
    current_user: User = Depends(require_analyst),
    db: Session = Depends(get_db)
):
    """
    Update a transaction.
    
    - Analysts can only update their own transactions
    - Admins can update any transaction
    
    Only provided fields will be updated.
    """
    user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    transaction = TransactionService.update_transaction(
        db, transaction_id, user_id, update_data
    )
    return TransactionResponse.model_validate(transaction)


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete transaction",
    description="Delete a transaction. Admin only."
)
def delete_transaction(
    transaction_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Delete a transaction.
    
    Requires admin role.
    """
    TransactionService.delete_transaction(db, transaction_id)
    return None


@router.get(
    "/categories/list",
    response_model=list[str],
    summary="Get unique categories",
    description="Get a list of all unique transaction categories."
)
def get_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all unique categories used by the current user.
    
    Useful for building filter dropdowns.
    """
    user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    return TransactionService.get_unique_categories(db, user_id)
