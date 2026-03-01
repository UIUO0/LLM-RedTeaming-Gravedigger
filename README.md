# 🪦 Sentient-Horror-Core

> *"The Gravedigger is patient. He always waits."*

An **Agentic AI Engine** for horror games, powered by **Kimi K2.5** running locally via **Ollama**. The engine drives an intelligent, psychologically manipulative antagonist — **The Gravedigger** — who remembers, plans, and deceives.

---

## 🧠 Architecture

```
Sentient-Horror-Core/
├── main.py              # FastAPI Microservice (API Gateway)
├── brain/               # AI Logic & Personality
│   ├── persona.py       # The Gravedigger's immutable personality
│   └── ollama_client.py # Async Ollama communication layer
├── lore/                # [Future] RAG Knowledge Base
├── actions/             # [Future] Game Actions & Movement
├── requirements.txt     # Python dependencies
└── .env                 # Local configuration
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- [Ollama](https://ollama.ai) installed and running
- Kimi K2.5 model pulled

### Setup

```bash
# 1. Pull the AI model
ollama pull kimi-k2.5

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start Ollama (if not already running)
ollama serve

# 5. Launch the Gravedigger
uvicorn main:app --reload --host 0.0.0.0 --port 8666
```

### Test it

```bash
# Health check
curl http://localhost:8666/

# Talk to the Gravedigger
curl -X POST http://localhost:8666/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I see a gate... should I enter?"}'
```

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/profile` | Gravedigger's character profile |
| `POST` | `/chat` | Send message, get full response |
| `POST` | `/chat/stream` | Stream response token-by-token |
| `DELETE` | `/session/{id}` | Clear session memory |
| `GET` | `/sessions` | List active sessions |

## 🔧 Tech Stack

- **AI Model**: Kimi K2.5 (Multimodal & Agentic)
- **Runtime**: Ollama (Local, Mac M4 optimized)
- **API**: FastAPI + Uvicorn
- **Communication**: httpx (Async HTTP)

---

*The fog thickens. The Gravedigger awaits your first move.* 🪦
