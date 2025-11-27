import base64
import html
import pprint
from typing import Any

# Initialize optional dependencies as Any to satisfy linters/mypy
HTML: Any = None
display: Any = None
pd: Any = None

try:
    import pandas as pd
except ImportError:
    pass

try:
    from IPython.display import HTML, display
except ImportError:

    def display(obj: Any) -> None:
        pass

    class _HTML:
        def __init__(self, data: Any):
            self.data = data

    HTML = _HTML


# Box-drawing configuration constants
BOX_WIDTH = 58  # Width for main conversation boxes
SUBAGENT_WIDTH = 54  # Width for subagent delegation blocks (slightly narrower for visual hierarchy)

# Box-drawing characters for clean visual formatting
BOX_TOP = "╭" + "─" * BOX_WIDTH + "╮"
BOX_BOTTOM = "╰" + "─" * BOX_WIDTH + "╯"
BOX_DIVIDER = "├" + "─" * BOX_WIDTH + "┤"
BOX_SIDE = "│"
SUBAGENT_TOP = "┌" + "─" * SUBAGENT_WIDTH + "┐"
SUBAGENT_BOTTOM = "└" + "─" * SUBAGENT_WIDTH + "┘"
SUBAGENT_SIDE = "│"


# Track subagent state for activity display
# WARNING: This global state is NOT thread-safe. If using this module in concurrent
# scenarios (e.g., multiple asyncio tasks processing different conversations simultaneously),
# each task should call reset_activity_context() before starting and be aware that
# interleaved operations may produce incorrect subagent tracking. For thread-safe usage,
# consider passing context explicitly or using contextvars.
_subagent_context: dict[str, Any] = {
    "active": False,
    "name": None,
    "depth": 0,
}


def print_activity(msg: Any) -> None:
    """
    Print activity with enhanced subagent visibility.

    Shows:
    - Main agent tool usage with 🤖
    - Subagent invocations with 🚀 and subagent name
    - Subagent tool usage with indented 📎
    """
    global _subagent_context

    if "Assistant" in msg.__class__.__name__:
        # Check if content exists and has elements
        if hasattr(msg, "content") and msg.content:
            first_block = msg.content[0]
            tool_name = first_block.name if hasattr(first_block, "name") else None

            if tool_name == "Task":
                # Extract subagent details from the Task tool input
                if hasattr(first_block, "input") and first_block.input:
                    subagent_type = first_block.input.get("subagent_type", "unknown")
                    description = first_block.input.get("description", "")
                    _subagent_context["active"] = True
                    _subagent_context["name"] = subagent_type
                    _subagent_context["depth"] += 1

                    print(f"🚀 Delegating to subagent: {subagent_type}")
                    if description:
                        print(f"   └─ Task: {description}")
                else:
                    print("🚀 Delegating to subagent...")
            elif tool_name:
                # Check if we're inside a subagent context
                if _subagent_context["active"]:
                    indent = "   " * _subagent_context["depth"]
                    print(f"{indent}📎 [{_subagent_context['name']}] Using: {tool_name}()")
                else:
                    print(f"🤖 Using: {tool_name}()")
            else:
                if _subagent_context["active"]:
                    indent = "   " * _subagent_context["depth"]
                    print(f"{indent}📎 [{_subagent_context['name']}] Thinking...")
                else:
                    print("🤖 Thinking...")
        else:
            if _subagent_context["active"]:
                indent = "   " * _subagent_context["depth"]
                print(f"{indent}📎 [{_subagent_context['name']}] Thinking...")
            else:
                print("🤖 Thinking...")

    elif "User" in msg.__class__.__name__:
        # Check if this is a Task tool result (subagent completed)
        if hasattr(msg, "content") and msg.content:
            for result in msg.content if isinstance(msg.content, list) else [msg.content]:
                if isinstance(result, dict) and result.get("type") == "tool_result":
                    # Try to detect if this was a Task result
                    content = result.get("content", "")
                    if isinstance(content, str) and ("subagent" in content.lower() or
                                                      _subagent_context["active"]):
                        if _subagent_context["active"]:
                            indent = "   " * _subagent_context["depth"]
                            print(f"{indent}✅ Subagent [{_subagent_context['name']}] completed")
                            _subagent_context["depth"] = max(0, _subagent_context["depth"] - 1)
                            if _subagent_context["depth"] == 0:
                                _subagent_context["active"] = False
                                _subagent_context["name"] = None
                        else:
                            print("✓ Task completed")
                        return

        if _subagent_context["active"]:
            indent = "   " * _subagent_context["depth"]
            print(f"{indent}✓ Tool completed")
        else:
            print("✓ Tool completed")


def reset_activity_context() -> None:
    """Reset the subagent tracking context. Call before starting a new query."""
    global _subagent_context
    _subagent_context = {
        "active": False,
        "name": None,
        "depth": 0,
    }


def print_final_result(messages: list[Any]) -> None:
    """Print the final agent result and cost information"""
    if not messages:
        return

    # Get the result message (last message)
    result_msg = messages[-1]

    # Find the last assistant message with actual content
    for msg in reversed(messages):
        if msg.__class__.__name__ == "AssistantMessage" and msg.content:
            # Check if it has text content (not just tool use)
            for block in msg.content:
                if hasattr(block, "text"):
                    print(f"\n📝 Final Result:\n{block.text}")
                    break
            break

    # Print cost if available
    if hasattr(result_msg, "total_cost_usd"):
        print(f"\n📊 Cost: ${result_msg.total_cost_usd:.2f}")

    # Print duration if available
    if hasattr(result_msg, "duration_ms"):
        print(f"⏱️  Duration: {result_msg.duration_ms / 1000:.2f}s")


def _format_tool_info(tool_name: str, tool_input: dict) -> str:
    """Format tool information with relevant parameters."""
    info_parts = [tool_name]

    if tool_input:
        if tool_name == "WebSearch" and "query" in tool_input:
            info_parts.append(f'→ "{tool_input["query"]}"')
        elif tool_name == "Bash" and "command" in tool_input:
            cmd = tool_input["command"]
            info_parts.append(f"→ {cmd}")
        elif tool_name == "Read" and "file_path" in tool_input:
            path = tool_input["file_path"]
            # Show just filename for readability
            filename = path.split("/")[-1] if "/" in path else path
            info_parts.append(f"→ {filename}")
        elif tool_name == "Write" and "file_path" in tool_input:
            path = tool_input["file_path"]
            filename = path.split("/")[-1] if "/" in path else path
            info_parts.append(f"→ {filename}")

    return " ".join(info_parts)


def visualize_conversation(messages: list[Any]) -> None:
    """
    Create a clean, professional visualization of the agent conversation.

    Features:
    - Box-drawing characters for structure
    - Grouped tool calls (no repetitive headers)
    - Clear subagent delegation sections
    - Minimal blank lines for compact output
    """
    # Header
    print()
    print(BOX_TOP)
    print(f"{BOX_SIDE}  🤖 AGENT CONVERSATION TIMELINE" + " " * 25 + BOX_SIDE)
    print(BOX_BOTTOM)
    print()

    # Track state
    in_subagent = False
    current_subagent = None
    pending_tools: list[str] = []  # Collect consecutive tool calls
    last_was_tool = False

    def flush_pending_tools(indent: str = "") -> None:
        """Print accumulated tool calls in a compact format."""
        nonlocal pending_tools, last_was_tool
        if pending_tools:
            if len(pending_tools) == 1:
                print(f"{indent}   🔧 {pending_tools[0]}")
            else:
                print(f"{indent}   🔧 Tools: {', '.join(pending_tools)}")
            pending_tools = []
        last_was_tool = False

    for _i, msg in enumerate(messages):
        msg_type = msg.__class__.__name__

        if msg_type == "SystemMessage":
            session_id = ""
            if hasattr(msg, "data") and "session_id" in msg.data:
                session_id = f" (Session: {msg.data['session_id'][:8]}...)"
            print(f"⚙️  System Initialized{session_id}")

        elif msg_type == "AssistantMessage":
            if not msg.content:
                continue

            for block in msg.content:
                if hasattr(block, "text"):
                    # Flush any pending tools before text
                    flush_pending_tools("   " if in_subagent else "")

                    text = block.text

                    if in_subagent:
                        print(f"\n   📎 [{current_subagent}] Response:")
                        # Indent the text nicely
                        for line in text.split('\n'):
                            if line.strip():
                                print(f"      {line.strip()}")
                    else:
                        print("\n🤖 Assistant:")
                        # Indent the text nicely
                        for line in text.split('\n'):
                            if line.strip():
                                print(f"   {line.strip()}")

                elif hasattr(block, "name"):
                    tool_name = block.name
                    tool_input = block.input if hasattr(block, "input") else {}

                    if tool_name == "Task":
                        # Flush pending tools
                        flush_pending_tools("   " if in_subagent else "")

                        # Subagent delegation - create clear visual block
                        subagent_type = tool_input.get("subagent_type", "unknown") if tool_input else "unknown"
                        description = tool_input.get("description", "") if tool_input else ""
                        prompt = tool_input.get("prompt", "") if tool_input else ""

                        print()
                        print(f"   {SUBAGENT_TOP}")
                        print(f"   {SUBAGENT_SIDE}  🚀 DELEGATING TO: {subagent_type.upper():<36} {SUBAGENT_SIDE}")
                        if description:
                            print(f"   {SUBAGENT_SIDE}     📋 {description:<45} {SUBAGENT_SIDE}")
                        print(f"   {SUBAGENT_BOTTOM}")

                        if prompt:
                            print(f"   📝 Prompt: {prompt}")

                        print()
                        in_subagent = True
                        current_subagent = subagent_type

                    else:
                        # Regular tool - accumulate for grouped display
                        tool_info = _format_tool_info(tool_name, tool_input)
                        pending_tools.append(tool_info)
                        last_was_tool = True

        elif msg_type == "UserMessage":
            if not msg.content or not isinstance(msg.content, list):
                continue

            for result in msg.content:
                if not isinstance(result, dict) or result.get("type") != "tool_result":
                    continue

                content = result.get("content", "")

                # Detect subagent completion (Task tool result with substantial content)
                is_subagent_result = (
                    in_subagent and
                    isinstance(content, str) and
                    len(content) > 200
                )

                if is_subagent_result:
                    # Flush any pending tools
                    flush_pending_tools("   ")

                    # Show subagent completion
                    print()
                    print(f"   {SUBAGENT_TOP}")
                    print(f"   {SUBAGENT_SIDE}  ✅ SUBAGENT [{current_subagent.upper()}] COMPLETE" + " " * (30 - len(current_subagent)) + SUBAGENT_SIDE)
                    print(f"   {SUBAGENT_BOTTOM}")

                    # Show result summary
                    if content:
                        lines = [line.strip() for line in content.split('\n') if line.strip()]
                        if lines:
                            print("   📊 Result:")
                            for line in lines:
                                print(f"      {line}")
                    print()

                    in_subagent = False
                    current_subagent = None
                else:
                    # Regular tool result - just flush pending tools
                    # (tool results don't need individual display)
                    pass

            # Flush tools after processing user message
            flush_pending_tools("   " if in_subagent else "")

        elif msg_type == "ResultMessage":
            # Flush any remaining pending tools
            flush_pending_tools("   " if in_subagent else "")

            # Close subagent if still open
            if in_subagent:
                print()
                print(f"   {SUBAGENT_TOP}")
                print(f"   {SUBAGENT_SIDE}  ✅ SUBAGENT [{current_subagent.upper()}] COMPLETE" + " " * (30 - len(current_subagent)) + SUBAGENT_SIDE)
                print(f"   {SUBAGENT_BOTTOM}")
                in_subagent = False

            # Final stats
            print()
            print("─" * 60)
            stats_parts = []
            if hasattr(msg, "num_turns"):
                stats_parts.append(f"Turns: {msg.num_turns}")
            if hasattr(msg, "total_cost_usd") and msg.total_cost_usd:
                stats_parts.append(f"Cost: ${msg.total_cost_usd:.2f}")
            if hasattr(msg, "duration_ms"):
                stats_parts.append(f"Duration: {msg.duration_ms / 1000:.1f}s")
            if hasattr(msg, "usage") and msg.usage:
                total = msg.usage.get("input_tokens", 0) + msg.usage.get("output_tokens", 0)
                stats_parts.append(f"Tokens: {total:,}")

            print(f"✅ Complete │ {' │ '.join(stats_parts)}")
            print("─" * 60)

    print()


def _image_to_base64(image_path: str) -> str:
    """Helper to convert image to base64 string"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def print_html(content: Any, title: str | None = None, is_image: bool = False) -> None:
    """
    Pretty-print inside a styled card.
    - If is_image=True and content is a string: treat as image path/URL and render <img>.
    - If content is a pandas DataFrame/Series: render as an HTML table.
    - Otherwise (strings/otros): show as code/text in <pre><code>.
    """
    # Render content
    rendered: str
    if is_image and isinstance(content, str):
        b64 = _image_to_base64(content)
        rendered = f'<img src="data:image/png;base64,{b64}" alt="Image" style="max-width:100%; height:auto; border-radius:8px;">'
    elif pd is not None and isinstance(content, pd.DataFrame):
        rendered = content.to_html(classes="pretty-table", index=False, border=0, escape=False)
    elif pd is not None and isinstance(content, pd.Series):
        rendered = content.to_frame().to_html(classes="pretty-table", border=0, escape=False)
    elif isinstance(content, list) and content and hasattr(content[-1], "__class__") and "Message" in content[-1].__class__.__name__:
        final_text = None
        for msg in reversed(content):
            if "Assistant" in msg.__class__.__name__ and hasattr(msg, "content") and msg.content:
                for block in msg.content:
                    if hasattr(block, "text"):
                        final_text = block.text
                        break
                if final_text:
                    break

        if final_text:
            try:
                import markdown
                rendered = markdown.markdown(final_text)
            except ImportError:
                rendered = f"<div style='white-space: pre-wrap; font-family: inherit;'>{html.escape(final_text)}</div>"
        else:
            rendered = f"<pre><code>{html.escape(pprint.pformat(content))}</code></pre>"
    elif isinstance(content, (list, dict)):
        rendered = f"<pre><code>{html.escape(pprint.pformat(content))}</code></pre>"
    elif isinstance(content, str):
        rendered = f"<pre><code>{html.escape(content)}</code></pre>"
    else:
        rendered = f"<pre><code>{html.escape(str(content))}</code></pre>"

    css = """
    <style>
    .pretty-card{
      font-family: ui-sans-serif, system-ui;
      border: 2px solid transparent;
      border-radius: 14px;
      padding: 14px 16px;
      margin: 10px 0;
      background: linear-gradient(#fff, #fff) padding-box,
                  linear-gradient(135deg, #3b82f6, #9333ea) border-box;
      color: #111;
      box-shadow: 0 4px 12px rgba(0,0,0,.08);
    }
    .pretty-title{
      font-weight:700;
      margin-bottom:8px;
      font-size:14px;
      color:#111;
    }
    /* 🔒 Only affects INSIDE the card */
    .pretty-card pre,
    .pretty-card code {
      background: #f3f4f6;
      color: #111;
      padding: 8px;
      border-radius: 8px;
      display: block;
      overflow-x: auto;
      font-size: 13px;
      white-space: pre-wrap;
    }
    .pretty-card img { max-width: 100%; height: auto; border-radius: 8px; }
    .pretty-card table.pretty-table {
      border-collapse: collapse;
      width: 100%;
      font-size: 13px;
      color: #111;
    }
    .pretty-card table.pretty-table th,
    .pretty-card table.pretty-table td {
      border: 1px solid #e5e7eb;
      padding: 6px 8px;
      text-align: left;
    }
    .pretty-card table.pretty-table th { background: #f9fafb; font-weight: 600; }
    </style>
    """

    title_html = f'<div class="pretty-title">{title}</div>' if title else ""
    card = f'<div class="pretty-card">{title_html}{rendered}</div>'
    display(HTML(css + card))
