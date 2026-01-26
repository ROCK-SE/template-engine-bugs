from jinja2 import nodes
from metadata.filter_defs import (
    JINJA2_BUILTIN_FILTERS_INFO,
    BUILTIN_FILTER_NAMES,
)

def extract_filters(parsed_ast):
    """
    Extract filters used in the Jinja2 template from the parsed AST
    Args:
        parsed_ast: Parsed AST of the Jinja2 template
    Returns:
        dict: Extracted filters with details
    """
    filters = {}

    def walk(node):
        if isinstance(node, nodes.Filter):
            name = node.name
            if name not in filters:
                entry = {
                    "is_builtin": name in BUILTIN_FILTER_NAMES,
                }
                # Add built-in filter details if available
                if name in JINJA2_BUILTIN_FILTERS_INFO:
                    entry.update(JINJA2_BUILTIN_FILTERS_INFO[name])
                filters[name] = entry

        # Recursively process child nodes
        for _, child in node.iter_fields():
            if isinstance(child, list):
                for c in child:
                    if isinstance(c, nodes.Node):
                        walk(c)
            elif isinstance(child, nodes.Node):
                walk(child)

    walk(parsed_ast)
    return filters