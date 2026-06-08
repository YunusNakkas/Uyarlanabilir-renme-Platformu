"""Başarılı web analizlerini StudentsPerformance_Extended.csv dosyasına ekler."""
from __future__ import annotations

import csv
import logging
import threading
from pathlib import Path

from .ml_context import CSV_PATH  # type: ignore

logger = logging.getLogger(__name__)

_CSV_LOCK = threading.Lock()

FIELDNAMES = [
    "math score",
    "physical score",
    "chemical score",
    "study_hours",
    "sleep_hours",
]


def append_analyze_submission(
    project_root: Path,
    ortalamalar: dict[str, int],
    calisma_saat: float,
    uyku_saat: float,
) -> bool:
    """Ortalama notlar + rutinleri CSV'ye yazar (model eğitim formatıyla uyumlu)."""
    path = project_root / CSV_PATH
    if not path.is_file():
        logger.warning("CSV yok, kayıt atlandı: %s", path)
        return False

    row = {
        "math score": int(ortalamalar["mat"]),
        "physical score": int(ortalamalar["fiz"]),
        "chemical score": int(ortalamalar["kim"]),
        "study_hours": round(calisma_saat, 1),  # type: ignore
        "sleep_hours": round(uyku_saat, 1),  # type: ignore
    }

    try:
        with _CSV_LOCK:
            with open(path, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=FIELDNAMES,
                    quoting=csv.QUOTE_MINIMAL,
                )
                writer.writerow(row)
        return True
    except OSError as e:
        logger.warning("CSV'ye yazılamadı: %s", e)
        return False
