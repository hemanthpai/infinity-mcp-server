# Infinity MCP Server

A structured memory system for AI coding agents, implemented as a Model Context Protocol (MCP) server.

## Overview

Infinity MCP Server provides a minimal, stateful memory system to store, retrieve, update, and delete structured project memories. It replaces unstructured markdown files with a structured, project-scoped system that improves traceability, reduces noise, and enables long-term codebase hygiene.

### Key Features

- **Project-scoped**: Each project has isolated memories stored in `.infinity/` directory
- **6 simple tools**: Minimal API surface for maximum utility
- **7 memory types**: Fixed set of structured memory categories
- **No file clutter**: All memories stored in a single `.infinity/memories.json` file
- **Atomic operations**: Safe concurrent access with atomic file writes
- **Easy installation**: Install via `uvx` with a single command

## Quick Start

### Installation with Claude Code

```bash
claude mcp add infinity -- uvx --from git+https://github.com/hemanthpai/infinity-mcp-server infinity-mcp-server
```

### Installation with uvx

```bash
# Run directly without installation
uvx --from git+https://github.com/hemanthpai/infinity-mcp-server infinity-mcp-server

# Or install globally
uvx --from git+https://github.com/hemanthpai/infinity-mcp-server infinity-mcp-server
```

### Manual Installation

```bash
# Clone the repository
git clone https://github.com/hemanthpai/infinity-mcp-server.git
cd infinity-mcp-server

# Install the package
pip install -e .

# For development (includes pytest)
pip install -e ".[dev]"
```

## MCP Configuration

Add to your MCP client configuration (e.g., `claude_desktop_config.json` or similar):

```json
{
  "mcpServers": {
    "infinity": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/hemanthpai/infinity-mcp-server",
        "infinity-mcp-server"
      ],
      "description": "Structured memory system for AI coding agents"
    }
  }
}
```

## Usage

### Running the Server

```bash
# If installed via pip
infinity-mcp-server

# Or run as module
python -m infinity_mcp_server.server

# Or run directly with uvx
uvx --from git+https://github.com/hemanthpai/infinity-mcp-server infinity-mcp-server
```

### MCP Tools

#### 1. `activate_project`

Activate the current project. **Must be called first before any other operations.**

**Parameters**: None

**Returns**:
```json
{
  "success": true,
  "project_id": "uuid-string"
}
```

**Example**:
```python
from infinity_mcp_server.server import activate_project

result = activate_project()
print(result)  # {"success": true, "project_id": "..."}
```

#### 2. `store_memory`

Create a new memory.

**Parameters**:
- `title` (str): Memory title (required, non-empty)
- `type` (str): Memory type - one of: `design_doc`, `project_overview`, `implementation_plan`, `progress_tracker`, `test_plan`, `instructions`, `rules`, `analysis`
- `content` (str): Memory content in markdown format

**Returns**:
```json
{
  "success": true,
  "memory_id": "uuid-string"
}
```

**Example**:
```python
from infinity_mcp_server.server import store_memory

result = store_memory(
    title="API Design",
    type="design_doc",
    content="# API Design\n\nREST API with JSON responses..."
)
print(result)  # {"success": true, "memory_id": "..."}
```

#### 3. `get_memory`

Retrieve a memory by its ID.

**Parameters**:
- `memory_id` (str): UUID of the memory

**Returns**:
```json
{
  "success": true,
  "memory": {
    "id": "uuid",
    "title": "string",
    "type": "string",
    "content": "string",
    "created_at": "ISO8601",
    "updated_at": "ISO8601 or null"
  }
}
```

#### 4. `list_memories`

List all memories, optionally filtered by type.

**Parameters**:
- `type` (str, optional): Filter by memory type

**Returns**:
```json
{
  "success": true,
  "memories": [
    {
      "id": "uuid",
      "title": "string",
      "type": "string"
    }
  ]
}
```

**Note**: Content is NOT included in list results to minimize token usage.

#### 5. `update_memory`

Update the content of an existing memory.

**Parameters**:
- `memory_id` (str): UUID of the memory
- `content` (str): New content

**Returns**:
```json
{
  "success": true
}
```

**Note**: Only content can be updated. Type, title, and ID are immutable.

#### 6. `delete_memory`

Permanently delete a memory.

**Parameters**:
- `memory_id` (str): UUID of the memory

**Returns**:
```json
{
  "success": true
}
```

## Memory Types

The following 7 memory types are supported (fixed set, no custom types allowed):

| Type | Purpose |
|------|---------|
| `design_doc` | Technical design for a feature or set of features |
| `project_overview` | Evolving high-level summary of project state |
| `implementation_plan` | Step-by-step plan to implement a design doc |
| `progress_tracker` | Fine-grained task list tracking implementation progress |
| `test_plan` | Detailed plan for testing features and edge cases |
| `instructions` | How to build, run, test the project; code style rules |
| `rules` | User-provided constraints or preferences for code modifications |
| `analysis` | Preliminary code review or investigation |

## Error Handling

All errors are returned as JSON objects with an `error` key:

| Error Code | Description |
|------------|-------------|
| `invalid_memory_type` | Memory type not in allowed list |
| `missing_required_field` | Required field (title, content, memory_id) missing |
| `project_not_activated` | `activate_project` not called before operation |
| `memory_not_found` | Memory with given UUID doesn't exist |
| `storage_error` | File I/O error (e.g., permissions) |

**Example**:
```json
{
  "error": "memory_not_found"
}
```

## Project Structure

```
infinity-mcp-server/
├── src/
│   └── infinity_mcp_server/
│       ├── __init__.py          # Package initialization
│       ├── models.py            # Data models and validation
│       ├── storage.py           # Storage layer (CRUD operations)
│       └── server.py            # MCP server with tools
├── tests/
│   ├── __init__.py
│   ├── test_storage.py          # Unit tests for storage layer
│   └── test_integration.py      # Integration tests (TC1-TC10)
├── .gitignore
├── LICENSE
├── pyproject.toml
└── README.md
```

## Storage Format

Memories are stored in `.infinity/memories.json`:

```json
{
  "project_id": "uuid-123",
  "memories": [
    {
      "id": "uuid-a",
      "title": "API Design",
      "type": "design_doc",
      "content": "# API Design\n\nDetails...",
      "created_at": "2024-04-01T10:00:00Z",
      "updated_at": "2024-04-05T14:30:00Z"
    }
  ]
}
```

The `.infinity/` directory is automatically created in your project's current working directory and should be added to `.gitignore`.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_storage.py

# Run specific test
pytest tests/test_integration.py::TestAcceptanceCriteria::test_tc1_activate_project_creates_infinity_dir
```

### Test Coverage

The project includes:
- **22 unit tests** for the storage layer (test_storage.py)
- **15 integration tests** covering all acceptance criteria (test_integration.py)
- **Total: 37 tests** with 100% pass rate

All 10 acceptance criteria from the PRD are validated:
- TC1: activate_project creates .infinity/project_id
- TC2: activate_project loads existing project ID
- TC3: store_memory with valid type saves correctly
- TC4: store_memory rejects invalid types
- TC5: get_memory validation
- TC6: list_memories returns metadata only
- TC7: list_memories filters by type
- TC8: update_memory updates content only
- TC9: delete_memory removes entry
- TC10: Project isolation (different directories)

## Design Principles

### KISS (Keep It Simple, Stupid)

- Minimal dependencies (only MCP SDK + standard library)
- Single JSON file storage (no database)
- Fixed set of 7 memory types (no custom types)
- 6 simple tools (no complex queries or search)
- Atomic file operations (temp file + rename)

### Project Scoping

- Each project is identified by its current working directory
- `.infinity/` folder is created in the CWD only
- Projects are completely isolated (no shared memories)
- Session state is maintained in memory during agent session

### Atomic Operations

- All file writes use temp file + atomic rename
- No partial writes or corrupted states
- Safe for concurrent access within same process

## Integration with AI Agents

### Claude Code / Cline / Roo / Kilo Code

AI agents should:

1. Call `activate_project()` at the start of each session
2. Use `store_memory()` to create structured memories instead of markdown files
3. Use `list_memories()` to discover existing memories
4. Use `get_memory()` to retrieve full memory content
5. Use `update_memory()` to evolve memories (e.g., project_overview)
6. Use `delete_memory()` to remove obsolete memories (e.g., completed implementation_plan)

### Best Practices

- Always activate project before other operations
- Use `project_overview` to maintain a living summary
- Delete `implementation_plan` memories after implementation is complete
- Update `progress_tracker` as tasks are completed
- Keep `rules` and `instructions` up to date

## Example Usage

See [example_usage.py](example_usage.py) for a complete demonstration of all features.

Run the example:
```bash
python example_usage.py
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Run tests (`pytest`)
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
5. Push to the branch (`git push origin feature/AmazingFeature`)
6. Open a Pull Request

## Support

- **Issues**: https://github.com/hemanthpai/infinity-mcp-server/issues
- **Discussions**: https://github.com/hemanthpai/infinity-mcp-server/discussions

## Acknowledgments

Built for AI coding agents using the [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic.
