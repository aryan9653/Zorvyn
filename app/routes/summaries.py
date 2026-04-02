"""
Summary and analytics routes.
"""

import csv
import io
from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User, UserRole
from app.models.transaction import TransactionType
from app.schemas.summary import (
    FinancialSummary,
    CategoryBreakdownResponse,
    MonthlySummaryResponse,
    RecentActivity,
    ExportResponse
)
from app.services.summary_service import SummaryService
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/summaries", tags=["Summary & Analytics"])


@router.get(
    "/overview",
    response_model=FinancialSummary,
    summary="Get financial overview",
    description="Get overall financial summary including totals and balance."
)
def get_overview(
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get financial overview.
    
    Returns:
    - Total income
    - Total expenses
    - Current balance
    - Transaction counts
    
    Supports date range filtering.
    """
    user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    return SummaryService.get_financial_summary(db, user_id, date_from, date_to)


@router.get(
    "/by-category",
    response_model=CategoryBreakdownResponse,
    summary="Get category breakdown",
    description="Get breakdown of transactions by category."
)
def get_by_category(
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    type: Optional[TransactionType] = Query(None, description="Filter by type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get category-wise breakdown.
    
    For each category, returns:
    - Total amount
    - Transaction count
    - Percentage of total
    - Average amount
    
    Supports date range and transaction type filtering.
    """
    user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    return SummaryService.get_category_breakdown(db, user_id, date_from, date_to, type)


@router.get(
    "/monthly",
    response_model=MonthlySummaryResponse,
    summary="Get monthly summary",
    description="Get monthly financial summary."
)
def get_monthly(
    year: Optional[int] = Query(None, description="Filter by year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get monthly financial summary.
    
    For each month, returns:
    - Total income
    - Total expenses
    - Net amount
    - Transaction count
    
    Also includes averages and totals.
    """
    user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    return SummaryService.get_monthly_summary(db, user_id, year)


@router.get(
    "/recent",
    response_model=RecentActivity,
    summary="Get recent activity",
    description="Get recent transaction activity."
)
def get_recent(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    limit: int = Query(10, ge=1, le=100, description="Maximum transactions to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get recent transaction activity.
    
    Returns transactions from the last N days.
    """
    user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    return SummaryService.get_recent_activity(db, user_id, days, limit)


@router.get(
    "/export",
    summary="Export transactions",
    description="Export transactions to JSON or CSV format."
)
def export_transactions(
    format: str = Query("json", description="Export format: json or csv"),
    date_from: Optional[date] = Query(None, description="Filter from date"),
    date_to: Optional[date] = Query(None, description="Filter to date"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export transactions.
    
    Supports JSON and CSV formats.
    """
    user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    transactions = SummaryService.export_transactions(
        db, user_id, format, date_from, date_to
    )
    
    if format.lower() == "csv":
        # Generate CSV
        output = io.StringIO()
        writer = csv.DictWriter(
            output, 
            fieldnames=["id", "amount", "type", "category", "date", "notes", "created_at"]
        )
        writer.writeheader()
        writer.writerows(transactions)
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=transactions.csv"
            }
        )
    else:
        # Return JSON
        return {
            "format": "json",
            "record_count": len(transactions),
            "data": transactions
        }
