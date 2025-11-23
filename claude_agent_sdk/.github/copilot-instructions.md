# GitHub Copilot Instructions for Claude Agent SDK Tutorial

This repository is a tutorial series for building AI agents using the `claude-agent-sdk`. It demonstrates progressive complexity from simple research agents to enterprise-grade multi-agent systems.

## Project Architecture & Concepts

- **Agent Structure**: Agents are built using `ClaudeSDKClient` and configured via `ClaudeAgentOptions`.
- **Configuration-as-Code**: The `.claude/` directory is central to agent behavior.
  - `.claude/agents/`: Defines subagents (e.g., `financial-analyst.md`).
  - `.claude/commands/`: Defines custom slash commands (e.g., `/budget-impact`).
  - `.claude/output-styles/`: Defines response templates.
  - `.claude/hooks/`: Scripts triggered by agent events.
- **Context & Memory**: `CLAUDE.md` files in agent directories provide persistent domain knowledge and instructions.
- **Tooling**:
  - **Built-in**: `WebSearch`, `Read`, `Write`, `Edit`, `Bash`.
  - **Task Tool**: Used for delegating work to subagents.
  - **MCP (Model Context Protocol)**: Used for external integrations (Git, GitHub), often running in Docker.

## Developer Workflow

- **Dependency Management**: Uses `uv`. Run `uv sync` to install dependencies.
- **Execution**: Primary interaction is through Jupyter Notebooks (`.ipynb`).
- **Environment**: Requires `.env` with `ANTHROPIC_API_KEY` and optionally `GITHUB_TOKEN`.
- **Testing**: No formal test suite. Validation is done by running the notebooks or agent scripts directly.

## Coding Conventions

### Agent Initialization
Always use `async` context managers for the client. Set `cwd` explicitly to the agent's directory to ensure it finds its local resources (`scripts/`, `financial_data/`, etc.).

```python
import os
from claude_agent_sdk import ClaudeAgentOptions, ClaudeSDKClient

async def run_agent():
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-5",
        allowed_tools=["Task", "Bash", "WebSearch", "Read"],
        cwd=os.path.dirname(os.path.abspath(__file__)), # Critical for relative paths
        system_prompt="...",
        permission_mode="default" # "default", "plan", or "acceptEdits"
    )

    async with ClaudeSDKClient(options=options) as agent:
        await agent.query(prompt="Analyze the Q2 budget")
        async for msg in agent.receive_response():
            # Handle streaming activity
            pass
```

### Activity Handling
Implement activity handlers to provide real-time feedback during agent execution.

```python
def print_activity(msg):
    if hasattr(msg, "content") and msg.content:
        # Extract and print tool usage or thinking
        pass
```

### Subagent Delegation
Define subagents in `.claude/agents/*.md` and enable the `Task` tool in the parent agent's options. The parent agent will automatically use `Task` to delegate relevant work.

### Python Scripts as Tools
Place utility scripts in a `scripts/` directory within the agent's folder. Agents can execute these using the `Bash` tool.
- Example: `python scripts/financial_forecast.py`

## Key Files
- `claude_agent_sdk/chief_of_staff_agent/agent.py`: Reference implementation of a complex agent.
- `claude_agent_sdk/utils/agent_visualizer.py`: Helpers for visualizing agent activity.
- `claude_agent_sdk/pyproject.toml`: Project dependencies.
