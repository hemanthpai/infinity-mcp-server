# **PRD: Structured Memory System (MCP Server) for AI Coding Agents**

> **Version**: 1.0  
> **Author**: Hemanth Pai 
> **Date**: November 2025 
> **Target Audience**: AI Coding Agent (e.g., Claude Code, Cline, Roo, Kilo Code)  
> **Goal**: Replace unstructured markdown files with a structured, project-scoped memory system to improve traceability, reduce noise, and enable long-term codebase hygiene.

---

## **1. Problem Statement**

Currently, AI coding agents create numerous markdown files (e.g., `design_doc.md`, `progress_tracker.md`) directly in the project directory. Over time:

- File clutter explodes, making it hard to distinguish active vs. obsolete documents.
- No clear lifecycle management: e.g., `ImplementationPlan.md` should be deleted after implementation; `ProjectOverview.md` must be updated on every change.
- No project isolation: agents working across multiple projects risk cross-contaminating memories.
- No consistent API or structure to retrieve, update, or delete memories programmatically.

**Result**: Reduced agent reliability, increased cognitive load, and degraded long-term project maintainability.

---

## **2. Solution Overview**

Build an **MCP (Model Control Protocol) Server** that provides a minimal, stateful memory system to store, retrieve, update, and delete structured project memories. All interactions are scoped per project via an `activate_project` call.

- **No files written to disk** except for internal storage (see “Implementation Notes”).
- Memories are stored as structured JSON entries with UUIDs, titles, types, and content.
- Only **6 tools** are exposed — minimal token usage, maximum utility.
- All memory types are predefined and strictly enforced.

---

## **3. Core Requirements**

### ✅ **3.1 Memory Types (Fixed Set)**

Only the following 7 memory types are allowed. No new types may be created.

| Type | Purpose |
|------|---------|
| `design_doc` | Technical design for a feature or set of features |
| `project_overview` | Evolving high-level summary of project state (must be updated on major changes) |
| `implementation_plan` | Step-by-step plan to implement a design doc; often includes TODOs |
| `progress_tracker` | Fine-grained task list (e.g., checklist) tracking implementation progress |
| `test_plan` | Detailed plan for testing features, edge cases, and system behavior |
| `instructions` | How to build, run, test the project; code style rules |
| `rules` | User-provided constraints or preferences for code modifications (e.g., “never use async/await”) |
| `analysis` | Preliminary code review or investigation to inform next steps (pre-design) |

> ⚠️ **Enforcement**: Any attempt to create/update a memory with an invalid type must return `400 Bad Request`.

---

### ✅ **3.2 Tools (API Endpoints)**

Must use modern MCP Frameworks (current as of November 2025). Input/output must be valid JSON.

#### **3.2.1 `activate_project`**

- **Purpose**: Scope all subsequent memory operations to the current project.
- **Trigger**: Must be called at the start of every new session. None of the other tools should work until this tool has been called. If another tool is called before this one, an error message indicating this requirement must be sent back to the agent.
- **Logic**:
  - Check for a hidden folder `.infinity` in the **current working directory (CWD)**.
    - If it exists → load project UUID from `.infinity/project_id`.
    - If not exist → generate a new UUID (v4), create `.infinity/` directory, write `project_id` file.
  - Store the project UUID in **session memory** (in-memory state for this agent session).
- **Input**: None
- **Output**: `{ "success": true, "project_id": "<uuid>" }`
- **Error**: If `.infinity` folder cannot be created (e.g., permissions), return `{ "error": "cannot_create_project_dir" }`
- **Important**: This is the **only** tool that does not require a project ID. All other tools assume activation has occurred.

#### **3.2.2 `store_memory`**

- **Purpose**: Create a new memory.
- **Input**:
  ```json
  {
    "title": "string",
    "type": "design_doc|project_overview|...|analysis",
    "content": "string (valid markdown)"
  }
  ```
- **Output**:
  ```json
  {
    "success": true,
    "memory_id": "<uuid>"
  }
  ```
- **Rules**:
  - Title must be non-empty.
  - Type must be from allowed list.
  - Content can be empty string (`""`), but not null.
  - On success: Store as `{ "id": "<uuid>", "title": "...", "type": "...", "content": "...", "created_at": "ISO8601" }` in project-specific store.
  - On duplicate title + type → allow it (title is not unique, only UUID is).

#### **3.2.3 `get_memory`**

- **Purpose**: Retrieve a single memory by UUID.
- **Input**:
  ```json
  { "memory_id": "<uuid>" }
  ```
- **Output**:
  ```json
  {
    "success": true,
    "memory": {
      "id": "<uuid>",
      "title": "string",
      "type": "string",
      "content": "string",
      "created_at": "ISO8601"
    }
  }
  ```
- **Error**: If UUID not found → `{ "error": "memory_not_found" }`

#### **3.2.4 `list_memories`**

- **Purpose**: List all memories, optionally filtered by type.
- **Input** (optional):
  ```json
  { "type": "design_doc" }  // optional filter
  ```
- **Output**:
  ```json
  {
    "success": true,
    "memories": [
      {
        "id": "<uuid>",
        "title": "string",
        "type": "string"
      },
      ...
    ]
  }
  ```
- **Note**: Do not return `content` — only metadata to minimize token usage.

#### **3.2.5 `update_memory`**

- **Purpose**: Update content of an existing memory.
- **Input**:
  ```json
  {
    "memory_id": "<uuid>",
    "content": "string (new markdown content)"
  }
  ```
- **Output**:
  ```json
  { "success": true }
  ```
- **Rules**:
  - Must update only the `content` field.
  - Cannot change `type`, `title`, or `id`.
  - If memory not found → `{ "error": "memory_not_found" }`
  - `updated_at` field may be added internally (optional).

#### **3.2.6 `delete_memory`**

- **Purpose**: Permanently remove a memory.
- **Input**:
  ```json
  { "memory_id": "<uuid>" }
  ```
- **Output**:
  ```json
  { "success": true }
  ```
- **Error**: If UUID not found → `{ "error": "memory_not_found" }`

---

## **4. Project Scoping & Session Management**

- **Project Identity**: Determined by the **current working directory (CWD)** where the agent is invoked.
- **Storage Location**: `.infinity/` folder in CWD (hidden, ignored by git).
- **Storage Format**: A single JSON file at `.infinity/memories.json` containing:
  ```json
  {
    "project_id": "uuid-123",
    "memories": [
      {
        "id": "uuid-a",
        "title": "API Design",
        "type": "design_doc",
        "content": "# ...",
        "created_at": "2024-04-01T10:00:00Z",
        "updated_at": "2024-04-05T14:30:00Z"
      },
      ...
    ]
  }
  ```
- **Session State**: The agent must maintain `project_id` in memory during its session. If the session ends, it must re-call `activate_project` on next run.
- **Cross-project safety**: If agent is invoked from a different directory, `activate_project` will create/load a new project context. Memories are **never** shared between projects.

> ✅ **Critical**: The agent must never write `.infinity` to other directories. Only CWD.

---

## **5. Error Handling & Validation**

| Scenario | Response |
|--------|----------|
| Invalid memory type | `{ "error": "invalid_memory_type" }` |
| Missing required field (`title`, `content`, `memory_id`) | `{ "error": "missing_required_field" }` |
| Project not activated before calling any tool except `activate_project` | `{ "error": "project_not_activated" }` |
| File I/O error (e.g., permissions) | `{ "error": "storage_error" }` |
| Malformed JSON input | `{ "error": "invalid_json" }` |

All errors must be JSON-formatted and include a machine-readable `error` key.

---

## **6. Non-Goals**

- ❌ Do not implement versioning or history of memories.
- ❌ Do not implement search by content (only type/title filter).
- ❌ Do not expose a web UI or CLI — this is for AI agent consumption only.
- ❌ Do not sync across devices or cloud.

---

## **7. Acceptance Criteria (Test Cases)**

The implementation is complete when the following are verified:

| Test | Description |
|------|-------------|
| TC1 | `activate_project` creates `.infinity/project_id` on first call in new dir |
| TC2 | `activate_project` loads existing project ID from `.infinity/project_id` on second call |
| TC3 | `store_memory` with valid type → returns UUID and saves to `.infinity/memories.json` |
| TC4 | `store_memory` with invalid type → rejects with error |
| TC5 | `get_memory` returns correct content for valid UUID; rejects with error on invalid |
| TC6 | `list_memories` returns list of {id, title, type} only; no content |
| TC7 | `list_memories` with `type=design_doc` filters correctly |
| TC8 | `update_memory` updates content but not type/title → success; error if UUID missing |
| TC9 | `delete_memory` removes entry from `.infinity/memories.json` → success |
| TC10 | Agent cannot access memories from other projects (different CWD) |

---

## **8. Implementation Notes for Agent**

- Use Python, Node.js, or your preferred language — but ensure **no external dependencies** beyond standard library.
- Store `.infinity/memories.json` as a **single file**, read/written atomically (use `json.load()` + `json.dump()` with temp file + rename to avoid corruption).
- Always validate input types strictly.
- Use `uuid.uuid4()` (Python) or equivalent for UUID generation.
- If agent crashes mid-operation, recovery is handled by reloading `.infinity/memories.json` on next `activate_project`.
- **Do not** write any markdown files to the project root.

---

## **9. Future Considerations**

> These are NOT part of this PRD, but may be considered later:
- Semantic search for memories
- Export to PDF/HTML (for human review)

---