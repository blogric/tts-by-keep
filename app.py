import os
import gradio as gr
import torch
from TTS.api import TTS
from pydub import AudioSegment
import subprocess
import tempfile

# Load the model on CPU
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)

def generate_tts(text: str, character: str, speed: float, pitch: float):
    if character == "Keep Voice 1":
        speaker_wav = "voices/keep1.wav"
    else:
        speaker_wav = "voices/keep2.wav"

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name
    
    tts.tts_to_file(text=text, speaker_wav=speaker_wav, language="en", file_path=temp_path)

    final_path = "output.wav"
    pitch_factor = 2 ** (pitch / 12.0)
    sr = 24000

    if pitch == 0 and speed == 1.0:
        AudioSegment.from_wav(temp_path).export(final_path, format="wav")
    else:
        filter_chain = f"asetrate={sr}*{pitch_factor},atempo={1/pitch_factor}"
        if speed != 1.0:
            filter_chain += f",atempo={speed}"

        cmd = ["ffmpeg", "-y", "-i", temp_path, "-filter:a", filter_chain, "-ac", "1", final_path]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    os.unlink(temp_path)
    return final_path

# === Gradio Interface ===
with gr.Blocks(title="TTS by Keep", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🎤 TTS by Keep\n**Unlimited • Free • Your Voice Cloned**")

    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(label="Enter Text", placeholder="Hello, this is Keep speaking...", lines=4)
            character = gr.Dropdown(choices=["Keep Voice 1", "Keep Voice 2"], value="Keep Voice 1", label="Your Character")
            speed = gr.Slider(0.5, 2.0, value=1.0, step=0.1, label="Speed")
            pitch = gr.Slider(-12, 12, value=0, step=0.5, label="Pitch (semitones)")
            generate_btn = gr.Button("🚀 Generate TTS", variant="primary")

        with gr.Column():
            audio_output = gr.Audio(label="Generated Audio", type="filepath")

    generate_btn.click(generate_tts, inputs=[text_input, character, speed, pitch], outputs=audio_output)

    gr.Markdown("Made with ❤️ • 100% Free & Unlimited on Railway")

# === Use Railway's PORT (This is the fix) ===
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))   # Railway sets $PORT automatically
    demo.launch(
        server_name="0.0.0.0", 
        server_port=port,
        share=False
    )
