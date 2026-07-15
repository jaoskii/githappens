"""
github_client.py — GitHub REST API wrapper using PyGithub.

Provides clean, typed methods for all GitPilot operations:
  - Repo creation
  - SSH key upload
  - Collaborator management & invite links
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from github import Github, GithubException, Auth
from github.Repository import Repository
from github.NamedUser import NamedUser

from src.display import error


# ── Result types ──────────────────────────────────────────────────────────────

@dataclass
class RepoResult:
    name: str
    full_name: str
    html_url: str
    ssh_url: str
    clone_url: str
    private: bool
    description: str


@dataclass
class CollabResult:
    username: str
    permission: str
    invite_url: Optional[str]  # None if user was added directly


@dataclass
class SshKeyResult:
    key_id: int
    title: str
    key: str
    url: str


# ── Client ────────────────────────────────────────────────────────────────────

class GitHubClient:
    """Wrapper around PyGithub for GitPilot operations."""

    def __init__(self, token: str):
        auth = Auth.Token(token)
        self._gh = Github(auth=auth)
        self._user: NamedUser | None = None

    def _get_user(self) -> NamedUser:
        if not self._user:
            self._user = self._gh.get_user()
        return self._user

    def username(self) -> str:
        return self._get_user().login

    # ── Repos ─────────────────────────────────────────────────────────────────

    def create_repo(
        self,
        name: str,
        private: bool = False,
        description: str = "",
        auto_init: bool = True,
    ) -> RepoResult:
        """Create a new repository under the authenticated user."""
        try:
            repo: Repository = self._get_user().create_repo(
                name=name,
                private=private,
                description=description,
                auto_init=auto_init,
            )
            return RepoResult(
                name=repo.name,
                full_name=repo.full_name,
                html_url=repo.html_url,
                ssh_url=repo.ssh_url,
                clone_url=repo.clone_url,
                private=repo.private,
                description=repo.description or "",
            )
        except GithubException as e:
            _gh_error("create repo", e)

    def get_repo(self, full_name: str) -> Repository:
        """Fetch a repo by 'owner/name'."""
        try:
            return self._gh.get_repo(full_name)
        except GithubException as e:
            _gh_error("get repo", e)

    def update_repo_visibility(self, repo_full_name: str, private: bool) -> RepoResult:
        """Update repository visibility between public and private."""
        try:
            repo = self.get_repo(repo_full_name)
            repo.edit(private=private)
            return RepoResult(
                name=repo.name,
                full_name=repo.full_name,
                html_url=repo.html_url,
                ssh_url=repo.ssh_url,
                clone_url=repo.clone_url,
                private=repo.private,
                description=repo.description or "",
            )
        except GithubException as e:
            _gh_error("update repository visibility", e)

    # ── SSH Keys ──────────────────────────────────────────────────────────────

    def add_ssh_key(self, title: str, public_key: str) -> SshKeyResult:
        """Upload a public SSH key to the authenticated user's GitHub account."""
        try:
            key = self._get_user().create_key(title=title, key=public_key.strip())
            return SshKeyResult(
                key_id=key.id,
                title=key.title,
                key=key.key,
                url=key.url,
            )
        except GithubException as e:
            _gh_error("upload SSH key", e)

    def list_ssh_keys(self) -> list[SshKeyResult]:
        """List all SSH keys on the authenticated user's account."""
        try:
            keys = self._get_user().get_keys()
            return [
                SshKeyResult(key_id=k.id, title=k.title, key=k.key, url=k.url)
                for k in keys
            ]
        except GithubException as e:
            _gh_error("list SSH keys", e)

    def delete_ssh_key(self, key_id: int):
        """Delete an SSH key by ID."""
        try:
            key = self._get_user().get_key(key_id)
            key.delete()
        except GithubException as e:
            _gh_error("delete SSH key", e)

    # ── Collaborators ─────────────────────────────────────────────────────────

    def add_collaborator(
        self,
        repo_full_name: str,
        username: str,
        permission: str = "push",
    ) -> CollabResult:
        """
        Add a collaborator to a repo.

        permission: 'pull' | 'push' | 'admin' | 'maintain' | 'triage'

        Returns CollabResult with invite_url if an invitation was sent,
        or None if the user was added directly (already a member).
        """
        try:
            repo = self.get_repo(repo_full_name)
            invitation = repo.add_to_collaborators(username, permission=permission)

            invite_url = None
            if invitation and hasattr(invitation, "html_url"):
                invite_url = invitation.html_url

            return CollabResult(
                username=username,
                permission=permission,
                invite_url=invite_url,
            )
        except GithubException as e:
            _gh_error("add collaborator", e)

    def list_collaborators(self, repo_full_name: str) -> list[dict]:
        """List all collaborators on a repo."""
        try:
            repo = self.get_repo(repo_full_name)
            return [
                {"username": c.login, "url": c.html_url}
                for c in repo.get_collaborators()
            ]
        except GithubException as e:
            _gh_error("list collaborators", e)

    def remove_collaborator(self, repo_full_name: str, username: str):
        """Remove a collaborator from a repo."""
        try:
            repo = self.get_repo(repo_full_name)
            repo.remove_from_collaborators(username)
        except GithubException as e:
            _gh_error("remove collaborator", e)

    # ── Repo Info (for AI analysis) ───────────────────────────────────────────

    def get_repo_summary(self, full_name: str) -> dict:
        """
        Fetch a structured summary of a repo for the AI analysis agent.
        Returns a dict with metadata the agent can use as context.
        """
        try:
            repo = self.get_repo(full_name)
            languages = dict(repo.get_languages())
            topics    = repo.get_topics()

            recent_commits = []
            try:
                for commit in repo.get_commits()[:5]:
                    recent_commits.append({
                        "sha":     commit.sha[:7],
                        "message": commit.commit.message.split("\n")[0],
                        "author":  commit.commit.author.name,
                        "date":    commit.commit.author.date.isoformat(),
                    })
            except Exception:
                pass

            open_issues_count = repo.open_issues_count
            return {
                "name":              repo.name,
                "full_name":         repo.full_name,
                "description":       repo.description or "",
                "url":               repo.html_url,
                "private":           repo.private,
                "default_branch":    repo.default_branch,
                "stars":             repo.stargazers_count,
                "forks":             repo.forks_count,
                "open_issues":       open_issues_count,
                "language":          repo.language or "Unknown",
                "languages":         languages,
                "topics":            topics,
                "created_at":        repo.created_at.isoformat(),
                "updated_at":        repo.updated_at.isoformat(),
                "recent_commits":    recent_commits,
                "license":           repo.license.name if repo.license else None,
            }
        except GithubException as e:
            _gh_error("fetch repo info", e)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _gh_error(action: str, exc: GithubException) -> None:
    """Format and raise a GitHub API error."""
    msg = exc.data.get("message", str(exc)) if isinstance(exc.data, dict) else str(exc)
    error(f"GitHub API error while {action}: {msg}")
    raise SystemExit(1)
