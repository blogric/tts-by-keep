FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN mkdir -p voices

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pre-accept Coqui TOS + Download XTTS v2 model during build
RUN python -c '
import os
os.environ["COQUI_TOS_AGREED"] = "1"
print("Downloading XTTS v2 model (this will take 8-15 minutes on first build)...")
from TTS.api import TTS
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
print("✅ XTTS v2 model downloaded successfully!")
'

EXPOSE 8000
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
