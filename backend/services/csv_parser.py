import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


logger = logging.getLogger(__name__)


# Raw CafeF CSV column names.
REQUIRED_COLUMNS = {
    "<Ticker>",
    "<DTYYYYMMDD>",
    "<Open>",
    "<High>",
    "<Low>",
    "<Close>",
    "<Volume>",
}


def parse_trading_date(value: str) -> datetime:
    return datetime.strptime(value.strip(), "%Y%m%d")

def parse_cafef_csv(
    file_path: Path,
    exchange: str,
) -> List[Dict[str, Any]]:

    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")

    exchange = exchange.strip().upper()

    allowed_exchanges = {"HSX", "HNX", "UPCOM"}

    if exchange not in allowed_exchanges:
        raise ValueError(
            f"Unsupported exchange '{exchange}'. "
            f"Expected one of: {sorted(allowed_exchanges)}"
        )

    records: List[Dict[str, Any]] = []

    with file_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:

        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            raise ValueError(f"CSV file has no header: {file_path}")

        actual_columns = {
            column.strip()
            for column in reader.fieldnames
            if column is not None
        }

        missing_columns = REQUIRED_COLUMNS - actual_columns

        if missing_columns:
            raise ValueError(
                f"Invalid CafeF CSV format: {file_path}. "
                f"Missing columns: {sorted(missing_columns)}"
            )

        for line_number, row in enumerate(reader, start=2):
            try:
                symbol = row["<Ticker>"].strip().upper()
                date_raw = row["<DTYYYYMMDD>"].strip()

                if not symbol:
                    logger.warning(
                        "Skipping row %s in %s: empty ticker",
                        line_number,
                        file_path.name,
                    )
                    continue

                trading_date = parse_trading_date(date_raw)

                open_price = float(row["<Open>"])
                high_price = float(row["<High>"])
                low_price = float(row["<Low>"])
                close_price = float(row["<Close>"])
                volume = int(float(row["<Volume>"]))

                record = {
                    "symbol": symbol,
                    "exchange": exchange,
                    "trading_date": trading_date,
                    "open_price": open_price,
                    "high_price": high_price,
                    "low_price": low_price,
                    "close_price": close_price,
                    "volume": volume,
                }

                records.append(record)

            except (ValueError, TypeError, KeyError) as exc:
                logger.warning(
                    "Skipping invalid row %s in %s: %s",
                    line_number,
                    file_path.name,
                    exc,
                )

    logger.info(
        "Parsed %s records from %s (%s)",
        len(records),
        file_path.name,
        exchange,
    )

    return records


def parse_all_exchange_csvs(
    data_directory: Path,
) -> List[Dict[str, Any]]:
    """
    Parse all three CafeF exchange CSV files from a directory.

    Expected files:
        CafeF.HSX.*.csv
        CafeF.HNX.*.csv
        CafeF.UPCOM.*.csv

    Args:
        data_directory: Directory containing the extracted CSV files.

    Returns:
        A single combined list containing records from HSX, HNX and UPCOM.
    """

    if not data_directory.exists():
        raise FileNotFoundError(
            f"CafeF data directory not found: {data_directory}"
        )

    exchange_patterns = {
        "HSX": "CafeF.HSX.*.csv",
        "HNX": "CafeF.HNX.*.csv",
        "UPCOM": "CafeF.UPCOM.*.csv",
    }

    all_records: List[Dict[str, Any]] = []

    for exchange, pattern in exchange_patterns.items():
        matching_files = sorted(data_directory.glob(pattern))

        if not matching_files:
            logger.warning(
                "No %s CSV file found in %s",
                exchange,
                data_directory,
            )
            continue

        # There should normally be exactly one file per exchange/day.
        # Use the latest matching file if multiple files exist.
        csv_file = matching_files[-1]

        records = parse_cafef_csv(
            file_path=csv_file,
            exchange=exchange,
        )

        all_records.extend(records)

    logger.info(
        "Parsed %s total stock records from %s",
        len(all_records),
        data_directory,
    )

    return all_records

