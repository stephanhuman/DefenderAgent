"""Azure DevOps authentication module"""

import base64
from typing import Optional
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class AzureDevOpsAuth:
    """Handle Azure DevOps authentication"""

    def __init__(self, organization: str, pat: str):
        """
        Initialize Azure DevOps authentication.

        Args:
            organization: Azure DevOps organization name
            pat: Personal Access Token
        """
        self.organization = organization
        self.pat = pat
        self.organization_url = f"https://dev.azure.com/{organization}"
        self._connection: Optional[Connection] = None

    def get_connection(self) -> Connection:
        """
        Get authenticated Azure DevOps connection.

        Returns:
            Authenticated Connection object

        Raises:
            ValueError: If PAT is invalid
        """
        if self._connection:
            return self._connection

        try:
            # Create authentication credentials
            credentials = BasicAuthentication('', self.pat)

            # Create connection
            self._connection = Connection(
                base_url=self.organization_url,
                creds=credentials
            )

            logger.info(f"Successfully authenticated with Azure DevOps: {self.organization}")
            return self._connection

        except Exception as e:
            logger.error(f"Failed to authenticate with Azure DevOps: {e}")
            raise ValueError(f"Invalid Azure DevOps credentials: {e}")

    def get_git_client(self):
        """Get Git client for repository operations"""
        connection = self.get_connection()
        return connection.clients.get_git_client()

    def get_core_client(self):
        """Get Core client for project operations"""
        connection = self.get_connection()
        return connection.clients.get_core_client()

    def validate_credentials(self) -> bool:
        """
        Validate that credentials are working.

        Returns:
            True if credentials are valid, False otherwise
        """
        try:
            connection = self.get_connection()
            # Try to get projects to validate credentials
            core_client = connection.clients.get_core_client()
            projects = core_client.get_projects()
            logger.info(f"Credentials validated. Found {len(projects.value)} projects")
            return True
        except Exception as e:
            logger.error(f"Credential validation failed: {e}")
            return False

    def get_git_credentials(self) -> tuple[str, str]:
        """
        Get Git credentials for cloning repositories.

        Returns:
            Tuple of (username, password) for Git operations
        """
        # For Azure DevOps, username can be anything, PAT is the password
        return ("pat", self.pat)

    def get_clone_url(self, project: str, repo: str) -> str:
        """
        Get authenticated clone URL for a repository.

        Args:
            project: Project name
            repo: Repository name

        Returns:
            Authenticated HTTPS clone URL
        """
        # Encode PAT in URL
        encoded_pat = base64.b64encode(f":{self.pat}".encode()).decode()
        return f"https://{encoded_pat}@dev.azure.com/{self.organization}/{project}/_git/{repo}"
