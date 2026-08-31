-- Smart Classroom Management System Database Schema
-- PostgreSQL Database

-- Create database
CREATE DATABASE classroom_management_db;

-- Use the database
\c classroom_management_db;

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    password_hash VARCHAR(120) NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'faculty', 'student')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Faculty table
CREATE TABLE faculty (
    id SERIAL PRIMARY KEY,
    faculty_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    department VARCHAR(50) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Students table
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    student_id VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    department VARCHAR(50) NOT NULL,
    year_of_study INTEGER,
    face_encoding TEXT, -- JSON string of face encoding
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Classrooms table
CREATE TABLE classrooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    capacity INTEGER NOT NULL,
    location VARCHAR(100) NOT NULL,
    equipment TEXT, -- JSON string of available equipment
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'occupied', 'maintenance')),
    current_class VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Schedules table
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    classroom_id INTEGER REFERENCES classrooms(id) ON DELETE CASCADE,
    faculty_id INTEGER REFERENCES faculty(id) ON DELETE CASCADE,
    subject VARCHAR(100) NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week >= 0 AND day_of_week <= 6), -- 0=Monday, 6=Sunday
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    semester VARCHAR(20) NOT NULL,
    academic_year VARCHAR(10) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT valid_time_range CHECK (end_time > start_time)
);

-- Attendance table
CREATE TABLE attendance (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    schedule_id INTEGER REFERENCES schedules(id) ON DELETE CASCADE,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'present' CHECK (status IN ('present', 'absent', 'late')),
    confidence_score FLOAT, -- Face recognition confidence (0.0 to 1.0)
    marked_by VARCHAR(20) DEFAULT 'system', -- 'system' for face recognition, 'manual' for manual entry
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Classroom usage tracking table
CREATE TABLE classroom_usage (
    id SERIAL PRIMARY KEY,
    classroom_id INTEGER REFERENCES classrooms(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    hour INTEGER NOT NULL CHECK (hour >= 0 AND hour <= 23),
    occupancy_count INTEGER DEFAULT 0,
    utilization_rate FLOAT DEFAULT 0.0 CHECK (utilization_rate >= 0.0 AND utilization_rate <= 1.0),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(classroom_id, date, hour)
);

-- Chat logs table
CREATE TABLE chat_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id VARCHAR(100),
    intent VARCHAR(50),
    confidence_score FLOAT
);

-- System logs table
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    log_level VARCHAR(20) NOT NULL CHECK (log_level IN ('INFO', 'WARNING', 'ERROR', 'DEBUG')),
    message TEXT NOT NULL,
    module VARCHAR(50),
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    additional_data JSONB
);

-- Face recognition training data table
CREATE TABLE face_training_data (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    image_path VARCHAR(255) NOT NULL,
    encoding_data TEXT, -- JSON string of face encoding
    training_status VARCHAR(20) DEFAULT 'pending' CHECK (training_status IN ('pending', 'processed', 'failed')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP
);

-- Notifications table
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(20) DEFAULT 'info' CHECK (type IN ('info', 'warning', 'error', 'success')),
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_attendance_student_id ON attendance(student_id);
CREATE INDEX idx_attendance_schedule_id ON attendance(schedule_id);
CREATE INDEX idx_attendance_timestamp ON attendance(timestamp);
CREATE INDEX idx_schedules_classroom_id ON schedules(classroom_id);
CREATE INDEX idx_schedules_faculty_id ON schedules(faculty_id);
CREATE INDEX idx_schedules_day_time ON schedules(day_of_week, start_time, end_time);
CREATE INDEX idx_classroom_usage_date ON classroom_usage(date);
CREATE INDEX idx_classroom_usage_classroom_date ON classroom_usage(classroom_id, date);
CREATE INDEX idx_chat_logs_timestamp ON chat_logs(timestamp);
CREATE INDEX idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read);

-- Create triggers for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_faculty_updated_at BEFORE UPDATE ON faculty FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_classrooms_updated_at BEFORE UPDATE ON classrooms FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_schedules_updated_at BEFORE UPDATE ON schedules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing

-- Insert admin user
INSERT INTO users (username, password_hash, role) VALUES 
('admin', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'admin'), -- password: admin123
('faculty', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'faculty'), -- password: faculty123
('student', '8bb0cf6eb9b17d0f7d22b456f121257dc1254e1f01665370476383ea776df414', 'student'); -- password: student123

-- Insert sample faculty
INSERT INTO faculty (faculty_id, name, email, department, phone) VALUES 
('FAC001', 'Dr. John Smith', 'john.smith@university.edu', 'Computer Science', '+1-555-0101'),
('FAC002', 'Prof. Sarah Johnson', 'sarah.johnson@university.edu', 'Mathematics', '+1-555-0102'),
('FAC003', 'Dr. Michael Brown', 'michael.brown@university.edu', 'Physics', '+1-555-0103'),
('FAC004', 'Prof. Emily Davis', 'emily.davis@university.edu', 'Chemistry', '+1-555-0104');

-- Insert sample students
INSERT INTO students (student_id, name, email, department, year_of_study) VALUES 
('STU001', 'Alice Wilson', 'alice.wilson@student.edu', 'Computer Science', 2),
('STU002', 'Bob Martinez', 'bob.martinez@student.edu', 'Computer Science', 2),
('STU003', 'Carol Thompson', 'carol.thompson@student.edu', 'Mathematics', 3),
('STU004', 'David Lee', 'david.lee@student.edu', 'Physics', 1),
('STU005', 'Eva Garcia', 'eva.garcia@student.edu', 'Chemistry', 2);

-- Insert sample classrooms
INSERT INTO classrooms (name, capacity, location, equipment) VALUES 
('A101', 50, 'Building A, Floor 1', '{"projector": true, "whiteboard": true, "ac": true, "computers": 0}'),
('A102', 40, 'Building A, Floor 1', '{"projector": true, "whiteboard": true, "ac": true, "computers": 0}'),
('B201', 60, 'Building B, Floor 2', '{"projector": true, "whiteboard": true, "ac": true, "computers": 30}'),
('B202', 35, 'Building B, Floor 2', '{"projector": true, "whiteboard": true, "ac": true, "computers": 0}'),
('C301', 80, 'Building C, Floor 3', '{"projector": true, "whiteboard": true, "ac": true, "computers": 0}');

-- Insert sample schedules
INSERT INTO schedules (classroom_id, faculty_id, subject, day_of_week, start_time, end_time, semester, academic_year) VALUES 
(1, 1, 'Data Structures', 0, '09:00:00', '10:30:00', 'Fall', '2024'),
(1, 1, 'Algorithms', 2, '09:00:00', '10:30:00', 'Fall', '2024'),
(2, 2, 'Calculus I', 1, '11:00:00', '12:30:00', 'Fall', '2024'),
(2, 2, 'Linear Algebra', 3, '11:00:00', '12:30:00', 'Fall', '2024'),
(3, 3, 'Physics I', 0, '14:00:00', '15:30:00', 'Fall', '2024'),
(4, 4, 'Organic Chemistry', 2, '14:00:00', '15:30:00', 'Fall', '2024'),
(5, 1, 'Database Systems', 4, '10:00:00', '11:30:00', 'Fall', '2024');

-- Insert sample attendance records
INSERT INTO attendance (student_id, schedule_id, timestamp, status, confidence_score) VALUES 
(1, 1, '2024-01-15 09:05:00', 'present', 0.95),
(2, 1, '2024-01-15 09:03:00', 'present', 0.92),
(3, 2, '2024-01-16 11:02:00', 'present', 0.88),
(4, 3, '2024-01-15 14:01:00', 'present', 0.94),
(5, 4, '2024-01-17 14:05:00', 'late', 0.91);

-- Insert sample classroom usage data
INSERT INTO classroom_usage (classroom_id, date, hour, occupancy_count, utilization_rate) VALUES 
(1, '2024-01-15', 9, 45, 0.90),
(1, '2024-01-15', 10, 42, 0.84),
(2, '2024-01-16', 11, 35, 0.88),
(3, '2024-01-15', 14, 55, 0.92),
(4, '2024-01-17', 14, 30, 0.86);

-- Create views for common queries

-- View for current classroom status
CREATE VIEW current_classroom_status AS
SELECT 
    c.id,
    c.name,
    c.capacity,
    c.location,
    c.status,
    c.current_class,
    s.subject,
    s.start_time,
    s.end_time,
    f.name as faculty_name
FROM classrooms c
LEFT JOIN schedules s ON c.id = s.classroom_id 
    AND s.day_of_week = EXTRACT(DOW FROM CURRENT_DATE) - 1
    AND CURRENT_TIME BETWEEN s.start_time AND s.end_time
LEFT JOIN faculty f ON s.faculty_id = f.id;

-- View for student attendance summary
CREATE VIEW student_attendance_summary AS
SELECT 
    s.id as student_id,
    s.student_id as student_number,
    s.name as student_name,
    s.department,
    COUNT(a.id) as total_classes_attended,
    COUNT(DISTINCT sch.id) as total_scheduled_classes,
    ROUND(
        CASE 
            WHEN COUNT(DISTINCT sch.id) > 0 
            THEN (COUNT(a.id)::FLOAT / COUNT(DISTINCT sch.id)) * 100 
            ELSE 0 
        END, 2
    ) as attendance_percentage
FROM students s
LEFT JOIN attendance a ON s.id = a.student_id AND a.status = 'present'
LEFT JOIN schedules sch ON a.schedule_id = sch.id
GROUP BY s.id, s.student_id, s.name, s.department;

-- View for classroom utilization
CREATE VIEW classroom_utilization_summary AS
SELECT 
    c.id as classroom_id,
    c.name as classroom_name,
    c.capacity,
    AVG(cu.utilization_rate) as avg_utilization_rate,
    COUNT(cu.id) as usage_records,
    MAX(cu.date) as last_usage_date
FROM classrooms c
LEFT JOIN classroom_usage cu ON c.id = cu.classroom_id
WHERE cu.date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY c.id, c.name, c.capacity
ORDER BY avg_utilization_rate DESC;

-- Grant permissions (adjust as needed for your deployment)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO classroom_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO classroom_app_user;