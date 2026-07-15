"""
ssh_manager.py — Pure Python SSH key generation and management.

Uses the `cryptography` library (no shell commands) so it works
identically on Windows, Linux, and macOS.
"""

import sys
from pathlib import Path

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.display import step, success, error


def generate_rsa_keypair(
    key_size: int = 4096,
    comment: str = "gitpilot",
) -> tuple[str, str]:
    """
    Generate an RSA key pair.

    Returns:
        (private_key_pem, public_key_openssh) as strings.
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size,
    )

    # Private key — PKCS8 PEM (no passphrase for ease of git use)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.OpenSSH,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()

    # Public key — OpenSSH format (what GitHub expects)
    public_openssh = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).decode()

    # Append comment (e.g., gitpilot-personal)
    public_openssh = public_openssh.strip() + f" {comment}\n"

    return private_pem, public_openssh


def save_keypair(
    keys_dir: Path,
    private_pem: str,
    public_openssh: str,
    filename: str = "id_rsa",
) -> tuple[Path, Path]:
    """
    Save a key pair to disk.

    Returns:
        (private_key_path, public_key_path)
    """
    keys_dir.mkdir(parents=True, exist_ok=True)

    private_path = keys_dir / filename
    public_path  = keys_dir / f"{filename}.pub"

    private_path.write_text(private_pem)
    public_path.write_text(public_openssh)

    # Restrict private key permissions on Unix
    if sys.platform != "win32":
        private_path.chmod(0o600)
        public_path.chmod(0o644)

    return private_path, public_path


def setup_ssh_for_profile(
    profile_name: str,
    keys_dir: Path,
    github_username: str,
) -> tuple[str, str, Path, Path]:
    """
    Full SSH setup flow: generate key pair and save to disk.

    Returns:
        (private_pem, public_openssh, private_path, public_path)
    """
    step(f"Generating RSA 4096-bit key pair for profile [bold]{profile_name}[/bold] …")

    comment = f"githappens-{profile_name}-{github_username}"
    private_pem, public_openssh = generate_rsa_keypair(comment=comment)

    private_path, public_path = save_keypair(keys_dir, private_pem, public_openssh)

    success(f"Key pair saved → {private_path}")
    return private_pem, public_openssh, private_path, public_path


def read_public_key(key_path: Path) -> str | None:
    """Read an existing public key from disk."""
    pub_path = Path(str(key_path) + ".pub") if not str(key_path).endswith(".pub") else key_path
    if pub_path.exists():
        return pub_path.read_text().strip()
    return None
