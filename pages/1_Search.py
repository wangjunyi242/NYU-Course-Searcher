"""Semantic course search page."""

from __future__ import annotations

import os

# CRITICAL: Set this FIRST to avoid PyTorch+FAISS conflicts
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
from pathlib import Path

import numpy as np
import streamlit as st

# Setup paths
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))

# CRITICAL ORDER: Import and cache embedding model BEFORE FAISS
from src.embeddings.nomic_embed import embed_texts
from src.constants import COURSE_EMBEDDINGS_PATH, FAISS_INDEX_PATH
from src.db.repo import get_course, save_course, unsave_course, set_thumb, list_saved_courses
from src.ui.auth import require_auth, get_current_user
from src.ui.components import inject_course_card_css, render_course_card, render_empty_state, render_search_header

# Pre-warm embedding model
if "embedding_ready" not in st.session_state:
	with st.spinner("Loading embedding model..."):
		_ = embed_texts(["initialization"])
		st.session_state.embedding_ready = True

# Now safe to import FAISS
import faiss


@st.cache_resource
def load_faiss_index():
	"""Load FAISS index (cached)."""
	if not FAISS_INDEX_PATH.exists():
		st.error(f"FAISS index not found at {FAISS_INDEX_PATH}")
		st.stop()
	return faiss.read_index(str(FAISS_INDEX_PATH))


@st.cache_resource
def load_embeddings_data():
	"""Load embeddings NPZ data (cached)."""
	if not COURSE_EMBEDDINGS_PATH.exists():
		st.error(f"Embeddings not found at {COURSE_EMBEDDINGS_PATH}")
		st.stop()
	data = np.load(COURSE_EMBEDDINGS_PATH)
	return data["ids"], data["embeddings"]


def get_saved_course_ids(user_id: int) -> set[int]:
	"""Get set of saved course IDs for user."""
	saved = list_saved_courses(user_id)
	return {c["course_id"] for c in saved}


def search_courses(query: str, top_k: int = 10) -> tuple[list[int], list[float]]:
	"""Search for courses using semantic search."""
	index = load_faiss_index()
	course_ids, embeddings = load_embeddings_data()
	
	# Embed query
	query_emb = embed_texts([query])
	
	# Search
	distances, indices = index.search(query_emb.astype(np.float32), top_k)
	
	# Map FAISS indices to course IDs
	result_ids = []
	result_dists = []
	for idx, dist in zip(indices[0], distances[0]):
		if idx >= 0 and idx < len(course_ids):
			result_ids.append(int(course_ids[idx]))
			result_dists.append(float(dist))
	
	return result_ids, result_dists, query_emb


def main():
	# Require authentication
	if not require_auth():
		st.stop()
	
	inject_course_card_css()
	render_search_header("Search NYU Courses")
	
	user = get_current_user()
	user_id = user["id"]
	
	# Search input
	col1, col2 = st.columns([3, 1])
	with col1:
		query = st.text_input(
			"Search for courses",
			placeholder="e.g., machine learning, data science, creative writing...",
			label_visibility="collapsed",
		)
	with col2:
		top_k = st.slider("Results", min_value=5, max_value=50, value=10, step=5)
	
	# Search
	if query:
		with st.spinner("Searching..."):
			try:
				result_ids, distances, query_emb = search_courses(query, top_k)
				saved_ids = get_saved_course_ids(user_id)
				thumb_state = st.session_state.setdefault("thumb_state", {})
				
				# Results header
				st.markdown(f"### Found {len(result_ids)} courses")
				
				# Debug panel
				with st.expander("Search Quality Debug"):
					st.markdown("**Query Embedding:**")
					st.write(f"- Norm: {np.linalg.norm(query_emb):.4f}")
					st.write(f"- Shape: {query_emb.shape}")
					st.markdown("**Distances (L2):**")
					for i, (cid, dist) in enumerate(zip(result_ids, distances), 1):
						st.write(f"{i}. Course ID {cid}: {dist:.4f}")
				
				# Render results
				if not result_ids:
					render_empty_state("No courses found for this query", "INFO")
				else:
					for course_id, distance in zip(result_ids, distances):
						course = get_course(course_id)
						if course:
							is_saved = course_id in saved_ids
							
							# Callbacks for actions
							def handle_save(cid):
								save_course(user_id, cid)
								st.rerun()
							
							def handle_unsave(cid):
								unsave_course(user_id, cid)
								st.rerun()
							
							def handle_thumb(cid, thumb_value):
								state_key = f"{user_id}:{query}:{cid}"
								if thumb_value is None:
									thumb_state.pop(state_key, None)
								else:
									set_thumb(user_id, cid, query, thumb_value)
									thumb_state[state_key] = thumb_value
								st.rerun()
							
							state_key = f"{user_id}:{query}:{course_id}"
							current_thumb = thumb_state.get(state_key)
							render_course_card(
								course=course,
								user_id=user_id,
								is_saved=is_saved,
								current_thumb=current_thumb,
								query=query,
								on_save=handle_save,
								on_unsave=handle_unsave,
								on_thumb=handle_thumb,
								show_distance=True,
								distance=distance,
							)
			
			except Exception as e:
				st.error(f"Search error: {e}")
				st.exception(e)
	else:
		st.info("Enter a search query to find relevant courses")


if __name__ == "__main__":
	main()
