"""Storage layer for memory management."""

import json
import os
import uuid
from pathlib import Path
from typing import Optional

from .models import (
    Memory,
    MemoryMetadata,
    MemoryNotFoundError,
    StorageError,
    get_iso_timestamp,
    validate_memory_type,
    validate_required_field,
)


class MemoryStorage:
    """Handles storage and retrieval of memories for a project."""

    INFINITY_DIR = ".infinity"
    PROJECT_ID_FILE = "project_id"
    MEMORIES_FILE = "memories.json"

    def __init__(self, working_dir: Optional[str] = None):
        """Initialize storage.

        Args:
            working_dir: Working directory for the project. Defaults to CWD.
        """
        self.working_dir = Path(working_dir or os.getcwd())
        self.infinity_dir = self.working_dir / self.INFINITY_DIR
        self.project_id_path = self.infinity_dir / self.PROJECT_ID_FILE
        self.memories_path = self.infinity_dir / self.MEMORIES_FILE
        self.project_id: Optional[str] = None

    def activate_project(self) -> str:
        """Activate the project by loading or creating project ID.

        Returns:
            The project UUID

        Raises:
            StorageError: If .infinity directory cannot be created
        """
        try:
            # Create .infinity directory if it doesn't exist
            if not self.infinity_dir.exists():
                self.infinity_dir.mkdir(parents=True, exist_ok=True)

            # Load or create project ID
            if self.project_id_path.exists():
                self.project_id = self.project_id_path.read_text().strip()
            else:
                self.project_id = str(uuid.uuid4())
                self.project_id_path.write_text(self.project_id)

            # Initialize memories file if it doesn't exist
            if not self.memories_path.exists():
                self._write_memories_file({"project_id": self.project_id, "memories": []})

            return self.project_id

        except (OSError, IOError) as e:
            raise StorageError(f"Cannot create project directory: {e}")

    def _ensure_activated(self) -> None:
        """Ensure project is activated.

        Raises:
            ProjectNotActivatedError: If activate_project hasn't been called
        """
        if self.project_id is None:
            from .models import ProjectNotActivatedError

            raise ProjectNotActivatedError()

    def _read_memories_file(self) -> dict:
        """Read the memories.json file.

        Returns:
            Dictionary with project_id and memories list

        Raises:
            StorageError: If file cannot be read
        """
        try:
            if not self.memories_path.exists():
                return {"project_id": self.project_id, "memories": []}

            with open(self.memories_path, "r") as f:
                return json.load(f)
        except (OSError, IOError, json.JSONDecodeError) as e:
            raise StorageError(f"Cannot read memories file: {e}")

    def _write_memories_file(self, data: dict) -> None:
        """Write the memories.json file atomically.

        Args:
            data: Dictionary with project_id and memories list

        Raises:
            StorageError: If file cannot be written
        """
        try:
            # Write to temp file first
            temp_path = self.memories_path.with_suffix(".tmp")
            with open(temp_path, "w") as f:
                json.dump(data, f, indent=2)

            # Atomic rename
            temp_path.replace(self.memories_path)
        except (OSError, IOError) as e:
            raise StorageError(f"Cannot write memories file: {e}")

    def store_memory(self, title: str, memory_type: str, content: str) -> str:
        """Store a new memory.

        Args:
            title: Memory title
            memory_type: Type of memory (must be in allowed types)
            content: Memory content (markdown)

        Returns:
            UUID of created memory

        Raises:
            InvalidMemoryTypeError: If type is not allowed
            MissingRequiredFieldError: If required field is missing
            StorageError: If storage operation fails
        """
        self._ensure_activated()

        # Validate inputs
        validate_required_field(title, "title")
        validate_memory_type(memory_type)
        # Content can be empty but not None
        if content is None:
            validate_required_field(content, "content")

        # Create memory
        memory_id = str(uuid.uuid4())
        memory = Memory(
            id=memory_id,
            title=title,
            type=memory_type,
            content=content,
            created_at=get_iso_timestamp(),
        )

        # Add to storage
        data = self._read_memories_file()
        data["memories"].append(memory.to_dict())
        self._write_memories_file(data)

        return memory_id

    def get_memory(self, memory_id: str) -> Memory:
        """Retrieve a memory by ID.

        Args:
            memory_id: UUID of the memory

        Returns:
            Memory object

        Raises:
            MemoryNotFoundError: If memory doesn't exist
            StorageError: If storage operation fails
        """
        self._ensure_activated()

        data = self._read_memories_file()
        for mem_dict in data["memories"]:
            if mem_dict["id"] == memory_id:
                return Memory.from_dict(mem_dict)

        raise MemoryNotFoundError(memory_id)

    def list_memories(self, memory_type: Optional[str] = None) -> list[MemoryMetadata]:
        """List all memories, optionally filtered by type.

        Args:
            memory_type: Optional type filter

        Returns:
            List of MemoryMetadata objects (without content)

        Raises:
            StorageError: If storage operation fails
        """
        self._ensure_activated()

        data = self._read_memories_file()
        memories = []

        for mem_dict in data["memories"]:
            # Filter by type if specified
            if memory_type is not None and mem_dict["type"] != memory_type:
                continue

            memories.append(
                MemoryMetadata(
                    id=mem_dict["id"],
                    title=mem_dict["title"],
                    type=mem_dict["type"],
                )
            )

        return memories

    def update_memory(self, memory_id: str, content: str) -> None:
        """Update a memory's content.

        Args:
            memory_id: UUID of the memory
            content: New content

        Raises:
            MemoryNotFoundError: If memory doesn't exist
            StorageError: If storage operation fails
        """
        self._ensure_activated()

        data = self._read_memories_file()
        found = False

        for mem_dict in data["memories"]:
            if mem_dict["id"] == memory_id:
                mem_dict["content"] = content
                mem_dict["updated_at"] = get_iso_timestamp()
                found = True
                break

        if not found:
            raise MemoryNotFoundError(memory_id)

        self._write_memories_file(data)

    def delete_memory(self, memory_id: str) -> None:
        """Delete a memory.

        Args:
            memory_id: UUID of the memory

        Raises:
            MemoryNotFoundError: If memory doesn't exist
            StorageError: If storage operation fails
        """
        self._ensure_activated()

        data = self._read_memories_file()
        original_length = len(data["memories"])

        # Filter out the memory to delete
        data["memories"] = [m for m in data["memories"] if m["id"] != memory_id]

        if len(data["memories"]) == original_length:
            raise MemoryNotFoundError(memory_id)

        self._write_memories_file(data)
