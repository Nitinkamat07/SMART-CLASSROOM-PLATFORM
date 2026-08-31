-- Student-Teacher Learning Interaction Module Schema
-- Append to existing classroom_management_db

-- Study materials uploaded by faculty
CREATE TABLE IF NOT EXISTS materials (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(100) NOT NULL,
    chapter VARCHAR(100) NOT NULL,
    filename VARCHAR(255) NOT NULL,
    file_url TEXT NOT NULL,
    uploaded_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_materials_subject ON materials(subject);
CREATE INDEX idx_materials_chapter ON materials(chapter);

-- Quizzes created by faculty
CREATE TABLE IF NOT EXISTS quizzes (
    id SERIAL PRIMARY KEY,
    subject VARCHAR(100) NOT NULL,
    chapter VARCHAR(100) NOT NULL,
    title VARCHAR(200) NOT NULL,
    time_limit INTEGER NOT NULL,          -- minutes
    deadline TIMESTAMP NOT NULL,
    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- MCQ questions belonging to a quiz
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    quiz_id INTEGER REFERENCES quizzes(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    option1 VARCHAR(300) NOT NULL,
    option2 VARCHAR(300) NOT NULL,
    option3 VARCHAR(300) NOT NULL,
    option4 VARCHAR(300) NOT NULL,
    correct_answer INTEGER NOT NULL CHECK (correct_answer BETWEEN 1 AND 4)
);

-- Student quiz attempts and scores
CREATE TABLE IF NOT EXISTS quiz_attempts (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    quiz_id INTEGER REFERENCES quizzes(id) ON DELETE CASCADE,
    score INTEGER NOT NULL DEFAULT 0,
    total INTEGER NOT NULL DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, quiz_id)           -- one attempt per student per quiz
);

CREATE INDEX idx_quiz_attempts_quiz ON quiz_attempts(quiz_id);
CREATE INDEX idx_quiz_attempts_student ON quiz_attempts(student_id);
