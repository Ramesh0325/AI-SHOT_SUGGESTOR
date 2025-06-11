import streamlit as st
import json
import os
from model import gemini as gemini_generate_shots, generate_shot_image
from db import (save_shot_results, get_project, get_project_shots, get_shot,
               save_shot_image, get_shot_images, delete_shot)

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

    # Reference image uploader (allow only one image)
    reference_images = st.file_uploader(
        "📷 Upload a reference image (optional)",
        type=["png", "jpg", "jpeg"],
        accept_multiple_files=False,
        key="reference_images"
    )
    if reference_images:
        st.write("1 image uploaded.")
        reference_images = [reference_images]  # Always a list for downstream compatibility
    else:
        reference_images = []
    st.session_state[f"reference_images_{project_id}"] = reference_images

    # Show uploaded reference image as visible frame
    if reference_images:
        st.write("**Reference Image Preview:**")
        st.image(reference_images[0], caption="Ref 1", use_container_width=True)

    # Re-enable text prompt area
    user_prompt = st.text_area(
        "📝 Enter a detailed description of the shot you want (e.g., 'A dramatic close-up of a woman under moody lighting, cinematic, 35mm film look')",
        value="",
        height=120
    )

    # Remove genre and mood options for clarity
    num_shots = st.slider("🎞️ Number of Shots", 1, 10, 5)
    model_name = st.selectbox("🎨 Diffusion Model", [
        "CompVis/stable-diffusion-v1-4",
        "runwayml/stable-diffusion-v1-5",
        "dreamlike-art/dreamlike-photoreal-2.0"
    ], index=2)
    generate_btn = st.button("🚀 Generate Shot Suggestions")
    st.markdown("---")
    
    # Add img2img strength slider
    img2img_strength = st.slider("Image-to-Image Strength", 0.2, 0.9, 0.4, 0.05)
    # Add ControlNet conditioning scale slider
    controlnet_conditioning_scale = st.slider("ControlNet Conditioning Scale (structure adherence)", 0.1, 1.0, 1.0, 0.05)
    # Add guidance scale slider
    guidance_scale = st.slider("Guidance Scale (prompt adherence)", 1.0, 15.0, 7.5, 0.5)
    
    # Show current metadata if available
    if st.session_state[metadata_key]:
        st.write("### Current Settings")
        st.markdown(f"**Scene:** {st.session_state[metadata_key].get('scene_description', '')[:50]}..." if len(st.session_state[metadata_key].get('scene_description', '')) > 50 else f"**Scene:** {st.session_state[metadata_key].get('scene_description', '')}")
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
if generate_btn and user_prompt.strip():
    # Use the prompt exactly as entered by the user, no augmentation
    enhanced_prompt = user_prompt.strip()
    with st.spinner("Generating shot suggestions..."):
        st.session_state[shots_key] = gemini_generate_shots(
            enhanced_prompt, "", "", num_shots  # Only use user prompt
        )
        st.session_state[images_key] = {}
        # Save the reference image (if any) in the metadata when saving shots
        metadata = {
            "scene_description": enhanced_prompt,
            "num_shots": num_shots,
            "model_name": model_name,
            "reference_image": None
        }
        if reference_images:
            # Store the reference image as base64 for persistence
            from db import image_to_base64
            # Convert UploadedFile to PIL Image before encoding
            from PIL import Image
            import io
            uploaded_file = reference_images[0]
            if hasattr(uploaded_file, 'read'):
                pil_img = Image.open(uploaded_file).convert("RGB")
            else:
                pil_img = uploaded_file
            metadata["reference_image"] = image_to_base64(pil_img)
        st.session_state[metadata_key] = metadata
        if st.session_state[shots_key]:
            shot_data = json.dumps(st.session_state[shots_key])
            metadata_json = json.dumps(metadata)
            shot_id = save_shot_results(
                project['id'],
                enhanced_prompt,
                "",  # genre removed
                "",  # mood removed
                model_name,
                shot_data,
                metadata_json
            )
            st.session_state[current_shot_id_key] = shot_id

# Layout columns
col1, col2 = st.columns([3, 7])

with col1:
    st.subheader("📜 Scene Description")
    if st.session_state[metadata_key].get('scene_description'):
        st.write(st.session_state[metadata_key].get('scene_description'))
    else:
        st.write(user_prompt if user_prompt else "_No scene description provided yet._")

    st.markdown("---")
    st.subheader("⚙️ Settings")
    if st.session_state[metadata_key]:
        st.write(f"**Shots:** {st.session_state[metadata_key].get('num_shots', num_shots)}")
        st.write(f"**Model:** `{st.session_state[metadata_key].get('model_name', model_name)}`")
    else:
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
            with st.expander(f"Shot Set {idx+1}", expanded=False):
                # Display metadata in a nice format
                st.markdown('<div class="metadata-box">', unsafe_allow_html=True)
                st.write("**Scene:**")
                st.write(metadata.get('scene_description', shot_set['scene_description']))
                st.markdown('<hr style="margin: 5px 0;">', unsafe_allow_html=True)
                st.write(f"**Shots:** {metadata.get('num_shots', 'N/A')}")
                st.write(f"**Model:** {metadata.get('model_name', shot_set['model_name'])}")
                st.write(f"**Created:** {shot_set['created_at'][:16]}")
                # Show reference image if present
                if metadata.get('reference_image'):
                    from db import base64_to_image
                    st.image(base64_to_image(metadata['reference_image']), caption="Reference Image", use_container_width=True)
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
                    # Delete this shot set and its images from the database
                    delete_shot(shot_set['id'])
                    st.success("Shot set deleted.")
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
                    ref_imgs = st.session_state.get(f"reference_images_{project_id}", [])
                    # Use the prompt exactly as entered by the user, no augmentation
                    enhanced_prompt = user_prompt.strip()
                    if ref_imgs:
                        with st.spinner(f"Preprocessing reference image(s) and generating for Shot {shot_num}..."):
                            current_model = st.session_state[metadata_key].get('model_name', model_name)
                            results = generate_shot_image(
                                enhanced_prompt,
                                enhanced_prompt,
                                model_name=current_model,
                                reference_images=ref_imgs,
                                use_controlnet=True,
                                strength=img2img_strength,
                                controlnet_conditioning_scale=controlnet_conditioning_scale,
                                guidance_scale=guidance_scale
                            )
                        if shot_key not in st.session_state[images_key]:
                            st.session_state[images_key][shot_key] = []
                        st.session_state[images_key][shot_key].extend(results)
                        if st.session_state[current_shot_id_key]:
                            # Save all generated images (now just Image objects, not tuples)
                            for img in results:
                                save_shot_image(
                                    st.session_state[current_shot_id_key],
                                    shot_num,
                                    img
                                )
                        st.rerun()
                    else:
                        with st.spinner(f"Generating image for Shot {shot_num}..."):
                            current_model = st.session_state[metadata_key].get('model_name', model_name)
                            results = generate_shot_image(
                                enhanced_prompt,
                                enhanced_prompt,
                                model_name=current_model,
                                reference_images=None,
                                use_controlnet=False,
                                strength=img2img_strength,
                                controlnet_conditioning_scale=controlnet_conditioning_scale,
                                guidance_scale=guidance_scale
                            )
                        if shot_key not in st.session_state[images_key]:
                            st.session_state[images_key][shot_key] = []
                        st.session_state[images_key][shot_key].extend(results)
                        if st.session_state[current_shot_id_key]:
                            # Save all generated images (now just Image objects, not tuples)
                            for img in results:
                                save_shot_image(
                                    st.session_state[current_shot_id_key],
                                    shot_num,
                                    img
                                )
                        st.rerun()
                # 📸 Display images
                if shot_key in st.session_state[images_key]:
                    imgs_and_expls = st.session_state[images_key][shot_key]
                    if imgs_and_expls:
                        # Only show the latest generated image for this shot
                        latest = imgs_and_expls[-1]
                        # Handle both (img, explanation) tuple and just img
                        if isinstance(latest, tuple) and len(latest) == 2:
                            img, _ = latest
                        else:
                            img = latest
                        st.image(img, use_container_width=True)

                st.markdown('</div>', unsafe_allow_html=True)
