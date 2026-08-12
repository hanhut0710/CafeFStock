from __future__ import annotations

import csv
import io
import logging
import sys
import zipfile
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

import requests
from sqlalchemy.exc import SQLAlchemyError

# ---------------------------------------------------------
# Make backend imports work when running:
#
# python scripts/backfill_historical_data.py
# ---------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from database import SessionLocal
from models import Company, StockPrice


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

CAFef_BASE_URL = (
    "http://cafef1.mediacdn.vn/data/ami_data"
)

START_DATE = date(2026, 7, 1)

EXCHANGES = {
    "HSX": "HSX",
    "HNX": "HNX",
    "UPCOM": "UPCOM",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

REQUEST_TIMEOUT = 30


# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------
# URL
# ---------------------------------------------------------

def build_zip_url(target_date: date) -> str:
    """
    Build CafeF daily ZIP URL.

    Example:
        2026-08-11
        ->
        http://cafef1.mediacdn.vn/data/ami_data/
        20260811/CafeF.SolieuGD.20260811.zip
    """

    date_string = target_date.strftime("%Y%m%d")
    date_string_2 = target_date.strftime("%d%m%Y")

    return (
        f"{CAFef_BASE_URL}/"
        f"{date_string}/"
        f"CafeF.SolieuGD.{date_string_2}.zip"
    )


# ---------------------------------------------------------
# Download ZIP
# ---------------------------------------------------------

def download_zip(target_date: date) -> Optional[bytes]:
    """
    Download CafeF ZIP for a specific date.

    Returns:
        bytes if successful
        None if file does not exist (404)
    """

    url = build_zip_url(target_date)

    logger.info("Downloading: %s", url)

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        if response.status_code == 404:
            logger.warning(
                "SKIP %s - CafeF file not available yet.",
                target_date,
            )
            return None

        response.raise_for_status()

        if not response.content:
            logger.warning(
                "SKIP %s - empty response.",
                target_date,
            )
            return None

        logger.info(
            "Downloaded %.2f MB",
            len(response.content) / 1024 / 1024,
        )

        return response.content

    except requests.RequestException as exc:
        logger.error(
            "Download failed for %s: %s",
            target_date,
            exc,
        )

        return None


# ---------------------------------------------------------
# CSV parser
# ---------------------------------------------------------

def parse_csv_content(
    csv_content: bytes,
) -> list[dict]:
    """
    Parse CafeF CSV content.

    Expected columns:

        Ticker
        DTYYYYMMDD
        Open
        High
        Low
        Close
        Volume
    """

    # CafeF files are generally UTF-8 / ANSI compatible.
    # utf-8-sig also removes BOM if present.
    text = csv_content.decode(
        "utf-8-sig",
        errors="replace",
    )

    reader = csv.DictReader(
        io.StringIO(text)
    )

    records = []

    for row in reader:
        ticker = (
            row.get("Ticker")
            or row.get("<Ticker>")
            or ""
        ).strip().upper()

        date_raw = (
            row.get("DTYYYYMMDD")
            or row.get("<DTYYYYMMDD>")
            or ""
        ).strip()

        open_raw = (
            row.get("Open")
            or row.get("<Open>")
        )

        high_raw = (
            row.get("High")
            or row.get("<High>")
        )

        low_raw = (
            row.get("Low")
            or row.get("<Low>")
        )

        close_raw = (
            row.get("Close")
            or row.get("<Close>")
        )

        volume_raw = (
            row.get("Volume")
            or row.get("<Volume>")
        )

        if not ticker or not date_raw:
            continue

        try:
            trading_date = datetime.strptime(
                date_raw,
                "%Y%m%d",
            )

            open_price = float(open_raw)
            high_price = float(high_raw)
            low_price = float(low_raw)
            close_price = float(close_raw)
            volume = int(float(volume_raw))

        except (
            ValueError,
            TypeError,
        ):
            logger.debug(
                "Skipping invalid row: %s",
                row,
            )
            continue

        records.append(
            {
                "symbol": ticker,
                "trading_date": trading_date,
                "open_price": open_price,
                "high_price": high_price,
                "low_price": low_price,
                "close_price": close_price,
                "volume": volume,
            }
        )

    return records


# ---------------------------------------------------------
# Extract + parse ZIP
# ---------------------------------------------------------

def extract_and_parse_zip(
    zip_bytes: bytes,
    target_date: date,
) -> dict[str, list[dict]]:
    """
    Extract the three exchange CSV files from ZIP.

    Returns:

        {
            "HSX": [...],
            "HNX": [...],
            "UPCOM": [...]
        }
    """

    result = {
        "HSX": [],
        "HNX": [],
        "UPCOM": [],
    }

    expected_date = target_date.strftime(
        "%d.%m.%Y"
    )

    with zipfile.ZipFile(
        io.BytesIO(zip_bytes)
    ) as zf:

        file_names = zf.namelist()

        logger.info(
            "ZIP contains %d files.",
            len(file_names),
        )

        for exchange in EXCHANGES:
            expected_prefix = (
                f"CafeF.{exchange}.{expected_date}"
            )

            matching_file = None

            for file_name in file_names:
                normalized_name = Path(
                    file_name
                ).name

                if normalized_name.startswith(
                    expected_prefix
                ) and normalized_name.lower().endswith(
                    ".csv"
                ):
                    matching_file = file_name
                    break

            if matching_file is None:
                logger.warning(
                    "%s CSV not found in ZIP.",
                    exchange,
                )
                continue

            logger.info(
                "Parsing %s: %s",
                exchange,
                matching_file,
            )

            csv_bytes = zf.read(
                matching_file
            )

            records = parse_csv_content(
                csv_bytes
            )

            result[exchange] = records

            logger.info(
                "%s: %d records",
                exchange,
                len(records),
            )

    return result


# ---------------------------------------------------------
# Company
# ---------------------------------------------------------

def get_or_create_company(
    db,
    symbol: str,
    exchange: str,
) -> Company:
    """
    Find existing company or create it.
    """

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
            name=f"Công ty cổ phần {symbol}",
            last_updated=None,
        )

        db.add(company)

    return company


# ---------------------------------------------------------
# Import one exchange
# ---------------------------------------------------------

def import_exchange_records(
    db,
    exchange: str,
    records: list[dict],
) -> int:
    """
    Insert/update StockPrice records.

    Uses the existing unique constraint:

        symbol + trading_date

    so running the script multiple times is safe.
    """

    imported_count = 0

    for item in records:

        symbol = item["symbol"]

        company = get_or_create_company(
            db=db,
            symbol=symbol,
            exchange=exchange,
        )

        existing = (
            db.query(StockPrice)
            .filter(
                StockPrice.symbol == symbol,
                StockPrice.trading_date
                == item["trading_date"],
            )
            .first()
        )

        if existing:
            # Update existing record
            existing.exchange = exchange
            existing.open_price = (
                item["open_price"]
            )
            existing.high_price = (
                item["high_price"]
            )
            existing.low_price = (
                item["low_price"]
            )
            existing.close_price = (
                item["close_price"]
            )
            existing.volume = item["volume"]

        else:
            stock_price = StockPrice(
                symbol=symbol,
                exchange=exchange,
                trading_date=item[
                    "trading_date"
                ],
                open_price=item[
                    "open_price"
                ],
                high_price=item[
                    "high_price"
                ],
                low_price=item[
                    "low_price"
                ],
                close_price=item[
                    "close_price"
                ],
                volume=item["volume"],
            )

            db.add(stock_price)

        imported_count += 1

    return imported_count


# ---------------------------------------------------------
# Import one day
# ---------------------------------------------------------

def process_date(
    db,
    target_date: date,
) -> int:
    """
    Download and import one trading day.

    Returns number of imported/updated records.
    """

    zip_bytes = download_zip(
        target_date
    )

    if zip_bytes is None:
        return 0

    parsed_data = extract_and_parse_zip(
        zip_bytes,
        target_date,
    )

    total_records = 0

    for exchange, records in parsed_data.items():

        if not records:
            continue

        count = import_exchange_records(
            db=db,
            exchange=exchange,
            records=records,
        )

        total_records += count

        logger.info(
            "%s: imported %d records",
            exchange,
            count,
        )

    return total_records


# ---------------------------------------------------------
# Main backfill
# ---------------------------------------------------------

def main():
    today = date.today()

    logger.info("")
    logger.info("=" * 60)
    logger.info("CafeF Historical Backfill")
    logger.info(
        "Range: %s -> %s",
        START_DATE,
        today,
    )
    logger.info("=" * 60)
    logger.info("")

    if START_DATE > today:
        logger.error(
            "START_DATE is later than today."
        )
        return

    db = SessionLocal()

    current_date = START_DATE

    processed_dates = 0
    skipped_dates = 0
    failed_dates = 0
    total_records = 0

    try:

        total_days = (
            today - START_DATE
        ).days + 1

        day_number = 0

        while current_date <= today:

            day_number += 1

            logger.info("")
            logger.info(
                "[%d/%d] Processing %s",
                day_number,
                total_days,
                current_date,
            )

            try:

                records = process_date(
                    db=db,
                    target_date=current_date,
                )

                if records == 0:
                    skipped_dates += 1

                else:
                    processed_dates += 1
                    total_records += records

                    # Commit after each date.
                    # This prevents one bad date from
                    # destroying successfully imported days.
                    db.commit()

                    logger.info(
                        "✅ %s completed: %d records",
                        current_date,
                        records,
                    )

                current_date += timedelta(
                    days=1
                )

            except Exception as exc:

                db.rollback()

                failed_dates += 1

                logger.exception(
                    "❌ Failed processing %s: %s",
                    current_date,
                    exc,
                )

                # Continue with next date
                current_date += timedelta(
                    days=1
                )

        # -------------------------------------------------
        # Update last_updated for companies
        # -------------------------------------------------

        # This means the database was successfully
        # populated by the backfill process.
        #
        # We deliberately do this at the end instead
        # of pretending that every company was refreshed
        # from CafeF today.

        now = datetime.utcnow()

        db.query(Company).update(
            {
                Company.last_updated: now
            },
            synchronize_session=False,
        )

        db.commit()

    except SQLAlchemyError as exc:

        db.rollback()

        logger.exception(
            "Database error during backfill: %s",
            exc,
        )

        raise

    finally:
        db.close()

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    logger.info("")
    logger.info("=" * 60)
    logger.info("BACKFILL COMPLETED")
    logger.info("=" * 60)

    logger.info(
        "Dates processed : %d",
        processed_dates,
    )

    logger.info(
        "Dates skipped   : %d",
        skipped_dates,
    )

    logger.info(
        "Dates failed    : %d",
        failed_dates,
    )

    logger.info(
        "Total records   : %d",
        total_records,
    )

    logger.info("=" * 60)


if __name__ == "__main__":
    main()