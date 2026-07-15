#!/usr/bin/env python3
"""
setup.py — Automated prerequisite installer for Git Happens.

Checks and installs everything needed to run Git Happens:
  ✔ Python 3.10+
  ✔ pip
  ✔ Node.js + npx (for AI analysis)
  ✔ Virtual environment (.venv)
  ✔ Python dependencies (requirements.txt)
  ✔ .env file from .env.example

Run this once before using Git Happens:
    python setup.py          # macOS / Linux / Windows
    python3 setup.py         # macOS / Linux (explicit)
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

# ── ANSI colors (works on all modern terminals) ───────────────────────────────
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def ok(msg):    print(f"  {GREEN}✔{RESET}  {msg}")
def warn(msg):  print(f"  {YELLOW}⚠{RESET}  {msg}")
def fail(msg):  print(f"  {RED}✘{RESET}  {msg}")
def info(msg):  print(f"  {CYAN}→{RESET}  {msg}")
def header(msg): print(f"\n{BOLD}{msg}{RESET}")

IS_WINDOWS = sys.platform == "win32"
ROOT = Path(__file__).parent.resolve()
VENV_DIR = ROOT / ".venv"
VENV_PYTHON = VENV_DIR / ("Scripts" if IS_WINDOWS else "bin") / ("python.exe" if IS_WINDOWS else "python")
VENV_PIP    = VENV_DIR / ("Scripts" if IS_WINDOWS else "bin") / ("pip.exe" if IS_WINDOWS else "pip")

BANNER = r"""
   ___  _ _     _   _
  / __|| | |_  | | | | __ _ _ __  _ __   ___ _ __  ___
 | (_ ||_   _| | |_| |/ _` | '_ \| '_ \ / _ \ '_ \/ __|
  \___||_|_|   |_|__/ \__,_| .__/| .__/ \___| .__/|___|
                            |_|   |_|        |_|

  Setup & Prerequisites Installer
"""

# ══════════════════════════════════════════════════════════════════════════════
# CHECKS
# ══════════════════════════════════════════════════════════════════════════════

def check_python() -> bool:
    version = sys.version_info
    if version >= (3, 10):
        ok(f"Python {version.major}.{version.minor}.{version.micro} detected")
        return True
    else:
        fail(f"Python {version.major}.{version.minor} detected — Git Happens requires Python 3.10+")
        info("Download Python from: https://www.python.org/downloads/")
        return False


def check_pip() -> bool:
    try:
        import pip
        ok("pip is available")
        return True
    except ImportError:
        fail("pip not found")
        info("Install pip: https://pip.pypa.io/en/stable/installation/")
        return False


def check_nodejs() -> bool:
    node = shutil.which("node")
    npx  = shutil.which("npx")
    if node and npx:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        ok(f"Node.js {result.stdout.strip()} detected (npx available)")
        return True
    else:
        warn("Node.js / npx not found")
        warn("  The 'analyze' command requires Node.js to run the GitHub MCP server.")
        info("  Install Node.js (includes npx): https://nodejs.org/")
        info("  All other commands (profile, repo, ssh, collab) work without Node.js.")
        return False  # Non-fatal — only needed for analyze


def check_git() -> bool:
    git = shutil.which("git")
    if git:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        ok(f"{result.stdout.strip()} detected")
        return True
    else:
        warn("Git not found — optional but recommended")
        info("  Install git: https://git-scm.com/downloads")
        return False  # Non-fatal


# ══════════════════════════════════════════════════════════════════════════════
# SETUP STEPS
# ══════════════════════════════════════════════════════════════════════════════

def create_venv() -> bool:
    if VENV_DIR.exists():
        ok(f"Virtual environment already exists at {VENV_DIR}")
        return True
    info(f"Creating virtual environment at {VENV_DIR} …")
    try:
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        ok("Virtual environment created")
        return True
    except subprocess.CalledProcessError as e:
        fail(f"Failed to create virtual environment: {e}")
        return False


def install_requirements() -> bool:
    req_file = ROOT / "requirements.txt"
    if not req_file.exists():
        fail("requirements.txt not found")
        return False

    info("Installing Python dependencies …")
    try:
        subprocess.run(
            [str(VENV_PIP), "install", "--upgrade", "pip"],
            check=True, capture_output=True,
        )
        subprocess.run(
            [str(VENV_PIP), "install", "-r", str(req_file)],
            check=True,
        )
        ok("All Python dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        fail(f"Failed to install dependencies: {e}")
        return False


def setup_env_file() -> bool:
    env_file     = ROOT / ".env"
    env_example  = ROOT / ".env.example"

    if env_file.exists():
        ok(".env file already exists")
        return True

    if not env_example.exists():
        warn(".env.example not found — skipping .env creation")
        return True

    shutil.copy(env_example, env_file)
    ok(".env created from .env.example")
    warn("  Open .env and add your GEMINI_API_KEY for the 'analyze' command")
    info("  Get a free key at: https://aistudio.google.com/app/api-keys")
    return True


# ══════════════════════════════════════════════════════════════════════════════
# PRINT NEXT STEPS
# ══════════════════════════════════════════════════════════════════════════════

def print_next_steps(all_good: bool):
    header("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if IS_WINDOWS:
        activate = r".venv\Scripts\activate"
        run      = "python githappens.py"
    else:
        activate = "source .venv/bin/activate"
        run      = "python githappens.py"

    if all_good:
        print(f"\n  {GREEN}{BOLD}✔ Setup complete! Git Happens is ready.{RESET}\n")
    else:
        print(f"\n  {YELLOW}{BOLD}⚠ Setup finished with warnings. See above.{RESET}\n")

    print(f"  {BOLD}Next steps:{RESET}\n")
    print(f"  1. Activate the virtual environment:")
    print(f"     {CYAN}{activate}{RESET}\n")
    print(f"  2. Add your Gemini API key to .env (for AI analysis):")
    print(f"     {CYAN}GEMINI_API_KEY=your_key_here{RESET}\n")
    print(f"  3. Add your first GitHub account:")
    print(f"     {CYAN}{run} profile add personal{RESET}\n")
    print(f"  4. Set up SSH key:")
    print(f"     {CYAN}{run} ssh setup{RESET}\n")
    print(f"  5. Create a repo:")
    print(f"     {CYAN}{run} repo create my-project{RESET}\n")
    print(f"  Run {CYAN}{run} --help{RESET} to see all commands.\n")
    print(f"  GitHub Token (required): {CYAN}https://github.com/settings/tokens{RESET}")
    print(f"  Gemini API Key (analyze): {CYAN}https://aistudio.google.com/app/api-keys{RESET}\n")
    print(f"{'━' * 52}\n")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"{GREEN}{BANNER}{RESET}")

    # ── Step 1: Check prerequisites ───────────────────────────────────────────
    header("[ 1 / 4 ]  Checking prerequisites …")
    python_ok = check_python()
    pip_ok    = check_pip()
    check_nodejs()  # non-fatal
    check_git()     # non-fatal

    if not python_ok or not pip_ok:
        fail("Required prerequisites are missing. Please install them and re-run setup.")
        sys.exit(1)

    # ── Step 2: Create virtual environment ────────────────────────────────────
    header("[ 2 / 4 ]  Setting up virtual environment …")
    venv_ok = create_venv()
    if not venv_ok:
        sys.exit(1)

    # ── Step 3: Install dependencies ─────────────────────────────────────────
    header("[ 3 / 4 ]  Installing dependencies …")
    deps_ok = install_requirements()
    if not deps_ok:
        sys.exit(1)

    # ── Step 4: Set up .env ───────────────────────────────────────────────────
    header("[ 4 / 4 ]  Setting up environment file …")
    setup_env_file()

    # ── Done ──────────────────────────────────────────────────────────────────
    print_next_steps(all_good=True)


if __name__ == "__main__":
    main()
