from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import json
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key'

# Database configuration for Vercel compatibility
DB_PATH = '/tmp/classroom.db' if os.environ.get('VERCEL') else 'classroom.db'

def get_db_connection():
    return sqlite3.connect(DB_PATH)


# Initialize SQLite database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            student_id TEXT UNIQUE,
            name TEXT,
            email TEXT,
            department TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classrooms (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE,
            capacity INTEGER,
            status TEXT DEFAULT 'available'
        )
    ''')
    
    # Insert demo data
    cursor.execute("INSERT OR IGNORE INTO users VALUES (1, 'admin', 'admin123', 'admin')")
    cursor.execute("INSERT OR IGNORE INTO users VALUES (2, 'faculty', 'faculty123', 'faculty')")
    cursor.execute("INSERT OR IGNORE INTO users VALUES (3, 'student', 'student123', 'student')")
    
    cursor.execute("INSERT OR IGNORE INTO classrooms VALUES (1, 'A101', 50, 'available')")
    cursor.execute("INSERT OR IGNORE INTO classrooms VALUES (2, 'A102', 40, 'occupied')")
    cursor.execute("INSERT OR IGNORE INTO classrooms VALUES (3, 'B201', 60, 'available')")
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        username = data['username']
        password = data['password']
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['role'] = user[3]
            return jsonify({'success': True, 'role': user[3]})
        return jsonify({'success': False, 'message': 'Invalid credentials'})
    
    return render_template('login.html')

@app.route('/dashboard/<role>')
def dashboard(role):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template(f'{role}/dashboard.html')

@app.route('/api/classrooms')
def get_classrooms():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classrooms")
    classrooms = cursor.fetchall()
    conn.close()
    
    return jsonify([{
        'id': c[0],
        'name': c[1],
        'capacity': c[2],
        'status': c[3],
        'current_class': 'Demo Class' if c[3] == 'occupied' else None
    } for c in classrooms])

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    message = data['message'].lower()
    
    if 'classroom' in message or 'room' in message:
        response = "A101 is available, A102 is occupied, B201 is available."
    elif 'attendance' in message:
        response = "Your attendance rate is 85%. You've attended 17 out of 20 classes."
    elif 'schedule' in message:
        response = "Today's classes: Data Structures at 9:00 AM in A101, Algorithms at 2:00 PM in B201."
    else:
        response = "I can help you with classroom availability, attendance records, and schedules. What would you like to know?"
    
    return jsonify({'response': response})

@app.route('/api/attendance', methods=['POST'])
def mark_attendance():
    # Simulate face recognition
    return jsonify({'success': True, 'student_id': 1, 'message': 'Attendance marked successfully!'})


@app.route('/api/student/<int:student_id>/attendance-stats')
def get_attendance_stats(student_id):
    return jsonify({'percentage': 85, 'attended': 34, 'total': 40})

@app.route('/api/student/<int:student_id>/today-schedule')
def get_today_schedule(student_id):
    return jsonify([
        {'id': 1, 'subject': 'Data Structures', 'start_time': '09:00', 'end_time': '10:30', 'classroom_name': 'A101', 'faculty_name': 'Dr. Smith'},
        {'id': 2, 'subject': 'Algorithms', 'start_time': '11:00', 'end_time': '12:30', 'classroom_name': 'B201', 'faculty_name': 'Prof. Johnson'}
    ])

@app.route('/api/student/<int:student_id>/schedule')
def get_schedule(student_id):
    return jsonify([
        {'id': 1, 'subject': 'Data Structures', 'day_of_week': 1, 'start_time': '09:00', 'end_time': '10:30', 'classroom_name': 'A101', 'faculty_name': 'Dr. Smith'},
        {'id': 2, 'subject': 'Algorithms', 'day_of_week': 1, 'start_time': '11:00', 'end_time': '12:30', 'classroom_name': 'B201', 'faculty_name': 'Prof. Johnson'},
        {'id': 3, 'subject': 'Database Systems', 'day_of_week': 2, 'start_time': '10:00', 'end_time': '11:30', 'classroom_name': 'C301', 'faculty_name': 'Dr. Lee'},
        {'id': 4, 'subject': 'Operating Systems', 'day_of_week': 3, 'start_time': '14:00', 'end_time': '15:30', 'classroom_name': 'A102', 'faculty_name': 'Dr. Brown'}
    ])

@app.route('/api/student/<int:student_id>/attendance-records')
def get_attendance_records(student_id):
    return jsonify([
        {'date': '2023-10-01', 'subject': 'Data Structures', 'start_time': '09:00', 'end_time': '10:30', 'status': 'present', 'classroom_name': 'A101'},
        {'date': '2023-10-02', 'subject': 'Database Systems', 'start_time': '10:00', 'end_time': '11:30', 'status': 'late', 'classroom_name': 'C301'},
        {'date': '2023-10-03', 'subject': 'Operating Systems', 'start_time': '14:00', 'end_time': '15:30', 'status': 'absent', 'classroom_name': 'A102'}
    ])

@app.route('/api/student/<int:student_id>/current-class')
def get_current_class(student_id):
    return jsonify({'id': 1, 'subject': 'Data Structures', 'classroom_name': 'A101', 'faculty_name': 'Dr. Smith'})

@app.route('/api/get-quizzes')
def get_quizzes():
    import datetime
    future = datetime.datetime.now() + datetime.timedelta(days=7)
    return jsonify([
        {'id': 1, 'title': 'Midterm Practice', 'subject': 'Data Structures', 'chapter': 'Trees', 'question_count': 5, 'time_limit': 10, 'deadline': future.isoformat()}
    ])

@app.route('/api/attempt-quiz/<int:quiz_id>')
def attempt_quiz(quiz_id):
    return jsonify({
        'success': True,
        'title': 'Midterm Practice',
        'time_limit': 10,
        'questions': [
            {'id': 1, 'question': 'What is the time complexity of binary search?', 'options': ['O(1)', 'O(n)', 'O(log n)', 'O(n^2)']},
            {'id': 2, 'question': 'Which data structure uses LIFO?', 'options': ['Queue', 'Stack', 'Tree', 'Graph']}
        ]
    })

@app.route('/api/submit-quiz', methods=['POST'])
def submit_quiz():
    return jsonify({'success': True, 'score': 2, 'total': 2, 'percentage': 100})

@app.route('/api/my-results')
def my_results():
    return jsonify([
        {'quiz_title': 'Midterm Practice', 'subject': 'Data Structures', 'timestamp': '2023-10-10 14:00', 'score': 2, 'total': 2, 'percentage': 100}
    ])


@app.route('/api/students')
def get_students():
    return jsonify([
        {'id': 1, 'name': 'Alice Smith', 'student_id': 'S001', 'department': 'Computer Science', 'email': 'alice@example.com', 'attendance_rate': 92},
        {'id': 2, 'name': 'Bob Jones', 'student_id': 'S002', 'department': 'Computer Science', 'email': 'bob@example.com', 'attendance_rate': 78}
    ])

@app.route('/api/attendance/stats')
def get_admin_attendance_stats():
    return jsonify({
        'overall_rate': 85,
        'present_today': 120,
        'absent_today': 15,
        'late_today': 5,
        'recent_records': []
    })

@app.route('/api/predict-usage')
def mock_predict_usage():
    return jsonify([
        {'time': '09:00', 'predicted_occupancy': 45},
        {'time': '10:00', 'predicted_occupancy': 50},
        {'time': '11:00', 'predicted_occupancy': 30},
        {'time': '12:00', 'predicted_occupancy': 10},
        {'time': '13:00', 'predicted_occupancy': 40}
    ])

@app.route('/api/optimization-suggestions')
def optimization_suggestions():
    return jsonify([
        "Turn off lights in A102 as it's predicted to be empty.",
        "Move CS101 to B201 for better capacity utilization."
    ])

@app.route('/api/admin/students', methods=['POST'])
def mock_add_student():
    return jsonify({'success': True, 'message': 'Student added successfully'})

@app.route('/api/admin/upload-face', methods=['POST'])
def mock_upload_face():
    return jsonify({'success': True, 'message': 'Face model updated successfully'})


@app.route('/api/create-quiz', methods=['POST'])
def create_quiz():
    return jsonify({'success': True, 'message': 'Quiz created successfully', 'quiz_id': 2})

@app.route('/api/quiz-results/<int:quiz_id>')
def get_quiz_results(quiz_id):
    return jsonify([
        {'student_name': 'Alice Smith', 'score': 4, 'total': 5, 'percentage': 80, 'timestamp': '2023-10-10 14:00'},
        {'student_name': 'Bob Jones', 'score': 2, 'total': 5, 'percentage': 40, 'timestamp': '2023-10-10 14:05'}
    ])

@app.route('/api/ai-analysis/<int:quiz_id>')
def ai_analysis(quiz_id):
    return jsonify({
        'weak_questions': [
            {'question': 'What is the time complexity of binary search?', 'wrong_count': 12},
            {'question': 'Which data structure uses LIFO?', 'wrong_count': 5}
        ]
    })

init_db()

if __name__ == '__main__':
    print("Smart Classroom Management System Starting...")
    print("Access the application at: http://localhost:5000")
    print("Login credentials:")
    print("   Admin: admin / admin123")
    print("   Faculty: faculty / faculty123") 
    print("   Student: student / student123")
    app.run(debug=True, host='0.0.0.0', port=5000)