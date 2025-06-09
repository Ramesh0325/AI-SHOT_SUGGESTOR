# 🎬 AI-Powered Cinematic Shot Suggestion Tool

This project is an intelligent assistant that analyzes cinematic scene descriptions and generates shot suggestions, complete with AI-generated images. It's powered by **Google Gemini** for natural language understanding and **Stable Diffusion** for image synthesis, all presented via a user-friendly **Streamlit** interface.

---

## ✨ Features

- 🔤 **Bilingual Input Support**: Accepts scene descriptions in **English** or **Telugu**.
- 🎭 **Genre & Mood Control**: Choose from Drama, Action, Comedy, Romance, Sci-Fi and moods like Tense, Happy, etc.
- 🎬 **AI Shot Suggestions**: Generates camera shots like Wide Shot, Close-Up, Overhead, Underwater, etc., with rich visual storytelling.
- 🖼️ **Image Generation**: Use Stable Diffusion models to create visual representations of the shots.
- 🔁 **Telugu Translation**: Automatic translation of shot descriptions for Telugu users.
- 🧠 **Shot Ordering**: Ensures output shots follow logical story progression.

---

## 🏗️ Project Structure

```
cinematic-shot-suggestion/
├── ui.py                # Streamlit front-end UI
├── model.py             # Core logic for Gemini & Stable Diffusion integration
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
streamlit run ui.py
```

Then open `http://localhost:8501` in your browser.

---

## 🖼️ Supported Image Models

You can switch between different Stable Diffusion models in `model.py`:

- `CompVis/stable-diffusion-v1-4`
- `runwayml/stable-diffusion-v1-5`
- `dreamlike-art/dreamlike-photoreal-2.0`

---

## 🧪 Example Usage

**Input**:
```
Scene: People were traveling to London by ship when suddenly a large tsunami struck.
Genre: Drama
Mood: Tense
Language: English
Shots: 3
```

**AI Output**:
1. **WIDE SHOT** – A ship dwarfed by a monstrous tsunami approaching from the horizon.
2. **CLOSE-UP** – A terrified passenger grips the railing, water splashing on her face.
3. **UNDERWATER SHOT** – Wreckage and floating debris engulfed in turbulent currents.

> You can click "Generate Image" beside each shot to visualize it.

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

---

## 📄 License

MIT License — use freely with attribution.

---

## 📬 Contact

For suggestions or feedback, contact: [rameshreddi146@gmail.com]