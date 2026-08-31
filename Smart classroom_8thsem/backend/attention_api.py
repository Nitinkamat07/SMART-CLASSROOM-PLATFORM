from flask import Blueprint, request, jsonify
from flask_socketio import emit
from backend.attention_detector import AttentionDetector
from backend.models import db
from datetime import datetime
import base64
import cv2
import numpy as np

attention_bp = Blueprint('attention', __name__)
detector = AttentionDetector()

# Store active sessions
active_sessions = {}

@attention_bp.route('/api/attention/start-session', methods=['POST'])
def start_attention_session():
    """Start a new attention monitoring session"""
    data = request.json
    faculty_id = data.get('faculty_id')
    class_id = data.get('class_id')
    
    session_id = f"{faculty_id}_{class_id}_{datetime.now().timestamp()}"
    
    # Create database entry
    from sqlalchemy import text
    query = text("""
        INSERT INTO class_attention_logs (class_id, faculty_id, total_students, session_duration)
        VALUES (:class_id, :faculty_id, 0, 0)
        RETURNING id
    """)
    result = db.session.execute(query, {'class_id': class_id, 'faculty_id': faculty_id})
    log_id = result.fetchone()[0]
    db.session.commit()
    
    active_sessions[session_id] = {
        'log_id': log_id,
        'start_time': datetime.now(),
        'faculty_id': faculty_id,
        'class_id': class_id
    }
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'log_id': log_id
    })

@attention_bp.route('/api/attention/process-frame', methods=['POST'])
def process_attention_frame():
    """Process a single frame for attention detection"""
    data = request.json
    session_id = data.get('session_id')
    frame_data = data.get('frame')
    
    if session_id not in active_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    # Decode base64 frame
    frame_bytes = base64.b64decode(frame_data.split(',')[1])
    nparr = np.frombuffer(frame_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Detect attention
    status, confidence, details = detector.detect_attention(frame)
    stats = detector.get_attention_stats()
    
    # Emit to WebSocket
    from app import socketio
    socketio.emit('attention_update', {
        'session_id': session_id,
        'status': status,
        'confidence': confidence,
        'stats': stats,
        'timestamp': datetime.now().isoformat()
    })
    
    return jsonify({
        'success': True,
        'status': status,
        'confidence': confidence,
        'stats': stats
    })

@attention_bp.route('/api/attention/end-session', methods=['POST'])
def end_attention_session():
    """End attention monitoring session and save results"""
    data = request.json
    session_id = data.get('session_id')
    
    if session_id not in active_sessions:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = active_sessions[session_id]
    log_id = session['log_id']
    duration = (datetime.now() - session['start_time']).seconds
    
    # Get final statistics
    stats = detector.get_attention_stats()
    
    # Update database
    from sqlalchemy import text
    query = text("""
        UPDATE class_attention_logs
        SET attentive_percentage = :attentive,
            distracted_percentage = :distracted,
            sleeping_percentage = :sleeping,
            session_duration = :duration
        WHERE id = :log_id
    """)
    db.session.execute(query, {
        'attentive': stats['attentive'],
        'distracted': stats['distracted'],
        'sleeping': stats['sleeping'],
        'duration': duration,
        'log_id': log_id
    })
    db.session.commit()
    
    # Clean up
    del active_sessions[session_id]
    detector.attention_history.clear()
    
    return jsonify({
        'success': True,
        'stats': stats,
        'duration': duration
    })

@attention_bp.route('/api/attention/stats/<int:log_id>', methods=['GET'])
def get_attention_stats(log_id):
    """Get attention statistics for a specific log"""
    from sqlalchemy import text
    query = text("""
        SELECT * FROM class_attention_logs WHERE id = :log_id
    """)
    result = db.session.execute(query, {'log_id': log_id}).fetchone()
    
    if not result:
        return jsonify({'error': 'Log not found'}), 404
    
    return jsonify({
        'id': result[0],
        'class_id': result[1],
        'faculty_id': result[2],
        'timestamp': result[3].isoformat(),
        'total_students': result[4],
        'attentive_count': result[5],
        'distracted_count': result[6],
        'sleeping_count': result[7],
        'attentive_percentage': result[8],
        'distracted_percentage': result[9],
        'sleeping_percentage': result[10],
        'session_duration': result[11]
    })

@attention_bp.route('/api/attention/history', methods=['GET'])
def get_attention_history():
    """Get attention monitoring history"""
    faculty_id = request.args.get('faculty_id')
    limit = request.args.get('limit', 10)
    
    from sqlalchemy import text
    query = text("""
        SELECT * FROM attention_analytics
        WHERE faculty_id = :faculty_id OR :faculty_id IS NULL
        ORDER BY timestamp DESC
        LIMIT :limit
    """)
    results = db.session.execute(query, {'faculty_id': faculty_id, 'limit': limit}).fetchall()
    
    history = []
    for row in results:
        history.append({
            'id': row[0],
            'timestamp': row[1].isoformat(),
            'faculty_name': row[2],
            'total_students': row[3],
            'attentive_percentage': row[4],
            'distracted_percentage': row[5],
            'sleeping_percentage': row[6],
            'session_duration': row[7],
            'attention_grade': row[8]
        })
    
    return jsonify({'history': history})
