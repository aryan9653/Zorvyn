"""
Pydantic schemas for summary and analytics responses.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from app.schemas.transaction import TransactionResponse


class FinancialSummary(BaseModel):
    """Schema for overall financial summary."""
    total_income: float = Field(..., description="Total income amount")
    total_expenses: float = Field(..., description="Total expenses amount")
    balance: float = Field(..., description="Current balance (income - expenses)")
    transaction_count: int = Field(..., description="Total number of transactions")
    income_count: int = Field(..., description="Number of income transactions")
    expense_count: int = Field(..., description="Number of expense transactions")


class CategoryBreakdown(BaseModel):
    """Schema for category-wise breakdown."""
    category: str = Field(..., description="Category name")
    total: float = Field(..., description="Total amount for this category")
    count: int = Field(..., description="Number of transactions")
    percentage: float = Field(..., description="Percentage of total transactions")
    average: float = Field(..., description="Average transaction amount")


class CategoryBreakdownResponse(BaseModel):
    """Schema for category breakdown response."""
    categories: list[CategoryBreakdown]
    total_transactions: int
    total_amount: float


class MonthlySummary(BaseModel):
    """Schema for monthly financial summary."""
    month: int = Field(..., ge=1, le=12, description="Month (1-12)")
    year: int = Field(..., description="Year")
    income: float = Field(..., description="Total income for the month")
    expenses: float = Field(..., description="Total expenses for the month")
    net: float = Field(..., description="Net amount (income - expenses)")
    transaction_count: int = Field(..., description="Number of transactions")


class MonthlySummaryResponse(BaseModel):
    """Schema for monthly summary response."""
    monthly_data: list[MonthlySummary]
    total_income: float
    total_expenses: float
    average_monthly_income: float
    average_monthly_expenses: float


class RecentActivity(BaseModel):
    """Schema for recent activity response."""
    transactions: list[TransactionResponse]
    total: int
    days: int = Field(..., description="Number of days covered")


class DateRangeSummary(BaseModel):
    """Schema for summary within a date range."""
    date_from: date
    date_to: date
    total_income: float
    total_expenses: float
    balance: float
    transaction_count: int
    category_breakdown: list[CategoryBreakdown]


class ExportResponse(BaseModel):
    """Schema for export response."""
    format: str = Field(..., description="Export format (json/csv)")
    record_count: int = Field(..., description="Number of records exported")
    download_url: Optional[str] = Field(None, description="Download URL if applicable")
