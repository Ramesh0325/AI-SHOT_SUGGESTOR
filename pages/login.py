import streamlit as st
import sys
import os

# Add parent directory to path to allow importing from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import authenticate_user

st.set_page_config(page_title="Login - AI Shot Suggestor", layout="centered")

def show_login():
    st.title("🎬 Login to Shot Suggestor")
    
    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if not username or not password:
                st.error("Please enter both username and password")
                return
                
            user = authenticate_user(username, password)
            if user:
                st.success("Login successful!")
                # Store user info in session state
                st.session_state.user = user
                st.session_state.is_authenticated = True
                # Redirect to main app
                st.rerun()
            else:
                st.error("Invalid username or password")
    
    st.markdown("---")
    st.markdown("Don't have an account? [Sign up](/signup)")
    
if __name__ == "__main__":
    # Check if user is already logged in
    if 'is_authenticated' in st.session_state and st.session_state.is_authenticated:
        st.switch_page("app.py")  # Redirect to main app
    else:
        show_login()