# 🎙️ Transcription system (Speech-To-Text & Text-To-Speech)

A locally-hosted transcription platform that combines the accuracy of Transformer-based AI models with the speed of streaming engines. This system is designed to handle both real-time speech-to-text (STT) & file-based transcription, and neural text-to-speech (TTS) synthesis.

---

## 🛠️ Technical Stack

| Component     | Technology                    | Role                                                      |
| ------------- | ----------------------------- | --------------------------------------------------------- |
| Gateway       | Nginx                         | Reverse Proxy, WebSocket handling, & Static Asset serving |
| STT Engine    | FastAPI, Faster-Whisper, Vosk | Audio processing (Batch & Real-time)                      |
| TTS Engine    | FastAPI, Kokoro-ONNX          | Neural Speech Synthesis                                   |
| Database      | MySQL 8.0                     | Metadata and transcription history storage                |
| Orchestration | Docker & Docker Compose       | Containerization and networking                           |
| Management    | phpMyAdmin                    | Visual database administration                            |

---

## 🏗️ Architecture Overview

The system follows a **Microservices Architecture**. Instead of one monolithic application, it is split into specialized services that communicate over an internal Docker network.

The **Nginx Gateway** acts as the single entry point (Port 8080), handling routing, protecting backend services, and directing traffic based on URL paths.

---

## 🚀 Getting Started

### Prerequisites

* Docker and Docker Compose installed
* At least **8GB of RAM** (required to load AI models)

---

### Installation & Deployment

#### 1. Clone the Repository

```bash
git clone <https://github.com/Yussuf-Tamami/transcription-system_STT-TTS>
cd transcription-system
```

#### 2. Spin up the Environment

```bash
docker-compose up -d
```

> **Note:** On the first run, the system will download AI models into the `./models` folder. This may take a few minutes depending on your internet speed.

#### 3. Verify the Services

```bash
docker ps
```

Ensure the following containers are running:

* `frontend_gateway`
* `stt_worker`
* `tts_worker`
* `mysql_database`

---

## 🌐 How to Access the Platform

Once the containers are running:

* **Main UI:** http://localhost:8080
* **Database Admin (phpMyAdmin):** http://localhost:8090
* **STT API Docs (Swagger):** http://localhost:8001/docs
* **TTS API Docs (Swagger):** http://localhost:8002/docs

---

## 📁 Repository Structure

```plaintext
.
├── frontend/             # Nginx config & HTML/JS/CSS assets
├── STT-Service/          # Python FastAPI service for Speech-to-Text
├── TTS-Service/          # Python FastAPI service for Text-to-Speech
├── storage/              # Shared volume for audio uploads and outputs
├── models/               # Shared volume for AI model weights
└── docker-compose.yml    # System orchestration file
```
