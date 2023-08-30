import streamlit as st
from PIL import Image
from streamlit_extras.switch_page_button import switch_page
import ktrain



def add_logo():
    st.markdown(
        """
        <style>
            [data-testid="stSidebarNav"] {
                background-image: url(https://enflux-static-prod.s3.amazonaws.com/email/Logo_signature.png);
                background-repeat: no-repeat;
                margin-top: 50px;
                margin-bottom: 50px;
                background-size: contain;
                height:100px;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hide_footer():
    # Hides 'Made with Streamlit'
    return st.markdown(
        """
        <style>
        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True
    )


def is_Authenticated():
    if "authentication_status" not in st.session_state or not st.session_state["authentication_status"]:
        switch_page("Profile")

def page_config():
    im = Image.open("src/images/favicon.ico")
    st.set_page_config(page_title="CompetencyGenie", page_icon=im, layout="wide")