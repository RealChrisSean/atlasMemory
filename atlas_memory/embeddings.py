from typing import List
from sentence_transformers import SentenceTransformer

_model = SentenceTransformer("all-MiniLM-L6-v2")


def embed(text: str) -> List[float]:
    return _model.encode(text).tolist()
