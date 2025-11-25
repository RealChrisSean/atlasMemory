from datetime import datetime
from typing import List
from sqlalchemy import text

from atlas_memory.db import get_session
from atlas_memory.schema import Memory


def save_point(user_id: str, tag: str, source_branch: str = "main") -> str:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    new_branch = f"{tag}-{timestamp}"

    with get_session() as db:
        source_memories = db.query(Memory).filter(
            Memory.user_id == user_id,
            Memory.branch == source_branch
        ).all()

        for mem in source_memories:
            new_memory = Memory(
                user_id=mem.user_id,
                text=mem.text,
                metadata_json=mem.metadata_json,
                embedding=mem.embedding,
                branch=new_branch
            )
            db.add(new_memory)

        db.commit()

    return new_branch


def load_point(branch: str) -> str:
    return branch


def delete_branch(user_id: str, branch: str) -> int:
    if branch == "main":
        raise ValueError("Can't delete main branch")

    with get_session() as db:
        deleted = db.query(Memory).filter(
            Memory.user_id == user_id,
            Memory.branch == branch
        ).delete()
        db.commit()

    return deleted


def list_branches(user_id: str) -> List[str]:
    with get_session() as db:
        sql = text("""
            SELECT DISTINCT branch FROM memories
            WHERE user_id = :user_id ORDER BY branch
        """)
        results = db.execute(sql, {"user_id": user_id}).fetchall()

    return [r.branch for r in results]
