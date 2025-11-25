# atlas_memory/memory.py

from typing import Optional, List, Dict
from sqlalchemy import text

from atlas_memory.db import get_session
from atlas_memory.schema import Memory
from atlas_memory.embeddings import embed


def add_memory(
    user_id: str,
    content: str,
    metadata: Optional[dict] = None,
    branch: str = "main"
) -> int:
    vector = embed(content)

    with get_session() as db:
        memory = Memory(
            user_id=user_id,
            text=content,
            metadata_json=metadata,
            embedding=vector,
            branch=branch
        )
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return memory.id


def search_memory(
    user_id: str,
    query: str,
    top_k: int = 5,
    branch: str = "main",
    mode: str = "hybrid"
) -> List[Dict]:
    query_vector = embed(query)

    with get_session() as db:
        if mode == "vector":
            return _vector_search(db, user_id, query_vector, top_k, branch)
        elif mode == "fulltext":
            return _fulltext_search(db, user_id, query, top_k, branch)
        else:
            return _hybrid_search(db, user_id, query, query_vector, top_k, branch)


def _vector_search(db, user_id: str, query_vector: list, top_k: int, branch: str) -> List[Dict]:
    sql = text("""
        SELECT id, text, metadata_json,
               vec_cosine_distance(embedding, :query_vec) as distance
        FROM memories
        WHERE user_id = :user_id AND branch = :branch
        ORDER BY distance ASC
        LIMIT :top_k
    """)

    results = db.execute(sql, {
        "query_vec": str(query_vector),
        "user_id": user_id,
        "branch": branch,
        "top_k": top_k
    }).fetchall()

    return [
        {"id": r.id, "text": r.text, "metadata": r.metadata_json, "score": 1 - r.distance}
        for r in results
    ]


def _fulltext_search(db, user_id: str, query: str, top_k: int, branch: str) -> List[Dict]:
    sql = text("""
        SELECT id, text, metadata_json
        FROM memories
        WHERE user_id = :user_id AND branch = :branch AND text LIKE :pattern
        LIMIT :top_k
    """)

    results = db.execute(sql, {
        "user_id": user_id,
        "branch": branch,
        "pattern": f"%{query}%",
        "top_k": top_k
    }).fetchall()

    return [
        {"id": r.id, "text": r.text, "metadata": r.metadata_json, "score": 1.0}
        for r in results
    ]


def _hybrid_search(db, user_id: str, query: str, query_vector: list, top_k: int, branch: str) -> List[Dict]:
    # get more results than needed, then boost matches that also hit fulltext
    vector_results = _vector_search(db, user_id, query_vector, top_k * 2, branch)

    query_lower = query.lower()
    for result in vector_results:
        if query_lower in result["text"].lower():
            result["score"] = min(result["score"] + 0.1, 1.0)

    vector_results.sort(key=lambda x: x["score"], reverse=True)
    return vector_results[:top_k]
