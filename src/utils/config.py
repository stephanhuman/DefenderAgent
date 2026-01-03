"""Configuration management for DefenderAgent"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AzureDevOpsConfig(BaseModel):
    """Azure DevOps configuration"""

    pat: str = Field(..., description="Personal Access Token")
    organization: str = Field(..., description="Organization name")

    @field_validator('pat')
    @classmethod
    def validate_pat(cls, v: str) -> str:
        if not v or v == "your_personal_access_token_here":
            raise ValueError("Azure DevOps PAT must be set")
        return v


class AgentConfig(BaseModel):
    """AI Agent configuration"""

    api_key: str = Field(..., description="Anthropic API key")
    model: str = Field(
        default="claude-sonnet-4-5-20250929",
        description="Model to use for coding tasks"
    )
    max_iterations: int = Field(
        default=10,
        description="Maximum iterations for task execution"
    )
    temperature: float = Field(
        default=0.0,
        description="Temperature for model responses"
    )

    @field_validator('api_key')
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        if not v or v == "your_anthropic_api_key_here":
            raise ValueError("Anthropic API key must be set")
        return v


class GitConfig(BaseModel):
    """Git configuration"""

    user_name: str = Field(
        default="DefenderAgent",
        description="Git user name"
    )
    user_email: str = Field(
        default="defender-agent@automation.local",
        description="Git user email"
    )
    default_base_branch: str = Field(
        default="main",
        description="Default base branch"
    )


class TaskConfig(BaseModel):
    """Task execution configuration"""

    auto_create_pr: bool = Field(
        default=False,
        description="Automatically create PR after task completion"
    )
    run_tests: bool = Field(
        default=True,
        description="Run tests before committing"
    )
    workspace_dir: Path = Field(
        default=Path("/workspace/repos"),
        description="Workspace directory for repositories"
    )


class Config(BaseModel):
    """Main configuration class"""

    azure: AzureDevOpsConfig
    agent: AgentConfig
    git: GitConfig
    task: TaskConfig
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        return cls(
            azure=AzureDevOpsConfig(
                pat=os.getenv("AZURE_DEVOPS_PAT", ""),
                organization=os.getenv("AZURE_DEVOPS_ORG", "")
            ),
            agent=AgentConfig(
                api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                model=os.getenv("AGENT_MODEL", "claude-sonnet-4-5-20250929"),
                max_iterations=int(os.getenv("MAX_ITERATIONS", "10")),
                temperature=float(os.getenv("TEMPERATURE", "0.0"))
            ),
            git=GitConfig(
                user_name=os.getenv("GIT_USER_NAME", "DefenderAgent"),
                user_email=os.getenv("GIT_USER_EMAIL", "defender-agent@automation.local"),
                default_base_branch=os.getenv("DEFAULT_BASE_BRANCH", "main")
            ),
            task=TaskConfig(
                auto_create_pr=os.getenv("AUTO_CREATE_PR", "false").lower() == "true",
                run_tests=os.getenv("RUN_TESTS", "true").lower() == "true",
                workspace_dir=Path(os.getenv("WORKSPACE_DIR", "/workspace/repos"))
            ),
            log_level=os.getenv("LOG_LEVEL", "INFO")
        )

    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        return self.model_dump()
