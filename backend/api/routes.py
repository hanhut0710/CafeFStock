from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import (
    StockDashboardResponse,
    CompanyListResponse,
)
import services.stock_service as stock_service


router = APIRouter(prefix="/api")


@router.get(
    "/companies",
    response_model=CompanyListResponse,
)
def get_companies(
    db: Session = Depends(get_db),
):
    """
    Retrieve all companies available in SQLite.
    """

    companies = stock_service.list_companies(db)

    return CompanyListResponse(
        companies=companies
    )


@router.get("/stocks/{symbol}", response_model=StockDashboardResponse)
def get_stock_data(
    symbol: str,
    force_refresh: bool = Query(
        False,
        description="Set true to force refetching from CafeF"
    ),
    db: Session = Depends(get_db)
):
    """Retrieves stock dashboard metrics and historical price data for a symbol."""

    try:
        print("🚨🚨 GET STOCK DASHBOARD CALLED")

        result = stock_service.get_stock_dashboard(
            db,
            symbol=symbol,
            force_refresh=force_refresh
        )

        print("✅ GET STOCK DASHBOARD SUCCESS")
        return result

    except Exception as e:
        import traceback

        print("💥💥 STOCK DASHBOARD ERROR")
        print("ERROR:", repr(e))
        traceback.print_exc()

        raise