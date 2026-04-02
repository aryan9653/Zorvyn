"""
Pydantic schemas for Transaction model validation and serialization.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict, AliasPath, AliasChoices
from typing import Optional
from datetime import date, datetime
from app.models.transaction import TransactionType


class TransactionBase(BaseModel):
    """Base transaction schema with common fields."""
    amount: float = Field(..., gt=0, description="Transaction amount (must be positive)")
    transaction_type: TransactionType = Field(
        ..., 
        validation_alias=AliasChoices("type", "transaction_type"),
        serialization_alias="type", 
        description="Transaction type: income or expense"
    )
    category: str = Field(..., min_length=1, max_length=50, description="Transaction category")
    transaction_date: date = Field(
        ..., 
        validation_alias=AliasChoices("date", "transaction_date"),
        serialization_alias="date", 
        description="Transaction date"
    )
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    model_config = ConfigDict(populate_by_name=True)


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    pass


class TransactionUpdate(BaseModel):
    """Schema for updating an existing transaction."""
    amount: Optional[float] = Field(None, gt=0, description="Transaction amount (must be positive)")
    transaction_type: Optional[TransactionType] = Field(
        None, 
        validation_alias=AliasChoices("type", "transaction_type"),
        serialization_alias="type", 
        description="Transaction type"
    )
    category: Optional[str] = Field(None, min_length=1, max_length=50, description="Category")
    transaction_date: Optional[date] = Field(
        None, 
        validation_alias=AliasChoices("date", "transaction_date"),
        serialization_alias="date", 
        description="Transaction date"
    )
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

    model_config = ConfigDict(populate_by_name=True)


class TransactionResponse(BaseModel):
    """Schema for transaction response."""
    id: int
    user_id: int
    amount: float
    transaction_type: TransactionType = Field(
        validation_alias=AliasPath('type'), 
        serialization_alias="type"
    )
    category: str
    transaction_date: date = Field(
        validation_alias=AliasPath('date'), 
        serialization_alias="date"
    )
    notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class TransactionFilter(BaseModel):
    """Schema for filtering transactions."""
    date_from: Optional[date] = Field(None, description="Filter from this date")
    date_to: Optional[date] = Field(None, description="Filter to this date")
    category: Optional[str] = Field(None, description="Filter by category")
    transaction_type: Optional[TransactionType] = Field(
        None, 
        validation_alias=AliasChoices("type", "transaction_type"),
        serialization_alias="type", 
        description="Filter by type"
    )
    min_amount: Optional[float] = Field(None, ge=0, description="Minimum amount")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum amount")
    search: Optional[str] = Field(None, max_length=100, description="Search in notes")

    model_config = ConfigDict(populate_by_name=True)
    
    @field_validator('date_to')
    @classmethod
    def validate_date_range(cls, v: Optional[date], info) -> Optional[date]:
        """Ensure date_to is after date_from if both are provided."""
        if v is not None and info.data.get('date_from') is not None:
            if v < info.data['date_from']:
                raise ValueError('date_to must be after or equal to date_from')
        return v
    
    @field_validator('max_amount')
    @classmethod
    def validate_amount_range(cls, v: Optional[float], info) -> Optional[float]:
        """Ensure max_amount is greater than min_amount if both are provided."""
        if v is not None and info.data.get('min_amount') is not None:
            if v < info.data['min_amount']:
                raise ValueError('max_amount must be greater than or equal to min_amount')
        return v


class TransactionListResponse(BaseModel):
    """Schema for paginated transaction list response."""
    transactions: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
