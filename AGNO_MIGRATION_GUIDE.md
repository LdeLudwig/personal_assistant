# Agno Migration Guide: v1.8.0 to v2.4.7

This guide provides step-by-step instructions for migrating the **Personal Notion Agent** project from Agno v1.8.0 to the latest version (v2.4.7).

## Table of Contents

1. [Overview](#overview)
2. [Breaking Changes Summary](#breaking-changes-summary)
3. [Pre-Migration Checklist](#pre-migration-checklist)
4. [Step-by-Step Migration](#step-by-step-migration)
   - [Step 1: Update Dependencies](#step-1-update-dependencies)
   - [Step 2: Update Team Configuration](#step-2-update-team-configuration)
   - [Step 3: Update Agent Parameters](#step-3-update-agent-parameters)
   - [Step 4: Update Tool Decorator Usage](#step-4-update-tool-decorator-usage)
   - [Step 5: Update Instruction Formatting](#step-5-update-instruction-formatting)
   - [Step 6: Consider New Features](#step-6-consider-new-features)
5. [Code Migration Examples](#code-migration-examples)
6. [Testing Checklist](#testing-checklist)
7. [Rollback Plan](#rollback-plan)
8. [References](#references)

---

## Overview

### Current State
- **Current Version**: Agno 1.8.0
- **Target Version**: Agno 2.4.7

### Affected Files
| File | Changes Required |
|------|------------------|
| `pyproject.toml` | Update version constraint |
| `requirements.txt` | Regenerate after update |
| `personal_notion_agent/app/agent_factory.py` | Team mode, Agent parameters |
| `skills/tools/notion_tools.py` | Potential tool decorator updates |
| `skills/tools/telegram_tools.py` | Potential tool decorator updates |

---

## Breaking Changes Summary

| Category | v1.8.0 (Current) | v2.4.7 (Target) | Impact |
|----------|------------------|-----------------|--------|
| Team Mode | `mode="coordinate"` | `respond_directly=True, delegate_to_all_members=False` | **HIGH** |
| Team Members | `agents=[...]` (accepted) | `members=[...]` (required) | Already compliant |
| Storage | `storage=Storage(...)` | `db=PostgresDb(...)` or `db=SqliteDb(...)` | N/A (not used) |
| Session ID | `conversation_id="..."` | `session_id="..."` | N/A (not used) |
| Memory | `memory=Memory(...)` | `enable_user_memories=True` | N/A (not used) |
| Instructions | Wrapped in `<instructions>` tags | No tags by default | **MEDIUM** |
| Knowledge API | `add_content()` | `insert()`, `insert_many()` | N/A (not used) |
| Context vars | `session_state`, `dependencies` | `RunContext` | N/A (not used) |
| Streaming | `stream_intermediate_steps` | `stream_events` | N/A (not used) |
| Yield | `yield_run_response` | `yield_run_output` | N/A (not used) |

---

## Pre-Migration Checklist

- [ ] Create a backup branch: `git checkout -b backup/pre-agno-migration`
- [ ] Ensure all tests pass on current version
- [ ] Review the [Agno Changelog](https://github.com/agno-agi/agno/releases)
- [ ] Check compatibility with other dependencies (Python 3.12+, agentops, etc.)
- [ ] Review custom tool implementations for async compatibility

---

## Step-by-Step Migration

### Step 1: Update Dependencies

#### 1.1 Update `pyproject.toml`

**Before:**
```toml
dependencies = [
    "agno==1.8.0",
    # ... other dependencies
]
```

**After:**
```toml
dependencies = [
    "agno>=2.4.7",
    # ... other dependencies
]
```

#### 1.2 Regenerate `requirements.txt`

```bash
# Using uv (as configured in project)
uv pip compile pyproject.toml -o requirements.txt

# Or using pip-tools
pip-compile pyproject.toml -o requirements.txt

# Install updated dependencies
uv pip sync requirements.txt
# or
pip install -r requirements.txt
```

---

### Step 2: Update Team Configuration

This is the **most critical change**. The `mode` parameter has been replaced with explicit delegation flags.

#### File: `personal_notion_agent/app/agent_factory.py`

**Before (Line 113-125):**
```python
coordinator_agent = Team(
    name="coordinator",
    mode="coordinate",  # DEPRECATED in v2.x
    model=OpenRouter(
        id=self.settings.open_gpt_5,
        api_key=self.settings.open_router_api_key,
        temperature=self.settings.temperature,
        max_tokens=None,
    ),
    members=[notion_agent, telegram_agent, formatter_agent],
    instructions=dedent(coordinator_agent_prompt),
    show_tool_calls=True,
)
```

**After:**
```python
coordinator_agent = Team(
    name="coordinator",
    # Replace mode="coordinate" with explicit flags
    respond_directly=True,
    delegate_to_all_members=False,
    model=OpenRouter(
        id=self.settings.open_gpt_5,
        api_key=self.settings.open_router_api_key,
        temperature=self.settings.temperature,
        max_tokens=None,
    ),
    members=[notion_agent, telegram_agent, formatter_agent],
    instructions=dedent(coordinator_agent_prompt),
    show_tool_calls=True,
)
```

#### Team Mode Mapping Reference

| Old Mode | New Parameters |
|----------|----------------|
| `mode="coordinate"` | `respond_directly=True, delegate_to_all_members=False` |
| `mode="collaborate"` | `respond_directly=False, delegate_to_all_members=True` |
| `mode="route"` | `respond_directly=False, delegate_to_all_members=False` |

---

### Step 3: Update Agent Parameters

Review agent configurations for deprecated parameters. Current implementation uses standard parameters that remain valid.

#### Parameters that remain unchanged:
- `name` - Still supported
- `model` - Still supported
- `instructions` - Still supported
- `tools` - Still supported
- `add_datetime_to_instructions` - Still supported
- `show_tool_calls` - Still supported

#### New optional parameters available in v2.4.7:

```python
Agent(
    name="notion",
    model=OpenRouter(...),
    instructions=dedent(notion_agent_prompt),
    tools=[...],
    add_datetime_to_instructions=True,
    show_tool_calls=True,
    # NEW in v2.x - Optional enhancements
    add_instruction_tags=True,  # Restore v1 behavior if needed
    db=SqliteDb(db_file="tmp/agents.db"),  # Enable persistence
    learning=True,  # Enable learning capabilities
    enable_user_memories=True,  # Enable memory features
)
```

---

### Step 4: Update Tool Decorator Usage

The `@tool` decorator remains largely compatible. However, review for new features:

#### Files:
- `skills/tools/notion_tools.py`
- `skills/tools/telegram_tools.py`

#### Current Implementation (Compatible):
```python
@tool(
    name="find_task_by_id",
    description="Busca uma pagina de tarefa especifica no Notion pelo ID da pagina.",
)
def find_task_by_id(id: str):
    # ...
```

#### New Optional Parameter in v2.4.4+:
```python
@tool(
    name="find_task_by_id",
    description="Busca uma pagina de tarefa especifica no Notion pelo ID da pagina.",
    external_execution_silent=True,  # NEW: Suppress verbose output
)
def find_task_by_id(id: str):
    # ...
```

#### Async Tool Support (v2.4.0+):
If you want to use async tools, Agno now automatically detects and uses them:

```python
@tool(
    name="list_tasks_async",
    description="Lista tarefas de forma assincrona",
)
async def list_tasks_async(name: str):
    # Async implementation
    async with aiohttp.ClientSession() as session:
        # ... async Notion API calls
        pass
```

---

### Step 5: Update Instruction Formatting

In v2.4.0+, instructions are no longer wrapped in `<instructions>` XML tags by default.

#### If your prompts rely on structured tags:

Add `add_instruction_tags=True` to preserve v1 behavior:

```python
Agent(
    name="interpreter",
    instructions=dedent(interpreter_agent_prompt),
    add_instruction_tags=True,  # Preserve v1 XML tag formatting
    # ...
)
```

#### Recommendation:
Test your agents without this flag first. If responses degrade, add the flag.

---

### Step 6: Consider New Features

Agno v2.4.7 introduces powerful new capabilities you may want to adopt:

#### 6.1 Learning Capabilities
```python
from agno.storage.sqlite import SqliteDb

Agent(
    name="notion",
    model=OpenRouter(...),
    db=SqliteDb(db_file="tmp/agents.db"),
    learning=True,  # Agents learn and improve over time
    enable_user_memories=True,
)
```

#### 6.2 Knowledge Protocol
```python
from agno.knowledge import Knowledge
from agno.vectordb import ChromaDb

knowledge = Knowledge(
    vectordb=ChromaDb(path="tmp/knowledge"),
)
knowledge.insert("Your documentation content here")

Agent(
    name="notion",
    knowledge=knowledge,
    # ...
)
```

#### 6.3 Guardrails
```python
from agno.guardrails import Guardrail

Agent(
    name="notion",
    guardrails=[
        Guardrail(
            name="content_filter",
            description="Filter inappropriate content",
        )
    ],
    # ...
)
```

---

## Code Migration Examples

### Complete Agent Factory Migration

**Before (`agent_factory.py` - v1.8.0):**
```python
from agno.agent import Agent
from agno.team import Team
from agno.models.openrouter import OpenRouter

class AgentFactory:
    def create_coordinator_agent(self):
        notion_agent = self.create_notion_agent()
        notion_agent.name = "notion"
        notion_agent.role = "Especialista em gerenciar as tarefas"

        coordinator_agent = Team(
            name="coordinator",
            mode="coordinate",  # OLD API
            model=OpenRouter(...),
            members=[notion_agent, ...],
            instructions=dedent(coordinator_agent_prompt),
            show_tool_calls=True,
        )
        return coordinator_agent
```

**After (`agent_factory.py` - v2.4.7):**
```python
from agno.agent import Agent
from agno.team import Team
from agno.models.openrouter import OpenRouter
# Optional: For persistence
# from agno.storage.sqlite import SqliteDb

class AgentFactory:
    def create_coordinator_agent(self):
        notion_agent = self.create_notion_agent()
        notion_agent.name = "notion"
        notion_agent.role = "Especialista em gerenciar as tarefas"

        coordinator_agent = Team(
            name="coordinator",
            # NEW API: Replace mode with explicit flags
            respond_directly=True,
            delegate_to_all_members=False,
            model=OpenRouter(...),
            members=[notion_agent, ...],
            instructions=dedent(coordinator_agent_prompt),
            show_tool_calls=True,
        )
        return coordinator_agent
```

---

## Testing Checklist

After migration, verify the following:

### Unit Tests
- [ ] All existing unit tests pass
- [ ] Tool decorator functions work correctly
- [ ] Agent creation doesn't throw errors

### Integration Tests
- [ ] Interpreter agent correctly parses user input
- [ ] Coordinator team properly delegates to member agents
- [ ] Notion agent CRUD operations work
- [ ] Telegram agent responds correctly
- [ ] Formatter agent formats output properly

### End-to-End Tests
- [ ] Create a new task via Telegram
- [ ] List tasks with date filtering
- [ ] Update an existing task
- [ ] Multi-step operations (create + update)

### Performance Tests
- [ ] Response times are comparable to v1.8.0
- [ ] No memory leaks during extended operation

---

## Rollback Plan

If issues occur during migration:

### Quick Rollback
```bash
# Revert to backup branch
git checkout backup/pre-agno-migration

# Or revert pyproject.toml and reinstall
git checkout HEAD -- pyproject.toml
uv pip sync requirements.txt
```

### Partial Rollback
If only Team mode causes issues, you can temporarily keep using `mode` (deprecated but may still work):

```python
# This may work as a temporary fallback
coordinator_agent = Team(
    name="coordinator",
    mode="coordinate",  # Deprecated but potentially functional
    # ...
)
```

---

## References

- [Agno PyPI Package](https://pypi.org/project/agno/)
- [Agno GitHub Releases](https://github.com/agno-agi/agno/releases)
- [Agno Official Documentation](https://docs.agno.com)
- [Agno Community](https://community.agno.com/)
- [Agno Agent Framework](https://www.agno.com/agent-framework)
- [Understanding Agno - DigitalOcean](https://www.digitalocean.com/community/conceptual-articles/agno-fast-scalable-multi-agent-framework)

---

## Migration Summary

| Step | File | Action | Priority |
|------|------|--------|----------|
| 1 | `pyproject.toml` | Update version to `>=2.4.7` | Required |
| 2 | `requirements.txt` | Regenerate | Required |
| 3 | `agent_factory.py` | Replace `mode` with delegation flags | **Critical** |
| 4 | `agent_factory.py` | Review Agent parameters | Recommended |
| 5 | `*_tools.py` | Consider async tools | Optional |
| 6 | All agents | Consider `add_instruction_tags` | If needed |
| 7 | All agents | Consider learning/memory features | Optional |

---

**Estimated Migration Time**: This migration involves primarily configuration changes with minimal code refactoring.

**Risk Level**: Medium - The Team mode change is breaking, but the fix is straightforward.

**Compatibility**: Python 3.12+ (current project already compliant)
