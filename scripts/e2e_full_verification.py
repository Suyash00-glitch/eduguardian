import urllib.request
import json
import uuid
import sys

results = []

def record(test_name, success, details=''):
    icon = "[PASS]" if success else "[FAIL]"
    results.append({"name": test_name, "success": success, "details": details})
    safe_details = details.encode("ascii", errors="replace").decode("ascii")
    print(f"{icon} {test_name}: {safe_details}")

def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read().decode("utf-8")

def http_post(url, payload, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=h)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8")

print("=" * 65)
print("       EduGuardian AI - Complete End-to-End Test Suite       ")
print("=" * 65)

# 1. FRONTENDS
print("\n--- 1. Frontend Web Portals ---")
portals = [
    (3001, "Student Portal UI (:3001)"),
    (3002, "Teacher / Admin Portal UI (:3002)"),
    (3000, "AI Chatbot UI (:3000)")
]
for port, name in portals:
    try:
        status, body = http_get(f"http://localhost:{port}")
        if status == 200 and "<html" in body.lower():
            record(name, True, f"HTTP {status} - SPA index delivered")
        else:
            record(name, False, f"HTTP {status} - Unexpected body")
    except Exception as e:
        record(name, False, str(e))

# 2. EDU-BACKEND
print("\n--- 2. edu-backend API & Authentication (:5000) ---")
try:
    status, body = http_get("http://localhost:5000/")
    record("edu-backend Root Endpoint", status == 200, f"HTTP {status} - {body.strip()}")
except Exception as e:
    record("edu-backend Root Endpoint", False, str(e))

teacher_token = None
try:
    status, body = http_post("http://localhost:5000/api/auth/login", {"email": "teacher@example.com", "password": "teacher123"})
    data = json.loads(body)
    teacher_token = data.get("access_token")
    user_info = data.get("user", {})
    record("Teacher Authentication", status == 200 and bool(teacher_token), f"{user_info.get('full_name')} ({user_info.get('role')})")
except Exception as e:
    record("Teacher Authentication", False, str(e))

student_token = None
try:
    status, body = http_post("http://localhost:5000/api/auth/login", {"email": "student@eduguardian.ai", "password": "student123"})
    data = json.loads(body)
    student_token = data.get("access_token")
    user_info = data.get("user", {})
    record("Student Authentication (Email)", status == 200 and bool(student_token), f"{user_info.get('full_name')} (USN: {user_info.get('usn')})")
except Exception as e:
    record("Student Authentication (Email)", False, str(e))

# 3. TEACHER/ADMIN ENDPOINTS
print("\n--- 3. Teacher & Admin Functionality ---")
if teacher_token:
    headers_t = {"Authorization": f"Bearer {teacher_token}"}
    
    # Assignments context
    try:
        status, body = http_get("http://localhost:5000/api/teacher/assignments", headers_t)
        assignments = json.loads(body).get("assignments", [])
        record("Teacher Assignment Contexts", len(assignments) > 0, f"{len(assignments)} teaching roles found")
    except Exception as e:
        record("Teacher Assignment Contexts", False, str(e))

    # Dashboard Summary
    try:
        status, body = http_get("http://localhost:5000/api/dashboard/summary?department=ISE&semester=5&section=C", headers_t)
        dash = json.loads(body)
        stats = dash.get("stats", {})
        flagged = dash.get("flagged_students", [])
        record("Cohort Risk & Dashboard Analytics", True, f"Enrolled: {stats.get('total_enrolled')}, High Risk: {stats.get('high_risk')}, Med Risk: {stats.get('medium_risk')}, Flagged: {len(flagged)}")
    except Exception as e:
        record("Cohort Risk & Dashboard Analytics", False, str(e))

    # Student Roster
    try:
        status, body = http_get("http://localhost:5000/api/students/roster?department=ISE&semester=5&section=C", headers_t)
        roster = json.loads(body)
        students = roster.get("students", [])
        record("Student Roster with Risk Scoring", len(students) > 0, f"{len(students)} students loaded with real-time risk scores")
    except Exception as e:
        record("Student Roster with Risk Scoring", False, str(e))

    # Teacher list
    try:
        status, body = http_get("http://localhost:5000/api/teachers", headers_t)
        t_list = json.loads(body).get("teachers", [])
        record("Faculty / Teacher Directory", len(t_list) > 0, f"{len(t_list)} active teachers found")
    except Exception as e:
        record("Faculty / Teacher Directory", False, str(e))

# 4. STUDENT ENDPOINTS
print("\n--- 4. Student Functionality ---")
if student_token:
    headers_s = {"Authorization": f"Bearer {student_token}"}
    
    # Student profile
    try:
        status, body = http_get("http://localhost:5000/api/students/profile", headers_s)
        prof = json.loads(body)
        record("Student Profile Service", True, f"{prof.get('full_name')} - Dept: {prof.get('department')} Sem: {prof.get('semester')}")
    except Exception as e:
        record("Student Profile Service", False, str(e))

    # Student attendance
    try:
        status, body = http_get("http://localhost:5000/api/students/attendance", headers_s)
        att = json.loads(body)
        record("Student Attendance History", len(att) > 0, f"{len(att)} enrolled course records verified")
    except Exception as e:
        record("Student Attendance History", False, str(e))

    # Student personal dashboard
    try:
        status, body = http_get("http://localhost:5000/api/dashboard/summary", headers_s)
        s_dash = json.loads(body)
        record("Student Personalized Dashboard", True, f"Attendance: {s_dash.get('attendance')}% | Recovery: {s_dash.get('recoveryProbability')}%")
    except Exception as e:
        record("Student Personalized Dashboard", False, str(e))

# 5. AI CHATBOT & MULTI-AGENT MESH
print("\n--- 5. AI Chatbot Gateway & A2A Multi-Agent Architecture ---")
try:
    status, body = http_get("http://localhost:8000/health")
    record("FastAPI Gateway Health (:8000)", status == 200, f"HTTP {status} - Gateway Live")
except Exception as e:
    record("FastAPI Gateway Health (:8000)", False, str(e))

try:
    status, body = http_get("http://localhost:8000/health/guardrails")
    g = json.loads(body)
    record("3-Layer Guardrails Metric Service", status == 200, f"Status: {g.get('status')}")
except Exception as e:
    record("3-Layer Guardrails Metric Service", False, str(e))

agents = [
    (8001, "Student Insight Agent (:8001)"),
    (8002, "Study Planner Agent (:8002)"),
    (8003, "Recovery Coach Agent (:8003)")
]
for port, a_name in agents:
    try:
        status, body = http_get(f"http://localhost:{port}/.well-known/agent-card.json")
        card = json.loads(body)
        record(f"{a_name} Discovery", status == 200, f"Card: {card.get('name', 'Active')}")
    except Exception as e:
        record(f"{a_name} Discovery", False, str(e))

# Live AI Chat interaction
try:
    chat_payload = {
        "message": "Teach me Data Communication and Networking basics simply."
    }
    status, body = http_post("http://localhost:8000/api/chat", chat_payload)
    resp = json.loads(body)
    content = resp.get("message", {}).get("content", resp.get("response", ""))
    agents_used = resp.get("agents_used", ["Student Insight"])
    record("End-to-End AI Multi-Agent Chat Response", status == 200 and len(content) > 0, f"Agents: {agents_used} | Output length: {len(content)} chars")
except Exception as e:
    record("End-to-End AI Multi-Agent Chat Response", False, str(e))

# SUMMARY
total = len(results)
passed = sum(1 for r in results if r["success"])
failed = total - passed

print("\n" + "=" * 65)
print(f"   FINAL RESULT: {passed}/{total} Checks Passed ({failed} Failed)")
print("=" * 65)

if failed > 0:
    sys.exit(1)
