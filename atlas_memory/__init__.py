# atlas_memory/__init__.py
# This file marks atlas_memory as a package you can import.
# Later we'll expose AtlasMemory here.

# init.py
from atlas_memory.db import engine
from atlas_memory.schema import init_db

if __name__ == "__main__":
    print("🔌 Connecting to TiDB...")
    init_db(engine)
    print("🚀 AtlasMemory Core is Live!")