"""
Triage engine for applying rules to alerts based on type and severity
"""

from typing import Dict, Any, List, Optional


class TriageEngine:
    """Engine for triaging alerts based on predefined rules"""

    def __init__(self, rules: Dict[str, Any]):
        """
        Initialize triage engine

        Args:
            rules: Triage rules dictionary from config
        """
        self.severity_levels = rules.get("severity_levels", {})
        self.triage_rules = rules.get("triage_rules", [])
        self.investigation_prompts = rules.get("investigation_prompts", {})

    def triage_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """
        Triage an alert and determine priority and investigation steps

        Args:
            alert: Alert dictionary from Defender API

        Returns:
            Triage result with priority, investigation steps, and prompt template
        """
        # Extract alert properties
        alert_title = alert.get("title", "")
        alert_category = alert.get("category", "")
        severity = alert.get("severity", "").lower()

        # Determine alert type from category or title
        alert_type = self._categorize_alert(alert_title, alert_category)

        # Find matching rule
        matching_rule = self._find_matching_rule(alert_type, severity)

        if not matching_rule:
            # Use default rule
            matching_rule = self._get_default_rule(severity)

        # Get investigation prompt template
        priority = matching_rule.get("priority", "medium")
        prompt_template = self.investigation_prompts.get(priority, self.investigation_prompts.get("medium", ""))

        return {
            "alert_type": alert_type,
            "severity": severity,
            "priority": priority,
            "auto_investigate": matching_rule.get("auto_investigate", False),
            "investigation_steps": matching_rule.get("investigation_steps", []),
            "prompt_template": prompt_template,
            "severity_score": self.severity_levels.get(severity, 0)
        }

    def _categorize_alert(self, title: str, category: str) -> str:
        """Categorize alert based on title and category"""
        title_lower = title.lower()
        category_lower = category.lower()

        # Malware detection
        if any(keyword in title_lower or keyword in category_lower
               for keyword in ["malware", "virus", "trojan", "ransomware", "backdoor"]):
            return "Malware"

        # Phishing
        if any(keyword in title_lower or keyword in category_lower
               for keyword in ["phishing", "credential", "suspicious email", "spam"]):
            return "Phishing"

        # Exploitation
        if any(keyword in title_lower or keyword in category_lower
               for keyword in ["exploit", "vulnerability", "cve-", "remote code execution"]):
            return "Exploit"

        # Suspicious activity
        if any(keyword in title_lower or keyword in category_lower
               for keyword in ["suspicious", "anomalous", "unusual", "abnormal"]):
            return "SuspiciousActivity"

        # Default
        return "Default"

    def _find_matching_rule(self, alert_type: str, severity: str) -> Optional[Dict[str, Any]]:
        """Find matching triage rule"""
        for rule in self.triage_rules:
            if rule.get("alert_type") == alert_type:
                # Check if severity matches
                rule_severities = rule.get("severity", [])
                if severity in rule_severities:
                    return rule

        return None

    def _get_default_rule(self, severity: str) -> Dict[str, Any]:
        """Get default rule based on severity"""
        # Find default rule for this severity
        for rule in self.triage_rules:
            if rule.get("alert_type") == "Default":
                rule_severities = rule.get("severity", [])
                if severity in rule_severities:
                    return rule

        # Fallback default
        return {
            "priority": "medium",
            "auto_investigate": True,
            "investigation_steps": [
                "Review alert details",
                "Assess potential impact",
                "Identify affected resources"
            ]
        }

    def format_investigation_prompt(
        self,
        triage_result: Dict[str, Any],
        alert: Dict[str, Any],
        kql_context: str = ""
    ) -> str:
        """
        Format investigation prompt with alert details and KQL context

        Args:
            triage_result: Result from triage_alert()
            alert: Alert dictionary
            kql_context: Additional context from KQL queries

        Returns:
            Formatted prompt for LLM
        """
        # Format alert details
        alert_details = self._format_alert_details(alert)

        # Format investigation steps
        steps = triage_result.get("investigation_steps", [])
        investigation_steps = "\n".join([f"- {step}" for step in steps])

        # Get template
        template = triage_result.get("prompt_template", "")

        # Format template
        prompt = template.format(
            alert_details=alert_details,
            investigation_steps=investigation_steps,
            kql_context=kql_context if kql_context else "No additional KQL query results available."
        )

        return prompt

    def _format_alert_details(self, alert: Dict[str, Any]) -> str:
        """Format alert details for prompt"""
        details = []

        # Basic information
        details.append(f"Alert ID: {alert.get('id', 'N/A')}")
        details.append(f"Title: {alert.get('title', 'N/A')}")
        details.append(f"Severity: {alert.get('severity', 'N/A')}")
        details.append(f"Category: {alert.get('category', 'N/A')}")
        details.append(f"Status: {alert.get('status', 'N/A')}")
        details.append(f"Created: {alert.get('createdDateTime', 'N/A')}")

        # Description
        if alert.get("description"):
            details.append(f"\nDescription: {alert['description']}")

        # Affected entities
        if alert.get("entities"):
            details.append("\nAffected Entities:")
            for entity in alert["entities"][:5]:  # Limit to first 5
                entity_type = entity.get("@odata.type", "Unknown")
                details.append(f"- {entity_type}: {entity.get('displayName', entity.get('userPrincipalName', 'N/A'))}")

        # Evidence
        if alert.get("evidence"):
            details.append("\nEvidence:")
            for evidence in alert["evidence"][:5]:  # Limit to first 5
                evidence_type = evidence.get("@odata.type", "Unknown")
                details.append(f"- {evidence_type}")

        # Detection source
        if alert.get("detectionSource"):
            details.append(f"\nDetection Source: {alert['detectionSource']}")

        return "\n".join(details)
