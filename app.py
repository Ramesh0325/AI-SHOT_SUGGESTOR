import streamlit as st
from model import gemini as gemini_generate_shots, generate_shot_image

st.set_page_config(layout="wide", page_title="AI Cinematic Shot Suggestions")
st.title("🎬 AI-Powered Cinematic Shot Suggestion Tool")

# Expanded genre & mood lists with defaults
GENRES = ["Drama", "Action", "Comedy", "Romance", "Sci-Fi", "Thriller", "Fantasy", "Horror"]
MOODS = ["Tense", "Happy", "Melancholy", "Excited", "Calm", "Suspenseful", "Romantic"]

with st.sidebar:
    st.header("Scene Details")
    scene_description = st.text_area("Enter Scene Description", height=150)

    genre = st.selectbox("Select Genre", GENRES, index=0)
    mood = st.selectbox("Select Mood", MOODS, index=0)

    num_shots = st.slider("Number of Shots to Generate", 1, 10, 5)
    model_name = st.selectbox("Select Diffusion Model", [
        "CompVis/stable-diffusion-v1-4",
        "runwayml/stable-diffusion-v1-5",
        "dreamlike-art/dreamlike-photoreal-2.0"
    ])
    generate_btn = st.button("Generate Shot Suggestions")

# Session state for shots and images (multiple images per shot)
if "shots" not in st.session_state:
    st.session_state.shots = []

if "images" not in st.session_state:
    # Dict key = shot_num, value = list of images
    st.session_state.images = {}

if generate_btn and scene_description.strip():
    with st.spinner("Generating shot suggestions..."):
        st.session_state.shots = gemini_generate_shots(
            scene_description, genre, mood, num_shots
        )
        # Reset images when new shots generated
        st.session_state.images = {}

col1, col2 = st.columns([3, 7])

with col1:
    st.subheader("Scene Description")
    st.write(scene_description if scene_description else "_No scene description yet._")

    st.markdown("---")
    st.subheader("Settings")
    st.write(f"**Genre:** {genre}")
    st.write(f"**Mood:** {mood}")
    st.write(f"**Number of Shots:** {num_shots}")
    st.write(f"**Diffusion Model:** {model_name}")

with col2:
    st.subheader("Shot Suggestions and Images")

    if not st.session_state.shots:
        st.info("No shot suggestions yet. Enter scene details and click Generate.")
    else:
        for shot in st.session_state.shots:
            shot_num = shot["num"]
            shot_key = f"shot_{shot_num}"
            if shot_key not in st.session_state.images:
                st.session_state.images[shot_key] = []

            cols = st.columns([6, 2])
            with cols[0]:
                st.markdown(f"### {shot_num}. {shot['name']}")
                # Show Telugu description if available, else English
                if "description_telugu" in shot:
                    st.markdown(f"**{shot['description_telugu']}**")
                else:
                    st.markdown(f"**{shot['description']}**")
                st.markdown("---")

            with cols[1]:
                btn_key = f"img_btn_{shot_num}"
                if st.button("Generate Image", key=btn_key):
                    with st.spinner(f"Generating image for Shot {shot_num}..."):
                        img = generate_shot_image(
                            scene_description, shot["description"], model_name=model_name
                        )
                        st.session_state.images[shot_key].append(img)

                # Display all generated images for this shot
                for img in st.session_state.images[shot_key]:
                    st.image(img, width=200)
