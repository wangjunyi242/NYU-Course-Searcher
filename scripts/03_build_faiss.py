"""Build FAISS index from course embeddings."""

from __future__ import annotations

import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
	sys.path.insert(0, str(ROOT_DIR))

from src.constants import COURSE_EMBEDDINGS_PATH, FAISS_INDEX_PATH
from src.retrieval.faiss_index import build_faiss_l2, load_index, save_index, search


def _now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def _write_worklog(count: int, dim: int, elapsed: float) -> None:
	worklog_path = ROOT_DIR / "WORKLOG.md"
	line = (
		f"{_now_iso()} build_faiss count={count} dim={dim} "
		f"elapsed_sec={elapsed:.1f}\n"
	)
	with worklog_path.open("a", encoding="utf-8") as handle:
		handle.write(line)


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

	if not COURSE_EMBEDDINGS_PATH.exists():
		logging.error("Embeddings file not found at %s", COURSE_EMBEDDINGS_PATH)
		sys.exit(1)

	start = time.time()

	# Load embeddings
	logging.info("Loading embeddings from %s", COURSE_EMBEDDINGS_PATH)
	data = np.load(COURSE_EMBEDDINGS_PATH)
	ids = data["ids"]
	embeddings = data["embeddings"]
	logging.info("Loaded %d embeddings with dim=%d", len(ids), embeddings.shape[1])

	# Build index
	index = build_faiss_l2(embeddings)

	# Save index
	save_index(index)

	# Reload to verify
	logging.info("Reloading index to verify...")
	reloaded_index = load_index()

	# Sanity test: search with a random embedding
	test_idx = len(embeddings) // 2
	test_embedding = embeddings[test_idx]
	result_ids, result_dists = search(reloaded_index, test_embedding, ids, top_k=1)

	logging.info(
		"Sanity test: query vector index=%d (ID=%d), nearest neighbor ID=%d, distance=%.6f",
		test_idx,
		ids[test_idx],
		result_ids[0],
		result_dists[0],
	)

	if result_ids[0] == ids[test_idx] and result_dists[0] < 1e-5:
		logging.info("✓ Sanity test passed: nearest neighbor is itself")
	else:
		logging.warning("✗ Sanity test failed")

	elapsed = time.time() - start
	_write_worklog(len(ids), embeddings.shape[1], elapsed)

	print(f"Built FAISS index: {len(ids)} vectors, dim={embeddings.shape[1]}")
	print(f"Saved to: {FAISS_INDEX_PATH}")
	print(f"Elapsed: {elapsed:.1f}s")
