import streamlit as st
import pandas as pd
import enum
import re
import numpy as np
from pydantic import ValidationError
from jinja2 import TemplateNotFound
from db.requests import insert_request
from mongo_db import init_service_collection
from utils.misc import highlight_is_valid
from utils.validation.request import ActionType
from db.services import get_my_service_objects

@st.cache_data
def convert_to_records(df):
    """
    Converts the dataframe to a list of objects.
    Also replaces the string 'None' values with empty strings.
    This functions result is cached.
    This is for request submission into the db.
    """
    record_list = df.copy(deep=True).drop(columns=['is_valid']).to_dict('records')

    # get rid of None values
    record_list = [ {key:val for key, val in record.items() if val != None} for record in record_list ] 

    return record_list

class ServicePage():
    """
    This class exists to support the multipage architecture. This is a generic service type page.
    """
    def __init__(self, cls):
        self.cls = cls
        split_name = re.sub( r"([A-Z])", r" \1", self.cls['name']).split()
        lower_split_name = [word.lower() for word in split_name]
        
        self.page_title = ' '.join(split_name)
        
        ### init the db collection
        snake_case_name = '_'.join(lower_split_name)
        self.snake_case_name = snake_case_name
        init_service_collection(snake_case_name)
        
        ### return page object
        self.url_pathname = '-'.join(lower_split_name)
        self.page_title = ' '.join(split_name)
        
    def validate_obj(self, obj):
        """
        Runs a pydantic validation on the object passed.
        """
        validation_cls = self.cls['obj']
        try:
            print(obj)
            raw_obj = validation_cls(**obj)
            validated_obj = raw_obj.model_dump(object_id_to_str=True)
        except ValidationError as err:
            raise err
            
        return validated_obj

    def validate_df(self, df):
        """
        Runs a pydantic validation on the dataframe passed.
        Recreates the error dataframe based on current validation errors.
        Sets the 'is_valid' column on the dataframe based on validation results.
        """
        st.session_state[self.error_df_name] = st.session_state[self.error_df_name].iloc[0:0].copy()
        
        df = df.assign(is_valid=True)
        
        df_dict = df.loc[:, df.columns != 'is_valid'].to_dict(orient="records")
        validated_dict = []
        
        for index, obj in enumerate(df_dict):
            try:
                validated_obj = self.validate_obj(obj)
                validated_dict.append(validated_obj)
            except ValidationError as err:
                for err_inst in err.errors():
                    invalid_col = err_inst['loc'][0]
                    st.session_state[self.error_df_name].loc[index, invalid_col] = err_inst['msg']
                    df.loc[index, 'is_valid'] = False
        
        if st.session_state[self.error_df_name].empty:
            df = pd.DataFrame.from_records(validated_dict).assign(is_valid=True).replace({np.nan: None})
            
        return df
    
    def submit_logic(self, submitted_objects, action_type):
        """
        Handles the submission logic itself, based on the action type.
        """
        if action_type == ActionType.CREATE:
            insert_request(self.snake_case_name, ActionType.CREATE, submitted_objects)
        elif action_type == ActionType.UPDATE:
            insert_request(self.snake_case_name, ActionType.UPDATE, submitted_objects)
        elif action_type == ActionType.DELETE:
            insert_request(self.snake_case_name, ActionType.DELETE, submitted_objects)
        
    def submit_button_on_click(self):
        """
        Handles submission on new request!
        """
        
        added_indices = st.session_state[self.df_name].index.isin(st.session_state[self.added_set_name])
        added_objects = st.session_state[self.df_name].loc[added_indices]
        added_objects = convert_to_records(added_objects)
        
        edited_indices = st.session_state[self.df_name].index.isin(st.session_state[self.edited_set_name])
        edited_objects = st.session_state[self.df_name].loc[edited_indices]
        edited_objects = convert_to_records(edited_objects)

        objects_to_delete = convert_to_records(st.session_state[self.deleted_df_name])
        
        try:
            if len(added_objects) != 0:
                self.submit_logic(added_objects, ActionType.CREATE)
                del st.session_state[self.added_set_name]
                
            if len(edited_objects) != 0:
                self.submit_logic(edited_objects, ActionType.UPDATE)
                del st.session_state[self.edited_set_name]
                
            if len(objects_to_delete) != 0:
                self.submit_logic(objects_to_delete, ActionType.DELETE)
                del st.session_state[self.deleted_df_name]
                
            del st.session_state[self.df_name]
                
        except Exception as err:
            st.exception(err)
        
    def data_editor_on_change(self):
        """
        Runs on change of the data editor component.
        Handles the changed data, and updates the relevant dataframe.
        Runs the validation function on the newly changed dataframe.
        """
        cls_obj = self.cls['obj']
        state = st.session_state[self.edited_df_name]
        
        for index, updates in state["edited_rows"].items():
            if index not in st.session_state[self.added_set_name]:
                st.session_state[self.edited_set_name].add(index)
            for key, value in updates.items():
                st.session_state[self.df_name].loc[st.session_state[self.df_name].index == index, key] = value
                
        for row in state["added_rows"]:
            df_row = pd.DataFrame.from_records([row])
            st.session_state[self.df_name] = pd.concat([st.session_state[self.df_name], df_row], ignore_index=True).replace({np.nan: None})
            st.session_state[self.added_set_name].add(st.session_state[self.df_name].last_valid_index())
            
        for row_index in state["deleted_rows"]:
            # add deleted object to a list that will be made into a DELETE action request
            if st.session_state[self.df_name].loc[row_index, 'is_valid']:
                deleted_row = st.session_state[self.df_name].loc[row_index].copy()
                st.session_state[self.deleted_df_name] = pd.concat([st.session_state[self.deleted_df_name], deleted_row.to_frame().T], ignore_index=True)
            st.session_state[self.df_name].drop(row_index, inplace=True)

        st.session_state[self.df_name] = self.validate_df(st.session_state[self.df_name])
        
    def upload_file(self):
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
                
                dataframe = self.validate_df(dataframe)
                # try to add the uploaded df to the saved one, throw exception if columns don't match
                if dataframe.columns.to_list() == st.session_state[self.df_name].columns.to_list():
                    try:
                        st.session_state[self.df_name] = pd.concat([st.session_state[self.df_name], dataframe], ignore_index=True )
                        st.session_state[self.added_set_name].add(st.session_state[self.df_name].last_valid_index())
                    except Exception as err:
                        st.exception(err)
                    
                    st.session_state[self.df_name] = self.validate_df(st.session_state[self.df_name])
                    # this is a hack to make this whole function run once for each file uploaded.
                    st.session_state['file_uploader_key'] = st.session_state['file_uploader_key'] + 1
                    
                    st.rerun()
                else:
                    st.error("File didn't have the correct columns! Please load a matching file next time!")
                    st.session_state['file_uploader_key'] = st.session_state['file_uploader_key'] + 1
        
    def submit_request(self):
        """
        Handles the submission of a request.
        """
        cls_name = self.cls['name']
        
        # handle download and data validity message
        submit_disabled = False if st.session_state[self.df_name]['is_valid'].all() else True
        
        if submit_disabled:
            st.error(f"The values are not valid!")
            st.subheader('Errors')
            st.dataframe(st.session_state[self.error_df_name], use_container_width=True)
        else:
            st.success(f"The values are valid!")

        submit_btn_name = f"submit_btn_{cls_name}"
        st.button(
            label="Submit Request",
            key=submit_btn_name,
            icon=":material/skull:",
            disabled=submit_disabled,
            on_click=self.submit_button_on_click
        )
        
    def get_page_data(self):
        """
        This function simply gets the data already existing in the db for this page.
        """
        return [get_my_service_objects(self.snake_case_name)]
    
    def run_page(self):
        """
        The 'main' fucntion of each page. Runs everything.
        """
        cls_name = self.cls['name']
        cls_obj = self.cls['obj']
        members = list(cls_obj.model_fields.keys())
        
        st.title(self.page_title)
        
        ### Set up column config with the selectbox for Enum attributes
        
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
        
        ### session data setup
        
        df_columns = list([*members, 'is_valid'])
                
        self.df_name = f"df_{cls_name}"
        self.error_df_name = f"df_{cls_name}_error"
        self.styled_df_name = f"df_{cls_name}_styled"
        self.edited_df_name = f"df_{cls_name}_edited"
        self.added_set_name = f"added_set_{cls_name}"
        self.edited_set_name = f"edited_set_{cls_name}"
        self.deleted_df_name = f"df_{cls_name}_deleted"
        
        if  self.error_df_name not in st.session_state:
            # Create an empty DataFrame with column names
            st.session_state[self.error_df_name] = pd.DataFrame(columns=[*members])
            
        if  self.added_set_name not in st.session_state:
            # Create an empty set
            st.session_state[self.added_set_name] = set()
            
        if  self.edited_set_name not in st.session_state:
            # Create an empty set
            st.session_state[self.edited_set_name] = set()
            
        if  self.deleted_df_name not in st.session_state:
            # Create an empty DataFrame with column names
            st.session_state[self.deleted_df_name] = pd.DataFrame(columns=df_columns)
            
        if  self.df_name not in st.session_state or st.session_state[self.df_name].empty:
            # Create a DataFrame
            # get service objects in db
            service_objects = self.get_page_data()
            service_objects_df = pd.DataFrame.from_records(service_objects)
            if not service_objects_df.empty:
                service_objects_df = self.validate_df(service_objects_df)
            st.session_state[self.df_name] = pd.DataFrame(service_objects_df, columns=df_columns).astype(str)
        
        st.session_state[self.styled_df_name] = st.session_state[self.df_name].style.map(highlight_is_valid, subset=pd.IndexSlice[:, ['is_valid']])

        columns_to_display = df_columns
        if 'id' in columns_to_display:
            columns_to_display.remove('id')
        
        if 'project' in columns_to_display:
            columns_to_display.remove('project')
        
        st.subheader('Editor')
        st.data_editor(
            st.session_state[self.styled_df_name],
            column_config=column_cfg,
            column_order=columns_to_display,
            key=self.edited_df_name,
            disabled=["is_valid"],
            num_rows="dynamic",
            hide_index=False,
            on_change=self.data_editor_on_change,
            use_container_width=False,
            width=10000,
        )

        self.upload_file()
        
        if not st.session_state[self.df_name].empty or not st.session_state[self.deleted_df_name].empty:
            self.submit_request()
        
    def get_page(self):
        """
        Returns the page object as needed.
        """
        page_icon = getattr(self.cls['obj'], f"_{self.cls['name']}__icon") # getting the default 
        return st.Page(self.run_page, title=self.page_title, icon=f"{page_icon.default}", url_path=self.url_pathname)