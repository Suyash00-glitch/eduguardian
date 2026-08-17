# 🎓 EduGuardian AI — Multi-Agent Academic Coaching & Support System

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-FF6F00?style=flat)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/Frontend-React_19_+_TypeScript-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Deployment-Docker_Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_15-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Groq](https://img.shields.io/badge/LLM-Groq_Llama--3.3--70B-F55036?style=flat)](https://groq.com/)

**EduGuardian AI** is an intelligent, multi-agent student mentoring and academic support platform. Three specialized AI agents — Student Insight, Study Planner, and Recovery Coach — collaborate in real time to explain academic concepts, build structured study roadmaps, and restore student confidence. Every response is guarded by a three-layer AI safety system that blocks harmful input, prevents fabricated academic data, and keeps interactions educationally appropriate.

---

## 🌟 Feature Overview

| Feature | Description |
|---|---|
| 🧠 **Student Insight Agent** | Explains concepts step-by-step using pedagogy adapted to the student's history |
| 📅 **Study Planner Agent** | Builds personalized roadmaps, milestones, and task checklists |
| 🧘 **Recovery Coach Agent** | Non-stigmatizing emotional support, burnout recovery, confidence rebuilding |
| 📖 **Teach Me Mode** | Multi-turn adaptive teaching sessions with automatic difficulty progression |
| 🧩 **Quiz Mode** | Context-aware quizzes with adaptive difficulty based on past performance |
| 🗓️ **Personalized Study Plans** | Structured plans saved per-student, renderable in the UI as interactive cards |
| 🎓 **StudentContext** | Authoritative source for name, grades, attendance, enrolled subjects, assignments |
| 📊 **LearningHistory** | Tracks per-topic quiz scores and mastery to drive adaptive difficulty |
| 🛡️ **Guardrails Layer** | Three-stage safety: InputGuardrail → OutputGuardrail → AcademicGroundingGuardrail |
| 📈 **Guardrail Metrics** | Thread-safe in-memory counters, reason codes, and `/health/guardrails` endpoint |
| 🔀 **LangGraph Orchestration** | State-machine routing that selects the right agent for each intent |
| 🤝 **A2A Protocol** | True microservice agents with `agent-card.json` discovery endpoints |
| ⚡ **SSE Streaming** | Real-time token streaming to the browser via Server-Sent Events |
| 💾 **PostgreSQL Persistence** | Conversation history, messages, and student contexts stored in Postgres |
| 🌓 **Light / Dark Theme** | Full theme toggle with system preference detection |
| 🐳 **Docker Compose** | One-command deployment of 6 containers |

---

## 🏗️ System Architecture

```
                              +-----------------------+
                              |    Student Browser    |
                              +-----------+-----------+
                                          |
                                          v
                          +-------------------------------+
                          |    Nginx Reverse Proxy (:80)  |
                          |   Serves React UI & /api/*    |
                          +---------------+---------------+
                                          |
                                          v
                          +-------------------------------+
                          |   FastAPI Gateway (:8000)     |
                          |  ┌─────────────────────────┐ |
                          |  │  InputGuardrail          │ |  ← Phase 8.1
                          |  │  LangGraph Orchestrator  │ |  ← Intent routing
                          |  │  StudentContext Cache     │ |  ← TTL-backed
                          |  │  LearningHistory         │ |  ← Adaptive state
                          |  │  OutputGuardrail         │ |  ← Phase 8.1
                          |  │  AcademicGrounding       │ |  ← Phase 8.2
                          |  │  GuardrailMetrics        │ |  ← Phase 8.3
                          |  └─────────────────────────┘ |
                          +---------------+---------------+
                                          |
                           +--------------+--------------+
                           |   A2A Protocol (HTTP JSON)  |
                     ------+------       |         ------+------
                     |           |       |         |           |
                     v           v       v         v           v
              +:8001+      +:8002+               +:8003+
       Student Insight   Study Planner       Recovery Coach
             Agent           Agent               Agent
                     \           |           /
                      \          v          /
                       +-------------------+
                       |   LLM Gateway     |
                       |  1. Groq API      |
                       |  2. OmniRoute     |
                       +-------------------+
                                 |
                                 v
                       +-------------------+
                       |  PostgreSQL :5432 |
                       +-------------------+
```

---

## 🛡️ Guardrails Architecture

EduGuardian uses a three-stage deterministic safety layer. The LLM is **not** used as a judge — all safety checks are deterministic Python logic.

```
User Input
    ↓
InputGuardrail.evaluate()          ← blocks prompt injection, credential extraction,
    ↓  (if BLOCK → safe rejection)    system prompt extraction, scope violations
LangGraph Orchestrator
    ↓
LLM + A2A Agents
    ↓
OutputGuardrail.evaluate()         ← strips think tags, credential leaks,
    ↓                                 internal A2A metadata, stigmatizing language
AcademicGroundingGuardrail         ← catches invented marks, grades, attendance,
    ↓                                 subjects, deadlines not in StudentContext
GuardrailMetrics.record()          ← counters, reason codes, /health/guardrails
    ↓
Student Response
```

### Observability

Every guardrail decision produces a structured log line:
```
INFO GuardrailEvent: guardrail=input category=prompt_injection action=block reason_code=prompt_injection conversation_id=abc123
```

Aggregate metrics are exposed at `GET /health/guardrails` (counters only — no PII).

---

## 📖 Adaptive Learning Modes

### Teach Me Mode
- Activated by "teach me X" or "explain X"
- Multi-turn sessions with configurable support levels (1–5)
- Automatically simplifies explanation if student says "I don't understand"
- Progresses difficulty when student demonstrates understanding
- State stored in `TeachingState` per conversation

### Quiz Mode
- Activated by "quiz me on X" or "test my knowledge"
- Generates questions calibrated to the student's prior performance in `LearningHistory`
- Tracks correct/incorrect answers per topic
- Adaptive difficulty: harder questions on mastery, easier on struggle
- State stored in `QuizState` per conversation

---

## 🚀 Quick Start — Docker (Recommended)

> No local Python, PostgreSQL, or Node.js required. Docker Compose builds and starts all 6 containers.

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/eduguardian.git
cd eduguardian
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```

Edit `.env` and set:
```env
# PostgreSQL password (choose any secure password)
POSTGRES_PASSWORD=your_secure_password

# Free Groq API key — https://console.groq.com/keys
GROQ_API_KEY=gsk_your_key_here

# Random JWT secret for token verification
JWT_SECRET_KEY=replace_with_a_strong_random_secret
```

### 3. Launch the Stack
```bash
docker compose up --build
```

### 4. Access
| URL | Service |
|---|---|
| http://localhost | React Chatbot UI |
| http://localhost:8000/docs | Swagger API Docs |
| http://localhost:8000/health | Gateway Health |
| http://localhost:8000/health/guardrails | Guardrail Metrics |
| http://localhost:8001/.well-known/agent-card.json | Student Insight Agent Card |
| http://localhost:8002/.well-known/agent-card.json | Study Planner Agent Card |
| http://localhost:8003/.well-known/agent-card.json | Recovery Coach Agent Card |

---

## 💻 Running Locally (Development)

### Prerequisites
- **Python** 3.10 or 3.11
- **Node.js** v18+ and `npm`
- **PostgreSQL** 14+ on port 5432
- **Groq API Key** — free from [console.groq.com](https://console.groq.com/keys)

### Setup

```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # Linux/macOS

# 2. Install backend dependencies
pip install -r chatbot/backend/requirements.txt

# 3. Install frontend dependencies
cd chatbot/frontend && npm install && cd ../..

# 4. Create database
# In psql: CREATE DATABASE eduguardian_chatbot;

# 5. Configure environment
cp .env.example .env
# Edit .env with your DATABASE_URL, GROQ_API_KEY, JWT_SECRET_KEY

# 6. Start all services (one command)
python run_all.py
```

Or use the Windows scripts:
```powershell
.\start_all.ps1           # Opens each service in a separate terminal window
.\start_background.ps1    # Starts all services silently in background
```

**Service URLs (local):**
- Frontend: http://localhost:5173
- Gateway: http://localhost:8000
- Student Insight: http://localhost:8001
- Study Planner: http://localhost:8002
- Recovery Coach: http://localhost:8003

---

## ⚙️ Environment Variables Reference

| Variable | Description | Required |
|---|---|:---:|
| `POSTGRES_PASSWORD` | PostgreSQL container password | **Yes (Docker)** |
| `DATABASE_URL` | SQLAlchemy async connection string | **Yes (Local)** |
| `GROQ_API_KEY` | Groq Cloud API key | **Recommended** |
| `JWT_SECRET_KEY` | JWT verification secret | **Yes** |
| `LLM_PROVIDER` | `auto` / `groq` / `omniroute` | No |
| `OMNIROUTE_BASE_URL` | OmniRoute gateway URL | No |
| `OMNIROUTE_API_KEY` | OmniRoute auth key | No |
| `OMNIROUTE_MODEL` | Model via OmniRoute | No |
| `GROQ_MODEL` | Direct Groq model name | No |
| `STUDENT_CONTEXT_CACHE_TTL_SECONDS` | StudentContext cache TTL (seconds) | No |
| `A2A_USE_REMOTE_SERVICES` | Enable HTTP microservices | No |
| `STUDENT_INSIGHT_AGENT_URL` | Insight agent endpoint | No |
| `STUDY_PLANNER_AGENT_URL` | Planner agent endpoint | No |
| `RECOVERY_COACH_AGENT_URL` | Coach agent endpoint | No |
| `A2A_TIMEOUT_SECONDS` | A2A call timeout | No |

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/chat` | Send a message, receive structured JSON response |
| `POST` | `/api/chat/stream` | Send a message, stream tokens via SSE |
| `GET` | `/api/chat/conversations` | List conversation threads for the student |
| `GET` | `/api/chat/{id}/messages` | Fetch all messages for a conversation |
| `PATCH` | `/api/chat/{id}/title` | Rename a conversation |
| `DELETE` | `/api/chat/{id}` | Delete a conversation thread |
| `GET` | `/health` | Gateway health check |
| `GET` | `/health/guardrails` | Guardrail observability (counters only, no PII) |
| `GET` | `/.well-known/agent-card.json` | A2A agent discovery (ports 8001–8003) |

---

## 📁 Repository Structure

```
eduguardian/
├── Dockerfile                       # Backend Docker image (gateway + agents)
├── docker-compose.yml               # 6-container stack (DB + 4 backend + Nginx)
├── .env.example                     # Environment variable template
├── .dockerignore                    # Docker build exclusions
├── .gitignore                       # Git tracking exclusions
├── run_all.py                       # Multi-process local dev runner
├── start_all.ps1                    # Windows PowerShell launcher
├── start_background.ps1             # Windows silent background launcher
├── start_all.bat                    # Windows batch launcher
├── pytest.ini                       # Test configuration
├── scripts/                         # Live verification scripts
│   ├── live_phase7_test.py
│   ├── verify_phase8_live.py
│   ├── verify_phase8_2_live.py
│   └── verify_phase8_3_live.py
│
└── chatbot/
    ├── backend/
    │   ├── a2a/                     # A2A SDK: client, executors, agent cards, protocol
    │   ├── agents/                  # Agent domain logic
    │   │   ├── student_insight/     # Concept tutor agent
    │   │   ├── study_planner/       # Roadmap & milestone agent
    │   │   └── recovery_coach/      # Wellbeing & confidence agent
    │   ├── api/                     # FastAPI factory, middleware, routes
    │   │   └── routes/
    │   │       ├── chat.py          # /api/chat & SSE streaming endpoints
    │   │       └── health.py        # /health & /health/guardrails
    │   ├── core/                    # Logging, exceptions, in-memory session cache
    │   ├── db/                      # SQLAlchemy async models, session, repositories
    │   │   └── repositories/
    │   │       ├── conversation.py
    │   │       └── student_context.py
    │   ├── guardrails/              # Three-stage safety layer
    │   │   ├── input_guardrail.py   # Prompt injection, scope, credential extraction
    │   │   ├── output_guardrail.py  # Think tags, credential leaks, stigmatizing language
    │   │   ├── academic_grounding.py # StudentContext fact verification
    │   │   ├── service.py           # GuardrailsService orchestrator
    │   │   └── metrics.py           # Thread-safe counters & reason codes
    │   ├── llm/                     # Resilient OmniRoute + Groq LLM client
    │   ├── orchestrator/            # LangGraph state machine & routing
    │   │   ├── graph.py             # LangGraph graph definition
    │   │   ├── router.py            # Intent classification & agent dispatch
    │   │   ├── adaptive_quiz.py     # Quiz difficulty state machine
    │   │   ├── adaptive_teaching.py # Teaching progression state machine
    │   │   ├── state.py             # ChatState definition
    │   │   └── validator.py        # Response validation
    │   ├── schemas/                 # All Pydantic data contracts
    │   ├── services/                # ASGI microservice entrypoints (8001–8003)
    │   ├── config.py                # Pydantic Settings loader
    │   └── requirements.txt
    │
    ├── tests/                       # Full test suite
    │   ├── test_schemas.py
    │   ├── test_phase8_guardrails.py
    │   ├── test_phase8_2_academic_grounding.py
    │   └── test_phase8_3_guardrail_metrics.py
    │
    └── frontend/
        ├── src/
        │   ├── components/          # ChatWindow, MessageBubble, StudyPlanCard, etc.
        │   ├── hooks/useChat.ts     # Streaming state management hook
        │   ├── api/chatApi.ts       # REST & SSE fetch client
        │   ├── App.tsx              # Main layout & theme toggle
        │   └── index.css            # Design tokens & dark mode theme
        ├── Dockerfile               # Multi-stage frontend build (Node → Nginx)
        ├── nginx.conf               # Nginx reverse proxy config
        └── package.json
```

---

## 🧪 Running Tests

```bash
# Schema contracts
pytest chatbot/tests/test_schemas.py -v

# Guardrails Phase 8.1
pytest chatbot/tests/test_phase8_guardrails.py -v

# Academic Grounding Phase 8.2
pytest chatbot/tests/test_phase8_2_academic_grounding.py -v

# Guardrail Metrics Phase 8.3
pytest chatbot/tests/test_phase8_3_guardrail_metrics.py -v

# All guardrail tests together
pytest chatbot/tests/test_phase8_guardrails.py chatbot/tests/test_phase8_2_academic_grounding.py chatbot/tests/test_phase8_3_guardrail_metrics.py -v
```

### Live Verification Scripts (requires running Docker stack)
```bash
python scripts/verify_phase8_live.py
python scripts/verify_phase8_2_live.py
python scripts/verify_phase8_3_live.py
```

---

## 🛠️ Troubleshooting

<details>
<summary><b>1. "POSTGRES_PASSWORD must be set in .env"</b></summary>

Copy the template and set the required variables:
```bash
cp .env.example .env
```
Then edit `.env` and set `POSTGRES_PASSWORD`.
</details>

<details>
<summary><b>2. LLM returning offline/fallback responses</b></summary>

Set a valid Groq API key (free at [console.groq.com/keys](https://console.groq.com/keys)):
```env
GROQ_API_KEY=gsk_your_key_here
LLM_PROVIDER=auto
```
</details>

<details>
<summary><b>3. Port 80 or 8000 already in use</b></summary>

Windows:
```powershell
netstat -ano | findstr :80
taskkill /F /PID <PID>
```
Linux/macOS:
```bash
lsof -ti:80 | xargs kill -9
```
</details>

<details>
<summary><b>4. Clean Docker rebuild</b></summary>

```bash
docker compose down -v
docker compose build --no-cache
docker compose up
```
</details>

---

## 📄 License

Built for modern, accessible student learning and academic support.
