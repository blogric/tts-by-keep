import gradio as gr
import torch
from TTS.api import TTS
from pydub import AudioSegment
import subprocess
import os
import tempfile

# Load model (CPU only for Railway)
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
def generate_tts(text: str, character: str, speed: float, pitch: float):
    # Select your voice sample
    if character == "Keep Voice 1":
        speaker_wav = "voices/keep1.wav"
    else:
        speaker_wav = "voices/keep2.wav"

    # Generate base audio with XTTS
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        temp_path = f.name
    tts.tts_to_file(text=text, speaker_wav=speaker_wav, language="en", file_path=temp_path)

    # === Pitch + Speed adjustment using FFmpeg (works perfectly) ===
    final_path = "output.wav"
    pitch_factor = 2 ** (pitch / 12.0)
    sr = 24000  # XTTS v2 sample rate

    if pitch == 0 and speed == 1.0:
        # No adjustment needed
        AudioSegment.from_wav(temp_path).export(final_path, format="wav")
    else:
        # Pitch shift (keeps duration) + speed
        filter_chain = f"asetrate={sr}*{pitch_factor},atempo={1/pitch_factor}"
        if speed != 1.0:
            filter_chain += f",atempo={speed}"

        cmd = [
            "ffmpeg", "-y", "-i", temp_path,
            "-filter:a", filter_chain,
            "-ac", "1",  # mono for smaller file
            final_path
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    os.unlink(temp_path)  # clean up
    return final_path

# === Beautiful Gradio Interface ===
with gr.Blocks(title="TTS by Keep", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🎤 TTS by Keep
    **Your personal unlimited voice cloning tool**  
    Powered by Coqui XTTS v2 • 100% Free • No limits • Runs on Railway
    """)
    
    with gr.Row():
        with gr.Column():
            text_input = gr.Textbox(
                label="Enter your text here",
                placeholder="Hello, this is my cloned voice speaking...",
                lines=4
            )
            character = gr.Dropdown(
                choices=["Keep Voice 1", "Keep Voice 2"],
                value="Keep Voice 1",
                label="Select Character (Your Voice)"
            )
            speed = gr.Slider(0.5, 2.0, value=1.0, step=0.1, label="Speed")
            pitch = gr.Slider(-12, 12, value=0, step=0.5, label="Pitch (semitones)")
            
            generate_btn = gr.Button("🚀 Generate TTS", variant="primary", size="large")
        
        with gr.Column():
            audio_output = gr.Audio(label="Your Generated Speech", type="filepath")
            gr.Markdown("**Tip**: Download the file below the player")

    generate_btn.click(
        generate_tts,
        inputs=[text_input, character, speed, pitch],
        outputs=audio_output
    )

    gr.Markdown("""
    ### How it works
    - Uses **your two voice samples** for perfect cloning  
    - Real-time pitch & speed control  
    - 100% private • Runs on your Railway server  
    Made with ❤️ by Keep
    """)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=int(os.getenv("PORT", 7860)))
