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
    submission_status varchar(20) check (submission_status in ('submitted', 'missed', 'late', 'graded')),
    submission_date date,
    marks_obtained decimal(6,2),
    feedback text,
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
    student_id int references students(id) on delete cascade,
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

CREATE TABLE IF NOT EXISTS goal_milestones (
    id serial primary key,
    goal_id int not null references student_goals(id) on delete cascade,
    title varchar(255) not null,
    completed boolean default false,
    completed_at timestamp,
    created_at timestamp default current_timestamp
);

CREATE TABLE IF NOT EXISTS portal_student_contexts (
    user_id int primary key references users(id) on delete cascade,
    student_context jsonb not null,
    updated_at timestamp default current_timestamp
);

-- Seed Subjects
INSERT INTO subjects (subject_code, subject_name, course_type) VALUES
    ('IS3001-1', 'DCN: Data Communication and Networking', 'IPCC'),
    ('IS2002-1', 'ML: Machine Learning Foundations', 'IPCC'),
    ('IS3101-1', 'OS: Operating Systems Fundamentals', 'PCC'),
    ('HU1011-1', 'UHV: Universal Human Values', 'HSMC'),
    ('IS1604-1', 'MD: MERNSTACK Development', 'PCC'),
    ('UM1003-1', 'ESD: Employability Skill Development', 'AEC'),
    ('HU1007-1', 'SCR: Social Connect & Responsibility', 'AEC'),
    ('HU1010-1', 'RM: Research Methodology', 'AEC')
ON CONFLICT (subject_code) DO NOTHING;

-- Seed NMAMIT ISE Semester 5 Section C Faculty Members: Default Password = 123456 ($2b$12$aizgSEhfyaL2eD/KUlvwmeETsPAbZbrJEvwwqYorv2iV.l2/t4342)

-- 1. Dr. Preethi Salian K (Class Advisor & UHV Faculty)
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES ('Dr. Preethi Salian K', 'preethi.salian@nitte.edu.in', '$2b$12$aizgSEhfyaL2eD/KUlvwmeETsPAbZbrJEvwwqYorv2iV.l2/t4342', 'teacher', true)
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name, password_hash = EXCLUDED.password_hash;

INSERT INTO teachers (user_id, employee_id, department, designation, capacity, is_active)
SELECT id, 'EMP-PSK', 'ISE', 'Associate Professor & Class Advisor', 15, true FROM users WHERE email = 'preethi.salian@nitte.edu.in'
ON CONFLICT (user_id) DO UPDATE SET employee_id = 'EMP-PSK', department = 'ISE', designation = 'Associate Professor & Class Advisor', capacity = 15, is_active = true;

-- 2. Dr. Ravi B (DCN Faculty)
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES ('Dr. Ravi B', 'ravi.b@nitte.edu.in', '$2b$12$aizgSEhfyaL2eD/KUlvwmeETsPAbZbrJEvwwqYorv2iV.l2/t4342', 'teacher', true)
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name, password_hash = EXCLUDED.password_hash;

INSERT INTO teachers (user_id, employee_id, department, designation, capacity, is_active)
SELECT id, 'EMP-RB', 'ISE', 'Professor', 10, true FROM users WHERE email = 'ravi.b@nitte.edu.in'
ON CONFLICT (user_id) DO UPDATE SET employee_id = 'EMP-RB', department = 'ISE', designation = 'Professor', capacity = 10, is_active = true;

-- 3. Dr. Ramesh G (ML Faculty)
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES ('Dr. Ramesh G', 'ramesh.g@nitte.edu.in', '$2b$12$aizgSEhfyaL2eD/KUlvwmeETsPAbZbrJEvwwqYorv2iV.l2/t4342', 'teacher', true)
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name, password_hash = EXCLUDED.password_hash;

INSERT INTO teachers (user_id, employee_id, department, designation, capacity, is_active)
SELECT id, 'EMP-RG', 'ISE', 'Professor', 10, true FROM users WHERE email = 'ramesh.g@nitte.edu.in'
ON CONFLICT (user_id) DO UPDATE SET employee_id = 'EMP-RG', department = 'ISE', designation = 'Professor', capacity = 10, is_active = true;

-- 4. Ms. Prathyakshini (OS Faculty)
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES ('Ms. Prathyakshini', 'prathyakshini@nitte.edu.in', '$2b$12$aizgSEhfyaL2eD/KUlvwmeETsPAbZbrJEvwwqYorv2iV.l2/t4342', 'teacher', true)
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name, password_hash = EXCLUDED.password_hash;

INSERT INTO teachers (user_id, employee_id, department, designation, capacity, is_active)
SELECT id, 'EMP-PR', 'ISE', 'Assistant Professor', 10, true FROM users WHERE email = 'prathyakshini@nitte.edu.in'
ON CONFLICT (user_id) DO UPDATE SET employee_id = 'EMP-PR', department = 'ISE', designation = 'Assistant Professor', capacity = 10, is_active = true;

-- 5. Mr. Krishnamoorthy C (MD / MERN Faculty)
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES ('Mr. Krishnamoorthy C', 'krishnamoorthy@nitte.edu.in', '$2b$12$aizgSEhfyaL2eD/KUlvwmeETsPAbZbrJEvwwqYorv2iV.l2/t4342', 'teacher', true)
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name, password_hash = EXCLUDED.password_hash;

INSERT INTO teachers (user_id, employee_id, department, designation, capacity, is_active)
SELECT id, 'EMP-KC', 'ISE', 'Assistant Professor', 8, true FROM users WHERE email = 'krishnamoorthy@nitte.edu.in'
ON CONFLICT (user_id) DO UPDATE SET employee_id = 'EMP-KC', department = 'ISE', designation = 'Assistant Professor', capacity = 8, is_active = true;

-- 6. Dr. Deepa (ESD Faculty)
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES ('Dr. Deepa', 'deepa@nitte.edu.in', '$2b$12$aizgSEhfyaL2eD/KUlvwmeETsPAbZbrJEvwwqYorv2iV.l2/t4342', 'teacher', true)
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name, password_hash = EXCLUDED.password_hash;

INSERT INTO teachers (user_id, employee_id, department, designation, capacity, is_active)
SELECT id, 'EMP-DS', 'ISE', 'Assistant Professor', 8, true FROM users WHERE email = 'deepa@nitte.edu.in'
ON CONFLICT (user_id) DO UPDATE SET employee_id = 'EMP-DS', department = 'ISE', designation = 'Assistant Professor', capacity = 8, is_active = true;

-- 7. Dr. Santhosh S (SCR Faculty)
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES ('Dr. Santhosh S', 'santhosh.s@nitte.edu.in', '$2b$12$aizgSEhfyaL2eD/KUlvwmeETsPAbZbrJEvwwqYorv2iV.l2/t4342', 'teacher', true)
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name, password_hash = EXCLUDED.password_hash;

INSERT INTO teachers (user_id, employee_id, department, designation, capacity, is_active)
SELECT id, 'EMP-SS', 'ISE', 'Assistant Professor', 8, true FROM users WHERE email = 'santhosh.s@nitte.edu.in'
ON CONFLICT (user_id) DO UPDATE SET employee_id = 'EMP-SS', department = 'ISE', designation = 'Assistant Professor', capacity = 8, is_active = true;

-- 8. Dr. Vasudeva (RM Faculty)
INSERT INTO users (full_name, email, password_hash, role, is_active)
VALUES ('Dr. Vasudeva', 'vasudeva@nitte.edu.in', '$2b$12$aizgSEhfyaL2eD/KUlvwmeETsPAbZbrJEvwwqYorv2iV.l2/t4342', 'teacher', true)
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name, password_hash = EXCLUDED.password_hash;

INSERT INTO teachers (user_id, employee_id, department, designation, capacity, is_active)
SELECT id, 'EMP-VD', 'ISE', 'Professor', 10, true FROM users WHERE email = 'vasudeva@nitte.edu.in'
ON CONFLICT (user_id) DO UPDATE SET employee_id = 'EMP-VD', department = 'ISE', designation = 'Professor', capacity = 10, is_active = true;

-- Teacher Assignments for ISE Semester 5 Section C
-- Class Advisor (Admin role)
INSERT INTO teacher_assignments (teacher_id, department, semester, section, subject_code, is_class_admin)
SELECT t.id, 'ISE', 5, 'C', NULL, true FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'preethi.salian@nitte.edu.in'
ON CONFLICT DO NOTHING;

-- Subject Roles
INSERT INTO teacher_assignments (teacher_id, department, semester, section, subject_code, is_class_admin)
SELECT t.id, 'ISE', 5, 'C', 'HU1011-1', false FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'preethi.salian@nitte.edu.in'
ON CONFLICT DO NOTHING;

INSERT INTO teacher_assignments (teacher_id, department, semester, section, subject_code, is_class_admin)
SELECT t.id, 'ISE', 5, 'C', 'IS3001-1', false FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'ravi.b@nitte.edu.in'
ON CONFLICT DO NOTHING;

INSERT INTO teacher_assignments (teacher_id, department, semester, section, subject_code, is_class_admin)
SELECT t.id, 'ISE', 5, 'C', 'IS2002-1', false FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'ramesh.g@nitte.edu.in'
ON CONFLICT DO NOTHING;

INSERT INTO teacher_assignments (teacher_id, department, semester, section, subject_code, is_class_admin)
SELECT t.id, 'ISE', 5, 'C', 'IS3101-1', false FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'prathyakshini@nitte.edu.in'
ON CONFLICT DO NOTHING;

INSERT INTO teacher_assignments (teacher_id, department, semester, section, subject_code, is_class_admin)
SELECT t.id, 'ISE', 5, 'C', 'IS1604-1', false FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'krishnamoorthy@nitte.edu.in'
ON CONFLICT DO NOTHING;

INSERT INTO teacher_assignments (teacher_id, department, semester, section, subject_code, is_class_admin)
SELECT t.id, 'ISE', 5, 'C', 'UM1003-1', false FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'deepa@nitte.edu.in'
ON CONFLICT DO NOTHING;

INSERT INTO teacher_assignments (teacher_id, department, semester, section, subject_code, is_class_admin)
SELECT t.id, 'ISE', 5, 'C', 'HU1007-1', false FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'santhosh.s@nitte.edu.in'
ON CONFLICT DO NOTHING;

INSERT INTO teacher_assignments (teacher_id, department, semester, section, subject_code, is_class_admin)
SELECT t.id, 'ISE', 5, 'C', 'HU1010-1', false FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'vasudeva@nitte.edu.in'
ON CONFLICT DO NOTHING;

-- Seed Sample Assignment
INSERT INTO assignments (department, semester, section, subject_code, created_by, assignment_name, max_marks, due_date, resource_name, resource_url)
SELECT 'ISE', 5, 'C', 'IS3001-1', t.id, 'Network Layer Subnetting Assignment', 100.0, (CURRENT_DATE + INTERVAL '7 days')::date, 'Subnetting_Guide.pdf', 'http://localhost:5000/uploads/Subnetting_Guide.pdf'
FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'ravi.b@nitte.edu.in'
LIMIT 1
ON CONFLICT DO NOTHING;

-- Students are populated dynamically upon live portal login.
-- No hardcoded mock students or demo goals.

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
