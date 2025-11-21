"""Integration tests for MCP server - covers all acceptance criteria."""

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from src.infinity_mcp_server.server import (
    activate_project,
    delete_memory,
    get_memory,
    list_memories,
    store_memory,
    update_memory,
)
from src.infinity_mcp_server.storage import MemoryStorage


class TestAcceptanceCriteria:
    """Test all acceptance criteria from the PRD."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Save current directory
        self.original_dir = os.getcwd()

        # Create temp directory and switch to it
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)

        # Reset global storage
        import src.infinity_mcp_server.server as server_module

        server_module.storage = None

        yield

        # Restore original directory and cleanup
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

        # Reset global storage again
        server_module.storage = None

    def test_tc1_activate_project_creates_infinity_dir(self):
        """TC1: activate_project creates .infinity/project_id on first call in new dir."""
        # Act
        result = activate_project()

        # Assert
        assert result["success"] is True
        assert "project_id" in result

        infinity_dir = Path(self.temp_dir) / ".infinity"
        assert infinity_dir.exists()

        project_id_file = infinity_dir / "project_id"
        assert project_id_file.exists()
        assert project_id_file.read_text().strip() == result["project_id"]

    def test_tc2_activate_project_loads_existing_project_id(self):
        """TC2: activate_project loads existing project ID from .infinity/project_id on second call."""
        # Arrange - first activation
        first_result = activate_project()
        first_project_id = first_result["project_id"]

        # Reset global storage to simulate new session
        import src.infinity_mcp_server.server as server_module

        server_module.storage = None

        # Act - second activation
        second_result = activate_project()
        second_project_id = second_result["project_id"]

        # Assert
        assert first_project_id == second_project_id

    def test_tc3_store_memory_with_valid_type(self):
        """TC3: store_memory with valid type → returns UUID and saves to .infinity/memories.json."""
        # Arrange
        activate_project()

        # Act
        result = store_memory(
            title="API Design", type="design_doc", content="# API Design\n\nDetails here"
        )

        # Assert
        assert result["success"] is True
        assert "memory_id" in result
        assert len(result["memory_id"]) == 36  # UUID length

        # Check that it was saved to memories.json
        memories_file = Path(self.temp_dir) / ".infinity" / "memories.json"
        assert memories_file.exists()

        with open(memories_file, "r") as f:
            data = json.load(f)

        assert len(data["memories"]) == 1
        assert data["memories"][0]["id"] == result["memory_id"]
        assert data["memories"][0]["title"] == "API Design"
        assert data["memories"][0]["type"] == "design_doc"

    def test_tc4_store_memory_with_invalid_type(self):
        """TC4: store_memory with invalid type → rejects with error."""
        # Arrange
        activate_project()

        # Act
        result = store_memory(title="Test", type="invalid_type", content="Content")

        # Assert
        assert "error" in result
        assert result["error"] == "invalid_memory_type"

    def test_tc5_get_memory_validation(self):
        """TC5: get_memory returns correct content for valid UUID; rejects with error on invalid."""
        # Arrange
        activate_project()
        store_result = store_memory(
            title="Test Memory", type="design_doc", content="Test content"
        )
        memory_id = store_result["memory_id"]

        # Act - valid UUID
        get_result = get_memory(memory_id)

        # Assert - valid UUID
        assert get_result["success"] is True
        assert "memory" in get_result
        assert get_result["memory"]["id"] == memory_id
        assert get_result["memory"]["title"] == "Test Memory"
        assert get_result["memory"]["content"] == "Test content"

        # Act - invalid UUID
        invalid_result = get_memory("invalid-uuid-12345")

        # Assert - invalid UUID
        assert "error" in invalid_result
        assert invalid_result["error"] == "memory_not_found"

    def test_tc6_list_memories_returns_metadata_only(self):
        """TC6: list_memories returns list of {id, title, type} only; no content."""
        # Arrange
        activate_project()
        store_memory(
            title="Memory 1", type="design_doc", content="Long content here..."
        )
        store_memory(
            title="Memory 2", type="test_plan", content="More long content..."
        )

        # Act
        result = list_memories()

        # Assert
        assert result["success"] is True
        assert "memories" in result
        assert len(result["memories"]) == 2

        # Check that content is not included
        for memory in result["memories"]:
            assert "id" in memory
            assert "title" in memory
            assert "type" in memory
            assert "content" not in memory

    def test_tc7_list_memories_with_type_filter(self):
        """TC7: list_memories with type=design_doc filters correctly."""
        # Arrange
        activate_project()
        store_memory(title="Design 1", type="design_doc", content="Content 1")
        store_memory(title="Test 1", type="test_plan", content="Content 2")
        store_memory(title="Design 2", type="design_doc", content="Content 3")

        # Act
        result = list_memories(type="design_doc")

        # Assert
        assert result["success"] is True
        assert len(result["memories"]) == 2
        assert all(m["type"] == "design_doc" for m in result["memories"])
        assert {m["title"] for m in result["memories"]} == {"Design 1", "Design 2"}

    def test_tc8_update_memory_updates_content_only(self):
        """TC8: update_memory updates content but not type/title → success; error if UUID missing."""
        # Arrange
        activate_project()
        store_result = store_memory(
            title="Original Title", type="design_doc", content="Original content"
        )
        memory_id = store_result["memory_id"]

        # Act - update with valid UUID
        update_result = update_memory(memory_id, "Updated content")

        # Assert - update success
        assert update_result["success"] is True

        # Verify content updated but other fields unchanged
        get_result = get_memory(memory_id)
        assert get_result["memory"]["content"] == "Updated content"
        assert get_result["memory"]["title"] == "Original Title"
        assert get_result["memory"]["type"] == "design_doc"

        # Act - update with invalid UUID
        invalid_result = update_memory("invalid-uuid", "New content")

        # Assert - error
        assert "error" in invalid_result
        assert invalid_result["error"] == "memory_not_found"

    def test_tc9_delete_memory_removes_entry(self):
        """TC9: delete_memory removes entry from .infinity/memories.json → success."""
        # Arrange
        activate_project()
        store_result = store_memory(title="To Delete", type="design_doc", content="Content")
        memory_id = store_result["memory_id"]

        # Act
        delete_result = delete_memory(memory_id)

        # Assert
        assert delete_result["success"] is True

        # Verify it's removed
        get_result = get_memory(memory_id)
        assert "error" in get_result
        assert get_result["error"] == "memory_not_found"

        # Verify it's removed from file
        memories_file = Path(self.temp_dir) / ".infinity" / "memories.json"
        with open(memories_file, "r") as f:
            data = json.load(f)
        assert len(data["memories"]) == 0

    def test_tc10_project_isolation(self):
        """TC10: Agent cannot access memories from other projects (different CWD)."""
        # Arrange - Create memory in project 1
        activate_project()
        store_result = store_memory(
            title="Project 1 Memory", type="design_doc", content="Content 1"
        )
        memory_id_1 = store_result["memory_id"]

        # Create second project directory
        temp_dir_2 = tempfile.mkdtemp()

        try:
            # Switch to project 2
            os.chdir(temp_dir_2)

            # Reset global storage
            import src.infinity_mcp_server.server as server_module

            server_module.storage = None

            # Activate project 2
            activate_project()

            # Try to access memory from project 1
            get_result = get_memory(memory_id_1)

            # Assert - should not find it
            assert "error" in get_result
            assert get_result["error"] == "memory_not_found"

            # List memories - should be empty
            list_result = list_memories()
            assert list_result["success"] is True
            assert len(list_result["memories"]) == 0

        finally:
            # Cleanup
            os.chdir(self.original_dir)
            shutil.rmtree(temp_dir_2)

    def test_project_not_activated_error(self):
        """Test that operations fail if project not activated."""
        # Reset global storage
        import src.infinity_mcp_server.server as server_module

        server_module.storage = None

        # Try to store memory without activation
        result = store_memory(title="Test", type="design_doc", content="Content")

        # Assert
        assert "error" in result
        assert result["error"] == "project_not_activated"

    def test_all_memory_types_accepted(self):
        """Test that all 7 defined memory types are accepted."""
        # Arrange
        activate_project()

        memory_types = [
            "design_doc",
            "project_overview",
            "implementation_plan",
            "progress_tracker",
            "test_plan",
            "instructions",
            "rules",
            "analysis",
        ]

        # Act & Assert
        for mem_type in memory_types:
            result = store_memory(title=f"Test {mem_type}", type=mem_type, content="Content")
            assert result["success"] is True, f"Failed for type {mem_type}"

    def test_duplicate_titles_allowed(self):
        """Test that duplicate titles are allowed (only UUID is unique)."""
        # Arrange
        activate_project()

        # Act
        result1 = store_memory(
            title="Same Title", type="design_doc", content="Content 1"
        )
        result2 = store_memory(
            title="Same Title", type="design_doc", content="Content 2"
        )

        # Assert
        assert result1["success"] is True
        assert result2["success"] is True
        assert result1["memory_id"] != result2["memory_id"]

        # Both should be in the list
        list_result = list_memories()
        assert len(list_result["memories"]) == 2

    def test_empty_content_allowed(self):
        """Test that empty content string is allowed."""
        # Arrange
        activate_project()

        # Act
        result = store_memory(title="Empty Content", type="design_doc", content="")

        # Assert
        assert result["success"] is True

        # Verify it was stored
        get_result = get_memory(result["memory_id"])
        assert get_result["memory"]["content"] == ""

    def test_created_at_and_updated_at_timestamps(self):
        """Test that created_at and updated_at timestamps are set correctly."""
        # Arrange
        activate_project()

        # Act - create memory
        store_result = store_memory(title="Test", type="design_doc", content="Original")
        memory_id = store_result["memory_id"]

        # Get memory and check created_at
        get_result = get_memory(memory_id)
        assert "created_at" in get_result["memory"]
        assert get_result["memory"]["created_at"] is not None
        assert get_result["memory"]["updated_at"] is None  # Not updated yet

        # Update memory
        update_memory(memory_id, "Updated content")

        # Get memory again and check updated_at
        get_result2 = get_memory(memory_id)
        assert "updated_at" in get_result2["memory"]
        assert get_result2["memory"]["updated_at"] is not None
        # created_at should remain the same
        assert get_result2["memory"]["created_at"] == get_result["memory"]["created_at"]
