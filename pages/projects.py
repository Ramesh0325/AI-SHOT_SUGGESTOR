import streamlit as st
import sys
import os
import json

# Add parent directory to path to allow importing from root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db import get_user_projects, create_project, delete_project, get_project_shots

st.set_page_config(page_title="Projects - AI Shot Suggestor", layout="wide")

def reset_app_state():
    """Reset the app state variables when switching projects"""
    keys_to_reset = ["shots", "images", "current_shot_id", "scene_description", "genre", "mood"]
    for key in keys_to_reset:
        if key in st.session_state:
            del st.session_state[key]

def show_projects():
    st.title("🎬 Your Shot Projects")
    
    # Authenticate user
    if 'is_authenticated' not in st.session_state or not st.session_state.is_authenticated:
        st.warning("Please log in to access your projects")
        st.page_link("pages/login.py", label="Go to Login", icon="🔐")
        return
    
    user = st.session_state.user
    st.write(f"Welcome, {user['username']}!")
    
    # Create a new project section
    with st.expander("Create New Project", expanded=False):
        with st.form("new_project_form"):
            project_name = st.text_input("Project Name")
            project_desc = st.text_area("Project Description (optional)")
            submit_button = st.form_submit_button("Create Project")
            
            if submit_button:
                if not project_name:
                    st.error("Please enter a project name")
                else:
                    project_id = create_project(user['id'], project_name, project_desc)
                    st.success(f"Project '{project_name}' created successfully!")
                    st.rerun()
    
    # Display existing projects
    projects = get_user_projects(user['id'])
    
    if not projects:
        st.info("You don't have any projects yet. Create one to get started!")
    else:
        st.write(f"You have {len(projects)} project(s):")
        
        for project in projects:
            with st.container():
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.subheader(project['name'])
                    st.write(project['description'] if project['description'] else "_No description_")
                    st.text(f"Created: {project['created_at']}")
                
                with col2:
                    # View project button
                    if st.button("View & Edit", key=f"view_{project['id']}"):
                        # Reset app state before switching to the new project
                        reset_app_state()
                        # Set the current project and navigate
                        st.session_state.current_project = project
                        st.switch_page("app.py")  # Go to main app with this project
                
                with col3:
                    # Delete project button
                    if st.button("Delete", key=f"delete_{project['id']}"):
                        if st.session_state.get('confirm_delete') == project['id']:
                            delete_project(project['id'])
                            st.success(f"Project deleted!")
                            st.session_state.pop('confirm_delete', None)
                            st.rerun()
                        else:
                            st.session_state.confirm_delete = project['id']
                            st.warning("Click again to confirm deletion")
                
                # Show shots for this project
                shots = get_project_shots(project['id'])
                if shots:
                    st.write(f"**Contains {len(shots)} shot sets**")
                
                st.markdown("---")

    # Logout button
    if st.button("Logout"):
        for key in ['user', 'is_authenticated', 'current_project']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    show_projects()