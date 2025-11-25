# atlas_memory/embeddings.py

from typing import List
from sentence_transformers import SentenceTransformer

# MiniLM: 384 dims, runs locally, no API key
_model = SentenceTransformer("all-MiniLM-L6-v2")


def embed(text: str) -> List[float]:
    return _model.encode(text).tolist()
