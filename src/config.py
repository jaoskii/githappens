"""
config.py — Profile manager for GitPilot.

Profiles are stored in ~/.gitpilot/profiles.json.
Each profile holds a GitHub PAT (Fernet-encrypted), username, and SSH key path.
A master key is derived from a machine-unique secret and stored alongside.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

from src.display import error, warn

# ── Config directory ──────────────────────────────────────────────────────────
_CONFIG_DIR = Path(os.environ.get("GITHAPPENS_CONFIG_DIR", Path.home() / ".githappens"))
_PROFILES_FILE = _CONFIG_DIR / "profiles.json"
_KEY_FILE = _CONFIG_DIR / ".master.key"


def _ensure_config_dir():
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    # Restrict permissions on Unix-like systems
    if sys.platform != "win32":
        _CONFIG_DIR.chmod(0o700)


def _load_or_create_fernet() -> Fernet:
    """Load (or create) the Fernet master key for token encryption."""
    _ensure_config_dir()
    if _KEY_FILE.exists():
        key = _KEY_FILE.read_bytes()
    else:
        key = Fernet.generate_key()
        _KEY_FILE.write_bytes(key)
        if sys.platform != "win32":
            _KEY_FILE.chmod(0o600)
    return Fernet(key)


def _load_profiles() -> dict:
    _ensure_config_dir()
    if not _PROFILES_FILE.exists():
        return {"active": None, "profiles": {}}
    with open(_PROFILES_FILE, "r") as f:
        return json.load(f)


def _save_profiles(data: dict):
    _ensure_config_dir()
    with open(_PROFILES_FILE, "w") as f:
        json.dump(data, f, indent=2)
    if sys.platform != "win32":
        _PROFILES_FILE.chmod(0o600)


# ── Public API ────────────────────────────────────────────────────────────────

def config_dir() -> Path:
    """Return the config directory path."""
    return _CONFIG_DIR


def keys_dir(profile_name: str) -> Path:
    """Return the SSH keys directory for a given profile."""
    return _CONFIG_DIR / "keys" / profile_name


def list_profiles() -> tuple[dict, str | None]:
    """Return (profiles_dict, active_profile_name)."""
    data = _load_profiles()
    return data.get("profiles", {}), data.get("active")


def get_active_profile_name() -> str | None:
    data = _load_profiles()
    return data.get("active")


def get_profile(name: str) -> Optional[dict]:
    """Return decrypted profile dict or None if not found."""
    data = _load_profiles()
    prof = data.get("profiles", {}).get(name)
    if not prof:
        return None
    # Decrypt token
    fernet = _load_or_create_fernet()
    encrypted = prof.get("token_encrypted", "")
    try:
        token = fernet.decrypt(encrypted.encode()).decode() if encrypted else ""
    except Exception:
        warn(f"Could not decrypt token for profile '{name}'. Re-add the profile.")
        token = ""
    return {**prof, "token": token}


def resolve_profile(profile_name: str | None) -> dict:
    """Resolve a profile by name (or use active). Exits on failure."""
    name = profile_name or get_active_profile_name()
    if not name:
        error("No active profile. Run: [bold]gitpilot profile add <name>[/bold]")
        raise SystemExit(1)
    prof = get_profile(name)
    if not prof:
        error(f"Profile '{name}' not found. Run: [bold]gitpilot profile list[/bold]")
        raise SystemExit(1)
    if not prof.get("token"):
        error(f"Profile '{name}' has no token. Re-add it with: [bold]gitpilot profile add {name}[/bold]")
        raise SystemExit(1)
    return prof


def add_profile(name: str, token: str, username: str):
    """Add or update a profile with an encrypted PAT."""
    data = _load_profiles()
    fernet = _load_or_create_fernet()
    encrypted = fernet.encrypt(token.encode()).decode()
    token_hint = token[-4:] if len(token) >= 4 else "????"

    data.setdefault("profiles", {})[name] = {
        "username": username,
        "token_encrypted": encrypted,
        "token_hint": token_hint,
        "ssh_key_path": None,
    }
    # Set as active if first profile
    if not data.get("active"):
        data["active"] = name

    _save_profiles(data)


def set_active_profile(name: str):
    data = _load_profiles()
    if name not in data.get("profiles", {}):
        error(f"Profile '{name}' not found.")
        raise SystemExit(1)
    data["active"] = name
    _save_profiles(data)


def remove_profile(name: str):
    data = _load_profiles()
    profiles = data.get("profiles", {})
    if name not in profiles:
        error(f"Profile '{name}' not found.")
        raise SystemExit(1)
    del profiles[name]
    if data.get("active") == name:
        data["active"] = next(iter(profiles), None)
    _save_profiles(data)


def update_ssh_key_path(profile_name: str, key_path: str):
    """Persist the SSH key path for a profile after generation."""
    data = _load_profiles()
    if profile_name in data.get("profiles", {}):
        data["profiles"][profile_name]["ssh_key_path"] = key_path
        _save_profiles(data)
