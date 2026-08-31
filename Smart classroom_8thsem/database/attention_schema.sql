-- Attention Detection Schema
-- Add to existing database

-- Class attention logs table
CREATE TABLE IF NOT EXISTS class_attention_logs (
    id SERIAL PRIMARY KEY,
    class_id INTEGER,
    faculty_id INTEGER REFERENCES faculty(id) ON DELETE SET NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_students INTEGER DEFAULT 0,
    attentive_count INTEGER DEFAULT 0,
    distracted_count INTEGER DEFAULT 0,
    sleeping_count INTEGER DEFAULT 0,
    attentive_percentage FLOAT DEFAULT 0.0,
    distracted_percentage FLOAT DEFAULT 0.0,
    sleeping_percentage FLOAT DEFAULT 0.0,
    session_duration INTEGER DEFAULT 0, -- in seconds
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Individual student attention logs
CREATE TABLE IF NOT EXISTS student_attention_logs (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    class_attention_log_id INTEGER REFERENCES class_attention_logs(id) ON DELETE CASCADE,
    status VARCHAR(20) CHECK (status IN ('attentive', 'distracted', 'sleeping', 'no_face')),
    confidence FLOAT DEFAULT 0.0,
    eye_aspect_ratio FLOAT,
    head_pitch FLOAT,
    head_yaw FLOAT,
    head_roll FLOAT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_class_attention_timestamp ON class_attention_logs(timestamp);
CREATE INDEX idx_class_attention_faculty ON class_attention_logs(faculty_id);
CREATE INDEX idx_student_attention_student ON student_attention_logs(student_id);
CREATE INDEX idx_student_attention_class ON student_attention_logs(class_attention_log_id);
CREATE INDEX idx_student_attention_status ON student_attention_logs(status);

-- View for attention analytics
CREATE OR REPLACE VIEW attention_analytics AS
SELECT 
    cal.id,
    cal.timestamp,
    f.name as faculty_name,
    cal.total_students,
    cal.attentive_percentage,
    cal.distracted_percentage,
    cal.sleeping_percentage,
    cal.session_duration,
    CASE 
        WHEN cal.attentive_percentage >= 80 THEN 'Excellent'
        WHEN cal.attentive_percentage >= 60 THEN 'Good'
        WHEN cal.attentive_percentage >= 40 THEN 'Average'
        ELSE 'Poor'
    END as attention_grade
FROM class_attention_logs cal
LEFT JOIN faculty f ON cal.faculty_id = f.id
ORDER BY cal.timestamp DESC;

-- Function to calculate attention statistics
CREATE OR REPLACE FUNCTION calculate_attention_stats(log_id INTEGER)
RETURNS TABLE(
    attentive_pct FLOAT,
    distracted_pct FLOAT,
    sleeping_pct FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(SUM(CASE WHEN status = 'attentive' THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) * 100, 0) as attentive_pct,
        COALESCE(SUM(CASE WHEN status = 'distracted' THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) * 100, 0) as distracted_pct,
        COALESCE(SUM(CASE WHEN status = 'sleeping' THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*), 0) * 100, 0) as sleeping_pct
    FROM student_attention_logs
    WHERE class_attention_log_id = log_id;
END;
$$ LANGUAGE plpgsql;

-- Sample data for testing
INSERT INTO class_attention_logs (class_id, faculty_id, total_students, attentive_count, distracted_count, sleeping_count, attentive_percentage, distracted_percentage, sleeping_percentage, session_duration)
VALUES 
(1, 1, 30, 24, 4, 2, 80.0, 13.3, 6.7, 3600),
(2, 2, 25, 20, 3, 2, 80.0, 12.0, 8.0, 3600);
