from flask import Blueprint, request, jsonify, session
from datetime import datetime
from backend.models import db, Quiz, Question, QuizAttempt
from sqlalchemy import func

quiz_bp = Blueprint('quiz', __name__)

# ── Faculty: Create Quiz ──────────────────────────────────────────────────────

@quiz_bp.route('/create-quiz', methods=['POST'])
def create_quiz():
    if session.get('role') != 'faculty':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json()
    required = ['subject', 'chapter', 'title', 'time_limit', 'deadline', 'questions']
    if not all(k in data for k in required):
        return jsonify({'success': False, 'message': 'Missing fields'}), 400

    quiz = Quiz(
        subject=data['subject'],
        chapter=data['chapter'],
        title=data['title'],
        time_limit=data['time_limit'],
        deadline=datetime.fromisoformat(data['deadline']),
        created_by=session['user_id']
    )
    db.session.add(quiz)
    db.session.flush()  # get quiz.id before commit

    for q in data['questions']:
        question = Question(
            quiz_id=quiz.id,
            question=q['question'],
            option1=q['option1'],
            option2=q['option2'],
            option3=q['option3'],
            option4=q['option4'],
            correct_answer=q['correct_answer']
        )
        db.session.add(question)

    db.session.commit()
    return jsonify({'success': True, 'quiz_id': quiz.id})

@quiz_bp.route('/get-quizzes', methods=['GET'])
def get_quizzes():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    subject = request.args.get('subject')
    query = Quiz.query
    if subject:
        query = query.filter_by(subject=subject)

    quizzes = query.order_by(Quiz.created_at.desc()).all()
    return jsonify([{
        'id': q.id,
        'title': q.title,
        'subject': q.subject,
        'chapter': q.chapter,
        'time_limit': q.time_limit,
        'deadline': q.deadline.isoformat(),
        'question_count': len(q.questions)
    } for q in quizzes])

# ── Student: Attempt Quiz ─────────────────────────────────────────────────────

@quiz_bp.route('/attempt-quiz/<int:quiz_id>', methods=['GET'])
def attempt_quiz(quiz_id):
    if session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    quiz = Quiz.query.get_or_404(quiz_id)
    if datetime.utcnow() > quiz.deadline:
        return jsonify({'success': False, 'message': 'Quiz deadline has passed'}), 400

    # Check if already attempted
    existing = QuizAttempt.query.filter_by(
        student_id=session['user_id'], quiz_id=quiz_id
    ).first()
    if existing:
        return jsonify({'success': False, 'message': 'Already attempted'}), 400

    questions = [{
        'id': q.id,
        'question': q.question,
        'options': [q.option1, q.option2, q.option3, q.option4]
    } for q in quiz.questions]

    return jsonify({
        'quiz_id': quiz.id,
        'title': quiz.title,
        'time_limit': quiz.time_limit,
        'questions': questions
    })

@quiz_bp.route('/submit-quiz', methods=['POST'])
def submit_quiz():
    if session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    data = request.get_json()
    quiz_id = data.get('quiz_id')
    answers = data.get('answers', {})  # {question_id: selected_option}

    quiz = Quiz.query.get_or_404(quiz_id)
    if datetime.utcnow() > quiz.deadline:
        return jsonify({'success': False, 'message': 'Deadline passed'}), 400

    existing = QuizAttempt.query.filter_by(
        student_id=session['user_id'], quiz_id=quiz_id
    ).first()
    if existing:
        return jsonify({'success': False, 'message': 'Already attempted'}), 400

    score = sum(
        1 for q in quiz.questions
        if str(answers.get(str(q.id))) == str(q.correct_answer)
    )
    total = len(quiz.questions)

    attempt = QuizAttempt(
        student_id=session['user_id'],
        quiz_id=quiz_id,
        score=score,
        total=total
    )
    db.session.add(attempt)
    db.session.commit()

    return jsonify({'success': True, 'score': score, 'total': total, 'percentage': round(score / total * 100, 1)})

# ── Results & Analytics ───────────────────────────────────────────────────────

@quiz_bp.route('/quiz-results/<int:quiz_id>', methods=['GET'])
def quiz_results(quiz_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    quiz = Quiz.query.get_or_404(quiz_id)
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id).all()

    if not attempts:
        return jsonify({'quiz_title': quiz.title, 'attempts': [], 'stats': {}})

    scores = [a.score for a in attempts]
    stats = {
        'average': round(sum(scores) / len(scores), 2),
        'highest': max(scores),
        'lowest': min(scores),
        'total_attempts': len(scores),
        'total_questions': quiz.questions[0].quiz.questions.__len__() if quiz.questions else 0
    }
    stats['total_questions'] = len(quiz.questions)

    return jsonify({
        'quiz_title': quiz.title,
        'stats': stats,
        'attempts': [{
            'student_id': a.student_id,
            'score': a.score,
            'total': a.total,
            'percentage': round(a.score / a.total * 100, 1) if a.total else 0,
            'timestamp': a.timestamp.strftime('%Y-%m-%d %H:%M')
        } for a in attempts]
    })

@quiz_bp.route('/my-results', methods=['GET'])
def my_results():
    if session.get('role') != 'student':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    attempts = QuizAttempt.query.filter_by(student_id=session['user_id']).all()
    return jsonify([{
        'quiz_id': a.quiz_id,
        'quiz_title': a.quiz.title,
        'subject': a.quiz.subject,
        'score': a.score,
        'total': a.total,
        'percentage': round(a.score / a.total * 100, 1) if a.total else 0,
        'timestamp': a.timestamp.strftime('%Y-%m-%d %H:%M')
    } for a in attempts])

# ── AI: Weak Student Analysis ─────────────────────────────────────────────────

@quiz_bp.route('/ai-analysis/<int:quiz_id>', methods=['GET'])
def ai_analysis(quiz_id):
    if session.get('role') != 'faculty':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    quiz = Quiz.query.get_or_404(quiz_id)
    attempts = QuizAttempt.query.filter_by(quiz_id=quiz_id).all()

    if not attempts:
        return jsonify({'message': 'No attempts yet'})

    threshold = 0.5  # below 50% = weak
    weak_students = [
        {'student_id': a.student_id, 'score': a.score, 'total': a.total,
         'percentage': round(a.score / a.total * 100, 1)}
        for a in attempts if a.total and (a.score / a.total) < threshold
    ]

    suggestions = []
    if weak_students:
        suggestions = [
            f"Revisit {quiz.chapter} concepts",
            f"Assign additional practice problems for {quiz.subject}",
            "Consider a remedial session for struggling students"
        ]

    return jsonify({
        'weak_students': weak_students,
        'weak_count': len(weak_students),
        'total_students': len(attempts),
        'suggestions': suggestions
    })
