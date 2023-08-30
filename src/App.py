import streamlit as st
from streamlit_extras.switch_page_button import switch_page
from utils import page_config

page_config()

# router
if "authentication_status" not in st.session_state or not st.session_state["authentication_status"]:
    switch_page("profile")