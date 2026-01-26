# Detailed information for built-in Jinja2 tags (including description and caveat)

JINJA2_BUILTIN_TAGS_INFO = {
    "for": {
        "syntax": "{% for target in iterable %}...{% else %}...{% endfor %}",
        "description": "Iterate over an iterable (such as a list, tuple, or dict) and render the block for each item.",
        "caveat": "Loop variables are only available inside the loop body."
    },
    "if": {
        "syntax": "{% if condition %}...{% elif condition %}...{% else %}...{% endif %}",
        "description": "Conditionally render blocks based on the truth value of expressions.",
        "caveat": "Conditions follow Python truthiness rules: empty sequences, empty strings, None, and 0 evaluate to False."
    },
    "set": {
        "syntax": "{% set name = value %} | {% set name %}...{% endset %}",
        "description": "Assign a value to a variable within the template. Supports both single-line assignment and block assignment.",
        "caveat": "Assignments are scoped to the current context. Block assignments capture rendered text, not expressions."
    },
    "block": {
        "syntax": "{% block name scoped %}...{% endblock %}",
        "description": "Define a named block that can be overridden by child templates during template inheritance.",
        "caveat": "Block names must be unique within a template."
    },
    "extends": {
        "syntax": "{% extends template %}",
        "description": "Declare template inheritance from a parent template. The child template may override blocks defined by the parent.",
        "caveat": "The extends tag must appear before any output, except whitespace or comments."
    },
    "include": {
        "syntax": "{% include template ignore missing with context %}",
        "description": "Include and render another template within the current one. Supports optional context isolation and missing-template handling.",
        "caveat": "Included templates share the current context by default."
    },
    "import": {
        "syntax": "{% import template as name with context %}",
        "description": "Import another template as a module to access its macros and exported variables.",
        "caveat": "Imported templates use their own namespace."
    },
    "from": {
        "syntax": "{% from template import name1, name2 as alias with context %}",
        "description": "Import specific macros or variables from another template into the current namespace.",
        "caveat": "Only explicitly imported names are available. Aliases should not shadow existing variables."
    },
    "macro": {
        "syntax": "{% macro name(args, kwargs=default) %}...{% endmacro %}",
        "description": "Define a reusable template function that can accept arguments and return rendered output.",
        "caveat": "Macros perform no type checking. Variables defined inside a macro are local. Recursive macros may cause stack overflows."
    },
    "call": {
        "syntax": "{% call(args) macro_name() %}...{% endcall %}",
        "description": "Invoke a macro and pass a block of template content as a callable via the special caller() function.",
        "caveat": "The macro must explicitly call caller() to render the block. Call blocks introduce additional rendering overhead."
    },
    "filter": {
        "syntax": "{% filter filter_name %}...{% endfilter %}",
        "description": "Apply a filter to the entire contents of a block.",
        "caveat": "All content inside the block, including whitespace and newlines, is filtered. Not all filters are suitable for block usage."
    },
    "with": {
        "syntax": "{% with name = value %}...{% endwith %}",
        "description": "Create a new inner scope with temporary variables.",
        "caveat": "Variables defined inside the with block do not exist outside it. Outer variables with the same name are temporarily shadowed."
    },
    "do": {
        "syntax": "{% do expression %}",
        "description": "Evaluate an expression for its side effects without rendering its result.",
        "caveat": "The result is discarded. To display a value, use {{ }} instead."
    },
    "autoescape": {
        "syntax": "{% autoescape true|false %}...{% endautoescape %}",
        "description": "Enable or disable automatic HTML escaping within a block.",
        "caveat": "Disabling autoescaping can introduce XSS vulnerabilities. Nested autoescape blocks may be hard to reason about."
    },
    "raw": {
        "syntax": "{% raw %}...{% endraw %}",
        "description": "Render content verbatim without processing Jinja syntax.",
        "caveat": "Jinja syntax inside raw blocks is ignored entirely. Raw blocks cannot be nested."
    },
    "scope": {
        "syntax": "{% scope %}...{% endscope %}",
        "description": "Create an explicit isolated scope for variable assignments.",
        "caveat": "Variables defined inside the scope block are not accessible outside. This tag may be unavailable in older Jinja versions."
    }
}

BUILTIN_TAG_NAMES = set(JINJA2_BUILTIN_TAGS_INFO.keys())
