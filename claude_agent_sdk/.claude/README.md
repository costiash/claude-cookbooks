# Claude Code Project Configuration

This directory contains project-specific settings for Claude Code.

## Permissions Configuration

The `settings.json` file defines tool permissions based on Claude Code best practices:

### Always Allowed Tools

#### Web Tools
- **WebSearch(*)** - Search the web for current information
- **WebFetch(*)** - Fetch content from any URL

#### Jupyter Notebook Operations
- **Read/Write/NotebookEdit(*.ipynb)** - Full access to Jupyter notebooks
- Enables seamless notebook editing and execution

#### File Operations
Allowed for common development file types:
- Python files (*.py)
- Markdown files (*.md)
- JSON files (*.json)
- YAML files (*.yaml, *.yml)
- Text files (*.txt)

#### Code Search & Navigation
- **Glob(**)** - Pattern-based file discovery
- **Grep(**)** - Content search across files

#### Safe Git Commands
Read-only git operations:
- `git status`
- `git diff*`
- `git log*`
- `git branch*`
- `git show*`

#### Python Development
- **pytest** - Run tests
- **pip list** - Check installed packages
- **python --version** - Version checking
- **python -m venv** - Virtual environment creation
- **uv**, **ruff**, **black**, **mypy**, **isort** - Modern Python tooling

#### Safe System Commands
- Directory listing: `ls`, `tree`, `find`
- Navigation: `pwd`, `which`
- Display: `cat`, `echo`
- Environment: `env | grep`, `printenv`
- File operations: `mkdir -p`, `chmod +x`
- Cleanup: Remove Python cache files

### Explicitly Denied

For security, these patterns are blocked:
- Destructive filesystem operations (`rm -rf /`, `rm -rf ~`)
- Privilege escalation (`sudo`)
- Piped remote code execution (`curl|bash`, `wget|sh`)

## Security Best Practices

1. **Wildcard Usage**: `*` matches within a path segment, `**` matches across directories
2. **Sandbox Mode**: Enabled by default (`allowUnsandboxedCommands: false`)
3. **Principle of Least Privilege**: Only allow what's needed for the project
4. **Regular Review**: Audit permissions as project needs evolve

## Additional Settings

- **todoFeatureEnabled**: Enables task tracking
- **thinkingEnabled**: Allows extended reasoning mode
- **verbose**: Controls output verbosity (set to false for cleaner output)

## Modifying Permissions

To add new permissions:
1. Edit `.claude/settings.json`
2. Add patterns to the `allow` array
3. Claude Code automatically picks up changes

Example:
```json
"allow": [
  "Bash(npm install*)",
  "Bash(node*)",
  "Read(**/*.ts)"
]
```

## Documentation

- Official Claude Code Docs: https://docs.anthropic.com/en/docs/claude-code
- Settings Reference: https://docs.anthropic.com/en/docs/claude-code/settings
- Security Guide: https://docs.anthropic.com/en/docs/claude-code/security
