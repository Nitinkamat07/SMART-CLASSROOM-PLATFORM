# Lecture Notes Generator - Setup Guide

## Quick Setup

### 1. Install Dependencies
```bash
install_lecture_notes.bat
```

### 2. Configure AWS
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Default region: us-east-1
```

### 3. Create S3 Bucket
```bash
aws s3 mb s3://classroom-lectures
```

### 4. Set Environment Variables
```bash
set AWS_REGION=us-east-1
set S3_BUCKET=classroom-lectures
```

### 5. Run Database Migration
```bash
psql -U postgres -d classroom_management_db -f database\lecture_notes_schema.sql
```

### 6. Start Application
```bash
python app.py
```

## Usage

### Faculty - Record Lecture
1. Navigate to: http://localhost:5000/faculty/record-lecture
2. Enter lecture title
3. Select schedule
4. Click "Start Recording"
5. Click "Stop Recording" when done
6. System will automatically transcribe and generate PDF

### Students - View Notes
1. Navigate to: http://localhost:5000/student/lecture-notes
2. Browse available lecture notes
3. Download PDF when status is "Completed"

## API Endpoints

- `POST /api/lecture/start-recording` - Start recording
- `POST /api/lecture/stop-recording` - Stop and process
- `GET /api/lecture/get-lecture-notes` - Get all notes
- `GET /api/lecture/download/<id>` - Download PDF

## Troubleshooting

### PyAudio Installation Error
```bash
pip install pipwin
pipwin install pyaudio
```

### AWS Transcribe Permission Error
Add this IAM policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["transcribe:*", "s3:*"],
    "Resource": "*"
  }]
}
```

### Database Connection Error
Update DATABASE_URL in app.py:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@localhost/classroom_db'
```
