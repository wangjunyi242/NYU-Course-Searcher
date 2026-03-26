"""Reusable UI components for the course search app."""

from __future__ import annotations

import streamlit as st


def inject_course_card_css() -> None:
	"""Inject CSS for course card styling."""
	st.markdown(
		"""
		<style>
		div[data-testid="stVerticalBlock"]:has(.course-card-marker) {
			background: #ffffff;
			padding: 1.5rem;
			border-radius: 12px;
			border: 1px solid #e6e6e6;
			margin-bottom: 1.25rem;
			box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
			transition: box-shadow 0.2s ease;
		}
		div[data-testid="stVerticalBlock"]:has(.course-card-marker):hover {
			box-shadow: 0 6px 16px rgba(0, 0, 0, 0.1);
		}
		.course-card-marker {
			display: none;
		}
		.course-code {
			color: #0066cc;
			font-weight: 600;
			font-size: 0.9rem;
			margin-bottom: 0.5rem;
		}
		.course-title {
			font-size: 1.3rem;
			font-weight: 600;
			color: #1a1a1a;
			margin-bottom: 0.75rem;
			line-height: 1.4;
		}
		.course-description {
			color: #4a4a4a;
			font-size: 0.95rem;
			line-height: 1.6;
			margin-bottom: 1rem;
		}
		.course-actions {
			display: flex;
			gap: 0.5rem;
			align-items: center;
			margin-top: 1rem;
		}
		.stButton button {
			font-size: 0.88rem;
			font-weight: 600;
			padding: 0.45rem 1rem;
			border-radius: 999px;
			border: 1px solid #d2d6dc;
			background: #f8f9fb;
			color: #1f2937;
			box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
			transition: transform 0.06s ease, box-shadow 0.12s ease, background 0.12s ease,
				border-color 0.12s ease;
		}
		.stButton button:hover {
			background: #eef2f7;
			box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
			transform: translateY(-1px);
			border-color: #c3c9d4;
		}
		.stButton button[kind="primary"] {
			background: #1a73e8;
			border-color: #1a73e8;
			color: #ffffff;
			box-shadow: 0 0 0 2px rgba(26, 115, 232, 0.18), 0 6px 14px rgba(26, 115, 232, 0.25);
		}
		.stButton button[kind="primary"]:hover {
			background: #155bb8;
			border-color: #155bb8;
			box-shadow: 0 0 0 2px rgba(21, 91, 184, 0.2), 0 8px 18px rgba(21, 91, 184, 0.3);
		}
		</style>
		""",
		unsafe_allow_html=True,
	)


def render_course_card(
	course: dict,
	user_id: int | None = None,
	is_saved: bool = False,
	current_thumb: int | None = None,
	query: str = "",
	on_save: callable | None = None,
	on_unsave: callable | None = None,
	on_thumb: callable | None = None,
	show_distance: bool = False,
	distance: float | None = None,
) -> None:
	"""
	Render a modern course card with actions.
	
	Args:
		course: Course dict with id, course_code, title, description
		user_id: Current user ID (required for save/thumb actions)
		is_saved: Whether this course is saved by the user
		current_thumb: Current thumb value (+1, -1, or None)
		query: Search query for thumb association
		on_save: Callback when save button clicked
		on_unsave: Callback when unsave button clicked
		on_thumb: Callback when thumb button clicked, receives (course_id, thumb_value)
		show_distance: Whether to show distance/score
		distance: L2 distance or search score
	"""
	course_id = course.get("id")
	code = course.get("course_code", "")
	title = course.get("title", "")
	description = course.get("description", "")
	
	with st.container():
		st.markdown('<div class="course-card-marker"></div>', unsafe_allow_html=True)

		# Course code
		st.markdown(f'<div class="course-code">{code}</div>', unsafe_allow_html=True)

		# Course title
		st.markdown(f'<div class="course-title">{title}</div>', unsafe_allow_html=True)

		# Distance/score if applicable
		if show_distance and distance is not None:
			st.caption(f"Relevance score: {distance:.2f}")

		# Full description
		if description:
			st.markdown(f'<div class="course-description">{description}</div>', unsafe_allow_html=True)

		# Action buttons
		col1, col2, col3, col4 = st.columns([2, 1, 1, 2])

		with col1:
			if user_id:
				if is_saved:
					if st.button("💾 Unsave", key=f"unsave_{course_id}", type="secondary"):
						if on_unsave:
							on_unsave(course_id)
				else:
					if st.button("📌 Save", key=f"save_{course_id}", type="primary"):
						if on_save:
							on_save(course_id)

		with col2:
			if user_id and on_thumb:
				thumb_up_type = "primary" if current_thumb == 1 else "secondary"
				if st.button("👍", key=f"thumb_up_{course_id}", type=thumb_up_type):
					new_thumb = 1 if current_thumb != 1 else None
					on_thumb(course_id, new_thumb)

		with col3:
			if user_id and on_thumb:
				thumb_down_type = "primary" if current_thumb == -1 else "secondary"
				if st.button("👎", key=f"thumb_down_{course_id}", type=thumb_down_type):
					new_thumb = -1 if current_thumb != -1 else None
					on_thumb(course_id, new_thumb)

		with col4:
			subject_slug = course.get("subject_slug", "N/A")
			source_url = course.get("source_url")
			details_parts = [f"Subject: {subject_slug}"]
			if source_url:
				details_parts.append(f"[NYU Bulletin]({source_url})")
			st.markdown(" | ".join(details_parts))


def render_empty_state(message: str = "No courses found", icon: str = "INFO") -> None:
	"""Render an empty state message."""
	st.markdown(
		f"""
		<div style="text-align: center; padding: 4rem 2rem; color: #666;">
			<div style="font-size: 4rem; margin-bottom: 1rem;">{icon}</div>
			<div style="font-size: 1.2rem;">{message}</div>
		</div>
		""",
		unsafe_allow_html=True,
	)


def render_search_header(title: str = "Search NYU Courses") -> None:
	"""Render a styled page header."""
	st.markdown(
		f"""
		<div style="margin-bottom: 2rem;">
			<h1 style="color: #1a1a1a; margin-bottom: 0.5rem;">{title}</h1>
			<div style="height: 3px; width: 60px; background: #0066cc; border-radius: 2px;"></div>
		</div>
		""",
		unsafe_allow_html=True,
	)
