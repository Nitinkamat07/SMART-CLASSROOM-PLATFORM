@echo off
echo Starting Smart Classroom Management System...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found. Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install flask flask-sqlalchemy flask-socketio flask-cors psycopg2-binary opencv-python tensorflow scikit-learn pandas numpy pillow python-dotenv

REM Create directories
if not exist "uploads" mkdir uploads
if not exist "face_data" mkdir face_data
if not exist "ml_models" mkdir ml_models
if not exist "logs" mkdir logs

REM Set environment variables
set DATABASE_URL=sqlite:///classroom.db
set FLASK_ENV=development
set SECRET_KEY=dev-secret-key

echo Starting application...
python app.py

pause