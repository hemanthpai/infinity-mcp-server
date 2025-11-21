"""Data models for memory MCP server."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

# Fixed set of allowed memory types
MemoryType = Literal[
    "design_doc",
    "project_overview",
    "implementation_plan",
    "progress_tracker",
    "test_plan",
    "instructions",
    "guidelines",
    "analysis",
]

ALLOWED_MEMORY_TYPES = {
    "design_doc",
    "project_overview",
    "implementation_plan",
    "progress_tracker",
    "test_plan",
    "instructions",
    "guidelines",
    "analysis",
}


@dataclass
class Memory:
    """Represents a memory entry."""

    id: str
    title: str
    type: str
    content: str
    created_at: str
    updated_at: str | None = None

    def to_dict(self) -> dict:
        """Convert memory to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "content": self.content,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Memory":
        """Create Memory from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            type=data["type"],
            content=data["content"],
            created_at=data["created_at"],
            updated_at=data.get("updated_at"),
        )


@dataclass
class MemoryMetadata:
    """Memory metadata without content (for list operations)."""

    id: str
    title: str
    type: str

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type,
        }


# Custom exceptions
class MemoryError(Exception):
    """Base exception for memory operations."""

    def __init__(self, error_code: str, message: str = ""):
        self.error_code = error_code
        self.message = message
        super().__init__(message)


class InvalidMemoryTypeError(MemoryError):
    """Raised when an invalid memory type is provided."""

    def __init__(self, memory_type: str):
        super().__init__(
            "invalid_memory_type",
            f"Invalid memory type: {memory_type}. Allowed types: {', '.join(ALLOWED_MEMORY_TYPES)}",
        )


class MissingRequiredFieldError(MemoryError):
    """Raised when a required field is missing."""

    def __init__(self, field: str):
        super().__init__("missing_required_field", f"Missing required field: {field}")


class MemoryNotFoundError(MemoryError):
    """Raised when a memory is not found."""

    def __init__(self, memory_id: str):
        super().__init__("memory_not_found", f"Memory not found: {memory_id}")


class ProjectNotActivatedError(MemoryError):
    """Raised when project is not activated."""

    def __init__(self):
        super().__init__(
            "project_not_activated",
            "Project not activated. Call activate_project first.",
        )


class StorageError(MemoryError):
    """Raised when a storage operation fails."""

    def __init__(self, message: str):
        super().__init__("storage_error", f"Storage error: {message}")


def validate_memory_type(memory_type: str) -> None:
    """Validate that the memory type is allowed.

    Args:
        memory_type: The memory type to validate

    Raises:
        InvalidMemoryTypeError: If the type is not in the allowed set
    """
    if memory_type not in ALLOWED_MEMORY_TYPES:
        raise InvalidMemoryTypeError(memory_type)


def validate_required_field(value: any, field_name: str) -> None:
    """Validate that a required field is present and non-empty.

    Args:
        value: The value to check
        field_name: Name of the field for error messages

    Raises:
        MissingRequiredFieldError: If the field is missing or empty
    """
    if value is None or (isinstance(value, str) and value == ""):
        raise MissingRequiredFieldError(field_name)


def get_iso_timestamp() -> str:
    """Get current timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
