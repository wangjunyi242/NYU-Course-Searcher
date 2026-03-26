"""CLI wrapper to scrape courses and log results."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import logging
from sqlalchemy import text

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))

from src.db.session import get_engine, init_db
from src.nyu_scraper.scrape_all import scrape_all_courses


def _now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def _count_courses() -> int:
	engine = get_engine()
	with engine.connect() as connection:
		row = connection.execute(text("SELECT COUNT(*) AS count FROM courses")).mappings().one()
		return int(row["count"])


def _write_worklog(summary: dict, total_courses: int) -> None:
	worklog_path = Path(__file__).resolve().parents[1] / "WORKLOG.md"
	line = (
		f"{_now_iso()} scrape_all_courses subjects={summary.get('subjects_processed', 0)} "
		f"failed={summary.get('subjects_failed', 0)} "
		f"parsed={summary.get('courses_parsed', 0)} "
		f"upserted={summary.get('courses_upserted', 0)} "
		f"db_total={total_courses}\n"
	)
	worklog_path.parent.mkdir(parents=True, exist_ok=True)
	with worklog_path.open("a", encoding="utf-8") as handle:
		handle.write(line)


def _parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Scrape all NYU courses")
	parser.add_argument("--force", action="store_true", help="Force re-download of HTML")
	parser.add_argument("--max-subjects", type=int, default=None, help="Limit subjects")
	return parser.parse_args()


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
	args = _parse_args()
	init_db()
	summary = scrape_all_courses(force=args.force, max_subjects=args.max_subjects)
	total_courses = _count_courses()
	print(f"Courses in DB: {total_courses}")
	_write_worklog(summary, total_courses)
