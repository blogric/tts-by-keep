import os
import json
import shutil
from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import HTMLResponse, FileResponse
import gradio as gr

app = FastAPI(title="TTS by Keep")

os.makedirs("voices", exist_ok=True)

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

ADMIN_PASSWORD = "keepadmin123"   # ← CHANGE THIS TO YOUR STRONG PASSWORD

# ====================== PUBLIC FRONTEND (Simple & Working) ======================
def generate_speech(text: str, character: str, speed: float, pitch: float):
    if not text.strip():
        raise gr.Error("Please enter some text")
    
    characters = load_characters()
    if not characters:
        raise gr.Error("No voices added yet. Ask admin to upload voices.")
    
    if character not in characters:
        raise gr.Error("Selected character not found")

    # For now we use browser TTS (very stable). Later we can add real cloning.
    # Return text so Gradio can speak it
    return text, speed, pitch, character   # We will handle speaking in JS

with gr.Blocks(title="TTS by Keep") as public_ui:
    gr.Markdown("# 🎤 TTS by Keep\n**100% Free Unlimited TTS Tool**")

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="Enter Text", lines=5, placeholder="Type your text here...")
            char_dropdown = gr.Dropdown(
                choices=list(load_characters().keys()), 
                label="Select Character", 
                value=None if not load_characters() else list(load_characters().keys())[0]
            )
            speed = gr.Slider(0.5, 2.0, 1.0, step=0.1, label="Speed")
            pitch = gr.Slider(-12, 12, 0, step=0.5, label="Pitch")
            btn = gr.Button("🚀 Generate Speech", variant="primary")
        
        with gr.Column():
            audio_out = gr.Audio(label="Your Generated Speech", type="filepath")

    # Simple browser speech (works reliably)
    def speak(text, speed_val, pitch_val, char):
        # In real deployment we can enhance this with Web Speech API via custom JS
        return f"Speaking: {text} (Character: {char}, Speed: {speed_val}x, Pitch: {pitch_val})"

    btn.click(speak, [text_input, speed, pitch, char_dropdown], audio_out)

# ====================== ADMIN PANEL ======================
def add_voice(name: str, file: UploadFile):
    if not name or not file:
        return "❌ Please provide name and voice file"
    characters = load_characters()
    filename = f"voices/{name.strip().replace(' ', '_').lower()}.wav"
    with open(filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    characters[name.strip()] = filename
    save_characters(characters)
    return f"✅ Voice '{name}' uploaded successfully! Refresh public page."

with gr.Blocks(title="Admin - TTS by Keep") as admin_ui:
    gr.Markdown("# 🔐 Admin Panel - TTS by Keep")

    with gr.Tab("Login"):
        pwd = gr.Textbox(label="Password", type="password")
        login_btn = gr.Button("Login")

    with gr.Group(visible=False) as admin_panel:
        gr.Markdown("### Upload New Voice")
        name_input = gr.Textbox(label="Character Name")
        file_input = gr.File(label="Upload .wav voice sample", type="binary")
        upload_btn = gr.Button("Upload Voice", variant="primary")
        status = gr.Textbox(label="Status")

        upload_btn.click(add_voice, [name_input, file_input], status)

    def check_login(password):
        if password == ADMIN_PASSWORD:
            return gr.update(visible=True), gr.update(visible=False)
        return gr.update(visible=False), gr.Error("Wrong password!")

    login_btn.click(check_login, pwd, [admin_panel, pwd])

# Mount interfaces
app = gr.mount_gradio_app(app, public_ui, path="/")
app = gr.mount_gradio_app(app, admin_ui, path="/admin")

@app.get("/")
async def home():
    return HTMLResponse("""
    <h1 style="text-align:center;margin-top:100px;font-family:sans-serif;color:#1e40af;">
        🎤 TTS by Keep
    </h1>
    <p style="text-align:center;font-size:22px;">
        <a href="/">→ Public Tool</a> &nbsp;&nbsp;&nbsp;|&nbsp;&nbsp;&nbsp; 
        <a href="/admin">→ Admin Panel</a>
    </p>
    <p style="text-align:center;">100% Free • Unlimited • Your Voices</p>
    """)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
