
import streamlit as st
import sys
import os
import re

# Add parent directory to path to allow importing from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import create_user

st.set_page_config(page_title="Sign Up - AI Shot Suggestor", layout="centered")

def validate_email(email):
    """Simple email validation"""
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(pattern, email) is not None

def show_signup():
    st.title("🎬 Sign Up for Shot Suggestor")
    
    with st.form("signup_form", clear_on_submit=True):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        submit_button = st.form_submit_button("Sign Up")
        
        if submit_button:
            if not username or not email or not password or not confirm_password:
                st.error("Please fill out all fields")
                return
                
            if not validate_email(email):
                st.error("Please enter a valid email address")
                return
                
            if password != confirm_password:
                st.error("Passwords do not match")
                return
                
            if len(password) < 6:
                st.error("Password should be at least 6 characters long")
                return
                
            user_id = create_user(username, email, password)
            if user_id:
                st.success("Account created successfully! Please log in.")
                st.page_link("pages/login.py", label="Go to Login", icon="🔐")
            else:
                st.error("Username or email already exists")
    
    st.markdown("---")
    st.markdown("Already have an account? [Login](/login)")
    
if __name__ == "__main__":
    # Check if user is already logged in
    if 'is_authenticated' in st.session_state and st.session_state.is_authenticated:
        st.switch_page("app.py")  # Redirect to main app
    else:
        show_signup()