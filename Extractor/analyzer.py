from .environment import create_environment
from .variable_extractor import extract_variables
from .tag_extractor import extract_tags
from .filter_extractor import extract_filters

EXTRACTOR_VERSION = "0.2.0"


def analyze_template(template: str, *, dialect="auto", environment=None,
                     extensions=(), runtime_globals=(), input_names=(), name=None):
    """
    Analyze Jinja without rendering it or executing application functions.
    Args:
        template: Content of the Jinja2 template
    Returns:
        dict: Analysis result containing variables, tags, and filters.

    The original one-argument API is preserved. A supplied Environment is used
    without mutation; otherwise the configured analysis environment is created.
    runtime_globals declares extra application-provided global names. input_names
    explicitly identifies context inputs that shadow an environment global.
    """
    
    if environment is not None and extensions:
        raise ValueError("configure extensions on the supplied environment")
    env = environment if environment is not None else create_environment(dialect, extensions=extensions)
    # Parse the template into an AST (Abstract Syntax Tree)
    parsed = env.parse(template, name=name)

    return {
        "variables": extract_variables(parsed, runtime_globals=runtime_globals, input_names=input_names),
        "tag": extract_tags(parsed, source=template, environment=env),
        "filter": extract_filters(parsed, source=template, environment=env),
    }

