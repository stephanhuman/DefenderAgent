"""Tests for configuration module"""

import pytest
import os
from pathlib import Path
from src.utils.config import Config, AzureDevOpsConfig, AgentConfig


def test_azure_devops_config_validation():
    """Test Azure DevOps config validation"""
    with pytest.raises(ValueError):
        AzureDevOpsConfig(pat="", organization="myorg")

    with pytest.raises(ValueError):
        AzureDevOpsConfig(pat="your_personal_access_token_here", organization="myorg")


def test_agent_config_validation():
    """Test Agent config validation"""
    with pytest.raises(ValueError):
        AgentConfig(api_key="")

    with pytest.raises(ValueError):
        AgentConfig(api_key="your_anthropic_api_key_here")


def test_config_from_env(monkeypatch):
    """Test loading config from environment"""
    monkeypatch.setenv("AZURE_DEVOPS_PAT", "test_pat_123")
    monkeypatch.setenv("AZURE_DEVOPS_ORG", "testorg")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key_123")

    config = Config.from_env()

    assert config.azure.pat == "test_pat_123"
    assert config.azure.organization == "testorg"
    assert config.agent.api_key == "test_key_123"


def test_config_defaults():
    """Test config defaults"""
    os.environ["AZURE_DEVOPS_PAT"] = "test_pat"
    os.environ["AZURE_DEVOPS_ORG"] = "testorg"
    os.environ["ANTHROPIC_API_KEY"] = "test_key"

    config = Config.from_env()

    assert config.git.default_base_branch == "main"
    assert config.task.run_tests is True
    assert config.task.auto_create_pr is False
    assert config.log_level == "INFO"
