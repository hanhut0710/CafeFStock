import logging
from datetime import date
from pathlib import Path
from zipfile import ZipFile

import requests


logger = logging.getLogger(__name__)


CAFEF_BASE_URL = "http://cafef1.mediacdn.vn/data/ami_data"


def build_cafef_zip_url(target_date: date) -> str:

    date_str = target_date.strftime("%Y%m%d")
    date_str_2 = target_date.strftime("%d%m%Y")

    return (
        f"{CAFEF_BASE_URL}/{date_str}/"
        f"CafeF.SolieuGD.{date_str_2}.zip"
    )


def download_cafef_zip(
    target_date: date,
    data_root: Path,
    timeout: int = 30,
) -> Path:

    date_str = target_date.strftime("%Y%m%d")

    output_directory = data_root / date_str
    output_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    zip_path = (
        output_directory
        / f"CafeF.SolieuGD.{date_str}.zip"
    )

    # Avoid downloading the same file again.
    if zip_path.exists() and zip_path.stat().st_size > 0:
        logger.info(
            "CafeF ZIP already exists: %s",
            zip_path,
        )
        return zip_path

    url = build_cafef_zip_url(target_date)

    logger.info(
        "Downloading CafeF data: %s",
        url,
    )

    response = requests.get(
        url,
        timeout=timeout,
    )

    response.raise_for_status()

    zip_path.write_bytes(response.content)

    logger.info(
        "CafeF ZIP downloaded successfully: %s",
        zip_path,
    )

    return zip_path


def extract_cafef_zip(zip_path: Path) -> Path:

    if not zip_path.exists():
        raise FileNotFoundError(
            f"CafeF ZIP file not found: {zip_path}"
        )

    output_directory = zip_path.parent

    try:
        with ZipFile(zip_path, "r") as zip_file:
            zip_file.extractall(output_directory)

    except Exception as exc:
        raise ValueError(
            f"Failed to extract CafeF ZIP: {zip_path}"
        ) from exc

    logger.info(
        "CafeF ZIP extracted successfully: %s",
        output_directory,
    )

    return output_directory


def download_and_extract_cafef(
    target_date: date,
    data_root: Path,
    timeout: int = 30,
) -> Path:

    zip_path = download_cafef_zip(
        target_date=target_date,
        data_root=data_root,
        timeout=timeout,
    )

    return extract_cafef_zip(zip_path)
