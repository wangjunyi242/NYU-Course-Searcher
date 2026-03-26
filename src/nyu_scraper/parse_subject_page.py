"""Parse NYU subject pages into structured course records."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from bs4 import BeautifulSoup

from src.constants import COURSE_HEADER_PATTERN, RAW_DIR

logger = logging.getLogger(__name__)


def _normalize_text(text: str) -> str:
	"""Normalize whitespace in scraped text."""
	return " ".join(text.split())


def _parse_course_header(line: str) -> tuple[str, str, int] | None:
	"""Parse a course header line into (course_code, title, credits)."""
	match = re.match(COURSE_HEADER_PATTERN, line)
	if not match:
		return None
	subject, number, title, credits = match.groups()
	course_code = f"{subject} {number}"
	return course_code, _normalize_text(title), int(credits)


def _parse_credits(text: str) -> int:
	"""Extract the first integer credit value from text."""
	match = re.search(r"\d+", text)
	if not match:
		return 0
	return int(match.group(0))


def _parse_structured_blocks(soup: BeautifulSoup) -> list[dict[str, object]]:
	"""Parse course blocks when structured markup is present."""
	courses: list[dict[str, object]] = []
	blocks = soup.select(".courseblock")
	if not blocks:
		return courses

	for block in blocks:
		code_el = block.select_one(".detail-code")
		title_el = block.select_one(".detail-title")
		credits_el = block.select_one(".detail-hours_html")
		desc_el = block.select_one(".courseblockextra")

		code_text = _normalize_text(code_el.get_text(" ", strip=True)) if code_el else ""
		title_text = _normalize_text(title_el.get_text(" ", strip=True)) if title_el else ""
		credits_text = _normalize_text(credits_el.get_text(" ", strip=True)) if credits_el else ""

		if not code_text or not title_text or not credits_text:
			title_fallback = _normalize_text(
				block.select_one(".courseblocktitle").get_text(" ", strip=True)
			) if block.select_one(".courseblocktitle") else ""
			header = _parse_course_header(title_fallback)
			if not header:
				continue
			course_code, title, credits = header
		else:
			course_code = code_text
			title = title_text
			credits = _parse_credits(credits_text)

		description = ""
		if desc_el:
			description = _normalize_text(desc_el.get_text(" ", strip=True))

		courses.append(
			{
				"course_code": course_code,
				"title": title,
				"credits": credits,
				"description": description,
			}
		)

	return courses


def _parse_text_fallback(soup: BeautifulSoup) -> list[dict[str, object]]:
	"""Fallback parsing using line-by-line text heuristics."""
	courses: list[dict[str, object]] = []
	lines = [line.strip() for line in soup.get_text("\n").splitlines()]
	lines = [line for line in lines if line]

	current: dict[str, object] | None = None
	description_lines: list[str] = []

	for line in lines:
		header = _parse_course_header(line)
		if header:
			if current:
				current["description"] = _normalize_text(" ".join(description_lines))
				courses.append(current)
			course_code, title, credits = header
			current = {
				"course_code": course_code,
				"title": title,
				"credits": credits,
				"description": "",
			}
			description_lines = []
			continue

		if current:
			description_lines.append(line)

	if current:
		current["description"] = _normalize_text(" ".join(description_lines))
		courses.append(current)

	return courses


def parse_subject_page(html: str, subject_slug: str, source_url: str) -> list[dict]:
	"""Parse a subject HTML page into course records."""
	soup = BeautifulSoup(html, "html.parser")

	courses = _parse_structured_blocks(soup)
	if not courses:
		logger.info("Structured parsing failed, falling back to text parsing for %s", subject_slug)
		courses = _parse_text_fallback(soup)

	for course in courses:
		course["subject_slug"] = subject_slug
		course["source_url"] = source_url

	return courses


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	candidates = [
		path
		for path in sorted(RAW_DIR.glob("*.html"))
		if path.name != "courses_index.html"
	]
	if not candidates:
		print("No sample subject HTML found in data/raw")
	else:
		sample_path = candidates[0]
		sample_html = sample_path.read_text(encoding="utf-8")
		slug = sample_path.stem
		results = parse_subject_page(sample_html, slug, sample_path.as_uri())
		print(f"Parsed {len(results)} courses from {sample_path.name}")
