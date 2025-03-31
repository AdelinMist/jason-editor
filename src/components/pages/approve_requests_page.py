import streamlit as st
import pandas as pd
from db.requests import update_requests, get_requests_for_approval
from utils.requests import execute_requests

def approve_button_on_click():
    """
    Handles approval and execution of requests!
    """
    selected_rows = st.session_state["approval_requests_selection_df"].selection.rows
    requests_copy = st.session_state["approval_requests_df"].copy(deep=True)
    df_dict = requests_copy.drop(columns=['project']).iloc[selected_rows]
    requests_to_execute_ids = df_dict.get('_id').tolist()

    try:
        exec_status = execute_requests(requests_to_execute_ids)
        if exec_status:
            df_dict = df_dict.assign(status='IN_PROGRESS').to_dict('records')
        else:
            df_dict = df_dict.assign(status='FAILED').to_dict('records')
        update_requests(df_dict)
    except Exception as err:
        st.exception(err)

class ApproveRequestsPage():
    """
    This class exists to support the multipage architecture. This is a page to approve requests.
    """
    
    def run_page(self):
        """
        The 'main' fucntion of each page. Runs everything.
        """
        st.title("Approve Requests")
        request_data = get_requests_for_approval()
        
        st.session_state["approval_requests_df"] = pd.DataFrame(request_data)
        columns_to_display = list(st.session_state["approval_requests_df"].columns)
        if '_id' in columns_to_display:
            columns_to_display.remove('_id')
        
        st.subheader('Requests For Approval')
        requests = st.dataframe(
            st.session_state["approval_requests_df"],
            column_config={
                "request_objects": st.column_config.JsonColumn(
                    "request data",
                    help="JSON strings or objects",
                    width="large",
                ),
            },
            key = "approval_requests_selection_df",
            on_select="rerun",
            selection_mode=["multi-row"],
            hide_index=False,
            column_order=columns_to_display,
            use_container_width=False,
            width=10000,
        )
        
        st.button(
            label="Approve Requests",
            icon=":material/skull:",
            on_click=approve_button_on_click,
            kwargs={}
        )
        
    def get_page(self):
        """
        Returns the page object as needed.
        """
        url_pathname = 'approve-requests'
        page_title = 'Requests For Approval'
        page_icon = ':material/mystery:' 
        return st.Page(self.run_page, title=page_title, icon=page_icon, url_path=url_pathname)