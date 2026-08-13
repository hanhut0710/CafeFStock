import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from models import Company, StockPrice
from schemas import (
    CompanySchema,
    StockDashboardResponse,
    StockPriceSchema,
)
from services.cafef_provider import fetch_cafef_daily_data
from services.data_importer import import_stock_records


logger = logging.getLogger(__name__)


REFRESH_INTERVAL = timedelta(hours=1)
INITIAL_START_DATE = date(2026, 7, 1)

def get_or_create_company(
    db: Session,
    symbol: str,
) -> Company:
    """
    Find a company by symbol.

    A company is created only after CafeF data provides
    the exchange information.
    """

    symbol_upper = symbol.strip().upper()

    company = (
        db.query(Company)
        .filter(
            Company.symbol == symbol_upper,
        )
        .first()
    )

    if company is None:
        raise ValueError(
            f"Company '{symbol_upper}' is not available."
        )

    return company


def get_latest_database_update(
    db: Session,
) -> Optional[datetime]:
    """
    Return the latest Company.last_updated timestamp
    across the entire database.
    """

    latest_company = (
        db.query(Company)
        .filter(
            Company.last_updated.isnot(None)
        )
        .order_by(
            Company.last_updated.desc()
        )
        .first()
    )

    if latest_company is None:
        return None

    return latest_company.last_updated


def is_data_stale(
    db: Session,
) -> bool:
    """
    Determine whether CafeF data should be refreshed.

    Data is considered stale when:
    - Database has never been imported.
    - Last import was more than one hour ago.
    - Last imported trading date is older than today.

    Note:
    The trading-date check ensures that a new trading day
    can trigger a refresh even if the previous import was
    less than one hour ago.
    """

    latest_update = get_latest_database_update(db)

    if latest_update is None:
        return True

    now = datetime.utcnow()

    if now - latest_update > REFRESH_INTERVAL:
        return True

    latest_price = (
        db.query(StockPrice)
        .order_by(
            StockPrice.trading_date.desc()
        )
        .first()
    )

    if latest_price is None:
        return True

    if latest_price.trading_date.date() < date.today():
        return True

    return False

def get_latest_trading_date(db: Session):
    result = (
        db.query(func.max(StockPrice.trading_date))
        .scalar()
    )

    return result.date() if result else None

def refresh_cafef_data(
    db: Session,
) -> dict:
    """
    Download and import CafeF data for all exchanges.

    CafeF daily ZIP contains:
    - HSX
    - HNX
    - UPCOM

    Therefore one refresh updates the whole database.
    """

    # logger.info(
    #     "Starting CafeF refresh for %s",
    #     target_date,
    # )

    lastest_date = get_latest_trading_date(db)

    if lastest_date is None:
        lastest_date = INITIAL_START_DATE

    today = date.today()

    while lastest_date <= today:
        print(f"🔥 STARTING CAFEF REFRESH: {lastest_date}")
        records = fetch_cafef_daily_data(
            target_date=lastest_date,
        )

        if not records:
            raise ValueError(
                f"CafeF returned no data for {lastest_date}"
            )

        result = import_stock_records(
            db=db,
            records=records,
        )

        # logger.info(
        #     "CafeF refresh completed: %s",
        #     result,
        # )
        print(f"✅ CAFEF REFRESH COMPLETED: {result}")

        lastest_date += timedelta(days=1)
    # print(f"🔥 STARTING CAFEF REFRESH: {target_date}")
    # records = fetch_cafef_daily_data(
    #     target_date=target_date,
    # )

    # if not records:
    #     raise ValueError(
    #         f"CafeF returned no data for {target_date}"
    #     )

    # result = import_stock_records(
    #     db=db,
    #     records=records,
    # )

    # # logger.info(
    # #     "CafeF refresh completed: %s",
    # #     result,
    # # )
    # print(f"✅ CAFEF REFRESH COMPLETED: {result}")
    # return result


def get_stock_dashboard(
    db: Session,
    symbol: str,
    force_refresh: bool = False,
) -> StockDashboardResponse:
    """
    Return dashboard data for a stock symbol.

    Refresh policy:
        - force_refresh=True -> always refresh CafeF data.
        - No existing company data -> refresh CafeF data.
        - Company data older than REFRESH_INTERVAL -> refresh CafeF data.
        - Otherwise -> use existing SQLite data.

    If CafeF refresh fails:
        - Return existing SQLite data if available.
        - Set is_stale=True.
        - Provide warning_message.

    If no SQLite data exists and CafeF refresh fails:
        - Raise ValueError.
    """

    print("🚨🚨 GET STOCK DASHBOARD CALLED")

    symbol_upper = symbol.strip().upper()

    is_stale = False
    warning_message: Optional[str] = None

    # ---------------------------------------------------------
    # 1. Find existing company
    # ---------------------------------------------------------

    company = (
        db.query(Company)
        .filter(Company.symbol == symbol_upper)
        .first()
    )

    # ---------------------------------------------------------
    # 2. Determine whether CafeF data needs refreshing
    # ---------------------------------------------------------

    now = datetime.utcnow()

    if company is None:
        needs_refresh = True
    elif company.last_updated is None:
        needs_refresh = True
    else:
        data_age = now - company.last_updated
        needs_refresh = data_age > REFRESH_INTERVAL

    # force_refresh always overrides the normal refresh policy
    if force_refresh:
        needs_refresh = True

    # Debug information
    print("📊 Symbol:", symbol_upper)
    print("🕐 Company last_updated:", company.last_updated if company else None)
    print("🕐 Current time:", now)

    if company and company.last_updated:
        print(
            "🕐 Data age:",
            now - company.last_updated
        )

    print("⏱️ Refresh interval:", REFRESH_INTERVAL)
    print("🔥 needs_refresh:", needs_refresh)
    print("🔥 force_refresh:", force_refresh)

    # ---------------------------------------------------------
    # 3. Refresh CafeF data if necessary
    # ---------------------------------------------------------

    if needs_refresh:
        print("🔥🔥 REFRESHING CAFEF NOW")

        try:
            refresh_cafef_data(
                db=db,
            )

            print("✅ CAFEF REFRESH COMPLETED")

            # Re-query company because refresh_cafef_data()
            # may create/update Company records.
            company = (
                db.query(Company)
                .filter(Company.symbol == symbol_upper)
                .first()
            )

        except Exception as exc:
            logger.warning(
                "CafeF refresh failed for %s: %s",
                symbol_upper,
                exc,
            )

            print("❌ CAFEF REFRESH FAILED:", repr(exc))

            is_stale = True

            warning_message = (
                "Không thể cập nhật dữ liệu mới từ CafeF. "
                "Đang hiển thị dữ liệu lưu trữ."
            )

    # ---------------------------------------------------------
    # 4. Query stock history from SQLite
    # ---------------------------------------------------------

    prices_db = (
        db.query(StockPrice)
        .filter(
            StockPrice.symbol == symbol_upper,
        )
        .order_by(
            StockPrice.trading_date.asc()
        )
        .all()
    )

    # ---------------------------------------------------------
    # 5. Handle missing stock data
    # ---------------------------------------------------------

    if not prices_db:
        if is_stale:
            raise ValueError(
                f"Không có dữ liệu lưu trữ cho mã "
                f"{symbol_upper} và không thể kết nối CafeF."
            )

        raise ValueError(
            f"Không tìm thấy dữ liệu cho mã "
            f"{symbol_upper}."
        )

    # ---------------------------------------------------------
    # 6. Determine exchange
    # ---------------------------------------------------------

    exchanges = {
        price.exchange
        for price in prices_db
    }

    if len(exchanges) > 1:
        logger.warning(
            "Symbol %s exists on multiple exchanges: %s",
            symbol_upper,
            exchanges,
        )

    exchange = prices_db[-1].exchange

    # ---------------------------------------------------------
    # 7. Get latest company metadata
    # ---------------------------------------------------------

    company = (
        db.query(Company)
        .filter(
            Company.symbol == symbol_upper,
            Company.exchange == exchange,
        )
        .first()
    )

    last_updated = (
        company.last_updated
        if company
        else None
    )

    # ---------------------------------------------------------
    # 8. Convert database models to Pydantic schemas
    # ---------------------------------------------------------

    history = [
        StockPriceSchema.model_validate(price)
        for price in prices_db
    ]

    latest_metrics = history[-1]

    # ---------------------------------------------------------
    # 9. Return dashboard response
    # ---------------------------------------------------------

    return StockDashboardResponse(
        symbol=symbol_upper,
        exchange=exchange,
        last_updated=last_updated,
        latest_metrics=latest_metrics,
        history=history,
        is_stale=is_stale,
        warning_message=warning_message,
    )

def list_companies(
    db: Session,
) -> List[CompanySchema]:
    """
    Return all companies imported from CafeF.
    """

    companies = (
        db.query(Company)
        .order_by(
            Company.symbol.asc()
        )
        .all()
    )

    return [
        CompanySchema.model_validate(company)
        for company in companies
    ]

