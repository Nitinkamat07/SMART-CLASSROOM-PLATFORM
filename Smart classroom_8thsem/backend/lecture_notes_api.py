from flask import Blueprint, request, jsonify, send_file
from backend.lecture_notes_generator import LectureNotesGenerator
from backend.pdf_generator import LectureNotesPDFGenerator
from backend.models import db
from sqlalchemy import text
from datetime import datetime
import os
import json

lecture_notes_bp = Blueprint('lecture_notes', __name__)

# Initialize generators
notes_generator = LectureNotesGenerator()
pdf_generator = LectureNotesPDFGenerator()

# Active recording sessions
active_recordings = {}

@lecture_notes_bp.route('/api/lecture-notes/start-recording', methods=['POST'])
def start_recording():
    """Start recording lecture audio"""
    data = request.json
    faculty_id = data.get('faculty_id')
    lecture_title = data.get('lecture_title')
    subject = data.get('subject')
    class_id = data.get('class_id')
    
    # Create database entry
    query = text("""
        INSERT INTO lecture_recordings (lecture_title, subject, faculty_id, class_id, status)
        VALUES (:title, :subject, :faculty_id, :class_id, 'recording')
        RETURNING id
    """)
    result = db.session.execute(query, {
        'title': lecture_title,
        'subject': subject,
        'faculty_id': faculty_id,
        'class_id': class_id
    })
    lecture_id = result.fetchone()[0]
    db.session.commit()
    
    # Start recording
    notes_generator.start_recording()
    
    session_id = f"lecture_{lecture_id}_{datetime.now().timestamp()}"
    active_recordings[session_id] = {
        'lecture_id': lecture_id,
        'start_time': datetime.now(),
        'faculty_id': faculty_id
    }
    
    return jsonify({
        'success': True,
        'session_id': session_id,
        'lecture_id': lecture_id
    })

@lecture_notes_bp.route('/api/lecture-notes/stop-recording', methods=['POST'])
def stop_recording():
    """Stop recording and process lecture"""
    data = request.json
    session_id = data.get('session_id')
    
    if session_id not in active_recordings:
        return jsonify({'error': 'Invalid session'}), 400
    
    session = active_recordings[session_id]
    lecture_id = session['lecture_id']
    
    # Stop recording
    audio_file = f"uploads/lectures/lecture_{lecture_id}.wav"
    os.makedirs(os.path.dirname(audio_file), exist_ok=True)
    notes_generator.stop_recording(audio_file)
    
    # Update status to processing
    query = text("""
        UPDATE lecture_recordings
        SET status = 'processing', audio_file_path = :audio_file
        WHERE id = :lecture_id
    """)
    db.session.execute(query, {'audio_file': audio_file, 'lecture_id': lecture_id})
    db.session.commit()
    
    # Process in background (simplified - should use Celery)
    try:
        # Get lecture details
        query = text("SELECT lecture_title, subject, faculty_id FROM lecture_recordings WHERE id = :id")
        result = db.session.execute(query, {'id': lecture_id}).fetchone()
        
        # Generate notes
        notes = notes_generator.generate_lecture_notes(
            audio_file,
            result[0],  # title
            result[1],  # subject
            'Faculty'   # faculty name
        )
        
        if notes:
            # Save transcript
            query = text("""
                INSERT INTO lecture_transcripts (lecture_id, transcript_text, word_count)
                VALUES (:lecture_id, :transcript, :word_count)
            """)
            db.session.execute(query, {
                'lecture_id': lecture_id,
                'transcript': notes['transcript'],
                'word_count': notes['word_count']
            })
            
            # Save summary
            query = text("""
                INSERT INTO lecture_summaries (lecture_id, summary_text, key_points)
                VALUES (:lecture_id, :summary, :key_points)
            """)
            db.session.execute(query, {
                'lecture_id': lecture_id,
                'summary': notes['summary'],
                'key_points': json.dumps(notes['key_points'])
            })
            
            # Update lecture status
            query = text("""
                UPDATE lecture_recordings
                SET status = 'completed', duration = :duration
                WHERE id = :lecture_id
            """)
            db.session.execute(query, {
                'duration': notes['duration'],
                'lecture_id': lecture_id
            })
            db.session.commit()
        
    except Exception as e:
        query = text("UPDATE lecture_recordings SET status = 'failed' WHERE id = :id")
        db.session.execute(query, {'id': lecture_id})
        db.session.commit()
        return jsonify({'error': str(e)}), 500
    
    # Clean up
    del active_recordings[session_id]
    
    return jsonify({
        'success': True,
        'lecture_id': lecture_id,
        'status': 'completed'
    })

@lecture_notes_bp.route('/api/lecture-notes/get-lecture-notes/<int:lecture_id>', methods=['GET'])
def get_lecture_notes(lecture_id):
    """Get lecture notes by ID"""
    query = text("SELECT * FROM lecture_notes_view WHERE id = :id")
    result = db.session.execute(query, {'id': lecture_id}).fetchone()
    
    if not result:
        return jsonify({'error': 'Lecture not found'}), 404
    
    key_points = json.loads(result[9]) if result[9] else []
    
    return jsonify({
        'id': result[0],
        'title': result[1],
        'subject': result[2],
        'faculty': result[3],
        'date': result[4].isoformat(),
        'duration': result[5],
        'status': result[6],
        'transcript': result[7],
        'word_count': result[8],
        'summary': result[9],
        'key_points': key_points
    })

@lecture_notes_bp.route('/api/lecture-notes/list', methods=['GET'])
def list_lecture_notes():
    """List all available lecture notes"""
    student_id = request.args.get('student_id')
    subject = request.args.get('subject')
    limit = request.args.get('limit', 20)
    
    query = text("""
        SELECT id, lecture_title, subject, faculty_name, recording_date, duration, status
        FROM lecture_notes_view
        WHERE status = 'completed'
        AND (:subject IS NULL OR subject = :subject)
        ORDER BY recording_date DESC
        LIMIT :limit
    """)
    
    results = db.session.execute(query, {
        'subject': subject,
        'limit': limit
    }).fetchall()
    
    lectures = []
    for row in results:
        lectures.append({
            'id': row[0],
            'title': row[1],
            'subject': row[2],
            'faculty': row[3],
            'date': row[4].isoformat(),
            'duration': row[5],
            'status': row[6]
        })
    
    return jsonify({'lectures': lectures})

@lecture_notes_bp.route('/api/lecture-notes/download-pdf/<int:lecture_id>', methods=['GET'])
def download_pdf(lecture_id):
    """Download lecture notes as PDF"""
    student_id = request.args.get('student_id')
    
    # Get lecture notes
    query = text("SELECT * FROM lecture_notes_view WHERE id = :id")
    result = db.session.execute(query, {'id': lecture_id}).fetchone()
    
    if not result:
        return jsonify({'error': 'Lecture not found'}), 404
    
    # Track access
    if student_id:
        query = text("""
            INSERT INTO student_lecture_access (student_id, lecture_id, downloaded, download_count)
            VALUES (:student_id, :lecture_id, TRUE, 1)
            ON CONFLICT (student_id, lecture_id)
            DO UPDATE SET downloaded = TRUE, download_count = student_lecture_access.download_count + 1
        """)
        db.session.execute(query, {'student_id': student_id, 'lecture_id': lecture_id})
        db.session.commit()
    
    # Prepare notes data
    key_points = json.loads(result[9]) if result[9] else []
    notes_data = {
        'title': result[1],
        'subject': result[2],
        'faculty': result[3],
        'date': result[4].strftime('%Y-%m-%d %H:%M'),
        'duration': result[5],
        'transcript': result[7],
        'word_count': result[8],
        'summary': result[8],
        'key_points': key_points
    }
    
    # Generate PDF
    pdf_bytes = pdf_generator.generate_pdf_bytes(notes_data)
    
    # Send file
    from io import BytesIO
    return send_file(
        BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"{result[1].replace(' ', '_')}.pdf"
    )

@lecture_notes_bp.route('/api/lecture-notes/search', methods=['GET'])
def search_lecture_notes():
    """Search lecture notes"""
    query_text = request.args.get('q', '')
    subject = request.args.get('subject')
    
    query = text("""
        SELECT id, lecture_title, subject, faculty_name, recording_date, duration
        FROM lecture_notes_view
        WHERE status = 'completed'
        AND (lecture_title ILIKE :query OR subject ILIKE :query OR summary_text ILIKE :query)
        AND (:subject IS NULL OR subject = :subject)
        ORDER BY recording_date DESC
        LIMIT 20
    """)
    
    results = db.session.execute(query, {
        'query': f'%{query_text}%',
        'subject': subject
    }).fetchall()
    
    lectures = []
    for row in results:
        lectures.append({
            'id': row[0],
            'title': row[1],
            'subject': row[2],
            'faculty': row[3],
            'date': row[4].isoformat(),
            'duration': row[5]
        })
    
    return jsonify({'results': lectures})
