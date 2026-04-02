"""
Transaction service for CRUD operations and filtering.
"""

from typing import Optional
from datetime import date
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import (
    TransactionCreate, 
    TransactionUpdate, 
    TransactionFilter,
    TransactionResponse,
    TransactionListResponse
)
from app.utils.validators import validate_pagination, calculate_pagination


class TransactionService:
    """Service class for transaction operations."""
    
    @staticmethod
    def create_transaction(
        db: Session, 
        user_id: int, 
        transaction_data: TransactionCreate
    ) -> Transaction:
        """
        Create a new transaction.
        
        Args:
            db: Database session
            user_id: ID of the user creating the transaction
            transaction_data: Transaction creation data
            
        Returns:
            Created Transaction object
        """
        new_transaction = Transaction(
            user_id=user_id,
            amount=transaction_data.amount,
            type=transaction_data.transaction_type,
            category=transaction_data.category,
            date=transaction_data.transaction_date,
            notes=transaction_data.notes
        )
        
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)
        
        return new_transaction
    
    @staticmethod
    def get_transaction(db: Session, transaction_id: int, user_id: Optional[int] = None) -> Transaction:
        """
        Get a single transaction by ID.
        
        Args:
            db: Database session
            transaction_id: ID of the transaction
            user_id: Optional user ID to filter by ownership
            
        Returns:
            Transaction object
            
        Raises:
            HTTPException: If transaction not found
        """
        query = db.query(Transaction).filter(Transaction.id == transaction_id)
        
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        
        transaction = query.first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return transaction
    
    @staticmethod
    def get_transactions(
        db: Session,
        user_id: Optional[int] = None,
        page: int = 1,
        page_size: int = 10,
        filters: Optional[TransactionFilter] = None
    ) -> TransactionListResponse:
        """
        Get a paginated list of transactions with optional filtering.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter by ownership
            page: Page number (1-indexed)
            page_size: Number of items per page
            filters: Optional filter criteria
            
        Returns:
            TransactionListResponse with paginated results
        """
        query = db.query(Transaction)
        
        # Filter by user if specified
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        
        # Apply filters
        if filters:
            if filters.date_from:
                query = query.filter(Transaction.date >= filters.date_from)
            if filters.date_to:
                query = query.filter(Transaction.date <= filters.date_to)
            if filters.category:
                query = query.filter(
                    Transaction.category.ilike(f"%{filters.category}%")
                )
            if filters.transaction_type:
                query = query.filter(Transaction.type == filters.transaction_type)
            if filters.min_amount is not None:
                query = query.filter(Transaction.amount >= filters.min_amount)
            if filters.max_amount is not None:
                query = query.filter(Transaction.amount <= filters.max_amount)
            if filters.search:
                query = query.filter(
                    Transaction.notes.ilike(f"%{filters.search}%")
                )
        
        # Get total count
        total = query.count()
        
        # Validate pagination
        page, page_size = validate_pagination(page, page_size)
        
        # Apply pagination
        offset = (page - 1) * page_size
        transactions = query.order_by(Transaction.date.desc()).offset(offset).limit(page_size).all()
        
        # Calculate pagination metadata
        pagination = calculate_pagination(total, page, page_size)
        
        return TransactionListResponse(
            transactions=[TransactionResponse.model_validate(t) for t in transactions],
            **pagination
        )
    
    @staticmethod
    def update_transaction(
        db: Session,
        transaction_id: int,
        user_id: int,
        update_data: TransactionUpdate
    ) -> Transaction:
        """
        Update an existing transaction.
        
        Args:
            db: Database session
            transaction_id: ID of the transaction to update
            user_id: ID of the user (for ownership validation)
            update_data: Transaction update data
            
        Returns:
            Updated Transaction object
            
        Raises:
            HTTPException: If transaction not found
        """
        transaction = TransactionService.get_transaction(db, transaction_id, user_id)
        
        # Update fields that are provided
        update_dict = update_data.model_dump(exclude_unset=True)
        # Map schema field names to model field names
        if 'transaction_type' in update_dict:
            update_dict['type'] = update_dict.pop('transaction_type')
        if 'transaction_date' in update_dict:
            update_dict['date'] = update_dict.pop('transaction_date')
        for field, value in update_dict.items():
            setattr(transaction, field, value)
        
        db.commit()
        db.refresh(transaction)
        
        return transaction
    
    @staticmethod
    def delete_transaction(db: Session, transaction_id: int, user_id: Optional[int] = None) -> dict:
        """
        Delete a transaction.
        
        Args:
            db: Database session
            transaction_id: ID of the transaction to delete
            user_id: Optional user ID to filter by ownership
            
        Returns:
            Success message dictionary
            
        Raises:
            HTTPException: If transaction not found
        """
        transaction = TransactionService.get_transaction(db, transaction_id, user_id)
        
        db.delete(transaction)
        db.commit()
        
        return {"message": "Transaction deleted successfully"}
    
    @staticmethod
    def get_transactions_by_date_range(
        db: Session,
        date_from: date,
        date_to: date,
        user_id: Optional[int] = None
    ) -> list[Transaction]:
        """
        Get all transactions within a date range.
        
        Args:
            db: Database session
            date_from: Start date
            date_to: End date
            user_id: Optional user ID to filter by ownership
            
        Returns:
            List of Transaction objects
        """
        query = db.query(Transaction).filter(
            and_(
                Transaction.date >= date_from,
                Transaction.date <= date_to
            )
        )
        
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        
        return query.order_by(Transaction.date.desc()).all()
    
    @staticmethod
    def get_unique_categories(db: Session, user_id: Optional[int] = None) -> list[str]:
        """
        Get all unique categories used by a user.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter by ownership
            
        Returns:
            List of unique category names
        """
        query = db.query(Transaction.category).distinct()
        
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        
        return [c[0] for c in query.all()]
