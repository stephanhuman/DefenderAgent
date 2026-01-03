#!/usr/bin/env python3
"""
Check DefenderAgent system status
"""

import sys
import docker
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from src.utils.config import Config
from src.azure_devops.auth import AzureDevOpsAuth

console = Console()


def check_docker():
    """Check Docker status"""
    try:
        client = docker.from_env()
        client.ping()
        return True, "Docker is running"
    except Exception as e:
        return False, f"Docker error: {str(e)}"


def check_container():
    """Check DefenderAgent container status"""
    try:
        client = docker.from_env()
        containers = client.containers.list(filters={"name": "defender-agent"})
        if containers:
            container = containers[0]
            return True, f"Container running ({container.status})"
        else:
            return False, "Container not found"
    except Exception as e:
        return False, f"Error: {str(e)}"


def check_config():
    """Check configuration"""
    try:
        config = Config.from_env()
        return True, "Configuration loaded"
    except Exception as e:
        return False, f"Config error: {str(e)}"


def check_azure_auth():
    """Check Azure DevOps authentication"""
    try:
        config = Config.from_env()
        auth = AzureDevOpsAuth(
            organization=config.azure.organization,
            pat=config.azure.pat
        )
        if auth.validate_credentials():
            return True, "Azure DevOps authenticated"
        else:
            return False, "Authentication failed"
    except Exception as e:
        return False, f"Auth error: {str(e)}"


def main():
    """Main entry point"""
    console.print("\n[bold blue]DefenderAgent System Status[/bold blue]\n")

    checks = [
        ("Docker", check_docker),
        ("Container", check_container),
        ("Configuration", check_config),
        ("Azure DevOps Auth", check_azure_auth),
    ]

    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Component", style="white")
    table.add_column("Status", style="white")
    table.add_column("Details", style="white")

    all_ok = True
    for name, check_func in checks:
        ok, message = check_func()
        status = "✅ OK" if ok else "❌ FAIL"
        style = "green" if ok else "red"
        table.add_row(name, f"[{style}]{status}[/{style}]", message)
        if not ok:
            all_ok = False

    console.print(table)
    console.print()

    if all_ok:
        console.print(Panel(
            "✅ All systems operational!",
            title="Status",
            border_style="green"
        ))
        sys.exit(0)
    else:
        console.print(Panel(
            "⚠️  Some systems are not operational. Please check the details above.",
            title="Status",
            border_style="yellow"
        ))
        sys.exit(1)


if __name__ == "__main__":
    main()
