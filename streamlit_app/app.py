"""
atlasMemory Demo - Streamlit Cloud Version
TiDB-powered AI memory with hybrid search + branching
"""

import streamlit as st
import uuid
from atlas_memory import (
    add_memory,
    search_memory,
    save_point,
    delete_branch,
    list_branches,
    init_db,
    engine,
    get_session,
)
from atlas_memory.schema import Memory

# Page config
st.set_page_config(
    page_title="atlasMemory Demo",
    page_icon="🧠",
    layout="wide",
)

# Custom CSS for polished look
st.markdown("""
<style>
    /* Banner styling */
    .banner {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1rem 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1.5rem;
        border: 1px solid #0f3460;
    }
    .banner h1 {
        color: #fff;
        margin: 0;
        font-size: 1.5rem;
    }
    .banner p {
        color: #a0aec0;
        margin: 0.25rem 0 0 0;
        font-size: 0.9rem;
    }
    .tidb-badge {
        background: linear-gradient(90deg, #e11d48, #f43f5e);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-top: 0.5rem;
    }

    /* Step indicator */
    .step-indicator {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .step {
        flex: 1;
        padding: 0.5rem;
        text-align: center;
        background: #1e293b;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        color: #94a3b8;
    }
    .step.active {
        background: linear-gradient(135deg, #3b82f6, #2563eb);
        color: white;
        font-weight: 600;
    }
    .step.completed {
        background: #22c55e;
        color: white;
    }

    /* Branch indicator */
    .branch-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 2rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .branch-main {
        background: rgba(34, 197, 94, 0.15);
        color: #22c55e;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .branch-experiment {
        background: rgba(249, 115, 22, 0.15);
        color: #f97316;
        border: 1px solid rgba(249, 115, 22, 0.3);
    }

    /* Result cards */
    .result-card {
        background: #1e293b;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 0.75rem;
        border-left: 3px solid #3b82f6;
    }
    .result-card.conflict {
        border-left-color: #ef4444;
        background: rgba(239, 68, 68, 0.1);
    }
    .score-badge {
        background: #3b82f6;
        color: white;
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* SQL block */
    .sql-block {
        background: #0f172a;
        padding: 1rem;
        border-radius: 0.5rem;
        font-family: monospace;
        font-size: 0.85rem;
        overflow-x: auto;
        border: 1px solid #334155;
    }

    /* Info box */
    .info-box {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 2rem;
        border: 1px solid #334155;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize database
@st.cache_resource
def init_database():
    init_db(engine)
    return True

init_database()

# Session state initialization
if "user_id" not in st.session_state:
    st.session_state.user_id = f"demo-{uuid.uuid4().hex[:8]}"
if "current_branch" not in st.session_state:
    st.session_state.current_branch = "main"
if "step" not in st.session_state:
    st.session_state.step = 1
if "memories_added" not in st.session_state:
    st.session_state.memories_added = False
if "experiment_branch" not in st.session_state:
    st.session_state.experiment_branch = None

user_id = st.session_state.user_id
current_branch = st.session_state.current_branch

# Banner
st.markdown("""
<div class="banner">
    <h1>🧠 atlasMemory</h1>
    <p>AI agent memory with vector search, fulltext, JSON, and git-like branching</p>
    <span class="tidb-badge">Powered by TiDB Cloud (HTAP + Vector + Branching)</span>
</div>
""", unsafe_allow_html=True)

# Step indicator
steps = ["Add Memories", "Search", "Branch", "Add Conflict", "Compare"]
step_html = '<div class="step-indicator">'
for i, s in enumerate(steps, 1):
    cls = "completed" if i < st.session_state.step else ("active" if i == st.session_state.step else "")
    step_html += f'<div class="step {cls}">{i}. {s}</div>'
step_html += '</div>'
st.markdown(step_html, unsafe_allow_html=True)

# Branch indicator
branch_class = "branch-main" if current_branch == "main" else "branch-experiment"
branch_label = "production" if current_branch == "main" else "experiment"
st.markdown(f"""
<div class="branch-badge {branch_class}">
    <span>●</span> {current_branch} <span style="opacity: 0.7">({branch_label})</span>
</div>
""", unsafe_allow_html=True)

# Main content
col1, col2 = st.columns(2)

with col1:
    st.subheader("Add Memory")

    memory_text = st.text_area(
        "Memory text",
        placeholder="e.g., User loves beach destinations with warm weather",
        height=100,
        key="memory_input"
    )

    source = st.selectbox("Source", ["chat", "user", "system"], key="source_select")
    tags = st.text_input("Tags (comma-separated)", placeholder="preference, travel", key="tags_input")

    if st.button("Add to Current Branch", type="primary", use_container_width=True):
        if memory_text.strip():
            metadata = {
                "source": source,
                "tags": [t.strip() for t in tags.split(",") if t.strip()]
            }
            memory_id = add_memory(user_id, memory_text, metadata, current_branch)
            st.success(f"Memory added (ID: {memory_id})")
            st.session_state.memories_added = True
            if st.session_state.step == 1:
                st.session_state.step = 2

            # Show SQL
            with st.expander("View SQL"):
                st.code(f"""INSERT INTO memories (user_id, text, metadata_json, embedding, branch)
VALUES ('{user_id}', '{memory_text[:30]}...', '{metadata}', <384-dim vector>, '{current_branch}')""", language="sql")
        else:
            st.error("Enter some text first")

    # Seed data button
    if st.button("Load Demo Data", use_container_width=True):
        seed_memories = [
            {"text": "User loves beach destinations with warm weather", "source": "user", "tags": "preference, travel"},
            {"text": "User prefers boutique hotels over large chains", "source": "user", "tags": "preference, hotel"},
            {"text": "Budget is around $3000 for a week-long trip", "source": "chat", "tags": "budget, travel"},
        ]
        for mem in seed_memories:
            metadata = {
                "source": mem["source"],
                "tags": [t.strip() for t in mem["tags"].split(",") if t.strip()]
            }
            add_memory(user_id, mem["text"], metadata, "main")
        st.success(f"Added {len(seed_memories)} demo memories!")
        st.session_state.memories_added = True
        st.session_state.step = 2
        st.rerun()

with col2:
    st.subheader("Search")

    query = st.text_input(
        "Query",
        placeholder="e.g., travel tips, hotel preferences",
        key="search_query"
    )

    mode = st.radio(
        "Search mode",
        ["hybrid", "vector", "fulltext"],
        horizontal=True,
        key="search_mode"
    )

    if st.button("Search", type="primary", use_container_width=True):
        if query.strip():
            results = search_memory(user_id, query, top_k=5, branch=current_branch, mode=mode)

            if st.session_state.step == 2:
                st.session_state.step = 3

            if not results:
                st.info("No results found")
            else:
                for r in results:
                    is_conflict = "hates" in r["text"].lower()
                    card_class = "conflict" if is_conflict else ""

                    st.markdown(f"""
                    <div class="result-card {card_class}">
                        <span class="score-badge">{r['score']*100:.0f}% match</span>
                        {"<span style='background:#ef4444;color:white;padding:0.25rem 0.5rem;border-radius:0.25rem;font-size:0.75rem;margin-left:0.5rem;'>⚠️ CONFLICT</span>" if is_conflict else ""}
                        <p style="margin-top:0.5rem;margin-bottom:0;">{r['text']}</p>
                    </div>
                    """, unsafe_allow_html=True)

            # Show SQL
            with st.expander("View SQL"):
                if mode == "vector":
                    sql = f"""SELECT id, text, metadata_json,
       vec_cosine_distance(embedding, <query_vector>) as distance
FROM memories
WHERE user_id='{user_id}' AND branch='{current_branch}'
ORDER BY distance ASC
LIMIT 5"""
                elif mode == "fulltext":
                    sql = f"""SELECT id, text, metadata_json
FROM memories
WHERE user_id='{user_id}' AND branch='{current_branch}'
  AND text LIKE '%{query}%'
LIMIT 5"""
                else:
                    sql = f"""-- Step 1: Vector search
SELECT id, text, vec_cosine_distance(embedding, <query_vector>) as distance
FROM memories WHERE user_id='{user_id}' AND branch='{current_branch}'
ORDER BY distance LIMIT 10

-- Step 2: Boost results that also match fulltext
-- Re-rank by boosted score"""
                st.code(sql, language="sql")
        else:
            st.error("Enter a search query")

# Branching section
st.divider()
st.subheader("Branching (Time Travel)")

col3, col4, col5 = st.columns(3)

with col3:
    if st.button("Create Experiment Branch", use_container_width=True, disabled=current_branch != "main"):
        new_branch = save_point(user_id, "experiment", "main")
        st.session_state.experiment_branch = new_branch
        st.session_state.current_branch = new_branch
        st.session_state.step = 4
        st.success(f"Created branch: {new_branch}")
        st.rerun()

with col4:
    branches = list_branches(user_id)
    if "main" not in branches:
        branches = ["main"] + branches

    selected = st.selectbox(
        "Switch branch",
        branches,
        index=branches.index(current_branch) if current_branch in branches else 0,
        key="branch_select"
    )
    if selected != current_branch:
        st.session_state.current_branch = selected
        if selected == "main" and st.session_state.step >= 4:
            st.session_state.step = 5
        st.rerun()

with col5:
    if current_branch != "main":
        if st.button("Delete This Branch", type="secondary", use_container_width=True):
            deleted = delete_branch(user_id, current_branch)
            st.session_state.current_branch = "main"
            st.session_state.experiment_branch = None
            st.success(f"Deleted {deleted} memories")
            st.rerun()

# Show SQL for branching
if st.session_state.experiment_branch:
    with st.expander("View Branching SQL"):
        st.code(f"""-- Copy all memories from main to new branch
INSERT INTO memories (user_id, text, metadata_json, embedding, branch)
SELECT user_id, text, metadata_json, embedding, '{st.session_state.experiment_branch}'
FROM memories
WHERE user_id='{user_id}' AND branch='main'""", language="sql")

# Current memories
st.divider()
st.subheader(f"Memories in '{current_branch}'")

with get_session() as db:
    memories = db.query(Memory).filter(
        Memory.user_id == user_id,
        Memory.branch == current_branch
    ).order_by(Memory.created_at.desc()).all()

if memories:
    for m in memories:
        is_conflict = "hates" in m.text.lower()
        st.markdown(f"""
        <div class="result-card {'conflict' if is_conflict else ''}">
            <small style="color:#94a3b8;">ID: {m.id} | {m.created_at.strftime('%H:%M:%S') if m.created_at else 'N/A'}</small>
            {"<span style='background:#ef4444;color:white;padding:0.25rem 0.5rem;border-radius:0.25rem;font-size:0.75rem;margin-left:0.5rem;'>⚠️ CONFLICT</span>" if is_conflict else ""}
            <p style="margin:0.25rem 0;">{m.text}</p>
        </div>
        """, unsafe_allow_html=True)
else:
    st.info("No memories yet. Add some above or load demo data!")

# Info box at bottom
st.markdown("""
<div class="info-box">
    <div style="display:flex;gap:2rem;flex-wrap:wrap;">
        <div>
            <strong>🧠 Vectors + Text + JSON</strong><br>
            <span style="color:#94a3b8;">All in one row</span>
        </div>
        <div>
            <strong>🌿 Branching</strong><br>
            <span style="color:#94a3b8;">WHERE branch = '...'</span>
        </div>
        <div>
            <strong>🚫 No Stack</strong><br>
            <span style="color:#94a3b8;">No Pinecone + Postgres + Redis</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Reset button (small, at bottom)
st.divider()
if st.button("Reset Demo", type="secondary"):
    with get_session() as db:
        db.query(Memory).filter(Memory.user_id == user_id).delete()
        db.commit()
    st.session_state.step = 1
    st.session_state.current_branch = "main"
    st.session_state.memories_added = False
    st.session_state.experiment_branch = None
    st.success("Demo reset!")
    st.rerun()
