-- ============================================================
-- EduGuardian Docker Init: Create databases & full schema
-- ============================================================

SELECT 'CREATE DATABASE eduguardian'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'eduguardian')\gexec

SELECT 'CREATE DATABASE eduguardian_chatbot'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'eduguardian_chatbot')\gexec

-- ============================================================
-- EDUGUARDIAN DATABASE SCHEMA
-- ============================================================
\connect eduguardian

CREATE TABLE IF NOT EXISTS users (
    id serial primary key,
    full_name varchar(100) not null,
    email varchar(150) unique not null,
    password_hash text not null,
    role varchar(20) not null check (role in ('student', 'teacher', 'admin')),
    is_active boolean default true,
    created_at timestamp default current_timestamp
);

CREATE TABLE IF NOT EXISTS students (
    id serial primary key,
    user_id int unique not null references users(id) on delete cascade,
    usn varchar(20) unique not null,
    department varchar(100),
    semester int,
    section varchar(20),
    enrollment_year int,
    data_source varchar(50) default 'demo',
    created_at timestamp default current_timestamp
);

CREATE TABLE IF NOT EXISTS teachers (
    id serial primary key,
    user_id int unique not null references users(id) on delete cascade,
    employee_id varchar(30) unique,
    department varchar(100),
    designation varchar(100) default 'Assistant Professor',
    capacity int default 5,
    is_active boolean default true,
    phone varchar(30),
    created_at timestamp default current_timestamp
);

CREATE TABLE IF NOT EXISTS teacher_assignments (
    id serial primary key,
    teacher_id int not null references teachers(id) on delete cascade,
    department varchar(100) not null,
    semester int not null,
    section varchar(20) not null,
    subject_code varchar(50),
    is_class_admin boolean default false,
    created_at timestamp default current_timestamp,
    unique (teacher_id, department, semester, section, subject_code)
);

CREATE TABLE IF NOT EXISTS mentor_assignments (
    id serial primary key,
    student_id int not null references students(id) on delete cascade,
    mentor_id int not null references teachers(id) on delete cascade,
    assigned_by int references users(id),
    status varchar(20) default 'active',
    notes text,
    assigned_at timestamp default current_timestamp,
    updated_at timestamp default current_timestamp
);

CREATE TABLE IF NOT EXISTS assignments (
    id serial primary key,
    department varchar(100) not null,
    semester int not null,
    section varchar(20) not null,
    subject_code varchar(50) not null,
    created_by int not null references teachers(id),
    assignment_name varchar(150) not null,
    max_marks decimal(6,2),
    due_date date,
    resource_name varchar(255),
    resource_url text,
    created_at timestamp default current_timestamp
);

CREATE TABLE IF NOT EXISTS assignment_submissions (
    id serial primary key,
    student_id int not null references students(id) on delete cascade,
    assignment_id int references assignments(id) on delete cascade,
    submission_status varchar(20) check (submission_status in ('submitted', 'missed', 'late')),
    submission_date date,
    marks_obtained decimal(6,2),
    file_name varchar(255),
    file_url text,
    file_type varchar(100),
    created_at timestamp default current_timestamp
);

CREATE TABLE IF NOT EXISTS attendance_records (
    id serial primary key,
    student_id int not null references students(id) on delete cascade,
    subject_code varchar(50),
    subject_name varchar(150),
    classes_held int,
    classes_attended int,
    attendance_percentage decimal(5,2),
    recorded_at timestamp default current_timestamp,
    source varchar(50) default 'college_portal'
);

CREATE TABLE IF NOT EXISTS subjects (
    id serial primary key,
    subject_code varchar(50) unique not null,
    subject_name varchar(150) not null,
    course_type varchar(20) not null,
    created_at timestamp default current_timestamp
);

CREATE TABLE IF NOT EXISTS quiz_results (
    id serial primary key,
    student_id int not null references students(id) on delete cascade,
    subject_code varchar(50),
    quiz_name varchar(150),
    marks_obtained decimal(6,2),
    max_marks decimal(6,2),
    quiz_date date default current_date,
    created_at timestamp default current_timestamp
);

CREATE TABLE IF NOT EXISTS risk_predictions (
    id serial primary key,
    student_id int not null references students(id) on delete cascade,
    risk_level varchar(20),
    recovery_probability decimal(5,2),
    support_signal text,
    attendance_change decimal(5,2),
    lms_activity_change decimal(5,2),
    missed_assignments int,
    model_name varchar(50),
    model_version varchar(20),
    created_at timestamp default current_timestamp
);

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

-- Seed Subjects
INSERT INTO subjects (subject_code, subject_name, course_type) VALUES
    ('IS3001-1', 'DCN: Data Communication and Networking', 'IPCC'),
    ('IS2002-1', 'ML: Machine Learning Foundations', 'IPCC'),
    ('IS3101-1', 'OS: Operating Systems Fundamentals', 'PCC'),
    ('HU1011-1', 'UHV: Universal Human Values', 'HSMC'),
    ('IS1604-1', 'MD: MERNSTACK Development', 'PCC')
ON CONFLICT (subject_code) DO NOTHING;

-- Seed Teachers:
-- 1. Dr. Sarah Jenkins: teacher@example.com / teacher123
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES ('Dr. Sarah Jenkins', 'teacher@example.com', '$2b$12$KKBYuRi5fTzfbr11gKK1oO2et1Pkrv7RomSVsF3H9SDptBrja6r4q', 'teacher', true)
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name;

INSERT INTO teachers (user_id, employee_id, department, designation, capacity, is_active)
SELECT id, 'EMP-001', 'ISE', 'Associate Professor', 10, true FROM users WHERE email = 'teacher@example.com'
ON CONFLICT (user_id) DO UPDATE SET designation = 'Associate Professor', capacity = 10, is_active = true;

-- 2. Dr. Ahmed Khan: ahmed.khan@university.edu / mentor123
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES ('Dr. Ahmed Khan', 'ahmed.khan@university.edu', '$2b$12$ENvT64sc6xP7Z.PFeAzIieZ5tD7/8V9NXZM7/lvAdLZf3hXMSqhWO', 'teacher', true)
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name, password_hash = EXCLUDED.password_hash;

INSERT INTO teachers (user_id, employee_id, department, designation, capacity, is_active)
SELECT id, 'EMP-002', 'ISE', 'Professor', 8, true FROM users WHERE email = 'ahmed.khan@university.edu'
ON CONFLICT (user_id) DO UPDATE SET designation = 'Professor', capacity = 8, is_active = true;

-- Seed Default Student: student@eduguardian.ai / student123
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES ('Alex Johnson', 'student@eduguardian.ai', '$2b$12$Okr.UwLokb3URnbGraNzNe/dVqbhw1IAyvYqoHeY463mcAXGVMDRa', 'student', true)
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name;

INSERT INTO students (user_id, usn, department, semester, section, enrollment_year, data_source)
SELECT id, '1MS21IS001', 'ISE', 5, 'C', 2022, 'demo' FROM users WHERE email = 'student@eduguardian.ai'
ON CONFLICT (user_id) DO UPDATE SET usn = '1MS21IS001', department = 'ISE', semester = 5, section = 'C';

-- Seed Teacher Assignments
INSERT INTO teacher_assignments (teacher_id, department, semester, section, subject_code, is_class_admin)
SELECT t.id, 'ISE', 5, 'C', NULL, true FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'teacher@example.com'
ON CONFLICT DO NOTHING;

INSERT INTO teacher_assignments (teacher_id, department, semester, section, subject_code, is_class_admin)
SELECT t.id, 'ISE', 5, 'C', 'IS3001-1', false FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'teacher@example.com'
ON CONFLICT DO NOTHING;

-- Seed Sample Assignment
INSERT INTO assignments (department, semester, section, subject_code, created_by, assignment_name, max_marks, due_date, resource_name, resource_url)
SELECT 'ISE', 5, 'C', 'IS3001-1', t.id, 'Network Layer Subnetting Assignment', 100.0, (CURRENT_DATE + INTERVAL '7 days')::date, 'Subnetting_Guide.pdf', 'http://localhost:5000/uploads/Subnetting_Guide.pdf'
FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'teacher@example.com'
LIMIT 1
ON CONFLICT DO NOTHING;

-- ============================================================
-- EDUGUARDIAN CHATBOT DATABASE SCHEMA
-- ============================================================
\connect eduguardian_chatbot

CREATE TABLE IF NOT EXISTS conversations (
    id uuid primary key,
    student_id varchar(128) not null,
    title varchar(256),
    created_at timestamp with time zone default current_timestamp,
    updated_at timestamp with time zone default current_timestamp
);

CREATE INDEX IF NOT EXISTS ix_conversations_student_id ON conversations (student_id);

CREATE TABLE IF NOT EXISTS messages (
    id uuid primary key,
    conversation_id uuid not null references conversations(id) on delete cascade,
    role varchar(16) not null,
    content text not null,
    structured_data jsonb,
    agents_used jsonb,
    created_at timestamp with time zone default current_timestamp
);

CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages (conversation_id);
