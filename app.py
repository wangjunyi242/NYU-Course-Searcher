"""NYU Course Searcher - Main entry point."""

from __future__ import annotations

import os

# CRITICAL: Set this FIRST to avoid PyTorch+FAISS conflicts
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
from pathlib import Path

import streamlit as st

# Setup paths
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))

from src.constants import APP_DB_PATH, FAISS_INDEX_PATH, COURSE_EMBEDDINGS_PATH
from src.ui.auth import init_session_state, is_authenticated, get_current_user, logout


def render_sidebar() -> None:
	"""Render sidebar with app info, auth, and data status."""
	with st.sidebar:
		st.markdown(
			"""
			<div style="text-align: center; padding: 1rem 0;">
				<h2 style="color: #0066cc; margin: 0;">🎓 NYU Course</h2>
				<h2 style="color: #0066cc; margin: 0;">Searcher</h2>
				<p style="color: #666; font-size: 0.9rem; margin-top: 0.5rem;">Semantic search powered</p>
			</div>
			""",
			unsafe_allow_html=True,
		)
		
		st.divider()
		
		# Auth status
		if is_authenticated():
			user = get_current_user()
			st.success(f"👤 Logged in as **{user['username']}**")
			if st.button("🚪 Logout", use_container_width=True):
				logout()
		else:
			st.info("👋 Please login to access features")
		
		st.divider()
		
		# Navigation
		st.markdown("### 📌 Navigation")
		st.markdown("""
		- **Home** - This page
		- **🔎 Search** - Semantic course search
		- **📚 My Courses** - Your saved courses
		- **⚙️ Admin Data** - System info & stats
		""")
		
		st.divider()
		
		# Data status
		st.markdown("### 📊 Data Status")
		
		db_exists = APP_DB_PATH.exists()
		index_exists = FAISS_INDEX_PATH.exists()
		emb_exists = COURSE_EMBEDDINGS_PATH.exists()
		
		st.markdown(f"{'✅' if db_exists else '❌'} Database")
		st.markdown(f"{'✅' if emb_exists else '❌'} Embeddings")
		st.markdown(f"{'✅' if index_exists else '❌'} FAISS Index")
		
		if not all([db_exists, index_exists, emb_exists]):
			st.warning("⚠️ Some data missing. Run setup scripts.")
		
		st.divider()
		st.caption("Built with 🤖 Nomic Embeddings")


def main():
	st.set_page_config(
		page_title="NYU Course Searcher",
		page_icon="🎓",
		layout="wide",
		initial_sidebar_state="expanded",
	)
	
	init_session_state()
	render_sidebar()
	
	# Main content
	st.title("🎓 Welcome to NYU Course Searcher")
	
	st.markdown(
		"""
		A semantic search engine for NYU courses powered by **nomic-ai embeddings** and **FAISS**.
		
		### 🚀 Getting Started
		
		1. **Login** or create an account using the sidebar
		2. **Search** for courses using natural language queries
		3. **Save** interesting courses to your collection
		4. **Rate** search results with 👍👎 to help improve results
		
		### 📖 Features
		
		- 🔍 **Semantic Search** - Find courses by meaning, not just keywords
		- 💾 **Save Courses** - Build your personal course collection
		- 👍👎 **Feedback** - Rate search quality to track relevance
		- 📊 **Debug Tools** - Inspect search quality and distances
		
		### 📚 Pages
		
		"""
	)
	
	col1, col2, col3 = st.columns(3)
	
	with col1:
		st.markdown(
			"""
			#### 🔎 Search
			Find courses using semantic search. Enter natural language queries like:
			- "machine learning and AI"
			- "creative writing workshops"
			- "data visualization techniques"
			"""
		)
	
	with col2:
		st.markdown(
			"""
			#### 📚 My Courses
			View and manage your saved courses. Add notes and organize your selections.
			"""
		)
	
	with col3:
		st.markdown(
			"""
			#### ⚙️ Admin Data
			View system statistics, database info, and data pipeline status.
			"""
		)
	
	if not is_authenticated():
		st.info("👈 Please login using the sidebar to access all features")
	else:
		st.success("✅ You're logged in! Use the sidebar to navigate.")


if __name__ == "__main__":
	main()
