from jinja2 import Environment, FileSystemLoader
import os

# jinja2 setup for the json schema templates
# loading the environment
file_path = os.path.abspath(os.path.dirname(__file__))
env = Environment(loader = FileSystemLoader(f"{file_path}/../json_schema_templates"))
json_control_mapping =  dict.fromkeys(range(32)) # the json control chars

def render_jinja(template_name, **kwargs):
    """
    Renders the json schema template with the values from the dataframe row
    """
    # loading the template
    template = env.get_template(template_name)

    # rendering the template and storing the resultant text in variable output
    output = template.render(**kwargs).translate(json_control_mapping)
    
    return output

def get_json_schema_template_name(cls_obj):
    """
    Gets the correct json schema template name for the given class object.
    """
    cls_name = cls_obj.__name__
    
    if hasattr(cls_obj, f"_{cls_name}__json_schema_template_name"):
        template_name = getattr(cls_obj, f"_{cls_name}__json_schema_template_name").default
    else:
        template_name = f"{cls_name}.jinja"
    
    return template_name

def highlight_is_valid(val):
    """
    Returns CSS based on value.
    """
    if isinstance(val, bool):
        color = 'darkgreen' if bool(val) else 'darkred'
    else:
        color = 'darkgreen' if val.lower() == 'true' else 'darkred'
    return 'background-color: {}'.format(color)