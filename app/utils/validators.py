"""
Custom validators for data validation.
"""

from datetime import date
from typing import Optional
from fastapi import HTTPException, status


def validate_date_not_future(transaction_date: date) -> date:
    """
    Validate that a date is not in the future.
    
    Args:
        transaction_date: The date to validate
        
    Returns:
        The validated date
        
    Raises:
        HTTPException: If the date is in the future
    """
    if transaction_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction date cannot be in the future"
        )
    return transaction_date


def validate_amount_positive(amount: float) -> float:
    """
    Validate that an amount is positive.
    
    Args:
        amount: The amount to validate
        
    Returns:
        The validated amount
        
    Raises:
        HTTPException: If the amount is not positive
    """
    if amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Amount must be positive"
        )
    return amount


def validate_pagination(page: int, page_size: int, max_page_size: int = 100) -> tuple[int, int]:
    """
    Validate and normalize pagination parameters.
    
    Args:
        page: The page number (1-indexed)
        page_size: The number of items per page
        max_page_size: Maximum allowed page size
        
    Returns:
        Tuple of (validated_page, validated_page_size)
    """
    if page < 1:
        page = 1
    
    if page_size < 1:
        page_size = 10
    
    if page_size > max_page_size:
        page_size = max_page_size
    
    return page, page_size


def calculate_pagination(total: int, page: int, page_size: int) -> dict:
    """
    Calculate pagination metadata.
    
    Args:
        total: Total number of items
        page: Current page number
        page_size: Number of items per page
        
    Returns:
        Dictionary with pagination metadata
    """
    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages
    }
