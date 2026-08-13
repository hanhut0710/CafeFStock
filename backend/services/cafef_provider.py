import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from services.cafef_downloader import download_and_extract_cafef
from services.csv_parser import parse_all_exchange_csvs
# from services.stock_service import find_latest_date_available


logger = logging.getLogger(__name__)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_ROOT = PROJECT_ROOT / "data" / "cafef"



def fetch_cafef_daily_data(
    target_date: date,
) -> List[Dict[str, Any]]:

    logger.info(
        "Fetching CafeF daily data for %s",
        target_date,
    )

    data_directory = download_and_extract_cafef(
        target_date=target_date,
        data_root=DATA_ROOT,
    )

    records = parse_all_exchange_csvs(
        data_directory,
    )

    logger.info(
        "Fetched %s CafeF records for %s",
        len(records),
        target_date,
    )

    return records

