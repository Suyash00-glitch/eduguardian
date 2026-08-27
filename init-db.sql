-- ============================================================
-- EduGuardian Docker Init: Create databases & seed demo data
-- ============================================================

SELECT 'CREATE DATABASE eduguardian'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'eduguardian')\gexec

SELECT 'CREATE DATABASE eduguardian_chatbot'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'eduguardian_chatbot')\gexec

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
    created_at timestamp default current_timestamp
);

CREATE TABLE IF NOT EXISTS teachers (
    id serial primary key,
    user_id int unique not null references users(id) on delete cascade,
    employee_id varchar(30) unique,
    department varchar(100),
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

INSERT INTO subjects (subject_code, subject_name, course_type) VALUES
    ('IS3001-1', 'DCN: Data Communication and Networking', 'IPCC'),
    ('IS2002-1', 'ML: Machine Learning Foundations', 'IPCC'),
    ('IS3101-1', 'OS: Operating Systems Fundamentals', 'PCC'),
    ('HU1011-1', 'UHV: Universal Human Values', 'HSMC'),
    ('IS1604-1', 'MD: MERNSTACK Development', 'PCC')
ON CONFLICT (subject_code) DO NOTHING;

-- Seed Student: student@eduguardian.ai / student123
INSERT INTO users (id, full_name, email, password_hash, role, is_active)
VALUES (1, 'Alex Johnson', 'student@eduguardian.ai', '$2b$12$Okr.UwLokb3URnbGraNzNe/dVqbhw1IAyvYqoHeY463mcAXGVMDRa', 'student', true)
ON CONFLICT (email) DO NOTHING;

INSERT INTO students (user_id, usn, department, semester, section, enrollment_year)
SELECT id, '1MS21IS001', 'ISE', 5, 'C', 2022 FROM users WHERE email = 'student@eduguardian.ai'
ON CONFLICT (user_id) DO NOTHING;

-- Seed Teacher: teacher@example.com / teacher123
INSERT INTO users (id, full_name, email, password_hash, role, is_active)
VALUES (2, 'Dr. Sarah Jenkins', 'teacher@example.com', '$2b$12$KKBYuRi5fTzfbr11gKK1oO2et1Pkrv7RomSVsF3H9SDptBrja6r4q', 'teacher', true)
ON CONFLICT (email) DO NOTHING;

INSERT INTO teachers (user_id, employee_id, department)
SELECT id, 'EMP-001', 'ISE' FROM users WHERE email = 'teacher@example.com'
ON CONFLICT (user_id) DO NOTHING;

-- Seed Teacher Assignments
INSERT INTO teacher_assignments (teacher_id, department, semester, section, subject_code, is_class_admin)
SELECT t.id, 'ISE', 5, 'C', NULL, true FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'teacher@example.com'
ON CONFLICT DO NOTHING;

INSERT INTO teacher_assignments (teacher_id, department, semester, section, subject_code, is_class_admin)
SELECT t.id, 'ISE', 5, 'C', 'IS3001-1', false FROM teachers t JOIN users u ON t.user_id = u.id WHERE u.email = 'teacher@example.com'
ON CONFLICT DO NOTHING;
