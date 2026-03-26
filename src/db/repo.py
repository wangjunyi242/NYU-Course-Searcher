"""Repository functions for data access."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Iterable

import bcrypt
from sqlalchemy import text

from src.db.session import get_engine

logger = logging.getLogger(__name__)


def _now_iso() -> str:
	"""Return current UTC time as ISO-8601 string."""
	return datetime.now(timezone.utc).isoformat()


def upsert_courses(courses: Iterable[dict]) -> int:
	"""Insert or update courses using the unique identity constraint."""
	rows = list(courses)
	if not rows:
		return 0

	sql = text(
		"""
		INSERT INTO courses (
			course_code, title, description, subject_slug, source_url, updated_at
		)
		VALUES (
			:course_code, :title, :description, :subject_slug, :source_url, :updated_at
		)
		ON CONFLICT(course_code, title, subject_slug) DO UPDATE SET
			description = excluded.description,
			source_url = excluded.source_url,
			updated_at = excluded.updated_at
		"""
	)

	now = _now_iso()
	payload = []
	for course in rows:
		payload.append(
			{
				"course_code": course.get("course_code", ""),
				"title": course.get("title", ""),
				"description": course.get("description", ""),
				"subject_slug": course.get("subject_slug", ""),
				"source_url": course.get("source_url", ""),
				"updated_at": course.get("updated_at", now),
			}
		)

	engine = get_engine()
	with engine.begin() as connection:
		connection.execute(sql, payload)
	logger.info("Upserted %s course rows", len(payload))
	return len(payload)


def list_courses(limit: int = 50, offset: int = 0) -> list[dict]:
	"""List courses with pagination."""
	sql = text(
		"""
		SELECT id, course_code, title, description, subject_slug, source_url, updated_at
		FROM courses
		ORDER BY course_code, title
		LIMIT :limit OFFSET :offset
		"""
	)
	engine = get_engine()
	with engine.connect() as connection:
		result = connection.execute(sql, {"limit": limit, "offset": offset})
		return [dict(row._mapping) for row in result]


def list_all_courses(limit: int | None = None) -> list[dict]:
	"""List all courses for embedding without pagination."""
	sql = text(
		"""
		SELECT id, course_code, title, description, subject_slug, source_url, updated_at
		FROM courses
		ORDER BY id
		"""
	)
	if limit is not None:
		sql = text(
			"""
			SELECT id, course_code, title, description, subject_slug, source_url, updated_at
			FROM courses
			ORDER BY id
			LIMIT :limit
			"""
		)
	engine = get_engine()
	with engine.connect() as connection:
		if limit is None:
			result = connection.execute(sql)
		else:
			result = connection.execute(sql, {"limit": limit})
		return [dict(row._mapping) for row in result]


def get_course(course_id: int) -> dict | None:
	"""Fetch a single course by id."""
	sql = text(
		"""
		SELECT id, course_code, title, description, subject_slug, source_url, updated_at
		FROM courses
		WHERE id = :course_id
		"""
	)
	engine = get_engine()
	with engine.connect() as connection:
		row = connection.execute(sql, {"course_id": course_id}).mappings().first()
		return dict(row) if row else None


def create_user(username: str, password_plain: str) -> int:
	"""Create a new user and return the new id."""
	password_hash = bcrypt.hashpw(password_plain.encode("utf-8"), bcrypt.gensalt()).decode(
		"utf-8"
	)
	sql = text(
		"""
		INSERT INTO users (username, password_hash, created_at)
		VALUES (:username, :password_hash, :created_at)
		"""
	)
	engine = get_engine()
	with engine.begin() as connection:
		result = connection.execute(
			sql,
			{
				"username": username,
				"password_hash": password_hash,
				"created_at": _now_iso(),
			},
		)
		return int(result.lastrowid)


def verify_user(username: str, password_plain: str) -> dict | None:
	"""Verify username/password, returning user row if valid."""
	sql = text("SELECT id, username, password_hash, created_at FROM users WHERE username = :username")
	engine = get_engine()
	with engine.connect() as connection:
		row = connection.execute(sql, {"username": username}).mappings().first()
		if not row:
			return None
		if bcrypt.checkpw(password_plain.encode("utf-8"), row["password_hash"].encode("utf-8")):
			return {"id": row["id"], "username": row["username"], "created_at": row["created_at"]}
	return None


def save_course(user_id: int, course_id: int, note: str = "") -> int:
	"""Save a course for a user."""
	sql = text(
		"""
		INSERT INTO saved_courses (user_id, course_id, saved_at, note)
		VALUES (:user_id, :course_id, :saved_at, :note)
		"""
	)
	engine = get_engine()
	with engine.begin() as connection:
		result = connection.execute(
			sql,
			{
				"user_id": user_id,
				"course_id": course_id,
				"saved_at": _now_iso(),
				"note": note,
			},
		)
		return int(result.lastrowid)


def unsave_course(user_id: int, course_id: int) -> int:
	"""Remove a saved course for a user."""
	sql = text(
		"""
		DELETE FROM saved_courses
		WHERE user_id = :user_id AND course_id = :course_id
		"""
	)
	engine = get_engine()
	with engine.begin() as connection:
		result = connection.execute(sql, {"user_id": user_id, "course_id": course_id})
		return int(result.rowcount)


def update_saved_course_note(user_id: int, course_id: int, note: str) -> int:
	"""Update the note for a saved course."""
	sql = text(
		"""
		UPDATE saved_courses
		SET note = :note
		WHERE user_id = :user_id AND course_id = :course_id
		"""
	)
	engine = get_engine()
	with engine.begin() as connection:
		result = connection.execute(sql, {"user_id": user_id, "course_id": course_id, "note": note})
		return int(result.rowcount)


def list_saved_courses(user_id: int) -> list[dict]:
	"""List saved courses for a user."""
	sql = text(
		"""
		SELECT sc.id AS saved_id, sc.saved_at, sc.note,
			   c.id AS course_id, c.course_code, c.title, c.description,
			   c.subject_slug, c.source_url, c.updated_at
		FROM saved_courses sc
		JOIN courses c ON c.id = sc.course_id
		WHERE sc.user_id = :user_id
		ORDER BY sc.saved_at DESC
		"""
	)
	engine = get_engine()
	with engine.connect() as connection:
		result = connection.execute(sql, {"user_id": user_id})
		return [dict(row._mapping) for row in result]


def set_thumb(user_id: int, course_id: int, query: str, thumb: int) -> int:
	"""Upsert a thumb value per user+course+query."""
	if thumb not in (1, -1):
		raise ValueError("thumb must be 1 or -1")

	delete_sql = text(
		"""
		DELETE FROM thumbs
		WHERE user_id = :user_id AND course_id = :course_id AND query = :query
		"""
	)
	insert_sql = text(
		"""
		INSERT INTO thumbs (user_id, course_id, query, thumb, created_at)
		VALUES (:user_id, :course_id, :query, :thumb, :created_at)
		"""
	)
	engine = get_engine()
	with engine.begin() as connection:
		connection.execute(
			delete_sql,
			{"user_id": user_id, "course_id": course_id, "query": query},
		)
		result = connection.execute(
			insert_sql,
			{
				"user_id": user_id,
				"course_id": course_id,
				"query": query,
				"thumb": thumb,
				"created_at": _now_iso(),
			},
		)
		return int(result.lastrowid)
