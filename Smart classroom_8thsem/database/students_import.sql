-- Student Data Import - 3 Students
-- Auto-generated login credentials: Username = Roll No, Password = Roll No

-- Insert students into database
INSERT INTO students (student_id, name, email, department, year, gender, phone, city) VALUES
('20221CSE0308', 'MANOJ P', 'manoj@gmail.com', 'CSE', 2022, 'Male', '9353300449', 'Bangalore'),
('20221CSE0680', 'Jyothi Prasad', 'jyothi@gmail.com', 'CSE AI', 2022, 'Male', '9353635315', 'Tumkur'),
('20221CSE0530', 'Jnan Sowrab', 'jnan@gmail.com', 'CSE ML', 2022, 'Male', '9986748526', 'Shivamogga');

-- Insert login credentials (Password = Roll Number)
INSERT INTO users (username, password_hash, role) VALUES
('20221CSE0308', SHA2('20221CSE0308', 256), 'student'),
('20221CSE0680', SHA2('20221CSE0680', 256), 'student'),
('20221CSE0530', SHA2('20221CSE0530', 256), 'student');

-- Verify insertion
SELECT * FROM students;
SELECT username, role FROM users WHERE role = 'student';
