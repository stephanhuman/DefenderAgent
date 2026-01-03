"""Task execution using AI agent"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from anthropic import Anthropic
from git import Repo
from src.utils.logger import setup_logger
from .context import TaskContext

logger = setup_logger(__name__)


class TaskExecutor:
    """Execute coding tasks using Claude AI"""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize task executor.

        Args:
            api_key: Anthropic API key
            model: Model to use for coding tasks
        """
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def analyze_codebase(self, repo_path: Path) -> str:
        """
        Analyze codebase structure.

        Args:
            repo_path: Path to repository

        Returns:
            Codebase analysis
        """
        logger.info("Analyzing codebase structure...")

        # Get file structure
        files = []
        for path in repo_path.rglob("*"):
            if path.is_file() and not self._should_ignore(path):
                rel_path = path.relative_to(repo_path)
                files.append(str(rel_path))

        # Identify key files
        key_files = self._identify_key_files(files)

        analysis = f"""
Codebase Analysis:
- Total files: {len(files)}
- Key files identified: {len(key_files)}

Key Files:
{chr(10).join(f"  - {f}" for f in key_files[:20])}

File types distribution:
{self._get_file_type_distribution(files)}
"""
        return analysis

    def execute_task(self, context: TaskContext) -> Dict[str, Any]:
        """
        Execute a coding task.

        Args:
            context: Task context

        Returns:
            Execution result
        """
        logger.info(f"Executing task: {context.description}")

        if not context.repo_path:
            raise ValueError("Repository path not set in context")

        # Analyze codebase
        codebase_analysis = self.analyze_codebase(context.repo_path)

        # Build prompt for Claude
        prompt = self._build_task_prompt(context, codebase_analysis)

        # Execute with Claude
        result = self._execute_with_claude(prompt, context)

        return result

    def _build_task_prompt(self, context: TaskContext, codebase_analysis: str) -> str:
        """Build prompt for Claude"""
        return f"""You are an expert software engineer working on a coding task.

Repository: {context.repo_url}
Base Branch: {context.base_branch}
Feature Branch: {context.feature_branch}

Task:
{context.description}

Codebase Analysis:
{codebase_analysis}

Instructions:
1. Analyze the codebase structure and understand the existing patterns
2. Implement the requested changes following the existing code style
3. Ensure code quality and best practices
4. Write clear, maintainable code
5. Add necessary tests if applicable
6. Provide a summary of changes made

Please provide:
1. List of files to modify/create
2. Specific changes for each file
3. Reasoning for the implementation approach
4. Any concerns or considerations

Format your response as JSON with the following structure:
{{
  "approach": "Brief description of implementation approach",
  "files_to_change": [
    {{
      "path": "path/to/file",
      "action": "create|modify|delete",
      "changes": "Description of changes",
      "content": "Full file content (for create/modify)"
    }}
  ],
  "reasoning": "Detailed reasoning for the approach",
  "concerns": ["Any concerns or considerations"],
  "next_steps": ["Suggested next steps or validations"]
}}
"""

    def _execute_with_claude(
        self,
        prompt: str,
        context: TaskContext
    ) -> Dict[str, Any]:
        """
        Execute prompt with Claude.

        Args:
            prompt: Task prompt
            context: Task context

        Returns:
            Execution result
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=8000,
                temperature=0.0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract response
            response_text = response.content[0].text

            # Try to parse as JSON
            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # If not JSON, wrap in a result structure
                result = {
                    "approach": "Analysis and implementation",
                    "files_to_change": [],
                    "reasoning": response_text,
                    "concerns": [],
                    "next_steps": []
                }

            logger.info(f"Task execution completed. Files to change: {len(result.get('files_to_change', []))}")
            return result

        except Exception as e:
            logger.error(f"Failed to execute task with Claude: {e}")
            raise

    def apply_changes(
        self,
        repo_path: Path,
        changes: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Apply changes to repository.

        Args:
            repo_path: Repository path
            changes: List of file changes

        Returns:
            List of modified file paths
        """
        modified_files = []

        for change in changes:
            file_path = repo_path / change["path"]
            action = change["action"]

            logger.info(f"Applying {action} to {change['path']}")

            if action == "create" or action == "modify":
                # Create parent directories if needed
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Write content
                content = change.get("content", "")
                file_path.write_text(content, encoding="utf-8")
                modified_files.append(change["path"])

            elif action == "delete":
                if file_path.exists():
                    file_path.unlink()
                    modified_files.append(change["path"])

        logger.info(f"Applied changes to {len(modified_files)} files")
        return modified_files

    def run_tests(self, repo_path: Path) -> bool:
        """
        Run tests in repository.

        Args:
            repo_path: Repository path

        Returns:
            True if tests pass, False otherwise
        """
        logger.info("Running tests...")

        # Detect test framework and run tests
        # This is a simplified version - in production, you'd detect the actual test framework

        import subprocess

        test_commands = [
            ["python", "-m", "pytest"],  # Python
            ["npm", "test"],  # JavaScript
            ["dotnet", "test"],  # .NET
            ["go", "test", "./..."],  # Go
            ["cargo", "test"],  # Rust
            ["mvn", "test"],  # Java/Maven
            ["gradle", "test"],  # Java/Gradle
        ]

        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    cwd=repo_path,
                    capture_output=True,
                    timeout=300
                )
                if result.returncode == 0:
                    logger.info(f"Tests passed using: {' '.join(cmd)}")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue

        logger.warning("No tests found or all test commands failed")
        return True  # Don't fail if no tests found

    @staticmethod
    def _should_ignore(path: Path) -> bool:
        """Check if path should be ignored"""
        ignore_patterns = [
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            "dist",
            "build",
            ".pytest_cache",
            ".mypy_cache",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".DS_Store"
        ]

        for pattern in ignore_patterns:
            if pattern in str(path):
                return True
        return False

    @staticmethod
    def _identify_key_files(files: List[str]) -> List[str]:
        """Identify key files in the codebase"""
        key_patterns = [
            "README",
            "package.json",
            "requirements.txt",
            "setup.py",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
            "build.gradle",
            ".csproj",
            "Dockerfile",
            "docker-compose",
            "main",
            "index",
            "app",
        ]

        key_files = []
        for file in files:
            file_lower = file.lower()
            if any(pattern.lower() in file_lower for pattern in key_patterns):
                key_files.append(file)

        return sorted(key_files)

    @staticmethod
    def _get_file_type_distribution(files: List[str]) -> str:
        """Get file type distribution"""
        extensions: Dict[str, int] = {}

        for file in files:
            ext = Path(file).suffix or "no extension"
            extensions[ext] = extensions.get(ext, 0) + 1

        # Sort by count
        sorted_exts = sorted(extensions.items(), key=lambda x: x[1], reverse=True)

        return "\n".join(
            f"  {ext}: {count}"
            for ext, count in sorted_exts[:10]
        )
