# DefenderAgent Setup Guide

This guide provides detailed step-by-step instructions for setting up DefenderAgent.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Azure AD App Registration](#azure-ad-app-registration)
3. [Python Environment Setup](#python-environment-setup)
4. [Configuration](#configuration)
5. [LLM Provider Setup](#llm-provider-setup)
6. [Testing](#testing)
7. [First Run](#first-run)

## Prerequisites

Before you begin, ensure you have:

- **Python 3.8+** installed on your system
- **Azure Active Directory** admin access (or someone who can create app registrations)
- **Microsoft Defender** active in your organization
- An **API key** for either OpenAI or Anthropic

Check Python version:
```bash
python --version
# or
python3 --version
```

## Azure AD App Registration

### Step 1: Create App Registration

1. Navigate to [Azure Portal](https://portal.azure.com)
2. Go to **Azure Active Directory**
3. Select **App registrations** from the left menu
4. Click **+ New registration**

### Step 2: Configure Basic Settings

1. **Name**: Enter a descriptive name (e.g., "DefenderAgent")
2. **Supported account types**: Select "Accounts in this organizational directory only (Single tenant)"
3. **Redirect URI**: Leave blank (not needed for this application)
4. Click **Register**

### Step 3: Record Application Details

After registration, you'll see the app overview page. Record these values:

- **Application (client) ID**: Copy this value
- **Directory (tenant) ID**: Copy this value

You'll need these for your `.env` file.

### Step 4: Create Client Secret

1. In your app registration, go to **Certificates & secrets**
2. Select **Client secrets** tab
3. Click **+ New client secret**
4. Add a description (e.g., "DefenderAgent Secret")
5. Select an expiration period (recommended: 12 months or less for security)
6. Click **Add**
7. **IMPORTANT**: Copy the **Value** immediately - you won't be able to see it again!

### Step 5: Grant API Permissions

1. Go to **API permissions** in your app registration
2. Click **+ Add a permission**
3. Select **Microsoft Graph**
4. Select **Application permissions** (not Delegated)
5. Find and add these permissions:
   - `SecurityAlert.Read.All`
   - `SecurityIncident.Read.All`
   - `SecurityEvents.Read.All` (optional, for additional context)

6. Click **Add permissions**
7. Click **Grant admin consent for [Your Organization]**
8. Confirm by clicking **Yes**

You should see green checkmarks next to all permissions indicating "Granted for [Your Organization]"

### Step 6: Verify Permissions

Ensure all three permissions show:
- Status: ✓ Granted for [Your Organization]
- Type: Application

## Python Environment Setup

### Option 1: Using venv (Recommended)

```bash
# Navigate to project directory
cd DefenderAgent

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Option 2: Using conda

```bash
# Create conda environment
conda create -n defenderagent python=3.10

# Activate environment
conda activate defenderagent

# Install dependencies
pip install -r requirements.txt
```

### Verify Installation

```bash
pip list
```

You should see packages including:
- msal
- requests
- openai or anthropic
- click
- rich
- pyyaml
- python-dotenv

## Configuration

### Step 1: Create .env File

```bash
cp .env.example .env
```

### Step 2: Edit .env File

Open `.env` in your favorite text editor and fill in your credentials:

```env
# Microsoft Defender API Configuration
TENANT_ID=your-tenant-id-from-step-3
CLIENT_ID=your-client-id-from-step-3
CLIENT_SECRET=your-client-secret-from-step-4

# Choose your LLM provider (openai or anthropic)
LLM_PROVIDER=openai

# If using OpenAI:
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-4-turbo-preview

# If using Anthropic (comment out OpenAI above and uncomment these):
# ANTHROPIC_API_KEY=your-anthropic-api-key
# ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Investigation Settings (optional - defaults shown)
MAX_ALERTS_TO_PROCESS=50
SEVERITY_THRESHOLD=medium
INVESTIGATION_DEPTH=basic
```

### Step 3: Customize Triage Rules (Optional)

Edit `config/triage_rules.yaml` to customize:
- Alert categorization logic
- Investigation steps for different alert types
- Priority assignments
- AI prompt templates

## LLM Provider Setup

### Option A: OpenAI

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign in or create an account
3. Navigate to **API keys** section
4. Click **+ Create new secret key**
5. Name your key (e.g., "DefenderAgent")
6. Copy the key and add to your `.env` file
7. Ensure you have credits in your OpenAI account

Recommended models:
- `gpt-4-turbo-preview` (best quality)
- `gpt-4` (good quality)
- `gpt-3.5-turbo` (faster, lower cost)

### Option B: Anthropic

1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign in or create an account
3. Navigate to **API Keys**
4. Click **Create Key**
5. Copy the key and add to your `.env` file
6. Ensure you have credits in your Anthropic account

Recommended models:
- `claude-3-5-sonnet-20241022` (best for analysis)
- `claude-3-opus-20240229` (highest quality)
- `claude-3-sonnet-20240229` (balanced)

## Testing

### Test 1: Verify Configuration

```bash
python -m src.main --help
```

You should see the CLI help message with available commands.

### Test 2: Test MS Defender Connection

```bash
python -m src.main test-connection
```

Expected output:
```
Testing MS Defender API connection...
✓ Connection successful!
```

If this fails:
- Double-check your credentials in `.env`
- Verify admin consent was granted
- Check that the client secret hasn't expired
- Ensure you have active Defender licenses

### Test 3: Fetch Sample Alerts

```bash
python -m src.main investigate-alerts --max-alerts 1 --format markdown
```

This will:
1. Fetch 1 alert from the last 24 hours
2. Investigate it using AI
3. Generate a markdown report

Check the `reports/` directory for the generated report.

## First Run

### Basic Alert Investigation

```bash
# Investigate critical and high severity alerts from last 24 hours
python -m src.main investigate-alerts \
  --severity critical \
  --severity high \
  --format all
```

This will:
1. Connect to MS Defender
2. Fetch critical and high severity alerts
3. Triage each alert
4. Perform AI-powered investigation
5. Generate JSON, HTML, and Markdown reports

### Review Results

Check the `reports/` directory:
- **JSON**: `alerts_investigation_YYYYMMDD_HHMMSS.json` - Full data
- **HTML**: `alerts_investigation_YYYYMMDD_HHMMSS.html` - Open in browser
- **Markdown**: `alerts_investigation_YYYYMMDD_HHMMSS.md` - View in text editor

## Common Issues

### Issue: "TENANT_ID is required"

**Solution**: Ensure your `.env` file has all required fields filled in.

### Issue: "Failed to acquire token"

**Solutions**:
- Verify CLIENT_ID and CLIENT_SECRET are correct
- Check that the app registration wasn't deleted
- Ensure the client secret hasn't expired

### Issue: "Insufficient privileges"

**Solutions**:
- Verify admin consent was granted
- Check that all three permissions are granted
- Ensure you're using Application permissions, not Delegated

### Issue: "No alerts found"

This is normal if:
- There are no alerts in the time range
- Your severity filters are too restrictive
- Your environment has no recent security alerts

Try:
- Extending the time range: `--hours 168` (7 days)
- Removing severity filters
- Checking Defender portal for alerts

### Issue: LLM API Errors

**Solutions**:
- Verify your API key is correct
- Check you have available credits/quota
- Try a different model name
- Check your internet connection

## Next Steps

Now that DefenderAgent is set up:

1. **Schedule Regular Runs**: Set up a cron job or scheduled task to run investigations daily
2. **Customize Rules**: Adjust `config/triage_rules.yaml` for your environment
3. **Integrate Reports**: Send reports to your SIEM or ticketing system
4. **Monitor API Usage**: Track your LLM API usage and costs
5. **Review Investigations**: Regularly review AI-generated recommendations

## Getting Help

If you encounter issues:
1. Check this setup guide
2. Review the main [README.md](README.md)
3. Check the troubleshooting section
4. Open an issue on GitHub

## Security Reminders

- Never commit your `.env` file
- Rotate secrets regularly
- Use read-only permissions where possible
- Review AI recommendations before acting
- Keep your API keys secure
