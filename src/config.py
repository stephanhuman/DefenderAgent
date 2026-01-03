"""
Configuration management for DefenderAgent
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import yaml


class Config:
    """Application configuration"""

    def __init__(self, env_file: Optional[str] = None):
        """
        Initialize configuration

        Args:
            env_file: Path to .env file. If None, looks for .env in project root
        """
        # Load environment variables
        if env_file:
            load_dotenv(env_file)
        else:
            # Try to find .env in project root
            project_root = Path(__file__).parent.parent
            env_path = project_root / ".env"
            if env_path.exists():
                load_dotenv(env_path)

        # Microsoft Defender API settings
        self.tenant_id = os.getenv("TENANT_ID")
        self.client_id = os.getenv("CLIENT_ID")
        self.client_secret = os.getenv("CLIENT_SECRET")

        # LLM Provider settings
        self.llm_provider = os.getenv("LLM_PROVIDER", "openai").lower()

        # OpenAI settings
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")

        # Anthropic settings
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

        # Investigation settings
        self.max_alerts_to_process = int(os.getenv("MAX_ALERTS_TO_PROCESS", "50"))
        self.severity_threshold = os.getenv("SEVERITY_THRESHOLD", "medium").lower()
        self.investigation_depth = os.getenv("INVESTIGATION_DEPTH", "basic").lower()

        # Load triage rules
        self.triage_rules = self._load_triage_rules()

    def _load_triage_rules(self) -> dict:
        """Load triage rules from YAML file"""
        project_root = Path(__file__).parent.parent
        rules_path = project_root / "config" / "triage_rules.yaml"

        if not rules_path.exists():
            raise FileNotFoundError(f"Triage rules file not found: {rules_path}")

        with open(rules_path, 'r') as f:
            return yaml.safe_load(f)

    def validate(self) -> list[str]:
        """
        Validate configuration

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate MS Defender credentials
        if not self.tenant_id:
            errors.append("TENANT_ID is required")
        if not self.client_id:
            errors.append("CLIENT_ID is required")
        if not self.client_secret:
            errors.append("CLIENT_SECRET is required")

        # Validate LLM configuration
        if self.llm_provider == "openai":
            if not self.openai_api_key:
                errors.append("OPENAI_API_KEY is required when using OpenAI provider")
        elif self.llm_provider == "anthropic":
            if not self.anthropic_api_key:
                errors.append("ANTHROPIC_API_KEY is required when using Anthropic provider")
        else:
            errors.append(f"Invalid LLM_PROVIDER: {self.llm_provider}. Must be 'openai' or 'anthropic'")

        return errors

    def get_llm_config(self) -> dict:
        """Get LLM configuration based on provider"""
        if self.llm_provider == "openai":
            return {
                "provider": "openai",
                "api_key": self.openai_api_key,
                "model": self.openai_model
            }
        elif self.llm_provider == "anthropic":
            return {
                "provider": "anthropic",
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model
            }
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")
