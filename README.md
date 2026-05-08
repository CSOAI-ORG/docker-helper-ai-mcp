[![docker-helper-ai-mcp MCP server](https://glama.ai/mcp/servers/CSOAI-ORG/docker-helper-ai-mcp/badges/score.svg)](https://glama.ai/mcp/servers/CSOAI-ORG/docker-helper-ai-mcp)
[![MCP Registry](https://img.shields.io/badge/MCP_Registry-Published-green)](https://registry.modelcontextprotocol.io)
[![PyPI](https://img.shields.io/pypi/v/docker-helper-ai-mcp)](https://pypi.org/project/docker-helper-ai-mcp/)

[![docker-helper-ai-mcp MCP server](https://glama.ai/mcp/servers/CSOAI-ORG/docker-helper-ai-mcp/badges/card.svg)](https://glama.ai/mcp/servers/CSOAI-ORG/docker-helper-ai-mcp)

<div align="center">

# Docker Helper Ai MCP

**Docker Helper AI MCP Server — Docker tools.**

[![PyPI](https://img.shields.io/pypi/v/meok-docker-helper-ai-mcp)](https://pypi.org/project/meok-docker-helper-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MEOK AI Labs](https://img.shields.io/badge/MEOK_AI_Labs-MCP_Server-purple)](https://meok.ai)

</div>

## Overview

Docker Helper AI MCP Server — Docker tools.

## Tools

| Tool | Description |
|------|-------------|
| `generate_dockerfile` | Generate a Dockerfile. Languages: python, node, go, rust, static. |
| `parse_compose` | Parse and analyze a docker-compose YAML string (basic YAML parser). |
| `optimize_image` | Analyze a Dockerfile and suggest optimizations. |
| `security_scan_data` | Scan Dockerfile for security issues (static analysis). |

## Installation

```bash
pip install meok-docker-helper-ai-mcp
```

## Usage with Claude Desktop

Add to your Claude Desktop MCP config:

```json
{
  "mcpServers": {
    "docker-helper-ai": {
      "command": "python",
      "args": ["-m", "meok_docker_helper_ai_mcp.server"]
    }
  }
}
```

## License

MIT © [MEOK AI Labs](https://meok.ai)
<!-- mcp-name: io.github.CSOAI-ORG/docker-helper-ai-mcp -->
