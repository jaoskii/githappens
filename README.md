# Git Happens 🌿

> *Because git happens.* — AI-Powered GitHub Manager for the terminal.

**Git Happens** is a cross-platform CLI tool (Windows / Linux / macOS) that lets you manage your GitHub accounts, repositories, SSH keys, and collaborators — all from the terminal, powered by **Google's Antigravity AI** and the **GitHub MCP server**.

No browser. No manual steps. No excuses.

---

## ⚡ Quick Command Reference

> Run all commands from inside the project folder with the venv activated.

```bash
cd /path/to/githappens
source .venv/bin/activate        # macOS / Linux
.venv\Scripts\activate           # Windows
```

### 👤 Profile (Account Management)
| Command | What it does |
|---|---|
| `python githappens.py profile add <name>` | Add a new GitHub account |
| `python githappens.py profile list` | List all accounts + active one |
| `python githappens.py profile use <name>` | Switch active account |
| `python githappens.py profile remove <name>` | Delete a profile |

### 📁 Repository
| Command | What it does |
|---|---|
| `python githappens.py repo create <name>` | Create a public repo, returns URL |
| `python githappens.py repo create <name> --private` | Create a private repo |
| `python githappens.py repo create <name> --description "..."` | Add a description |
| `python githappens.py repo create <name> --no-init` | Skip auto README |
| `python githappens.py repo create <name> --profile work` | Create under a specific account |

### 🔑 SSH Keys
| Command | What it does |
|---|---|
| `python githappens.py ssh setup` | Generate key pair + upload to GitHub |
| `python githappens.py ssh setup --force` | Overwrite existing key |
| `python githappens.py ssh setup --title "my-laptop"` | Custom key title on GitHub |
| `python githappens.py ssh list` | List all SSH keys on GitHub account |
| `python githappens.py ssh delete <key-id>` | Delete an SSH key by ID |

### 👥 Collaborators
| Command | What it does |
|---|---|
| `python githappens.py collab add <repo> <username>` | Add collaborator (push access) |
| `python githappens.py collab add <repo> <username> --permission admin` | Add with custom permission |
| `python githappens.py collab list <repo>` | List all collaborators |
| `python githappens.py collab remove <repo> <username>` | Remove a collaborator |

### 🤖 AI Analysis
| Command | What it does |
|---|---|
| `python githappens.py analyze <owner/repo>` | Full AI analysis of any repo |
| `python githappens.py analyze <repo>` | Analyze your own repo (short form) |
| `python githappens.py analyze <repo> --profile work` | Analyze using a specific account |

> Every command supports `--profile <name>` to target a specific account. If omitted, uses the active profile.

---

## ✨ Features

### 🗂️ Multi-Account Profile Management
Manage multiple GitHub accounts (personal, work, client, or any custom name) from one tool. Each account is stored as a **named profile** with its token **Fernet-encrypted** locally. Switch between accounts with a single command — every other command automatically uses your active profile, or you can target a specific one with `--profile`.

### 📁 Repository Creation
Create a new GitHub repository instantly by just providing a name. Git Happens returns:
- The **HTTPS URL** for cloning
- The **SSH URL** for git operations
- Visibility (public/private), description, and branch info

All in a beautiful terminal panel.

### 🔑 Automatic SSH Key Setup
SSH key management — fully automated, no shell commands:
- **Generates** a 4096-bit RSA key pair using pure Python (`cryptography` library)
- **Saves** the private key to `~/.githappens/keys/<profile>/id_rsa`
- **Uploads** the public key to your GitHub account automatically
- Works identically on **Windows, Linux, and macOS** (no `ssh-keygen` needed)

### 👥 Collaborator Management & Invite Links
Add GitHub users to any of your repositories:
- Set **permission levels**: `pull`, `push`, `admin`, `maintain`, `triage`
- Returns a **shareable invite link** the collaborator can use to accept
- List all current collaborators on any repo
- Remove collaborators from repos

### 🤖 AI-Powered Repository Analysis
The flagship feature. Powered by **Google Antigravity SDK** connected to the **GitHub MCP server**, the AI agent:
- Reads the repository's README, file structure, open issues, and recent commits
- Analyzes language breakdown, topics, stars, forks, and activity
- Produces a **structured analysis report** with:
  - Project overview summary
  - Tech stack breakdown
  - Health score (1–10) across activity, docs, community, and maintenance
  - Strengths of the codebase
  - Concrete, actionable improvement suggestions
  - One-line verdict

---

## 👤 Account Setup Guide

### Profile Names — Fully Custom ✅

Profile names can be **anything you want**. There are no reserved names. Examples:

```bash
python githappens.py profile add personal
python githappens.py profile add work
python githappens.py profile add freelance
python githappens.py profile add client-acme
python githappens.py profile add opensource
python githappens.py profile add jao-inventlabs
python githappens.py profile add staging-bot
```

Each profile is completely independent — separate token, separate SSH keys, separate active state.

---

### Setting Up Multiple Accounts

#### Step 1 — Add your accounts one by one

```bash
# Personal GitHub account
python githappens.py profile add personal
# → prompts for token → verifies → saves

# Work GitHub account
python githappens.py profile add work
# → prompts for a different token → verifies → saves

# Freelance / client account
python githappens.py profile add freelance
# → prompts for another token → verifies → saves
```

#### Step 2 — Set up SSH keys per account

```bash
python githappens.py ssh setup --profile personal
python githappens.py ssh setup --profile work
python githappens.py ssh setup --profile freelance
```

Each generates its own key pair stored at:
```
~/.githappens/keys/personal/id_rsa
~/.githappens/keys/work/id_rsa
~/.githappens/keys/freelance/id_rsa
```

#### Step 3 — Add SSH entries to ~/.ssh/config

```
Host github-personal
  HostName github.com
  User git
  IdentityFile ~/.githappens/keys/personal/id_rsa

Host github-work
  HostName github.com
  User git
  IdentityFile ~/.githappens/keys/work/id_rsa

Host github-freelance
  HostName github.com
  User git
  IdentityFile ~/.githappens/keys/freelance/id_rsa
```

#### Step 4 — Switch between accounts

```bash
# Use personal as default
python githappens.py profile use personal

# Or target any account per-command with --profile
python githappens.py repo create client-site --profile freelance
python githappens.py collab add my-repo dev-guy --profile work
python githappens.py analyze some/repo --profile personal
```

#### Step 5 — Check your setup anytime

```bash
python githappens.py profile list
```

```
  Active profile: personal

 ●  personal    jaoskii        ✔    ••••xxxx
    work        jaoskii-corp   ✔    ••••yyyy
    freelance   jaoskii-dev    —    ••••zzzz
```

---

### Overwriting an Existing Profile

Just run `profile add` again with the same name — it overwrites automatically:

```bash
python githappens.py profile add personal
# → enter new token → saves over the old one ✅
```

---


## 📋 Requirements

| Requirement | Version | Notes |
|---|---|---|
| Python | 3.10+ | 3.14 recommended |
| Node.js + npx | 16+ | Required for AI analysis only |
| GitHub PAT | Classic | See token setup below |
| Gemini API Key | — | Required for `analyze` command |

---

## 🚀 Installation

### 1. Clone / navigate to the project

```bash
cd /path/to/gitpilot
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate the virtual environment

**macOS / Linux:**
```bash
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and add your Gemini API key:

```
GEMINI_API_KEY=your_gemini_api_key_here
```

> Get a free Gemini API key at: https://aistudio.google.com/app/api-keys

---

## 🔑 GitHub Token Setup

Git Happens needs a **Personal Access Token (Classic)** to talk to GitHub.

1. Go to **https://github.com/settings/tokens**
2. Click **"Generate new token (classic)"**
3. Give it a name (e.g., `git-happens`)
4. Set an expiration (90 days recommended)
5. Select these scopes:

| Scope | Used for |
|---|---|
| ✅ `repo` | Create repos, read/write code |
| ✅ `admin:public_key` | Upload SSH keys to your account |
| ✅ `admin:org` | Add collaborators to org repos |
| ✅ `user` | Read your GitHub username |

6. Click **Generate token** and copy it — you won't see it again.

> ⚠️ Keep this token secret. Git Happens encrypts it locally with Fernet encryption.

---

## 📖 Usage Guide

All commands follow this structure:

```
python githappens.py <command group> <action> [arguments] [options]
```

Always run from inside the project directory with the venv activated:

```bash
cd /path/to/gitpilot
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
```

---

## 👤 Profile Commands

Profiles are named GitHub accounts. Config is stored in `~/.githappens/profiles.json`.

### Add a profile

```bash
python githappens.py profile add personal
```

You'll be prompted for your GitHub token. Git Happens verifies it with GitHub automatically and stores your username.

```bash
# Add a second account
python githappens.py profile add work
```

### List all profiles

```bash
python githappens.py profile list
```

Shows a table of all accounts with the active one marked with ●.

### Switch active profile

```bash
python githappens.py profile use work
```

All commands will now use the `work` account by default.

### Remove a profile

```bash
python githappens.py profile remove old-account
```

---

## 📁 Repository Commands

### Create a repository

```bash
# Create a public repo
python githappens.py repo create my-project

# Create a private repo with a description
python githappens.py repo create my-project --private --description "My awesome project"

# Create without auto-initializing README
python githappens.py repo create my-project --no-init

# Create on a specific account
python githappens.py repo create my-project --profile work
```

**Output includes:**
- ✅ HTTPS URL (`https://github.com/you/my-project`)
- ✅ SSH URL (`git@github.com:you/my-project.git`)
- ✅ Visibility badge (public/private)

---

## 🔑 SSH Key Commands

### Set up SSH (generate + upload automatically)

```bash
python githappens.py ssh setup
```

This does everything:
1. Generates a 4096-bit RSA key pair (pure Python, no shell)
2. Saves it to `~/.githappens/keys/<profile>/id_rsa`
3. Uploads the public key to your GitHub account
4. Shows you the SSH config snippet to add to `~/.ssh/config`

```bash
# Set up SSH for a specific profile
python githappens.py ssh setup --profile work

# Use a custom key title on GitHub
python githappens.py ssh setup --title "my-laptop"

# Force regenerate (overwrites existing key)
python githappens.py ssh setup --force
```

### List SSH keys on GitHub

```bash
python githappens.py ssh list
```

### Delete an SSH key

```bash
# First, list keys to get the ID
python githappens.py ssh list

# Then delete by ID
python githappens.py ssh delete 12345678
```

### SSH Config (recommended)

After setup, add this to your `~/.ssh/config` for seamless git operations:

```
Host github-personal
  HostName github.com
  User git
  IdentityFile ~/.githappens/keys/personal/id_rsa

Host github-work
  HostName github.com
  User git
  IdentityFile ~/.githappens/keys/work/id_rsa
```

Then clone using:
```bash
git clone git@github-personal:username/repo.git
git clone git@github-work:company/repo.git
```

---

## 👥 Collaborator Commands

### Add a collaborator

```bash
# Add with default push permission
python githappens.py collab add my-repo their-username

# Add with specific permission
python githappens.py collab add my-repo their-username --permission admin

# Full repo path (for repos you don't own)
python githappens.py collab add owner/my-repo their-username --permission pull
```

**Permission levels:**
| Level | Can do |
|---|---|
| `pull` | Read-only |
| `push` | Read + write (default) |
| `maintain` | Push + manage issues/PRs |
| `triage` | Manage issues without write |
| `admin` | Full access including settings |

**Returns:** An invite link the collaborator can click to accept.

### List collaborators

```bash
python githappens.py collab list my-repo
```

### Remove a collaborator

```bash
python githappens.py collab remove my-repo their-username
```

---

## 🤖 AI Analysis Command

### Analyze a repository

```bash
# Analyze any public repo
python githappens.py analyze torvalds/linux

# Analyze one of your own repos (just the name)
python githappens.py analyze my-project

# Analyze using a specific profile's token
python githappens.py analyze owner/repo --profile work

# Pass Gemini key directly (overrides .env)
python githappens.py analyze owner/repo --gemini-key AIza...
```

The AI agent will:
1. Fetch repo metadata (stars, language, issues, commits, topics)
2. Use the GitHub MCP server to explore the repo deeper (README, files, issues)
3. Stream a full analysis report to your terminal

**Example output sections:**
- **Overview** — What the project does
- **Tech Stack** — Languages, frameworks, tools
- **Health Score** — Rated 1–10
- **Strengths** — What the repo does well
- **Suggestions** — Actionable improvements
- **Verdict** — One-line summary

> Requires `GEMINI_API_KEY` in your `.env` file and `npx` installed.

---

## 🔄 Multi-Account Workflow Example

```bash
# Morning: work on client project
python githappens.py profile use client
python githappens.py repo create client-dashboard --private
python githappens.py collab add client-dashboard boss@company --permission admin

# Afternoon: personal project
python githappens.py profile use personal
python githappens.py repo create side-project
python githappens.py ssh setup

# Quick analysis of a competitor's open source project
python githappens.py analyze facebook/react --profile personal
```

---

## 📁 File Structure

```
gitpilot/
├── githappens.py          # ← Main CLI entry point
├── src/
│   ├── config.py          # Profile manager (encrypted tokens)
│   ├── github_client.py   # GitHub REST API wrapper
│   ├── ssh_manager.py     # Pure Python SSH key generation
│   ├── ai_agent.py        # Antigravity AI + GitHub MCP
│   └── display.py         # Rich terminal UI helpers
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── .env                   # Your local secrets (gitignored)
└── .venv/                 # Virtual environment (gitignored)
```

**Config stored at:**
```
~/.githappens/
├── profiles.json           # All account profiles (tokens encrypted)
├── .master.key             # Fernet encryption key (keep safe!)
└── keys/
    ├── personal/
    │   ├── id_rsa          # Private key (chmod 600)
    │   └── id_rsa.pub      # Public key
    └── work/
        ├── id_rsa
        └── id_rsa.pub
```

---

## 🛠️ Troubleshooting

**`No active profile` error**
```bash
python githappens.py profile add personal
```

**`Invalid token` error**
- Make sure you copied the full token
- Check the token hasn't expired at https://github.com/settings/tokens
- Verify the required scopes are checked

**`GEMINI_API_KEY` not found (analyze command)**
- Copy `.env.example` to `.env`
- Add your key: `GEMINI_API_KEY=AIza...`
- Or pass it directly: `--gemini-key AIza...`

**`npx` not found (analyze command)**
- Install Node.js from https://nodejs.org
- `npx` is included with Node.js 16+

**SSH key already exists warning**
```bash
python githappens.py ssh setup --force
```

**Windows: venv activation blocked by execution policy**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\Activate.ps1
```

---

## 🧰 Tech Stack

| Library | Purpose |
|---|---|
| `typer` | CLI framework with auto-generated help |
| `rich` | Beautiful terminal output (tables, panels, spinners) |
| `PyGithub` | GitHub REST API client |
| `cryptography` | RSA key generation + Fernet token encryption |
| `google-antigravity` | Antigravity SDK for AI analysis |
| `python-dotenv` | `.env` file loading |

---

## 📄 License

MIT — do whatever you want with it. And remember: *git happens*.
