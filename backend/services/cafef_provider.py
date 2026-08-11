import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://s.cafef.vn/",
    "Accept": "application/json, text/javascript, */*; q=0.01"
}

def parse_date(date_str: str) -> Optional[datetime]:
    """Parses various date formats from CafeF."""
    formats = ["%d/%m/%Y", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def fetch_stock_history_cafef(symbol: str, page_size: int = 100) -> List[Dict[str, Any]]:
    """
    Fetches historical stock prices for a given symbol from CafeF APIs.
    Returns a normalized list of price dictionaries sorted by date ascending.
    Raises Exception if request fails or data is invalid.
    """
    symbol_upper = symbol.strip().upper()
    
    # Endpoint 1: CafeF DataHistory Ajax API
    url1 = f"https://s.cafef.vn/Ajax/PageNew/DataHistory/PriceHistory.ashx?Symbol={symbol_upper}&PageIndex=1&PageSize={page_size}"
    
    # Endpoint 2: Alternative CafeF API
    url2 = f"https://apipub.cafef.vn/api/data/getlichsugiadieuchinh?symbol={symbol_upper}&page=1&size={page_size}"

    raw_items = []
    
    try:
        response = requests.get(url1, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and data.get("Success") and "Data" in data:
                inner_data = data["Data"]
                if isinstance(inner_data, dict) and "Data" in inner_data:
                    raw_items = inner_data["Data"]
                elif isinstance(inner_data, list):
                    raw_items = inner_data
    except Exception as e:
        logger.warning(f"Endpoint 1 failed for {symbol_upper}: {e}")

    # Fallback to Endpoint 2 if Endpoint 1 yielded no items
    if not raw_items:
        try:
            response = requests.get(url2, headers=HEADERS, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    raw_items = data
                elif isinstance(data, dict) and "data" in data:
                    raw_items = data["data"]
        except Exception as e:
            logger.warning(f"Endpoint 2 failed for {symbol_upper}: {e}")

    if not raw_items:
        raise ValueError(f"Could not retrieve CafeF data for symbol '{symbol_upper}'")

    normalized_data = []
    for item in raw_items:
        # Handle field mappings across different CafeF APIs
        date_raw = item.get("Ngay") or item.get("TradingDate") or item.get("date")
        close_raw = item.get("GiaDongCua") or item.get("GiaDieuChinh") or item.get("close", 0)
        open_raw = item.get("GiaMoCua") or item.get("open", close_raw)
        high_raw = item.get("GiaCaoNhat") or item.get("high", max(close_raw, open_raw))
        low_raw = item.get("GiaThapNhat") or item.get("low", min(close_raw, open_raw))
        vol_raw = item.get("KhoanLuongGiaoDich") or item.get("KhoiLuongGiaoDich") or item.get("volume", 0)

        if not date_raw:
            continue

        parsed_dt = parse_date(str(date_raw))
        if not parsed_dt:
            continue

        try:
            close_price = float(close_raw)
            open_price = float(open_raw)
            high_price = float(high_raw)
            low_price = float(low_raw)
            volume = int(vol_raw)
        except (ValueError, TypeError):
            continue

        normalized_data.append({
            "trading_date": parsed_dt,
            "close_price": close_price,
            "open_price": open_price,
            "high_price": high_price,
            "low_price": low_price,
            "volume": volume
        })

    # Sort by date ascending (oldest to newest)
    normalized_data.sort(key=lambda x: x["trading_date"])
    return normalized_data
