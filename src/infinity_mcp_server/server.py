"""MCP Server for memory management."""

import os
from typing import Optional

from mcp.server.fastmcp import FastMCP

from .models import (
    InvalidMemoryTypeError,
    MemoryError,
    MemoryNotFoundError,
    MissingRequiredFieldError,
    ProjectNotActivatedError,
)
from .storage import MemoryStorage

# Create FastMCP server instance
mcp = FastMCP("Memory MCP Server")

# Global storage instance
storage: Optional[MemoryStorage] = None


def get_storage() -> MemoryStorage:
    """Get or create storage instance.

    The storage instance is created lazily based on the current working directory.
    """
    global storage
    if storage is None:
        storage = MemoryStorage(working_dir=os.getcwd())
    return storage


@mcp.tool()
def activate_project() -> dict:
    """Activate the current project and load/create its memory system.

    This must be called before any other memory operations.
    Creates a .infinity directory in the current working directory if it doesn't exist.

    Returns:
        dict: Success response with project_id
            {
                "success": true,
                "project_id": "uuid-string"
            }

    Errors:
        - Cannot create .infinity directory: {"error": "cannot_create_project_dir"}
    """
    try:
        storage_instance = get_storage()
        project_id = storage_instance.activate_project()
        return {"success": True, "project_id": project_id}
    except MemoryError as e:
        return {"error": e.error_code}
    except Exception as e:
        return {"error": "storage_error"}


@mcp.tool()
def store_memory(title: str, type: str, content: str) -> dict:
    """Store a new memory.

    Args:
        title: Memory title (required, non-empty)
        type: Memory type - must be one of: design_doc, project_overview,
              implementation_plan, progress_tracker, test_plan, instructions,
              rules, analysis
        content: Memory content in markdown format (can be empty string)

    Returns:
        dict: Success response with memory_id
            {
                "success": true,
                "memory_id": "uuid-string"
            }

    Errors:
        - Invalid type: {"error": "invalid_memory_type"}
        - Missing required field: {"error": "missing_required_field"}
        - Project not activated: {"error": "project_not_activated"}
        - Storage error: {"error": "storage_error"}
    """
    try:
        storage_instance = get_storage()
        memory_id = storage_instance.store_memory(title, type, content)
        return {"success": True, "memory_id": memory_id}
    except (
        InvalidMemoryTypeError,
        MissingRequiredFieldError,
        ProjectNotActivatedError,
    ) as e:
        return {"error": e.error_code}
    except Exception as e:
        return {"error": "storage_error"}


@mcp.tool()
def get_memory(memory_id: str) -> dict:
    """Retrieve a memory by its ID.

    Args:
        memory_id: UUID of the memory to retrieve

    Returns:
        dict: Success response with memory details
            {
                "success": true,
                "memory": {
                    "id": "uuid",
                    "title": "string",
                    "type": "string",
                    "content": "string",
                    "created_at": "ISO8601",
                    "updated_at": "ISO8601" or null
                }
            }

    Errors:
        - Memory not found: {"error": "memory_not_found"}
        - Project not activated: {"error": "project_not_activated"}
        - Storage error: {"error": "storage_error"}
    """
    try:
        storage_instance = get_storage()
        memory = storage_instance.get_memory(memory_id)
        return {"success": True, "memory": memory.to_dict()}
    except (MemoryNotFoundError, ProjectNotActivatedError) as e:
        return {"error": e.error_code}
    except Exception as e:
        return {"error": "storage_error"}


@mcp.tool()
def list_memories(type: Optional[str] = None) -> dict:
    """List all memories, optionally filtered by type.

    Args:
        type: Optional memory type filter (design_doc, project_overview, etc.)

    Returns:
        dict: Success response with list of memory metadata (no content)
            {
                "success": true,
                "memories": [
                    {
                        "id": "uuid",
                        "title": "string",
                        "type": "string"
                    },
                    ...
                ]
            }

    Errors:
        - Project not activated: {"error": "project_not_activated"}
        - Storage error: {"error": "storage_error"}
    """
    try:
        storage_instance = get_storage()
        memories = storage_instance.list_memories(memory_type=type)
        return {"success": True, "memories": [m.to_dict() for m in memories]}
    except ProjectNotActivatedError as e:
        return {"error": e.error_code}
    except Exception as e:
        return {"error": "storage_error"}


@mcp.tool()
def update_memory(memory_id: str, content: str) -> dict:
    """Update the content of an existing memory.

    Only the content field can be updated. Type, title, and ID cannot be changed.

    Args:
        memory_id: UUID of the memory to update
        content: New content in markdown format

    Returns:
        dict: Success response
            {
                "success": true
            }

    Errors:
        - Memory not found: {"error": "memory_not_found"}
        - Project not activated: {"error": "project_not_activated"}
        - Storage error: {"error": "storage_error"}
    """
    try:
        storage_instance = get_storage()
        storage_instance.update_memory(memory_id, content)
        return {"success": True}
    except (MemoryNotFoundError, ProjectNotActivatedError) as e:
        return {"error": e.error_code}
    except Exception as e:
        return {"error": "storage_error"}


@mcp.tool()
def delete_memory(memory_id: str) -> dict:
    """Permanently delete a memory.

    Args:
        memory_id: UUID of the memory to delete

    Returns:
        dict: Success response
            {
                "success": true
            }

    Errors:
        - Memory not found: {"error": "memory_not_found"}
        - Project not activated: {"error": "project_not_activated"}
        - Storage error: {"error": "storage_error"}
    """
    try:
        storage_instance = get_storage()
        storage_instance.delete_memory(memory_id)
        return {"success": True}
    except (MemoryNotFoundError, ProjectNotActivatedError) as e:
        return {"error": e.error_code}
    except Exception as e:
        return {"error": "storage_error"}


def main():
    """Main entry point for the MCP server."""
    mcp.run()


# Entry point for running the server
if __name__ == "__main__":
    main()
