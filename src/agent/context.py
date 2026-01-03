"""Task context management"""

from pathlib import Path
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime


class TaskContext(BaseModel):
    """Context for a coding task"""

    # Task identification
    task_id: str = Field(description="Unique task identifier")
    description: str = Field(description="Task description/prompt")
    created_at: datetime = Field(default_factory=datetime.now)

    # Repository information
    repo_url: str = Field(description="Azure DevOps repository URL")
    repo_path: Optional[Path] = Field(None, description="Local repository path")
    base_branch: str = Field(default="main", description="Base branch")
    feature_branch: str = Field(description="Feature branch to create")

    # Task configuration
    run_tests: bool = Field(default=True, description="Run tests before committing")
    create_pr: bool = Field(default=False, description="Create PR after completion")
    max_iterations: int = Field(default=10, description="Maximum iterations")

    # Execution state
    status: str = Field(default="pending", description="Task status")
    current_iteration: int = Field(default=0, description="Current iteration")
    error_message: Optional[str] = Field(None, description="Error message if failed")

    # Results
    commits: List[str] = Field(default_factory=list, description="Commit hashes")
    files_changed: List[str] = Field(default_factory=list, description="Files modified")
    pr_url: Optional[str] = Field(None, description="Pull request URL")

    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        arbitrary_types_allowed = True

    def mark_started(self) -> None:
        """Mark task as started"""
        self.status = "running"

    def mark_completed(self) -> None:
        """Mark task as completed"""
        self.status = "completed"

    def mark_failed(self, error: str) -> None:
        """Mark task as failed"""
        self.status = "failed"
        self.error_message = error

    def increment_iteration(self) -> None:
        """Increment iteration counter"""
        self.current_iteration += 1

    def add_commit(self, commit_hash: str) -> None:
        """Add a commit to the list"""
        self.commits.append(commit_hash)

    def add_changed_file(self, file_path: str) -> None:
        """Add a changed file to the list"""
        if file_path not in self.files_changed:
            self.files_changed.append(file_path)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return self.model_dump(mode='json')

    @classmethod
    def from_dict(cls, data: dict) -> "TaskContext":
        """Create from dictionary"""
        return cls(**data)
