#!/usr/bin/env python3
"""Example usage of Memory MCP Server."""

from src.infinity_mcp_server.server import (
    activate_project,
    store_memory,
    get_memory,
    list_memories,
    update_memory,
    delete_memory,
)


def main():
    """Demonstrate basic usage of the memory MCP server."""
    print("=" * 60)
    print("Memory MCP Server - Example Usage")
    print("=" * 60)

    # Step 1: Activate project
    print("\n1. Activating project...")
    result = activate_project()
    print(f"   Project activated: {result['project_id']}")

    # Step 2: Store some memories
    print("\n2. Storing memories...")

    design_doc_id = store_memory(
        title="API Design",
        type="design_doc",
        content="# API Design\n\nREST API with JSON responses.\nEndpoints: /users, /projects",
    )["memory_id"]
    print(f"   Stored design_doc: {design_doc_id[:8]}...")

    overview_id = store_memory(
        title="Project Overview",
        type="project_overview",
        content="Building a memory system for AI agents using MCP protocol.",
    )["memory_id"]
    print(f"   Stored project_overview: {overview_id[:8]}...")

    test_plan_id = store_memory(
        title="Test Plan",
        type="test_plan",
        content="- Unit tests\n- Integration tests\n- E2E tests",
    )["memory_id"]
    print(f"   Stored test_plan: {test_plan_id[:8]}...")

    # Step 3: List all memories
    print("\n3. Listing all memories...")
    all_memories = list_memories()
    for mem in all_memories["memories"]:
        print(f"   - {mem['type']:20s} | {mem['title']}")

    # Step 4: Filter by type
    print("\n4. Listing only design_doc memories...")
    design_docs = list_memories(type="design_doc")
    for mem in design_docs["memories"]:
        print(f"   - {mem['title']}")

    # Step 5: Get a specific memory
    print("\n5. Getting API Design memory...")
    memory = get_memory(design_doc_id)
    print(f"   Title: {memory['memory']['title']}")
    print(f"   Type: {memory['memory']['type']}")
    print(f"   Content preview: {memory['memory']['content'][:50]}...")

    # Step 6: Update a memory
    print("\n6. Updating project overview...")
    update_memory(
        overview_id,
        "Building a memory system for AI agents using MCP protocol.\n"
        "Status: Implementation complete, all tests passing!",
    )
    updated = get_memory(overview_id)
    print(f"   Updated content: {updated['memory']['content'][:80]}...")

    # Step 7: Delete a memory
    print("\n7. Deleting test plan...")
    delete_memory(test_plan_id)
    remaining = list_memories()
    print(f"   Remaining memories: {len(remaining['memories'])}")

    # Step 8: Show final state
    print("\n8. Final memory state:")
    final_memories = list_memories()
    for mem in final_memories["memories"]:
        print(f"   - {mem['type']:20s} | {mem['title']}")

    print("\n" + "=" * 60)
    print("Demo complete! Check .infinity/memories.json for storage.")
    print("=" * 60)


if __name__ == "__main__":
    main()
