from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert
from datetime import datetime, timedelta
import logging
from typing import List, Optional

from models import Company, StockPrice
from schemas import StockDashboardResponse, StockPriceSchema, CompanySchema
from services.cafef_provider import fetch_stock_history_cafef

logger = logging.getLogger(__name__)

REFRESH_INTERVAL = timedelta(hours=1)

def get_or_create_company(db: Session, symbol: str) -> Company:
    symbol_upper = symbol.strip().upper()
    company = db.query(Company).filter(Company.symbol == symbol_upper).first()
    if not company:
        company = Company(symbol=symbol_upper, name=f"Công ty cổ phần {symbol_upper}")
        db.add(company)
        db.commit()
        db.refresh(company)
    return company


def update_stock_prices_in_db(db: Session, company: Company, raw_prices: List[dict]):
    """Upserts stock prices into SQLite DB and updates company last_updated timestamp."""
    for item in raw_prices:
        stmt = insert(StockPrice).values(
            symbol=company.symbol,
            trading_date=item["trading_date"],
            close_price=item["close_price"],
            open_price=item["open_price"],
            high_price=item["high_price"],
            low_price=item["low_price"],
            volume=item["volume"]
        ).on_conflict_do_update(
            index_elements=['symbol', 'trading_date'],
            set_={
                'close_price': item["close_price"],
                'open_price': item["open_price"],
                'high_price': item["high_price"],
                'low_price': item["low_price"],
                'volume': item["volume"]
            }
        )
        db.execute(stmt)
    
    company.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(company)


def get_stock_dashboard(db: Session, symbol: str, force_refresh: bool = False) -> StockDashboardResponse:
    symbol_upper = symbol.strip().upper()
    company = get_or_create_company(db, symbol_upper)
    
    now = datetime.utcnow()
    is_stale = False
    warning_message = None

    # Check if refresh is needed (older than 1 hour or never updated or force_refresh)
    needs_refresh = force_refresh or (company.last_updated is None) or (now - company.last_updated > REFRESH_INTERVAL)

    if needs_refresh:
        try:
            logger.info(f"Fetching fresh data from CafeF for {symbol_upper}...")
            fresh_data = fetch_stock_history_cafef(symbol_upper)
            update_stock_prices_in_db(db, company, fresh_data)
        except Exception as e:
            logger.warning(f"Failed to fetch data from CafeF for {symbol_upper}: {e}")
            is_stale = True
            warning_message = f"Không thể cập nhật từ CafeF ({str(e)}). Đang hiển thị dữ liệu lưu trữ."

    # Fetch stored history from DB
    prices_db = (
        db.query(StockPrice)
        .filter(StockPrice.symbol == symbol_upper)
        .order_by(StockPrice.trading_date.asc())
        .all()
    )

    history = [StockPriceSchema.model_validate(p) for p in prices_db]
    latest_metrics = history[-1] if history else None

    # If no history exists at all and fetch failed
    if not history and is_stale:
        warning_message = f"Không thể kết nối với CafeF và chưa có dữ liệu lưu trữ cho mã {symbol_upper}."

    return StockDashboardResponse(
        symbol=company.symbol,
        name=company.name,
        last_updated=company.last_updated,
        latest_metrics=latest_metrics,
        history=history,
        is_stale=is_stale,
        warning_message=warning_message
    )


def list_companies(db: Session) -> List[CompanySchema]:
    # Ensure default symbols exist if DB is fresh
    default_symbols = ["A32", "SSI", "VIC", "VNM", "HPG", "FPT"]
    for sym in default_symbols:
        if not db.query(Company).filter(Company.symbol == sym).first():
            db.add(Company(symbol=sym, name=f"Công ty cổ phần {sym}"))
    db.commit()

    companies = db.query(Company).order_by(Company.symbol.asc()).all()
    return [CompanySchema.model_validate(c) for c in companies]
