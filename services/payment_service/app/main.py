from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, String, ForeignKey, DECIMAL, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session, relationship
from datetime import datetime
import uuid
from uuid import UUID as PythonUUID
import enum
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from decimal import Decimal
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../'))
from shared.database_config import get_db, create_tables, Base

# Models
class TransactionType(str, enum.Enum):
    RIDE_PAYMENT = "RIDE_PAYMENT"
    WALLET_TOPUP = "WALLET_TOPUP"
    WITHDRAWAL = "WITHDRAWAL"
    REFUND = "REFUND"

class TransactionStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"

class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), unique=True, nullable=False, index=True)
    balance = Column(DECIMAL(10, 2), default=0.00)
    currency = Column(String(3), default="BDT")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ride_id = Column(UUID(as_uuid=True))
    from_wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    to_wallet_id = Column(UUID(as_uuid=True), ForeignKey("wallets.id"), nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    status = Column(SQLEnum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

# Schemas
class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: PythonUUID
    user_id: PythonUUID
    balance: Decimal
    currency: str
    is_active: bool

class TransactionCreate(BaseModel):
    ride_id: Optional[PythonUUID] = None
    to_user_id: PythonUUID
    amount: Decimal = Field(..., gt=0)
    transaction_type: TransactionType
    description: Optional[str] = None

class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: PythonUUID
    ride_id: Optional[PythonUUID]
    amount: Decimal
    transaction_type: TransactionType
    status: TransactionStatus
    description: Optional[str]
    created_at: datetime

app = FastAPI(title="RickshawX Payment Service", version="1.0.0")

@app.on_event("startup")
async def startup():
    create_tables()

# Mock user validation (replace with actual user service call)
async def get_current_user_id() -> PythonUUID:
    return PythonUUID("12345678-1234-5678-9012-123456789012")

@app.post("/api/v1/wallets", response_model=WalletResponse)
async def create_wallet(user_id: PythonUUID, db: Session = Depends(get_db)):
    """Create wallet for user"""
    existing = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Wallet already exists")
    
    wallet = Wallet(user_id=user_id)
    db.add(wallet)
    db.commit()
    db.refresh(wallet)
    return wallet

@app.get("/api/v1/wallets/{user_id}", response_model=WalletResponse)
async def get_wallet(user_id: PythonUUID, db: Session = Depends(get_db)):
    """Get wallet by user ID"""
    wallet = db.query(Wallet).filter(Wallet.user_id == user_id).first()
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return wallet

@app.post("/api/v1/transactions", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate, 
    from_user_id: PythonUUID = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    """Create transaction between wallets"""
    # Get wallets
    from_wallet = db.query(Wallet).filter(Wallet.user_id == from_user_id).first()
    to_wallet = db.query(Wallet).filter(Wallet.user_id == transaction.to_user_id).first()
    
    if not from_wallet or not to_wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    # Check balance for debit transactions
    if transaction.transaction_type == TransactionType.RIDE_PAYMENT:
        if from_wallet.balance < transaction.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Create transaction
    db_transaction = Transaction(
        ride_id=transaction.ride_id,
        from_wallet_id=from_wallet.id,
        to_wallet_id=to_wallet.id,
        amount=transaction.amount,
        transaction_type=transaction.transaction_type,
        description=transaction.description,
        status=TransactionStatus.COMPLETED,  # Mock success
        completed_at=datetime.utcnow()
    )
    
    # Update balances
    if transaction.transaction_type == TransactionType.RIDE_PAYMENT:
        from_wallet.balance -= transaction.amount
        to_wallet.balance += transaction.amount
    
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "payment-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003) 