
\connect eduguardian

        INSERT INTO users (full_name, email, password_hash, role, is_active)
        VALUES ('Rahul Sharma', 'rahul.sharma@eduguardian.ai', '$2b$10$dtQgBfvzhW5zFEmswPxe0.pjWqjGlhcqoCoOOQRcc7fNJn2gycGuW', 'student', true)
        ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name;

        INSERT INTO students (user_id, usn, department, semester, section, enrollment_year)
        SELECT id, 'NNM24IS045', 'ISE', 5, 'C', 2024 FROM users WHERE email = 'rahul.sharma@eduguardian.ai'
        ON CONFLICT (user_id) DO UPDATE SET usn = 'NNM24IS045', department = 'ISE', semester = 5, section = 'C';

        DELETE FROM attendance_records WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'rahul.sharma@eduguardian.ai');
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3001-1', 'DCN: Data Communication and Networking', 38, 22, 57.89, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'rahul.sharma@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS2002-1', 'ML: Machine Learning Foundations', 38, 22, 57.89, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'rahul.sharma@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3101-1', 'OS: Operating Systems Fundamentals', 38, 22, 57.89, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'rahul.sharma@eduguardian.ai';

        DELETE FROM risk_predictions WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'rahul.sharma@eduguardian.ai');
        INSERT INTO risk_predictions (student_id, risk_level, recovery_probability, support_signal, attendance_change, lms_activity_change, missed_assignments, model_name, model_version)
        SELECT s.id, 'high', 42.5, 'Critical attendance (58%) and 3 missed assignments in OS & DCN', -5.0, -10.0, 3, 'xgboost_risk_v2', '2.1.0' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'rahul.sharma@eduguardian.ai';

        DELETE FROM quiz_results WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'rahul.sharma@eduguardian.ai');
        INSERT INTO quiz_results (student_id, subject_code, quiz_name, marks_obtained, max_marks, quiz_date)
        SELECT s.id, 'IS3001-1', 'DCN Quiz 1', 38.0, 100, CURRENT_DATE FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'rahul.sharma@eduguardian.ai';
    

        INSERT INTO users (full_name, email, password_hash, role, is_active)
        VALUES ('Priya Nair', 'priya.nair@eduguardian.ai', '$2b$10$dtQgBfvzhW5zFEmswPxe0.pjWqjGlhcqoCoOOQRcc7fNJn2gycGuW', 'student', true)
        ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name;

        INSERT INTO students (user_id, usn, department, semester, section, enrollment_year)
        SELECT id, 'NNM24IS088', 'ISE', 5, 'C', 2024 FROM users WHERE email = 'priya.nair@eduguardian.ai'
        ON CONFLICT (user_id) DO UPDATE SET usn = 'NNM24IS088', department = 'ISE', semester = 5, section = 'C';

        DELETE FROM attendance_records WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'priya.nair@eduguardian.ai');
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3001-1', 'DCN: Data Communication and Networking', 36, 22, 61.11, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'priya.nair@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS2002-1', 'ML: Machine Learning Foundations', 36, 22, 61.11, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'priya.nair@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3101-1', 'OS: Operating Systems Fundamentals', 36, 22, 61.11, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'priya.nair@eduguardian.ai';

        DELETE FROM risk_predictions WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'priya.nair@eduguardian.ai');
        INSERT INTO risk_predictions (student_id, risk_level, recovery_probability, support_signal, attendance_change, lms_activity_change, missed_assignments, model_name, model_version)
        SELECT s.id, 'high', 48.0, 'Low quiz average (42%) and irregular LMS activity', -5.0, -10.0, 2, 'xgboost_risk_v2', '2.1.0' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'priya.nair@eduguardian.ai';

        DELETE FROM quiz_results WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'priya.nair@eduguardian.ai');
        INSERT INTO quiz_results (student_id, subject_code, quiz_name, marks_obtained, max_marks, quiz_date)
        SELECT s.id, 'IS3001-1', 'DCN Quiz 1', 42.0, 100, CURRENT_DATE FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'priya.nair@eduguardian.ai';
    

        INSERT INTO users (full_name, email, password_hash, role, is_active)
        VALUES ('David Miller', 'david.miller@eduguardian.ai', '$2b$10$dtQgBfvzhW5zFEmswPxe0.pjWqjGlhcqoCoOOQRcc7fNJn2gycGuW', 'student', true)
        ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name;

        INSERT INTO students (user_id, usn, department, semester, section, enrollment_year)
        SELECT id, 'NNM24IS019', 'ISE', 5, 'C', 2024 FROM users WHERE email = 'david.miller@eduguardian.ai'
        ON CONFLICT (user_id) DO UPDATE SET usn = 'NNM24IS019', department = 'ISE', semester = 5, section = 'C';

        DELETE FROM attendance_records WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'david.miller@eduguardian.ai');
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3001-1', 'DCN: Data Communication and Networking', 40, 21, 52.5, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'david.miller@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS2002-1', 'ML: Machine Learning Foundations', 40, 21, 52.5, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'david.miller@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3101-1', 'OS: Operating Systems Fundamentals', 40, 21, 52.5, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'david.miller@eduguardian.ai';

        DELETE FROM risk_predictions WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'david.miller@eduguardian.ai');
        INSERT INTO risk_predictions (student_id, risk_level, recovery_probability, support_signal, attendance_change, lms_activity_change, missed_assignments, model_name, model_version)
        SELECT s.id, 'high', 39.0, 'Consecutive missed classes (54%) and struggling with ML concepts', -5.0, -10.0, 4, 'xgboost_risk_v2', '2.1.0' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'david.miller@eduguardian.ai';

        DELETE FROM quiz_results WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'david.miller@eduguardian.ai');
        INSERT INTO quiz_results (student_id, subject_code, quiz_name, marks_obtained, max_marks, quiz_date)
        SELECT s.id, 'IS3001-1', 'DCN Quiz 1', 35.0, 100, CURRENT_DATE FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'david.miller@eduguardian.ai';
    

        INSERT INTO users (full_name, email, password_hash, role, is_active)
        VALUES ('Sneha Rao', 'sneha.rao@eduguardian.ai', '$2b$10$dtQgBfvzhW5zFEmswPxe0.pjWqjGlhcqoCoOOQRcc7fNJn2gycGuW', 'student', true)
        ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name;

        INSERT INTO students (user_id, usn, department, semester, section, enrollment_year)
        SELECT id, 'NNM24IS092', 'ISE', 5, 'C', 2024 FROM users WHERE email = 'sneha.rao@eduguardian.ai'
        ON CONFLICT (user_id) DO UPDATE SET usn = 'NNM24IS092', department = 'ISE', semester = 5, section = 'C';

        DELETE FROM attendance_records WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'sneha.rao@eduguardian.ai');
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3001-1', 'DCN: Data Communication and Networking', 38, 28, 73.68, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'sneha.rao@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS2002-1', 'ML: Machine Learning Foundations', 38, 28, 73.68, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'sneha.rao@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3101-1', 'OS: Operating Systems Fundamentals', 38, 28, 73.68, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'sneha.rao@eduguardian.ai';

        DELETE FROM risk_predictions WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'sneha.rao@eduguardian.ai');
        INSERT INTO risk_predictions (student_id, risk_level, recovery_probability, support_signal, attendance_change, lms_activity_change, missed_assignments, model_name, model_version)
        SELECT s.id, 'medium', 74.0, 'Declining quiz trend in DCN Foundations (64%)', -5.0, -10.0, 1, 'xgboost_risk_v2', '2.1.0' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'sneha.rao@eduguardian.ai';

        DELETE FROM quiz_results WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'sneha.rao@eduguardian.ai');
        INSERT INTO quiz_results (student_id, subject_code, quiz_name, marks_obtained, max_marks, quiz_date)
        SELECT s.id, 'IS3001-1', 'DCN Quiz 1', 64.0, 100, CURRENT_DATE FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'sneha.rao@eduguardian.ai';
    

        INSERT INTO users (full_name, email, password_hash, role, is_active)
        VALUES ('Karthik Verma', 'karthik.verma@eduguardian.ai', '$2b$10$dtQgBfvzhW5zFEmswPxe0.pjWqjGlhcqoCoOOQRcc7fNJn2gycGuW', 'student', true)
        ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name;

        INSERT INTO students (user_id, usn, department, semester, section, enrollment_year)
        SELECT id, 'NNM24IS056', 'ISE', 5, 'C', 2024 FROM users WHERE email = 'karthik.verma@eduguardian.ai'
        ON CONFLICT (user_id) DO UPDATE SET usn = 'NNM24IS056', department = 'ISE', semester = 5, section = 'C';

        DELETE FROM attendance_records WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'karthik.verma@eduguardian.ai');
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3001-1', 'DCN: Data Communication and Networking', 36, 27, 75.0, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'karthik.verma@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS2002-1', 'ML: Machine Learning Foundations', 36, 27, 75.0, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'karthik.verma@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3101-1', 'OS: Operating Systems Fundamentals', 36, 27, 75.0, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'karthik.verma@eduguardian.ai';

        DELETE FROM risk_predictions WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'karthik.verma@eduguardian.ai');
        INSERT INTO risk_predictions (student_id, risk_level, recovery_probability, support_signal, attendance_change, lms_activity_change, missed_assignments, model_name, model_version)
        SELECT s.id, 'medium', 78.5, 'Average quiz performance (61%) - high potential with mentoring', -5.0, -10.0, 1, 'xgboost_risk_v2', '2.1.0' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'karthik.verma@eduguardian.ai';

        DELETE FROM quiz_results WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'karthik.verma@eduguardian.ai');
        INSERT INTO quiz_results (student_id, subject_code, quiz_name, marks_obtained, max_marks, quiz_date)
        SELECT s.id, 'IS3001-1', 'DCN Quiz 1', 61.0, 100, CURRENT_DATE FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'karthik.verma@eduguardian.ai';
    

        INSERT INTO users (full_name, email, password_hash, role, is_active)
        VALUES ('Ananya Gupta', 'ananya.gupta@eduguardian.ai', '$2b$10$dtQgBfvzhW5zFEmswPxe0.pjWqjGlhcqoCoOOQRcc7fNJn2gycGuW', 'student', true)
        ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name;

        INSERT INTO students (user_id, usn, department, semester, section, enrollment_year)
        SELECT id, 'NNM24IS012', 'ISE', 5, 'C', 2024 FROM users WHERE email = 'ananya.gupta@eduguardian.ai'
        ON CONFLICT (user_id) DO UPDATE SET usn = 'NNM24IS012', department = 'ISE', semester = 5, section = 'C';

        DELETE FROM attendance_records WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'ananya.gupta@eduguardian.ai');
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3001-1', 'DCN: Data Communication and Networking', 38, 29, 76.32, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'ananya.gupta@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS2002-1', 'ML: Machine Learning Foundations', 38, 29, 76.32, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'ananya.gupta@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3101-1', 'OS: Operating Systems Fundamentals', 38, 29, 76.32, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'ananya.gupta@eduguardian.ai';

        DELETE FROM risk_predictions WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'ananya.gupta@eduguardian.ai');
        INSERT INTO risk_predictions (student_id, risk_level, recovery_probability, support_signal, attendance_change, lms_activity_change, missed_assignments, model_name, model_version)
        SELECT s.id, 'medium', 76.0, 'Moderate LMS engagement, requires OS fundamentals review', -5.0, -10.0, 1, 'xgboost_risk_v2', '2.1.0' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'ananya.gupta@eduguardian.ai';

        DELETE FROM quiz_results WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'ananya.gupta@eduguardian.ai');
        INSERT INTO quiz_results (student_id, subject_code, quiz_name, marks_obtained, max_marks, quiz_date)
        SELECT s.id, 'IS3001-1', 'DCN Quiz 1', 68.0, 100, CURRENT_DATE FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'ananya.gupta@eduguardian.ai';
    

        INSERT INTO users (full_name, email, password_hash, role, is_active)
        VALUES ('Alex Johnson', 'student@eduguardian.ai', '$2b$10$dtQgBfvzhW5zFEmswPxe0.pjWqjGlhcqoCoOOQRcc7fNJn2gycGuW', 'student', true)
        ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name;

        INSERT INTO students (user_id, usn, department, semester, section, enrollment_year)
        SELECT id, '1MS21IS001', 'ISE', 5, 'C', 2024 FROM users WHERE email = 'student@eduguardian.ai'
        ON CONFLICT (user_id) DO UPDATE SET usn = '1MS21IS001', department = 'ISE', semester = 5, section = 'C';

        DELETE FROM attendance_records WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'student@eduguardian.ai');
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3001-1', 'DCN: Data Communication and Networking', 40, 37, 92.5, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'student@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS2002-1', 'ML: Machine Learning Foundations', 40, 37, 92.5, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'student@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3101-1', 'OS: Operating Systems Fundamentals', 40, 37, 92.5, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'student@eduguardian.ai';

        DELETE FROM risk_predictions WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'student@eduguardian.ai');
        INSERT INTO risk_predictions (student_id, risk_level, recovery_probability, support_signal, attendance_change, lms_activity_change, missed_assignments, model_name, model_version)
        SELECT s.id, 'low', 95.0, 'Consistent attendance and high quiz performance (88%)', -5.0, -10.0, 0, 'xgboost_risk_v2', '2.1.0' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'student@eduguardian.ai';

        DELETE FROM quiz_results WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'student@eduguardian.ai');
        INSERT INTO quiz_results (student_id, subject_code, quiz_name, marks_obtained, max_marks, quiz_date)
        SELECT s.id, 'IS3001-1', 'DCN Quiz 1', 88.0, 100, CURRENT_DATE FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'student@eduguardian.ai';
    

        INSERT INTO users (full_name, email, password_hash, role, is_active)
        VALUES ('Student NNM', 'nnm24is127@eduguardian.ai', '$2b$10$dtQgBfvzhW5zFEmswPxe0.pjWqjGlhcqoCoOOQRcc7fNJn2gycGuW', 'student', true)
        ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name;

        INSERT INTO students (user_id, usn, department, semester, section, enrollment_year)
        SELECT id, 'NNM24IS127', 'ISE', 5, 'C', 2024 FROM users WHERE email = 'nnm24is127@eduguardian.ai'
        ON CONFLICT (user_id) DO UPDATE SET usn = 'NNM24IS127', department = 'ISE', semester = 5, section = 'C';

        DELETE FROM attendance_records WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'nnm24is127@eduguardian.ai');
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3001-1', 'DCN: Data Communication and Networking', 38, 34, 89.47, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'nnm24is127@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS2002-1', 'ML: Machine Learning Foundations', 38, 34, 89.47, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'nnm24is127@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3101-1', 'OS: Operating Systems Fundamentals', 38, 34, 89.47, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'nnm24is127@eduguardian.ai';

        DELETE FROM risk_predictions WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'nnm24is127@eduguardian.ai');
        INSERT INTO risk_predictions (student_id, risk_level, recovery_probability, support_signal, attendance_change, lms_activity_change, missed_assignments, model_name, model_version)
        SELECT s.id, 'low', 92.0, 'Active LMS engagement and on-time submissions', -5.0, -10.0, 0, 'xgboost_risk_v2', '2.1.0' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'nnm24is127@eduguardian.ai';

        DELETE FROM quiz_results WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'nnm24is127@eduguardian.ai');
        INSERT INTO quiz_results (student_id, subject_code, quiz_name, marks_obtained, max_marks, quiz_date)
        SELECT s.id, 'IS3001-1', 'DCN Quiz 1', 82.0, 100, CURRENT_DATE FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'nnm24is127@eduguardian.ai';
    

        INSERT INTO users (full_name, email, password_hash, role, is_active)
        VALUES ('Vikram Patel', 'vikram.patel@eduguardian.ai', '$2b$10$dtQgBfvzhW5zFEmswPxe0.pjWqjGlhcqoCoOOQRcc7fNJn2gycGuW', 'student', true)
        ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name;

        INSERT INTO students (user_id, usn, department, semester, section, enrollment_year)
        SELECT id, 'NNM24IS110', 'ISE', 5, 'C', 2024 FROM users WHERE email = 'vikram.patel@eduguardian.ai'
        ON CONFLICT (user_id) DO UPDATE SET usn = 'NNM24IS110', department = 'ISE', semester = 5, section = 'C';

        DELETE FROM attendance_records WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'vikram.patel@eduguardian.ai');
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3001-1', 'DCN: Data Communication and Networking', 40, 38, 95.0, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'vikram.patel@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS2002-1', 'ML: Machine Learning Foundations', 40, 38, 95.0, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'vikram.patel@eduguardian.ai';
        INSERT INTO attendance_records (student_id, subject_code, subject_name, classes_held, classes_attended, attendance_percentage, source)
        SELECT s.id, 'IS3101-1', 'OS: Operating Systems Fundamentals', 40, 38, 95.0, 'college_portal' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'vikram.patel@eduguardian.ai';

        DELETE FROM risk_predictions WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'vikram.patel@eduguardian.ai');
        INSERT INTO risk_predictions (student_id, risk_level, recovery_probability, support_signal, attendance_change, lms_activity_change, missed_assignments, model_name, model_version)
        SELECT s.id, 'low', 98.0, 'Top quartile performance across all enrolled subjects (94%)', -5.0, -10.0, 0, 'xgboost_risk_v2', '2.1.0' FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'vikram.patel@eduguardian.ai';

        DELETE FROM quiz_results WHERE student_id = (SELECT s.id FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'vikram.patel@eduguardian.ai');
        INSERT INTO quiz_results (student_id, subject_code, quiz_name, marks_obtained, max_marks, quiz_date)
        SELECT s.id, 'IS3001-1', 'DCN Quiz 1', 94.0, 100, CURRENT_DATE FROM students s JOIN users u ON u.id = s.user_id WHERE u.email = 'vikram.patel@eduguardian.ai';
    