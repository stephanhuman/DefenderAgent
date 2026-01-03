# DefenderAgent - Docker-Based Coding Environment

A containerized coding environment that integrates with Azure DevOps, automatically branches repositories, and executes coding tasks using AI agents.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Input                                │
│  - Coding Task/Prompt                                           │
│  - Azure DevOps Repo URL                                        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Agent Orchestrator                              │
│  - Parses task requirements                                     │
│  - Manages workflow execution                                   │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│              Azure DevOps Integration                            │
│  - Authenticate with PAT                                        │
│  - Clone repository                                             │
│  - Create feature branch                                        │
│  - Sync to Docker volume                                        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│               Docker Coding Container                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Development Tools:                                       │  │
│  │  - Python, Node.js, Java, .NET, Go, Rust                │  │
│  │  - Git, Azure CLI                                        │  │
│  │  - Build tools & package managers                        │  │
│  └───────────────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Coding Agent:                                           │  │
│  │  - Analyzes codebase                                     │  │
│  │  - Implements features                                   │  │
│  │  - Fixes bugs                                            │  │
│  │  - Runs tests                                            │  │
│  │  - Generates documentation                               │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Git Push & PR Creation                          │
│  - Commit changes with descriptive messages                     │
│  - Push to feature branch                                       │
│  - Create Pull Request (optional)                               │
└─────────────────────────────────────────────────────────────────┘
```

## Features

- **Multi-language Support**: Pre-configured with Python, Node.js, Java, .NET, Go, and Rust
- **Azure DevOps Integration**: Seamless authentication and repository management
- **Automatic Branching**: Creates feature branches following best practices
- **AI-Powered Coding**: Executes complex coding tasks autonomously
- **Test Execution**: Runs tests and ensures code quality
- **Git Workflow**: Automatic commits and push to remote
- **Isolated Environment**: Each task runs in a clean Docker container

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Azure DevOps Personal Access Token (PAT)
- Python 3.11+

### 1. Configuration

Create a `.env` file:

```bash
AZURE_DEVOPS_PAT=your_personal_access_token
AZURE_DEVOPS_ORG=your_organization
ANTHROPIC_API_KEY=your_claude_api_key  # For AI agent
```

### 2. Start the System

```bash
# Build and start the container
docker-compose up -d

# Run a coding task
python run_task.py \
  --repo "https://dev.azure.com/yourorg/project/_git/repo" \
  --task "Add user authentication using JWT" \
  --branch "feature/add-jwt-auth"
```

### 3. Monitor Progress

```bash
# View logs
docker-compose logs -f agent

# Check status
python status.py
```

## Usage Examples

### Example 1: Bug Fix

```bash
python run_task.py \
  --repo "https://dev.azure.com/myorg/myproject/_git/api" \
  --task "Fix the null pointer exception in UserService.login()" \
  --branch "bugfix/userservice-npe"
```

### Example 2: Feature Implementation

```bash
python run_task.py \
  --repo "https://dev.azure.com/myorg/myproject/_git/webapp" \
  --task "Implement dark mode toggle with user preference persistence" \
  --branch "feature/dark-mode"
```

### Example 3: Refactoring

```bash
python run_task.py \
  --repo "https://dev.azure.com/myorg/myproject/_git/service" \
  --task "Refactor payment processing to use strategy pattern" \
  --branch "refactor/payment-strategy"
```

## Project Structure

```
DefenderAgent/
├── README.md
├── Dockerfile                    # Coding environment container
├── docker-compose.yml           # Container orchestration
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment variables template
├── run_task.py                  # Main entry point
├── src/
│   ├── __init__.py
│   ├── azure_devops/
│   │   ├── __init__.py
│   │   ├── auth.py             # Azure DevOps authentication
│   │   ├── repo.py             # Repository operations
│   │   └── branch.py           # Branch management
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── orchestrator.py    # Agent workflow orchestration
│   │   ├── executor.py        # Task execution
│   │   └── context.py         # Task context management
│   ├── docker/
│   │   ├── __init__.py
│   │   ├── manager.py         # Docker container management
│   │   └── sync.py            # Code synchronization
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # Logging configuration
│       └── config.py          # Configuration management
└── tests/
    └── ...
```

## Configuration Options

### Environment Variables

- `AZURE_DEVOPS_PAT`: Personal Access Token for Azure DevOps
- `AZURE_DEVOPS_ORG`: Organization name
- `ANTHROPIC_API_KEY`: API key for Claude (coding agent)
- `DEFAULT_BASE_BRANCH`: Default base branch (default: `main`)
- `AUTO_CREATE_PR`: Auto-create PR after task completion (default: `false`)
- `RUN_TESTS`: Run tests before committing (default: `true`)

### Task Configuration (YAML)

```yaml
# task_config.yaml
task:
  description: "Implement user authentication"
  repository: "https://dev.azure.com/org/project/_git/repo"
  base_branch: "main"
  feature_branch: "feature/auth"

options:
  run_tests: true
  create_pr: true
  pr_reviewers:
    - user@example.com

agent:
  model: "claude-sonnet-4"
  temperature: 0.0
  max_iterations: 10
```

## Security Considerations

1. **PAT Storage**: Store Azure DevOps PAT securely, never commit to repo
2. **Container Isolation**: Each task runs in isolated container
3. **Network Security**: Container has limited network access
4. **Code Review**: Always review generated code before merging
5. **Secret Scanning**: Automated scanning for committed secrets

## Troubleshooting

### Authentication Errors

```bash
# Verify PAT is valid
az devops login --organization https://dev.azure.com/yourorg

# Check PAT permissions (requires: Code Read/Write, PR Read/Write)
```

### Docker Issues

```bash
# Reset containers
docker-compose down -v
docker-compose up --build

# Check logs
docker-compose logs agent
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest tests/`
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- GitHub Issues: [DefenderAgent Issues](https://github.com/yourorg/DefenderAgent/issues)
- Documentation: [Wiki](https://github.com/yourorg/DefenderAgent/wiki)
