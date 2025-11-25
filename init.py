#!/usr/bin/env python3
# init.py - run once to create the memories table

from atlas_memory.db import engine
from atlas_memory.schema import init_db

if __name__ == "__main__":
    init_db(engine)
