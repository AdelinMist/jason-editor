import streamlit as st
import pandas as pd
import enum
import re
import json
import os
from pydantic import BaseModel, ValidationError
from typing import List
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from mongo_db import insert_request

# jinja2 setup for the json schema templates
# loading the environment
file_path = os.path.abspath(os.path.dirname(__file__))
env = Environment(loader = FileSystemLoader(f"{file_path}/../../json_schema_templates"))

def highlight_is_valid(val):
    """
    Returns CSS based on value.
    """
    if isinstance(val, bool):
        color = 'green' if bool(val) else 'red'
    else:
        color = 'green' if val.lower() == 'true' else 'red'
    return 'background-color: {}'.format(color)

def validate_df(df, validation_cls, error_df_name):
    """
    Runs a pydantic validation on the dataframe passed.
    Recreates the error dataframe based on current validation errors.
    Sets the 'is_valid' column on the dataframe based on validation results.
    """
    st.session_state[error_df_name] = st.session_state[error_df_name].iloc[0:0]
    ValidationClass = validation_cls
    # Wrap the data_schema into a helper class for validation
    class ValidationWrap(BaseModel):
        df_dict: List[ValidationClass]
        
    df = df.assign(is_valid=True)
    
    try:
        df_dict = df.loc[:, df.columns != 'is_valid'].to_dict(orient="records")
        ValidationWrap(df_dict=df_dict)
    except ValidationError as err:
        for err_inst in err.errors():
            invalid_index = err_inst['loc'][1]
            invalid_col = err_inst['loc'][2]
            st.session_state[error_df_name].loc[invalid_index, invalid_col] = err_inst['msg']
            df.loc[invalid_index, 'is_valid'] = False
        
    return df
    
def download_button_on_click():
    """
    Stupid function that shows snow on screen when the download button is clicked!
    """
    st.snow()
    
def render_jinja(template_name, **kwargs):
    """
    Renders the json schema template with the values from the dataframe row
    """
    # loading the template
    template = env.get_template(template_name)

    # rendering the template and storing the resultant text in variable output
    output = template.render(**kwargs)
    
    return output

@st.cache_data
def convert_to_json(df, cls):
    """
    Converts the dataframe to a json object.
    Also replaces the string 'None' values with empty strings.
    This functions result is cached.
    """
    df_to_convert = df.copy(deep=True).replace('None', '').drop(columns=['is_valid'])
    
    if hasattr(cls['obj'], f"_{cls['name']}__json_schema_template_name"):
        template_name = getattr(cls['obj'], f"_{cls['name']}__json_schema_template_name").default
    else:
        template_name = f"{cls['name']}.jinja"
    
    json_list = []
    mapping =  dict.fromkeys(range(32)) # the json control chars
    for row in df_to_convert.to_dict('records'):
        try:
            # we also remove json control chars from the result of templating!
            rendered_schema = render_jinja(template_name, **row).translate(mapping)
            json_to_add = json.loads(rendered_schema)
        except TemplateNotFound as err:
            json_to_add = row
            
        json_list.append(json_to_add)

    
    return json.dumps(json_list)

@st.cache_data
def convert_to_dict(df, cls):
    """
    Converts the dataframe to a dict object.
    Also replaces the string 'None' values with empty strings.
    This functions result is cached.
    This is for request submission into the db.
    """
    df_to_convert = df.copy(deep=True).replace('None', '').drop(columns=['is_valid'])
    
    if hasattr(cls['obj'], f"_{cls['name']}__json_schema_template_name"):
        template_name = getattr(cls['obj'], f"_{cls['name']}__json_schema_template_name").default
    else:
        template_name = f"{cls['name']}.jinja"

    json_list = []
    mapping =  dict.fromkeys(range(32)) # the json control chars
    for row in df_to_convert.to_dict('records'):
        try:
            # we also remove json control chars from the result of templating!
            rendered_schema = render_jinja(template_name, **row).translate(mapping)
            json_to_add = json.loads(rendered_schema)
        except TemplateNotFound as err:
            json_to_add = row
            
        json_list.append(json_to_add)

    
    return json_list

def submit_button_on_click(**kwargs):
    """
    Handles submission on new request!
    """
    request_objects = kwargs["request_objects"]
    service_name = kwargs['service_name']
    
    try:
        insert_request(service_name, request_objects)
    except Exception as err:
        st.exception(err)
    
    

class NewProjectPage():
    """
    This class exists to support the multipage architecture. This is a generic service type page.
    """
    def __init__(self, cls):
        self.cls = cls
        
    def data_editor_on_change(self, **kwargs):
        """
        Runs on change of the data editor component.
        Handles the changed data, and updates the relevant dataframe.
        Runs the validation function on the newly changed dataframe.
        """
        cls_obj = self.cls['obj']
        df_name = kwargs['df_name']
        error_df_name = kwargs['error_df_name']
        edited_df_name = kwargs['edited_df_name']
        state = st.session_state[edited_df_name]
        
        for index, updates in state["edited_rows"].items():
            for key, value in updates.items():
                st.session_state[df_name].loc[st.session_state[df_name].index == index, key] = value
                
        for row in state["added_rows"]:
            df_row = pd.DataFrame.from_records([row])
            st.session_state[df_name] = pd.concat([st.session_state[df_name], df_row], ignore_index=True)
            
        for row_index in state["deleted_rows"]:
            st.session_state[df_name].drop(row_index, inplace=True)
            
        st.session_state[df_name] = validate_df(st.session_state[df_name], cls_obj, error_df_name)
        
    def upload_file(self, df_name, error_df_name):
        """
        Handles file uploading into the app.
        """
        cls_name = self.cls['name']
        cls_obj = self.cls['obj']
        
        if  'file_uploader_key' not in st.session_state:
            st.session_state['file_uploader_key'] = 0
        
        uploaded_file = st.file_uploader("Choose a CSV/JSON file", key=st.session_state['file_uploader_key'])
        if uploaded_file is not None:
            # Can be used wherever a "file-like" object is accepted:
            file_type = uploaded_file.name.split('.')[1]
            
            is_csv = file_type == 'csv'
            is_json = file_type == 'json'
            if is_csv:
                try:
                    dataframe = pd.read_csv(uploaded_file, index_col=0)
                except Exception as err:
                    st.exception(err)
            elif is_json:
                try:
                    dataframe = pd.read_json(uploaded_file, orient='records')
                except Exception as err:
                    st.exception(err)
            else:
                st.error("File was neither CSV or JSON! Please select a CSV/JSON file!")
            
            if is_json or is_csv:
                dataframe = dataframe.astype(str)
                
                # add the is_valid column if not existent
                if 'is_valid' not in dataframe.columns:
                    dataframe.assign(is_valid=False)
                
                # try to add the uploaded df to the saved one, throw exception if columns don't match
                if dataframe.columns.to_list() == st.session_state[df_name].columns.to_list():
                    try:
                        st.session_state[df_name] = pd.concat([st.session_state[df_name], dataframe], ignore_index=True )
                    except Exception as err:
                        st.exception(err)
                    
                    st.session_state[df_name] = validate_df(st.session_state[df_name], cls_obj, error_df_name)
                    # this is a hack to make this whole function run once for each file uploaded.
                    st.session_state['file_uploader_key'] = st.session_state['file_uploader_key'] + 1
                    
                    st.rerun()
                else:
                    st.error("File didn't have the correct columns! Please load a matching file next time!")
                    st.session_state['file_uploader_key'] = st.session_state['file_uploader_key'] + 1

            
    def download_json(self, df_name, error_df_name):
        """
        Handles the download of files.
        """
        cls_name = self.cls['name']
        
        # handle download and data validity message
        download_disabled = False if st.session_state[df_name]['is_valid'].all() else True
        
        if download_disabled:
            st.error(f"The values are not valid!")
            st.subheader('Errors')
            st.dataframe(st.session_state[error_df_name], use_container_width=True)
        else:
            st.success(f"The values are valid!")
            
        json_obj = convert_to_json(st.session_state[df_name], self.cls)

        st.download_button(
            label="Download JSON",
            data=json_obj,
            file_name=f"{cls_name}_data.json",
            mime="text/json",
            icon=":material/download:",
            disabled=download_disabled,
            on_click=download_button_on_click
        )
        
    def submit_request(self, df_name, error_df_name):
        """
        Handles the submission of a request.
        """
        cls_name = self.cls['name']
        
        # handle download and data validity message
        submit_disabled = False if st.session_state[df_name]['is_valid'].all() else True
        
        if submit_disabled:
            st.error(f"The values are not valid!")
            st.subheader('Errors')
            st.dataframe(st.session_state[error_df_name], use_container_width=True)
        else:
            st.success(f"The values are valid!")
            
        dict_obj = convert_to_dict(st.session_state[df_name], self.cls)

        submit_btn_name = f"submit_btn_{cls_name}"
        st.button(
            label="Submit Request",
            key=submit_btn_name,
            icon=":material/skull:",
            disabled=submit_disabled,
            on_click=submit_button_on_click,
            kwargs={'request_objects': dict_obj, 'service_name': cls_name}
        )
    
    def run_page(self):
        """
        The 'main' fucntion of each page. Runs everything.
        """
        cls_name = self.cls['name']
        cls_obj = self.cls['obj']
        members = list(cls_obj.model_fields.keys())
        
        split_name = re.sub( r"([A-Z])", r" \1", cls_name).split()
        page_title = ' '.join(split_name)
        st.title(page_title)
        
        # Set up column config with the selectbox for Enum attributes
        column_cfg={
            "is_valid": st.column_config.TextColumn("IsValid", width="small", default=False),
        }
        
        for member in members:
            member_type = cls_obj.model_fields[member].annotation
            if issubclass(member_type, enum.Enum):
                member_values = [el.value for el in member_type]
                column_cfg.update({member: st.column_config.SelectboxColumn(
                    f"{member.capitalize()}",
                    help=cls_obj.model_fields[member].description,
                    width="small",
                    options=member_values,
                    required=True,
                )})
            else:
                column_cfg.update({member: st.column_config.TextColumn(
                    f"{member.capitalize()}",
                    help=cls_obj.model_fields[member].description,
                    width="small",
                    required=True,
                )})
                
        df_name = f"df_{cls_name}"
        error_df_name = f"df_{cls_name}_error"
        styled_df_name = f"df_{cls_name}_styled"
        edited_df_name = f"df_{cls_name}_edited"
        if  error_df_name not in st.session_state:
            # Create an empty DataFrame with column names
            st.session_state[error_df_name] = pd.DataFrame(columns=[*members])
            
        if  df_name not in st.session_state:
            # Create an empty DataFrame with column names
            st.session_state[df_name] = pd.DataFrame(columns=[*members, 'is_valid'])
        
        st.session_state[styled_df_name] = st.session_state[df_name].style.map(highlight_is_valid, subset=pd.IndexSlice[:, ['is_valid']])

        st.subheader('Editor')
        st.data_editor(
            st.session_state[styled_df_name],
            column_config=column_cfg,
            key=edited_df_name,
            disabled=["is_valid"],
            num_rows="dynamic",
            hide_index=False,
            on_change=self.data_editor_on_change,
            kwargs={'cls_name': cls_name, 'cls_obj': cls_obj, 'df_name': df_name, 'edited_df_name': edited_df_name, 'error_df_name': error_df_name},
            use_container_width=False,
            width=10000,
        )
        
        self.upload_file(df_name, error_df_name)
        
        if not st.session_state[df_name].empty:
            self.submit_request(df_name, error_df_name)
        
    def get_page(self):
        """
        Returns the page object as needed.
        """
        split_name = re.sub( r"([A-Z])", r" \1", self.cls['name']).split()
        lower_split_name = [word.lower() for word in split_name]
        url_pathname = '-'.join(lower_split_name)
        page_title = ' '.join(split_name)
        page_icon = getattr(self.cls['obj'], f"_{self.cls['name']}__icon") # getting the default 
        return st.Page(self.run_page, title=page_title, icon=f"{page_icon.default}", url_path=url_pathname)