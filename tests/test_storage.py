"""Unit tests for storage layer."""

import json
import pytest
import tempfile
import shutil
from pathlib import Path

from src.infinity_mcp_server.storage import MemoryStorage
from src.infinity_mcp_server.models import (
    InvalidMemoryTypeError,
    MissingRequiredFieldError,
    MemoryNotFoundError,
    ProjectNotActivatedError,
)


class TestMemoryStorage:
    """Test cases for MemoryStorage class."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def storage(self, temp_dir):
        """Create a storage instance with temporary directory."""
        return MemoryStorage(working_dir=temp_dir)

    def test_activate_project_creates_infinity_dir(self, storage, temp_dir):
        """Test that activate_project creates .infinity directory."""
        # Act
        project_id = storage.activate_project()

        # Assert
        infinity_dir = Path(temp_dir) / ".infinity"
        assert infinity_dir.exists()
        assert infinity_dir.is_dir()
        assert project_id is not None

    def test_activate_project_creates_project_id_file(self, storage, temp_dir):
        """Test that activate_project creates project_id file."""
        # Act
        project_id = storage.activate_project()

        # Assert
        project_id_file = Path(temp_dir) / ".infinity" / "project_id"
        assert project_id_file.exists()
        assert project_id_file.read_text().strip() == project_id

    def test_activate_project_loads_existing_project_id(self, storage, temp_dir):
        """Test that activate_project loads existing project ID."""
        # Arrange - first activation
        first_id = storage.activate_project()

        # Create new storage instance
        storage2 = MemoryStorage(working_dir=temp_dir)

        # Act - second activation
        second_id = storage2.activate_project()

        # Assert
        assert first_id == second_id

    def test_activate_project_creates_memories_file(self, storage, temp_dir):
        """Test that activate_project creates memories.json file."""
        # Act
        storage.activate_project()

        # Assert
        memories_file = Path(temp_dir) / ".infinity" / "memories.json"
        assert memories_file.exists()

        # Check file structure
        with open(memories_file, "r") as f:
            data = json.load(f)
        assert "project_id" in data
        assert "memories" in data
        assert data["memories"] == []

    def test_store_memory_without_activation_raises_error(self, storage):
        """Test that store_memory raises error if project not activated."""
        with pytest.raises(ProjectNotActivatedError) as exc_info:
            storage.store_memory("Test", "design_doc", "Content")
        assert exc_info.value.error_code == "project_not_activated"

    def test_store_memory_with_valid_data(self, storage):
        """Test storing a memory with valid data."""
        # Arrange
        storage.activate_project()

        # Act
        memory_id = storage.store_memory("API Design", "design_doc", "# API Design\n\nDetails here")

        # Assert
        assert memory_id is not None
        assert len(memory_id) == 36  # UUID length

    def test_store_memory_with_invalid_type(self, storage):
        """Test that store_memory rejects invalid memory type."""
        # Arrange
        storage.activate_project()

        # Act & Assert
        with pytest.raises(InvalidMemoryTypeError) as exc_info:
            storage.store_memory("Test", "invalid_type", "Content")
        assert exc_info.value.error_code == "invalid_memory_type"

    def test_store_memory_with_empty_title(self, storage):
        """Test that store_memory rejects empty title."""
        # Arrange
        storage.activate_project()

        # Act & Assert
        with pytest.raises(MissingRequiredFieldError) as exc_info:
            storage.store_memory("", "design_doc", "Content")
        assert exc_info.value.error_code == "missing_required_field"

    def test_store_memory_with_empty_content(self, storage):
        """Test that store_memory allows empty content."""
        # Arrange
        storage.activate_project()

        # Act
        memory_id = storage.store_memory("Test", "design_doc", "")

        # Assert
        assert memory_id is not None

    def test_store_memory_with_none_content(self, storage):
        """Test that store_memory rejects None content."""
        # Arrange
        storage.activate_project()

        # Act & Assert
        with pytest.raises(MissingRequiredFieldError):
            storage.store_memory("Test", "design_doc", None)

    def test_get_memory_returns_correct_memory(self, storage):
        """Test that get_memory returns the correct memory."""
        # Arrange
        storage.activate_project()
        memory_id = storage.store_memory("Test Memory", "design_doc", "Test content")

        # Act
        memory = storage.get_memory(memory_id)

        # Assert
        assert memory.id == memory_id
        assert memory.title == "Test Memory"
        assert memory.type == "design_doc"
        assert memory.content == "Test content"
        assert memory.created_at is not None

    def test_get_memory_with_invalid_id(self, storage):
        """Test that get_memory raises error for invalid ID."""
        # Arrange
        storage.activate_project()

        # Act & Assert
        with pytest.raises(MemoryNotFoundError) as exc_info:
            storage.get_memory("invalid-uuid")
        assert exc_info.value.error_code == "memory_not_found"

    def test_list_memories_returns_all_memories(self, storage):
        """Test that list_memories returns all memories."""
        # Arrange
        storage.activate_project()
        id1 = storage.store_memory("Memory 1", "design_doc", "Content 1")
        id2 = storage.store_memory("Memory 2", "test_plan", "Content 2")

        # Act
        memories = storage.list_memories()

        # Assert
        assert len(memories) == 2
        assert {m.id for m in memories} == {id1, id2}
        assert {m.title for m in memories} == {"Memory 1", "Memory 2"}
        # Ensure content is not included
        assert not hasattr(memories[0], "content")

    def test_list_memories_filtered_by_type(self, storage):
        """Test that list_memories can filter by type."""
        # Arrange
        storage.activate_project()
        id1 = storage.store_memory("Design", "design_doc", "Content")
        storage.store_memory("Test", "test_plan", "Content")
        storage.store_memory("Analysis", "analysis", "Content")

        # Act
        design_docs = storage.list_memories(memory_type="design_doc")

        # Assert
        assert len(design_docs) == 1
        assert design_docs[0].id == id1
        assert design_docs[0].type == "design_doc"

    def test_list_memories_returns_empty_list_when_no_matches(self, storage):
        """Test that list_memories returns empty list when no matches."""
        # Arrange
        storage.activate_project()
        storage.store_memory("Test", "design_doc", "Content")

        # Act
        results = storage.list_memories(memory_type="test_plan")

        # Assert
        assert results == []

    def test_update_memory_updates_content(self, storage):
        """Test that update_memory updates content."""
        # Arrange
        storage.activate_project()
        memory_id = storage.store_memory("Test", "design_doc", "Original content")

        # Act
        storage.update_memory(memory_id, "Updated content")

        # Assert
        memory = storage.get_memory(memory_id)
        assert memory.content == "Updated content"
        assert memory.updated_at is not None

    def test_update_memory_does_not_change_other_fields(self, storage):
        """Test that update_memory only changes content."""
        # Arrange
        storage.activate_project()
        memory_id = storage.store_memory("Original Title", "design_doc", "Content")
        original = storage.get_memory(memory_id)

        # Act
        storage.update_memory(memory_id, "New content")

        # Assert
        updated = storage.get_memory(memory_id)
        assert updated.title == original.title
        assert updated.type == original.type
        assert updated.id == original.id
        assert updated.created_at == original.created_at

    def test_update_memory_with_invalid_id(self, storage):
        """Test that update_memory raises error for invalid ID."""
        # Arrange
        storage.activate_project()

        # Act & Assert
        with pytest.raises(MemoryNotFoundError):
            storage.update_memory("invalid-uuid", "New content")

    def test_delete_memory_removes_memory(self, storage):
        """Test that delete_memory removes the memory."""
        # Arrange
        storage.activate_project()
        memory_id = storage.store_memory("Test", "design_doc", "Content")

        # Act
        storage.delete_memory(memory_id)

        # Assert
        with pytest.raises(MemoryNotFoundError):
            storage.get_memory(memory_id)

    def test_delete_memory_with_invalid_id(self, storage):
        """Test that delete_memory raises error for invalid ID."""
        # Arrange
        storage.activate_project()

        # Act & Assert
        with pytest.raises(MemoryNotFoundError):
            storage.delete_memory("invalid-uuid")

    def test_multiple_memories_of_same_type(self, storage):
        """Test that multiple memories of the same type can be stored."""
        # Arrange
        storage.activate_project()

        # Act
        id1 = storage.store_memory("Design 1", "design_doc", "Content 1")
        id2 = storage.store_memory("Design 2", "design_doc", "Content 2")

        # Assert
        assert id1 != id2
        memories = storage.list_memories(memory_type="design_doc")
        assert len(memories) == 2

    def test_all_memory_types_are_valid(self, storage):
        """Test that all defined memory types are valid."""
        # Arrange
        storage.activate_project()
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
            memory_id = storage.store_memory(f"Test {mem_type}", mem_type, "Content")
            assert memory_id is not None
