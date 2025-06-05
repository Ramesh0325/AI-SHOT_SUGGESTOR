import streamlit as st
import json
import os
from model import gemini as gemini_generate_shots, generate_shot_image
from db import (save_shot_results, get_project, get_project_shots, get_shot,
               save_shot_image, get_shot_images)

st.set_page_config(layout="wide", page_title="AI Cinematic Shot Suggestions")

# Check authentication
if 'is_authenticated' not in st.session_state or not st.session_state.is_authenticated:
    st.switch_page("pages/login.py")
    st.stop()

# Check if a project is selected
if 'current_project' not in st.session_state:
    st.switch_page("pages/projects.py")
    st.stop()

project = st.session_state.current_project
project_id = project['id']

# Use project-specific session state keys
shots_key = f"shots_{project_id}"
images_key = f"images_{project_id}"
current_shot_id_key = f"current_shot_id_{project_id}"

# Initialize session state for this project if needed
if shots_key not in st.session_state:
    st.session_state[shots_key] = []

if images_key not in st.session_state:
    st.session_state[images_key] = {}

if current_shot_id_key not in st.session_state:
    st.session_state[current_shot_id_key] = None

st.title("🎬 AI-Powered Cinematic Shot Suggestion Tool")
st.subheader(f"Project: {project['name']}")

# 🎨 Apply page-wide CSS
st.markdown("""
    <style>
        .shot-container {
            background-color: #f4f8fb;
            padding: 1.5rem;
            border-radius: 12px;
            margin-bottom: 1.5rem;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.05);
        }
        .shot-title {
            font-size: 20px;
            color: #0a58ca;
            font-weight: bold;
        }
        .shot-description {
            font-size: 16px;
            color: #333333;
        }
        .section-divider {
            margin-top: 2rem;
            margin-bottom: 1rem;
            border-top: 2px solid #dee2e6;
        }
    </style>
""", unsafe_allow_html=True)

# Options
GENRES = ["Drama", "Action", "Comedy", "Romance", "Sci-Fi", "Thriller", "Fantasy", "Horror"]
MOODS = ["Tense", "Happy", "Melancholy", "Excited", "Calm", "Suspenseful", "Romantic"]

# Sidebar
with st.sidebar:
    st.header("🎭 Scene Details")
    scene_description = st.text_area("📝 Enter Scene Description (English or Telugu)", height=150)

    genre = st.selectbox("🎬 Select Genre", GENRES, index=0)
    mood = st.selectbox("🎭 Select Mood", MOODS, index=0)

    num_shots = st.slider("🎞️ Number of Shots", 1, 10, 5)
    model_name = st.selectbox("🎨 Diffusion Model", [
        "CompVis/stable-diffusion-v1-4",
        "runwayml/stable-diffusion-v1-5",
        "dreamlike-art/dreamlike-photoreal-2.0"
    ])
    generate_btn = st.button("🚀 Generate Shot Suggestions")
    
    st.markdown("---")
    if st.button("Back to Projects"):
        # Clear current project and session state
        if 'current_project' in st.session_state:
            del st.session_state.current_project
        
        # Clear other session state variables
        keys_to_reset = ["shots", "images", "current_shot_id"]
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        
        st.switch_page("pages/projects.py")

# Trigger shot generation
if generate_btn and scene_description.strip():
    with st.spinner("Generating shot suggestions..."):
        st.session_state[shots_key] = gemini_generate_shots(
            scene_description, genre, mood, num_shots
        )
        st.session_state[images_key] = {}
        
        # Save shots to database
        if st.session_state[shots_key]:
            shot_data = json.dumps(st.session_state[shots_key])
            shot_id = save_shot_results(
                project['id'], 
                scene_description, 
                genre, 
                mood, 
                model_name, 
                shot_data
            )
            # Store the current shot ID for image saving
            st.session_state[current_shot_id_key] = shot_id

# Layout columns
col1, col2 = st.columns([3, 7])

with col1:
    st.subheader("📜 Scene Description")
    st.write(scene_description if scene_description else "_No scene description provided yet._")

    st.markdown("---")
    st.subheader("⚙️ Settings")
    st.write(f"**Genre:** {genre}")
    st.write(f"**Mood:** {mood}")
    st.write(f"**Shots:** {num_shots}")
    st.write(f"**Model:** `{model_name}`")
    
    st.markdown("---")
    st.subheader("📚 Saved Shot Sets")
    
    # Show saved shots for this project
    saved_shots = get_project_shots(project['id'])
    if not saved_shots:
        st.info("No saved shots for this project yet.")
    else:
        for idx, shot_set in enumerate(saved_shots):
            # When loading history:
            if st.button(f"Shot Set {idx+1}: {shot_set['created_at'][:16]}", key=f"load_{shot_set['id']}"):
                # Load this shot set into the UI
                shot_data = json.loads(shot_set['shot_data'])
                st.session_state[shots_key] = shot_data
                # Get saved images for this shot set
                shot_images = get_shot_images(shot_set['id'])
                # Convert the shot_images dict keys from integers to the format used in your app
                formatted_images = {}
                for shot_num, images in shot_images.items():
                    formatted_images[f"shot_{shot_num}"] = images
                st.session_state[images_key] = formatted_images
                st.session_state[current_shot_id_key] = shot_set['id']
                st.rerun()

with col2:
    st.subheader("🎥 Shot Suggestions and Images")

    # For the display of shots:
    if not st.session_state[shots_key]:
        st.info("Enter scene details and click 'Generate Shot Suggestions' to begin.")
    else:
        for shot in st.session_state[shots_key]:
            shot_num = shot["num"]
            shot_key = f"shot_{shot_num}"
            if shot_key not in st.session_state[images_key]:
                st.session_state[images_key][shot_key] = []
                
            with st.container():
                st.markdown('<div class="shot-container">', unsafe_allow_html=True)

                # 🧠 Shot Title
                st.markdown(f'<div class="shot-title">{shot_num}. {shot["name"]}</div>', unsafe_allow_html=True)

                # 📄 Shot Description (Telugu or English)
                description = shot.get("description_telugu", shot["description"])
                st.markdown(f'<div class="shot-description">{description}</div>', unsafe_allow_html=True)

                # 🖼️ Image Generator
                btn_key = f"img_btn_{shot_num}"
                if st.button("🎨 Generate Image", key=btn_key):
                    with st.spinner(f"Generating image for Shot {shot_num}..."):
                        img = generate_shot_image(
                            scene_description, shot["description"], model_name=model_name
                        )
                        
                        # Add image to session state
                        if shot_key not in st.session_state[images_key]:
                            st.session_state[images_key][shot_key] = []
                        st.session_state[images_key][shot_key].append(img)
                        
                        # Save image to database if we have a shot ID
                        if st.session_state[current_shot_id_key]:
                            save_shot_image(
                                st.session_state[current_shot_id_key], 
                                shot_num, 
                                img
                            )

                # 📸 Display images
                if shot_key in st.session_state[images_key]:
                    for img in st.session_state[images_key][shot_key]:
                        st.image(img, width=220)

                st.markdown('</div>', unsafe_allow_html=True)
