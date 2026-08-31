-- Lecture Notes Table Schema
CREATE TABLE IF NOT EXISTS lecture_notes (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER NOT NULL REFERENCES schedules(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    transcript TEXT NOT NULL,
    summary TEXT NOT NULL,
    audio_file_path VARCHAR(500),
    pdf_file_path VARCHAR(500),
    recording_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_minutes INTEGER,
    status VARCHAR(20) DEFAULT 'processing',
    CONSTRAINT fk_schedule FOREIGN KEY (schedule_id) REFERENCES schedules(id)
);

-- Create index for faster queries
CREATE INDEX idx_lecture_notes_schedule ON lecture_notes(schedule_id);
CREATE INDEX idx_lecture_notes_date ON lecture_notes(recording_date DESC);
CREATE INDEX idx_lecture_notes_status ON lecture_notes(status);
