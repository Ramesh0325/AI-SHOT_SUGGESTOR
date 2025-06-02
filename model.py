import re
import torch
from langdetect import detect
from PIL import Image
from google import genai
from diffusers import StableDiffusionPipeline

# Hardcoded API key (replace with your own securely in production)
API_KEY = "AIzaSyDht3f9HNigORJTQsbH1s0sks6zAoF0nDw"
client = genai.Client(api_key=API_KEY)

def detect_language(text: str) -> str:
    try:
        lang = detect(text)
        if lang == "te":  # Telugu ISO code
            return "Telugu"
    except Exception:
        pass
    return "English"

def translate_to_english(text: str) -> str:
    # Translate Telugu to English if needed, else return as is
    if detect_language(text) == "Telugu":
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-05-20",
            contents=f"Translate this Telugu cinematic description to concise English in 1 sentence only:\n\n{text}"
        )
        return response.text.strip()
    return text

def translate_to_telugu(text: str) -> str:
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-05-20",
        contents=f"Translate this English cinematic shot description into concise Telugu (1-2 lines, no explanations):\n\n{text}"
    )
    return response.text.strip()

def gemini(prompt: str, genre: str = "Drama", mood: str = "Tense", num_shots: int = 5):
    # Always work with English internally for stable results
    lang = detect_language(prompt)
    prompt_eng = translate_to_english(prompt) if lang == "Telugu" else prompt.strip()

    full_prompt = (
        f"Scene Description:\n{prompt_eng}\n\n"
        f"Genre: {genre}\n"
        f"Mood: {mood}\n"
        f"Suggest {num_shots} concise cinematic shot descriptions, 1-2 lines each. "
        "Include shot type and brief visual or emotional detail. No explanations."
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=full_prompt
    )

    shots = parse_gemini_response(response.text, max_shots=num_shots)

    # Add Telugu concise translation if original input was Telugu
    if lang == "Telugu":
        for shot in shots:
            shot["description_telugu"] = translate_to_telugu(shot["description"])

    return shots

def parse_gemini_response(text: str, max_shots: int = 5):
    shots = []
    lines = text.strip().split('\n')
    count = 0
    for line in lines:
        clean_line = line.strip()
        if clean_line and not clean_line.lower().startswith("here are"):
            count += 1
            match = re.match(r"^(?:\d+\.\s*)?(.*?shot)?[:\-]?\s*(.*)$", clean_line, re.IGNORECASE)
            name = match.group(1).strip() if match and match.group(1) else f"Shot {count}"
            desc = match.group(2).strip() if match else clean_line
            shots.append({
                "num": count,
                "name": name.capitalize(),
                "description": desc
            })
            if count >= max_shots:
                break
    return shots

# Caching pipeline for performance
@torch.no_grad()
def load_pipeline(model_name: str):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    pipe = StableDiffusionPipeline.from_pretrained(model_name, torch_dtype=dtype)
    return pipe.to(device)

def generate_shot_image(scene_prompt: str, shot_prompt: str, model_name: str = "CompVis/stable-diffusion-v1-4",
                        width: int = 320, height: int = 320, steps: int = 25):
    # Always use English prompt internally for image generation
    prompt_eng = translate_to_english(scene_prompt)
    shot_eng = translate_to_english(shot_prompt)
    full_prompt = f"{prompt_eng}, {shot_eng}"

    pipe = load_pipeline(model_name)
    image = pipe(full_prompt, num_inference_steps=steps, guidance_scale=7.5,
                 height=height, width=width).images[0]
    return image
