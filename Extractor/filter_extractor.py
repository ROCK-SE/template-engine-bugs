from jinja2 import Environment, nodes

from .metadata.filter_defs import JINJA2_BUILTIN_FILTERS_INFO
from .source_elements import source_elements


def extract_filters(parsed_ast, source=None, environment=None):
    """Report explicit filters, including blocks, without extension-generated ones."""
    if source is not None:
        names = source_elements(source, environment or getattr(parsed_ast, "environment", None))[1]
    else:
        candidates = ([parsed_ast] if isinstance(parsed_ast, nodes.Filter) else [])
        candidates.extend(parsed_ast.find_all(nodes.Filter))
        names = dict.fromkeys(node.name for node in candidates)
    builtin_names = Environment().filters
    filters = {}
    for name in names:
        entry = {"is_builtin": name in builtin_names}
        if name in JINJA2_BUILTIN_FILTERS_INFO:
            entry.update(JINJA2_BUILTIN_FILTERS_INFO[name])
        filters[name] = entry
    return filters
