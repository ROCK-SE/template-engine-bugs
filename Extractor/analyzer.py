from jinja2 import Environment
from variable_extractor import extract_variables
from tag_extractor import extract_tags
from filter_extractor import extract_filters

def analyze_template(template: str):
    """
    Analyze a Jinja2 template and extract variables, tags, and filters
    Args:
        template: Content of the Jinja2 template
    Returns:
        dict: Analysis result containing variables, tags, and filters
    """
    
    # Create a Jinja2 environment
    env = Environment()
    # Parse the template into an AST (Abstract Syntax Tree)
    parsed = env.parse(template)

    return {
        "variables": extract_variables(parsed),
        "tag": extract_tags(parsed),
        "filter": extract_filters(parsed),
    }

