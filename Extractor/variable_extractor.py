import builtins
from jinja2 import nodes, Environment
from metadata.python_stdlib import ALL_PYTHON_MODULES

# ==========================================
# Global Storage
# ==========================================
# Stores the inferred structure of variables found in the template.
variables_model = {}

# Tracks temporary variables defined in loops (e.g., 'item' in 'for item in items').
# These should not be treated as root variables.
loop_variables = set()

# Tracks macro names to avoid treating them as variables.
defined_macros = set()

# ==========================================
# Dynamic Whitelist & Helpers
# ==========================================

def get_runtime_builtins():
    """
    Generates a set of safe built-in names (Python built-ins + Jinja2 globals).
    These names are excluded from variable extraction.
    """
    py_builtins = set(dir(builtins))
    jinja_env = Environment()
    jinja_globals = set(jinja_env.globals.keys())
    final_set = py_builtins | jinja_globals
    
    # Exceptions: We want to treat these specific built-ins as variables
    # if they appear in the template, or at least not strictly ignore them
    # if they are shadowed.
    EXCEPTIONS = {'id', 'type', 'list', 'dict', 'filter', 'map', 'min', 'max', 'sum'}
    return final_set - EXCEPTIONS

RUNTIME_BUILTINS = get_runtime_builtins()

def _ensure_structure(container, key):
    """Ensures a dictionary key exists and returns the value (defaulting to empty dict)."""
    if key not in container:
        container[key] = {}
    return container[key]

def _ensure_property_path(container, prop_name):
    """Ensures the 'property' -> 'prop_name' path exists in the structure."""
    props = _ensure_structure(container, "property")
    return _ensure_structure(props, prop_name)

def _ensure_getitem_path(container, key_name):
    """Ensures the 'property' -> '__getitem__()' -> 'key_name' path exists."""
    props = _ensure_structure(container, "property")
    getitem_method = _ensure_structure(props, "__getitem__()")
    return _ensure_structure(getitem_method, key_name)

def _get_loop_targets(target_node):
    """
    Extracts variable names from a loop target.
    Handles single variables (for x in ...) and unpacking (for x, y in ...).
    """
    names = []
    if isinstance(target_node, nodes.Name):
        names.append(target_node.name)
    elif isinstance(target_node, (nodes.Tuple, nodes.List)):
        for item in target_node.items:
            if isinstance(item, nodes.Name):
                names.append(item.name)
    return names

def unwrap_filters(node):
    """Recursively unwraps Jinja2 filters to find the underlying variable node."""
    current = node
    while isinstance(current, nodes.Filter):
        current = current.node
    return current

def unwrap_dict_methods(node):
    """
    Unwraps .items(), .keys(), or .values() calls on a dictionary 
    to get the underlying dictionary variable.
    """
    if isinstance(node, nodes.Call):
        if isinstance(node.node, nodes.Getattr):
            if node.node.attr in ('items', 'keys', 'values'):
                return node.node.node
    return node

# ==========================================
# Variable Logic & Chain Resolution
# ==========================================

def ensure_root_tree(name):
    """
    Ensures a root-level variable exists in the global variables_model.
    Checks for conflicts with Python standard library modules.
    """
    if name not in variables_model:
        variables_model[name] = {}
        if name in ALL_PYTHON_MODULES:
            variables_model[name]["caveat"] = f"Variable name '{name}' conflicts with a Python built-in module."
            variables_model[name]["is_conflicting_with_builtin_module"] = True
    return variables_model[name]

def resolve_chain(node):
    """
    Traverses an AST node (Getattr/Getitem/Name) bottom-up to build a linear access chain.
    
    Returns:
        tuple: (chain, temp_items)
        - chain: List of strings for simple path analysis (e.g., ['user', 'name']).
        - temp_items: List of (type, value) tuples describing the access method.
    """
    current_node = node
    temp_items = []
    
    while True:
        if isinstance(current_node, nodes.Getattr):
            # Case: obj.attr
            temp_items.append(('attr', current_node.attr))
            current_node = current_node.node
        elif isinstance(current_node, nodes.Getitem):
            # Case: obj['key']
            if isinstance(current_node.arg, nodes.Const):
                temp_items.append(('getitem', {'key': current_node.arg.value, 'is_const': True}))
            elif isinstance(current_node.arg, nodes.Name):
                key_name = current_node.arg.name
                temp_items.append(('getitem', {'key': key_name, 'is_const': False}))
            else:
                temp_items.append(('getitem', {'key': '???', 'is_const': False}))
            current_node = current_node.node
        elif isinstance(current_node, nodes.Name):
            # Case: root variable
            temp_items.append(('name', current_node.name))
            break
        elif hasattr(current_node, 'node'):
            # Traverse through other nodes (like Call, Filter, etc.)
            current_node = current_node.node
        else:
            break
            
    temp_items.reverse()
    
    chain = []
    for item_type, item_value in temp_items:
        if item_type in ('name', 'attr'):
            chain.append(item_value)
            
    return (chain if chain else None), temp_items

def process_remaining_chain(parent_obj, chain_with_type):
    """
    Recursively applies the remaining parts of an access chain to the model structure.
    Used principally when resolving loop variables back to their iterable source.
    """
    if not chain_with_type:
        return
        
    current = parent_obj
    for item_type, item_value in chain_with_type:
        if item_type == 'attr':
            current = _ensure_property_path(current, item_value)
        elif item_type == 'getitem':
            getitem_info = item_value
            if getitem_info['is_const']:
                key = getitem_info['key']
                
                # --- Modification 1: Filter Integer Constants ---
                # We ignore integer keys (e.g., list[0]) as they imply array access,
                # not a specific named property in the schema.
                if isinstance(key, int):
                    continue
                # ------------------------------------------------
                
                current = _ensure_getitem_path(current, key)

def add_property_recursive_tree(chain, chain_with_type, root=None, start_index=0):
    """
    Recursively builds the variable model tree based on an access chain.
    """
    if not chain or not chain_with_type:
        return
        
    name = chain[0]
    
    # Skip if the name is a builtin, a loop variable, or a macro.
    if name in RUNTIME_BUILTINS or name in loop_variables or name in defined_macros:
        return
    
    # Determine the current object context
    if root is None:
        current = ensure_root_tree(name)
    else:
        current = _ensure_property_path(root, name)
    
    # Locate the current segment in the detailed chain (chain_with_type)
    current_index = start_index
    for i in range(start_index, len(chain_with_type)):
        item_type, item_value = chain_with_type[i]
        if item_type in ('name', 'attr') and item_value == name:
            current_index = i
            break
    
    next_index = current_index + 1
    
    # Process the next segment if it exists
    if next_index < len(chain_with_type):
        next_type, next_value = chain_with_type[next_index]
        
        if next_type == 'getitem':
            getitem_info = next_value
            if getitem_info['is_const']:
                key = getitem_info['key']
                
                # --- Modification 2: Filter Integer Constants ---
                if isinstance(key, int):
                    # If it's an integer index, we skip recording it as a specific property key.
                    # We continue processing the rest of the chain on the *current* object.
                    if next_index + 1 < len(chain_with_type):
                         process_remaining_chain(current, chain_with_type[next_index + 1:])
                    return
                # ------------------------------------------------
                
                key_obj = _ensure_getitem_path(current, key)
                if next_index + 1 < len(chain_with_type):
                    process_remaining_chain(key_obj, chain_with_type[next_index + 1:])
            return 
    
    # Continue recursion for standard attributes
    if len(chain) > 1:
        add_property_recursive_tree(chain[1:], chain_with_type, current, start_index=next_index)

# ==========================================
# Extraction Logic
# ==========================================

def extract_variables_from_expr(expr_node, context="expression"):
    """
    Analyzes a single expression node to find variable references.
    """
    # Recursively check children nodes first
    if _recurse_generic_nodes(expr_node, extract_variables_from_expr, context):
        return

    if isinstance(expr_node, nodes.Name):
        if (expr_node.name not in loop_variables and 
            expr_node.name not in defined_macros and 
            expr_node.name not in RUNTIME_BUILTINS):
            
            chain = [expr_node.name]
            chain_with_type = [('name', expr_node.name)]
            add_property_recursive_tree(chain, chain_with_type)
            
    elif isinstance(expr_node, (nodes.Getattr, nodes.Getitem)):
        # If the key is dynamic (e.g. dict[var]), analyze the variable used as key
        if isinstance(expr_node, nodes.Getitem) and not isinstance(expr_node.arg, nodes.Const):
            extract_variables_from_expr(expr_node.arg, "dynamic_key")
            
        chain, chain_with_type = resolve_chain(expr_node)
        if chain:
            add_property_recursive_tree(chain, chain_with_type)

def mark_variable_as_iterable_tree(iter_node, container_context=None):
    """
    Identifies the collection being iterated over in a For-loop and marks it as 'Iterable'.
    Refers back to the global variables_model or a local container context (nested loops).
    """
    target_obj = None
    
    if isinstance(iter_node, nodes.Name):
        var_name = iter_node.name
        if container_context and var_name in container_context:
            target_obj = container_context[var_name]
        elif (var_name not in loop_variables and 
              var_name not in defined_macros and 
              var_name not in RUNTIME_BUILTINS):
            target_obj = ensure_root_tree(var_name)
                
    elif isinstance(iter_node, (nodes.Getattr, nodes.Getitem)):
        chain, _ = resolve_chain(iter_node)
        if chain and len(chain) > 0:
            root_name = chain[0]
            
            # Resolve root object
            if container_context and root_name in container_context:
                current = container_context[root_name]
            elif (root_name not in loop_variables and 
                  root_name not in defined_macros and 
                  root_name not in RUNTIME_BUILTINS):
                current = ensure_root_tree(root_name)
            else:
                return None

            # Traverse path to the iterable property
            for i in range(1, len(chain)):
                current = _ensure_property_path(current, chain[i])
            target_obj = current

    if target_obj is not None:
        target_obj["type"] = "Iterable"
        return target_obj
    return None

def extract_loop_var_properties_tree(expr_node, loop_var_names, loop_var_container):
    """
    Analyzes expressions *inside* a loop to map usage of loop variables 
    back to the structure of the iterable they came from.
    
    Example: In `for item in items`, seeing `item.id` adds `id` property to `items`.
    """
    callback = lambda n, ctx: extract_loop_var_properties_tree(n, loop_var_names, loop_var_container)
    
    # Handle method calls (e.g. user.get_name())
    if isinstance(expr_node, nodes.Call):
        if isinstance(expr_node.node, nodes.Getattr):
            callback(expr_node.node.node, None) 
        for arg in expr_node.args: callback(arg, None)
        for kwarg in expr_node.kwargs: callback(kwarg.value, None)
        return
    
    if _recurse_generic_nodes(expr_node, callback):
        return

    # Handle direct variable access
    if isinstance(expr_node, nodes.Name):
        var_name = expr_node.name
        if (var_name not in loop_var_names and 
            var_name not in defined_macros and 
            var_name not in RUNTIME_BUILTINS):
            extract_variables_from_expr(expr_node, "loop_body_independent_var")
        return

    # Handle attribute or item access (e.g., item.prop)
    elif isinstance(expr_node, (nodes.Getattr, nodes.Getitem)):
        if isinstance(expr_node, nodes.Getitem) and not isinstance(expr_node.arg, nodes.Const):
             extract_variables_from_expr(expr_node.arg, "loop_dynamic_key")

        chain, chain_with_type = resolve_chain(expr_node)
        
        # If the chain starts with a loop variable, map it back to the container
        if chain and chain[0] in loop_var_names:
            loop_var_name = chain[0]
            element_obj = loop_var_container.get(loop_var_name)
            if element_obj is None:
                return
            
            # Find where the loop variable appears in the chain
            loop_var_index = -1
            for i, (item_type, item_value) in enumerate(chain_with_type):
                if item_type == 'name' and item_value == loop_var_name:
                    loop_var_index = i
                    break
            
            # Apply subsequent properties to the container's element structure
            if loop_var_index >= 0:
                remaining_chain_with_type = chain_with_type[loop_var_index + 1:]
                process_remaining_chain(element_obj, remaining_chain_with_type)
        else:
            # It's an external variable used inside the loop
            extract_variables_from_expr(expr_node, "loop_body_external_var")

def extract_model_with_loop_context_tree(node, loop_target, loop_var_container, loop_var_names=None):
    """
    Traverses nodes within a loop body, maintaining context of loop variables.
    """
    if loop_var_names is None:
        loop_var_names = _get_loop_targets(loop_target)
    
    if isinstance(node, nodes.Output):
        for exp in node.nodes:
            extract_loop_var_properties_tree(exp, loop_var_names, loop_var_container)
            
    elif isinstance(node, nodes.If):
        extract_loop_var_properties_tree(node.test, loop_var_names, loop_var_container)
        for n in node.body:
            extract_model_with_loop_context_tree(n, loop_target, loop_var_container, loop_var_names)
        for elif_node in node.elif_:
            extract_loop_var_properties_tree(elif_node.test, loop_var_names, loop_var_container)
            for n in elif_node.body:
                extract_model_with_loop_context_tree(n, loop_target, loop_var_container, loop_var_names)
        if node.else_:
            for n in node.else_:
                extract_model_with_loop_context_tree(n, loop_target, loop_var_container, loop_var_names)
    
    elif isinstance(node, nodes.For):
        # Nested loop handling
        actual_iter = unwrap_dict_methods(unwrap_filters(node.iter))
        target_obj = mark_variable_as_iterable_tree(actual_iter, loop_var_container)
        
        added_vars = _get_loop_targets(node.target)
        new_loop_vars = loop_var_names + added_vars
        inner_container = loop_var_container.copy()
        
        # Initialize properties for the new nested loop variables
        if target_obj:
            props = _ensure_structure(target_obj, "property")
            for nv in added_vars:
                if nv not in props:
                    props[nv] = {}
                inner_container[nv] = props[nv]

        # Register nested loop vars to avoid global pollution
        for v in added_vars:
            loop_variables.add(v)
        try:
            for body_node in node.body:
                extract_model_with_loop_context_tree(body_node, node.target, inner_container, new_loop_vars)
        finally:
            for v in added_vars:
                if v in loop_variables:
                    loop_variables.remove(v)

    elif isinstance(node, nodes.Assign):
        extract_loop_var_properties_tree(node.node, loop_var_names, loop_var_container)
        # Track assignments within loops (local vars)
        if isinstance(node.target, nodes.Name):
            target_name = node.target.name
            if target_name not in loop_var_names:
                loop_var_names.append(target_name)
                loop_variables.add(target_name)
                
    elif isinstance(node, (nodes.Block, nodes.Scope, nodes.OverlayScope, nodes.With)):
        for n in node.body:
            extract_model_with_loop_context_tree(n, loop_target, loop_var_container, loop_var_names)
    else:
        # Fallback recursion for other node types
        for _, child in node.iter_fields():
            if isinstance(child, list):
                for c in child:
                    if isinstance(c, nodes.Node):
                        extract_model_with_loop_context_tree(c, loop_target, loop_var_container, loop_var_names)
            elif isinstance(child, nodes.Node):
                extract_model_with_loop_context_tree(child, loop_target, loop_var_container, loop_var_names)

def _recurse_generic_nodes(node, callback, context=None):
    """
    Helper to traverse common generic node types (operators, calls, lists, dicts).
    Returns True if the node was handled, False otherwise.
    """
    if node is None: return True
    
    # Logic/Unary operators
    if isinstance(node, (nodes.Filter, nodes.Test, nodes.Not, nodes.Neg, nodes.Pos)):
        callback(node.node, context)
        if hasattr(node, 'args'):
            for arg in node.args: callback(arg, context)
        if hasattr(node, 'kwargs'):
            for kwarg in node.kwargs: callback(kwarg.value, context)
        return True
        
    # Comparison
    if isinstance(node, nodes.Compare):
        callback(node.expr, context)
        for op in node.ops: callback(op.expr, context)
        return True
        
    # Binary operators
    if isinstance(node, (nodes.Add, nodes.Sub, nodes.Mul, nodes.Div, nodes.FloorDiv, nodes.Mod, nodes.Pow, nodes.And, nodes.Or)):
        callback(node.left, context)
        callback(node.right, context)
        return True
        
    # Concatenation
    if isinstance(node, nodes.Concat):
        for child in node.nodes: callback(child, context)
        return True
        
    # Function calls
    if isinstance(node, nodes.Call):
        if isinstance(node.node, nodes.Getattr):
             callback(node.node.node, context)
        for arg in node.args:
             callback(arg, f"{context}.arg" if context else None)
        for kwarg in node.kwargs:
             callback(kwarg.value, f"{context}.kwarg" if context else None)
        return True
        
    # Collections
    if isinstance(node, (nodes.List, nodes.Tuple)):
        for item in node.items: callback(item, context)
        return True
    if isinstance(node, nodes.Dict):
        for item in node.items:
            callback(item.key, context)
            callback(item.value, context)
        return True
        
    # Conditionals/Slice
    if isinstance(node, nodes.CondExpr):
        callback(node.test, f"{context}.condition" if context else None)
        callback(node.expr1, f"{context}.then" if context else None)
        callback(node.expr2, f"{context}.else" if context else None)
        return True
    if isinstance(node, nodes.Slice):
        callback(node.start, context)
        callback(node.stop, context)
        callback(node.step, context)
        return True
        
    return False

def extract_model_tree(node):
    """
    Main recursive function to traverse the AST and populate the variables model.
    """
    # Handle Macros (define scope to avoid variable pollution)
    if isinstance(node, nodes.Macro):
        defined_macros.add(node.name)
        macro_args = [arg.name for arg in node.args]
        for arg in macro_args:
            loop_variables.add(arg)
        try:
            for n in node.body:
                extract_model_tree(n)
        finally:
            for arg in macro_args:
                if arg in loop_variables:
                    loop_variables.remove(arg)
        return

    # Handle Loops
    if isinstance(node, nodes.For):
        actual_iter = unwrap_dict_methods(unwrap_filters(node.iter))
        target_obj = mark_variable_as_iterable_tree(actual_iter)
        
        loop_var_names = _get_loop_targets(node.target)
        loop_var_container = {}
        
        # If the iterable is known, prepare the structure for loop variables
        if target_obj:
            props = _ensure_structure(target_obj, "property")
            for lv_name in loop_var_names:
                if lv_name not in props:
                    props[lv_name] = {}
                loop_var_container[lv_name] = props[lv_name]
        
        # Add loop vars to exclusion list for global extraction
        for name in loop_var_names:
            loop_variables.add(name)
        try:
            for n in node.body:
                extract_model_with_loop_context_tree(n, node.target, loop_var_container, loop_var_names)
        finally:
            for v in loop_var_names:
                if v in loop_variables:
                    loop_variables.remove(v)

    # Handle Simple Nodes
    elif isinstance(node, nodes.Output):
        for exp in node.nodes:
            extract_variables_from_expr(exp, "output")
    elif isinstance(node, nodes.If):
        extract_variables_from_expr(node.test, "if_condition")
        for n in node.body:
            extract_model_tree(n)
        for elif_node in node.elif_:
            extract_variables_from_expr(elif_node.test, "elif_condition")
            for n in elif_node.body:
                extract_model_tree(n)
        if node.else_:
            for n in node.else_:
                extract_model_tree(n)
    elif isinstance(node, (nodes.Block, nodes.Scope, nodes.OverlayScope, nodes.With)):
        for n in node.body:
            extract_model_tree(n)
    elif isinstance(node, nodes.Assign):
        extract_variables_from_expr(node.node, "assignment")
    else:
        # Generic traversal
        for _, child in node.iter_fields():
            if isinstance(child, list):
                for c in child:
                    if isinstance(c, nodes.Node):
                        extract_model_tree(c)
            elif isinstance(child, nodes.Node):
                extract_model_tree(child)

def clean_empty_properties_tree(obj):
    """
    Recursively cleans up empty 'property' dictionaries from the model
    to ensure the output is concise.
    """
    if isinstance(obj, dict):
        cleaned = {}
        for key, value in obj.items():
            if key == "property" and isinstance(value, dict):
                if len(value) == 0:
                    continue 
                else:
                    cleaned_properties = {}
                    for prop_name, prop_value in value.items():
                        cleaned_prop = clean_empty_properties_tree(prop_value)
                        cleaned_properties[prop_name] = cleaned_prop
                    cleaned[key] = cleaned_properties
            else:
                cleaned[key] = clean_empty_properties_tree(value)
        return cleaned
    else:
        return obj

def extract_variables(parsed_ast):
    """
    Public Entry Point: Analyzes a parsed Jinja2 AST and returns the inferred variable model.
    """
    variables_model.clear()
    loop_variables.clear()
    defined_macros.clear()
    
    if isinstance(parsed_ast, list):
        for node in parsed_ast:
            extract_model_tree(node)
    else:
        extract_model_tree(parsed_ast)
        
    return clean_empty_properties_tree(variables_model)