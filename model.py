import re
import torch
from langdetect import detect
from PIL import Image
from google import genai
from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
from diffusers import ControlNetModel, StableDiffusionControlNetPipeline
from diffusers.utils import load_image
import numpy as np

try:
    import cv2
except ImportError:
    raise ImportError("OpenCV (cv2) is required for ControlNet reference image preprocessing. Please install it with 'pip install opencv-python-headless' and restart your app.")

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
    lang = detect_language(prompt)
    prompt_eng = translate_to_english(prompt) if lang == "Telugu" else prompt.strip()

    # Make the prompt strict and clear for Gemini
    full_prompt = (
        f"Scene Description:\n{prompt_eng}\n\n"
        f"Suggest {num_shots} cinematic shot suggestions as a numbered list. "
        "Each line must be in the format: [Shot Name]: [1-sentence description]. "
        "Do not include any other text, explanations, or greetings. Only output the list."
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=full_prompt
    )

    shots = parse_gemini_response(response.text, max_shots=num_shots)

    if lang == "Telugu":
        for shot in shots:
            shot["description_telugu"] = translate_to_telugu(shot["description"])

    return shots

def parse_gemini_response(text: str, max_shots: int = 5):
    shots = []
    lines = text.strip().split('\n')
    count = 0
    for line in lines:
        line = line.strip()
        # Skip lines that are not actual shot suggestions
        if not line:
            continue
        if line.lower().startswith("here are"):
            continue
        if line.lower().startswith("genre"):
            continue
        if line.lower().startswith("mood"):
            continue
        if line.lower().startswith(","):
            continue
        if line.lower() in {"okay", "ok"}:
            continue
        if re.match(r"^\d+\.?$", line):  # skip lines that are just numbers
            continue
        # Only accept lines that match the strict format: [number]. [Shot Name]: [Description]
        match = re.match(r"^\d+\.\s*([^:]+):\s*(.+)$", line)
        if match:
            name = match.group(1).strip().title()
            description = match.group(2).strip()
        else:
            # fallback: skip lines that don't match the strict format
            continue
        count += 1
        shots.append({
            "num": count,
            "name": name,
            "description": description
        })
        if count >= max_shots:
            break
    return shots

@torch.no_grad()
def load_pipeline(model_name: str):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    pipe = StableDiffusionPipeline.from_pretrained(model_name, torch_dtype=dtype)
    return pipe.to(device)

def explain_shot(scene_prompt: str, shot_prompt: str) -> str:
    """
    Generate a concise, cinematic explanation of the shot, combining scene and shot prompts.
    """
    prompt_eng = translate_to_english(scene_prompt)
    shot_eng = translate_to_english(shot_prompt)
    explanation = (
        f"This shot captures: {shot_eng}. "
        f"Scene context: {prompt_eng}. "
        "Visual style: cinematic, high quality, with strong composition and mood as described."
    )
    return explanation

def generate_shot_image(
    scene_prompt: str,
    shot_prompt: str = None,
    model_name: str = "runwayml/stable-diffusion-v1-5",
    width: int = 512,
    height: int = 512,
    steps: int = 25,
    reference_images=None,  # List of reference images
    use_controlnet=True,  # Always use ControlNet for best accuracy
    strength=1.0,  # ControlNet uses conditioning_scale instead
    controlnet_conditioning_scale: float = 1.0,  # User control for structure adherence
    guidance_scale: float = 7.5  # User control for prompt adherence
):
    """
    Generate a cinematic shot image using the blended canny edges of all reference images.
    Returns a list with a single image.
    The prompt is used for both shot suggestion and image generation.
    """
    prompt_eng = translate_to_english(scene_prompt)
    full_prompt = prompt_eng

    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    if reference_images and len(reference_images) > 0:
        from diffusers import ControlNetModel, StableDiffusionControlNetPipeline
        controlnet = ControlNetModel.from_pretrained(
            "lllyasviel/sd-controlnet-canny", torch_dtype=dtype
        )
        pipe = StableDiffusionControlNetPipeline.from_pretrained(
            model_name,
            controlnet=controlnet,
            torch_dtype=dtype
        ).to(device)
        pipe.safety_checker = None
        # Use only the first reference image for canny edge (robust ControlNet workflow)
        ref_img = reference_images[0]
        if hasattr(ref_img, "read"):
            ref_img = Image.open(ref_img).convert("RGB")
        ref_img = ref_img.resize((512, 512))
        np_img = np.array(ref_img)
        low_threshold, high_threshold = 100, 200
        canny = cv2.Canny(np_img, low_threshold, high_threshold)
        canny = np.stack([canny] * 3, axis=-1)
        canny_img = Image.fromarray(canny)
        img = pipe(
            prompt=full_prompt,
            image=canny_img,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            controlnet_conditioning_scale=controlnet_conditioning_scale,
            width=512,
            height=512
        ).images[0]
        return [img]
    raise ValueError("At least one reference image is required for generation.")
