"""Read source-level tags and filters with Jinja's lexer, not regular expressions."""
from jinja2 import Environment


def source_elements(source, environment=None):
    """Return unique opening tags and explicit filters in source order.

    The lexer distinguishes strings, comments, raw text, custom delimiters,
    and whitespace control. Closing/branch tags use their enclosing construct.
    """
    env = environment or Environment()
    tokens = [t for t in env.lex(source) if t[1] != "whitespace"]
    extension_tags = {tag for extension in env.extensions.values() for tag in extension.tags}
    tags, filters = {}, {}
    in_expression = False

    def filter_name(index):
        if index >= len(tokens) or tokens[index][1] != "name":
            return
        name = tokens[index][2]
        index += 1
        while (index + 1 < len(tokens) and tokens[index][1:] == ("operator", ".")
               and tokens[index + 1][1] == "name"):
            name += "." + tokens[index + 1][2]
            index += 2
        filters.setdefault(name, None)

    for i, (line, kind, value) in enumerate(tokens):
        if kind == "raw_begin":
            tags.setdefault("raw", line)
        elif kind in {"block_begin", "linestatement_begin"}:
            in_expression = True
            if i + 1 < len(tokens) and tokens[i + 1][1] == "name":
                name = tokens[i + 1][2]
                if ((not name.startswith("end") or name in extension_tags)
                        and name not in {"else", "elif", "pluralize"}):
                    tags.setdefault(name, line)
                if name == "filter":
                    filter_name(i + 2)
        elif kind == "variable_begin":
            in_expression = True
        elif kind in {"block_end", "linestatement_end", "variable_end"}:
            in_expression = False
        elif in_expression and kind == "operator" and value == "|":
            filter_name(i + 1)
    return tags, list(filters)
