from pydantic import ValidationError
import streamlit as st
import pandas as pd
from db.requests import get_my_requests, update_requests
from utils.requests import execute_requests
from utils.validation.request import Request

class RequestsPage():
    """
    This class exists to support the multipage architecture. This is a generic requests type page.
    """
    def __init__(self):
        """
        Init, meant to be overloaded.
        """
        
        self.url_pathname = ''
        self.page_title = ''
        self.page_icon = ':material/genetics:' 
        
        self.allow_execute = False
        self.exec_button_label = ""
        
    def exec_button_on_click(self):
        """
        Handles approval and execution of requests!
        """
        selected_rows = st.session_state[self.select_df_name].selection.rows
        requests_copy = st.session_state[self.df_name].copy(deep=True)
        requests_to_execute = requests_copy.iloc[selected_rows]

        try:
            exec_status = execute_requests(requests_to_execute)
            if exec_status:
                requests_to_execute = requests_to_execute.assign(status='APPROVED').to_dict('records')
            else:
                requests_to_execute = requests_to_execute.assign(status='FAILED').to_dict('records')
            update_requests(requests_to_execute)
        except Exception as err:
            st.exception(err)
        
    def validate_obj(self, obj):
        """
        Runs a pydantic validation on the object passed.
        """
        try:
            raw_obj = Request(**obj)
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
        if df.empty:
            return df
        
        st.session_state[self.error_df_name] = st.session_state[self.error_df_name].iloc[0:0].copy()
        
        df_dict = df.to_dict(orient="records")
        validated_dict = []
        
        for index, obj in enumerate(df_dict):
            try:
                validated_obj = self.validate_obj(obj)
                validated_dict.append(validated_obj)
            except ValidationError as err:
                for err_inst in err.errors():
                    invalid_col = err_inst['loc'][0]
                    st.session_state[self.error_df_name].loc[index, invalid_col] = err_inst['msg']
        
        if st.session_state[self.error_df_name].empty:
            df = pd.DataFrame.from_records(validated_dict)
            
        return df
    
    def get_page_data(self):
        """
        This function simply gets the data already existing in the db for this page. Meant for overloading.
        """
        return get_my_requests()
    
    def run_page(self):
        """
        The 'main' fucntion of each page. Runs everything.
        """
        st.title(self.page_title)
        
        self.error_df_name = f"df_{__file__}_error"
        self.select_df_name = f"df_{__file__}_select"
        self.df_name = f"df_{__file__}"
        
        request_data = self.get_page_data()
        st.session_state[self.df_name] = pd.DataFrame(request_data)
        
        columns_to_display = list(st.session_state[self.df_name].columns)
        exclude = ['_id', 'id']
        for col in exclude:
            if col in columns_to_display:
                columns_to_display.remove(col)
            
        if  self.error_df_name not in st.session_state:
            # Create an empty DataFrame with column names
            st.session_state[self.error_df_name] = pd.DataFrame(columns=st.session_state[self.df_name].columns)
            
        st.session_state[self.df_name] = self.validate_df(st.session_state[self.df_name])
        
        if not st.session_state[self.error_df_name].empty:
            st.error(f"The values are not valid!")
            st.subheader('Errors')
            st.dataframe(st.session_state[self.error_df_name], use_container_width=True)
        
        if self.allow_execute:
            selection_mode = ["multi-row"]
        else:
            selection_mode = []
            
        st.subheader('Requests')
        requests = st.dataframe(
            st.session_state[self.df_name],
            column_config={
                "request_objects": st.column_config.JsonColumn(
                    "request data",
                    help="JSON strings or objects",
                    width="large",
                ),
            },
            key = self.select_df_name,
            on_select="rerun",
            selection_mode=selection_mode,
            hide_index=False,
            column_order=columns_to_display,
            use_container_width=False,
            width=10000,
        )

        if self.allow_execute:
            st.button(
                label=self.exec_button_label,
                icon=":material/skull:",
                on_click=self.exec_button_on_click,
                kwargs={}
            )
        
    def get_page(self):
        """
        Returns the page object as needed.
        """
        return st.Page(self.run_page, title=self.page_title, icon=self.page_icon, url_path=self.url_pathname)