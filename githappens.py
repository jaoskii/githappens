#!/usr/bin/env python3
"""
githappens.py — AI-Powered GitHub Manager CLI

Because git happens. Cross-platform CLI using:
  - Typer      → CLI framework
  - PyGithub   → GitHub REST API
  - Antigravity + GitHub MCP → AI repo analysis
  - cryptography → SSH key generation (no shell)
  - Rich       → Terminal UI

Usage:
    python githappens.py --help
    python githappens.py profile add personal
    python githappens.py repo create my-new-repo
    python githappens.py ssh setup
    python githappens.py collab add owner/repo username
    python githappens.py analyze owner/repo
"""

import sys
from pathlib import Path
from typing import Optional

# Load .env before anything else
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=False)

import typer
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm

import src.display as ui
from src.config import (
    add_profile,
    list_profiles,
    set_active_profile,
    remove_profile,
    resolve_profile,
    update_ssh_key_path,
    keys_dir,
)
from src.github_client import GitHubClient
from src.ssh_manager import setup_ssh_for_profile, read_public_key
from src.ai_agent import analyze_repo

# ── App ───────────────────────────────────────────────────────────────────────

app = typer.Typer(
    name="githappens",
    help="🌿 Git Happens — AI-Powered GitHub Manager",
    add_completion=False,
    rich_markup_mode="rich",
    no_args_is_help=True,
)

profile_app = typer.Typer(help="Manage GitHub account profiles", no_args_is_help=True)
repo_app    = typer.Typer(help="Repository operations",          no_args_is_help=True)
ssh_app     = typer.Typer(help="SSH key management",             no_args_is_help=True)
collab_app  = typer.Typer(help="Collaborator management",        no_args_is_help=True)

app.add_typer(profile_app, name="profile")
app.add_typer(repo_app,    name="repo")
app.add_typer(ssh_app,     name="ssh")
app.add_typer(collab_app,  name="collab")


# ── Callback: show logo ───────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def main(ctx: typer.Context):
    ui.print_logo()
    if ctx.invoked_subcommand is None:
        ui.info("Use [bold]--help[/bold] to see available commands.")


# ═══════════════════════════════════════════════════════════════════════════════
# PROFILE COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@profile_app.command("add")
def profile_add(
    name: str = typer.Argument(..., help="Profile name (e.g., personal, work)"),
):
    """Add a new GitHub account profile."""
    ui.print_logo()
    ui.info(f"Adding profile [bold]{name}[/bold]")
    ui.info("You need a GitHub Personal Access Token (classic) with scopes: [bold]repo, admin:public_key, admin:org, user[/bold]")
    ui.info("Get one at: [link=https://github.com/settings/tokens]https://github.com/settings/tokens[/link]\n")

    token = Prompt.ask("GitHub Personal Access Token", password=True)
    if not token:
        ui.error("Token cannot be empty.")
        raise typer.Exit(1)

    with ui.spinner("Verifying token with GitHub …"):
        try:
            client = GitHubClient(token)
            username = client.username()
        except SystemExit:
            ui.error("Invalid token or no network access.")
            raise typer.Exit(1)

    add_profile(name=name, token=token, username=username)
    ui.success(f"Profile [bold]{name}[/bold] added for GitHub user [bold]{username}[/bold]!")
    ui.info("Run [bold]githappens ssh setup[/bold] to generate and upload an SSH key for this profile.")


@profile_app.command("list")
def profile_list():
    """List all configured profiles."""
    ui.print_logo()
    profiles, active = list_profiles()
    if not profiles:
        ui.warn("No profiles configured. Run: [bold]githappens profile add <name>[/bold]")
        return
    ui.console.print(f"\n  Active profile: [bold bright_green]{active}[/bold bright_green]\n")
    ui.profiles_table(profiles, active)


@profile_app.command("use")
def profile_use(
    name: str = typer.Argument(..., help="Profile name to activate"),
):
    """Switch the active GitHub account profile."""
    set_active_profile(name)
    ui.success(f"Active profile set to [bold]{name}[/bold]")


@profile_app.command("remove")
def profile_remove(
    name: str = typer.Argument(..., help="Profile name to remove"),
):
    """Remove a GitHub account profile."""
    confirmed = Confirm.ask(f"Remove profile [bold]{name}[/bold]? This cannot be undone.")
    if not confirmed:
        ui.info("Cancelled.")
        return
    remove_profile(name)
    ui.success(f"Profile [bold]{name}[/bold] removed.")


# ═══════════════════════════════════════════════════════════════════════════════
# REPO COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@repo_app.command("create")
def repo_create(
    name: str = typer.Argument(..., help="Repository name"),
    private: bool = typer.Option(False, "--private", "-p", help="Make the repo private"),
    description: str = typer.Option("", "--description", "-d", help="Repository description"),
    no_init: bool = typer.Option(False, "--no-init", help="Skip auto-initializing with README"),
    profile: Optional[str] = typer.Option(None, "--profile", "-P", help="Profile to use"),
):
    """Create a new GitHub repository and return its URLs."""
    ui.print_logo()
    prof = resolve_profile(profile)
    client = GitHubClient(prof["token"])

    visibility = "private" if private else "public"
    ui.step(f"Creating [bold]{visibility}[/bold] repo [bold]{name}[/bold] on GitHub …")

    with ui.spinner(f"Creating {name} …"):
        result = client.create_repo(
            name=name,
            private=private,
            description=description,
            auto_init=not no_init,
        )

    ui.repo_panel(
        name=result.name,
        url=result.html_url,
        ssh_url=result.ssh_url,
        private=result.private,
        description=result.description,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# SSH COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

@ssh_app.command("setup")
def ssh_setup(
    profile: Optional[str] = typer.Option(None, "--profile", "-P", help="Profile to use"),
    title: Optional[str]   = typer.Option(None, "--title", "-t", help="Key title on GitHub (default: githappens-<profile>)"),
    force: bool            = typer.Option(False, "--force", "-f", help="Overwrite existing key"),
):
    """Generate an RSA SSH key pair and upload it to GitHub."""
    ui.print_logo()
    prof = resolve_profile(profile)
    profile_name = profile or _active_profile_name()
    client = GitHubClient(prof["token"])
    username = prof["username"]

    k_dir = keys_dir(profile_name)
    private_path = k_dir / "id_rsa"

    if private_path.exists() and not force:
        ui.warn(f"SSH key already exists at [bold]{private_path}[/bold]")
        ui.info("Use [bold]--force[/bold] to overwrite, or [bold]githappens ssh list[/bold] to see existing keys.")
        return

    # Generate and save key
    _, public_openssh, priv_path, pub_path = setup_ssh_for_profile(
        profile_name=profile_name,
        keys_dir=k_dir,
        github_username=username,
    )

    key_title = title or f"githappens-{profile_name}"

    ui.step(f"Uploading public key to GitHub as [bold]{key_title}[/bold] …")
    with ui.spinner("Uploading …"):
        client.add_ssh_key(title=key_title, public_key=public_openssh)

    update_ssh_key_path(profile_name, str(priv_path))

    ui.ssh_panel(
        profile=profile_name,
        pub_key=public_openssh,
        key_path=str(priv_path),
    )

    ui.console.print(
        f"\n  [grey62]Add to your SSH config (~/.ssh/config):[/grey62]\n"
        f"  [bright_green]Host github-{profile_name}[/bright_green]\n"
        f"    HostName github.com\n"
        f"    User git\n"
        f"    IdentityFile {priv_path}\n"
    )


@ssh_app.command("list")
def ssh_list(
    profile: Optional[str] = typer.Option(None, "--profile", "-P", help="Profile to use"),
):
    """List all SSH keys on the GitHub account."""
    ui.print_logo()
    prof = resolve_profile(profile)
    client = GitHubClient(prof["token"])

    with ui.spinner("Fetching SSH keys …"):
        keys = client.list_ssh_keys()

    if not keys:
        ui.warn("No SSH keys found on this GitHub account.")
        return

    from rich.table import Table
    from rich import box

    table = Table(box=box.ROUNDED, border_style=ui.PRIMARY, header_style=f"bold {ui.PRIMARY}")
    table.add_column("ID",    style="dim")
    table.add_column("Title", style="bold")
    table.add_column("Key (preview)")

    for k in keys:
        preview = k.key[:40] + "…" if len(k.key) > 40 else k.key
        table.add_row(str(k.key_id), k.title, preview)

    ui.console.print(table)


@ssh_app.command("delete")
def ssh_delete(
    key_id: int = typer.Argument(..., help="Key ID to delete (from 'ssh list')"),
    profile: Optional[str] = typer.Option(None, "--profile", "-P", help="Profile to use"),
):
    """Delete an SSH key from the GitHub account by ID."""
    ui.print_logo()
    prof = resolve_profile(profile)
    client = GitHubClient(prof["token"])

    confirmed = Confirm.ask(f"Delete SSH key [bold]#{key_id}[/bold] from GitHub?")
    if not confirmed:
        ui.info("Cancelled.")
        return

    with ui.spinner(f"Deleting key #{key_id} …"):
        client.delete_ssh_key(key_id)
    ui.success(f"SSH key #{key_id} deleted.")


# ═══════════════════════════════════════════════════════════════════════════════
# COLLAB COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

_PERMISSIONS = ["pull", "push", "admin", "maintain", "triage"]


@collab_app.command("add")
def collab_add(
    repo: str     = typer.Argument(..., help="Repository (owner/name or just name for your own)"),
    username: str = typer.Argument(..., help="GitHub username to invite"),
    permission: str = typer.Option("push", "--permission", "-p",
                                   help=f"Permission level: {', '.join(_PERMISSIONS)}"),
    profile: Optional[str] = typer.Option(None, "--profile", "-P", help="Profile to use"),
):
    """Add a collaborator to a repository and return the invite link."""
    ui.print_logo()
    if permission not in _PERMISSIONS:
        ui.error(f"Invalid permission '{permission}'. Choose from: {', '.join(_PERMISSIONS)}")
        raise typer.Exit(1)

    prof = resolve_profile(profile)
    client = GitHubClient(prof["token"])

    if "/" not in repo:
        repo = f"{prof['username']}/{repo}"

    ui.step(f"Adding [bold]{username}[/bold] to [bold]{repo}[/bold] with [bold]{permission}[/bold] permission …")

    with ui.spinner("Sending invite …"):
        result = client.add_collaborator(
            repo_full_name=repo,
            username=username,
            permission=permission,
        )

    ui.collab_panel(
        repo=repo,
        username=result.username,
        invite_url=result.invite_url,
        permission=result.permission,
    )


@collab_app.command("list")
def collab_list(
    repo: str = typer.Argument(..., help="Repository (owner/name or just name for your own)"),
    profile: Optional[str] = typer.Option(None, "--profile", "-P", help="Profile to use"),
):
    """List all collaborators on a repository."""
    ui.print_logo()
    prof = resolve_profile(profile)
    client = GitHubClient(prof["token"])

    if "/" not in repo:
        repo = f"{prof['username']}/{repo}"

    with ui.spinner(f"Fetching collaborators for {repo} …"):
        collabs = client.list_collaborators(repo)

    if not collabs:
        ui.info(f"No collaborators found on [bold]{repo}[/bold].")
        return

    from rich.table import Table
    from rich import box

    table = Table(box=box.ROUNDED, border_style=ui.ACCENT, header_style=f"bold {ui.ACCENT}")
    table.add_column("Username", style="bold")
    table.add_column("GitHub URL", style=ui.PRIMARY)

    for c in collabs:
        table.add_row(c["username"], c["url"])

    ui.console.print(f"\n  Collaborators on [bold]{repo}[/bold]:\n")
    ui.console.print(table)


@collab_app.command("remove")
def collab_remove(
    repo: str     = typer.Argument(..., help="Repository (owner/name)"),
    username: str = typer.Argument(..., help="GitHub username to remove"),
    profile: Optional[str] = typer.Option(None, "--profile", "-P", help="Profile to use"),
):
    """Remove a collaborator from a repository."""
    ui.print_logo()
    prof = resolve_profile(profile)
    client = GitHubClient(prof["token"])

    if "/" not in repo:
        repo = f"{prof['username']}/{repo}"

    confirmed = Confirm.ask(f"Remove [bold]{username}[/bold] from [bold]{repo}[/bold]?")
    if not confirmed:
        ui.info("Cancelled.")
        return

    with ui.spinner(f"Removing {username} …"):
        client.remove_collaborator(repo, username)
    ui.success(f"[bold]{username}[/bold] removed from [bold]{repo}[/bold].")


# ═══════════════════════════════════════════════════════════════════════════════
# ANALYZE COMMAND
# ═══════════════════════════════════════════════════════════════════════════════

@app.command("analyze")
def cmd_analyze(
    repo: str = typer.Argument(..., help="Repository to analyze (owner/name)"),
    profile: Optional[str] = typer.Option(None, "--profile", "-P", help="Profile to use"),
    gemini_key: Optional[str] = typer.Option(
        None, "--gemini-key", "-g",
        help="Gemini API key override (or set GEMINI_API_KEY in .env)",
        envvar="GEMINI_API_KEY",
    ),
):
    """
    🤖 AI-powered repository analysis using Antigravity + GitHub MCP.

    Analyzes the repo structure, activity, documentation, and health,
    then streams a detailed report to the terminal.
    """
    ui.print_logo()
    prof = resolve_profile(profile)
    client = GitHubClient(prof["token"])

    if "/" not in repo:
        repo = f"{prof['username']}/{repo}"

    ui.step(f"Fetching metadata for [bold]{repo}[/bold] …")
    with ui.spinner("Fetching repo info …"):
        summary = client.get_repo_summary(repo)

    ui.info(
        f"Repo: [bold]{summary['full_name']}[/bold]  •  "
        f"Stars: [bold]{summary['stars']}[/bold]  •  "
        f"Language: [bold]{summary['language']}[/bold]  •  "
        f"Open issues: [bold]{summary['open_issues']}[/bold]\n"
    )

    analysis = analyze_repo(
        repo_full_name=repo,
        repo_summary=summary,
        github_token=prof["token"],
        gemini_api_key=gemini_key,
    )

    ui.console.print(Markdown(analysis))


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _active_profile_name() -> str:
    from src.config import get_active_profile_name
    name = get_active_profile_name()
    if not name:
        ui.error("No active profile. Run: [bold]githappens profile add <name>[/bold]")
        raise SystemExit(1)
    return name


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app()
