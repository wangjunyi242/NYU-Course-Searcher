"""Embedding utilities for course text."""

from __future__ import annotations

import json
import logging
import os
import random
from datetime import datetime, timezone
from typing import Iterable

import numpy as np

from src.constants import (
	COURSE_EMBEDDINGS_META_PATH,
	COURSE_EMBEDDINGS_PATH,
	EMBEDDINGS_MODEL_NAME,
	PROCESSED_DIR,
)

logger = logging.getLogger(__name__)

# Global model cache to avoid reloading
_MODEL_CACHE: dict = {}


def _now_iso() -> str:
	return datetime.now(timezone.utc).isoformat()


def _set_deterministic(seed: int = 42) -> None:
	"""Set random seeds for deterministic embeddings."""
	random.seed(seed)
	np.random.seed(seed)
	try:
		import torch

		torch.manual_seed(seed)
		if torch.cuda.is_available():
			torch.cuda.manual_seed_all(seed)
			torch.backends.cudnn.deterministic = True
			torch.backends.cudnn.benchmark = False
	except Exception:  # noqa: BLE001
		logger.debug("Torch not available for seeding")


def _get_device() -> str:
	"""Return 'cuda' if available, otherwise 'cpu'."""
	try:
		import torch

		return "cuda" if torch.cuda.is_available() else "cpu"
	except Exception:  # noqa: BLE001
		return "cpu"


def _batched(items: list[str], batch_size: int) -> Iterable[list[str]]:
	for idx in range(0, len(items), batch_size):
		yield items[idx : idx + batch_size]


def _progress(iterable: Iterable, total: int) -> Iterable:
	try:
		from tqdm import tqdm

		return tqdm(iterable, total=total)
	except Exception:  # noqa: BLE001
		return iterable


def embed_texts(texts: list[str], batch_size: int = 32) -> np.ndarray:
	"""Embed a list of texts into a float32 array of shape [N, D]."""
	if not texts:
		return np.zeros((0, 0), dtype=np.float32)

	_set_deterministic()
	device = _get_device()

	# Check cache first
	if "model" in _MODEL_CACHE:
		model = _MODEL_CACHE["model"]
		logger.debug("Using cached embedding model")
		if hasattr(model, "encode"):
			embeddings = model.encode(
				texts,
				batch_size=batch_size,
				show_progress_bar=False,
				normalize_embeddings=False,
			)
			return np.asarray(embeddings, dtype=np.float32)

	try:
		from sentence_transformers import SentenceTransformer

		model = SentenceTransformer(
			EMBEDDINGS_MODEL_NAME,
			device=device,
			trust_remote_code=True,
		)
		_MODEL_CACHE["model"] = model
		logger.info("Embedding with sentence-transformers on %s", device)
		embeddings = model.encode(
			texts,
			batch_size=batch_size,
			show_progress_bar=True,
			normalize_embeddings=False,
		)
		return np.asarray(embeddings, dtype=np.float32)
	except Exception as exc:  # noqa: BLE001
		logger.warning("sentence-transformers unavailable, falling back: %s", exc)

	import torch
	from transformers import AutoModel, AutoTokenizer

	logger.info("Embedding with transformers on %s", device)
	model = AutoModel.from_pretrained(EMBEDDINGS_MODEL_NAME, trust_remote_code=True)
	model.to(device)
	model.eval()
	_tokenizer = AutoTokenizer.from_pretrained(EMBEDDINGS_MODEL_NAME, trust_remote_code=True)

	outputs: list[np.ndarray] = []
	for batch in _progress(list(_batched(texts, batch_size)), total=(len(texts) - 1) // batch_size + 1):
		encoded = _tokenizer(
			batch,
			padding=True,
			truncation=True,
			return_tensors="pt",
		)
		encoded = {key: val.to(device) for key, val in encoded.items()}
		with torch.no_grad():
			model_out = model(**encoded)
			last_hidden = model_out.last_hidden_state
			attention_mask = encoded.get("attention_mask")
			mask = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
			summed = torch.sum(last_hidden * mask, dim=1)
			counts = torch.clamp(mask.sum(dim=1), min=1e-9)
			pooled = summed / counts
		outputs.append(pooled.cpu().numpy())

	return np.asarray(np.vstack(outputs), dtype=np.float32)


def save_embeddings(ids: list[int], embeddings: np.ndarray) -> None:
	"""Save embeddings and metadata to the processed data directory."""
	if embeddings.ndim != 2:
		raise ValueError("embeddings must be a 2D array")
	if len(ids) != embeddings.shape[0]:
		raise ValueError("ids must align with embeddings rows")

	PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
	meta = {
		"model": EMBEDDINGS_MODEL_NAME,
		"dim": int(embeddings.shape[1]),
		"count": int(embeddings.shape[0]),
		"created_at": _now_iso(),
		"device": _get_device(),
		"batch_size": None,
	}

	np.savez_compressed(
		COURSE_EMBEDDINGS_PATH,
		ids=np.asarray(ids, dtype=np.int64),
		embeddings=embeddings.astype(np.float32),
		dim=meta["dim"],
	)
	COURSE_EMBEDDINGS_META_PATH.write_text(
		json.dumps(meta, indent=2, ensure_ascii=True),
		encoding="utf-8",
	)
	logger.info("Saved embeddings to %s", COURSE_EMBEDDINGS_PATH)


if __name__ == "__main__":
	logging.basicConfig(level=logging.INFO)
	texts = ["Intro to data science", "Advanced machine learning"]
	emb = embed_texts(texts, batch_size=2)
	print(f"Embeddings shape: {emb.shape}")
