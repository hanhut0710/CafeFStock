from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class StockPriceSchema(BaseModel):
    trading_date: datetime
    close_price: float
    open_price: float
    high_price: float
    low_price: float
    volume: int

    class Config:
        from_attributes = True


class CompanySchema(BaseModel):
    symbol: str
    name: Optional[str] = None
    last_updated: Optional[datetime] = None

    class Config:
        from_attributes = True


class StockDashboardResponse(BaseModel):
    symbol: str
    name: Optional[str] = None
    last_updated: Optional[datetime] = None
    latest_metrics: Optional[StockPriceSchema] = None
    history: List[StockPriceSchema] = []
    is_stale: bool = False
    warning_message: Optional[str] = None


class CompanyListResponse(BaseModel):
    companies: List[CompanySchema]
