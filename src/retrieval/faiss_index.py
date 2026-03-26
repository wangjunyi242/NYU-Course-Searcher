"""FAISS index utilities for semantic course search."""

from __future__ import annotations

import logging
from pathlib import Path

import faiss
import numpy as np

from src.constants import FAISS_INDEX_PATH, INDEXES_DIR

logger = logging.getLogger(__name__)


def build_faiss_l2(embeddings: np.ndarray) -> faiss.Index:
	"""Build a FAISS L2 index from embeddings."""
	if embeddings.ndim != 2:
		raise ValueError("embeddings must be a 2D array")

	dim = embeddings.shape[1]
	index = faiss.IndexFlatL2(dim)
	index.add(embeddings.astype(np.float32))
	logger.info("Built FAISS L2 index with %d vectors, dim=%d", index.ntotal, dim)
	return index


def save_index(index: faiss.Index, path: Path | None = None) -> None:
	"""Save FAISS index to disk."""
	index_path = path or FAISS_INDEX_PATH
	index_path.parent.mkdir(parents=True, exist_ok=True)
	faiss.write_index(index, str(index_path))
	logger.info("Saved FAISS index to %s", index_path)


def load_index(path: Path | None = None) -> faiss.Index:
	"""Load FAISS index from disk."""
	index_path = path or FAISS_INDEX_PATH
	if not index_path.exists():
		raise FileNotFoundError(f"Index not found at {index_path}")
	index = faiss.read_index(str(index_path))
	logger.info("Loaded FAISS index from %s (ntotal=%d)", index_path, index.ntotal)
	return index


def search(
	index: faiss.Index,
	query_embedding: np.ndarray,
	course_ids: np.ndarray,
	top_k: int = 10,
) -> tuple[list[int], list[float]]:
	"""Search the index and return (course_ids, distances)."""
	if query_embedding.ndim == 1:
		query_embedding = query_embedding.reshape(1, -1)

	distances, indices = index.search(query_embedding.astype(np.float32), top_k)
	distances = distances[0]
	indices = indices[0]

	result_ids = [int(course_ids[idx]) for idx in indices if idx < len(course_ids)]
	result_dists = [float(d) for d in distances[: len(result_ids)]]

	return result_ids, result_dists


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)

	# Self-test: build a tiny index and ensure nearest neighbor is itself
	test_embeddings = np.random.randn(5, 128).astype(np.float32)
	test_ids = np.array([10, 20, 30, 40, 50], dtype=np.int64)

	index = build_faiss_l2(test_embeddings)
	result_ids, result_dists = search(index, test_embeddings[2], test_ids, top_k=1)

	print(f"Query vector index: 2 (ID={test_ids[2]})")
	print(f"Nearest neighbor: ID={result_ids[0]}, distance={result_dists[0]:.6f}")

	if result_ids[0] == test_ids[2] and result_dists[0] < 1e-5:
		print("✓ Self-test passed: nearest neighbor is itself")
	else:
		print("✗ Self-test failed")
