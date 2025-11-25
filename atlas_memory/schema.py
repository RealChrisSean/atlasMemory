# atlas_memory/schema.py
from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Index
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from tidb_vector.sqlalchemy import VectorType  # TiDB vector column type

Base = declarative_base()

class Memory(Base):
    __tablename__ = "memories"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(String(255), nullable=False, index=True)

    # Logical branching (OSS-friendly time travel)
    branch = Column(String(255), default="main", nullable=False, index=True)

    text = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)

    # 384 dims = MiniLM embeddings we’ll use (OSS)
    embedding = Column(VectorType(dim=384), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    __table_args__ = (
        Index("idx_user_branch", "user_id", "branch"),
    )

def init_db(engine):
    """Create tables if they don't exist."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database Tables Created Successfully!")