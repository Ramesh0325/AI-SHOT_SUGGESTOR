import re
from google import genai
from diffusers import StableDiffusionPipeline
from PIL import Image
import torch
import streamlit as st

# Hardcoded API key (replace with your actual key or better use env vars)
API_KEY = "AIzaSyAO7OYzRski9LnFLbkToOyFerwLIJsB154"
client = genai.Client(api_key=API_KEY)

def translate_to_english(text: str, src_lang: str) -> str:
    if src_lang.lower() == "telugu":
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Translate this Telugu cinematic description to English in one sentence only:\n\n{text}"
        )
        return response.text.strip()
    return text

def translate_to_telugu(text: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=f"Translate the following short English cinematic shot description to concise Telugu:\n\n{text}"
    )
    return response.text.strip()

def gemini(prompt: str, genre: str = "Drama", mood: str = "Tense", language: str = "English", num_shots: int = 5) -> list:
    original_prompt = prompt.strip()

    if language.lower() == "telugu":
        prompt = translate_to_english(original_prompt, src_lang="Telugu")

    full_prompt = (
        f"Scene Description:\n{prompt}\n\n"
        f"Genre: {genre}\n"
        f"Mood: {mood}\n"
        f"Suggest {num_shots} cinematic shot descriptions in 1–2 lines each. Include the shot type and a brief visual/emotional detail. No explanation, no options."
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=full_prompt
    )
    suggestions_en = parse_gemini_response(response.text, max_shots=num_shots)

    if language.lower() == "telugu":
        for s in suggestions_en:
            s["description_telugu"] = translate_to_telugu(s["description"])

    return suggestions_en

def parse_gemini_response(text: str, max_shots: int = 5) -> list:
    suggestions = []
    lines = text.strip().split('\n')
    count = 0
    for line in lines:
        clean_line = line.strip()
        if clean_line and not clean_line.lower().startswith("here are"):
            count += 1
            match = re.match(r"^(.*?shot)[:\-]?\s*(.*)$", clean_line, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                desc = match.group(2).strip()
            else:
                name = f"Shot {count}"
                desc = clean_line
            suggestions.append({"num": count, "name": name.capitalize(), "description": desc})
            if count >= max_shots:
                break
    return suggestions

@st.cache_resource(show_spinner=False)
def load_pipeline(model_name):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    pipe = StableDiffusionPipeline.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32
    )
    pipe = pipe.to(device)
    return pipe

def generate_shot_image(
    scene_prompt: str,
    shot_prompt: str,
    language: str = "English",
    model_name: str = "CompVis/stable-diffusion-v1-4",
    width: int = 320,
    height: int = 320,
    steps: int = 25
) -> Image.Image:
    if language.lower() == "telugu":
        scene_prompt = translate_to_english(scene_prompt, "Telugu")
        shot_prompt = translate_to_english(shot_prompt, "Telugu")

    full_prompt = f"{scene_prompt.strip()}, {shot_prompt.strip()}"
    pipe = load_pipeline(model_name)
    image = pipe(
        full_prompt,
        num_inference_steps=steps,
        guidance_scale=7.5,
        height=height,
        width=width
    ).images[0]
    return image