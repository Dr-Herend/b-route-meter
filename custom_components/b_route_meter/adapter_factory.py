"""Factory for creating B-route adapters."""

from typing import Type

from .adapter_interface import AdapterInterface
from .adapters.bp35a1 import BP35A1Adapter
from .adapters.bp35c2 import BP35C2Adapter

class AdapterFactory:
    """Factory class for creating B-route adapters."""

    _adapters: dict[str, Type[AdapterInterface]] = {
        "BP35A1": BP35A1Adapter,
        "BP35C2": BP35C2Adapter,
    }

    @classmethod
    def create(cls, model: str, **kwargs) -> AdapterInterface:
        """Create an adapter instance.

        Args:
            model: Adapter model name (e.g., "BP35A1", "BP35C2")
            **kwargs: Additional arguments passed to adapter constructor

        Returns:
            AdapterInterface: An instance of the appropriate adapter

        Raises:
            ValueError: If adapter model is not supported
        """
        adapter_class = cls._adapters.get(model.upper())
        if not adapter_class:
            raise ValueError(f"Unsupported adapter model: {model}")

        return adapter_class(**kwargs)

    @classmethod
    def register_adapter(
        cls, model: str, adapter_class: Type[AdapterInterface]
    ) -> None:
        """Register a new adapter type.

        Args:
            model: Adapter model name
            adapter_class: Adapter class implementing AdapterInterface
        """
        cls._adapters[model.upper()] = adapter_class

    @classmethod
    def get_supported_models(cls) -> list[str]:
        """Get list of supported adapter models.

        Returns:
            list[str]: List of supported model names
        """
        return list(cls._adapters.keys())
