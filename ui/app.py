import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from atlas_memory import (
    add_memory,
    search_memory,
    save_point,
    load_point,
    delete_branch,
    list_branches,
    init_db,
    engine,
    get_session,
)
from atlas_memory.schema import Memory

app = FastAPI(title="atlasMemory Demo")

@app.on_event("startup")
def startup():
    init_db(engine)


class AddMemoryRequest(BaseModel):
    user_id: str = "demo-user"
    text: str
    source: str = "chat"
    tags: str = ""
    branch: str = "main"


class SearchRequest(BaseModel):
    user_id: str = "demo-user"
    query: str
    mode: str = "hybrid"  # vector, fulltext, hybrid
    top_k: int = 5
    branch: str = "main"


class SavePointRequest(BaseModel):
    user_id: str = "demo-user"
    tag: str
    source_branch: str = "main"


class DeleteBranchRequest(BaseModel):
    user_id: str = "demo-user"
    branch: str


class MemoryResponse(BaseModel):
    id: int
    text: str
    metadata: Optional[dict]
    branch: str
    created_at: Optional[str]


class SearchResultResponse(BaseModel):
    id: int
    text: str
    metadata: Optional[dict]
    score: float
    sql_used: Optional[str] = None


@app.post("/api/memories")
def api_add_memory(req: AddMemoryRequest):
    metadata = {
        "source": req.source,
        "tags": [t.strip() for t in req.tags.split(",") if t.strip()]
    }

    memory_id = add_memory(
        user_id=req.user_id,
        content=req.text,
        metadata=metadata,
        branch=req.branch
    )

    # SQL that was executed
    sql_used = f"""INSERT INTO memories (user_id, text, metadata_json, embedding, branch)
VALUES ('{req.user_id}', '{req.text[:50]}...', '{metadata}', <384-dim vector>, '{req.branch}')"""

    return {
        "id": memory_id,
        "message": "Memory added",
        "branch": req.branch,
        "sql_used": sql_used
    }


@app.get("/api/memories")
def api_list_memories(user_id: str = "demo-user", branch: str = "main"):
    with get_session() as db:
        memories = db.query(Memory).filter(
            Memory.user_id == user_id,
            Memory.branch == branch
        ).order_by(Memory.created_at.desc()).all()

        return {
            "memories": [
                {
                    "id": m.id,
                    "text": m.text,
                    "metadata": m.metadata_json,
                    "branch": m.branch,
                    "created_at": m.created_at.isoformat() if m.created_at else None
                }
                for m in memories
            ],
            "sql_used": f"SELECT * FROM memories WHERE user_id='{user_id}' AND branch='{branch}' ORDER BY created_at DESC"
        }


@app.post("/api/search")
def api_search(req: SearchRequest):
    results = search_memory(
        user_id=req.user_id,
        query=req.query,
        top_k=req.top_k,
        branch=req.branch,
        mode=req.mode
    )

    # Generate SQL explanation based on mode
    if req.mode == "vector":
        sql_used = f"""SELECT id, text, metadata_json,
       vec_cosine_distance(embedding, <query_vector>) as distance
FROM memories
WHERE user_id='{req.user_id}' AND branch='{req.branch}'
ORDER BY distance ASC
LIMIT {req.top_k}"""
    elif req.mode == "fulltext":
        sql_used = f"""SELECT id, text, metadata_json
FROM memories
WHERE user_id='{req.user_id}' AND branch='{req.branch}'
  AND text LIKE '%{req.query}%'
LIMIT {req.top_k}"""
    else:  # hybrid
        sql_used = f"""-- Step 1: Vector search
SELECT id, text, vec_cosine_distance(embedding, <query_vector>) as distance
FROM memories WHERE user_id='{req.user_id}' AND branch='{req.branch}'
ORDER BY distance LIMIT {req.top_k * 2}

-- Step 2: Boost results that also match fulltext
-- Re-rank by boosted score"""

    return {
        "results": results,
        "mode": req.mode,
        "branch": req.branch,
        "sql_used": sql_used
    }


@app.get("/api/branches")
def api_list_branches(user_id: str = "demo-user"):
    branches = list_branches(user_id)
    # Always include 'main' even if empty
    if "main" not in branches:
        branches = ["main"] + branches

    return {
        "branches": branches,
        "sql_used": f"SELECT DISTINCT branch FROM memories WHERE user_id='{user_id}' ORDER BY branch"
    }


@app.post("/api/branches/save")
def api_save_point(req: SavePointRequest):
    new_branch = save_point(
        user_id=req.user_id,
        tag=req.tag,
        source_branch=req.source_branch
    )

    return {
        "new_branch": new_branch,
        "source_branch": req.source_branch,
        "message": f"Created branch '{new_branch}' from '{req.source_branch}'",
        "sql_used": f"""-- Copy all memories from source branch to new branch
INSERT INTO memories (user_id, text, metadata_json, embedding, branch)
SELECT user_id, text, metadata_json, embedding, '{new_branch}'
FROM memories
WHERE user_id='{req.user_id}' AND branch='{req.source_branch}'"""
    }


@app.delete("/api/branches/{branch}")
def api_delete_branch(branch: str, user_id: str = "demo-user"):
    if branch == "main":
        raise HTTPException(status_code=400, detail="Cannot delete main branch")

    deleted = delete_branch(user_id, branch)

    return {
        "deleted_count": deleted,
        "branch": branch,
        "message": f"Deleted {deleted} memories from branch '{branch}'",
        "sql_used": f"DELETE FROM memories WHERE user_id='{user_id}' AND branch='{branch}'"
    }


SEED_MEMORIES = [
    {"text": "User loves beach destinations with warm weather", "source": "user", "tags": "preference, travel"},
    {"text": "User prefers boutique hotels over large chains", "source": "user", "tags": "preference, hotel"},
    {"text": "Budget is around $3000 for a week-long trip", "source": "chat", "tags": "budget, travel"},
]

@app.post("/api/seed")
def api_seed_data(user_id: str = "demo-user"):
    with get_session() as db:
        count = db.query(Memory).filter(
            Memory.user_id == user_id,
            Memory.branch == "main"
        ).count()

        if count > 0:
            return {"seeded": False, "message": "Main branch already has data"}

    # main is empty, add seed data
    for mem in SEED_MEMORIES:
        metadata = {
            "source": mem["source"],
            "tags": [t.strip() for t in mem["tags"].split(",") if t.strip()]
        }
        add_memory(user_id, mem["text"], metadata, "main")

    return {"seeded": True, "count": len(SEED_MEMORIES)}


@app.post("/api/reset")
def api_reset_demo(user_id: str = "demo-user"):
    with get_session() as db:
        # delete everything for this user
        db.query(Memory).filter(Memory.user_id == user_id).delete()
        db.commit()

    # re-seed
    for mem in SEED_MEMORIES:
        metadata = {
            "source": mem["source"],
            "tags": [t.strip() for t in mem["tags"].split(",") if t.strip()]
        }
        add_memory(user_id, mem["text"], metadata, "main")

    return {"reset": True, "seeded": len(SEED_MEMORIES)}


@app.get("/", response_class=HTMLResponse)
def serve_frontend():
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return html_path.read_text()
    else:
        return "<h1>Frontend not found. Create static/index.html</h1>"


if __name__ == "__main__":
    import uvicorn
    print("Starting atlasMemory Demo UI...")
    print("Open http://localhost:8000 in your browser")
    uvicorn.run(app, host="0.0.0.0", port=8000)
