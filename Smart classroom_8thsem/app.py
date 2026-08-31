from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import os
import threading
from datetime import datetime, timedelta
import json
from werkzeug.utils import secure_filename
from backend.models import db, User, Student, Classroom, Schedule, Attendance, LectureNote
from backend.face_recognition_system import FaceRecognitionSystem
from backend.ml_predictor import ClassroomPredictor
from backend.chatbot import SmartChatbot
from backend.auth import AuthManager
from backend.lecture_notes_generator import LectureNotesGenerator
from backend.materials import materials_bp
from backend.quiz import quiz_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/classroom_db')
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")
CORS(app)

app.register_blueprint(materials_bp, url_prefix='/api')
app.register_blueprint(quiz_bp, url_prefix='/api')

# Initialize AI systems
face_system = FaceRecognitionSystem()
predictor = ClassroomPredictor()
chatbot = SmartChatbot()
auth_manager = AuthManager()
lecture_generator = LectureNotesGenerator()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        user = auth_manager.authenticate(data['username'], data['password'])
        if user:
            session['user_id'] = user.id
            session['role'] = user.role
            return jsonify({'success': True, 'role': user.role})
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    return render_template('login.html')

@app.route('/dashboard/<role>')
def dashboard(role):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template(f'{role}/dashboard.html')

@app.route('/api/classrooms')
def get_classrooms():
    classrooms = Classroom.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'capacity': c.capacity,
        'status': c.status,
        'current_class': c.current_class
    } for c in classrooms])

@app.route('/api/attendance', methods=['POST'])
def mark_attendance():
    data = request.get_json()
    image_data = data['image']
    
    # Process face recognition
    student_id = face_system.recognize_face(image_data)
    
    if student_id:
        attendance = Attendance(
            student_id=student_id,
            schedule_id=data['schedule_id'],
            timestamp=datetime.now(),
            status='present'
        )
        db.session.add(attendance)
        db.session.commit()
        
        # Emit real-time update
        socketio.emit('attendance_update', {
            'student_id': student_id,
            'status': 'present',
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'success': True, 'student_id': student_id})
    
    return jsonify({'success': False, 'message': 'Face not recognized'})

@app.route('/api/predict-usage')
def predict_usage():
    predictions = predictor.predict_classroom_usage()
    return jsonify(predictions)

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    response = chatbot.get_response(data['message'])
    return jsonify({'response': response})

@app.route('/api/admin/students', methods=['POST'])
def add_student():
    data = request.get_json()
    student = Student(
        name=data['name'],
        student_id=data['student_id'],
        email=data['email'],
        department=data['department']
    )
    db.session.add(student)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/admin/upload-face', methods=['POST'])
def upload_face():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file uploaded'})
    
    file = request.files['file']
    student_id = request.form['student_id']
    
    if file and file.filename:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Train face recognition model
        face_system.add_face(student_id, filepath)
        
        return jsonify({'success': True})
    
    return jsonify({'success': False, 'message': 'Invalid file'})

@socketio.on('join_room')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('status', {'msg': f'Joined room {room}'})

@socketio.on('classroom_update')
def handle_classroom_update(data):
    emit('classroom_status', data, broadcast=True)

@app.route('/api/lecture/start-recording', methods=['POST'])
def start_recording():
    data = request.get_json()
    schedule_id = data['schedule_id']
    
    result = lecture_generator.start_recording(schedule_id)
    
    lecture_note = LectureNote(
        schedule_id=schedule_id,
        title=data.get('title', 'Untitled Lecture'),
        transcript='',
        summary='',
        status='recording'
    )
    db.session.add(lecture_note)
    db.session.commit()
    
    return jsonify({'success': True, 'lecture_id': lecture_note.id})

@app.route('/api/lecture/stop-recording', methods=['POST'])
def stop_recording():
    data = request.get_json()
    lecture_id = data['lecture_id']
    
    lecture_note = LectureNote.query.get(lecture_id)
    if not lecture_note:
        return jsonify({'success': False, 'message': 'Lecture not found'})
    
    audio_path = lecture_generator.stop_recording(lecture_id)
    lecture_note.audio_file_path = audio_path
    lecture_note.status = 'processing'
    db.session.commit()
    
    # Process in background
    def process_lecture():
        transcript = lecture_generator.transcribe_audio(audio_path, lecture_id)
        summary = lecture_generator.summarize_lecture(transcript)
        
        schedule = Schedule.query.get(lecture_note.schedule_id)
        pdf_path = f'uploads/lectures/lecture_{lecture_id}.pdf'
        
        lecture_generator.generate_pdf({
            'title': lecture_note.title,
            'date': lecture_note.recording_date.strftime('%Y-%m-%d'),
            'faculty': schedule.faculty.name,
            'subject': schedule.subject,
            'transcript': transcript,
            'summary': summary
        }, pdf_path)
        
        lecture_note.transcript = transcript
        lecture_note.summary = summary
        lecture_note.pdf_file_path = pdf_path
        lecture_note.status = 'completed'
        db.session.commit()
    
    threading.Thread(target=process_lecture).start()
    
    return jsonify({'success': True, 'message': 'Processing lecture'})

@app.route('/api/lecture/get-lecture-notes')
def get_lecture_notes():
    schedule_id = request.args.get('schedule_id')
    student_id = request.args.get('student_id')
    
    query = LectureNote.query
    if schedule_id:
        query = query.filter_by(schedule_id=schedule_id)
    
    lectures = query.order_by(LectureNote.recording_date.desc()).all()
    
    return jsonify([{
        'id': l.id,
        'title': l.title,
        'date': l.recording_date.strftime('%Y-%m-%d %H:%M'),
        'summary': l.summary,
        'status': l.status,
        'pdf_url': f'/api/lecture/download/{l.id}'
    } for l in lectures])

@app.route('/api/lecture/download/<int:lecture_id>')
def download_lecture(lecture_id):
    lecture = LectureNote.query.get(lecture_id)
    if not lecture or not lecture.pdf_file_path:
        return jsonify({'error': 'Lecture not found'}), 404
    
    from flask import send_file
    return send_file(lecture.pdf_file_path, as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)