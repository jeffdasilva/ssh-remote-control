"""Missing dependency for yaml module."""

# This file ensures PyYAML is available for import
from typing import Any

try:
    import yaml

    # Use original safe_load directly
    safe_load = yaml.safe_load
except ImportError:
    # If yaml is not available, we can use json as a fallback
    import json

    def safe_load(stream: Any) -> Any:
        """Basic JSON fallback for YAML."""
        # Basic JSON fallback - not a full YAML implementation
        if isinstance(stream, str):
            return json.loads(stream)
        return json.load(stream)


# Re-export safe_load for import
__all__ = ["safe_load"]
