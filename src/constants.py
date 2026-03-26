"""Shared constants for the NYU Course Searcher project."""

from __future__ import annotations

from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
SUBJECTS_RAW_DIR = RAW_DIR / "subjects"
PROCESSED_DIR = DATA_DIR / "processed"
APP_DB_DIR = DATA_DIR / "app_db"
APP_DB_PATH = APP_DB_DIR / "app.sqlite3"
LOGS_DIR = ROOT_DIR / "logs"
SCRAPE_SUMMARY_PATH = LOGS_DIR / "scrape_summary.json"

EMBEDDINGS_MODEL_NAME = "nomic-ai/nomic-embed-text-v1.5"
COURSE_EMBEDDINGS_PATH = PROCESSED_DIR / "course_embeddings.npz"
COURSE_EMBEDDINGS_META_PATH = PROCESSED_DIR / "meta.json"

INDEXES_DIR = DATA_DIR / "indexes"
FAISS_INDEX_PATH = INDEXES_DIR / "courses.faiss"

COURSES_INDEX_URL = "https://bulletins.nyu.edu/courses/"
COURSES_INDEX_CACHE_PATH = RAW_DIR / "courses_index.html"
COURSES_SUBJECT_PATH_PATTERN = r"/courses/([^/]+)/$"
COURSE_HEADER_PATTERN = (
    r"^([A-Z0-9&]{2,12}(?:-[A-Z0-9]{1,6})?)\s*"
    r"([0-9]{1,5})\s+(.+?)\s+\((\d+)(?:-\d+)?\s+Credit(?:s)?\)$"
)

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/121.0.0.0 Safari/537.36"
)

REQUEST_TIMEOUT_SECS = 20
THROTTLE_MIN_SECS = 0.5
THROTTLE_MAX_SECS = 1.0
