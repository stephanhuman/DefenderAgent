"""Agent orchestration for task execution"""

import uuid
from pathlib import Path
from typing import Optional
from git import Repo
from src.utils.logger import setup_logger
from src.utils.config import Config
from src.azure_devops.auth import AzureDevOpsAuth
from src.azure_devops.repo import RepositoryManager
from src.azure_devops.branch import BranchManager
from .context import TaskContext
from .executor import TaskExecutor

logger = setup_logger(__name__)


class AgentOrchestrator:
    """Orchestrate the entire coding task workflow"""

    def __init__(self, config: Config):
        """
        Initialize agent orchestrator.

        Args:
            config: Configuration object
        """
        self.config = config

        # Initialize components
        self.auth = AzureDevOpsAuth(
            organization=config.azure.organization,
            pat=config.azure.pat
        )
        self.repo_manager = RepositoryManager(
            auth=self.auth,
            workspace_dir=config.task.workspace_dir
        )
        self.executor = TaskExecutor(
            api_key=config.agent.api_key,
            model=config.agent.model
        )

    def execute_task(
        self,
        task_description: str,
        repo_url: str,
        feature_branch: str,
        base_branch: Optional[str] = None,
        run_tests: Optional[bool] = None,
        create_pr: Optional[bool] = None
    ) -> TaskContext:
        """
        Execute a complete coding task.

        Args:
            task_description: Description of the coding task
            repo_url: Azure DevOps repository URL
            feature_branch: Name of the feature branch to create
            base_branch: Base branch to branch from (defaults to config)
            run_tests: Whether to run tests (defaults to config)
            create_pr: Whether to create PR (defaults to config)

        Returns:
            TaskContext with execution results
        """
        # Create task context
        context = TaskContext(
            task_id=str(uuid.uuid4()),
            description=task_description,
            repo_url=repo_url,
            base_branch=base_branch or self.config.git.default_base_branch,
            feature_branch=feature_branch,
            run_tests=run_tests if run_tests is not None else self.config.task.run_tests,
            create_pr=create_pr if create_pr is not None else self.config.task.auto_create_pr,
            max_iterations=self.config.agent.max_iterations
        )

        logger.info(f"Starting task execution: {context.task_id}")
        logger.info(f"Task: {task_description}")
        logger.info(f"Repository: {repo_url}")
        logger.info(f"Feature branch: {feature_branch}")

        try:
            # Step 1: Clone repository
            context.mark_started()
            repo = self._clone_repository(context)
            logger.info(f"Repository cloned to: {repo.working_dir}")

            # Step 2: Create feature branch
            self._create_feature_branch(repo, context)

            # Step 3: Execute task with AI agent
            result = self.executor.execute_task(context)
            logger.info(f"Task execution result: {result.get('approach', 'N/A')}")

            # Step 4: Apply changes
            if result.get("files_to_change"):
                modified_files = self.executor.apply_changes(
                    Path(repo.working_dir),
                    result["files_to_change"]
                )
                for file in modified_files:
                    context.add_changed_file(file)

            # Step 5: Run tests (if configured)
            if context.run_tests:
                tests_passed = self.executor.run_tests(Path(repo.working_dir))
                if not tests_passed:
                    logger.warning("Tests failed, but continuing...")

            # Step 6: Commit changes
            if context.files_changed:
                commit_hash = self._commit_changes(repo, context, result)
                context.add_commit(commit_hash)

            # Step 7: Push to remote
            self._push_changes(repo, context)

            # Step 8: Create PR (if configured)
            if context.create_pr:
                pr_url = self._create_pull_request(context, result)
                context.pr_url = pr_url

            # Mark as completed
            context.mark_completed()
            logger.info(f"Task completed successfully: {context.task_id}")

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            context.mark_failed(str(e))
            raise

        return context

    def _clone_repository(self, context: TaskContext) -> Repo:
        """Clone repository"""
        logger.info("Cloning repository...")
        repo = self.repo_manager.clone_repository(
            repo_url=context.repo_url,
            branch=context.base_branch
        )
        context.repo_path = Path(repo.working_dir)
        return repo

    def _create_feature_branch(self, repo: Repo, context: TaskContext) -> None:
        """Create feature branch"""
        logger.info(f"Creating feature branch: {context.feature_branch}")
        branch_manager = BranchManager(repo)

        # Check if branch already exists
        if branch_manager.branch_exists(context.feature_branch):
            logger.warning(f"Branch {context.feature_branch} already exists, checking out...")
            branch_manager.checkout_branch(context.feature_branch)
        else:
            branch_manager.create_branch(
                context.feature_branch,
                base_branch=context.base_branch,
                checkout=True
            )

    def _commit_changes(
        self,
        repo: Repo,
        context: TaskContext,
        result: dict
    ) -> str:
        """Commit changes to repository"""
        logger.info("Committing changes...")

        # Configure git user
        with repo.config_writer() as git_config:
            git_config.set_value("user", "name", self.config.git.user_name)
            git_config.set_value("user", "email", self.config.git.user_email)

        # Stage all changes
        repo.git.add(A=True)

        # Create commit message
        commit_message = self._generate_commit_message(context, result)

        # Commit
        commit = repo.index.commit(commit_message)
        logger.info(f"Created commit: {commit.hexsha[:8]}")

        return commit.hexsha

    def _generate_commit_message(self, context: TaskContext, result: dict) -> str:
        """Generate commit message"""
        approach = result.get("approach", "Implementation")
        files_count = len(context.files_changed)

        message = f"{approach}\n\n"
        message += f"Task: {context.description}\n\n"
        message += f"Modified {files_count} file(s):\n"
        for file in context.files_changed[:10]:  # Limit to first 10
            message += f"- {file}\n"

        if len(context.files_changed) > 10:
            message += f"... and {len(context.files_changed) - 10} more\n"

        message += f"\nTask ID: {context.task_id}"

        return message

    def _push_changes(self, repo: Repo, context: TaskContext) -> None:
        """Push changes to remote"""
        logger.info(f"Pushing changes to {context.feature_branch}...")

        # Set up authentication for push
        username, password = self.auth.get_git_credentials()

        # Configure remote URL with credentials
        repo_info = self.repo_manager.parse_repo_url(context.repo_url)
        push_url = self.auth.get_clone_url(
            repo_info["project"],
            repo_info["repository"]
        )

        # Update remote URL
        origin = repo.remote("origin")
        origin.set_url(push_url)

        # Push
        origin.push(context.feature_branch)
        logger.info("Changes pushed successfully")

    def _create_pull_request(self, context: TaskContext, result: dict) -> str:
        """Create pull request"""
        logger.info("Creating pull request...")

        # This would integrate with Azure DevOps REST API
        # For now, we'll return a placeholder

        repo_info = self.repo_manager.parse_repo_url(context.repo_url)

        # In production, you would use the Azure DevOps REST API:
        # git_client = self.auth.get_git_client()
        # pr = git_client.create_pull_request(...)

        pr_url = (
            f"https://dev.azure.com/{repo_info['organization']}/"
            f"{repo_info['project']}/_git/{repo_info['repository']}/"
            f"pullrequest/create"
        )

        logger.info(f"PR URL: {pr_url}")
        logger.info("Note: Automated PR creation requires additional Azure DevOps API integration")

        return pr_url

    def get_status(self, task_id: str) -> Optional[TaskContext]:
        """Get task status (placeholder for future implementation)"""
        # In production, this would query a database or cache
        logger.info(f"Getting status for task: {task_id}")
        return None
