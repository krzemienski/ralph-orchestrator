# Ralph Mobile Server - API Reference

Complete documentation of all REST endpoints provided by ralph-mobile-server.

## Base URL

```
http://127.0.0.1:8080       # Local development
http://<server-ip>:8080     # Network access
http://localhost:3000       # Custom port
```

## Authentication

Currently **no authentication required** (local/trusted network only).

Future versions may support:
- API keys
- JWT tokens
- Basic authentication

## Response Format

### Success Response
```json
{
  "data": {...},           // Endpoint-specific payload
  "meta": {                // Optional metadata
    "total": 10,
    "page": 1,
    "limit": 20
  }
}
```

### Error Response
```json
{
  "error": "Session not found",
  "code": "NOT_FOUND",
  "details": "Session id: abc123"
}
```

## HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | Request succeeded |
| 201 | Resource created |
| 204 | No content (deleted successfully) |
| 400 | Bad request (invalid parameters) |
| 404 | Resource not found |
| 409 | Conflict (resource already exists) |
| 500 | Server error |
| 503 | Service unavailable |

## Endpoints

---

## Health Check

### GET /api/health

Check server availability.

**Response**
```
200 OK
"OK"
```

**Example**
```bash
curl http://127.0.0.1:8080/api/health
# Output: OK
```

---

## Sessions

### GET /api/sessions

List all discovered and active Ralph sessions.

**Response**
```json
[
  {
    "id": "abc12345678901234",
    "iteration": 5,
    "hat": "builder",
    "started_at": "2026-02-05T10:30:00Z"
  },
  {
    "id": "def67890123456789",
    "iteration": 2,
    "hat": "planner",
    "started_at": "2026-02-05T09:15:00Z"
  }
]
```

**Fields**
- `id` (string): Unique session identifier
- `iteration` (integer): Current iteration number
- `hat` (string): Current hat name (planner, builder, reviewer, etc.)
- `started_at` (string): ISO 8601 timestamp when session started

**Status Codes**
- 200: Success
- 500: Server error during session discovery

**Example**
```bash
curl http://127.0.0.1:8080/api/sessions

# Response:
[
  {
    "id": "b4c8a9f21e4d5f8c",
    "iteration": 3,
    "hat": "planner",
    "started_at": "2026-02-05T15:30:00.000Z"
  }
]
```

---

### GET /api/sessions/{id}/status

Get detailed status for a specific session.

**Path Parameters**
- `id` (string): Session ID (or first 8 characters)

**Response**
```json
{
  "id": "abc12345678901234",
  "iteration": 5,
  "total": 10,
  "hat": "builder",
  "elapsed_secs": 345,
  "mode": "live"
}
```

**Fields**
- `id` (string): Session identifier
- `iteration` (integer): Current iteration number
- `total` (integer, optional): Total iterations in plan
- `hat` (string): Current hat
- `elapsed_secs` (integer): Seconds since session start
- `mode` (string): "live" (running) | "complete" (finished) | "paused" (paused)

**Status Codes**
- 200: Success
- 404: Session not found

**Example**
```bash
curl http://127.0.0.1:8080/api/sessions/abc12345/status

# Response:
{
  "id": "abc12345678901234",
  "iteration": 5,
  "total": 10,
  "hat": "builder",
  "elapsed_secs": 345,
  "mode": "live"
}
```

---

### POST /api/sessions

Start a new Ralph session.

**Request Body**
```json
{
  "config_path": "presets/tdd-red-green.yml",
  "prompt_path": "prompts/my-task.md",
  "working_dir": "/path/to/working/directory"
}
```

**Fields**
- `config_path` (string): Path to config file relative to project root
- `prompt_path` (string): Path to prompt file relative to project root
- `working_dir` (string, optional): Working directory for ralph process (defaults to current directory)

**Response**
```json
{
  "id": "new_session_id",
  "status": "starting"
}
```

**Status Codes**
- 201: Session created
- 400: Invalid config or prompt path
- 500: Failed to spawn process

**Example**
```bash
curl -X POST http://127.0.0.1:8080/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "config_path": "presets/tdd-red-green.yml",
    "prompt_path": "prompts/feature.md",
    "working_dir": "/home/user/my-project"
  }'

# Response:
{
  "id": "new_abc123_session",
  "status": "starting"
}
```

---

### DELETE /api/sessions/{id}

Stop and terminate a running session.

**Path Parameters**
- `id` (string): Session ID

**Request Body** (empty)

**Response**
```json
{
  "status": "stopped"
}
```

**Status Codes**
- 200: Session stopped
- 404: Session not found
- 500: Failed to terminate process

**Example**
```bash
curl -X DELETE http://127.0.0.1:8080/api/sessions/abc12345

# Response:
{
  "status": "stopped"
}
```

---

### GET /api/sessions/{id}/events

Stream real-time events from a session via Server-Sent Events (SSE).

**Path Parameters**
- `id` (string): Session ID

**Query Parameters**
- `since` (string, optional): ISO 8601 timestamp - only receive events after this time

**Response Headers**
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

**Response Format**
Each event is sent as SSE format:
```
event: workflow
data: {"id":"evt_123","type":"hat.transition","ts":"2026-02-05T10:30:45.123Z","topic":"hat.changed","payload":{"from":"planner","to":"builder"},"hat":"builder"}

event: workflow
data: {"id":"evt_124","type":"tool.call","ts":"2026-02-05T10:30:46.456Z","topic":"tool.invoked","payload":{"tool":"execute_code","args":{"code":"..."}}}

```

**Event Fields**
- `id` (string): Unique event identifier
- `type` (string): Event type
- `ts` (string): ISO 8601 timestamp
- `topic` (string): Event topic
- `payload` (object): Event-specific data
- `hat` (string, optional): Associated hat name

**Status Codes**
- 200: SSE stream established
- 404: Session not found
- 500: Failed to create event stream

**Example**
```bash
curl http://127.0.0.1:8080/api/sessions/abc12345/events

# Output (streaming):
event: workflow
data: {"id":"evt_123","type":"iteration.started","ts":"2026-02-05T10:31:00.000Z","topic":"iteration","payload":{"iteration":1}}

event: workflow
data: {"id":"evt_124","type":"hat.transition","ts":"2026-02-05T10:31:05.000Z","topic":"hat.changed","payload":{"from":"idle","to":"planner"},"hat":"planner"}

# ... more events stream in real-time ...
```

**JavaScript Client Example**
```javascript
const eventSource = new EventSource('http://127.0.0.1:8080/api/sessions/abc12345/events');

eventSource.addEventListener('workflow', (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data);
});

eventSource.addEventListener('error', (event) => {
  console.error('SSE error:', event);
  eventSource.close();
});
```

---

### POST /api/sessions/{id}/emit

Send a custom event to a session.

**Path Parameters**
- `id` (string): Session ID

**Request Body**
```json
{
  "topic": "build.done",
  "payload": {
    "status": "success",
    "output": "Build completed in 2.3s"
  }
}
```

**Fields**
- `topic` (string): Event topic
- `payload` (object, optional): Event payload (can be any JSON value)

**Response**
```json
{
  "success": true,
  "topic": "build.done",
  "timestamp": "2026-02-05T10:31:30.123Z"
}
```

**Status Codes**
- 200: Event emitted
- 404: Session not found
- 500: Failed to emit event

**Example**
```bash
curl -X POST http://127.0.0.1:8080/api/sessions/abc12345/emit \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "review.approved",
    "payload": {
      "reviewer": "alice",
      "notes": "Looks good!"
    }
  }'

# Response:
{
  "success": true,
  "topic": "review.approved",
  "timestamp": "2026-02-05T10:31:30.123Z"
}
```

---

### POST /api/sessions/{id}/pause

Pause a running session.

**Path Parameters**
- `id` (string): Session ID

**Request Body** (empty)

**Response**
```json
{
  "status": "paused"
}
```

**Status Codes**
- 200: Session paused
- 404: Session not found
- 409: Session already paused or not running
- 500: Failed to pause process

**Example**
```bash
curl -X POST http://127.0.0.1:8080/api/sessions/abc12345/pause

# Response:
{
  "status": "paused"
}
```

---

### POST /api/sessions/{id}/resume

Resume a paused session.

**Path Parameters**
- `id` (string): Session ID

**Request Body** (empty)

**Response**
```json
{
  "status": "running"
}
```

**Status Codes**
- 200: Session resumed
- 404: Session not found
- 409: Session not paused
- 500: Failed to resume process

**Example**
```bash
curl -X POST http://127.0.0.1:8080/api/sessions/abc12345/resume

# Response:
{
  "status": "running"
}
```

---

### POST /api/sessions/{id}/steer

Send a steering message to a running session.

**Path Parameters**
- `id` (string): Session ID

**Request Body**
```json
{
  "message": "Use the builder hat for the next iteration"
}
```

**Fields**
- `message` (string): Steering message

**Response**
```json
{
  "status": "delivered",
  "delivered_at": "2026-02-05T10:31:45.123Z"
}
```

**Status Codes**
- 200: Message delivered
- 404: Session not found
- 500: Failed to deliver message

**Example**
```bash
curl -X POST http://127.0.0.1:8080/api/sessions/abc12345/steer \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Focus on test coverage for this feature"
  }'

# Response:
{
  "status": "delivered",
  "delivered_at": "2026-02-05T10:31:45.123Z"
}
```

---

### GET /api/sessions/{id}/scratchpad

Get the session's scratchpad content.

**Path Parameters**
- `id` (string): Session ID

**Response**
```json
{
  "content": "# Session Scratchpad\n\n## Notes\n- Completed test phase\n- Ready for execution\n",
  "updated_at": "2026-02-05T10:31:50.123Z"
}
```

**Fields**
- `content` (string): Scratchpad markdown content
- `updated_at` (string, optional): ISO 8601 timestamp of last update

**Status Codes**
- 200: Success
- 404: Session not found or no scratchpad file

**Example**
```bash
curl http://127.0.0.1:8080/api/sessions/abc12345/scratchpad

# Response:
{
  "content": "# Planning Phase\n\n## Analysis\n- Target: Build authentication system\n- Scope: 5 iterations planned\n",
  "updated_at": "2026-02-05T10:31:50.123Z"
}
```

---

## Configurations

### GET /api/configs

List available configuration files.

**Response**
```json
[
  {
    "path": "presets/tdd-red-green.yml",
    "name": "tdd-red-green",
    "description": "Test-driven development with red-green-refactor cycle"
  },
  {
    "path": "presets/feature-fast-track.yml",
    "name": "feature-fast-track",
    "description": "Rapid feature development with minimal testing"
  }
]
```

**Fields**
- `path` (string): Relative path to config file
- `name` (string): Config name (filename without extension)
- `description` (string): Description from first YAML comment

**Status Codes**
- 200: Success
- 500: Error reading config directory

**Example**
```bash
curl http://127.0.0.1:8080/api/configs

# Response:
[
  {
    "path": "presets/default.yml",
    "name": "default",
    "description": "Default configuration"
  },
  {
    "path": "presets/aggressive.yml",
    "name": "aggressive",
    "description": "Aggressive iteration strategy"
  }
]
```

---

### GET /api/configs/{path}

Get raw content of a configuration file.

**Path Parameters**
- `path` (string): Path to config file (e.g., `presets/tdd-red-green.yml`)

**Response**
```json
{
  "path": "presets/tdd-red-green.yml",
  "content": "# TDD Configuration\nmode: red-green-refactor\niterations: 10\n...",
  "content_type": "application/x-yaml"
}
```

**Status Codes**
- 200: Success
- 404: Config file not found
- 400: Invalid path

**Example**
```bash
curl http://127.0.0.1:8080/api/configs/presets/tdd-red-green.yml

# Response:
{
  "path": "presets/tdd-red-green.yml",
  "content": "# TDD Configuration\n\nmode: red-green-refactor\niterations: 10\nbackends:\n  - claude\n",
  "content_type": "application/x-yaml"
}
```

---

## Prompts

### GET /api/prompts

List available prompt files.

**Response**
```json
[
  {
    "path": "prompts/feature.md",
    "name": "feature",
    "preview": "Build a new authentication system"
  },
  {
    "path": "prompts/refactor/cleanup.md",
    "name": "cleanup",
    "preview": "Remove dead code and simplify modules"
  }
]
```

**Fields**
- `path` (string): Relative path to prompt file
- `name` (string): Prompt name (filename without extension)
- `preview` (string): First line of content, truncated to 50 characters

**Status Codes**
- 200: Success
- 500: Error reading prompts directory

**Example**
```bash
curl http://127.0.0.1:8080/api/prompts

# Response:
[
  {
    "path": "prompts/auth.md",
    "name": "auth",
    "preview": "Implement JWT-based authentication"
  }
]
```

---

### GET /api/prompts/{path}

Get raw content of a prompt file.

**Path Parameters**
- `path` (string): Path to prompt file (e.g., `prompts/feature.md`)

**Response**
```json
{
  "path": "prompts/feature.md",
  "content": "# Build Authentication System\n\n## Requirements\n- JWT tokens\n- Refresh tokens\n...",
  "content_type": "text/markdown"
}
```

**Status Codes**
- 200: Success
- 404: Prompt file not found
- 400: Invalid path

**Example**
```bash
curl http://127.0.0.1:8080/api/prompts/prompts/auth.md

# Response:
{
  "path": "prompts/auth.md",
  "content": "# Implement JWT Authentication\n\n## Goals\n1. Add JWT token generation\n2. Add token validation middleware\n3. Add refresh token rotation\n",
  "content_type": "text/markdown"
}
```

---

## Skills

### GET /api/skills

List all available skills.

**Response**
```json
[
  {
    "name": "write-code",
    "description": "Generate and execute code",
    "tags": ["development", "coding"],
    "hats": ["builder", "architect"],
    "backends": ["claude"],
    "auto_inject": true,
    "source": "built-in"
  },
  {
    "name": "run-tests",
    "description": "Execute test suite",
    "tags": ["testing", "validation"],
    "hats": ["reviewer"],
    "backends": ["built-in"],
    "auto_inject": true,
    "source": "built-in"
  }
]
```

**Fields**
- `name` (string): Unique skill identifier
- `description` (string): Human-readable description
- `tags` (array): Skill tags/categories
- `hats` (array): Hats that can use this skill
- `backends` (array): Backend systems this skill works with
- `auto_inject` (boolean): Whether skill is automatically injected
- `source` (string): "built-in" or "file"

**Status Codes**
- 200: Success
- 500: Failed to load skills

**Example**
```bash
curl http://127.0.0.1:8080/api/skills

# Response:
[
  {
    "name": "execute",
    "description": "Execute shell commands",
    "tags": ["execution"],
    "hats": ["builder"],
    "backends": ["*"],
    "auto_inject": true,
    "source": "built-in"
  }
]
```

---

### GET /api/skills/{name}

Get metadata for a specific skill.

**Path Parameters**
- `name` (string): Skill name

**Response**
```json
{
  "name": "write-code",
  "description": "Generate and execute code",
  "tags": ["development", "coding"],
  "hats": ["builder", "architect"],
  "backends": ["claude"],
  "auto_inject": true,
  "source": "built-in"
}
```

**Status Codes**
- 200: Success
- 404: Skill not found

**Example**
```bash
curl http://127.0.0.1:8080/api/skills/write-code

# Response:
{
  "name": "write-code",
  "description": "Generate and execute code",
  "tags": ["development", "coding"],
  "hats": ["builder", "architect"],
  "backends": ["claude"],
  "auto_inject": true,
  "source": "built-in"
}
```

---

### POST /api/skills/{name}/load

Load full skill content wrapped in XML format.

**Path Parameters**
- `name` (string): Skill name

**Request Body** (empty)

**Response**
```json
{
  "name": "write-code",
  "content": "<skill>\n<name>write-code</name>\n<description>Generate and execute code</description>\n<content>\n# Skill Implementation\n...\n</content>\n</skill>"
}
```

**Fields**
- `name` (string): Skill name
- `content` (string): XML-wrapped skill content

**Status Codes**
- 200: Success
- 404: Skill not found
- 500: Failed to load skill

**Example**
```bash
curl -X POST http://127.0.0.1:8080/api/skills/write-code/load

# Response:
{
  "name": "write-code",
  "content": "<skill>\n<name>write-code</name>\n<description>Generate and execute code</description>\n<content>\n## Usage\nDescribe code to generate...\n</content>\n</skill>"
}
```

---

## Hats

### GET /api/hats

List all available hats (decision-making roles).

**Response**
```json
[
  {
    "name": "planner",
    "description": "Plans the solution strategy",
    "color": "#00d9ff",
    "emoji": "📋"
  },
  {
    "name": "builder",
    "description": "Implements the solution",
    "color": "#c71585",
    "emoji": "🔨"
  },
  {
    "name": "reviewer",
    "description": "Reviews and validates work",
    "color": "#39ff14",
    "emoji": "✓"
  }
]
```

**Fields**
- `name` (string): Hat identifier
- `description` (string): Purpose and responsibility
- `color` (string): Hex color code for UI
- `emoji` (string): Visual representation

**Status Codes**
- 200: Success

**Example**
```bash
curl http://127.0.0.1:8080/api/hats

# Response:
[
  {
    "name": "planner",
    "description": "Plans the solution strategy",
    "color": "#00d9ff",
    "emoji": "📋"
  },
  {
    "name": "builder",
    "description": "Implements the solution",
    "color": "#c71585",
    "emoji": "🔨"
  }
]
```

---

## Host Metrics

### GET /api/host/metrics

Get current system metrics (CPU, memory, disk).

**Response**
```json
{
  "cpu_percent": 23.5,
  "memory_percent": 45.2,
  "disk_percent": 67.8,
  "load_avg": [1.23, 1.45, 1.67],
  "timestamp": "2026-02-05T10:32:00.000Z"
}
```

**Fields**
- `cpu_percent` (float): CPU usage 0-100%
- `memory_percent` (float): Memory usage 0-100%
- `disk_percent` (float): Disk usage 0-100%
- `load_avg` (array): 1min, 5min, 15min load averages
- `timestamp` (string): ISO 8601 timestamp

**Status Codes**
- 200: Success
- 500: Failed to retrieve metrics

**Example**
```bash
curl http://127.0.0.1:8080/api/host/metrics

# Response:
{
  "cpu_percent": 15.3,
  "memory_percent": 32.1,
  "disk_percent": 55.0,
  "load_avg": [1.1, 1.2, 1.3],
  "timestamp": "2026-02-05T10:32:00.000Z"
}
```

---

## Error Handling

### Common Error Codes

| Code | Status | Meaning |
|------|--------|---------|
| `NOT_FOUND` | 404 | Session, config, or prompt not found |
| `BAD_REQUEST` | 400 | Invalid parameters or malformed JSON |
| `ALREADY_EXISTS` | 409 | Resource already exists |
| `INTERNAL_ERROR` | 500 | Server error during operation |
| `UNAVAILABLE` | 503 | Service temporarily unavailable |

### Error Response Example

```json
{
  "error": "Session not found",
  "code": "NOT_FOUND",
  "details": "Session id: unknown_id"
}
```

---

## Rate Limiting

Currently **no rate limiting** is implemented.

Future versions may implement:
- Per-IP rate limits
- Per-session connection limits
- Burst allowances for control operations

---

## WebSocket Support

Currently **SSE only** for event streaming.

WebSocket support may be added in future versions:
- Bidirectional communication
- Lower latency
- Better mobile performance
- Persistent connection

---

## Backward Compatibility

The API follows semantic versioning:

- **Major** (1.x → 2.x): Breaking changes
- **Minor** (1.0 → 1.1): New endpoints/fields
- **Patch** (1.0.0 → 1.0.1): Bug fixes

Fields are added conservatively:
- Old fields never removed
- New optional fields may appear
- Clients should ignore unknown fields

---

## Testing the API

### Using cURL

```bash
# List sessions
curl http://127.0.0.1:8080/api/sessions

# Get session status
curl http://127.0.0.1:8080/api/sessions/{id}/status

# Start new session
curl -X POST http://127.0.0.1:8080/api/sessions \
  -H "Content-Type: application/json" \
  -d '{"config_path":"presets/default.yml","prompt_path":"prompts/test.md"}'

# Stream events
curl http://127.0.0.1:8080/api/sessions/{id}/events
```

### Using Python

```python
import requests
import json

BASE_URL = "http://127.0.0.1:8080/api"

# List sessions
sessions = requests.get(f"{BASE_URL}/sessions").json()
print(f"Found {len(sessions)} sessions")

# Get status
session_id = sessions[0]["id"]
status = requests.get(f"{BASE_URL}/sessions/{session_id}/status").json()
print(f"Session {session_id}: {status['hat']} (iteration {status['iteration']})")

# Start new session
new_session = requests.post(f"{BASE_URL}/sessions", json={
    "config_path": "presets/default.yml",
    "prompt_path": "prompts/test.md"
}).json()
print(f"Started session {new_session['id']}")
```

### Using JavaScript

```javascript
const BASE_URL = "http://127.0.0.1:8080/api";

// List sessions
async function getSessions() {
  const response = await fetch(`${BASE_URL}/sessions`);
  return await response.json();
}

// Stream events
function streamEvents(sessionId) {
  const eventSource = new EventSource(`${BASE_URL}/sessions/${sessionId}/events`);

  eventSource.addEventListener('workflow', (event) => {
    const data = JSON.parse(event.data);
    console.log('Event:', data);
  });
}

// Example
getSessions().then(sessions => {
  console.log(`Found ${sessions.length} sessions`);
  if (sessions.length > 0) {
    streamEvents(sessions[0].id);
  }
});
```

---

## Migration Guide

### Upgrading from v1 to v2

No breaking changes currently planned. New versions will:
1. Add new endpoints under `/api/v2/`
2. Keep existing `/api/` endpoints working
3. Provide migration guide for new features

---

## See Also

- [Ralph Mobile Server README](./README.md)
- [iOS App Guide](../ios/README.md)
- [Ralph Orchestrator Documentation](../../README.md)
