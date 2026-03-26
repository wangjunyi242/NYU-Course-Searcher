"""Database engine and session helpers."""

from __future__ import annotations

import logging

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from src.constants import APP_DB_DIR, APP_DB_PATH
from src.db.schema import create_schema

logger = logging.getLogger(__name__)


def get_engine() -> Engine:
	"""Create or return a SQLite engine for the app database."""
	APP_DB_DIR.mkdir(parents=True, exist_ok=True)
	return create_engine(
		f"sqlite:///{APP_DB_PATH}",
		future=True,
		connect_args={"check_same_thread": False},
	)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def init_db() -> None:
	"""Initialize database schema if missing."""
	engine = get_engine()
	create_schema(engine)
	logger.info("Database initialized at %s", APP_DB_PATH)
