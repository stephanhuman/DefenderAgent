"""Repository management for Azure DevOps"""

import re
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
import git
from git import Repo
from src.utils.logger import setup_logger
from .auth import AzureDevOpsAuth

logger = setup_logger(__name__)


class RepositoryManager:
    """Manage Azure DevOps repository operations"""

    def __init__(self, auth: AzureDevOpsAuth, workspace_dir: Path):
        """
        Initialize repository manager.

        Args:
            auth: Azure DevOps authentication instance
            workspace_dir: Directory for cloning repositories
        """
        self.auth = auth
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self.git_client = auth.get_git_client()

    @staticmethod
    def parse_repo_url(repo_url: str) -> dict:
        """
        Parse Azure DevOps repository URL.

        Args:
            repo_url: Repository URL

        Returns:
            Dictionary with organization, project, and repo name

        Example:
            https://dev.azure.com/myorg/myproject/_git/myrepo
        """
        # Pattern: https://dev.azure.com/{org}/{project}/_git/{repo}
        pattern = r'https://dev\.azure\.com/([^/]+)/([^/]+)/_git/(.+?)(?:\.git)?$'
        match = re.match(pattern, repo_url)

        if not match:
            raise ValueError(f"Invalid Azure DevOps repository URL: {repo_url}")

        org, project, repo = match.groups()
        return {
            "organization": org,
            "project": project,
            "repository": repo
        }

    def clone_repository(
        self,
        repo_url: str,
        branch: Optional[str] = None,
        local_name: Optional[str] = None
    ) -> Repo:
        """
        Clone Azure DevOps repository.

        Args:
            repo_url: Repository URL
            branch: Branch to checkout (defaults to default branch)
            local_name: Local directory name (defaults to repo name)

        Returns:
            GitPython Repo object
        """
        repo_info = self.parse_repo_url(repo_url)

        # Determine local directory
        if local_name:
            local_path = self.workspace_dir / local_name
        else:
            local_path = self.workspace_dir / repo_info["repository"]

        # Remove existing directory if it exists
        if local_path.exists():
            logger.warning(f"Directory {local_path} already exists, removing...")
            import shutil
            shutil.rmtree(local_path)

        # Get authenticated clone URL
        clone_url = self.auth.get_clone_url(
            repo_info["project"],
            repo_info["repository"]
        )

        logger.info(f"Cloning repository: {repo_info['repository']} to {local_path}")

        try:
            # Clone repository
            repo = Repo.clone_from(
                clone_url,
                local_path,
                branch=branch,
                depth=1  # Shallow clone for faster cloning
            )

            logger.info(f"Successfully cloned {repo_info['repository']}")
            return repo

        except git.exc.GitCommandError as e:
            logger.error(f"Failed to clone repository: {e}")
            raise

    def get_repository(self, local_path: Path) -> Repo:
        """
        Get existing repository.

        Args:
            local_path: Path to local repository

        Returns:
            GitPython Repo object
        """
        if not local_path.exists():
            raise ValueError(f"Repository not found: {local_path}")

        return Repo(local_path)

    def fetch_updates(self, repo: Repo, remote: str = "origin") -> None:
        """
        Fetch updates from remote.

        Args:
            repo: GitPython Repo object
            remote: Remote name (default: origin)
        """
        logger.info(f"Fetching updates from {remote}...")
        repo.remote(remote).fetch()
        logger.info("Fetch completed")

    def pull_updates(self, repo: Repo, branch: Optional[str] = None) -> None:
        """
        Pull updates from remote.

        Args:
            repo: GitPython Repo object
            branch: Branch to pull (defaults to current branch)
        """
        if branch:
            repo.git.checkout(branch)

        current_branch = repo.active_branch.name
        logger.info(f"Pulling updates for branch: {current_branch}")

        repo.remote("origin").pull()
        logger.info("Pull completed")

    def push_changes(
        self,
        repo: Repo,
        branch: Optional[str] = None,
        force: bool = False
    ) -> None:
        """
        Push changes to remote.

        Args:
            repo: GitPython Repo object
            branch: Branch to push (defaults to current branch)
            force: Force push (use with caution)
        """
        if branch:
            repo.git.checkout(branch)

        current_branch = repo.active_branch.name
        logger.info(f"Pushing changes for branch: {current_branch}")

        if force:
            logger.warning("Force pushing changes...")
            repo.remote("origin").push(force=True)
        else:
            repo.remote("origin").push()

        logger.info("Push completed")

    def get_repo_info(self, repo: Repo) -> dict:
        """
        Get repository information.

        Args:
            repo: GitPython Repo object

        Returns:
            Dictionary with repository info
        """
        return {
            "path": str(repo.working_dir),
            "current_branch": repo.active_branch.name,
            "remotes": [remote.name for remote in repo.remotes],
            "is_dirty": repo.is_dirty(),
            "untracked_files": repo.untracked_files
        }
