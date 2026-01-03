"""Branch management for Git repositories"""

from typing import Optional, List
from git import Repo
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class BranchManager:
    """Manage Git branches"""

    def __init__(self, repo: Repo):
        """
        Initialize branch manager.

        Args:
            repo: GitPython Repo object
        """
        self.repo = repo

    def create_branch(
        self,
        branch_name: str,
        base_branch: Optional[str] = None,
        checkout: bool = True
    ) -> None:
        """
        Create a new branch.

        Args:
            branch_name: Name of the new branch
            base_branch: Base branch to branch from (defaults to current branch)
            checkout: Whether to checkout the new branch
        """
        if base_branch:
            # Ensure base branch exists
            if base_branch not in self.repo.heads:
                logger.error(f"Base branch '{base_branch}' not found")
                raise ValueError(f"Base branch '{base_branch}' does not exist")

            # Checkout base branch first
            self.repo.git.checkout(base_branch)

        logger.info(f"Creating branch: {branch_name}")

        # Create new branch
        new_branch = self.repo.create_head(branch_name)

        if checkout:
            new_branch.checkout()
            logger.info(f"Checked out branch: {branch_name}")
        else:
            logger.info(f"Created branch: {branch_name} (not checked out)")

    def checkout_branch(self, branch_name: str) -> None:
        """
        Checkout an existing branch.

        Args:
            branch_name: Branch name to checkout
        """
        if branch_name not in self.repo.heads:
            raise ValueError(f"Branch '{branch_name}' does not exist")

        logger.info(f"Checking out branch: {branch_name}")
        self.repo.git.checkout(branch_name)

    def delete_branch(self, branch_name: str, force: bool = False) -> None:
        """
        Delete a branch.

        Args:
            branch_name: Branch name to delete
            force: Force delete even if unmerged
        """
        if branch_name not in self.repo.heads:
            raise ValueError(f"Branch '{branch_name}' does not exist")

        logger.info(f"Deleting branch: {branch_name}")
        self.repo.delete_head(branch_name, force=force)

    def list_branches(self, remote: bool = False) -> List[str]:
        """
        List all branches.

        Args:
            remote: List remote branches instead of local

        Returns:
            List of branch names
        """
        if remote:
            branches = [ref.name for ref in self.repo.remote().refs]
        else:
            branches = [head.name for head in self.repo.heads]

        return branches

    def get_current_branch(self) -> str:
        """
        Get current branch name.

        Returns:
            Current branch name
        """
        return self.repo.active_branch.name

    def branch_exists(self, branch_name: str, remote: bool = False) -> bool:
        """
        Check if a branch exists.

        Args:
            branch_name: Branch name to check
            remote: Check remote branches

        Returns:
            True if branch exists, False otherwise
        """
        branches = self.list_branches(remote=remote)
        return branch_name in branches

    def merge_branch(
        self,
        source_branch: str,
        target_branch: Optional[str] = None,
        strategy: str = "merge"
    ) -> None:
        """
        Merge a branch into current or target branch.

        Args:
            source_branch: Branch to merge from
            target_branch: Branch to merge into (defaults to current)
            strategy: Merge strategy ('merge', 'squash', 'rebase')
        """
        if target_branch:
            self.checkout_branch(target_branch)

        current = self.get_current_branch()
        logger.info(f"Merging {source_branch} into {current} using {strategy} strategy")

        if strategy == "merge":
            self.repo.git.merge(source_branch)
        elif strategy == "squash":
            self.repo.git.merge(source_branch, squash=True)
        elif strategy == "rebase":
            self.repo.git.rebase(source_branch)
        else:
            raise ValueError(f"Unknown merge strategy: {strategy}")

        logger.info("Merge completed")

    def get_branch_info(self, branch_name: Optional[str] = None) -> dict:
        """
        Get information about a branch.

        Args:
            branch_name: Branch name (defaults to current branch)

        Returns:
            Dictionary with branch info
        """
        if branch_name:
            if branch_name not in self.repo.heads:
                raise ValueError(f"Branch '{branch_name}' does not exist")
            branch = self.repo.heads[branch_name]
        else:
            branch = self.repo.active_branch

        return {
            "name": branch.name,
            "commit": str(branch.commit),
            "author": str(branch.commit.author),
            "message": branch.commit.message.strip(),
            "date": branch.commit.committed_datetime.isoformat()
        }
