import streamlit as st
import json
import os
from model import gemini as gemini_generate_shots, generate_shot_image
from db import save_shot_results, get_project, get_project_shots, get_shot

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
user = st.session_state.user

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
        # Clear current project and go back to projects page
        if 'current_project' in st.session_state:
            del st.session_state.current_project
        st.switch_page("pages/projects.py")

# Session State
if "shots" not in st.session_state:
    st.session_state.shots = []

if "images" not in st.session_state:
    st.session_state.images = {}

# Trigger shot generation
if generate_btn and scene_description.strip():
    with st.spinner("Generating shot suggestions..."):
        st.session_state.shots = gemini_generate_shots(
            scene_description, genre, mood, num_shots
        )
        st.session_state.images = {}
        
        # Save shots to database
        if st.session_state.shots:
            shot_data = json.dumps(st.session_state.shots)
            save_shot_results(
                project['id'], 
                scene_description, 
                genre, 
                mood, 
                model_name, 
                shot_data
            )

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
            if st.button(f"Shot Set {idx+1}: {shot_set['created_at'][:16]}", key=f"load_{shot_set['id']}"):
                # Load this shot set into the UI
                shot_data = json.loads(shot_set['shot_data'])
                st.session_state.shots = shot_data
                st.session_state.images = {}
                st.rerun()

with col2:
    st.subheader("🎥 Shot Suggestions and Images")

    if not st.session_state.shots:
        st.info("Enter scene details and click 'Generate Shot Suggestions' to begin.")
    else:
        for shot in st.session_state.shots:
            shot_num = shot["num"]
            shot_key = f"shot_{shot_num}"
            if shot_key not in st.session_state.images:
                st.session_state.images[shot_key] = []

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
                        st.session_state.images[shot_key].append(img)

                # 📸 Display images
                for img in st.session_state.images[shot_key]:
                    st.image(img, width=220)

                st.markdown('</div>', unsafe_allow_html=True)
