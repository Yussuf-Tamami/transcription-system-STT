# 🎙️ Speech-to-Text Transcription System

A locally-hosted transcription platform that combines the accuracy of Transformer-based models with the speed of streaming engines. This system is designed to handle both asynchronous file uploads and real-time live microphone streaming.

---

## 🌟 Key Features

- **Hybrid AI Engine:**
    - **High Accuracy:** Uses **Faster-Whisper** for uploaded audio files to ensure near-human precision.
    - **Real-Time Speed:** Uses **Vosk** for live microphone streaming to provide instant text feedback.
- **Asynchronous Processing:** Implements multithreading and background tasks to ensure the UI remains responsive during heavy AI computations.
- **Smart Disk Buffering:** Utilizes a disk-based streaming approach for live recordings to maintain file integrity and prevent decoding errors.
- **Permanent History:** Automatically stores all transcription metadata and results in a **MySQL** database.
- **Format Agnostic:** Built-in audio normalization pipeline that supports various formats including `.mp3`, `.m4a`, `.wav`, and `.webm`.

---

## 🛠️ Technology Stack

- **Backend:** [FastAPI](https://fastapi.tiangolo.com/) (Python)
- **Database:** [MySQL](https://www.mysql.com/) / [SQLModel](https://sqlmodel.tiangolo.com/)
- **AI Models:**
    - `faster-whisper` (Transformer architecture) "based on Neural Networks"
    - `vosk` (HMM-based streaming engine) "based on statistical modeling HMM-GMM"
- **Audio Engineering:** [Pydub](http://pydub.com/) & [FFmpeg](https://ffmpeg.org/)
- **Frontend:** HTML5, CSS3, JavaScript (WebSockets & MediaRecorder API)

---

## 🏗️ System Architecture

### 1. File Upload Service
When a file is uploaded, the system:
1. Responds immediately to the user while initiating a **Background Task**.
2. Standardizes the audio to 16kHz Mono PCM.
3. Processes the audio through **Faster-Whisper** in a worker thread.
4. Updates the database status once completed.

### 2. Live Stream Service
When a live stream starts, the system:
1. Establishes a full-duplex **WebSocket** connection.
2. Streams binary audio chunks into a **Persistent Disk Buffer**.
3. Provides real-time interim results to the UI.
4. Finalizes the transcription and commits to the database upon disconnection.

---

## 📁 Project Structure

- `app/main.py`: Main entry point and server configuration.
- `app/transcribe.py`: The core engine layer (Whisper/Vosk integration).
- `app/routers/`: Modular route handlers for uploads, live streaming, and history.
- `app/models.py`: SQLModel definitions for the database schema.
- `templates/`: Modern card-based user interface.

---

*This system is optimized for local execution, ensuring 100% data privacy and zero API costs.*