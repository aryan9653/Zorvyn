"""
Transaction model for financial records.
"""

from sqlalchemy import Column, Integer, Float, String, Text, Date, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum


class TransactionType(str, enum.Enum):
    """Transaction types for financial records."""
    INCOME = "income"
    EXPENSE = "expense"


class Transaction(Base):
    """Transaction model for financial records."""
    
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    type = Column(Enum(TransactionType), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to user
    user = relationship("User", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, type={self.type}, category='{self.category}')>"
