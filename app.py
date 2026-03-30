import os
import json
import shutil
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import gradio as gr
from TTS.api import TTS
import torch
import tempfile
import subprocess

app = FastAPI(title="TTS by Keep")

os.makedirs("voices", exist_ok=True)

# Load TTS model (CPU for Railway)
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)

# Simple admin password - CHANGE THIS immediately after first deploy!
ADMIN_PASSWORD = "keepadmin123"   # ← Change to your strong password

CHARACTERS_FILE = "characters.json"
if not os.path.exists(CHARACTERS_FILE):
    with open(CHARACTERS_FILE, "w") as f:
        json.dump({}, f)

def load_characters():
    with open(CHARACTERS_FILE, "r") as f:
        return json.load(f)

def save_characters(chars):
    with open(CHARACTERS_FILE, "w") as f:
        json.dump(chars, f, indent=2)

# ====================== PUBLIC FRONTEND ======================
def generate_speech(text: str, character_name: str, speed: float, pitch: float):
    characters = load_characters()
    if not characters or character_name not in characters:
        raise gr.Error("No characters available. Ask admin to add voices.")
    
    speaker_wav = characters[character_name]
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name
    
    tts.tts_to_file(text=text, speaker_wav=speaker_wav, language="en", file_path=temp_path)

    output_path = "output.wav"
    pitch_factor = 2 ** (pitch / 12.0)
    sr = 24000

    filter_chain = f"asetrate={sr}*{pitch_factor},atempo={1/pitch_factor}"
    if speed != 1.0:
        filter_chain += f",atempo={speed}"

    cmd = ["ffmpeg", "-y", "-i", temp_path, "-filter:a", filter_chain, "-ac", "1", output_path]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.unlink(temp_path)
    return output_path

with gr.Blocks(title="TTS by Keep") as public_ui:
    gr.Markdown("# 🎤 TTS by Keep\n**100% Free & Unlimited Voice Tool**")
    
    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="Enter your text", lines=5, placeholder="Hello, this is my cloned voice...")
            char_dropdown = gr.Dropdown(choices=list(load_characters().keys()), label="Select Character", value=None)
            speed_slider = gr.Slider(0.5, 2.0, value=1.0, step=0.1, label="Speed")
            pitch_slider = gr.Slider(-12, 12, value=0, step=0.5, label="Pitch (semitones)")
            generate_btn = gr.Button("🚀 Generate Speech", variant="primary")
        
        with gr.Column():
            audio_output = gr.Audio(label="Generated Audio", type="filepath")
    
    generate_btn.click(generate_speech, [text_input, char_dropdown, speed_slider, pitch_slider], audio_output)

# ====================== ADMIN PANEL ======================
def admin_login(password):
    if password == ADMIN_PASSWORD:
        return gr.update(visible=True), gr.update(visible=False)
    return gr.update(visible=False), gr.Error("Incorrect password")

def add_character(name: str, file):
    if not name or not file:
        return "❌ Name and voice file are required"
    
    characters = load_characters()
    filename = f"voices/{name.strip().replace(' ', '_').lower()}.wav"
    
    with open(filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    characters[name.strip()] = filename
    save_characters(characters)
    
    # Refresh dropdown in public UI (Gradio will handle on reload)
    return f"✅ Character '{name}' added successfully! Refresh the public page to see it."

with gr.Blocks(title="Admin - TTS by Keep") as admin_ui:
    gr.Markdown("# 🔐 Admin Panel")
    
    with gr.Tab("Login"):
        password_input = gr.Textbox(label="Admin Password", type="password")
        login_btn = gr.Button("Login")
    
    with gr.Group(visible=False) as admin_panel:
        gr.Markdown("### Add New Character")
        char_name = gr.Textbox(label="Character Name (e.g. Ahmed Voice)")
        voice_upload = gr.File(label="Upload Voice Sample (.wav)", type="binary")
        upload_btn = gr.Button("Upload Voice & Add Character", variant="primary")
        status_msg = gr.Textbox(label="Status")
        
        upload_btn.click(add_character, [char_name, voice_upload], status_msg)

    login_btn.click(admin_login, password_input, [admin_panel, password_input])

# Mount both interfaces
app = gr.mount_gradio_app(app, public_ui, path="/")
app = gr.mount_gradio_app(app, admin_ui, path="/admin")

# Simple home page
@app.get("/")
async def home():
    return HTMLResponse("""
    <h1 style="text-align:center; margin-top:80px; font-family:sans-serif;">
        🎤 TTS by Keep
    </h1>
    <p style="text-align:center; font-size:20px;">
        <a href="/">Public Tool</a> &nbsp;&nbsp;&nbsp; | &nbsp;&nbsp;&nbsp; 
        <a href="/admin">Admin Panel</a>
    </p>
    """)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
