"""
Microsoft Defender API client for fetching alerts and incidents
"""

import msal
import requests
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta


class DefenderClient:
    """Client for Microsoft Defender API via Microsoft Graph"""

    # Microsoft Graph API endpoints
    GRAPH_ENDPOINT = "https://graph.microsoft.com/v1.0"
    SECURITY_ENDPOINT = f"{GRAPH_ENDPOINT}/security"
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

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[Any, Any]:
        """
        Make authenticated request to Microsoft Graph API

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            JSON response
        """
        token = self._get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        response = requests.get(endpoint, headers=headers, params=params)
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
