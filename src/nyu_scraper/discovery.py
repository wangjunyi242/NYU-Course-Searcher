"""Discover NYU course subject pages from the bulletin index."""

from __future__ import annotations

import logging
import random
import re
import time
from typing import Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from src.constants import (
	COURSES_INDEX_CACHE_PATH,
	COURSES_INDEX_URL,
	COURSES_SUBJECT_PATH_PATTERN,
	REQUEST_TIMEOUT_SECS,
	THROTTLE_MAX_SECS,
	THROTTLE_MIN_SECS,
	USER_AGENT,
)

logger = logging.getLogger(__name__)


def _sleep_polite() -> None:
	"""Sleep briefly to avoid hammering the server."""
	delay = random.uniform(THROTTLE_MIN_SECS, THROTTLE_MAX_SECS)
	logger.debug("Polite sleep for %.2fs", delay)
	time.sleep(delay)


def download_courses_index_html(session: requests.Session | None = None) -> str:
	"""Download the NYU courses index HTML."""
	_sleep_polite()
	active_session = session or requests.Session()
	response = active_session.get(
		COURSES_INDEX_URL,
		headers={"User-Agent": USER_AGENT},
		timeout=REQUEST_TIMEOUT_SECS,
	)
	response.raise_for_status()
	return response.text


def load_courses_index_html(*, force: bool = False, session: requests.Session | None = None) -> str:
	"""Load courses index HTML from cache unless forced."""
	if COURSES_INDEX_CACHE_PATH.exists() and not force:
		logger.info("Using cached courses index at %s", COURSES_INDEX_CACHE_PATH)
		return COURSES_INDEX_CACHE_PATH.read_text(encoding="utf-8")

	html = download_courses_index_html(session=session)
	COURSES_INDEX_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
	COURSES_INDEX_CACHE_PATH.write_text(html, encoding="utf-8")
	logger.info("Cached courses index at %s", COURSES_INDEX_CACHE_PATH)
	return html


def _extract_subject_links(html: str) -> Iterable[tuple[str, str]]:
	"""Yield (slug, url) tuples from the courses index HTML."""
	soup = BeautifulSoup(html, "html.parser")
	pattern = re.compile(COURSES_SUBJECT_PATH_PATTERN)

	for link in soup.select("a[href]"):
		href = link.get("href")
		if not href:
			continue
		absolute_url = urljoin(COURSES_INDEX_URL, href)
		path = urlparse(absolute_url).path
		match = pattern.fullmatch(path)
		if not match:
			continue
		slug = match.group(1)
		yield slug, absolute_url


def parse_subjects(html: str) -> list[dict[str, str]]:
	"""Parse unique subject pages from the courses index HTML."""
	subjects: dict[str, str] = {}
	for slug, url in _extract_subject_links(html):
		subjects.setdefault(slug, url)

	return [
		{"slug": slug, "url": url}
		for slug, url in sorted(subjects.items(), key=lambda item: item[0])
	]


def get_subjects(*, force: bool = False, session: requests.Session | None = None) -> list[dict[str, str]]:
	"""Get subject pages with caching and parsing."""
	html = load_courses_index_html(force=force, session=session)
	return parse_subjects(html)


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	subjects_list = get_subjects()
	print(f"Subjects: {len(subjects_list)}")
