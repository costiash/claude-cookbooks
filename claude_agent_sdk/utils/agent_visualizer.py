import base64
import html
import pprint
from typing import Any, Optional

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


def print_activity(msg: Any) -> None:
    if "Assistant" in msg.__class__.__name__:
        # Check if content exists and has elements
        if hasattr(msg, "content") and msg.content:
            tool_name = msg.content[0].name if hasattr(msg.content[0], "name") else "Thinking..."
            print(f"🤖 Using: {tool_name}()")
        else:
            print("🤖 Thinking...")
    elif "User" in msg.__class__.__name__:
        print("✓ Tool completed")


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


def visualize_conversation(messages: list[Any]) -> None:
    """Create a visual representation of the entire agent conversation"""
    print("\n" + "=" * 60)
    print("🤖 AGENT CONVERSATION TIMELINE")
    print("=" * 60 + "\n")

    for i, msg in enumerate(messages):
        msg_type = msg.__class__.__name__

        if msg_type == "SystemMessage":
            print("⚙️  System Initialized")
            if hasattr(msg, "data") and "session_id" in msg.data:
                print(f"   Session: {msg.data['session_id'][:8]}...")
            print()

        elif msg_type == "AssistantMessage":
            print("🤖 Assistant:")
            if msg.content:
                for block in msg.content:
                    if hasattr(block, "text"):
                        # Text response
                        text = block.text[:500] + "..." if len(block.text) > 500 else block.text
                        print(f"   💬 {text}")
                    elif hasattr(block, "name"):
                        # Tool use
                        tool_name = block.name
                        print(f"   🔧 Using tool: {tool_name}")

                        # Show key parameters for certain tools
                        if hasattr(block, "input") and block.input:
                            if tool_name == "WebSearch" and "query" in block.input:
                                print(f'      Query: "{block.input["query"]}"')
                            elif tool_name == "TodoWrite" and "todos" in block.input:
                                todos = block.input["todos"]
                                in_progress = [t for t in todos if t["status"] == "in_progress"]
                                completed = [t for t in todos if t["status"] == "completed"]
                                print(
                                    f"      📋 {len(completed)} completed, {len(in_progress)} in progress"
                                )
            print()

        elif msg_type == "UserMessage":
            if msg.content and isinstance(msg.content, list):
                for result in msg.content:
                    if isinstance(result, dict) and result.get("type") == "tool_result":
                        print("👤 Tool Result Received")
                        tool_id = result.get("tool_use_id", "unknown")[:8]
                        print(f"   ID: {tool_id}...")

                        # Show result summary
                        if "content" in result:
                            content = result["content"]
                            if isinstance(content, str):
                                # Show more of the content
                                summary = content[:500] + "..." if len(content) > 500 else content
                                print(f"   📥 {summary}")
            print()

        elif msg_type == "ResultMessage":
            print("✅ Conversation Complete")
            if hasattr(msg, "num_turns"):
                print(f"   Turns: {msg.num_turns}")
            if hasattr(msg, "total_cost_usd"):
                print(f"   Cost: ${msg.total_cost_usd:.2f}")
            if hasattr(msg, "duration_ms"):
                print(f"   Duration: {msg.duration_ms / 1000:.2f}s")
            if hasattr(msg, "usage"):
                usage = msg.usage
                total_tokens = usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                print(f"   Tokens: {total_tokens:,}")
            print()

    print("=" * 60 + "\n")


def _image_to_base64(image_path: str) -> str:
    """Helper to convert image to base64 string"""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")


def print_html(content: Any, title: Optional[str] = None, is_image: bool = False) -> None:
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
