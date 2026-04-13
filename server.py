"""Docker Helper AI MCP Server — Docker tools."""
import re
import time
from typing import Any
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("docker-helper-ai-mcp")
_calls: dict[str, list[float]] = {}
DAILY_LIMIT = 50

def _rate_check(tool: str) -> bool:
    now = time.time()
    _calls.setdefault(tool, [])
    _calls[tool] = [t for t in _calls[tool] if t > now - 86400]
    if len(_calls[tool]) >= DAILY_LIMIT:
        return False
    _calls[tool].append(now)
    return True

TEMPLATES = {
    "python": {"base": "python:3.12-slim", "install": "pip install --no-cache-dir -r requirements.txt", "copy": ".", "cmd": 'python app.py', "workdir": "/app", "port": 8000},
    "node": {"base": "node:20-alpine", "install": "npm ci --only=production", "copy": ".", "cmd": "node index.js", "workdir": "/app", "port": 3000},
    "go": {"base": "golang:1.22-alpine AS builder", "install": "go build -o main .", "copy": ".", "cmd": "./main", "workdir": "/app", "port": 8080, "multistage": True},
    "rust": {"base": "rust:1.77-slim AS builder", "install": "cargo build --release", "copy": ".", "cmd": "./target/release/app", "workdir": "/app", "port": 8080, "multistage": True},
    "static": {"base": "nginx:alpine", "install": None, "copy": "html /usr/share/nginx/html", "cmd": None, "workdir": None, "port": 80},
}

@mcp.tool()
def generate_dockerfile(language: str, app_port: int = 0, env_vars: str = "", multi_stage: bool = False) -> dict[str, Any]:
    """Generate a Dockerfile. Languages: python, node, go, rust, static."""
    if not _rate_check("generate_dockerfile"):
        return {"error": "Rate limit exceeded (50/day)"}
    lang = language.lower()
    if lang not in TEMPLATES:
        return {"error": f"Unsupported language. Available: {', '.join(TEMPLATES)}"}
    t = TEMPLATES[lang]
    port = app_port or t["port"]
    lines = [f"FROM {t['base']}", ""]
    if t.get("workdir"):
        lines += [f"WORKDIR {t['workdir']}", ""]
    envs = {}
    if env_vars:
        for pair in env_vars.split(","):
            if "=" in pair:
                k, v = pair.split("=", 1)
                envs[k.strip()] = v.strip()
    for k, v in envs.items():
        lines.append(f"ENV {k}={v}")
    if envs:
        lines.append("")
    if lang == "python":
        lines += ["COPY requirements.txt .", f"RUN {t['install']}", "", f"COPY {t['copy']} ."]
    elif lang == "node":
        lines += ["COPY package*.json .", f"RUN {t['install']}", "", f"COPY {t['copy']} ."]
    else:
        lines += [f"COPY {t['copy']} .", ""]
        if t["install"]:
            lines.append(f"RUN {t['install']}")
    lines += ["", f"EXPOSE {port}"]
    if t.get("multistage") or multi_stage:
        lines += ["", "FROM alpine:latest", f"WORKDIR {t.get('workdir', '/app')}", f"COPY --from=builder {t.get('workdir', '/app')}/{t['cmd'].lstrip('./')} ."]
        lines.append(f'CMD ["./{t["cmd"].lstrip("./").split("/")[-1]}"]')
    elif t["cmd"]:
        cmd_parts = t["cmd"].split()
        lines.append(f'CMD [{", ".join(f"{c!r}" for c in cmd_parts)}]')
    dockerfile = "\n".join(lines)
    return {"dockerfile": dockerfile, "language": lang, "port": port, "multi_stage": t.get("multistage", False) or multi_stage}

@mcp.tool()
def parse_compose(compose_yaml: str) -> dict[str, Any]:
    """Parse and analyze a docker-compose YAML string (basic YAML parser)."""
    if not _rate_check("parse_compose"):
        return {"error": "Rate limit exceeded (50/day)"}
    services = []
    volumes = []
    networks = []
    current_section = None
    current_service = None
    for line in compose_yaml.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0 and stripped.endswith(":"):
            current_section = stripped[:-1]
            current_service = None
        elif indent == 2 and stripped.endswith(":") and current_section == "services":
            current_service = stripped[:-1]
            services.append({"name": current_service, "properties": {}})
        elif indent == 4 and current_service and ":" in stripped:
            key, val = stripped.split(":", 1)
            services[-1]["properties"][key.strip()] = val.strip()
        elif indent == 2 and stripped.endswith(":") and current_section == "volumes":
            volumes.append(stripped[:-1])
        elif indent == 2 and stripped.endswith(":") and current_section == "networks":
            networks.append(stripped[:-1])
    return {
        "services": services, "service_count": len(services),
        "volumes": volumes, "networks": networks,
        "has_healthcheck": any("healthcheck" in str(s) for s in services)
    }

@mcp.tool()
def optimize_image(dockerfile: str) -> dict[str, Any]:
    """Analyze a Dockerfile and suggest optimizations."""
    if not _rate_check("optimize_image"):
        return {"error": "Rate limit exceeded (50/day)"}
    suggestions = []
    lines = dockerfile.strip().split("\n")
    from_lines = [l for l in lines if l.strip().startswith("FROM")]
    run_lines = [l for l in lines if l.strip().startswith("RUN")]
    # Check base image
    for fl in from_lines:
        if "latest" in fl:
            suggestions.append({"severity": "high", "message": "Pin base image version instead of using :latest"})
        if not any(s in fl for s in ["slim", "alpine", "distroless", "scratch"]):
            suggestions.append({"severity": "medium", "message": f"Consider using slim/alpine variant: {fl.strip()}"})
    # Multiple RUN = multiple layers
    if len(run_lines) > 3:
        suggestions.append({"severity": "medium", "message": f"Combine {len(run_lines)} RUN commands to reduce layers"})
    # Check for cache-busting
    for rl in run_lines:
        if "apt-get install" in rl and "apt-get update" not in rl:
            suggestions.append({"severity": "high", "message": "Combine apt-get update && apt-get install in same RUN"})
        if "apt-get" in rl and "rm -rf /var/lib/apt/lists/*" not in rl:
            suggestions.append({"severity": "medium", "message": "Clean apt cache: rm -rf /var/lib/apt/lists/*"})
        if "pip install" in rl and "--no-cache-dir" not in rl:
            suggestions.append({"severity": "low", "message": "Add --no-cache-dir to pip install"})
    # .dockerignore check
    if not any("AS" in fl for fl in from_lines) and len(from_lines) == 1:
        suggestions.append({"severity": "low", "message": "Consider multi-stage build to reduce final image size"})
    # COPY before RUN
    copy_idx = [i for i, l in enumerate(lines) if l.strip().startswith("COPY")]
    run_idx = [i for i, l in enumerate(lines) if l.strip().startswith("RUN")]
    if copy_idx and run_idx and any(c < min(run_idx) for c in copy_idx if "requirements" not in lines[c] and "package" not in lines[c]):
        suggestions.append({"severity": "medium", "message": "Copy dependency files first, install, then copy app code for better layer caching"})
    score = max(0, 100 - sum(20 if s["severity"] == "high" else 10 if s["severity"] == "medium" else 5 for s in suggestions))
    return {"suggestions": suggestions, "score": score, "layers": len(from_lines) + len(run_lines), "from_count": len(from_lines)}

@mcp.tool()
def security_scan_data(dockerfile: str) -> dict[str, Any]:
    """Scan Dockerfile for security issues (static analysis)."""
    if not _rate_check("security_scan_data"):
        return {"error": "Rate limit exceeded (50/day)"}
    issues = []
    lines = dockerfile.strip().split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("USER root"):
            issues.append({"line": i, "severity": "high", "issue": "Running as root user"})
        if re.search(r'(password|secret|api_key|token)\s*=', stripped, re.IGNORECASE):
            issues.append({"line": i, "severity": "critical", "issue": "Hardcoded secret detected"})
        if "chmod 777" in stripped:
            issues.append({"line": i, "severity": "high", "issue": "Overly permissive file permissions (777)"})
        if stripped.startswith("ADD") and ("http" in stripped or "ftp" in stripped):
            issues.append({"line": i, "severity": "medium", "issue": "Use COPY instead of ADD for local files; ADD with URLs is risky"})
        if "sudo" in stripped:
            issues.append({"line": i, "severity": "medium", "issue": "Avoid sudo in Dockerfile; use USER directive"})
        if stripped.startswith("EXPOSE") and any(p in stripped for p in ["22", "23", "3389"]):
            issues.append({"line": i, "severity": "high", "issue": "Exposing management port (SSH/Telnet/RDP)"})
    has_user = any(l.strip().startswith("USER") and "root" not in l for l in lines)
    if not has_user:
        issues.append({"line": 0, "severity": "medium", "issue": "No non-root USER directive found"})
    has_healthcheck = any(l.strip().startswith("HEALTHCHECK") for l in lines)
    if not has_healthcheck:
        issues.append({"line": 0, "severity": "low", "issue": "No HEALTHCHECK defined"})
    score = max(0, 100 - sum(25 if i["severity"] == "critical" else 15 if i["severity"] == "high" else 10 if i["severity"] == "medium" else 5 for i in issues))
    return {"issues": issues, "issue_count": len(issues), "security_score": score}

if __name__ == "__main__":
    mcp.run()
