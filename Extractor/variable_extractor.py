"""Scope-aware, per-analysis inference of external input structures.

The public schema retains property, __getitem__(), type=Iterable, and loop-target
placeholders. A dynamic subscript uses a distinct __dynamic_getitem__() node.
No template expressions or application functions are executed.
"""
from dataclasses import dataclass
from jinja2 import Environment, nodes

from .metadata.python_stdlib import ALL_PYTHON_MODULES


@dataclass(frozen=True)
class Binding:
    origins: tuple = ()
    # Conditional assignments can leave an external value in scope.
    unbound: bool = False


def _unique_origins(origins):
    result = []
    for origin in origins:
        if all(origin is not other for other in result):
            result.append(origin)
    return tuple(result)


def _property(parent, name):
    return parent.setdefault("property", {}).setdefault(name, {})


def _targets(node):
    if isinstance(node, nodes.Name):
        return [node.name]
    if isinstance(node, (nodes.Tuple, nodes.List)):
        return [name for child in node.items for name in _targets(child)]
    return []


# These filters can preserve a collection or a direct alias. Other filter return
# shapes are deliberately not guessed.
PRESERVING_FILTERS = {
    "default", "d", "list", "sort", "unique", "reverse",
    "select", "reject", "selectattr", "rejectattr",
}


class VariableExtractor:
    def __init__(self, runtime_globals):
        self.model = {}
        self.runtime_globals = set(runtime_globals)
        self.scopes = [{"self": Binding()}]

    def _root(self, name):
        if name not in self.model:
            value = {}
            if name in ALL_PYTHON_MODULES:
                value.update(
                    caveat=f"Variable name '{name}' conflicts with a Python built-in module.",
                    is_conflicting_with_builtin_module=True,
                )
            self.model[name] = value
        return self.model[name]

    def _lookup(self, name, frames=None):
        for frame in reversed(self.scopes if frames is None else frames):
            if name in frame:
                return frame[name]
        return Binding(unbound=True)

    def _name_origins(self, name):
        binding = self._lookup(name)
        origins = list(binding.origins)
        if binding.unbound and name not in self.runtime_globals:
            origins.append(self._root(name))
        return _unique_origins(origins)

    def _origins(self, node):
        """Resolve explicit accesses; never attach a call's return shape to its receiver."""
        if isinstance(node, nodes.Name):
            return self._name_origins(node.name)
        if isinstance(node, nodes.Getattr):
            return tuple(_property(parent, node.attr) for parent in self._origins(node.node))
        if isinstance(node, nodes.Getitem):
            parents = self._origins(node.node)
            if isinstance(node.arg, nodes.Slice):
                return parents
            if isinstance(node.arg, nodes.Const):
                key = node.arg.value
                # Preserve the original schema's treatment of positional indices.
                if type(key) is int:
                    return parents
                return tuple(
                    parent.setdefault("property", {}).setdefault("__getitem__()", {}).setdefault(str(key), {})
                    for parent in parents
                )
            return tuple(_property(parent, "__dynamic_getitem__()") for parent in parents)
        return ()

    def _alias_origins(self, node):
        if isinstance(node, nodes.Filter) and node.name in PRESERVING_FILTERS:
            result = list(self._alias_origins(node.node))
            if node.name in {"default", "d"} and node.args:
                result.extend(self._alias_origins(node.args[0]))
            return _unique_origins(result)
        if isinstance(node, nodes.CondExpr):
            return _unique_origins(
                self._alias_origins(node.expr1) + self._alias_origins(node.expr2)
            )
        return self._origins(node)

    def _iterable_origins(self, node):
        if (isinstance(node, nodes.Call) and isinstance(node.node, nodes.Getattr)
                and node.node.attr in {"items", "keys", "values"}
                and not node.args and not node.kwargs and not node.dyn_args and not node.dyn_kwargs):
            return self._alias_origins(node.node.node)
        return self._alias_origins(node)

    def _access_side_expressions(self, node):
        """Collect all dynamic keys, filter args, and calls inside an access chain."""
        if isinstance(node, nodes.Name):
            return
        if isinstance(node, nodes.Getattr):
            self._access_side_expressions(node.node)
        elif isinstance(node, nodes.Getitem):
            self.expression(node.arg)
            self._access_side_expressions(node.node)
        else:
            self.expression(node)

    def _arguments(self, node):
        for argument in getattr(node, "args", ()):
            self.expression(argument)
        for argument in getattr(node, "kwargs", ()):
            self.expression(argument.value)
        self.expression(getattr(node, "dyn_args", None))
        self.expression(getattr(node, "dyn_kwargs", None))

    def expression(self, node):
        if node is None:
            return
        if isinstance(node, nodes.Name):
            if node.ctx == "load":
                self._name_origins(node.name)
        elif isinstance(node, (nodes.Getattr, nodes.Getitem)):
            self._origins(node)
            self._access_side_expressions(node)
        elif isinstance(node, nodes.Call):
            # A method is not a data field; its receiver and all call arguments
            # are inputs. An external callable name is itself a context input.
            if isinstance(node.node, nodes.Getattr):
                self.expression(node.node.node)
            else:
                self.expression(node.node)
            self._arguments(node)
        elif isinstance(node, (nodes.Filter, nodes.Test)):
            self.expression(node.node)
            self._arguments(node)
        else:
            for child in node.iter_child_nodes():
                self.visit(child)

    def visit(self, node):
        if node is None:
            return
        if isinstance(node, nodes.Expr):
            self.expression(node)
            return
        method = getattr(self, "visit_" + type(node).__name__, None)
        if method:
            method(node)
        else:
            for child in node.iter_child_nodes():
                self.visit(child)

    def body(self, body):
        for node in body:
            self.visit(node)

    def _scoped_body(self, body, bindings=None):
        self.scopes.append(dict(bindings or {}))
        try:
            self.body(body)
        finally:
            self.scopes.pop()

    def _bind_target(self, target, value):
        names = _targets(target)
        if isinstance(target, nodes.Name):
            self.scopes[-1][target.name] = Binding(self._alias_origins(value))
        elif (isinstance(target, (nodes.Tuple, nodes.List))
              and isinstance(value, (nodes.Tuple, nodes.List))
              and len(target.items) == len(value.items)):
            for lhs, rhs in zip(target.items, value.items):
                self._bind_target(lhs, rhs)
        else:
            for name in names:
                self.scopes[-1][name] = Binding()

    def visit_Assign(self, node):
        self.expression(node.node)
        if isinstance(node.target, nodes.NSRef):
            for origin in self._name_origins(node.target.name):
                _property(origin, node.target.attr)
        else:
            self._bind_target(node.target, node.node)

    def visit_AssignBlock(self, node):
        self._scoped_body(node.body)
        self.expression(node.filter)
        for name in _targets(node.target):
            self.scopes[-1][name] = Binding()

    def visit_For(self, node):
        self.expression(node.iter)
        origins = self._iterable_origins(node.iter)
        bindings = {}
        for origin in origins:
            origin["type"] = "Iterable"
        for name in _targets(node.target):
            bindings[name] = Binding(tuple(_property(origin, name) for origin in origins))
        self.scopes.append(bindings)
        try:
            # The filter test can refer to its target and external arguments.
            self.expression(node.test)
            self.scopes[-1]["loop"] = Binding()
            self.body(node.body)
        finally:
            self.scopes.pop()
        # The loop target is not bound in the else branch.
        self._scoped_body(node.else_)

    def visit_If(self, node):
        self.expression(node.test)
        base = self.scopes[-1].copy()
        branches = []

        def branch(body):
            self.scopes[-1] = base.copy()
            self.body(body)
            branches.append(self.scopes[-1])

        try:
            branch(node.body)
            for alternate in node.elif_:
                self.scopes[-1] = base.copy()
                self.expression(alternate.test)
                branch(alternate.body)
            branch(node.else_)  # Missing else represents the unchanged path.
        finally:
            self.scopes[-1] = base
        for name in set().union(*(frame.keys() for frame in branches)):
            prior = self._lookup(name)
            values = [frame.get(name, prior) for frame in branches]
            self.scopes[-1][name] = Binding(
                _unique_origins(origin for value in values for origin in value.origins),
                any(value.unbound for value in values),
            )

    def visit_With(self, node):
        bindings = {}
        # All initializers are evaluated in the outer scope.
        for value in node.values:
            self.expression(value)
        for target, value in zip(node.targets, node.values):
            if isinstance(target, nodes.Name):
                bindings[target.name] = Binding(self._alias_origins(value))
            else:
                for name in _targets(target):
                    bindings[name] = Binding()
        self._scoped_body(node.body, bindings)

    def visit_Macro(self, node):
        self.scopes[-1][node.name] = Binding()
        bindings = {arg.name: Binding() for arg in node.args}
        bindings.update({name: Binding() for name in ("caller", "kwargs", "varargs")})
        self.scopes.append(bindings)
        try:
            for value in node.defaults:
                self.expression(value)
            self.body(node.body)
        finally:
            self.scopes.pop()

    def visit_CallBlock(self, node):
        self.expression(node.call)
        bindings = {arg.name: Binding() for arg in node.args}
        bindings.update({name: Binding() for name in ("caller", "kwargs", "varargs")})
        self.scopes.append(bindings)
        try:
            for value in node.defaults:
                self.expression(value)
            self.body(node.body)
        finally:
            self.scopes.pop()

    def visit_Import(self, node):
        self.expression(node.template)
        self.scopes[-1][node.target] = Binding()

    def visit_FromImport(self, node):
        self.expression(node.template)
        for value in node.names:
            self.scopes[-1][value[1] if isinstance(value, tuple) else value] = Binding()

    def visit_Block(self, node):
        frames = self.scopes
        # Ordinary inherited blocks get template context, not loop/macro locals.
        # Jinja's explicit "scoped" modifier carries the surrounding locals.
        if not node.scoped:
            self.scopes = [frames[0]]
        try:
            self._scoped_body(node.body, {"super": Binding()})
        finally:
            self.scopes = frames

    def visit_Scope(self, node):
        self._scoped_body(node.body)

    def visit_OverlayScope(self, node):
        self.expression(node.context)
        self._scoped_body(node.body)

    def visit_FilterBlock(self, node):
        self.expression(node.filter)
        self._scoped_body(node.body)


def extract_variables(parsed_ast, runtime_globals=(), input_names=()):
    """Return external input structure using fresh state for every invocation.

    Only actual Jinja environment globals (and explicitly supplied names) are
    excluded. Macro arguments, imports, assignments, loop targets, and with/call
    bindings are local. Conditional assignments retain possible external inputs.
    """
    context = parsed_ast[0] if isinstance(parsed_ast, list) and parsed_ast else parsed_ast
    environment = getattr(context, "environment", None)
    globals_ = (set((environment or Environment()).globals) | set(runtime_globals or ())) - set(input_names or ())
    extractor = VariableExtractor(globals_)
    if isinstance(parsed_ast, list):
        extractor.body(parsed_ast)
    else:
        extractor.visit(parsed_ast)
    return extractor.model
