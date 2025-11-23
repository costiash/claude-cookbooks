# Claude Agent SDK Troubleshooting Guide

## Buffer Overflow Errors with ClaudeSDKClient

### Problem

When using `ClaudeSDKClient` with multimodal content (images, large documents), you may encounter:

```
Fatal error in message reader: Failed to decode JSON: JSON message exceeded maximum buffer size of 1048576 bytes
```

After this error, the conversation loop doesn't recover properly, and subsequent `receive_response()` calls may hang or fail.

### Root Cause

1. **Default Buffer Limit**: The SDK's CLI communication has a default 1MB buffer (`max_buffer_size=1048576`)
2. **Image Encoding**: Images are base64-encoded in JSON messages, increasing size by ~33%
   - A 200KB PNG becomes ~270KB+ when encoded
   - Plus message envelope overhead (metadata, tool results, etc.)
3. **No Automatic Recovery**: After buffer overflow, the async iterator enters a corrupted state

### Solutions

#### Solution 1: Increase Buffer Size (Recommended)

Add `max_buffer_size` to your `ClaudeAgentOptions`:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async with ClaudeSDKClient(
    options=ClaudeAgentOptions(
        model="claude-sonnet-4-5",
        allowed_tools=["WebSearch", "Read"],
        max_buffer_size=10 * 1024 * 1024,  # 10MB for images
    )
) as client:
    await client.query("Analyze this image...")
    async for msg in client.receive_response():
        print(msg)
```

**Buffer size recommendations:**
- **Text only**: 1MB (default) is usually sufficient
- **Images/PDFs**: 10MB recommended
- **Large documents**: 50MB or higher
- **Video frames**: 100MB+

#### Solution 2: Add Error Handling

Wrap `receive_response()` in try-except to handle failures gracefully:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async with ClaudeSDKClient(
    options=ClaudeAgentOptions(
        model="claude-sonnet-4-5",
        allowed_tools=["WebSearch", "Read"],
        max_buffer_size=10 * 1024 * 1024,
    )
) as client:
    try:
        await client.query("Analyze this image...")
        async for msg in client.receive_response():
            print(msg)
    except Exception as e:
        print(f"Error during response: {e}")
        # Client context manager will clean up automatically
```

#### Solution 3: Process Content in Chunks

For very large content, consider breaking it into smaller pieces:

```python
# Instead of analyzing one huge image
await client.query("Analyze this 10MB chart...")

# Break it into regions or use thumbnails
await client.query("Analyze the top-left quadrant of the chart...")
await client.query("Now analyze the bottom-right...")
```

#### Solution 4: Use Descriptions Instead of Full Images

Sometimes you don't need the full image:

```python
# Instead of:
await client.query("Analyze research_agent/large_chart.png")

# Consider:
await client.query(
    "Based on this description: 'Chart showing project distribution "
    "with Personal Projects at 36% and Startup Work at 33%', "
    "research the implications..."
)
```

### Best Practices

1. **Set buffer size proactively** when you know you'll handle images/large data
2. **Monitor stderr output** for early warning signs:
   ```python
   options = ClaudeAgentOptions(
       stderr=lambda msg: print(f"[SDK]: {msg}"),
       max_buffer_size=10 * 1024 * 1024,
   )
   ```
3. **Use async context managers** to ensure cleanup on errors
4. **Test with representative data** before production
5. **Consider trade-offs**: Larger buffers use more memory

### Why This Matters

The buffer overflow issue is particularly important because:

- **No graceful degradation**: The error causes complete conversation failure
- **Silent hangs**: The second `receive_response()` may appear to hang indefinitely
- **Context loss**: You lose all work done before the error
- **Production impact**: Can cause agent systems to become unresponsive

### Technical Details

The buffer overflow happens in the SDK's JSON message parsing layer, which reads from the underlying CLI process via stdout. When a message exceeds `max_buffer_size`:

1. The JSON parser fails mid-message
2. The async iterator doesn't properly signal completion
3. Subsequent calls to `receive_response()` wait for data that won't arrive
4. The CLI process may be in an error state, not sending more data

### Related Issues

- Working with PDFs: Same buffer considerations apply
- Large tool results: WebSearch with many results can also hit limits
- Concurrent subagents: Each subagent's output counts toward the buffer

### Example: Production-Ready Image Analysis

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def analyze_chart(image_path: str) -> str:
    """
    Analyze a chart image with proper error handling.

    Returns the analysis text or None if failed.
    """
    options = ClaudeAgentOptions(
        model="claude-sonnet-4-5",
        allowed_tools=["Read", "WebSearch"],
        max_buffer_size=10 * 1024 * 1024,  # 10MB buffer
        stderr=lambda msg: print(f"[SDK Warning]: {msg}"),
    )

    try:
        async with ClaudeSDKClient(options=options) as client:
            # First query: Analyze the chart
            await client.query(f"Analyze the chart at {image_path}")

            result_text = None
            async for msg in client.receive_response():
                if hasattr(msg, 'result'):
                    result_text = msg.result

            if not result_text:
                print("No result from first query")
                return None

            # Second query: Research insights
            await client.query(
                "Research the key insights from this chart using web search"
            )

            final_result = None
            async for msg in client.receive_response():
                if hasattr(msg, 'result'):
                    final_result = msg.result

            return final_result

    except Exception as e:
        print(f"Chart analysis failed: {e}")
        return None

# Usage
result = await analyze_chart("research_agent/projects_claude.png")
print(f"Analysis: {result}")
```

## Additional Resources

- [Claude Agent SDK Documentation](https://docs.anthropic.com/en/docs/claude-code/en__docs__agent-sdk__overview)
- [Python SDK Reference](https://docs.anthropic.com/en/docs/claude-code/en__docs__agent-sdk__python)
- [GitHub Issues - TypeScript SDK](https://github.com/anthropics/claude-agent-sdk-typescript/issues)
- [GitHub Issues - Python SDK](https://github.com/anthropics/claude-agent-sdk-python/issues)

---

**Last Updated**: 2025-01-22
**SDK Version**: claude-agent-sdk 0.0.x
