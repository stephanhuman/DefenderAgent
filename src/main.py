"""
Main entry point for DefenderAgent CLI
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pathlib import Path

from .config import Config
from .defender_client import DefenderClient
from .llm_client import create_llm_client
from .triage_engine import TriageEngine
from .investigation_agent import InvestigationAgent
from .report_generator import ReportGenerator


console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """
    DefenderAgent - MS Defender Alert Investigation Agent

    Automatically investigates alerts and incidents from Microsoft Defender
    using AI-powered analysis with your own model (BYOM).
    """
    pass


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to .env configuration file"
)
def test_connection(config):
    """Test connection to MS Defender API"""
    try:
        cfg = Config(config)
        errors = cfg.validate()

        if errors:
            console.print("[bold red]Configuration errors:[/bold red]")
            for error in errors:
                console.print(f"  - {error}")
            return

        console.print("[bold blue]Testing MS Defender API connection...[/bold blue]")

        client = DefenderClient(
            tenant_id=cfg.tenant_id,
            client_id=cfg.client_id,
            client_secret=cfg.client_secret
        )

        if client.test_connection():
            console.print("[bold green]✓ Connection successful![/bold green]")
        else:
            console.print("[bold red]✗ Connection failed[/bold red]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to .env configuration file"
)
@click.option(
    "--max-alerts",
    "-n",
    type=int,
    help="Maximum number of alerts to process"
)
@click.option(
    "--severity",
    "-s",
    multiple=True,
    type=click.Choice(["critical", "high", "medium", "low", "informational"], case_sensitive=False),
    help="Filter by severity (can be specified multiple times)"
)
@click.option(
    "--hours",
    "-h",
    type=int,
    default=24,
    help="Time range in hours to fetch alerts (default: 24)"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "html", "markdown", "all"], case_sensitive=False),
    default="json",
    help="Report format (default: json)"
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default="reports",
    help="Output directory for reports (default: reports)"
)
def investigate_alerts(config, max_alerts, severity, hours, format, output_dir):
    """Investigate alerts from MS Defender"""
    try:
        # Load configuration
        cfg = Config(config)
        errors = cfg.validate()

        if errors:
            console.print("[bold red]Configuration errors:[/bold red]")
            for error in errors:
                console.print(f"  - {error}")
            return

        # Override config with CLI options if provided
        if max_alerts:
            cfg.max_alerts_to_process = max_alerts

        # Convert severity tuple to list
        severity_filter = list(severity) if severity else None

        # Display configuration
        console.print(Panel.fit(
            f"[bold]Configuration[/bold]\n\n"
            f"LLM Provider: {cfg.llm_provider}\n"
            f"Max Alerts: {cfg.max_alerts_to_process}\n"
            f"Time Range: {hours} hours\n"
            f"Severity Filter: {', '.join(severity_filter) if severity_filter else 'All'}\n"
            f"Output Format: {format}",
            title="DefenderAgent",
            border_style="blue"
        ))

        # Initialize clients
        defender_client = DefenderClient(
            tenant_id=cfg.tenant_id,
            client_id=cfg.client_id,
            client_secret=cfg.client_secret
        )

        llm_client = create_llm_client(cfg.get_llm_config())
        triage_engine = TriageEngine(cfg.triage_rules)

        # Create investigation agent
        agent = InvestigationAgent(
            defender_client=defender_client,
            llm_client=llm_client,
            triage_engine=triage_engine
        )

        # Run investigation
        results = agent.investigate_alerts(
            max_alerts=cfg.max_alerts_to_process,
            severity_filter=severity_filter,
            time_range_hours=hours
        )

        if not results:
            console.print("[yellow]No results to report[/yellow]")
            return

        # Display summary
        _display_summary(results, "alerts")

        # Generate reports
        report_gen = ReportGenerator(output_dir)

        if format == "json" or format == "all":
            json_path = report_gen.generate_json_report(results, "alerts")
            console.print(f"[green]✓ JSON report saved to: {json_path}[/green]")

        if format == "html" or format == "all":
            html_path = report_gen.generate_html_report(results, "alerts")
            console.print(f"[green]✓ HTML report saved to: {html_path}[/green]")

        if format == "markdown" or format == "all":
            md_path = report_gen.generate_markdown_report(results, "alerts")
            console.print(f"[green]✓ Markdown report saved to: {md_path}[/green]")

        console.print("\n[bold green]Investigation complete![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to .env configuration file"
)
@click.option(
    "--max-incidents",
    "-n",
    type=int,
    help="Maximum number of incidents to process"
)
@click.option(
    "--hours",
    "-h",
    type=int,
    default=24,
    help="Time range in hours to fetch incidents (default: 24)"
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["json", "html", "markdown", "all"], case_sensitive=False),
    default="json",
    help="Report format (default: json)"
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default="reports",
    help="Output directory for reports (default: reports)"
)
def investigate_incidents(config, max_incidents, hours, format, output_dir):
    """Investigate incidents from MS Defender"""
    try:
        # Load configuration
        cfg = Config(config)
        errors = cfg.validate()

        if errors:
            console.print("[bold red]Configuration errors:[/bold red]")
            for error in errors:
                console.print(f"  - {error}")
            return

        # Override config with CLI options if provided
        if max_incidents:
            cfg.max_alerts_to_process = max_incidents

        # Display configuration
        console.print(Panel.fit(
            f"[bold]Configuration[/bold]\n\n"
            f"LLM Provider: {cfg.llm_provider}\n"
            f"Max Incidents: {cfg.max_alerts_to_process}\n"
            f"Time Range: {hours} hours\n"
            f"Output Format: {format}",
            title="DefenderAgent",
            border_style="blue"
        ))

        # Initialize clients
        defender_client = DefenderClient(
            tenant_id=cfg.tenant_id,
            client_id=cfg.client_id,
            client_secret=cfg.client_secret
        )

        llm_client = create_llm_client(cfg.get_llm_config())
        triage_engine = TriageEngine(cfg.triage_rules)

        # Create investigation agent
        agent = InvestigationAgent(
            defender_client=defender_client,
            llm_client=llm_client,
            triage_engine=triage_engine
        )

        # Run investigation
        results = agent.investigate_incidents(
            max_incidents=cfg.max_alerts_to_process,
            time_range_hours=hours
        )

        if not results:
            console.print("[yellow]No results to report[/yellow]")
            return

        # Display summary
        _display_summary(results, "incidents")

        # Generate reports
        report_gen = ReportGenerator(output_dir)

        if format == "json" or format == "all":
            json_path = report_gen.generate_json_report(results, "incidents")
            console.print(f"[green]✓ JSON report saved to: {json_path}[/green]")

        if format == "html" or format == "all":
            html_path = report_gen.generate_html_report(results, "incidents")
            console.print(f"[green]✓ HTML report saved to: {html_path}[/green]")

        if format == "markdown" or format == "all":
            md_path = report_gen.generate_markdown_report(results, "incidents")
            console.print(f"[green]✓ Markdown report saved to: {md_path}[/green]")

        console.print("\n[bold green]Investigation complete![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())


@cli.command()
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    help="Path to .env configuration file"
)
@click.option(
    "--query",
    "-q",
    type=str,
    help="KQL query to execute (use quotes for multi-line queries)"
)
@click.option(
    "--query-name",
    "-n",
    type=str,
    help="Name of predefined query to run"
)
@click.option(
    "--list-queries",
    "-l",
    is_flag=True,
    help="List all available predefined queries"
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Save results to JSON file"
)
def run_kql(config, query, query_name, list_queries, output):
    """Run KQL (Kusto Query Language) queries against Defender Advanced Hunting"""
    try:
        # Load configuration
        cfg = Config(config)
        errors = cfg.validate()

        if errors:
            console.print("[bold red]Configuration errors:[/bold red]")
            for error in errors:
                console.print(f"  - {error}")
            return

        # Initialize Defender client
        defender_client = DefenderClient(
            tenant_id=cfg.tenant_id,
            client_id=cfg.client_id,
            client_secret=cfg.client_secret
        )

        # List predefined queries
        if list_queries:
            console.print("[bold blue]Available Predefined KQL Queries:[/bold blue]\n")
            predefined = defender_client._get_predefined_queries()
            for name in sorted(predefined.keys()):
                console.print(f"  • {name}")
            console.print(f"\n[cyan]Total: {len(predefined)} queries[/cyan]")
            console.print("\nUse --query-name <name> to run a predefined query")
            return

        # Run query
        if query:
            console.print("[bold blue]Running custom KQL query...[/bold blue]")
            result = defender_client.run_kql_query(query)
        elif query_name:
            console.print(f"[bold blue]Running predefined query: {query_name}[/bold blue]")

            # Prompt for parameters
            console.print("\n[yellow]Enter query parameters (press Enter to skip):[/yellow]")
            params = {}
            params["hours"] = click.prompt("Hours to look back", default="24")
            params["limit"] = click.prompt("Max results", default="10")

            # Query-specific parameters
            if "device" in query_name.lower():
                params["device_name"] = click.prompt("Device name", default="")
            if "file_hash" in query_name:
                params["file_hash"] = click.prompt("File hash (SHA256)", default="")
            if "file_name" in query_name or "file_activity" in query_name:
                params["file_name"] = click.prompt("File name", default="")
            if "account" in query_name.lower() or "login" in query_name.lower():
                params["account_name"] = click.prompt("Account name", default="")
            if "email" in query_name:
                params["sender_email"] = click.prompt("Sender email", default="")
            if "network" in query_name:
                params["domain"] = click.prompt("Domain", default="")
                params["ip"] = click.prompt("IP address", default="")
            if "process" in query_name:
                params["indicator"] = click.prompt("Indicator/pattern", default="")
                params["process_name"] = click.prompt("Process name", default="powershell.exe")
            if "powershell" in query_name:
                params["keywords"] = click.prompt("Keywords to search", default="bypass")
            if "registry" in query_name:
                params["registry_path"] = click.prompt("Registry path", default="CurrentVersion\\Run")

            result = defender_client.run_predefined_query(query_name, **params)
        else:
            console.print("[bold red]Error: Must specify --query or --query-name[/bold red]")
            console.print("Use --list-queries to see available predefined queries")
            return

        # Display results
        results_data = result.get("results", [])
        results_count = len(results_data)

        console.print(f"\n[bold green]✓ Query executed successfully![/bold green]")
        console.print(f"[cyan]Found {results_count} results[/cyan]")

        # Display stats if available
        stats = result.get("stats", {})
        if stats.get("execution_time"):
            console.print(f"Execution time: {stats['execution_time']}")

        # Display results in table
        if results_data:
            console.print("\n[bold]Results:[/bold]")

            # Show first 20 results
            display_results = results_data[:20]

            if display_results:
                # Create table from first result's keys
                result_table = Table()
                first_row = display_results[0]
                for key in first_row.keys():
                    result_table.add_column(key, style="cyan", no_wrap=False)

                for row in display_results:
                    values = [str(row.get(key, ""))[:100] for key in first_row.keys()]
                    result_table.add_row(*values)

                console.print(result_table)

                if results_count > 20:
                    console.print(f"\n[yellow]Showing first 20 of {results_count} results[/yellow]")

        # Save to file if requested
        if output:
            import json
            with open(output, 'w') as f:
                json.dump(result, f, indent=2)
            console.print(f"\n[green]✓ Results saved to: {output}[/green]")

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())


def _display_summary(results, report_type):
    """Display summary table of results"""
    table = Table(title=f"\n{report_type.title()} Investigation Summary")

    table.add_column("Priority", style="cyan")
    table.add_column("Count", style="magenta")

    # Count by priority
    priority_counts = {}
    for result in results:
        priority = result.get("priority", "unknown")
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    for priority in ["critical", "high", "medium", "low"]:
        count = priority_counts.get(priority, 0)
        if count > 0:
            table.add_row(priority.upper(), str(count))

    console.print(table)


if __name__ == "__main__":
    cli()
