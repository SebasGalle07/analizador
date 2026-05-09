import os
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"


def get_configured_data_dir():
    configured = os.getenv("ANALIZADOR_DATA_DIR") or os.getenv("DATA_DIR")
    return Path(configured) if configured else DATA_DIR


def get_configured_processed_dir():
    return get_configured_data_dir() / "processed"


def get_configured_reports_dir():
    configured = os.getenv("ANALIZADOR_REPORTS_DIR") or os.getenv("REPORTS_DIR")
    return Path(configured) if configured else REPORTS_DIR


def get_fallback_processed_dir():
    return Path(tempfile.gettempdir()) / "analizador" / "processed"


def get_fallback_reports_dir():
    return Path(tempfile.gettempdir()) / "analizador" / "reports"


def ensure_writable_dir(preferred, fallback):
    try:
        preferred.mkdir(parents=True, exist_ok=True)
        probe = preferred / ".write_test"
        with probe.open("w", encoding="utf-8") as handle:
            handle.write("ok")
        probe.unlink(missing_ok=True)
        return preferred
    except Exception:
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback


def get_runtime_processed_dir():
    return ensure_writable_dir(get_configured_processed_dir(), get_fallback_processed_dir())


def get_runtime_reports_dir():
    return ensure_writable_dir(get_configured_reports_dir(), get_fallback_reports_dir())
