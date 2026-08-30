"""
Database Migration: student_goals, goal_milestones, and seed data for student_resources
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")
DB_NAME = "eduguardian"

def run_migration():
    print(f"Connecting to {DB_NAME} on {DB_HOST}:{DB_PORT} as {DB_USER}...")
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        dbname=DB_NAME
    )
    conn.autocommit = True
    cur = conn.cursor(cursor_factory=RealDictCursor)

    print("1. Creating student_goals table if not exists...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_goals (
            id serial primary key,
            student_id int not null references students(id) on delete cascade,
            title varchar(255) not null,
            category varchar(50) default 'Academic',
            target varchar(100) not null,
            progress int default 0,
            status varchar(30) default 'in-progress',
            due_date date,
            created_at timestamp default current_timestamp,
            updated_at timestamp default current_timestamp
        );
    """)

    print("2. Creating goal_milestones table if not exists...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS goal_milestones (
            id serial primary key,
            goal_id int not null references student_goals(id) on delete cascade,
            title varchar(255) not null,
            completed boolean default false,
            completed_at timestamp,
            created_at timestamp default current_timestamp
        );
    """)

    print("3. Ensuring student_resources table exists...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_resources (
            id serial primary key,
            student_id int not null references students(id) on delete cascade,
            teacher_id int not null references teachers(id) on delete cascade,
            title varchar(255) not null,
            description text,
            resource_url text not null,
            resource_type varchar(50) default 'PDF',
            target_category varchar(50) default 'ALL',
            target_student_id int,
            created_at timestamp default current_timestamp,
            is_read boolean default false
        );
    """)

    print("4. Seeding student resources for demo and existing students...")
    cur.execute("""
        INSERT INTO student_resources (student_id, teacher_id, title, description, resource_url, resource_type, target_category)
        SELECT s.id, t.id, 'Data Communication & Networking - Complete Unit Notes', 'Comprehensive lecture notes covering OSI model, TCP/IP, IP subnetting, and routing protocols.', 'https://en.wikipedia.org/wiki/Computer_network', 'PDF', 'ALL'
        FROM students s, teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'teacher@example.com' AND s.usn = '1MS21IS001'
        ON CONFLICT DO NOTHING;

        INSERT INTO student_resources (student_id, teacher_id, title, description, resource_url, resource_type, target_category)
        SELECT s.id, t.id, 'Machine Learning Foundations - Lab Manual & Datasets', 'Hands-on Jupyter notebooks, gradient descent examples, and supervised learning algorithms.', 'https://en.wikipedia.org/wiki/Machine_learning', 'PDF', 'ALL'
        FROM students s, teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'teacher@example.com' AND s.usn = '1MS21IS001'
        ON CONFLICT DO NOTHING;

        INSERT INTO student_resources (student_id, teacher_id, title, description, resource_url, resource_type, target_category)
        SELECT s.id, t.id, 'Operating Systems - Process Synchronization & Scheduling Guide', 'Detailed breakdown of Semaphores, Deadlock detection algorithms (Banker''s), and Virtual Memory.', 'https://en.wikipedia.org/wiki/Operating_system', 'Guide', 'ALL'
        FROM students s, teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'teacher@example.com' AND s.usn = '1MS21IS001'
        ON CONFLICT DO NOTHING;

        INSERT INTO student_resources (student_id, teacher_id, title, description, resource_url, resource_type, target_category)
        SELECT s.id, t.id, 'MERN Stack Development - REST API & MongoDB Schema Design', 'Full-stack application blueprint, JWT auth patterns, Express routing, and React state hooks.', 'https://en.wikipedia.org/wiki/MEAN_(solution_stack)', 'PDF', 'ALL'
        FROM students s, teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'teacher@example.com' AND s.usn = '1MS21IS001'
        ON CONFLICT DO NOTHING;

        INSERT INTO student_resources (student_id, teacher_id, title, description, resource_url, resource_type, target_category)
        SELECT s.id, t.id, 'Universal Human Values - Case Studies & Ethics Handbook', 'Course reading pack on self-exploration, professional ethics, and harmonious living guidelines.', 'https://en.wikipedia.org/wiki/Ethics', 'PDF', 'ALL'
        FROM students s, teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'teacher@example.com' AND s.usn = '1MS21IS001'
        ON CONFLICT DO NOTHING;
    """)

    print("5. Seeding initial goals and milestones for demo student...")
    cur.execute("""
        INSERT INTO student_goals (id, student_id, title, category, target, progress, status, due_date)
        SELECT 1, s.id, 'Maintain 85% Attendance', 'Attendance', '85%', 66, 'in-progress', (CURRENT_DATE + INTERVAL '30 days')::date
        FROM students s WHERE s.usn = '1MS21IS001'
        ON CONFLICT (id) DO NOTHING;

        INSERT INTO goal_milestones (id, goal_id, title, completed) VALUES
        (1, 1, 'Attend all DCN lectures this week (4/4)', true),
        (2, 1, 'Attend all ML Foundations lectures (3/3)', true),
        (3, 1, 'Check OS attendance record on portal by Friday', false)
        ON CONFLICT (id) DO NOTHING;

        INSERT INTO student_goals (id, student_id, title, category, target, progress, status, due_date)
        SELECT 2, s.id, 'Complete All Coursework & Assignments', 'Assignment', '100%', 33, 'in-progress', (CURRENT_DATE + INTERVAL '20 days')::date
        FROM students s WHERE s.usn = '1MS21IS001'
        ON CONFLICT (id) DO NOTHING;

        INSERT INTO goal_milestones (id, goal_id, title, completed) VALUES
        (4, 2, 'Submit Network Layer Subnetting Assignment in DCN', true),
        (5, 2, 'Complete ML Foundation Lab Exercise 3', false),
        (6, 2, 'Verify submission status with course mentor', false)
        ON CONFLICT (id) DO NOTHING;

        INSERT INTO student_goals (id, student_id, title, category, target, progress, status, due_date)
        SELECT 3, s.id, 'Target 8.5+ SGPA in Semester 5', 'Academic', 'SGPA 8.5', 50, 'on-track', (CURRENT_DATE + INTERVAL '60 days')::date
        FROM students s WHERE s.usn = '1MS21IS001'
        ON CONFLICT (id) DO NOTHING;

        INSERT INTO goal_milestones (id, goal_id, title, completed) VALUES
        (7, 3, 'Complete 2 hours of self-study on DCN routing protocols', true),
        (8, 3, 'Score 18+ in ML Internal Assessment 1', false)
        ON CONFLICT (id) DO NOTHING;

        SELECT setval(pg_get_serial_sequence('student_goals', 'id'), coalesce(max(id), 1)) FROM student_goals;
        SELECT setval(pg_get_serial_sequence('goal_milestones', 'id'), coalesce(max(id), 1)) FROM goal_milestones;
    """)

    print("Migration finished successfully!")
    cur.close()
    conn.close()

if __name__ == "__main__":
    run_migration()
