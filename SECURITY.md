# Security Policy

## Supported Versions

This project is currently maintained as a rolling main branch.

Please report security issues against the latest version of the repository.

## Reporting a Vulnerability

Do not open a public issue for a suspected security vulnerability.

Instead:

1. prepare a minimal description of the issue
2. describe impact, affected files, and reproduction steps
3. send the report privately to the current maintainer of this repository

If you do not know the maintainer contact yet, do not disclose exploit details publicly until a private reporting address is added.

## Scope Notes

This repository automates local Windows desktop interactions. Security-sensitive areas include:

- command execution
- clipboard handling
- local file access
- desktop input simulation
- MCP server exposure

When reporting an issue, include whether it requires:

- local access
- user interaction
- MCP client access
- a crafted file path or command argument
