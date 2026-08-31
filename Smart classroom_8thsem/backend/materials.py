import os
import boto3
from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
from datetime import datetime
from backend.models import db, Material

materials_bp = Blueprint('materials', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'ppt', 'pptx', 'png', 'jpg', 'jpeg'}
S3_BUCKET = os.getenv('S3_BUCKET', 'smart-classroom-materials')
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')

s3_client = boto3.client(
    's3',
    region_name=AWS_REGION,
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def upload_to_s3(file, subject, chapter, filename):
    key = f"materials/{subject}/{chapter}/{filename}"
    s3_client.upload_fileobj(
        file,
        S3_BUCKET,
        key,
        ExtraArgs={'ContentType': file.content_type}
    )
    return f"https://{S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}"

@materials_bp.route('/upload-material', methods=['POST'])
def upload_material():
    if session.get('role') != 'faculty':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400

    file = request.files['file']
    subject = request.form.get('subject', '').strip()
    chapter = request.form.get('chapter', '').strip()

    if not file or not allowed_file(file.filename):
        return jsonify({'success': False, 'message': 'Invalid file type'}), 400
    if not subject or not chapter:
        return jsonify({'success': False, 'message': 'Subject and chapter required'}), 400

    filename = secure_filename(f"{datetime.utcnow().timestamp()}_{file.filename}")
    try:
        file_url = upload_to_s3(file, subject, chapter, filename)
    except Exception as e:
        return jsonify({'success': False, 'message': f'S3 upload failed: {str(e)}'}), 500

    material = Material(
        subject=subject,
        chapter=chapter,
        filename=file.filename,
        file_url=file_url,
        uploaded_by=session['user_id']
    )
    db.session.add(material)
    db.session.commit()
    return jsonify({'success': True, 'material_id': material.id, 'file_url': file_url})

@materials_bp.route('/get-materials', methods=['GET'])
def get_materials():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    subject = request.args.get('subject')
    chapter = request.args.get('chapter')
    keyword = request.args.get('keyword', '').strip()

    query = Material.query
    if subject:
        query = query.filter_by(subject=subject)
    if chapter:
        query = query.filter_by(chapter=chapter)
    if keyword:
        query = query.filter(
            db.or_(
                Material.filename.ilike(f'%{keyword}%'),
                Material.subject.ilike(f'%{keyword}%'),
                Material.chapter.ilike(f'%{keyword}%')
            )
        )

    materials = query.order_by(Material.timestamp.desc()).all()
    return jsonify([{
        'id': m.id,
        'subject': m.subject,
        'chapter': m.chapter,
        'filename': m.filename,
        'file_url': m.file_url,
        'timestamp': m.timestamp.strftime('%Y-%m-%d %H:%M')
    } for m in materials])

@materials_bp.route('/delete-material/<int:material_id>', methods=['DELETE'])
def delete_material(material_id):
    if session.get('role') != 'faculty':
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403

    material = Material.query.get_or_404(material_id)
    # Extract S3 key from URL and delete
    key = '/'.join(material.file_url.split('.amazonaws.com/')[1:])
    try:
        s3_client.delete_object(Bucket=S3_BUCKET, Key=key)
    except Exception:
        pass
    db.session.delete(material)
    db.session.commit()
    return jsonify({'success': True})
