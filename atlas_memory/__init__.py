from atlas_memory.memory import add_memory, search_memory
from atlas_memory.branching import save_point, load_point, delete_branch, list_branches
from atlas_memory.embeddings import embed
from atlas_memory.db import get_session, engine, TiDBConnectionError
from atlas_memory.schema import Memory, init_db


class MemoryClient:
    def __init__(self, user_id: str, branch: str = "main"):
        self.user_id = user_id
        self.branch = branch
        init_db(engine)

    def add(self, text: str, metadata: dict = None) -> int:
        return add_memory(self.user_id, text, metadata, self.branch)

    def search(self, query: str, top_k: int = 5, mode: str = "hybrid"):
        return search_memory(self.user_id, query, top_k, self.branch, mode)

    def save_point(self, tag: str) -> str:
        new_branch = save_point(self.user_id, tag, self.branch)
        self.branch = new_branch
        return new_branch

    def switch_branch(self, branch: str):
        self.branch = branch

    def delete_branch(self, branch: str = None) -> int:
        target = branch or self.branch
        if target == self.branch and target != "main":
            self.branch = "main"
        return delete_branch(self.user_id, target)

    def list_branches(self):
        return list_branches(self.user_id)


__all__ = [
    "MemoryClient",
    "add_memory",
    "search_memory",
    "save_point",
    "load_point",
    "delete_branch",
    "list_branches",
    "embed",
    "get_session",
    "engine",
    "Memory",
    "init_db",
    "TiDBConnectionError",
]
