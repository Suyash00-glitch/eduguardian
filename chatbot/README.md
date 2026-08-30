# EduGuardian AI — Chatbot Component
## Quick Start Guide

### Prerequisites
- Python 3.11+
- PostgreSQL (running locally)
- Node.js 18+

---

## 🚀 Backend Setup

```bash
cd c:\hackthon_2\eduguardian

# 1. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Mac/Linux

# 2. Install dependencies
pip install -r chatbot/backend/requirements.txt

# 3. Set up environment variables
copy chatbot\backend\.env.example chatbot\backend\.env
# Edit .env with your PostgreSQL URL and other settings

# 4. Create the PostgreSQL database
# Connect to PostgreSQL and run:
# CREATE DATABASE eduguardian_chatbot;

# 5. Start the backend
uvicorn chatbot.backend.api.main:app --reload --port 8000
# API docs: http://localhost:8000/docs
```

---

## 🌐 Frontend Setup

```bash
cd c:\hackthon_2\eduguardian\chatbot\frontend

# 1. Copy env file
copy .env.example .env

# 2. Install dependencies (already done during scaffold)
npm install

# 3. Start the dev server
npm run dev
# Opens at: http://localhost:5173
```

---

## 🧪 Running Tests

```bash
cd c:\hackthon_2\eduguardian
.venv\Scripts\activate

# Run all chatbot tests
pytest

# Run specific test files
pytest chatbot/tests/test_orchestrator.py -v
pytest chatbot/tests/test_recovery_coach.py -v
```

---

## 🔑 JWT Token (Development)

Before the auth teammate integrates, you can manually create a test JWT:

```python
import jwt
token = jwt.encode({"sub": "student_001"}, "replace-with-shared-jwt-secret", algorithm="HS256")
print(token)
```

Set it in the frontend browser console:
```js
localStorage.setItem('edu_token', '<paste token here>')
```

---

## 🔧 Feature Flags (in .env)

| Variable | Default | Effect |
|---|---|---|
| `USE_MOCK_LLM` | `true` | Use canned responses instead of OmniRoute |
| `USE_MOCK_STUDENT_DATA` | `true` | Use fake student profiles instead of real DB |

Set both to `false` when real integrations are ready.

---

## 📁 Key Integration Points for Teammates

| What | Where | Who |
|---|---|---|
| Real student data | `chatbot/backend/db/repositories/student_context.py` → `_get_real_student_context()` | University portal teammate |
| JWT signing/issuing | Auth service (separate) — chatbot only verifies | Auth teammate |
| OmniRoute config | `.env` → `OMNIROUTE_BASE_URL`, `OMNIROUTE_API_KEY`, `OMNIROUTE_MODEL` | You (when config arrives) |
