import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from models import Company, StockPrice


logger = logging.getLogger(__name__)


def import_stock_records(
    db: Session,
    records: List[Dict[str, Any]],
) -> Dict[str, int]:
    """
    Import normalized CafeF records into SQLite.

    Expected record format:

        {
            "symbol": "ACB",
            "exchange": "HSX",
            "trading_date": datetime(...),
            "open_price": 22.65,
            "high_price": 22.75,
            "low_price": 22.50,
            "close_price": 22.65,
            "volume": 9756800
        }

    Returns import statistics.
    """

    companies_created = 0
    companies_updated = 0
    prices_created = 0
    prices_skipped = 0

    company_cache: Dict[tuple[str, str], Company] = {}

    # One timestamp for the whole import operation.
    import_time = datetime.utcnow()

    try:
        for record in records:
            symbol = record["symbol"].strip().upper()
            exchange = record["exchange"].strip().upper()

            trading_date = record["trading_date"]

            # Normalize trading date to midnight.
            if isinstance(trading_date, datetime):
                trading_date = trading_date.replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                )

            company_key = (symbol, exchange)

            # -------------------------------------------------
            # 1. Find or create Company
            # -------------------------------------------------

            company = company_cache.get(company_key)

            if company is None:
                company = (
                    db.query(Company)
                    .filter(
                        Company.symbol == symbol,
                        Company.exchange == exchange,
                    )
                    .first()
                )

                if company is None:
                    company = Company(
                        symbol=symbol,
                        exchange=exchange,
                        name=None,
                        last_updated=import_time,
                    )

                    db.add(company)
                    db.flush()

                    companies_created += 1

                else:
                    company.last_updated = import_time
                    companies_updated += 1

                company_cache[company_key] = company

            # -------------------------------------------------
            # 2. Check duplicate StockPrice
            # -------------------------------------------------

            existing_price = (
                db.query(StockPrice)
                .filter(
                    StockPrice.symbol == symbol,
                    StockPrice.exchange == exchange,
                    StockPrice.trading_date == trading_date,
                )
                .first()
            )

            if existing_price is not None:
                # The record already exists.
                # We still consider the company refreshed.
                company.last_updated = import_time

                prices_skipped += 1
                continue

            # -------------------------------------------------
            # 3. Insert StockPrice
            # -------------------------------------------------

            stock_price = StockPrice(
                symbol=symbol,
                exchange=exchange,
                trading_date=trading_date,
                open_price=float(record["open_price"]),
                high_price=float(record["high_price"]),
                low_price=float(record["low_price"]),
                close_price=float(record["close_price"]),
                volume=int(record["volume"]),
            )

            db.add(stock_price)

            prices_created += 1

        # -----------------------------------------------------
        # 4. Commit everything in one transaction
        # -----------------------------------------------------

        db.commit()

        logger.info(
            "CafeF import completed: "
            "companies_created=%s, "
            "companies_updated=%s, "
            "prices_created=%s, "
            "prices_skipped=%s",
            companies_created,
            companies_updated,
            prices_created,
            prices_skipped,
        )

        return {
            "companies_created": companies_created,
            "companies_updated": companies_updated,
            "prices_created": prices_created,
            "prices_skipped": prices_skipped,
        }

    except Exception:
        db.rollback()

        logger.exception(
            "CafeF data import failed"
        )

        raise
