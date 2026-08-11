# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKeyConstraint, Index
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    exchange = Column(String, index=True, nullable=False)
    name = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

    stock_prices = relationship("StockPrice", back_populates="company", cascade="all, delete-orphan")


class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    exchange = Column(String, index=True, nullable=False)
    trading_date = Column(DateTime, index=True, nullable=False)
    close_price = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)

    company = relationship("Company", 
        back_populates="stock_prices", 
        primaryjoin=("and_(" "StockPrice.symbol == Company.symbol, " "StockPrice.exchange == Company.exchange" ")" ), 
        foreign_keys="[StockPrice.symbol, StockPrice.exchange]",
    )

    __table_args__ = (
        ForeignKeyConstraint( ["symbol", "exchange"], ["companies.symbol", "companies.exchange"], ), 
        Index( "idx_symbol_exchange_date", "symbol", "exchange", "trading_date", unique=True, )
    )
