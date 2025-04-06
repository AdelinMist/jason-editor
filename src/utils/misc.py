import json
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
import streamlit as st
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

@st.cache_data
def convert_to_json(df, cls_obj):
    """
    Converts the dataframe to a json object.
    Also replaces the string 'None' values with empty strings.
    This functions result is cached.
    """
    df_to_convert = df.copy(deep=True).replace('None', '').drop(columns=['is_valid'])
    
    template_name = get_json_schema_template_name(cls_obj)
    
    json_list = []
    for row in df_to_convert.to_dict('records'):
        try:
            # we also remove json control chars from the result of templating!
            rendered_schema = render_jinja(template_name, **row)
            json_to_add = json.loads(rendered_schema)
        except TemplateNotFound as err:
            json_to_add = row
            
        json_list.append(json_to_add)

    
    return json.dumps(json_list)

def highlight_is_valid(val):
    """
    Returns CSS based on value.
    """
    if isinstance(val, bool):
        color = 'darkgreen' if bool(val) else 'darkred'
    else:
        color = 'darkgreen' if val.lower() == 'true' else 'darkred'
    return 'background-color: {}'.format(color)