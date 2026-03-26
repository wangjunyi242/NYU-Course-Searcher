"""Database schema definitions for SQLite."""

from __future__ import annotations

import logging

from sqlalchemy import (
	CheckConstraint,
	Column,
	ForeignKey,
	Index,
	Integer,
	MetaData,
	Table,
	Text,
	UniqueConstraint,
)
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)


def build_metadata() -> MetaData:
	"""Build SQLAlchemy metadata for the application schema."""
	metadata = MetaData()

	Table(
		"courses",
		metadata,
		Column("id", Integer, primary_key=True),
		Column("course_code", Text, nullable=False),
		Column("title", Text, nullable=False),
		Column("description", Text, nullable=False, default=""),
		Column("subject_slug", Text, nullable=False),
		Column("source_url", Text, nullable=False),
		Column("updated_at", Text, nullable=False),
		UniqueConstraint("course_code", "title", "subject_slug", name="uq_courses_identity"),
		Index("idx_courses_course_code", "course_code"),
	)

	Table(
		"users",
		metadata,
		Column("id", Integer, primary_key=True),
		Column("username", Text, nullable=False, unique=True),
		Column("password_hash", Text, nullable=False),
		Column("created_at", Text, nullable=False),
	)

	Table(
		"saved_courses",
		metadata,
		Column("id", Integer, primary_key=True),
		Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
		Column("course_id", Integer, ForeignKey("courses.id"), nullable=False),
		Column("saved_at", Text, nullable=False),
		Column("note", Text, nullable=False, default=""),
	)

	Table(
		"thumbs",
		metadata,
		Column("id", Integer, primary_key=True),
		Column("user_id", Integer, ForeignKey("users.id"), nullable=False),
		Column("course_id", Integer, ForeignKey("courses.id"), nullable=False),
		Column("query", Text, nullable=False),
		Column("thumb", Integer, nullable=False),
		Column("created_at", Text, nullable=False),
		CheckConstraint("thumb IN (1, -1)", name="ck_thumbs_value"),
		Index("idx_thumbs_query", "query"),
	)

	return metadata


def create_schema(engine: Engine) -> None:
	"""Create all tables in the configured database."""
	metadata = build_metadata()
	metadata.create_all(engine)
	logger.info("Database schema ensured.")
