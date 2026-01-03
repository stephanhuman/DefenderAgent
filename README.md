# DefenderAgent

An AI-powered alert investigation agent for Microsoft Defender that automatically triages and investigates security alerts and incidents using your own AI model (BYOM - Bring Your Own Model).

## Features

- **Automated Alert Investigation**: Automatically fetch and investigate alerts from Microsoft Defender
- **Incident Analysis**: Comprehensive investigation of security incidents
- **BYOM Support**: Use your own AI model (OpenAI GPT-4 or Anthropic Claude)
- **Rule-Based Triage**: Configurable rules based on alert type and severity
- **Multiple Report Formats**: Generate reports in JSON, HTML, or Markdown
- **Rich CLI Interface**: Beautiful command-line interface with progress tracking
- **Configurable**: Extensive configuration options via environment variables

## Phase 1 Capabilities

This is Phase 1 of the DefenderAgent, which focuses on:

1. Reading alerts and incidents from MS Defender
2. Performing basic investigation and triage based on predefined rules
3. Generating comprehensive investigation reports

## Prerequisites

- Python 3.8 or higher
- Microsoft Defender (Azure AD) credentials with appropriate permissions
- API key for either OpenAI or Anthropic

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd DefenderAgent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your environment:
```bash
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

### Microsoft Defender Setup

You need to register an application in Azure AD and grant it the necessary permissions:

1. Go to [Azure Portal](https://portal.azure.com)
2. Navigate to **Azure Active Directory** > **App registrations**
3. Click **New registration**
4. Name your app (e.g., "DefenderAgent")
5. Set **Supported account types** to "Accounts in this organizational directory only"
6. Click **Register**

7. **Note down the Application (client) ID and Directory (tenant) ID**

8. Create a client secret:
   - Go to **Certificates & secrets**
   - Click **New client secret**
   - Add a description and set expiration
   - **Copy the secret value immediately** (you won't be able to see it again)

9. Grant API permissions:
   - Go to **API permissions**
   - Click **Add a permission**
   - Select **Microsoft Graph**
   - Select **Application permissions**
   - Add the following permissions:
     - `SecurityAlert.Read.All`
     - `SecurityIncident.Read.All`
     - `SecurityEvents.Read.All`
   - Click **Grant admin consent**

### Environment Variables

Edit the `.env` file with your credentials:

```env
# Microsoft Defender API Configuration
TENANT_ID=your-tenant-id-here
CLIENT_ID=your-client-id-here
CLIENT_SECRET=your-client-secret-here

# AI Model Configuration (choose one)
# For OpenAI:
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4-turbo-preview
LLM_PROVIDER=openai

# OR for Anthropic:
# ANTHROPIC_API_KEY=your-anthropic-api-key-here
# ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
# LLM_PROVIDER=anthropic

# Investigation Settings
MAX_ALERTS_TO_PROCESS=50
SEVERITY_THRESHOLD=medium
INVESTIGATION_DEPTH=basic
```

### Triage Rules Configuration

Edit `config/triage_rules.yaml` to customize investigation rules based on:
- Alert type (Malware, Phishing, Exploit, SuspiciousActivity, etc.)
- Severity level (critical, high, medium, low, informational)
- Investigation steps for each category
- AI prompt templates for different priority levels

## Usage

### Test Connection

Test your MS Defender API connection:

```bash
python -m src.main test-connection
```

### Investigate Alerts

Investigate alerts from the last 24 hours:

```bash
python -m src.main investigate-alerts
```

Investigate only critical and high severity alerts:

```bash
python -m src.main investigate-alerts --severity critical --severity high
```

Investigate alerts from the last 48 hours with HTML report:

```bash
python -m src.main investigate-alerts --hours 48 --format html
```

Limit to 10 alerts and generate all report formats:

```bash
python -m src.main investigate-alerts --max-alerts 10 --format all
```

### Investigate Incidents

Investigate incidents from the last 24 hours:

```bash
python -m src.main investigate-incidents
```

Investigate incidents with custom time range:

```bash
python -m src.main investigate-incidents --hours 72 --format markdown
```

### CLI Options

#### investigate-alerts

```
Options:
  -c, --config PATH              Path to .env configuration file
  -n, --max-alerts INTEGER       Maximum number of alerts to process
  -s, --severity [critical|high|medium|low|informational]
                                 Filter by severity (can be specified multiple times)
  -h, --hours INTEGER            Time range in hours to fetch alerts (default: 24)
  -f, --format [json|html|markdown|all]
                                 Report format (default: json)
  -o, --output-dir PATH          Output directory for reports (default: reports)
  --help                         Show this message and exit
```

#### investigate-incidents

```
Options:
  -c, --config PATH              Path to .env configuration file
  -n, --max-incidents INTEGER    Maximum number of incidents to process
  -h, --hours INTEGER            Time range in hours to fetch incidents (default: 24)
  -f, --format [json|html|markdown|all]
                                 Report format (default: json)
  -o, --output-dir PATH          Output directory for reports (default: reports)
  --help                         Show this message and exit
```

## Report Formats

### JSON Report

Machine-readable format containing:
- Full investigation results
- Alert/incident details
- Summary statistics
- Timestamps

### HTML Report

Beautiful, styled HTML report with:
- Color-coded severity badges
- Sortable tables
- Expandable investigation details
- Summary dashboard

### Markdown Report

Markdown-formatted report suitable for:
- GitHub/GitLab integration
- Documentation systems
- Plain text viewing
- Version control

## Project Structure

```
DefenderAgent/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore file
├── config/
│   └── triage_rules.yaml        # Triage rules configuration
├── src/
│   ├── __init__.py
│   ├── main.py                  # CLI entry point
│   ├── config.py                # Configuration management
│   ├── defender_client.py       # MS Defender API client
│   ├── llm_client.py            # BYOM LLM integration
│   ├── triage_engine.py         # Rules engine
│   ├── investigation_agent.py   # Investigation orchestration
│   └── report_generator.py      # Report generation
└── reports/                     # Generated reports directory
```

## How It Works

1. **Fetch Alerts/Incidents**: The agent connects to Microsoft Defender API and fetches recent alerts or incidents based on your filters

2. **Triage**: Each alert is processed through the triage engine which:
   - Categorizes the alert type (Malware, Phishing, Exploit, etc.)
   - Determines priority based on severity and type
   - Selects appropriate investigation steps

3. **Investigation**: For alerts requiring auto-investigation:
   - A detailed prompt is constructed with alert details and investigation steps
   - The LLM analyzes the alert and provides detailed findings
   - Recommendations are generated for containment and remediation

4. **Report Generation**: Results are compiled into comprehensive reports in your chosen format(s)

## Security Best Practices

- **Never commit your `.env` file** - it contains sensitive credentials
- **Use environment-specific credentials** - don't use production credentials for testing
- **Rotate secrets regularly** - especially client secrets
- **Review permissions** - grant only the minimum required permissions
- **Secure API keys** - keep your OpenAI/Anthropic API keys secure
- **Review reports** - always review AI-generated recommendations before acting

## Troubleshooting

### Authentication Errors

If you get authentication errors:
1. Verify your `TENANT_ID`, `CLIENT_ID`, and `CLIENT_SECRET` are correct
2. Ensure admin consent is granted for API permissions
3. Check that the client secret hasn't expired

### No Alerts Found

If no alerts are returned:
1. Verify you have alerts in the specified time range
2. Check severity filters aren't too restrictive
3. Ensure your app has the correct permissions

### LLM Errors

If you get LLM-related errors:
1. Verify your API key is correct
2. Check you have sufficient API credits/quota
3. Ensure the model name is correct for your provider

## Future Enhancements (Phase 2+)

Planned features for future phases:
- Automated response actions (containment, isolation)
- Integration with SOAR platforms
- Custom investigation playbooks
- Machine learning for pattern detection
- Threat hunting capabilities
- Real-time monitoring and alerting
- Dashboard and visualization
- Multi-tenant support

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Open an issue on GitHub
- Check the troubleshooting section
- Review Microsoft Defender API documentation

## Acknowledgments

- Microsoft Graph API for Defender integration
- OpenAI and Anthropic for AI capabilities
- Click and Rich for beautiful CLI experience
