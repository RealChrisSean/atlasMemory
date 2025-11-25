#!/usr/bin/env python3
# examples/travel_agent_demo.py

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from atlas_memory import MemoryClient


def print_results(results):
    for i, r in enumerate(results[:5], 1):
        text = r["text"][:60] + "..." if len(r["text"]) > 60 else r["text"]
        print(f"  {i}. [{r['score']*100:.0f}%] {text}")


def main():
    client = MemoryClient(user_id="cli-demo")

    print()
    print("=" * 50)
    print("  atlasMemory - branching demo")
    print("=" * 50)

    # cleanup previous runs
    for branch in client.list_branches():
        if branch != "main":
            client.delete_branch(branch)
    client.switch_branch("main")

    # add some memories
    print("\n>>> MAIN: adding memories\n")
    client.add("User loves beach destinations with warm weather", {"source": "user"})
    client.add("User prefers boutique hotels over large chains", {"source": "user"})
    client.add("Budget is around $3000 for a week-long trip", {"source": "chat"})
    print("  added 3 memories")

    # search
    print("\n>>> MAIN: search 'vacation recommendations'\n")
    print_results(client.search("vacation recommendations"))

    # branch
    print("\n>>> creating branch 'experiment'")
    branch = client.save_point("experiment")
    print(f"  now on: {branch}")

    # add conflicting data
    print("\n>>> EXPERIMENT: adding conflicting memory\n")
    client.add("User hates beaches and wants mountain hiking only", {"source": "chat"})
    print("  added: 'User hates beaches...'")

    # search experiment
    print("\n>>> EXPERIMENT: search 'vacation recommendations'\n")
    print_results(client.search("vacation recommendations"))

    # rollback
    print("\n>>> switching back to MAIN")
    client.switch_branch("main")

    print("\n>>> MAIN: search 'vacation recommendations'\n")
    print_results(client.search("vacation recommendations"))
    print("\n  ^ conflict is gone")

    # cleanup
    print("\n>>> cleanup")
    deleted = client.delete_branch(branch)
    print(f"  deleted {deleted} rows from experiment")

    print()
    print("=" * 50)
    print("  done")
    print("=" * 50)
    print()


if __name__ == "__main__":
    main()
