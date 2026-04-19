# ⚙️ System Workflow & Features Logic

This document explains the internal logic of the features and how data flows through the system. It is intended for developers looking to scale or modify existing features.

---

## 1. Speech-to-Text (STT) Service features

### A. Speech Upload (File - audio batch)

Users upload an audio file (MP3/WAV/M4A) to be transcribed using the Faster-Whisper engine.

* **Request:** Client sends file to `POST /api/stt/upload`
* **Storage:** File is saved to the shared `/app/storage/uploads` volume
* **Processing:** A background task triggers Faster-Whisper using the base model
* **Database:** Transcription text and metadata are saved to the MySQL history table
* **Response:** JSON result containing the transcription text is returned

---

### B. Live Transcription (Real-time)

A continuous audio stream processed via WebSockets using the Vosk engine for low-latency results.

* **Handshake:** Client connects to `ws://localhost:8080/ws/live`
* **Tunneling:** Nginx upgrades the connection and forwards binary audio chunks to the STT worker
* **Inference:** Vosk processes audio frames in real-time and returns partial results
* **Finalization:** On connection close, the final transcription is stored in the database

---

## 2. Text-to-Speech (TTS) Service

Converts text into natural-sounding audio using the Kokoro-ONNX model.

* **Input:** User provides text and selects a voice (e.g., `af_bella`)
* **Synthesis:** Backend generates a `.wav` file using the ONNX model
* **Shared Storage:** Output is saved to `/app/storage/outputs`
* **Direct Delivery:** Nginx serves the file directly via `/api/tts/outputs/`, enabling immediate playback

---

## 3. Data & Persistence Flow

### Shared Volumes

The system uses a global shared storage volume between containers:

* **STT Service:** Writes uploaded audio files
* **TTS Service:** Writes generated speech files
* **Nginx Gateway:** Reads and serves files directly to the client without routing through backend services

---

### Database Interaction

* **Storage:** MySQL stores transcription records and metadata
* **ORM Layer:** SQLModel (built on SQLAlchemy) manages database interactions
* **Auto-Initialization:** A retry mechanism ensures the database is ready before services attempt schema creation
