"""Static extraction of Jinja inputs, structures, tags, and filters."""
from .analyzer import EXTRACTOR_VERSION, analyze_template
from .environment import create_environment

__version__ = EXTRACTOR_VERSION
__all__ = ["analyze_template", "create_environment", "__version__"]
