"""Analysis-only Jinja environments and a small dbt generic-test grammar."""
from jinja2 import Environment, nodes
from jinja2.ext import Extension


class DbtTestExtension(Extension):
    """Parse dbt's test signature/body as a scoped macro, without running dbt.

    Follows dbt-common's TestExtension grammar. The original tag is retained
    for AST-only callers. This is not a dbt compiler or project validator.
    """
    tags = {"test"}

    def parse(self, parser):
        token = next(parser.stream)
        name = parser.parse_assign_target(name_only=True).name
        node = nodes.Macro(lineno=token.lineno)
        parser.parse_signature(node)
        node.name = "test_" + name
        node.body = parser.parse_statements(("name:endtest",), drop_needle=True)
        node.extractor_source_tag = "test"
        return node


DEFAULT_EXTENSIONS = ("jinja2.ext.i18n", "jinja2.ext.do", "jinja2.ext.loopcontrols")


def create_environment(dialect="auto", *, extensions=(), globals=None, **options):
    """Build an environment for static analysis, never template execution.

    auto accepts Jinja plus dbt generic tests; jinja disables dbt syntax;
    dbt explicitly enables it. Unknown tags remain errors.
    """
    if dialect not in {"auto", "jinja", "dbt"}:
        raise ValueError("dialect must be 'auto', 'jinja', or 'dbt'")
    enabled = list(DEFAULT_EXTENSIONS)
    if dialect in {"auto", "dbt"}:
        enabled.append(DbtTestExtension)
    enabled.extend(extensions)
    env = Environment(extensions=enabled, **options)
    # Declare i18n callables so lowered gettext calls are not external inputs.
    # No rendering or translation is performed.
    env.install_null_translations()
    if globals:
        env.globals.update(globals)
    return env
