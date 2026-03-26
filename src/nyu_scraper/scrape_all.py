"""Scrape all NYU course subjects and store parsed courses."""

from __future__ import annotations

import argparse
import json
import logging
import random
import time
from datetime import datetime, timezone

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.constants import (
	LOGS_DIR,
	REQUEST_TIMEOUT_SECS,
	SCRAPE_SUMMARY_PATH,
	SUBJECTS_RAW_DIR,
	THROTTLE_MAX_SECS,
	THROTTLE_MIN_SECS,
	USER_AGENT,
)
from src.db.repo import upsert_courses
from src.db.session import init_db
from src.nyu_scraper.discovery import get_subjects
from src.nyu_scraper.parse_subject_page import parse_subject_page

logger = logging.getLogger(__name__)


def _now_iso() -> str:
	"""Return current UTC time as ISO-8601 string."""
	return datetime.now(timezone.utc).isoformat()


def _sleep_polite() -> None:
	"""Sleep briefly to avoid hammering the server."""
	delay = random.uniform(THROTTLE_MIN_SECS, THROTTLE_MAX_SECS)
	logger.debug("Polite sleep for %.2fs", delay)
	time.sleep(delay)


def _fetch_subject_html(
	slug: str,
	url: str,
	*,
	force: bool,
	session: requests.Session,
) -> str:
	"""Fetch or load cached subject HTML."""
	cache_path = SUBJECTS_RAW_DIR / f"{slug}.html"
	if cache_path.exists() and not force:
		logger.debug("Using cached HTML for %s", slug)
		return cache_path.read_text(encoding="utf-8")

	_sleep_polite()
	try:
		response = session.get(
			url,
			headers={"User-Agent": USER_AGENT},
			timeout=(5, 15),
		)
		response.raise_for_status()
	except requests.RequestException as exc:
		logger.warning("Request failed for %s (%s): %s", slug, url, exc)
		raise
	SUBJECTS_RAW_DIR.mkdir(parents=True, exist_ok=True)
	cache_path.write_text(response.text, encoding="utf-8")
	logger.info("Cached subject HTML for %s", slug)
	return response.text


def scrape_all_courses(*, force: bool = False, max_subjects: int | None = None) -> dict:
	"""Scrape all subjects and upsert courses into the database."""
	init_db()
	SUMMARY_FIELDS = {
		"started_at": _now_iso(),
		"finished_at": None,
		"subjects_total": 0,
		"subjects_processed": 0,
		"subjects_failed": 0,
		"courses_parsed": 0,
		"courses_upserted": 0,
		"failures": [],
	}

	session = requests.Session()
	retry = Retry(
		total=4,
		connect=4,
		read=4,
		status=4,
		backoff_factor=0.8,
		status_forcelist=(429, 500, 502, 503, 504),
		allowed_methods=("GET",),
		raise_on_status=False,
	)
	adapter = HTTPAdapter(max_retries=retry)
	session.mount("https://", adapter)
	session.mount("http://", adapter)
	try:
		subjects = get_subjects(force=force, session=session)
		if max_subjects is not None:
			subjects = subjects[:max_subjects]
		SUMMARY_FIELDS["subjects_total"] = len(subjects)

		for subject in subjects:
			slug = subject.get("slug", "")
			url = subject.get("url", "")
			try:
				logger.info("Scraping subject %s", slug)
				html = _fetch_subject_html(slug, url, force=force, session=session)
				courses = parse_subject_page(html, slug, url)
				SUMMARY_FIELDS["courses_parsed"] += len(courses)
				SUMMARY_FIELDS["courses_upserted"] += upsert_courses(courses)
				SUMMARY_FIELDS["subjects_processed"] += 1
			except KeyboardInterrupt:
				logger.warning("Scrape interrupted by user")
				break
			except Exception as exc:  # noqa: BLE001
				logger.exception("Failed to scrape %s", slug)
				SUMMARY_FIELDS["subjects_failed"] += 1
				SUMMARY_FIELDS["failures"].append(
					{"slug": slug, "url": url, "error": str(exc)}
				)
	finally:
		SUMMARY_FIELDS["finished_at"] = _now_iso()
		LOGS_DIR.mkdir(parents=True, exist_ok=True)
		SCRAPE_SUMMARY_PATH.write_text(
			json.dumps(SUMMARY_FIELDS, indent=2, ensure_ascii=True),
			encoding="utf-8",
		)
		logger.info("Wrote scrape summary to %s", SCRAPE_SUMMARY_PATH)
		session.close()

	return SUMMARY_FIELDS


def _parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Scrape NYU course subjects")
	parser.add_argument("--force", action="store_true", help="Force re-download of HTML")
	parser.add_argument("--max-subjects", type=int, default=None, help="Limit subjects")
	return parser.parse_args()


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	args = _parse_args()
	summary = scrape_all_courses(force=args.force, max_subjects=args.max_subjects)
	print(
		f"Subjects: {summary['subjects_processed']} processed, "
		f"{summary['subjects_failed']} failed; "
		f"Courses: {summary['courses_upserted']} upserted."
	)
