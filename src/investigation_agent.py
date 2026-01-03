"""
Investigation agent that orchestrates the triage and investigation process
"""

from typing import Dict, Any, List
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .defender_client import DefenderClient
from .llm_client import LLMClient
from .triage_engine import TriageEngine


class InvestigationAgent:
    """Agent for investigating MS Defender alerts"""

    def __init__(
        self,
        defender_client: DefenderClient,
        llm_client: LLMClient,
        triage_engine: TriageEngine
    ):
        """
        Initialize investigation agent

        Args:
            defender_client: MS Defender API client
            llm_client: LLM client for analysis
            triage_engine: Triage engine for rule-based processing
        """
        self.defender_client = defender_client
        self.llm_client = llm_client
        self.triage_engine = triage_engine
        self.console = Console()

    def investigate_alerts(
        self,
        max_alerts: int = 50,
        severity_filter: List[str] = None,
        time_range_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Investigate alerts from MS Defender

        Args:
            max_alerts: Maximum number of alerts to process
            severity_filter: Filter by severity (e.g., ['high', 'critical'])
            time_range_hours: Time range to fetch alerts

        Returns:
            List of investigation results
        """
        self.console.print("[bold blue]Fetching alerts from MS Defender...[/bold blue]")

        # Fetch alerts
        alerts = self.defender_client.get_alerts(
            max_results=max_alerts,
            severity=severity_filter,
            time_range_hours=time_range_hours
        )

        if not alerts:
            self.console.print("[yellow]No alerts found matching criteria[/yellow]")
            return []

        self.console.print(f"[green]Found {len(alerts)} alerts[/green]")

        # Process each alert
        investigation_results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(
                f"[cyan]Investigating {len(alerts)} alerts...",
                total=len(alerts)
            )

            for alert in alerts:
                result = self._investigate_single_alert(alert)
                investigation_results.append(result)
                progress.advance(task)

        return investigation_results

    def _investigate_single_alert(self, alert: Dict[str, Any], enable_kql: bool = True) -> Dict[str, Any]:
        """
        Investigate a single alert

        Args:
            alert: Alert dictionary from Defender API
            enable_kql: Whether to run KQL queries for additional context

        Returns:
            Investigation result
        """
        # Triage the alert
        triage_result = self.triage_engine.triage_alert(alert)

        # Check if auto-investigation is enabled
        if not triage_result.get("auto_investigate", False):
            return {
                "alert_id": alert.get("id"),
                "alert_title": alert.get("title"),
                "severity": triage_result.get("severity"),
                "priority": triage_result.get("priority"),
                "triage_result": triage_result,
                "investigation_status": "skipped",
                "investigation_report": "Alert does not require automatic investigation based on current rules."
            }

        # Run KQL queries if enabled
        kql_context = ""
        kql_results = {}
        if enable_kql:
            kql_results = self._run_kql_queries_for_alert(alert, triage_result)
            kql_context = self._format_kql_context(kql_results)

        # Generate investigation prompt with KQL context
        prompt = self.triage_engine.format_investigation_prompt(
            triage_result,
            alert,
            kql_context=kql_context
        )

        # Get LLM analysis
        try:
            investigation_report = self.llm_client.generate(prompt, max_tokens=3000)
        except Exception as e:
            investigation_report = f"Error during LLM investigation: {str(e)}"

        # Compile result
        return {
            "alert_id": alert.get("id"),
            "alert_title": alert.get("title"),
            "severity": triage_result.get("severity"),
            "priority": triage_result.get("priority"),
            "alert_type": triage_result.get("alert_type"),
            "severity_score": triage_result.get("severity_score"),
            "triage_result": triage_result,
            "investigation_status": "completed",
            "investigation_report": investigation_report,
            "alert_details": alert,
            "kql_results": kql_results,
            "timestamp": alert.get("createdDateTime")
        }

    def _run_kql_queries_for_alert(self, alert: Dict[str, Any], triage_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run KQL queries based on alert data and triage result

        Args:
            alert: Alert dictionary
            triage_result: Triage result with KQL query list

        Returns:
            Dictionary of query results
        """
        results = {}

        # Extract entities from alert
        entities = self._extract_alert_entities(alert)

        # Get KQL queries from triage result
        kql_queries = triage_result.get("kql_queries", [])

        for query_name in kql_queries:
            try:
                # Prepare query parameters based on extracted entities
                params = self._prepare_kql_parameters(query_name, entities)

                # Run the query
                query_result = self.defender_client.run_predefined_query(query_name, **params)

                # Store results if we got any
                if query_result.get("results"):
                    results[query_name] = {
                        "count": len(query_result["results"]),
                        "results": query_result["results"][:10],  # Limit to first 10 results
                        "stats": query_result.get("stats", {})
                    }
            except Exception as e:
                # Log error but continue with other queries
                self.console.print(f"[yellow]Warning: KQL query '{query_name}' failed: {str(e)}[/yellow]")
                continue

        return results

    def _extract_alert_entities(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant entities from alert for KQL queries"""
        entities = {
            "device_name": None,
            "account_name": None,
            "file_hash": None,
            "file_name": None,
            "ip_address": None,
            "domain": None,
            "email": None
        }

        # Extract from evidence/entities
        evidence_list = alert.get("evidence", alert.get("entities", []))

        for evidence in evidence_list:
            evidence_type = evidence.get("@odata.type", "")

            # Device/Host
            if "device" in evidence_type.lower() or "host" in evidence_type.lower():
                entities["device_name"] = evidence.get("deviceName") or evidence.get("hostName")

            # User/Account
            if "user" in evidence_type.lower() or "account" in evidence_type.lower():
                entities["account_name"] = evidence.get("userPrincipalName") or evidence.get("accountName")
                if evidence.get("userPrincipalName"):
                    entities["email"] = evidence["userPrincipalName"]

            # File
            if "file" in evidence_type.lower():
                entities["file_hash"] = evidence.get("sha256") or evidence.get("sha1")
                entities["file_name"] = evidence.get("fileName")

            # IP Address
            if "ip" in evidence_type.lower():
                entities["ip_address"] = evidence.get("ipAddress")

            # Domain/URL
            if "url" in evidence_type.lower() or "domain" in evidence_type.lower():
                entities["domain"] = evidence.get("domainName") or evidence.get("url")

        return entities

    def _prepare_kql_parameters(self, query_name: str, entities: Dict[str, Any]) -> Dict[str, str]:
        """Prepare parameters for KQL query based on query name and available entities"""
        # Default parameters
        params = {
            "hours": "24",
            "limit": "10"
        }

        # Query-specific parameter mapping
        if "device" in query_name.lower() or "alerts_for_device" in query_name:
            params["device_name"] = entities.get("device_name") or "unknown"

        if "file_hash" in query_name:
            params["file_hash"] = entities.get("file_hash") or ""

        if "file_name" in query_name or "file_activity" in query_name:
            params["file_name"] = entities.get("file_name") or ""

        if "account" in query_name.lower() or "login" in query_name.lower():
            params["account_name"] = entities.get("account_name") or ""

        if "email" in query_name:
            params["sender_email"] = entities.get("email") or ""

        if "network" in query_name:
            params["domain"] = entities.get("domain") or ""
            params["ip"] = entities.get("ip_address") or ""

        if "process" in query_name or "powershell" in query_name:
            params["process_name"] = "powershell.exe"
            params["indicator"] = ""
            params["keywords"] = "bypass"

        if "registry" in query_name:
            params["registry_path"] = "CurrentVersion\\Run"

        return params

    def _format_kql_context(self, kql_results: Dict[str, Any]) -> str:
        """Format KQL query results for LLM context"""
        if not kql_results:
            return ""

        context_parts = ["Additional Context from Advanced Hunting Queries:\n"]

        for query_name, result in kql_results.items():
            count = result.get("count", 0)
            context_parts.append(f"\n{query_name.replace('_', ' ').title()}:")
            context_parts.append(f"  Found {count} results")

            # Add sample results
            results = result.get("results", [])
            if results:
                context_parts.append("  Sample findings:")
                for i, row in enumerate(results[:3], 1):  # Show top 3
                    # Format row data
                    row_str = ", ".join([f"{k}: {v}" for k, v in row.items() if v and k not in ["@odata.type"]])
                    context_parts.append(f"    {i}. {row_str[:200]}")  # Limit length

        return "\n".join(context_parts)

    def investigate_incidents(
        self,
        max_incidents: int = 50,
        time_range_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Investigate incidents from MS Defender

        Args:
            max_incidents: Maximum number of incidents to process
            time_range_hours: Time range to fetch incidents

        Returns:
            List of investigation results
        """
        self.console.print("[bold blue]Fetching incidents from MS Defender...[/bold blue]")

        # Fetch incidents
        incidents = self.defender_client.get_incidents(
            max_results=max_incidents,
            time_range_hours=time_range_hours
        )

        if not incidents:
            self.console.print("[yellow]No incidents found[/yellow]")
            return []

        self.console.print(f"[green]Found {len(incidents)} incidents[/green]")

        # For incidents, we can aggregate their alerts
        investigation_results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        ) as progress:
            task = progress.add_task(
                f"[cyan]Investigating {len(incidents)} incidents...",
                total=len(incidents)
            )

            for incident in incidents:
                result = self._investigate_single_incident(incident)
                investigation_results.append(result)
                progress.advance(task)

        return investigation_results

    def _investigate_single_incident(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """
        Investigate a single incident

        Args:
            incident: Incident dictionary from Defender API

        Returns:
            Investigation result
        """
        # Build investigation prompt for incident
        incident_details = self._format_incident_details(incident)

        prompt = f"""You are a security analyst investigating a security incident.

Incident Details:
{incident_details}

Provide a comprehensive investigation report including:
1. Summary of the incident
2. Affected assets and users
3. Attack timeline and progression
4. Indicators of Compromise (IOCs)
5. Risk assessment and potential impact
6. Recommended containment and remediation actions
7. Lessons learned and preventive measures

Be specific and actionable in your recommendations."""

        # Get LLM analysis
        try:
            investigation_report = self.llm_client.generate(prompt, max_tokens=3000)
        except Exception as e:
            investigation_report = f"Error during LLM investigation: {str(e)}"

        return {
            "incident_id": incident.get("id"),
            "incident_name": incident.get("displayName"),
            "severity": incident.get("severity", "").lower(),
            "status": incident.get("status"),
            "investigation_status": "completed",
            "investigation_report": investigation_report,
            "incident_details": incident,
            "timestamp": incident.get("createdDateTime")
        }

    def _format_incident_details(self, incident: Dict[str, Any]) -> str:
        """Format incident details for prompt"""
        details = []

        details.append(f"Incident ID: {incident.get('id', 'N/A')}")
        details.append(f"Name: {incident.get('displayName', 'N/A')}")
        details.append(f"Severity: {incident.get('severity', 'N/A')}")
        details.append(f"Status: {incident.get('status', 'N/A')}")
        details.append(f"Created: {incident.get('createdDateTime', 'N/A')}")
        details.append(f"Last Updated: {incident.get('lastUpdateDateTime', 'N/A')}")

        if incident.get("assignedTo"):
            details.append(f"Assigned To: {incident['assignedTo']}")

        if incident.get("classification"):
            details.append(f"Classification: {incident['classification']}")

        if incident.get("determination"):
            details.append(f"Determination: {incident['determination']}")

        # Alert count
        alerts = incident.get("alerts", [])
        details.append(f"\nNumber of Alerts: {len(alerts)}")

        if alerts:
            details.append("\nRelated Alerts:")
            for alert in alerts[:10]:  # Limit to first 10
                details.append(f"- {alert.get('title', 'N/A')} (Severity: {alert.get('severity', 'N/A')})")

        return "\n".join(details)
