from fastapi import FastAPI
from routes.user import router as auth_router
from routes.student import router as student_router
from fastapi.middleware.cors import CORSMiddleware
from routes.teacher import router as teacher_router
from routes.resource import router as resource_router
from routes.assignment import router as assignment_router
from routes.teacherAssignment import router as teacher_assignment_router
from routes.mentor import router as mentor_router
from fastapi.staticfiles import StaticFiles
from routes.dashboard import router as dashboard_router




app = FastAPI(
    title="eduguardian api"
)


import os
os.makedirs("uploads", exist_ok=True)
app.mount(
    "/uploads",
    StaticFiles(directory="uploads"),
    name="uploads"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local dev (npm run dev)
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        # Docker ports
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standard REST API routes
app.include_router(auth_router)
app.include_router(student_router)
app.include_router(teacher_router)
app.include_router(resource_router)
app.include_router(assignment_router)
app.include_router(teacher_assignment_router)
app.include_router(mentor_router)
app.include_router(dashboard_router)



@app.get("/")
def root():
    return {
        "message": "eduguardian backend running"
    }