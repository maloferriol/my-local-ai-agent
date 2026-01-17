"""
Model Configuration module for managing model-specific settings and capabilities.

This module provides configuration classes and settings for different
models, their capabilities, and runtime behavior.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ModelCapability(Enum):
    """Enumeration of model capabilities."""

    TOOLS = "tools"
    THINKING = "thinking"
    STREAMING = "streaming"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    CODE_EXECUTION = "code_execution"


@dataclass
class ModelConfig:
    """Configuration for a specific model."""

    name: str
    display_name: str = ""
    capabilities: List[ModelCapability] = field(default_factory=list)
    default_thinking_effort: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: float = 0.7
    supports_streaming: bool = True
    supports_tools: bool = False
    context_window: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize display name if not provided."""
        if not self.display_name:
            self.display_name = self.name

        # Set supports_tools based on capabilities
        if ModelCapability.TOOLS in self.capabilities:
            self.supports_tools = True

    def has_capability(self, capability: ModelCapability) -> bool:
        """Check if model has a specific capability."""
        return capability in self.capabilities

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "capabilities": [cap.value for cap in self.capabilities],
            "default_thinking_effort": self.default_thinking_effort,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "supports_streaming": self.supports_streaming,
            "supports_tools": self.supports_tools,
            "context_window": self.context_window,
            "metadata": self.metadata,
        }


class ModelConfigRegistry:
    """Registry for managing model configurations."""

    def __init__(self):
        self.configs: Dict[str, ModelConfig] = {}
        self._initialize_default_configs()

    def _initialize_default_configs(self):
        """Initialize default model configurations."""
        # GPT-OSS 20B model
        self.register_model(
            ModelConfig(
                name="gpt-oss:20b",
                display_name="GPT-OSS 20B",
                capabilities=[
                    ModelCapability.TOOLS,
                    ModelCapability.THINKING,
                    ModelCapability.STREAMING,
                    ModelCapability.FUNCTION_CALLING,
                ],
                default_thinking_effort="low",
                max_tokens=4096,
                temperature=0.7,
                context_window=32768,
                metadata={
                    "provider": "ollama",
                    "model_type": "chat",
                    "parameter_count": "20B",
                },
            )
        )

        # Add more model configurations as needed
        logger.info(f"Initialized {len(self.configs)} default model configurations")

    def register_model(self, config: ModelConfig) -> None:
        """Register a model configuration."""
        self.configs[config.name] = config
        logger.debug(f"Registered model config: {config.name}")

    def get_model_config(self, model_name: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        return self.configs.get(model_name)

    def get_models_with_capability(
        self, capability: ModelCapability
    ) -> List[ModelConfig]:
        """Get all models that have a specific capability."""
        return [
            config
            for config in self.configs.values()
            if config.has_capability(capability)
        ]

    def list_models(self) -> List[str]:
        """List all registered model names."""
        return list(self.configs.keys())

    def get_tool_capable_models(self) -> List[ModelConfig]:
        """Get all models that support tools."""
        return self.get_models_with_capability(ModelCapability.TOOLS)

    def validate_model(self, model_name: str) -> bool:
        """Validate that a model is registered and available."""
        return model_name in self.configs

    def get_model_metadata(self, model_name: str) -> Dict[str, Any]:
        """Get metadata for a specific model."""
        config = self.get_model_config(model_name)
        if not config:
            return {}
        return config.metadata

    def get_default_config_for_model(self, model_name: str) -> Dict[str, Any]:
        """Get default runtime configuration for a model."""
        config = self.get_model_config(model_name)
        if not config:
            return {
                "thinking_effort": None,
                "supports_tools": False,
                "max_tokens": None,
                "temperature": 0.7,
            }

        return {
            "thinking_effort": config.default_thinking_effort,
            "supports_tools": config.supports_tools,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "capabilities": [cap.value for cap in config.capabilities],
        }


# Global registry instance
model_registry = ModelConfigRegistry()


def get_model_registry() -> ModelConfigRegistry:
    """Get the global model registry instance."""
    return model_registry


def get_model_config(model_name: str) -> Optional[ModelConfig]:
    """Convenience function to get model configuration."""
    return model_registry.get_model_config(model_name)


def is_model_supported(model_name: str) -> bool:
    """Check if a model is supported."""
    return model_registry.validate_model(model_name)


def get_tool_capable_models() -> List[str]:
    """Get list of models that support tools."""
    configs = model_registry.get_tool_capable_models()
    return [config.name for config in configs]


def get_model_thinking_effort(model_name: str) -> Optional[str]:
    """Get default thinking effort for a model."""
    config = model_registry.get_model_config(model_name)
    return config.default_thinking_effort if config else None
