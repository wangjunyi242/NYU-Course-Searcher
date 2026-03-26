"""
Script 04: End-to-end test of the search pipeline.
"""
import os
# --- THE FIX: THIS MUST BE THE VERY FIRST LINE ---
# This allows PyTorch and FAISS to coexist on macOS without crashing.
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import sys
import logging
import numpy as np
import sqlite3
from pathlib import Path

# Setup paths
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Configure logging FIRST
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

# Imports - CRITICAL ORDER: Load embedding model BEFORE FAISS
from src.embeddings.nomic_embed import embed_texts
from src.constants import APP_DB_PATH

# Pre-warm the embedding model to avoid PyTorch+FAISS conflicts
logger.info("Pre-loading embedding model...")
_ = embed_texts(["test"])  # Force model load
logger.info("Model ready.")

# Now safe to import FAISS
import faiss

def main():
    # 1. Load the FAISS Index
    index_path = ROOT_DIR / "data" / "indexes" / "courses.faiss"
    logger.info(f"Loading index from {index_path}...")
    index = faiss.read_index(str(index_path))
    
    # 2. Connect to DB
    conn = sqlite3.connect(APP_DB_PATH)
    cursor = conn.cursor()

    # 3. Define a test query
    query_text = "machine learning and neural networks"
    logger.info(f"\nQuery: '{query_text}'")

    # 4. Embed the query (model already loaded)
    logger.info("Embedding query...")
    query_emb = embed_texts([query_text]) 
    
    # 5. Search FAISS
    k = 5
    logger.info(f"Searching for top {k} matches...")
    distances, indices = index.search(query_emb, k)
    
    # 6. Map results to Course Names
    data = np.load(ROOT_DIR / "data" / "processed" / "course_embeddings.npz")
    db_ids = data['ids'] 
    
    print("\n--- RESULTS ---")
    for i, idx_in_faiss in enumerate(indices[0]):
        if idx_in_faiss == -1: continue 
        
        real_db_id = db_ids[idx_in_faiss]
        score = distances[0][i]
        
        # Fetch details
        cursor.execute("SELECT course_code, title FROM courses WHERE id = ?", (int(real_db_id),))
        row = cursor.fetchone()
        
        if row:
            # Score is L2 distance (lower is better)
            print(f"[Dist {score:.2f}] {row[0]}: {row[1]}")

    conn.close()

if __name__ == "__main__":
    main()