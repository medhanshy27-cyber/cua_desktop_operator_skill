# Compatibility

This skill is written for MCP-capable agents that can:

- call local stdio MCP servers
- inspect screenshot file paths returned by tools
- follow an iterative observe-plan-act-verify loop

## Expected agent behavior

- Use the same MCP tool names across clients.
- Keep reasoning in the agent.
- Keep desktop execution in the MCP runtime.

## Typical client differences

- Some agents are better at planning one step at a time.
- Some agents can batch a few primitive actions before observing again.
- Some agents render image artifacts directly; others need the absolute file path surfaced in text.

These differences stay in the agent behavior layer. The runtime and tool surface stay the same.
