# 🎓 EduGuardian AI — Multi-Agent Academic Coaching & Support System

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-FF6F00?style=flat)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/Frontend-React_19_+_TypeScript-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Deployment-Docker_Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_15-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Groq](https://img.shields.io/badge/LLM-Groq_Llama--3.3--70B-F55036?style=flat)](https://groq.com/)

**EduGuardian AI** is an intelligent, multi-agent student mentoring and academic support platform. It pairs students with three specialized AI agents to explain difficult academic concepts, create structured study roadmaps, and rebuild academic confidence—all wrapped in a sleek, responsive glassmorphic chat interface.

---

## 🌟 Key Highlights & Features

- 🧠 **Student Insight Agent**: Clarifies academic concepts, breaks down complex topics step-by-step, and delivers pedagogical explanations tailored to the student's background.
- 📅 **Study Planner Agent**: Builds customized study schedules, actionable milestone roadmaps, and interactive task checklists that students can track in real-time.
- 🧘 **Recovery Coach Agent**: Provides non-stigmatizing emotional support, combats academic anxiety, builds self-confidence, and guides students through burnout.
- 🔀 **Hybrid Intent Routing**: Combines deterministic high-speed intent matching with **LangGraph** dynamic routing to send every prompt to the best agent with zero lag.
- 🤝 **A2A Protocol (Agent-to-Agent)**: True microservice design where agents expose standardized `agent-card.json` endpoints and communicate via HTTP A2A protocols.
- ⚡ **Dual LLM Resilience & Auto-Failover**: First-class direct integration with official **Groq API** (`llama-3.3-70b-versatile`), local **OmniRoute** gateway support, and robust offline contextual fallbacks.
- 🛡️ **Student-Level Context Caching & Isolation**: Server-side in-memory TTL caching (`STUDENT_CONTEXT_CACHE_TTL_SECONDS=3600`) sharing academic context across all conversations of the same authenticated student while strictly isolating cross-student data.
- 💬 **Modern Glassmorphic UI**: Real-time SSE token streaming, interactive study plan modals with interactive checkboxes, session history drawer with rename/delete capabilities.

---

## 🏗️ System Architecture

```
                                  +-----------------------+
                                  |    Student Browser    |
                                  +-----------+-----------+
                                              | HTTP
                                              v
                              +-------------------------------+
                              |    Nginx Reverse Proxy (:80)  |
                              |   Serves React UI & /api/*    |
                              +---------------+---------------+
                                              |
                                              | Proxies /api/
                                              v
                              +-------------------------------+
                              |   FastAPI Gateway (:8000)     |
                              |  - LangGraph Orchestrator     |
                              |  - Session & Memory Service   |
                              |  - StudentContext TTL Cache   |
                              +---------------+---------------+
                                              |
                               +--------------+--------------+
                               | A2A Protocol (HTTP JSON)    |
                               v                             v
                +-----------------------------+ +-----------------------------+ +-----------------------------+
                |    Student Insight Agent    | |     Study Planner Agent     | |    Recovery Coach Agent     |
                |         Port: 8001          | |         Port: 8002          | |         Port: 8003          |
                +--------------+--------------+ +--------------+--------------+ +--------------+--------------+
                               |                               |                               |
                               +-------------------------------+-------------------------------+
                                                               |
                                                               v
                                              +---------------------------------+
                                              |   LLM Gateway & Resilience      |
                                              |  1. Direct Groq API (Primary)   |
                                              |  2. OmniRoute Proxy (Fallback)  |
                                              |  3. Contextual Offline Recovery |
                                              +----------------+----------------+
                                                               |
                                                               v
                                              +---------------------------------+
                                              |   PostgreSQL Database (:5432)   |
                                              |  Conversation History & Memory  |
                                              +---------------------------------+
```

---

## 🚀 Quick Start with Docker (Recommended)

> **No local Python, PostgreSQL, or Node.js required!** Docker Compose builds and coordinates all 6 containers with a single command.

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/eduguardian.git
cd eduguardian
```

### 2. Configure Environment Variables
Copy the template file to `.env`:
```bash
cp .env.example .env
```

Open `.env` and fill in the required keys:
```env
# 1. Choose any password for your PostgreSQL container
POSTGRES_PASSWORD=your_secure_password

# 2. Add your free Groq API key (https://console.groq.com/keys)
GROQ_API_KEY=gsk_your_groq_api_key_here

# 3. Add a random secret key for JWT verification
JWT_SECRET_KEY=generate_any_random_32_char_string
```

### 3. Launch the Stack
```bash
docker compose up --build
```

### 4. Access the Application
Once containers initialize (~30-60 seconds):
- 🌐 **Web Chatbot UI**: [http://localhost](http://localhost)
- 📖 **Interactive Swagger API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- 🩺 **Gateway Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 💻 Running Locally (Development Mode)

If you prefer to run natively without Docker:

### Prerequisites
- **Python**: 3.10 or 3.11
- **Node.js**: v18+ and `npm`
- **PostgreSQL**: 14+ running locally on port `5432`
- **Groq API Key**: Free from [console.groq.com](https://console.groq.com/keys)

### Step-by-Step Local Setup

1. **Clone & Create Python Virtual Environment**:
   ```bash
   git clone https://github.com/your-username/eduguardian.git
   cd eduguardian

   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. **Install Backend Dependencies**:
   ```bash
   pip install -r chatbot/backend/requirements.txt
   ```

3. **Set Up PostgreSQL Database**:
   ```bash
   # In psql or your DB client:
   CREATE DATABASE eduguardian_chatbot;
   ```

4. **Install Frontend Dependencies**:
   ```bash
   cd chatbot/frontend
   npm install
   cd ../..
   ```

5. **Configure `.env`**:
   ```bash
   cp .env.example .env
   ```
   Ensure `DATABASE_URL` matches your local PostgreSQL credentials:
   ```env
   DATABASE_URL=postgresql+asyncpg://postgres:your_local_password@localhost:5432/eduguardian_chatbot
   GROQ_API_KEY=gsk_your_groq_api_key_here
   LLM_PROVIDER=auto
   STUDENT_CONTEXT_CACHE_TTL_SECONDS=3600
   ```

6. **Start All Services with One Command**:
   ```bash
   python run_all.py
   ```
   This unified launcher starts:
   - `http://localhost:5173` — Frontend React UI
   - `http://localhost:8000` — FastAPI Gateway & Orchestrator
   - `http://localhost:8001` — Student Insight Agent
   - `http://localhost:8002` — Study Planner Agent
   - `http://localhost:8003` — Recovery Coach Agent

---

## ⚙️ Environment Variables Reference

| Variable | Description | Default / Example | Required |
|---|---|---|:---:|
| `POSTGRES_PASSWORD` | PostgreSQL root user password (used by Docker) | `my_secret_pass` | **Yes (Docker)** |
| `POSTGRES_USER` | PostgreSQL user name | `postgres` | No |
| `POSTGRES_DB` | PostgreSQL database name | `eduguardian_chatbot` | No |
| `DATABASE_URL` | Async SQLAlchemy DB connection string | `postgresql+asyncpg://postgres:pwd@localhost:5432/eduguardian_chatbot` | **Yes (Local)** |
| `GROQ_API_KEY` | Official Groq Cloud API Key | `gsk_...` | **Recommended** |
| `LLM_PROVIDER` | LLM routing mode (`auto`, `groq`, `omniroute`) | `auto` | No |
| `OMNIROUTE_BASE_URL` | OmniRoute gateway URL | `http://localhost:20128/v1` | No |
| `OMNIROUTE_API_KEY` | OmniRoute auth key | `your-omniroute-key` | No |
| `STUDENT_CONTEXT_CACHE_TTL_SECONDS` | Server-side cache TTL for student academic records (in seconds) | `3600` | No |
| `JWT_SECRET_KEY` | Secret key for JWT signature verification | `random_secret_string` | **Yes** |
| `A2A_USE_REMOTE_SERVICES` | Enable remote HTTP microservices for agents | `true` | No |

---

## 📁 Repository Structure

```
eduguardian/
├── Dockerfile                      # Backend Docker image (Gateway + Agents)
├── docker-compose.yml              # Multi-container orchestration (DB + 4 Backend + Nginx UI)
├── .env.example                    # Environment variable template
├── .dockerignore                   # Docker build exclusions
├── .gitignore                      # Git tracking exclusions
├── run_all.py                      # Multi-process local dev runner
├── README.md                       # Project documentation
│
└── chatbot/
    ├── backend/
    │   ├── a2a/                    # Agent-to-Agent protocol client, executors & cards
    │   ├── agents/                 # Agent domain logic
    │   │   ├── student_insight/    # Concept explanation & academic tutor agent
    │   │   ├── study_planner/      # Roadmap, milestone & plan generation agent
    │   │   └── recovery_coach/     # Confidence, mindset & burnout recovery agent
    │   ├── api/                    # FastAPI app factory, middleware & endpoints
    │   │   ├── routes/chat.py      # /api/chat and SSE /api/chat/stream routes
    │   │   └── routes/health.py    # Health check endpoints
    │   ├── core/                   # Logging, exceptions & security utilities
    │   ├── db/                     # SQLAlchemy async models, session & repositories
    │   │   └── repositories/
    │   │       ├── conversation.py    # Conversation & message CRUD
    │   │       └── student_context.py # StudentContext TTL cache & portal provider seam
    │   ├── llm/                    # Resilient OmniRoute & Groq API LLM Client
    │   ├── orchestrator/           # LangGraph state machine, router & context manager
    │   ├── services/               # Microservice ASGI entrypoints (:8001, :8002, :8003)
    │   ├── config.py               # Pydantic Settings management
    │   └── requirements.txt        # Production Python dependencies
    │
    └── frontend/
        ├── src/
        │   ├── components/         # ChatWindow, MessageBubble, StudyPlanCard, etc.
        │   ├── hooks/useChat.ts    # Streaming state management hook
        │   ├── api/chatApi.ts      # REST & SSE fetch client
        │   ├── App.tsx             # Main layout & glassmorphic dashboard
        │   └── index.css           # Design tokens, variables & dark mode theme
        ├── Dockerfile              # Multi-stage frontend Docker build (Node + Nginx)
        ├── nginx.conf              # Nginx reverse proxy routing
        └── package.json            # Frontend scripts & dependencies
```

---

## 📡 API Endpoints Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a prompt and receive a structured JSON response + study plan |
| `POST` | `/api/chat/stream` | Send a prompt and stream real-time response tokens (Server-Sent Events) |
| `GET` | `/api/chat/conversations` | Retrieve list of historical conversation threads for the user |
| `GET` | `/api/chat/{id}/messages` | Fetch all historical messages for a specific conversation |
| `PATCH`| `/api/chat/{id}/title` | Rename a conversation thread |
| `DELETE`| `/api/chat/{id}` | Permanently delete a conversation thread |
| `GET` | `/health` | Health check endpoint for container uptime monitoring |
| `GET` | `/.well-known/agent-card.json` | A2A Protocol Agent Card discovery endpoint on agent services |

---

## 🛠️ Common Troubleshooting

<details>
<summary><b>1. Docker: "POSTGRES_PASSWORD must be set in .env"</b></summary>

Make sure you copied `.env.example` to `.env` in the root directory and populated `POSTGRES_PASSWORD`:
```bash
cp .env.example .env
```
</details>

<details>
<summary><b>2. LLM: Agents replying with offline/contextual responses</b></summary>

The agents have an automated fallback when no LLM API key is provided or when rate-limited.
To get live AI responses:
1. Obtain a free key at [console.groq.com/keys](https://console.groq.com/keys).
2. Set `GROQ_API_KEY=gsk_your_key_here` in `.env`.
3. Ensure `LLM_PROVIDER=auto` or `LLM_PROVIDER=groq`.
</details>

<details>
<summary><b>3. Port 80 / 8000 already in use</b></summary>

If another local web server is bound to port 80 or 8000:
- **Windows**:
  ```powershell
  netstat -ano | findstr :80
  taskkill /F /PID <PID>
  ```
- **Linux / macOS**:
  ```bash
  lsof -ti:80 | xargs kill -9
  ```
</details>

<details>
<summary><b>4. Clean Rebuild in Docker</b></summary>

If you modified code or dependencies and want a completely clean rebuild:
```bash
docker compose down -v
docker compose build --no-cache
docker compose up
```
</details>

---

## 📄 License & Contributing

Built for modern, accessible student learning and support. Contributions, issues, and feature requests are welcome!
