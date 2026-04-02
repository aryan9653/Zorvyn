"""
Summary service for financial analytics and reporting.
"""

from typing import Optional
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, extract, case
from app.models.transaction import Transaction, TransactionType
from app.schemas.transaction import TransactionResponse
from app.schemas.summary import (
    FinancialSummary,
    CategoryBreakdown,
    CategoryBreakdownResponse,
    MonthlySummary,
    MonthlySummaryResponse,
    RecentActivity
)


class SummaryService:
    """Service class for financial summary and analytics."""
    
    @staticmethod
    def get_financial_summary(
        db: Session,
        user_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> FinancialSummary:
        """
        Get overall financial summary.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter by ownership
            date_from: Optional start date
            date_to: Optional end date
            
        Returns:
            FinancialSummary with totals and counts
        """
        query = db.query(Transaction)
        
        # Apply filters
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        if date_from:
            query = query.filter(Transaction.date >= date_from)
        if date_to:
            query = query.filter(Transaction.date <= date_to)
        
        # Calculate totals using aggregation
        result = query.with_entities(
            func.sum(
                case(
                    (Transaction.type == TransactionType.INCOME, Transaction.amount),
                    else_=0
                )
            ).label("total_income"),
            func.sum(
                case(
                    (Transaction.type == TransactionType.EXPENSE, Transaction.amount),
                    else_=0
                )
            ).label("total_expenses"),
            func.count().label("transaction_count"),
            func.sum(
                case(
                    (Transaction.type == TransactionType.INCOME, 1),
                    else_=0
                )
            ).label("income_count"),
            func.sum(
                case(
                    (Transaction.type == TransactionType.EXPENSE, 1),
                    else_=0
                )
            ).label("expense_count")
        ).first()
        
        total_income = float(result.total_income or 0)
        total_expenses = float(result.total_expenses or 0)
        
        return FinancialSummary(
            total_income=total_income,
            total_expenses=total_expenses,
            balance=total_income - total_expenses,
            transaction_count=result.transaction_count or 0,
            income_count=int(result.income_count or 0),
            expense_count=int(result.expense_count or 0)
        )
    
    @staticmethod
    def get_category_breakdown(
        db: Session,
        user_id: Optional[int] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        transaction_type: Optional[TransactionType] = None
    ) -> CategoryBreakdownResponse:
        """
        Get breakdown of transactions by category.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter by ownership
            date_from: Optional start date
            date_to: Optional end date
            transaction_type: Optional filter by transaction type
            
        Returns:
            CategoryBreakdownResponse with category-wise statistics
        """
        query = db.query(Transaction)
        
        # Apply filters
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        if date_from:
            query = query.filter(Transaction.date >= date_from)
        if date_to:
            query = query.filter(Transaction.date <= date_to)
        if transaction_type:
            query = query.filter(Transaction.type == transaction_type)
        
        # Get total first
        total_count = query.count()
        
        # Group by category
        results = query.with_entities(
            Transaction.category,
            func.sum(Transaction.amount).label("total"),
            func.count().label("count")
        ).group_by(Transaction.category).all()
        
        total_amount = sum(float(r.total or 0) for r in results)
        
        categories = []
        for r in results:
            percentage = (float(r.count or 0) / total_count * 100) if total_count > 0 else 0
            average = float(r.total or 0) / (r.count or 1)
            
            categories.append(CategoryBreakdown(
                category=r.category,
                total=float(r.total or 0),
                count=r.count or 0,
                percentage=round(percentage, 2),
                average=round(average, 2)
            ))
        
        # Sort by total amount descending
        categories.sort(key=lambda x: x.total, reverse=True)
        
        return CategoryBreakdownResponse(
            categories=categories,
            total_transactions=total_count,
            total_amount=total_amount
        )
    
    @staticmethod
    def get_monthly_summary(
        db: Session,
        user_id: Optional[int] = None,
        year: Optional[int] = None
    ) -> MonthlySummaryResponse:
        """
        Get monthly financial summary.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter by ownership
            year: Optional year to filter by (defaults to current year)
            
        Returns:
            MonthlySummaryResponse with monthly data
        """
        query = db.query(Transaction)
        
        # Apply filters
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        if year:
            query = query.filter(extract('year', Transaction.date) == year)
        
        # Group by month and year
        results = query.with_entities(
            extract('year', Transaction.date).label('year'),
            extract('month', Transaction.date).label('month'),
            func.sum(
                case(
                    (Transaction.type == TransactionType.INCOME, Transaction.amount),
                    else_=0
                )
            ).label("income"),
            func.sum(
                case(
                    (Transaction.type == TransactionType.EXPENSE, Transaction.amount),
                    else_=0
                )
            ).label("expenses"),
            func.count().label("count")
        ).group_by('year', 'month').order_by('year', 'month').all()
        
        monthly_data = []
        total_income = 0.0
        total_expenses = 0.0
        
        for r in results:
            income = float(r.income or 0)
            expenses = float(r.expenses or 0)
            total_income += income
            total_expenses += expenses
            
            monthly_data.append(MonthlySummary(
                month=int(r.month),
                year=int(r.year),
                income=income,
                expenses=expenses,
                net=income - expenses,
                transaction_count=r.count
            ))
        
        # Calculate averages
        num_months = len(monthly_data) if monthly_data else 1
        avg_monthly_income = total_income / num_months
        avg_monthly_expenses = total_expenses / num_months
        
        return MonthlySummaryResponse(
            monthly_data=monthly_data,
            total_income=total_income,
            total_expenses=total_expenses,
            average_monthly_income=round(avg_monthly_income, 2),
            average_monthly_expenses=round(avg_monthly_expenses, 2)
        )
    
    @staticmethod
    def get_recent_activity(
        db: Session,
        user_id: Optional[int] = None,
        days: int = 30,
        limit: int = 10
    ) -> RecentActivity:
        """
        Get recent transaction activity.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter by ownership
            days: Number of days to look back
            limit: Maximum number of transactions to return
            
        Returns:
            RecentActivity with recent transactions
        """
        cutoff_date = date.today() - timedelta(days=days)
        
        query = db.query(Transaction).filter(Transaction.date >= cutoff_date)
        
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        
        transactions = query.order_by(Transaction.date.desc()).limit(limit).all()
        total = query.count()
        
        return RecentActivity(
            transactions=[TransactionResponse.model_validate(t) for t in transactions],
            total=total,
            days=days
        )
    
    @staticmethod
    def export_transactions(
        db: Session,
        user_id: Optional[int] = None,
        format: str = "json",
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> list[dict]:
        """
        Export transactions for external use.
        
        Args:
            db: Database session
            user_id: Optional user ID to filter by ownership
            format: Export format (json or csv)
            date_from: Optional start date
            date_to: Optional end date
            
        Returns:
            List of transaction dictionaries
        """
        query = db.query(Transaction)
        
        # Apply filters
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        if date_from:
            query = query.filter(Transaction.date >= date_from)
        if date_to:
            query = query.filter(Transaction.date <= date_to)
        
        transactions = query.order_by(Transaction.date.desc()).all()
        
        return [
            {
                "id": t.id,
                "amount": t.amount,
                "type": t.type.value,
                "category": t.category,
                "date": t.date.isoformat(),
                "notes": t.notes,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in transactions
        ]
