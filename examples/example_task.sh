#!/bin/bash
# Example: Run a coding task with DefenderAgent

# Configuration
REPO_URL="https://dev.azure.com/myorg/myproject/_git/myrepo"
TASK_DESCRIPTION="Add user authentication using JWT tokens with bcrypt password hashing"
FEATURE_BRANCH="feature/jwt-authentication"
BASE_BRANCH="main"

# Run the task
python run_task.py \
  --repo "$REPO_URL" \
  --task "$TASK_DESCRIPTION" \
  --branch "$FEATURE_BRANCH" \
  --base-branch "$BASE_BRANCH" \
  --run-tests \
  --create-pr

# Alternative using make
# make run-task REPO="$REPO_URL" TASK="$TASK_DESCRIPTION" BRANCH="$FEATURE_BRANCH"
