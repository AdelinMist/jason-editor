import streamlit as st
import pandas as pd
import enum
import re
import json
import os
from pydantic import ValidationError
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from db.requests import insert_request
from mongo_db import init_service_collection
from utils.misc import highlight_is_valid
from utils.validation.request import ActionType

# jinja2 setup for the json schema templates
# loading the environment
file_path = os.path.abspath(os.path.dirname(__file__))
env = Environment(loader = FileSystemLoader(f"{file_path}/../../json_schema_templates"))

def validate_obj(obj, validation_cls):
    """
    Runs a pydantic validation on the object passed.
    """
    try:
        validated_obj = validation_cls(**obj).model_dump()
    except ValidationError as err:
        raise err
        
    return validated_obj

def validate_df(df, validation_cls, error_df_name):
    """
    Runs a pydantic validation on the dataframe passed.
    Recreates the error dataframe based on current validation errors.
    Sets the 'is_valid' column on the dataframe based on validation results.
    """
    st.session_state[error_df_name] = st.session_state[error_df_name].iloc[0:0].copy()

    df = df.assign(is_valid=True)
    
    df_dict = df.loc[:, df.columns != 'is_valid'].to_dict(orient="records")
    validated_dict = []
    
    for index, obj in enumerate(df_dict):
        try:
            validated_obj = validate_obj(obj, validation_cls)
            validated_dict.append(validated_obj)
        except ValidationError as err:
            for err_inst in err.errors():
                invalid_col = err_inst['loc'][0]
                st.session_state[error_df_name].loc[index, invalid_col] = err_inst['msg']
                df.loc[index, 'is_valid'] = False
    
    if st.session_state[error_df_name].empty:
        df = pd.DataFrame.from_records(validated_dict).assign(is_valid=True)
        
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
    
    validation_cls = kwargs['validation_cls'] 
    df_name = kwargs['df_name']
    deleted_df_name = kwargs['deleted_df_name']
    added_set_name = kwargs['added_set_name']
    edited_set_name = kwargs['edited_set_name']
    service_name = kwargs['service_name']
    
    added_indices = st.session_state[df_name].index.isin(st.session_state[added_set_name])
    added_objects = st.session_state[df_name].loc[added_indices]
    added_objects = convert_to_dict(added_objects, validation_cls)
    
    edited_indices = st.session_state[df_name].index.isin(st.session_state[edited_set_name])
    edited_objects = st.session_state[df_name].loc[edited_indices]
    edited_objects = convert_to_dict(edited_objects, validation_cls)

    objects_to_delete = convert_to_dict(st.session_state[deleted_df_name], validation_cls)
    
    try:
        if len(added_objects) != 0:
            insert_request(service_name, ActionType.CREATE, added_objects)
            del st.session_state[added_set_name]
            
        if len(edited_objects) != 0:
            insert_request(service_name, ActionType.UPDATE, edited_objects)
            del st.session_state[edited_set_name]
            
        if len(objects_to_delete) != 0:
            insert_request(service_name, ActionType.DELETE, objects_to_delete)
            del st.session_state[deleted_df_name]
            
        del st.session_state[df_name]
             
    except Exception as err:
        st.exception(err)
    

class ServicePage():
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
        added_set_name = kwargs['added_set_name']
        edited_set_name = kwargs['edited_set_name']
        deleted_df_name = kwargs['deleted_df_name']
        state = st.session_state[edited_df_name]
        
        for index, updates in state["edited_rows"].items():
            if index not in st.session_state[added_set_name]:
                st.session_state[edited_set_name].add(index)
            for key, value in updates.items():
                st.session_state[df_name].loc[st.session_state[df_name].index == index, key] = value
                
        for row in state["added_rows"]:
            df_row = pd.DataFrame.from_records([row])
            st.session_state[df_name] = pd.concat([st.session_state[df_name], df_row], ignore_index=True)
            st.session_state[added_set_name].add(st.session_state[df_name].last_valid_index())
            
        for row_index in state["deleted_rows"]:
            # add deleted object to a list that will be made into a DELETE action request
            if st.session_state[df_name].loc[row_index, 'is_valid']:
                deleted_row = st.session_state[df_name].loc[row_index].copy()
                st.session_state[deleted_df_name] = pd.concat([st.session_state[deleted_df_name], deleted_row.to_frame().T], ignore_index=True)
            st.session_state[df_name].drop(row_index, inplace=True)
            
        st.session_state[df_name] = validate_df(st.session_state[df_name], cls_obj, error_df_name)
        
    def upload_file(self, df_name, error_df_name, added_set_name):
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
                
                dataframe = validate_df(dataframe, cls_obj, error_df_name)
                # try to add the uploaded df to the saved one, throw exception if columns don't match
                if dataframe.columns.to_list() == st.session_state[df_name].columns.to_list():
                    try:
                        st.session_state[df_name] = pd.concat([st.session_state[df_name], dataframe], ignore_index=True )
                        st.session_state[added_set_name].add(st.session_state[df_name].last_valid_index())
                    except Exception as err:
                        st.exception(err)
                    
                    st.session_state[df_name] = validate_df(st.session_state[df_name], cls_obj, error_df_name)
                    # this is a hack to make this whole function run once for each file uploaded.
                    st.session_state['file_uploader_key'] = st.session_state['file_uploader_key'] + 1
                    
                    st.rerun()
                else:
                    st.error("File didn't have the correct columns! Please load a matching file next time!")
                    st.session_state['file_uploader_key'] = st.session_state['file_uploader_key'] + 1
        
    def submit_request(self, df_name, error_df_name, deleted_df_name, added_set_name, edited_set_name):
        """
        Handles the submission of a request.
        """
        cls_name = self.cls['name']
        cls_obj = self.cls['obj']
        
        # handle download and data validity message
        submit_disabled = False if st.session_state[df_name]['is_valid'].all() else True
        
        if submit_disabled:
            st.error(f"The values are not valid!")
            st.subheader('Errors')
            st.dataframe(st.session_state[error_df_name], use_container_width=True)
        else:
            st.success(f"The values are valid!")

        submit_btn_name = f"submit_btn_{cls_name}"
        st.button(
            label="Submit Request",
            key=submit_btn_name,
            icon=":material/skull:",
            disabled=submit_disabled,
            on_click=submit_button_on_click,
            kwargs={'service_name': cls_name, 'added_set_name': added_set_name, 'edited_set_name': edited_set_name, 'df_name': df_name, 'deleted_df_name': deleted_df_name, 'validation_cls': self.cls}
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
            "is_valid": st.column_config.TextColumn("IsValid", width="medium", default=False),
        }
        
        for member in members:
            member_type = cls_obj.model_fields[member].annotation
            try:
                is_enum = issubclass(member_type, enum.Enum)
            except:
                is_enum = False
            if is_enum:
                member_values = [el.value for el in member_type]
                column_cfg.update({member: st.column_config.SelectboxColumn(
                    f"{member.capitalize()}",
                    help=cls_obj.model_fields[member].description,
                    width="medium",
                    options=member_values,
                    required=True,
                )})
            else:
                column_cfg.update({member: st.column_config.TextColumn(
                    f"{member.capitalize()}",
                    help=cls_obj.model_fields[member].description,
                    width="medium",
                    required=True,
                )})
                
        df_columns = list([*members, 'is_valid'])
                
        df_name = f"df_{cls_name}"
        error_df_name = f"df_{cls_name}_error"
        styled_df_name = f"df_{cls_name}_styled"
        edited_df_name = f"df_{cls_name}_edited"
        added_set_name = f"added_set_{cls_name}"
        edited_set_name = f"edited_set_{cls_name}"
        deleted_df_name = f"df_{cls_name}_deleted"
        if  error_df_name not in st.session_state:
            # Create an empty DataFrame with column names
            st.session_state[error_df_name] = pd.DataFrame(columns=[*members])
            
        if  added_set_name not in st.session_state:
            # Create an empty set
            st.session_state[added_set_name] = set()
            
        if  edited_set_name not in st.session_state:
            # Create an empty set
            st.session_state[edited_set_name] = set()
            
        if  deleted_df_name not in st.session_state:
            # Create an empty DataFrame with column names
            st.session_state[deleted_df_name] = pd.DataFrame(columns=df_columns)
            
        if  df_name not in st.session_state or st.session_state[df_name].empty:
            # Create an empty DataFrame with column names
            st.session_state[df_name] = pd.DataFrame(columns=df_columns)
            
        st.session_state[styled_df_name] = st.session_state[df_name].style.map(highlight_is_valid, subset=pd.IndexSlice[:, ['is_valid']])

        columns_to_display = df_columns
        if 'id' in columns_to_display:
            columns_to_display.remove('id')
            
        st.subheader('Editor')
        st.data_editor(
            st.session_state[styled_df_name],
            column_config=column_cfg,
            column_order=columns_to_display,
            key=edited_df_name,
            disabled=["is_valid"],
            num_rows="dynamic",
            hide_index=False,
            on_change=self.data_editor_on_change,
            kwargs={'cls_name': cls_name, 'cls_obj': cls_obj, 'df_name': df_name, 'edited_df_name': edited_df_name, 'error_df_name': error_df_name, 'added_set_name': added_set_name, 'edited_set_name': edited_set_name, 'deleted_df_name': deleted_df_name},
            use_container_width=False,
            width=10000,
        )

        self.upload_file(df_name, error_df_name, added_set_name)
        
        if not st.session_state[df_name].empty or not st.session_state[deleted_df_name].empty:
            self.submit_request(df_name, error_df_name, deleted_df_name, added_set_name, edited_set_name)
        
    def get_page(self):
        """
        Returns the page object as needed.
        """
        split_name = re.sub( r"([A-Z])", r" \1", self.cls['name']).split()
        lower_split_name = [word.lower() for word in split_name]
        
        ### init the db collection
        coll_name = '_'.join(lower_split_name)
        init_service_collection(coll_name)
        
        ### return page object
        url_pathname = '-'.join(lower_split_name)
        page_title = ' '.join(split_name)
        page_icon = getattr(self.cls['obj'], f"_{self.cls['name']}__icon") # getting the default 
        return st.Page(self.run_page, title=page_title, icon=f"{page_icon.default}", url_path=url_pathname)