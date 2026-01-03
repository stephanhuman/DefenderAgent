"""
Microsoft Defender API client for fetching alerts and incidents
"""

import msal
import requests
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta


class DefenderClient:
    """Client for Microsoft Defender API via Microsoft Graph"""

    # Microsoft Graph API endpoints
    GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
    SECURITY_ENDPOINT = f"{GRAPH_ENDPOINT}/security"
    ADVANCED_HUNTING_ENDPOINT = f"{SECURITY_ENDPOINT}/runHuntingQuery"
    AUTHORITY = "https://login.microsoftonline.com"
    SCOPE = ["https://graph.microsoft.com/.default"]

    def __init__(self, tenant_id: str, client_id: str, client_secret: str):
        """
        Initialize Defender API client

        Args:
            tenant_id: Azure AD tenant ID
            client_id: Application (client) ID
            client_secret: Client secret
        """
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self._access_token: Optional[str] = None

    def _get_access_token(self) -> str:
        """
        Acquire access token using client credentials flow

        Returns:
            Access token string
        """
        app = msal.ConfidentialClientApplication(
            self.client_id,
            authority=f"{self.AUTHORITY}/{self.tenant_id}",
            client_credential=self.client_secret
        )

        result = app.acquire_token_silent(self.SCOPE, account=None)
        if not result:
            result = app.acquire_token_for_client(scopes=self.SCOPE)

        if "access_token" not in result:
            raise Exception(f"Failed to acquire token: {result.get('error_description', 'Unknown error')}")

        self._access_token = result["access_token"]
        return self._access_token

    def _make_request(self, endpoint: str, params: Optional[Dict] = None, method: str = "GET", data: Optional[Dict] = None) -> Dict[Any, Any]:
        """
        Make authenticated request to Microsoft Graph API

        Args:
            endpoint: API endpoint
            params: Query parameters
            method: HTTP method (GET, POST, etc.)
            data: Request body data (for POST requests)

        Returns:
            JSON response
        """
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        if method.upper() == "GET":
            response = requests.get(endpoint, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(endpoint, headers=headers, params=params, data=json.dumps(data) if data else None)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        response.raise_for_status()

        return response.json()

    def get_alerts(
        self,
        max_results: int = 50,
        severity: Optional[List[str]] = None,
        time_range_hours: int = 24
    ) -> List[Dict[Any, Any]]:
        """
        Fetch alerts from Microsoft Defender

        Args:
            max_results: Maximum number of alerts to retrieve
            severity: Filter by severity levels (e.g., ['high', 'critical'])
            time_range_hours: Look back period in hours

        Returns:
            List of alert dictionaries
        """
        endpoint = f"{self.SECURITY_ENDPOINT}/alerts_v2"

        # Build filter
        filters = []

        # Time filter
        start_time = datetime.utcnow() - timedelta(hours=time_range_hours)
        time_filter = f"createdDateTime ge {start_time.isoformat()}Z"
        filters.append(time_filter)

        # Severity filter
        if severity:
            severity_filter = " or ".join([f"severity eq '{s}'" for s in severity])
            filters.append(f"({severity_filter})")

        params = {
            "$top": max_results,
            "$orderby": "createdDateTime desc"
        }

        if filters:
            params["$filter"] = " and ".join(filters)

        try:
            response = self._make_request(endpoint, params)
            return response.get("value", [])
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Try legacy alerts endpoint
                return self._get_legacy_alerts(max_results, severity, time_range_hours)
            raise

    def _get_legacy_alerts(
        self,
        max_results: int,
        severity: Optional[List[str]],
        time_range_hours: int
    ) -> List[Dict[Any, Any]]:
        """Fallback to legacy alerts endpoint"""
        endpoint = f"{self.SECURITY_ENDPOINT}/alerts"

        params = {
            "$top": max_results,
            "$orderby": "createdDateTime desc"
        }

        response = self._make_request(endpoint, params)
        alerts = response.get("value", [])

        # Manual filtering if needed
        if severity:
            alerts = [a for a in alerts if a.get("severity", "").lower() in severity]

        return alerts[:max_results]

    def get_incidents(
        self,
        max_results: int = 50,
        time_range_hours: int = 24
    ) -> List[Dict[Any, Any]]:
        """
        Fetch incidents from Microsoft Defender

        Args:
            max_results: Maximum number of incidents to retrieve
            time_range_hours: Look back period in hours

        Returns:
            List of incident dictionaries
        """
        endpoint = f"{self.SECURITY_ENDPOINT}/incidents"

        start_time = datetime.utcnow() - timedelta(hours=time_range_hours)

        params = {
            "$top": max_results,
            "$orderby": "createdDateTime desc",
            "$filter": f"createdDateTime ge {start_time.isoformat()}Z"
        }

        response = self._make_request(endpoint, params)
        return response.get("value", [])

    def get_alert_details(self, alert_id: str) -> Dict[Any, Any]:
        """
        Get detailed information for a specific alert

        Args:
            alert_id: Alert ID

        Returns:
            Alert details dictionary
        """
        endpoint = f"{self.SECURITY_ENDPOINT}/alerts_v2/{alert_id}"

        try:
            return self._make_request(endpoint)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                # Try legacy endpoint
                endpoint = f"{self.SECURITY_ENDPOINT}/alerts/{alert_id}"
                return self._make_request(endpoint)
            raise

    def run_kql_query(self, query: str, timeout_seconds: int = 60) -> Dict[str, Any]:
        """
        Execute a KQL (Kusto Query Language) query using Advanced Hunting

        Args:
            query: KQL query string
            timeout_seconds: Query timeout in seconds

        Returns:
            Query results dictionary with schema and results

        Example:
            query = '''
            DeviceProcessEvents
            | where Timestamp > ago(1d)
            | where FileName =~ "powershell.exe"
            | take 10
            '''
            results = client.run_kql_query(query)
        """
        # Prepare the request body
        body = {
            "Query": query
        }

        try:
            response = self._make_request(
                self.ADVANCED_HUNTING_ENDPOINT,
                method="POST",
                data=body
            )

            return {
                "schema": response.get("Schema", []),
                "results": response.get("Results", []),
                "stats": {
                    "execution_time": response.get("Stats", {}).get("ExecutionTime"),
                    "resource_usage": response.get("Stats", {}).get("ResourceUsage"),
                    "dataset_statistics": response.get("Stats", {}).get("DatasetStatistics")
                }
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 400:
                error_detail = e.response.json().get("error", {}).get("message", "Invalid query")
                raise ValueError(f"KQL Query Error: {error_detail}")
            raise

    def run_predefined_query(self, query_name: str, **kwargs) -> Dict[str, Any]:
        """
        Run a predefined KQL query with parameters

        Args:
            query_name: Name of the predefined query
            **kwargs: Parameters to substitute in the query

        Returns:
            Query results dictionary
        """
        queries = self._get_predefined_queries()

        if query_name not in queries:
            raise ValueError(f"Unknown query: {query_name}. Available: {list(queries.keys())}")

        query_template = queries[query_name]
        query = query_template.format(**kwargs)

        return self.run_kql_query(query)

    def _get_predefined_queries(self) -> Dict[str, str]:
        """Get predefined KQL queries for common investigations"""
        return {
            # Process investigation queries
            "suspicious_process_activity": """
                DeviceProcessEvents
                | where Timestamp > ago({hours}h)
                | where ProcessCommandLine contains "{indicator}"
                | project Timestamp, DeviceName, AccountName, FileName, ProcessCommandLine, SHA256
                | order by Timestamp desc
                | take {limit}
            """,

            "powershell_execution": """
                DeviceProcessEvents
                | where Timestamp > ago({hours}h)
                | where FileName in~ ("powershell.exe", "pwsh.exe", "powershell_ise.exe")
                | where ProcessCommandLine has_any ("{keywords}")
                | project Timestamp, DeviceName, AccountName, ProcessCommandLine, SHA256
                | order by Timestamp desc
                | take {limit}
            """,

            # File investigation queries
            "file_hash_investigation": """
                DeviceFileEvents
                | where Timestamp > ago({hours}h)
                | where SHA256 == "{file_hash}"
                | project Timestamp, DeviceName, AccountName, FileName, FolderPath, FileOriginUrl, FileOriginIP
                | order by Timestamp desc
                | take {limit}
            """,

            "file_activity_by_name": """
                DeviceFileEvents
                | where Timestamp > ago({hours}h)
                | where FileName =~ "{file_name}"
                | project Timestamp, DeviceName, AccountName, ActionType, FolderPath, SHA256
                | order by Timestamp desc
                | take {limit}
            """,

            # Network investigation queries
            "network_connections": """
                DeviceNetworkEvents
                | where Timestamp > ago({hours}h)
                | where RemoteUrl contains "{domain}" or RemoteIP == "{ip}"
                | project Timestamp, DeviceName, InitiatingProcessFileName, RemoteUrl, RemoteIP, RemotePort
                | order by Timestamp desc
                | take {limit}
            """,

            "outbound_connections_by_process": """
                DeviceNetworkEvents
                | where Timestamp > ago({hours}h)
                | where InitiatingProcessFileName =~ "{process_name}"
                | project Timestamp, DeviceName, RemoteUrl, RemoteIP, RemotePort, InitiatingProcessCommandLine
                | order by Timestamp desc
                | take {limit}
            """,

            # Login investigation queries
            "failed_logins": """
                DeviceLogonEvents
                | where Timestamp > ago({hours}h)
                | where AccountName == "{account_name}"
                | where ActionType == "LogonFailed"
                | project Timestamp, DeviceName, AccountName, LogonType, FailureReason, RemoteIP
                | order by Timestamp desc
                | take {limit}
            """,

            "successful_logins_by_user": """
                DeviceLogonEvents
                | where Timestamp > ago({hours}h)
                | where AccountName == "{account_name}"
                | where ActionType == "LogonSuccess"
                | project Timestamp, DeviceName, AccountName, LogonType, RemoteIP
                | order by Timestamp desc
                | take {limit}
            """,

            # Malware investigation queries
            "malware_detections": """
                DeviceEvents
                | where Timestamp > ago({hours}h)
                | where ActionType has_any ("AntivirusDetection", "AntivirusSignatureUpdate", "AntivirusRealtimeProtectionError")
                | project Timestamp, DeviceName, ActionType, FileName, FolderPath, SHA256
                | order by Timestamp desc
                | take {limit}
            """,

            # Registry investigation queries
            "registry_modifications": """
                DeviceRegistryEvents
                | where Timestamp > ago({hours}h)
                | where RegistryKey has "{registry_path}"
                | project Timestamp, DeviceName, ActionType, RegistryKey, RegistryValueName, RegistryValueData, InitiatingProcessFileName
                | order by Timestamp desc
                | take {limit}
            """,

            # Email investigation queries
            "email_by_sender": """
                EmailEvents
                | where Timestamp > ago({hours}h)
                | where SenderFromAddress == "{sender_email}"
                | project Timestamp, Subject, RecipientEmailAddress, DeliveryAction, ThreatTypes, AttachmentCount
                | order by Timestamp desc
                | take {limit}
            """,

            "email_with_attachments": """
                EmailAttachmentInfo
                | where Timestamp > ago({hours}h)
                | where FileName has "{file_name}" or SHA256 == "{file_hash}"
                | join EmailEvents on NetworkMessageId
                | project Timestamp, SenderFromAddress, RecipientEmailAddress, Subject, FileName, SHA256, ThreatTypes
                | order by Timestamp desc
                | take {limit}
            """,

            # Alert correlation query
            "alerts_for_device": """
                AlertInfo
                | where Timestamp > ago({hours}h)
                | join AlertEvidence on AlertId
                | where DeviceName == "{device_name}"
                | project Timestamp, Title, Severity, Category, ServiceSource
                | order by Timestamp desc
                | take {limit}
            """
        }

    def test_connection(self) -> bool:
        """
        Test API connection and credentials

        Returns:
            True if connection successful
        """
        try:
            self._get_access_token()
            # Try a simple API call
            self._make_request(f"{self.SECURITY_ENDPOINT}/alerts_v2", {"$top": 1})
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def test_kql_query(self) -> bool:
        """
        Test KQL query capability with a simple query

        Returns:
            True if KQL queries are working
        """
        try:
            # Simple test query
            query = "AlertInfo | take 1"
            self.run_kql_query(query)
            return True
        except Exception as e:
            print(f"KQL query test failed: {e}")
            return False
