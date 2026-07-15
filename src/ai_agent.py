"""
ai_agent.py — Antigravity Agent wired to the GitHub MCP server.

Used for AI-powered repo analysis. The agent reads repo metadata
(fetched via PyGithub) and the GitHub MCP server for deeper access,
then streams a structured analysis back to the terminal.
"""

from __future__ import annotations

import asyncio
import json
import os

from google.antigravity import Agent, LocalAgentConfig, types

from src.display import console, ai_stream_header, ACCENT, PRIMARY, MUTED

# ── System prompt ─────────────────────────────────────────────────────────────

_ANALYSIS_SYSTEM_PROMPT = """
You are Git Happens' AI analyst — an expert software engineering analyst who reviews
GitHub repositories and provides clear, actionable insights.

When given a repository to analyze, you will:

1. **Overview** — Summarize what the project does in 2-3 sentences.
2. **Tech Stack** — List the main languages, frameworks, and tools detected.
3. **Health Score** — Rate the repo 1–10 across:
   - Code activity (recent commits, open issues)
   - Documentation (README quality, descriptions)
   - Community (stars, forks, topics, license)
   - Maintenance (issue response, update frequency)
4. **Strengths** — 2-3 things the repo does well.
5. **Suggestions** — 2-3 concrete, actionable improvements.
6. **Summary** — One-line verdict.

Format your response in clean markdown with headers and bullet points.
Be direct and specific. Avoid generic statements.
"""


# ── Public API ────────────────────────────────────────────────────────────────

async def analyze_repo_async(
    repo_full_name: str,
    repo_summary: dict,
    github_token: str,
    gemini_api_key: str | None = None,
) -> str:
    """
    Run the Antigravity agent to analyze a repo.

    Args:
        repo_full_name:  e.g. "owner/repo"
        repo_summary:    dict from GitHubClient.get_repo_summary()
        github_token:    PAT for the GitHub MCP server
        gemini_api_key:  optional override (otherwise reads GEMINI_API_KEY env)

    Returns:
        The full analysis text.
    """
    api_key = gemini_api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        from src.display import error
        error(
            "No Gemini API key found. Set [bold]GEMINI_API_KEY[/bold] in your .env "
            "or get one at https://aistudio.google.com/app/api-keys"
        )
        raise SystemExit(1)

    # Wire in the GitHub MCP server (npx, cross-platform)
    mcp_servers = [
        types.McpStdioServer(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-github"],
            env={"GITHUB_PERSONAL_ACCESS_TOKEN": github_token},
        )
    ]

    config = LocalAgentConfig(
        api_key=api_key,
        system_instruction=_ANALYSIS_SYSTEM_PROMPT,
        mcp_servers=mcp_servers,
    )

    # Build a rich prompt with the pre-fetched metadata
    prompt = (
        f"Please analyze this GitHub repository: **{repo_full_name}**\n\n"
        f"Here is the metadata I already fetched for context:\n"
        f"```json\n{json.dumps(repo_summary, indent=2)}\n```\n\n"
        f"Use the GitHub MCP tools to explore the repository further if needed "
        f"(e.g., read the README, browse files, check open issues). "
        f"Then produce your full analysis."
    )

    ai_stream_header(repo_full_name)
    full_text = ""

    async with Agent(config) as agent:
        response = await agent.chat(prompt)
        text = await response.text()
        full_text = text

    return full_text


def analyze_repo(
    repo_full_name: str,
    repo_summary: dict,
    github_token: str,
    gemini_api_key: str | None = None,
) -> str:
    """Synchronous wrapper around analyze_repo_async."""
    return asyncio.run(
        analyze_repo_async(
            repo_full_name=repo_full_name,
            repo_summary=repo_summary,
            github_token=github_token,
            gemini_api_key=gemini_api_key,
        )
    )
