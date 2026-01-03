#!/usr/bin/env python3
"""
DefenderAgent - Main entry point for executing coding tasks
"""

import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from src.utils.logger import setup_logger
from src.utils.config import Config
from src.agent.orchestrator import AgentOrchestrator

console = Console()
logger = setup_logger(__name__)


def print_banner():
    """Print DefenderAgent banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║              🛡️  D E F E N D E R   A G E N T              ║
    ║                                                           ║
    ║        Docker-Based AI Coding Environment                ║
    ║        with Azure DevOps Integration                     ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    console.print(banner, style="bold blue")


def print_task_info(args):
    """Print task information"""
    table = Table(title="Task Information", show_header=False, border_style="blue")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Repository", args.repo)
    table.add_row("Task", args.task)
    table.add_row("Feature Branch", args.branch)
    table.add_row("Base Branch", args.base_branch)
    table.add_row("Run Tests", "Yes" if args.run_tests else "No")
    table.add_row("Create PR", "Yes" if args.create_pr else "No")

    console.print(table)
    console.print()


def print_results(context):
    """Print task execution results"""
    if context.status == "completed":
        console.print(Panel(
            f"✅ Task completed successfully!\n\n"
            f"Task ID: {context.task_id}\n"
            f"Files Changed: {len(context.files_changed)}\n"
            f"Commits: {len(context.commits)}\n"
            f"Branch: {context.feature_branch}",
            title="Success",
            border_style="green"
        ))

        # Show changed files
        if context.files_changed:
            console.print("\n📝 Changed Files:", style="bold")
            for file in context.files_changed[:20]:
                console.print(f"  • {file}")
            if len(context.files_changed) > 20:
                console.print(f"  ... and {len(context.files_changed) - 20} more")

        # Show commits
        if context.commits:
            console.print("\n📦 Commits:", style="bold")
            for commit in context.commits:
                console.print(f"  • {commit[:8]}")

        # Show PR URL
        if context.pr_url:
            console.print(f"\n🔗 Pull Request: {context.pr_url}", style="bold")

    else:
        console.print(Panel(
            f"❌ Task failed!\n\n"
            f"Task ID: {context.task_id}\n"
            f"Error: {context.error_message}",
            title="Failed",
            border_style="red"
        ))


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="DefenderAgent - Automated coding with Azure DevOps",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple bug fix
  python run_task.py \\
    --repo "https://dev.azure.com/myorg/project/_git/repo" \\
    --task "Fix null pointer exception in UserService" \\
    --branch "bugfix/userservice-npe"

  # Feature implementation with PR
  python run_task.py \\
    --repo "https://dev.azure.com/myorg/project/_git/webapp" \\
    --task "Implement dark mode toggle" \\
    --branch "feature/dark-mode" \\
    --create-pr

  # Refactoring without tests
  python run_task.py \\
    --repo "https://dev.azure.com/myorg/project/_git/service" \\
    --task "Refactor payment processing" \\
    --branch "refactor/payment" \\
    --no-tests
        """
    )

    # Required arguments
    parser.add_argument(
        "--repo",
        required=True,
        help="Azure DevOps repository URL"
    )
    parser.add_argument(
        "--task",
        required=True,
        help="Coding task description"
    )
    parser.add_argument(
        "--branch",
        required=True,
        help="Feature branch name"
    )

    # Optional arguments
    parser.add_argument(
        "--base-branch",
        default="main",
        help="Base branch to branch from (default: main)"
    )
    parser.add_argument(
        "--run-tests",
        dest="run_tests",
        action="store_true",
        default=True,
        help="Run tests before committing (default: true)"
    )
    parser.add_argument(
        "--no-tests",
        dest="run_tests",
        action="store_false",
        help="Skip running tests"
    )
    parser.add_argument(
        "--create-pr",
        action="store_true",
        default=False,
        help="Create pull request after completion"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Print banner
    print_banner()

    try:
        # Load configuration
        console.print("📋 Loading configuration...", style="bold")
        config = Config.from_env()

        # Override with command-line arguments
        if args.verbose:
            config.log_level = "DEBUG"

        # Print task info
        print_task_info(args)

        # Validate credentials
        console.print("🔐 Validating Azure DevOps credentials...", style="bold")
        from src.azure_devops.auth import AzureDevOpsAuth
        auth = AzureDevOpsAuth(
            organization=config.azure.organization,
            pat=config.azure.pat
        )
        if not auth.validate_credentials():
            console.print("❌ Failed to validate credentials", style="bold red")
            sys.exit(1)
        console.print("✅ Credentials validated\n", style="bold green")

        # Create orchestrator
        orchestrator = AgentOrchestrator(config)

        # Execute task
        console.print("🚀 Starting task execution...\n", style="bold")
        context = orchestrator.execute_task(
            task_description=args.task,
            repo_url=args.repo,
            feature_branch=args.branch,
            base_branch=args.base_branch,
            run_tests=args.run_tests,
            create_pr=args.create_pr
        )

        # Print results
        console.print()
        print_results(context)

        # Exit with appropriate code
        sys.exit(0 if context.status == "completed" else 1)

    except KeyboardInterrupt:
        console.print("\n⚠️  Task cancelled by user", style="bold yellow")
        sys.exit(130)

    except Exception as e:
        logger.exception("Task execution failed")
        console.print(
            Panel(
                f"❌ Unexpected error:\n\n{str(e)}",
                title="Error",
                border_style="red"
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
