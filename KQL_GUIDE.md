# KQL Query Support in DefenderAgent

DefenderAgent now supports running KQL (Kusto Query Language) queries against Microsoft Defender Advanced Hunting tables. This enables deep investigation and correlation across security data.

## Features

- **Automated KQL Queries**: Relevant queries are automatically run during alert investigations based on alert type
- **Predefined Queries**: 15+ ready-to-use queries for common investigation scenarios
- **Custom Queries**: Run any KQL query directly from the CLI
- **Rich Context**: KQL results are included in AI-powered investigation reports

## Available Tables

DefenderAgent can query the following Defender Advanced Hunting tables:

- `AlertInfo` - Alert metadata
- `AlertEvidence` - Alert evidence and entities
- `DeviceProcessEvents` - Process execution events
- `DeviceFileEvents` - File creation, modification, and deletion events
- `DeviceNetworkEvents` - Network connections
- `DeviceLogonEvents` - Authentication and logon events
- `DeviceRegistryEvents` - Registry modifications
- `DeviceEvents` - General device events including AV detections
- `EmailEvents` - Email messages
- `EmailAttachmentInfo` - Email attachments

## Predefined Queries

### Process Investigation
- `suspicious_process_activity` - Search for processes by command line
- `powershell_execution` - Find PowerShell executions with specific keywords

### File Investigation
- `file_hash_investigation` - Track file by SHA256 hash
- `file_activity_by_name` - Find file operations by filename

### Network Investigation
- `network_connections` - Find connections to specific domains/IPs
- `outbound_connections_by_process` - Network connections by process name

### Login Investigation
- `failed_logins` - Failed login attempts for a user
- `successful_logins_by_user` - Successful logins for a user

### Malware Investigation
- `malware_detections` - Antivirus detections and alerts

### Registry Investigation
- `registry_modifications` - Registry changes by path

### Email Investigation
- `email_by_sender` - Emails from specific sender
- `email_with_attachments` - Emails with specific attachments

### Alert Correlation
- `alerts_for_device` - All alerts for a specific device

## CLI Usage

### List Available Queries

```bash
python -m src.main run-kql --list-queries
```

### Run a Predefined Query

```bash
# Interactive mode - prompts for parameters
python -m src.main run-kql --query-name file_hash_investigation

# With output file
python -m src.main run-kql --query-name malware_detections --output results.json
```

### Run a Custom Query

```bash
python -m src.main run-kql --query "
DeviceProcessEvents
| where Timestamp > ago(1d)
| where FileName =~ 'powershell.exe'
| project Timestamp, DeviceName, ProcessCommandLine
| take 10
"
```

## Integration with Investigations

KQL queries are automatically integrated into alert investigations:

1. When an alert is triaged, the system identifies the alert type
2. Relevant KQL queries are selected from the triage rules
3. Entities (devices, files, users, IPs) are extracted from the alert
4. KQL queries are run with extracted parameters
5. Results are formatted and included in the AI analysis prompt
6. The LLM considers both alert data and KQL results for deeper analysis

Example triage rule with KQL queries:

```yaml
- alert_type: "Malware"
  severity: ["high", "critical"]
  priority: "critical"
  auto_investigate: true
  investigation_steps:
    - "Check file hash reputation"
    - "Identify affected devices"
  kql_queries:
    - "malware_detections"
    - "file_hash_investigation"
    - "alerts_for_device"
```

## Python API Usage

### Run Custom Query

```python
from src.defender_client import DefenderClient

client = DefenderClient(tenant_id, client_id, client_secret)

query = """
DeviceProcessEvents
| where Timestamp > ago(24h)
| where FileName =~ "cmd.exe"
| take 10
"""

result = client.run_kql_query(query)
print(f"Found {len(result['results'])} results")
```

### Run Predefined Query

```python
result = client.run_predefined_query(
    "file_hash_investigation",
    file_hash="abc123...",
    hours="48",
    limit="20"
)
```

## Query Parameters

Most predefined queries support these parameters:

- `hours` - Time range to search (default: 24)
- `limit` - Maximum number of results (default: 10)
- Query-specific parameters:
  - `device_name` - Device/host name
  - `account_name` - User account name
  - `file_hash` - SHA256 file hash
  - `file_name` - File name
  - `domain` - Domain name
  - `ip` - IP address
  - `sender_email` - Email sender address
  - `process_name` - Process executable name
  - `indicator` - Search pattern/indicator
  - `keywords` - Keywords to search for
  - `registry_path` - Registry path

## Permission Requirements

To use KQL queries, ensure your Azure AD app has the following permissions:

- `ThreatHunting.Read.All` (Application permission)

Grant admin consent after adding this permission in Azure Portal.

## Examples

### Investigate PowerShell Activity

```bash
python -m src.main run-kql --query-name powershell_execution
# Enter parameters when prompted
# Hours to look back: 48
# Keywords to search: encoded bypass
```

### Find Files by Hash

```bash
python -m src.main run-kql --query-name file_hash_investigation
# File hash (SHA256): abc123def456...
# Hours to look back: 72
```

### Check Failed Logins

```bash
python -m src.main run-kql --query-name failed_logins
# Account name: user@company.com
# Hours to look back: 24
```

### Custom Threat Hunting

```bash
python -m src.main run-kql --query "
DeviceProcessEvents
| where Timestamp > ago(7d)
| where ProcessCommandLine has_any ('mimikatz', 'procdump', 'bloodhound')
| project Timestamp, DeviceName, AccountName, FileName, ProcessCommandLine
| order by Timestamp desc
" --output threat_hunt.json
```

## Best Practices

1. **Start Narrow**: Begin with specific time ranges and expand if needed
2. **Limit Results**: Use `take` or the `limit` parameter to avoid overwhelming output
3. **Use Filters Early**: Apply `where` clauses early in the query for better performance
4. **Test Queries**: Test new queries with small time ranges first
5. **Save Results**: Use `--output` to save results for further analysis
6. **Combine with AI**: Let the LLM analyze KQL results for deeper insights

## Troubleshooting

### "ThreatHunting.Read.All permission required"

Add the permission in Azure AD app registration and grant admin consent.

### "Query execution timeout"

- Reduce time range
- Add more filters
- Use `take` to limit results

### "Invalid query syntax"

- Check KQL syntax
- Ensure table names are correct
- Verify column names exist in the table

## Advanced Usage

### Create Custom Predefined Queries

Edit `src/defender_client.py` and add to the `_get_predefined_queries()` method:

```python
"my_custom_query": """
    DeviceEvents
    | where Timestamp > ago({hours}h)
    | where ActionType == "MyCustomAction"
    | take {limit}
"""
```

### Modify Query Parameters

Queries support Python string formatting. Use `{parameter_name}` in your query template.

## Resources

- [KQL Quick Reference](https://docs.microsoft.com/en-us/azure/data-explorer/kql-quick-reference)
- [Advanced Hunting Schema](https://docs.microsoft.com/en-us/microsoft-365/security/defender/advanced-hunting-schema-tables)
- [Microsoft Defender API Documentation](https://docs.microsoft.com/en-us/microsoft-365/security/defender/api-advanced-hunting)
