# Quick Start Guide

Get up and running with DefenderAgent in 5 minutes!

## Prerequisites

- Docker and Docker Compose
- Python 3.11+
- Azure DevOps account with PAT (Personal Access Token)
- Anthropic API key (for Claude)

## Step 1: Get Your Credentials

### Azure DevOps Personal Access Token

1. Go to Azure DevOps: https://dev.azure.com
2. Click on User Settings (top right) → Personal Access Tokens
3. Click "New Token"
4. Give it a name (e.g., "DefenderAgent")
5. Set expiration as needed
6. Select scopes:
   - **Code**: Read & Write
   - **Pull Request**: Read, Write & Manage
7. Click "Create" and **copy the token** (you won't see it again!)

### Anthropic API Key

1. Go to: https://console.anthropic.com/
2. Sign in or create an account
3. Navigate to API Keys
4. Create a new API key
5. Copy the key

## Step 2: Configure Environment

```bash
# Clone or navigate to DefenderAgent directory
cd DefenderAgent

# Copy the example environment file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Update these values in `.env`:
```bash
AZURE_DEVOPS_PAT=your_pat_token_here
AZURE_DEVOPS_ORG=your_organization_name
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## Step 3: Install and Build

```bash
# Install Python dependencies
make install

# Build the Docker image (this may take a few minutes)
make build

# Start the container
make up
```

## Step 4: Run Your First Task

### Example 1: Simple Bug Fix

```bash
python run_task.py \
  --repo "https://dev.azure.com/myorg/myproject/_git/myrepo" \
  --task "Fix the null pointer exception in UserService.login() method" \
  --branch "bugfix/userservice-npe"
```

### Example 2: Feature Implementation

```bash
python run_task.py \
  --repo "https://dev.azure.com/myorg/webapp/_git/frontend" \
  --task "Add a dark mode toggle button in the settings page with localStorage persistence" \
  --branch "feature/dark-mode" \
  --create-pr
```

### Example 3: Using Make

```bash
make run-task \
  REPO="https://dev.azure.com/myorg/project/_git/repo" \
  TASK="Add input validation for email addresses" \
  BRANCH="feature/email-validation"
```

## Step 5: Monitor Progress

```bash
# View real-time logs
make logs

# Check container status
make status

# Open a shell in the container
make shell
```

## What Happens During Execution?

1. **Authentication**: Validates your Azure DevOps credentials
2. **Clone**: Clones the repository to the Docker container
3. **Branch**: Creates a new feature branch from the base branch
4. **Analyze**: AI agent analyzes the codebase structure
5. **Implement**: Agent makes the necessary code changes
6. **Test**: Runs tests (if enabled)
7. **Commit**: Creates a descriptive commit with changes
8. **Push**: Pushes the feature branch to Azure DevOps
9. **PR** (optional): Creates a pull request

## Common Commands

```bash
# Start DefenderAgent
make up

# Stop DefenderAgent
make down

# View logs
make logs

# Run tests
make test

# Format code
make format

# Clean up
make clean

# Complete cleanup (including Docker volumes)
make clean-all

# Get help
make help
```

## Troubleshooting

### "Authentication failed"

- Double-check your PAT in `.env`
- Verify the PAT has Code Read/Write permissions
- Ensure the PAT hasn't expired

### "Repository not found"

- Verify the repository URL is correct
- Ensure your PAT has access to the repository
- Check that the organization name in `.env` matches the URL

### "Docker build failed"

- Ensure Docker is running: `docker ps`
- Try rebuilding: `make clean && make build`
- Check Docker logs: `docker-compose logs`

### "Task execution failed"

- Check the logs: `make logs`
- Verify your Anthropic API key is valid
- Ensure you have sufficient API credits

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [examples/](examples/) for more task examples
- Configure advanced options in `.env`
- Integrate with your CI/CD pipeline

## Getting Help

- Check the logs: `make logs`
- Review the [README.md](README.md)
- Open an issue on GitHub
- Check Azure DevOps PAT permissions

## Security Notes

⚠️ **Important Security Practices:**

1. **Never commit `.env` file** (it's in `.gitignore`)
2. **Rotate PATs regularly** (set expiration dates)
3. **Use least-privilege access** (only required permissions)
4. **Review generated code** before merging
5. **Enable branch protection** rules in Azure DevOps

Happy coding! 🚀
