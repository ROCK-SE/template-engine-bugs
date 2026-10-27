from jinja2 import nodes

from .metadata.node_maps import NODE_TO_TAG_MAP
from .metadata.tag_defs import JINJA2_BUILTIN_TAGS_INFO, BUILTIN_TAG_NAMES
from .source_elements import source_elements


def extract_tags(parsed_ast, source=None, environment=None):
    """Prefer source constructs over artifacts of extension AST lowering.

    AST-only calls remain supported. Source is needed to recover raw/trans and
    avoid reporting synthetic set/scope/macro tags introduced by extensions.
    """
    ast_types = {}

    def walk(node):
        if isinstance(node, nodes.Stmt):
            name = type(node).__name__
            tag = getattr(node, "extractor_source_tag", NODE_TO_TAG_MAP.get(name))
            if tag:
                ast_types.setdefault(tag, name)
        for child in node.iter_child_nodes():
            walk(child)

    walk(parsed_ast)
    env = environment or getattr(parsed_ast, "environment", None)
    names = source_elements(source, env)[0] if source is not None else ast_types
    tags = {}
    for tag in names:
        entry = {"node_type": ast_types.get(tag, "SourceTag"),
                 "is_builtin": tag in BUILTIN_TAG_NAMES}
        if tag in JINJA2_BUILTIN_TAGS_INFO:
            entry.update(JINJA2_BUILTIN_TAGS_INFO[tag])
        if tag == "test":
            entry.update(origin="dbt", syntax="{% test name(args) %}...{% endtest %}",
                         description="Define a dbt generic data test with local parameters.")
        tags[tag] = entry
    return tags
