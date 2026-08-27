# 🎓 EduGuardian AI — Comprehensive Student Success & Faculty Intervention Platform

[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-FF6F00?style=flat)](https://langchain-ai.github.io/langgraph/)
[![React](https://img.shields.io/badge/Frontend-React_18_+_Vite-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev/)
[![Docker](https://img.shields.io/badge/Deployment-Docker_Compose-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_15-336791?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

**EduGuardian AI** is an enterprise-grade academic mentoring, early-warning risk prediction, and automated intervention platform. It bridges the gap between students, faculty advisors, and institutional data systems through authoritative live student portal synchronization, calibrated academic risk modeling, and a multi-agent conversational coaching architecture.

---

## 🌟 Architecture & Core Capabilities

```
                                  ┌──────────────────────────────┐
                                  │   University Solutions EMS   │
                                  │    Live Student Web Portal   │
                                  └──────────────┬───────────────┘
                                                 │ HTTPS / Mobile Auth
                                                 ▼
┌────────────────────────┐        ┌──────────────────────────────┐        ┌────────────────────────┐
│  Student Portal (:3001)│        │   EduGuardian API (:5000)    │        │  Admin Portal (:3002)  │
│  - Academic Progress   │◄──────►│  - Portal Adapter & Normalizer│◄──────►│  - Hybrid Live Roster  │
│  - Attendance & Marks  │ (JWT)  │  - Academic Risk Engine      │ (JWT)  │  - Mentor Management   │
│  - Course Resources    │        │  - Mentor Quota Enforcement  │        │  - Resource Dispatch   │
│  - Constructive Advice │        │  - Intervention Audit Trail  │        │  - Explainable Risk    │
└────────────────────────┘        └──────────────┬───────────────┘        └────────────────────────┘
                                                 │
                                                 │ Real-Time Academic Context
                                                 ▼
                                  ┌──────────────────────────────┐
                                  │  Chatbot Gateway (:8000)     │
                                  │  - LangGraph Orchestrator    │
                                  │  - 3-Stage Guardrails Layer  │
                                  │  - PostgreSQL Long-Term Mem  │
                                  └──────────────┬───────────────┘
                                                 │
                      ┌──────────────────────────┼──────────────────────────┐
                      ▼                          ▼                          ▼
        ┌─────────────────────────┐┌─────────────────────────┐┌─────────────────────────┐
        │  Insight Agent (:8001)  ││  Planner Agent (:8002)  ││  Coach Agent (:8003)    │
        │  - Academic Diagnosis   ││  - Weekly Action Plans  ││  - Supportive Dialogue  │
        │  - Subject Strengths    ││  - Deadline Management  ││  - Confidence Building  │
        └─────────────────────────┘└─────────────────────────┘└─────────────────────────┘
```

---

## 🚀 Main Components

### 1. Student Dashboard Portal (`prat-frontend/` — Port 3001)
- **Authoritative Academic Records**: Renders real SGPA, CGPA, semester marks cards, and enrolled subjects directly synchronized from University Solutions.
- **Support & Resources**: Displays targeted remedial materials, course notes, and study guides dispatched by faculty mentors.
- **Constructive Guidance**: Provides motivating, forward-looking academic tips without exposing demoralizing raw risk scores or clinical risk labels.

### 2. Faculty / Admin Portal (`ash-frontend/admin-portal/` — Port 3002)
- **Hybrid Student Roster**: Unified view displaying both real synchronized students and seeded demo students.
- **Explainable Risk Profiles**: Deep dive into calculated risk metrics, confidence scores, and specific trajectory factors (e.g., negative SGPA velocity, backlog detection).
- **Mentor Management & Quota Enforcement**: Add/edit faculty mentors, designate department roles, and strictly enforce mentee assignment limits.
- **Intervention & Resource Dispatch Center**: Multi-target material distribution (Entire Cohort, Risk-Tiered, Assigned Mentees, or Specific Student) with immutable audit history.

### 3. Multi-Agent AI Chatbot (`chatbot/` — Ports 8000, 8001, 8002, 8003, 3000)
- **LangGraph State Orchestration**: Deterministic intent classification routing conversations to specialized agents.
- **Three A2A Microservice Agents**:
  - `agent-insight` (8001): Performs academic diagnosis and subject trend evaluation.
  - `agent-planner` (8002): Creates actionable weekly revision schedules and priorities.
  - `agent-coach` (8003): Delivers empathetic, non-judgmental guidance and motivational coaching.
- **Three-Stage Guardrails**:
  1. *Input Guardrail*: Filters prompt injections and inappropriate student queries.
  2. *Output Guardrail*: Prevents exposure of internal risk scores, model jargon, or system prompts.
  3. *Academic Grounding*: Ensures study recommendations strictly adhere to authoritative course syllabi.
- **Long-Term Memory**: Conversation history, episodic user facts, and contextual state persisted in PostgreSQL (`eduguardian_chatbot`).

---

## 📊 Academic Risk Engine & Hybrid Model

### Calibrated Risk Prediction
The system computes an explainable multi-factor academic risk level:
- **High Risk (Score ≥ 70)**: Active backlogs, failing grades, or sharp downward SGPA trajectories.
- **Medium Risk (Score 35–69)**: Marginal SGPA trends or missing foundational prerequisites.
- **Low Risk (Score < 35)**: Steady or upward academic velocity with solid cumulative performance.
- *Graceful Fallback*: Missing or pending attendance data is explicitly handled as `not_available` rather than penalized as 0%.

### Hybrid Roster Architecture
The platform intentionally operates a hybrid data model:
- **`data_source = "student_portal"`**: Real students authenticated and synchronized via the University Solutions portal adapter (e.g., `MOHAMMED AJMAL` / `NNM24IS127`, `PRAYAG M` / `NNM24IS172`).
- **`data_source = "demo"`**: Database-backed benchmark students (`seed_students.sql`) illustrating various academic risk archetypes across cohorts.

---

## 👥 Mentor Management & Student Assignment

1. **Capacity Enforcement**: Every faculty mentor has a configured quota (e.g., max 5–10 mentees). The backend rejects any assignment exceeding capacity (`HTTP 400 Bad Request`).
2. **Duplicate Prevention**: A student can only be assigned to one active mentor at a time.
3. **Targeted Resource Distribution**: Faculty can dispatch remedial materials across targeted categories:
   - `ALL` — Entire cohort.
   - `HIGH` / `MEDIUM` / `LOW` — Dynamically filtered by the risk engine.
   - `MY_MENTEES` — Active mentees assigned to the authenticated teacher.
   - `SPECIFIC_STUDENT` — Exact student targeting with isolation (other students cannot access).

---

## 🔒 Security, RBAC & Multi-Tenant Isolation

- **Role-Based Access Control (RBAC)**:
  - `student`: Strictly restricted to own profile, assigned resources, constructive feedback, and chatbot sessions. 403 Forbidden on administrative endpoints (`/api/students/roster`, `/api/students/risk-detail/*`, `/api/mentors/*`).
  - `teacher` / `admin`: Full access to cohort rosters, risk analytics, mentor configuration, and dispatch centers.
- **Zero Risk Exposure to Students**: Student API responses sanitize internal risk labels, scores, and confidence values.
- **Cross-Tenant Isolation**: Students cannot query other students' marks cards, assignments, or private resources.

---

## 🐳 Docker Setup & One-Command Deployment

### Prerequisites
- Docker Engine 24+ & Docker Compose v2+

### Run Full System (All 9 Services)
```bash
docker compose -f docker-compose.full.yml up --build
```

### Access URLs & Container Services
| Service | URL / Port | Container Name | Description |
| :--- | :--- | :--- | :--- |
| **Student Portal** | [http://localhost:3001](http://localhost:3001) | `student-ui` | Student Dashboard Web UI |
| **Admin Portal** | [http://localhost:3002](http://localhost:3002) | `admin-ui` | Faculty & Admin Roster Web UI |
| **AI Chatbot UI** | [http://localhost:3000](http://localhost:3000) | `chatbot-ui` | Standalone Chatbot Web UI |
| **Main Backend API** | [http://localhost:5000](http://localhost:5000) | `edu-backend` | REST API (Swagger docs: `/docs`) |
| **Chatbot Gateway** | [http://localhost:8000](http://localhost:8000) | `gateway` | Orchestrator API (Swagger docs: `/docs`) |
| **Student Insight Agent** | `localhost:8001` | `agent-insight` | A2A Academic Diagnosis Microservice |
| **Study Planner Agent** | `localhost:8002` | `agent-planner` | A2A Study Schedule Microservice |
| **Recovery Coach Agent** | `localhost:8003` | `agent-coach` | A2A Motivation & Coaching Microservice |
| **PostgreSQL Database** | `localhost:5432` | `db` | Databases: `eduguardian`, `eduguardian_chatbot` |

---

## 💻 Local Development Setup

### 1. Python Environment
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/macOS
pip install -r chatbot/backend/requirements.txt
```

### 2. Environment Configuration
Copy the template files and fill in your development settings:
```bash
cp .env.example .env
```

### 3. Unified Local Runner
```bash
python run_all.py
```
Or use the provided launch scripts on Windows:
```cmd
start_all.bat
```

---

## 🧪 Testing & Verification

The repository includes a comprehensive automated test suite with 100% pass rates:

```bash
# Run root regression, RBAC, and risk isolation tests (51/51 PASS)
.venv\Scripts\pytest.exe tests/ -v

# Run chatbot unit, A2A, memory, and guardrail tests
.venv\Scripts\pytest.exe chatbot/tests/ -v

# Run 20/20 End-to-End Architecture Audit
python scripts/e2e_final_audit.py
```

---

## 📁 Repository Structure

```
eduguardian/
├── .env.example                            # Root environment template
├── .gitignore                              # Git exclusion rules
├── .dockerignore                           # Docker build exclusion rules
├── docker-compose.full.yml                 # Full stack (8 services) compose definition
├── docker-compose.yml                      # Chatbot-only compose definition
├── Dockerfile                              # Chatbot Gateway & A2A Dockerfile
├── init-db.sql                             # Database schema initializer
├── seed_students.sql                       # Benchmark demo students seed
├── pytest.ini                              # Pytest configuration
├── run_all.py                              # Unified local process runner
├── start_all.bat / start_all.ps1           # Windows launch helpers
├── EduGuardian_Student_Risk_Calculation_Framework.pdf  # Technical whitepaper
│
├── ash-frontend/admin-portal/              # Faculty & Admin Portal (React + Vite)
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── pages/admin/                    # Roster, Mentors, Interventions, Reports
│       └── components/                     # Risk badges, filters, modal dialogs
│
├── prat-frontend/                          # Student Dashboard Portal (React + Vite)
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── pages/                          # Profile, Progress, Resources, Goals
│       └── services/                       # API clients and portal sync handlers
│
├── edu-backend/                            # Main Academic REST API (FastAPI)
│   ├── Dockerfile
│   ├── main.py                             # API router registration
│   ├── db.py                               # SQLAlchemy engine & session factory
│   ├── controllers/                        # Student, Mentor, Resource controllers
│   ├── routes/                             # API route declarations
│   └── utils/
│       ├── academic_risk_engine.py         # Multi-factor calibrated risk engine
│       ├── academic_guidance.py            # Constructive guidance generator
│       ├── portal_adapter.py               # University Solutions EMS adapter
│       └── jwt.py                          # Token issuance & verification
│
├── chatbot/                                # AI Conversational Subsystem
│   ├── run_a2a_services.py                 # Multi-agent microservice runner
│   ├── frontend/                           # Chatbot React/TypeScript UI
│   │   ├── Dockerfile
│   │   └── src/                            # Chat window, A2A status indicators
│   ├── backend/
│   │   ├── api/                            # FastAPI Gateway & SSE streaming
│   │   ├── orchestrator/                   # LangGraph graph & deterministic router
│   │   ├── agents/                         # Insight, Planner, Recovery Coach
│   │   ├── guardrails/                     # 3-Stage safety & grounding filters
│   │   └── core/                           # Memory, conversation history, TTL cache
│   └── tests/                              # 19 Chatbot test modules
│
├── tests/                                  # Root Regression & Security Test Suite
│   ├── test_admin_portal_roster.py         # Hybrid roster & risk detail tests
│   ├── test_role_based_risk_isolation.py   # RBAC & student data protection tests
│   ├── test_marks_card_extraction.py       # EMS parsing & marks card extraction
│   └── test_dynamic_academic_guidance.py   # Guidance generation tests
│
└── scripts/                                # Maintenance & Audit Utilities
    ├── docker_migrate.py                   # Container schema migration helper
    ├── e2e_final_audit.py                  # 20/20 Complete architecture audit
    ├── e2e_full_verification.py            # End-to-end full system verifier
    └── test_portal_adapter_e2e.py          # Portal adapter verification
```

---

## 🛡️ Security Notes & Best Practices

1. **Never Commit Secrets**: Ensure `.env` is never added to version control. Use `.env.example` as a template with placeholders only.
2. **JWT Secret Rotation**: Generate strong, cryptographically random keys for production deployments (`openssl rand -hex 32`).
3. **Database Credentials**: In production environments, override default compose credentials via environment variables or secret managers.
4. **Authoritative Context Sanitation**: Student endpoints must always use the sanitization pipeline to strip raw risk scores and diagnostic metadata before delivery to the browser.
