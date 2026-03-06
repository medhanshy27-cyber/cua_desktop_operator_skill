# MCP Client Setup

Use this file when the current agent session does not expose the `desktop_*` MCP tools yet.

## Desktop Operator MCP values

Use the same server name and launch values across clients:

- Server name: `desktop-operator`
- Command: `python`
- Args: `["-m", "desktop_operator_mcp"]`
- Required env:
  - `PYTHONPATH`: the project root that contains `desktop_operator_core` and `desktop_operator_mcp`
  - `DESKTOP_OPERATOR_ROOT`: the same project root

Project root rule:

- Use the folder that directly contains `desktop_operator_core` and `desktop_operator_mcp`.
- If this repository was cloned straight into a skills directory, that clone root is usually the project root.

Example placeholder:

- `<PROJECT_ROOT>`

## Agent policy

If MCP is missing:

1. Detect the current client.
2. If it is Codex, Claude Code, Cursor, or OpenCode, configure MCP first.
3. Restart or reload the client if needed.
4. Verify the server is visible.
5. Only then start the desktop task.

If the client is not one of those four:

1. Do not guess the client-specific config format.
2. Tell the user the agent needs manual MCP setup first.
3. Send them the generic local stdio server values from this file.

## Codex

Official docs say Codex can connect to MCP servers in the CLI or IDE extension, and the configuration is shared. The docs show direct editing of `~/.codex/config.toml` and `codex mcp list` for verification.

Recommended config:

```toml
[mcp_servers.desktop-operator]
command = "python"
args = ["-m", "desktop_operator_mcp"]

[mcp_servers.desktop-operator.env]
PYTHONPATH = "<PROJECT_ROOT>"
DESKTOP_OPERATOR_ROOT = "<PROJECT_ROOT>"
```

Verify:

```bash
codex mcp list
```

Source:

- [OpenAI Docs MCP quickstart](https://developers.openai.com/resources/docs-mcp)

## Claude Code

Official docs support both command-based setup and JSON config. For local stdio servers, the docs show:

```bash
claude mcp add --transport stdio <name> -- <command> [args...]
```

For deterministic workspace setup, prefer a project `.mcp.json`:

```json
{
  "mcpServers": {
    "desktop-operator": {
      "command": "python",
      "args": ["-m", "desktop_operator_mcp"],
      "env": {
        "PYTHONPATH": "<PROJECT_ROOT>",
        "DESKTOP_OPERATOR_ROOT": "<PROJECT_ROOT>"
      }
    }
  }
}
```

Equivalent CLI form:

```bash
claude mcp add --transport stdio ^
  --env PYTHONPATH=<PROJECT_ROOT> ^
  --env DESKTOP_OPERATOR_ROOT=<PROJECT_ROOT> ^
  desktop-operator -- python -m desktop_operator_mcp
```

Relevant official points:

- project scope uses `.mcp.json`
- user/local scopes are stored in `~/.claude.json`
- `claude mcp add` and `claude mcp add-json` are supported

Source:

- [Claude Code MCP docs](https://code.claude.com/docs/en/mcp)

## Cursor

Official docs say Cursor supports MCP through `mcp.json`, with:

- project config: `.cursor/mcp.json`
- global config: `~/.cursor/mcp.json`
- `cursor-agent` uses the same MCP configuration model

Use a stdio server entry like this:

```json
{
  "mcpServers": {
    "desktop-operator": {
      "command": "python",
      "args": ["-m", "desktop_operator_mcp"],
      "env": {
        "PYTHONPATH": "<PROJECT_ROOT>",
        "DESKTOP_OPERATOR_ROOT": "<PROJECT_ROOT>"
      }
    }
  }
}
```

After adding it, restart Cursor and verify the server appears under MCP / Available Tools.

CLI verification:

```bash
cursor-agent mcp list
```

Notes:

- The docs explicitly document `command`, `args`, and `env` for local stdio servers.
- The docs also document `cursor-agent mcp` for listing configured MCP servers and their status.
- Expanding `~/.cursor/mcp.json` to a Windows home-directory path is an inference from the documented path convention.

Source:

- [Cursor MCP docs](https://docs.cursor.com/advanced/model-context-protocol)
- [Cursor CLI MCP docs](https://docs.cursor.com/cli/mcp)

## OpenCode

Official docs support:

- project config: `opencode.json`
- global config: `~/.config/opencode/opencode.json`
- interactive CLI setup: `opencode mcp add`

For a local server, the docs use:

- `"type": "local"`
- `"command": ["..."]`
- optional `"environment"`
- optional `"enabled": true`

Recommended config:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "desktop-operator": {
      "type": "local",
      "command": ["python", "-m", "desktop_operator_mcp"],
      "enabled": true,
      "environment": {
        "PYTHONPATH": "<PROJECT_ROOT>",
        "DESKTOP_OPERATOR_ROOT": "<PROJECT_ROOT>"
      }
    }
  }
}
```

CLI alternative:

```bash
opencode mcp add
```

The official CLI docs say this command walks the user through adding a local or remote MCP server.

Sources:

- [OpenCode MCP servers docs](https://opencode.ai/docs/mcp-servers/)
- [OpenCode CLI docs](https://opencode.ai/docs/cli/)

## Manual fallback for other agents

If the client is not Codex, Claude Code, Cursor, or OpenCode, send the user this generic MCP payload and ask them to add it using that client's MCP settings flow:

```json
{
  "name": "desktop-operator",
  "transport": "stdio",
  "command": "python",
  "args": ["-m", "desktop_operator_mcp"],
  "env": {
    "PYTHONPATH": "<PROJECT_ROOT>",
    "DESKTOP_OPERATOR_ROOT": "<PROJECT_ROOT>"
  }
}
```

Also tell them:

1. restart or reload the client after adding the server
2. verify that `desktop-operator` is connected
3. only then ask the agent to perform desktop tasks
