from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from schemas import StockDashboardResponse, CompanySchema, CompanyListResponse
import services.stock_service as stock_service

router = APIRouter(prefix="/api")

@router.get("/companies", response_model=CompanyListResponse)
def get_companies(db: Session = Depends(get_db)):
    """Retrieves list of tracked companies."""
    companies = stock_service.list_companies(db)
    return CompanyListResponse(companies=companies)


@router.get("/stocks/{symbol}", response_model=StockDashboardResponse)
def get_stock_data(
    symbol: str, 
    force_refresh: bool = Query(False, description="Set true to force refetching from CafeF"),
    db: Session = Depends(get_db)
):
    """Retrieves stock dashboard metrics and historical price data for a symbol."""
    return stock_service.get_stock_dashboard(db, symbol=symbol, force_refresh=force_refresh)


@router.post("/companies/{symbol}", response_model=CompanySchema)
def add_new_company(symbol: str, db: Session = Depends(get_db)):
    """Tracks a new company by symbol."""
    company = stock_service.get_or_create_company(db, symbol)
    return CompanySchema.model_validate(company)
