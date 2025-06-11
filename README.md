# 🎬 AI-Powered Cinematic Shot Suggestion Tool

This project is an intelligent assistant that analyzes cinematic scene descriptions and generates shot suggestions, complete with AI-generated images. It's powered by **Google Gemini** for natural language understanding and **Stable Diffusion** for image synthesis, all presented via a user-friendly **Streamlit** interface.

---

## ✨ Features

- 🔤 **Bilingual Input Support**: Accepts scene descriptions in **English** or **Telugu**.
- 🎬 **AI Shot Suggestions**: Generates camera shots like Wide Shot, Close-Up, Overhead, Underwater, etc., with rich visual storytelling.
- 🖼️ **Image Generation**: Use Stable Diffusion models to create visual representations of the shots, with or without a reference image.
- 📷 **Reference Image Support**: Optionally upload a single reference image to guide the structure of generated images (using ControlNet/canny). If no image is provided, images are generated purely from the prompt.
- 🔁 **Telugu Translation**: Automatic translation of shot descriptions for Telugu users.
- 🧠 **Shot Ordering**: Ensures output shots follow logical story progression.
- 💾 **Save & Manage Shots**: Save, load, and delete shot sets, with reference image stored in metadata.

---

## 🏗️ Project Structure

```
ai-shot-suggestor/
├── app.py               # Streamlit main app (UI, workflow)
├── model.py             # Core logic for Gemini & Stable Diffusion integration
├── db.py                # Database logic for users, projects, shots, images
├── requirements.txt     # Required Python packages
├── README.md            # Project documentation
```

---

## 📦 Installation

1. **Clone the repository**
```bash
git clone https://github.com/your-username/ai-shot-suggestor.git
cd ai-shot-suggestor
```

2. **Create and activate a virtual environment**
```bash
python -m venv venv
# Activate the environment:
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set your Gemini API key**

In `model.py`, replace the line:
```python
API_KEY = "your-api-key"
```
with your actual Gemini API key from [Google AI Studio](https://makersuite.google.com/).

> 🔐 For production, use environment variables instead of hardcoding the key.

---

## ▶️ Run the App

```bash
streamlit run app.py
```

Then open `http://localhost:8501` in your browser.

---

## 🖼️ Supported Image Models

You can switch between different Stable Diffusion models in the app UI:

- `CompVis/stable-diffusion-v1-4`
- `runwayml/stable-diffusion-v1-5`
- `dreamlike-art/dreamlike-photoreal-2.0`

---

## 🧪 Example Usage

**Input**:
```
Scene: People were traveling to London by ship when suddenly a large tsunami struck.
Shots: 3
Language: English
```

**AI Output**:
1. **WIDE SHOT** – A ship dwarfed by a monstrous tsunami approaching from the horizon.
2. **CLOSE-UP** – A terrified passenger grips the railing, water splashing on her face.
3. **UNDERWATER SHOT** – Wreckage and floating debris engulfed in turbulent currents.

> You can optionally upload a reference image to guide the generated visuals. If no image is uploaded, the AI will generate images based only on your prompt.

---

## 🧰 Built With

- [Streamlit](https://streamlit.io/) – For web UI
- [Google Gemini (Generative AI)](https://ai.google.dev) – For text understanding
- [Diffusers](https://github.com/huggingface/diffusers) – Stable Diffusion image generation
- [Torch](https://pytorch.org/)
- [PIL (Pillow)](https://python-pillow.org/)

---

## 📌 Notes

- This project is intended for **educational, creative, and experimental** purposes.
- Do not share your API key publicly.
- Best results are achieved with meaningful, vivid scene descriptions.
- Only one reference image is supported per shot set. If multiple images are uploaded, only the first is used.
- Genre and mood selection are not required in the current workflow.

---

## 📄 License

MIT License — use freely with attribution.

---

## 📬 Contact

For suggestions or feedback, contact: [rameshreddi146@gmail.com]