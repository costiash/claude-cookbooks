# 04 - The Python Implementation Mission

## Welcome to the Real World

Congratulations on passing the Notebook Assessment! You've proven you understand the concepts. But as Alex Rivera, our CEO, put it in this morning's all-hands:

> *"Notebooks are great for research, but we can't ship a `.ipynb` file to our Customer Success team. It's time to take the training wheels off and build a proper, standalone Python application."*

## The Backstory: DataFlow Labs - Week 4

**From:** Linda Yeung, Head of Customer Success  
**To:** You (AI/Agent Engineer)  
**Subject:** URGENT: CLI Tool for Support Reps  

> *"My team is drowning in tickets. They need a fast, reliable tool they can run right from their terminal to help them draft responses and look up documentation. No web UI, no complex setup. Just a solid command-line interface (CLI) agent that knows our product and can search the web for known issues."*

## Your Mission

Your task is to convert your agentic knowledge into a **production-ready Python script**. You are no longer filling in blank cells; you are architecting the application structure.

### The Assignment

Create a robust CLI application in a file named `support_agent.py` inside this directory that fulfills the following requirements.

#### 1. Application Architecture
-   **No Notebooks**: This must be a pure Python script (`.py`).
-   **Entry Point**: A clean `if __name__ == "__main__":` block or `main()` function.
-   **Configuration**: Use `python-dotenv` to load API keys securely.
-   **Type Safety**: Use Python type hints throughout your code.

#### 2. Agent Configuration
-   **Persona**: The agent must act as a "Senior Technical Support Specialist" for DataFlow Labs.
-   **Tone**: Empathetic, technical, and concise.
-   **Tools**:
    -   `WebSearch`: To look up current error codes or library documentation.
    -   `Read`: To allow the user to provide log files or documentation for context.

#### 3. Interactive Features
-   **The Loop**: Implement a continuous `while` loop that accepts user input and prints the agent's response.
-   **State Persistence**: The agent *must* remember the conversation context (use `ClaudeSDKClient` as a context manager).
-   **Streaming Feedback**: Implement a custom activity handler to show "Thinking..." or "Using Tool: [Name]" in real-time so the user knows it's working.
-   **Exit Strategy**: Handle "exit", "quit", or Ctrl+C gracefully.

#### 4. Formatting (Bonus)
-   Use `rich` or standard ANSI escape codes to make the output readable (e.g., different colors for User vs. Agent). *Note: If you don't have `rich` installed, standard print is fine, but make it distinct.*

## Getting Started

1.  Create a new file named `support_agent.py` in this directory.
2.  Set up your imports (refer to your previous notebooks or the `chief_of_staff_agent/agent.py` for inspiration).
3.  Start coding!

## Verification

You will know you have succeeded when you can run:

```bash
python support_agent.py
```

And have a conversation like this:

```text
Initializing DataFlow Support Agent...
✅ Agent Ready. (Type 'exit' to quit)

User: I'm getting a ConnectionRefusedError on port 8080.
Thinking...
Agent: That usually indicates the service isn't running or a firewall is blocking it. Are you running the server locally?

User: Yes, locally.
Thinking...
Agent: ...
```

## Tips from the Engineering Team

-   **Error Handling**: What happens if the API call fails? Wrap your main logic in try/except blocks.
-   **Asyncio**: Remember that `ClaudeSDKClient` is async. You'll need `asyncio.run(main())`.
-   **Dependencies**: Ensure you have `claude-agent-sdk` and `python-dotenv` installed in your environment.
-   **Reference**: If you get stuck, look at `chief_of_staff_agent/agent.py`. It's a good example of a standalone script, although much more complex than what you need here. Keep it simple!

Good luck. The Support team is waiting!
