# Contributing

Thanks for your interest. Right now, the only contribution path open is **MCP-based integrations**.

---

## How it works

Ragchat connects to external services through MCP (Model Context Protocol) servers. If a service you use has an MCP adapter — Notion, Linear, Slack, GitHub, Jira, etc. — you can add support for it here without writing any core code.

Your contribution is a config definition, not Python.

---

## Adding an integration

Create a folder under `integrations/mcp/` with two files:

```
integrations/
  mcp/
    notion/
      config.json
      README.md
```

**`config.json`** — how Ragchat connects to the MCP server:

```json
{
  "name": "notion",
  "transport": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-notion"],
  "env": {
    "NOTION_API_KEY": "${NOTION_API_KEY}"
  }
}
```

**`README.md`** — keep it short:
- What data it syncs
- Required env vars and where to get them
- Any known limits or caveats

PRs without a `README.md` won't be reviewed.

---

## Submitting

1. Fork the repo and create a branch: `feature/integration-<service-name>`
2. Add your folder under `integrations/mcp/`
3. Open a PR titled `[Integration] Service Name`

---

## Rules

- Secrets go in env vars only — never hardcoded in config
- One integration per PR
- If the service doesn't have an official MCP server yet, open a [Discussion](https://github.com/soumen888/Rag-Chatbot/discussions) first before building one from scratch
