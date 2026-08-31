from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, faculty, student
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Student(db.Model):
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    face_encoding = db.Column(db.Text)  # Stored as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    attendances = db.relationship('Attendance', backref='student', lazy=True)

class Faculty(db.Model):
    __tablename__ = 'faculty'
    
    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    
    # Relationships
    schedules = db.relationship('Schedule', backref='faculty', lazy=True)

class Classroom(db.Model):
    __tablename__ = 'classrooms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    capacity = db.Column(db.Integer, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    equipment = db.Column(db.Text)  # JSON string of available equipment
    status = db.Column(db.String(20), default='available')  # available, occupied, maintenance
    current_class = db.Column(db.String(100))
    
    # Relationships
    schedules = db.relationship('Schedule', backref='classroom', lazy=True)
    usage_logs = db.relationship('ClassroomUsage', backref='classroom', lazy=True)

class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    semester = db.Column(db.String(20), nullable=False)
    
    # Relationships
    attendances = db.relationship('Attendance', backref='schedule', lazy=True)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='present')  # present, absent, late
    confidence_score = db.Column(db.Float)  # Face recognition confidence

class ClassroomUsage(db.Model):
    __tablename__ = 'classroom_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.Integer, nullable=False)  # 0-23
    occupancy_count = db.Column(db.Integer, default=0)
    utilization_rate = db.Column(db.Float, default=0.0)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

class ChatLog(db.Model):
    __tablename__ = 'chat_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(100))

class LectureNote(db.Model):
    __tablename__ = 'lecture_notes'

    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey('schedules.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    transcript = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    audio_file_path = db.Column(db.String(500))
    pdf_file_path = db.Column(db.String(500))
    recording_date = db.Column(db.DateTime, default=datetime.utcnow)
    duration_minutes = db.Column(db.Integer)
    status = db.Column(db.String(20), default='processing')  # recording, processing, completed


# ── Learning Interaction Module Models ────────────────────────────────────────

class Material(db.Model):
    __tablename__ = 'materials'

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    chapter = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.Text, nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(100), nullable=False)
    chapter = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    time_limit = db.Column(db.Integer, nullable=False)  # minutes
    deadline = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('Question', backref='quiz', lazy=True, cascade='all, delete-orphan')
    attempts = db.relationship('QuizAttempt', backref='quiz', lazy=True, cascade='all, delete-orphan')


class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    option1 = db.Column(db.String(300), nullable=False)
    option2 = db.Column(db.String(300), nullable=False)
    option3 = db.Column(db.String(300), nullable=False)
    option4 = db.Column(db.String(300), nullable=False)
    correct_answer = db.Column(db.Integer, nullable=False)  # 1-4


class QuizAttempt(db.Model):
    __tablename__ = 'quiz_attempts'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False, default=0)
    total = db.Column(db.Integer, nullable=False, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)