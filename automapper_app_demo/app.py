import os
os.environ["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

import streamlit as st
import pandas as pd
from utils.interface_utils import display_mapper_interface

st.set_page_config(layout="wide")

def initialize_session_state():
    """Initialize session state variables"""
    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = True  # Auto-authenticated for now
    if "username" not in st.session_state:
        st.session_state.username = "user"
    if "edit_mode" not in st.session_state:
        st.session_state.edit_mode = False
    if "current_file" not in st.session_state:
        st.session_state.current_file = None

def main():
    initialize_session_state()
    display_mapper_interface()

if __name__ == "__main__":
    main()
