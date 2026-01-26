from jinja2 import nodes
from metadata.node_maps import NODE_TO_TAG_MAP
from metadata.tag_defs import JINJA2_BUILTIN_TAGS_INFO, BUILTIN_TAG_NAMES

def extract_tags(parsed_ast):
    """
    Extract tags used in the Jinja2 template from the parsed AST
    Args:
        parsed_ast: Parsed AST of the Jinja2 template
    Returns:
        dict: Extracted tags with details
    """
    tags = {}

    def walk(node):
        # Get node type name (e.g., "For" for For statement nodes)
        if isinstance(node, nodes.Stmt):
            name = type(node).__name__
            if name in NODE_TO_TAG_MAP:
                tag = NODE_TO_TAG_MAP[name]
                if tag not in tags:
                    entry = {
                        "node_type": name,
                        "is_builtin": tag in BUILTIN_TAG_NAMES,
                    }
                    # Add built-in tag details if available
                    if tag in JINJA2_BUILTIN_TAGS_INFO:
                        entry.update(JINJA2_BUILTIN_TAGS_INFO[tag])
                    tags[tag] = entry

        # Recursively process child nodes
        for _, child in node.iter_fields():
            if isinstance(child, list):
                for c in child:
                    if isinstance(c, nodes.Node):
                        walk(c)
            elif isinstance(child, nodes.Node):
                walk(child)

    walk(parsed_ast)
    return tags
