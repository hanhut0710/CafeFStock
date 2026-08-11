from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

    stock_prices = relationship("StockPrice", back_populates="company", cascade="all, delete-orphan")


class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, ForeignKey("companies.symbol"), index=True, nullable=False)
    trading_date = Column(DateTime, index=True, nullable=False)
    close_price = Column(Float, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)

    company = relationship("Company", back_populates="stock_prices")


Index("idx_symbol_date", StockPrice.symbol, StockPrice.trading_date, unique=True)
