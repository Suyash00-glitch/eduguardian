from db import get_db
from sqlalchemy import text

db = next(get_db())

print('Existing tables:')
tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")).fetchall()
for t in tables:
    print(' ', t[0])

# Run all column additions in separate statements
# Teachers table
try:
    db.execute(text("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS designation VARCHAR(100) DEFAULT 'Assistant Professor'"))
    print("Added teachers.designation")
except Exception as e:
    print(f"teachers.designation: {e}")

try:
    db.execute(text("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS capacity INTEGER DEFAULT 5"))
    print("Added teachers.capacity")
except Exception as e:
    print(f"teachers.capacity: {e}")

try:
    db.execute(text("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT true"))
    print("Added teachers.is_active")
except Exception as e:
    print(f"teachers.is_active: {e}")

try:
    db.execute(text("ALTER TABLE teachers ADD COLUMN IF NOT EXISTS phone VARCHAR(30)"))
    print("Added teachers.phone")
except Exception as e:
    print(f"teachers.phone: {e}")

# mentor_assignments
try:
    db.execute(text("ALTER TABLE mentor_assignments ADD COLUMN IF NOT EXISTS notes TEXT"))
    print("Added mentor_assignments.notes")
except Exception as e:
    print(f"mentor_assignments.notes: {e}")

try:
    db.execute(text("ALTER TABLE mentor_assignments ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
    print("Added mentor_assignments.updated_at")
except Exception as e:
    print(f"mentor_assignments.updated_at: {e}")

# student_resources - check what cols exist first
sr_cols = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'student_resources'")).fetchall()
print("student_resources columns:", [c[0] for c in sr_cols])

if sr_cols:
    try:
        db.execute(text("ALTER TABLE student_resources ADD COLUMN IF NOT EXISTS description TEXT"))
        print("Added student_resources.description")
    except Exception as e:
        print(f"student_resources.description: {e}")

    try:
        db.execute(text("ALTER TABLE student_resources ADD COLUMN IF NOT EXISTS target_student_id INTEGER"))
        print("Added student_resources.target_student_id")
    except Exception as e:
        print(f"student_resources.target_student_id: {e}")
else:
    # Create the table
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS student_resources (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL,
            teacher_id INTEGER NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            resource_url TEXT NOT NULL,
            resource_type VARCHAR(50) DEFAULT 'PDF',
            target_category VARCHAR(50) DEFAULT 'ALL',
            target_student_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_read BOOLEAN DEFAULT false
        )
    """))
    print("Created student_resources table")

# Update existing teachers
db.execute(text("UPDATE teachers SET designation = 'Assistant Professor', capacity = 5, is_active = true WHERE id = 1"))
db.execute(text("UPDATE teachers SET designation = 'Associate Professor', capacity = 10, is_active = true WHERE id = 2"))

# Add Dr. Ahmed Khan if not exists
existing = db.execute(text("SELECT id FROM teachers WHERE UPPER(employee_id) = 'EMP-002'")).mappings().first()
if not existing:
    import bcrypt
    pwd = bcrypt.hashpw(b"mentor123", bcrypt.gensalt()).decode()
    res = db.execute(text("""
        INSERT INTO users (full_name, email, password_hash, role)
        VALUES ('Dr. Ahmed Khan', 'ahmed.khan@university.edu', :pwd, 'teacher')
        RETURNING id
    """), {"pwd": pwd}).mappings().first()
    ahmed_uid = res["id"]
    db.execute(text("""
        INSERT INTO teachers (user_id, employee_id, department, designation, capacity, is_active)
        VALUES (:uid, 'EMP-002', 'ISE', 'Professor', 8, true)
    """), {"uid": ahmed_uid})
    print("Added Dr. Ahmed Khan")
else:
    print("Dr. Ahmed Khan already exists")

db.commit()
print("Docker DB migration completed successfully!")
