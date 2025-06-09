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
metadata_key = f"metadata_{project_id}"  # Add metadata key

# Initialize session state for this project if needed
if shots_key not in st.session_state:
    st.session_state[shots_key] = []

if images_key not in st.session_state:
    st.session_state[images_key] = {}

if current_shot_id_key not in st.session_state:
    st.session_state[current_shot_id_key] = None

if metadata_key not in st.session_state:  # Initialize metadata
    st.session_state[metadata_key] = {}

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
        .metadata-box {
            background-color: #f9f9f9;
            border-left: 3px solid #0a58ca;
            padding: 10px 15px;
            margin-bottom: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Options
GENRES = ["Drama", "Action", "Comedy", "Romance", "Sci-Fi", "Thriller", "Fantasy", "Horror"]
MOODS = ["Tense", "Happy", "Melancholy", "Excited", "Calm", "Suspenseful", "Romantic"]

# Sidebar
with st.sidebar:
    st.header("🎭 Scene Details")
    
    # Use stored metadata for defaults if available
    default_desc = st.session_state[metadata_key].get('scene_description', '')
    default_genre_idx = 0
    if 'genre' in st.session_state[metadata_key]:
        try:
            default_genre_idx = GENRES.index(st.session_state[metadata_key]['genre'])
        except ValueError:
            default_genre_idx = 0
            
    default_mood_idx = 0
    if 'mood' in st.session_state[metadata_key]:
        try:
            default_mood_idx = MOODS.index(st.session_state[metadata_key]['mood'])
        except ValueError:
            default_mood_idx = 0
            
    default_shots = st.session_state[metadata_key].get('num_shots', 5)
    default_model = st.session_state[metadata_key].get('model_name', "dreamlike-art/dreamlike-photoreal-2.0")
    
    scene_description = st.text_area("📝 Enter Scene Description (English or Telugu)", 
                                    value=default_desc, 
                                    height=150)

    genre = st.selectbox("🎬 Select Genre", GENRES, index=default_genre_idx)
    mood = st.selectbox("🎭 Select Mood", MOODS, index=default_mood_idx)

    num_shots = st.slider("🎞️ Number of Shots", 1, 10, default_shots)
    model_name = st.selectbox("🎨 Diffusion Model", [
        "CompVis/stable-diffusion-v1-4",
        "runwayml/stable-diffusion-v1-5",
        "dreamlike-art/dreamlike-photoreal-2.0"
    ], index=0 if default_model not in ["CompVis/stable-diffusion-v1-4", "runwayml/stable-diffusion-v1-5", "dreamlike-art/dreamlike-photoreal-2.0"] else ["CompVis/stable-diffusion-v1-4", "runwayml/stable-diffusion-v1-5", "dreamlike-art/dreamlike-photoreal-2.0"].index(default_model))
    
    generate_btn = st.button("🚀 Generate Shot Suggestions")
    
    st.markdown("---")
    
    # Show current metadata if available
    if st.session_state[metadata_key]:
        st.write("### Current Settings")
        st.markdown(f"**Scene:** {st.session_state[metadata_key].get('scene_description', '')[:50]}..." if len(st.session_state[metadata_key].get('scene_description', '')) > 50 else f"**Scene:** {st.session_state[metadata_key].get('scene_description', '')}")
        st.write(f"**Genre:** {st.session_state[metadata_key].get('genre', '')}")
        st.write(f"**Mood:** {st.session_state[metadata_key].get('mood', '')}")
        st.write(f"**Shots:** {st.session_state[metadata_key].get('num_shots', '')}")
        st.write(f"**Model:** {st.session_state[metadata_key].get('model_name', '')}")
    
    if st.button("Back to Projects"):
        # Clear current project and session state
        if 'current_project' in st.session_state:
            del st.session_state.current_project
        
        # Clear other session state variables
        project_keys = [key for key in st.session_state.keys() if key.startswith(f"shots_") or 
                        key.startswith(f"images_") or 
                        key.startswith(f"current_shot_id_") or
                        key.startswith(f"metadata_")]
        for key in project_keys:
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
        
        # Create and store metadata
        metadata = {
            "scene_description": scene_description,
            "genre": genre,
            "mood": mood,
            "num_shots": num_shots,
            "model_name": model_name
        }
        st.session_state[metadata_key] = metadata
        
        # Save shots to database
        if st.session_state[shots_key]:
            shot_data = json.dumps(st.session_state[shots_key])
            metadata_json = json.dumps(metadata)
            shot_id = save_shot_results(
                project['id'], 
                scene_description, 
                genre, 
                mood, 
                model_name, 
                shot_data,
                metadata_json  # Pass metadata as JSON string
            )
            # Store the current shot ID for image saving
            st.session_state[current_shot_id_key] = shot_id

# Layout columns
col1, col2 = st.columns([3, 7])

with col1:
    st.subheader("📜 Scene Description")
    if st.session_state[metadata_key].get('scene_description'):
        st.write(st.session_state[metadata_key].get('scene_description'))
    else:
        st.write(scene_description if scene_description else "_No scene description provided yet._")

    st.markdown("---")
    st.subheader("⚙️ Settings")
    if st.session_state[metadata_key]:
        st.write(f"**Genre:** {st.session_state[metadata_key].get('genre', genre)}")
        st.write(f"**Mood:** {st.session_state[metadata_key].get('mood', mood)}")
        st.write(f"**Shots:** {st.session_state[metadata_key].get('num_shots', num_shots)}")
        st.write(f"**Model:** `{st.session_state[metadata_key].get('model_name', model_name)}`")
    else:
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
            # Extract metadata if available
            metadata = {}
            if 'metadata' in shot_set and shot_set['metadata']:
                try:
                    metadata = json.loads(shot_set['metadata'])
                except:
                    # If metadata is malformed, create minimal metadata
                    metadata = {
                        "genre": shot_set['genre'],
                        "mood": shot_set['mood'],
                        "model_name": shot_set['model_name'],
                        "scene_description": shot_set['scene_description'][:100]
                    }
            
            # Create an expander for each shot set with some metadata preview
            with st.expander(f"Shot Set {idx+1} - {metadata.get('genre', shot_set['genre'])}/{metadata.get('mood', shot_set['mood'])}", expanded=False):
                # Display metadata in a nice format
                st.markdown('<div class="metadata-box">', unsafe_allow_html=True)
                st.write("**Scene:**")
                st.write(metadata.get('scene_description', shot_set['scene_description']))
                st.markdown('<hr style="margin: 5px 0;">', unsafe_allow_html=True)
                st.write(f"**Genre:** {metadata.get('genre', shot_set['genre'])}")
                st.write(f"**Mood:** {metadata.get('mood', shot_set['mood'])}")
                st.write(f"**Shots:** {metadata.get('num_shots', 'N/A')}")
                st.write(f"**Model:** {metadata.get('model_name', shot_set['model_name'])}")
                st.write(f"**Created:** {shot_set['created_at'][:16]}")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Load button
                if st.button("📋 Load This Set", key=f"load_{shot_set['id']}"):
                    # Load this shot set into the UI
                    shot_data = json.loads(shot_set['shot_data'])
                    st.session_state[shots_key] = shot_data
                    
                    # Store the metadata in session state
                    st.session_state[metadata_key] = metadata
                    
                    # Get saved images for this shot set
                    shot_images = get_shot_images(shot_set['id'])
                    # Convert the shot_images dict keys from integers to the format used in your app
                    formatted_images = {}
                    for shot_num, images in shot_images.items():
                        formatted_images[f"shot_{shot_num}"] = images
                    st.session_state[images_key] = formatted_images
                    st.session_state[current_shot_id_key] = shot_set['id']
                    st.rerun()
                
                # Delete button
                if st.button("🗑️ Delete", key=f"delete_{shot_set['id']}"):
                    # Add your delete logic here
                    pass

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
                        # Use scene description from metadata if available
                        current_scene = st.session_state[metadata_key].get('scene_description', scene_description)
                        current_model = st.session_state[metadata_key].get('model_name', model_name)
                        
                        img = generate_shot_image(
                            current_scene, 
                            shot["description"], 
                            model_name=current_model
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
