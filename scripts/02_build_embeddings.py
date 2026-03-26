"""Build embeddings for all courses in the database."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))

from src.constants import EMBEDDINGS_MODEL_NAME
from src.db.repo import list_all_courses
from src.embeddings.nomic_embed import embed_texts, save_embeddings


def _now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def _build_text(course: dict) -> str:
	"""Build embedding input from course fields."""
	code = course.get("course_code", "")
	title = course.get("title", "")
	description = course.get("description", "")
	return f"{code}: {title}. {description}".strip()


def _write_worklog(count: int, dim: int, elapsed: float) -> None:
	worklog_path = ROOT_DIR / "WORKLOG.md"
	line = (
		f"{_now_iso()} build_embeddings count={count} dim={dim} "
		f"model={EMBEDDINGS_MODEL_NAME} elapsed_sec={elapsed:.1f}\n"
	)
	with worklog_path.open("a", encoding="utf-8") as handle:
		handle.write(line)


def _parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Build course embeddings")
	parser.add_argument("--limit", type=int, default=None, help="Limit courses for testing")
	parser.add_argument("--batch-size", type=int, default=32, help="Embedding batch size")
	return parser.parse_args()


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
	args = _parse_args()

	start = time.time()
	courses = list_all_courses(limit=args.limit)
	logging.info("Loaded %d courses from database", len(courses))

	if not courses:
		logging.warning("No courses found, exiting")
		sys.exit(0)

	ids = [course["id"] for course in courses]
	texts = [_build_text(course) for course in courses]

	embeddings = embed_texts(texts, batch_size=args.batch_size)
	save_embeddings(ids, embeddings)

	elapsed = time.time() - start
	_write_worklog(len(ids), embeddings.shape[1], elapsed)

	print(f"Embedded {len(ids)} courses → {embeddings.shape}")
	print(f"Elapsed: {elapsed:.1f}s")
