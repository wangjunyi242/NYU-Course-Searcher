"""Saved courses page."""

from __future__ import annotations

import os

# CRITICAL: Set this FIRST to avoid PyTorch+FAISS conflicts
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
from pathlib import Path

import streamlit as st

# Setup paths
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))

from src.db.repo import list_saved_courses, unsave_course, update_saved_course_note
from src.ui.auth import require_auth, get_current_user
from src.ui.components import inject_course_card_css, render_empty_state, render_search_header


def render_saved_course_card(saved_course: dict, user_id: int) -> None:
	"""Render a card for a saved course with note editing."""
	course_id = saved_course["course_id"]
	code = saved_course.get("course_code", "")
	title = saved_course.get("title", "")
	description = saved_course.get("description", "")
	note = saved_course.get("note", "")
	saved_at = saved_course.get("saved_at", "")
	
	st.markdown('<div class="course-card">', unsafe_allow_html=True)
	
	# Course code
	st.markdown(f'<div class="course-code">{code}</div>', unsafe_allow_html=True)
	
	# Course title
	st.markdown(f'<div class="course-title">{title}</div>', unsafe_allow_html=True)
	
	# Saved date
	st.caption(f"Saved on {saved_at[:10]}")
	
	# Description
	if description:
		desc_preview = description[:150] + "..." if len(description) > 150 else description
		if len(description) > 150:
			st.markdown(f'<div class="course-description">{desc_preview}</div>', unsafe_allow_html=True)
			with st.expander("Read full description"):
				st.write(description)
		else:
			st.markdown(f'<div class="course-description">{description}</div>', unsafe_allow_html=True)
	
	st.divider()
	
	# Notes section
	st.markdown("**Your Notes:**")
	note_key = f"note_{course_id}"
	
	# Initialize session state for this note if not present
	if note_key not in st.session_state:
		st.session_state[note_key] = note
	
	new_note = st.text_area(
		"Add personal notes about this course",
		label_visibility="collapsed",
		value=st.session_state[note_key],
		key=f"note_input_{course_id}",
		placeholder="Add notes here...",
	)
	
	# Action buttons
	col1, col2, col3 = st.columns([2, 2, 4])
	
	with col1:
		if st.button("Update Note", key=f"update_{course_id}"):
			update_saved_course_note(user_id, course_id, new_note)
			st.session_state[note_key] = new_note
			st.success("Note updated!")
			st.rerun()
	
	with col2:
		if st.button("Remove", key=f"remove_{course_id}", type="secondary"):
			unsave_course(user_id, course_id)
			st.success("Course removed!")
			st.rerun()
	
	with col3:
		with st.expander("Details"):
			st.markdown(f"**Subject:** {saved_course.get('subject_slug', 'N/A')}")
			if saved_course.get("source_url"):
				st.markdown(f"[View on NYU Bulletin]({saved_course.get('source_url')})")
	
	st.markdown('</div>', unsafe_allow_html=True)


def main():
	# Require authentication
	if not require_auth():
		st.stop()
	
	inject_course_card_css()
	render_search_header("My Saved Courses")
	
	user = get_current_user()
	user_id = user["id"]
	
	# Load saved courses
	saved_courses = list_saved_courses(user_id)
	
	if not saved_courses:
		render_empty_state("You haven't saved any courses yet", "NOTE")
		st.info("Go to the Search page to find and save courses!")
		return
	
	# Filter section
	col1, col2 = st.columns([3, 1])
	with col1:
		filter_text = st.text_input(
			"Filter courses",
			placeholder="Search by code, title, or notes...",
			label_visibility="collapsed",
		)
	with col2:
		st.metric("Total Saved", len(saved_courses))
	
	# Apply filter
	filtered_courses = saved_courses
	if filter_text:
		filter_lower = filter_text.lower()
		filtered_courses = [
			c for c in saved_courses
			if (
				filter_lower in c.get("course_code", "").lower()
				or filter_lower in c.get("title", "").lower()
				or filter_lower in c.get("note", "").lower()
				or filter_lower in c.get("description", "").lower()
			)
		]
	
	if not filtered_courses:
		render_empty_state(f"No courses match '{filter_text}'", "INFO")
		return
	
	st.markdown(f"### Showing {len(filtered_courses)} course(s)")
	
	# Render saved courses
	for saved_course in filtered_courses:
		render_saved_course_card(saved_course, user_id)


if __name__ == "__main__":
	main()
