"""
display.py — Rich terminal UI helpers for Git Happens.
All visual output goes through here for a consistent look.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich import box
import contextlib

console = Console()

# ── Brand colours ────────────────────────────────────────────────────────────
PRIMARY   = "bright_green"
SUCCESS   = "green"
WARNING   = "yellow"
ERROR     = "bright_red"
MUTED     = "grey62"
ACCENT    = "cyan"

LOGO = r"""
   ___  _ _     _   _
  / __|| | |_  | | | | __ _ _ __  _ __   ___ _ __  ___
 | (_ ||_   _| | |_| |/ _` | '_ \| '_ \ / _ \ '_ \/ __|
  \___||_|_|   |_|__/ \__,_| .__/| .__/ \___| .__/|___|
                            |_|   |_|        |_|
"""


def print_logo():
    console.print(f"[{PRIMARY}]{LOGO}[/{PRIMARY}]")
    console.print(f"  [{MUTED}]Because git happens — AI-Powered GitHub Manager  •  v1.0.0[/{MUTED}]\n")


def success(msg: str):
    console.print(f"[{SUCCESS}]✔[/{SUCCESS}]  {msg}")


def error(msg: str):
    console.print(f"[{ERROR}]✘[/{ERROR}]  {msg}")


def warn(msg: str):
    console.print(f"[{WARNING}]⚠[/{WARNING}]  {msg}")


def info(msg: str):
    console.print(f"[{PRIMARY}]ℹ[/{PRIMARY}]  {msg}")


def step(msg: str):
    console.print(f"[{ACCENT}]→[/{ACCENT}]  {msg}")


def panel(title: str, content: str, color: str = PRIMARY):
    console.print(
        Panel(
            content,
            title=f"[bold {color}]{title}[/bold {color}]",
            border_style=color,
            padding=(1, 2),
        )
    )


def repo_panel(name: str, url: str, ssh_url: str, private: bool, description: str = ""):
    """Display a newly created repo in a nice panel."""
    priv_badge = f"[{WARNING}]private[/{WARNING}]" if private else f"[{SUCCESS}]public[/{SUCCESS}]"
    content = (
        f"[bold]Name:[/bold]        {name}\n"
        f"[bold]Visibility:[/bold]  {priv_badge}\n"
        f"[bold]HTTPS URL:[/bold]   [{PRIMARY}]{url}[/{PRIMARY}]\n"
        f"[bold]SSH URL:[/bold]     [{ACCENT}]{ssh_url}[/{ACCENT}]"
    )
    if description:
        content += f"\n[bold]Description:[/bold] {description}"
    panel("🎉 Repository Created", content, SUCCESS)


def ssh_panel(profile: str, pub_key: str, key_path: str):
    """Display SSH key info after generation."""
    content = (
        f"[bold]Profile:[/bold]    {profile}\n"
        f"[bold]Key path:[/bold]   {key_path}\n\n"
        f"[bold]Public key:[/bold]\n[{MUTED}]{pub_key[:72]}...[/{MUTED}]"
    )
    panel("🔑 SSH Key Generated & Uploaded", content, PRIMARY)


def collab_panel(repo: str, username: str, invite_url: str | None, permission: str):
    """Display collaborator add result."""
    content = (
        f"[bold]Repo:[/bold]       {repo}\n"
        f"[bold]User:[/bold]       {username}\n"
        f"[bold]Permission:[/bold] {permission}\n"
    )
    if invite_url:
        content += f"[bold]Invite URL:[/bold] [{PRIMARY}]{invite_url}[/{PRIMARY}]"
    else:
        content += f"[{SUCCESS}]User added directly (no invite needed)[/{SUCCESS}]"
    panel("👥 Collaborator Added", content, ACCENT)


def profiles_table(profiles: dict, active: str):
    """Render a table of all configured profiles."""
    table = Table(
        box=box.ROUNDED,
        border_style=PRIMARY,
        show_header=True,
        header_style=f"bold {PRIMARY}",
    )
    table.add_column("", width=3)
    table.add_column("Profile", style="bold")
    table.add_column("Username")
    table.add_column("SSH Key")
    table.add_column("Token")

    for name, data in profiles.items():
        active_marker = f"[{SUCCESS}]●[/{SUCCESS}]" if name == active else " "
        username = data.get("username", "—")
        ssh = "✔" if data.get("ssh_key_path") else "—"
        token_hint = "••••" + data.get("token_hint", "????")
        table.add_row(active_marker, name, username, ssh, token_hint)

    console.print(table)


@contextlib.contextmanager
def spinner(msg: str):
    """Context manager for a spinner while doing async work."""
    with Progress(
        SpinnerColumn(spinner_name="dots", style=PRIMARY),
        TextColumn(f"[{MUTED}]{msg}[/{MUTED}]"),
        transient=True,
        console=console,
    ) as progress:
        progress.add_task("", total=None)
        yield


def ai_stream_header(repo: str):
    console.print(
        Panel(
            f"Analyzing [{PRIMARY}]{repo}[/{PRIMARY}] …",
            title=f"[bold {ACCENT}]🤖 AI Analysis[/bold {ACCENT}]",
            border_style=ACCENT,
            padding=(0, 2),
        )
    )
