import streamlit as st
from model import gemini as gemini_generate_shots, generate_shot_image, translate_to_english

st.set_page_config(layout="wide", page_title="AI Cinematic Shot Suggestions")
st.title("🎬 AI-Powered Cinematic Shot Suggestion Tool")

# Sidebar for input
with st.sidebar:
    st.header("Scene Details")
    language = st.selectbox("Scene Description Language", options=["English", "Telugu"], index=0)
    scene_description = st.text_area("Enter Scene Description", height=150)
    genre = st.selectbox("Select Genre", ["Drama", "Action", "Comedy", "Romance", "Sci-Fi"])
    mood = st.selectbox("Select Mood", ["Tense", "Happy", "Melancholy", "Excited", "Calm"])
    num_shots = st.slider("Number of Shots to Generate", 1, 10, 5)
    model_name = st.selectbox("Select Diffusion Model", [
        "CompVis/stable-diffusion-v1-4",
        "runwayml/stable-diffusion-v1-5",
        "dreamlike-art/dreamlike-photoreal-2.0"
    ])

    generate_btn = st.button("Generate Shot Suggestions")

# Session state
if "shots" not in st.session_state:
    st.session_state.shots = []
if "images" not in st.session_state:
    st.session_state.images = {}

if generate_btn:
    if not scene_description.strip():
        st.sidebar.error("Please enter a scene description.")
    else:
        with st.spinner("Generating shot suggestions..."):
            st.session_state.shots = gemini_generate_shots(
                scene_description, genre, mood, language, num_shots
            )

# Layout columns
col1, col2 = st.columns([3, 7])

with col1:
    st.subheader("Scene Description")
    st.write(scene_description if scene_description else "_No scene description yet._")
    st.markdown("---")
    st.subheader("Settings")
    st.write(f"**Language:** {language}")
    st.write(f"**Genre:** {genre}")
    st.write(f"**Mood:** {mood}")
    st.write(f"**Number of Shots:** {num_shots}")
    st.write(f"**Diffusion Model:** {model_name}")

with col2:
    st.subheader("Shot Suggestions and Images")

    if not st.session_state.shots:
        st.info("No shot suggestions yet. Fill in the scene and click Generate.")
    else:
        for shot in st.session_state.shots:
            shot_key = f"shot_{shot['num']}"
            if shot_key not in st.session_state.images:
                st.session_state.images[shot_key] = None

            cols = st.columns([6, 2])
            with cols[0]:
                st.markdown(f"### {shot['num']}. {shot['name']}")
                if language.lower() == "telugu" and "description_telugu" in shot:
                    st.markdown(f"**{shot['description_telugu']}**")
                else:
                    st.markdown(f"**{shot['description']}**")
                st.markdown("---")

            with cols[1]:
                btn_key = f"img_btn_{shot['num']}"
                if st.button("Generate Image", key=btn_key):
                    with st.spinner(f"Generating image for Shot {shot['num']}..."):
                        desc_for_img = (
                            translate_to_english(shot["description"], language)
                            if language.lower() == "telugu"
                            else shot["description"]
                        )
                        img = generate_shot_image(
                            scene_description, desc_for_img,
                            language=language, model_name=model_name
                        )
                        st.session_state.images[shot_key] = img

                if st.session_state.images[shot_key] is not None:
                    st.image(st.session_state.images[shot_key], width=200)
