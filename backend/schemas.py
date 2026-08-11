from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class StockPriceSchema(BaseModel):
    symbol: str
    exchange: str

    trading_date: datetime

    close_price: float
    open_price: float
    high_price: float
    low_price: float

    volume: int

    model_config = ConfigDict(
        from_attributes=True
    )


class CompanySchema(BaseModel):
    symbol: str
    exchange: str

    model_config = ConfigDict(
        from_attributes=True
    )


class StockDashboardResponse(BaseModel):
    symbol: str
    exchange: str

    last_updated: Optional[datetime] = None

    latest_metrics: Optional[StockPriceSchema] = None

    history: List[StockPriceSchema] = Field(
        default_factory=list
    )

    is_stale: bool = False

    warning_message: Optional[str] = None


class CompanyListResponse(BaseModel):
    companies: List[CompanySchema]
