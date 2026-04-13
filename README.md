# docker-helper-ai-mcp

MCP server for Docker tools.

## Tools

- **generate_dockerfile** — Generate Dockerfiles for Python, Node, Go, Rust, static
- **parse_compose** — Parse and analyze docker-compose YAML
- **optimize_image** — Suggest Dockerfile optimizations
- **security_scan_data** — Static security analysis of Dockerfiles

## Usage

```bash
pip install mcp
python server.py
```

## Rate Limits

50 calls/day per tool (free tier).
