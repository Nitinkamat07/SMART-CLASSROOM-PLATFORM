@echo off
echo ========================================
echo  Installing Lecture Notes Generator
echo ========================================
echo.

cd /d "c:\Users\MANOJ P\Downloads\final project"

echo Step 1: Installing PyAudio...
pip install PyAudio==0.2.13

echo.
echo Step 2: Installing ReportLab...
pip install reportlab==4.0.4

echo.
echo Step 3: Installing Transformers...
pip install transformers==4.33.2

echo.
echo Step 4: Installing AWS SDK...
pip install boto3==1.28.57

echo.
echo Step 5: Creating directories...
if not exist "uploads\lectures" mkdir uploads\lectures

echo.
echo Step 6: Setting up database...
psql -U postgres -d classroom_management_db -f database\lecture_notes_schema.sql

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo Installed:
echo - PyAudio (audio recording)
echo - ReportLab (PDF generation)
echo - Transformers (AI summarization)
echo - Boto3 (AWS Transcribe)
echo.
echo Next Steps:
echo 1. Set AWS credentials: aws configure
echo 2. Set environment variables:
echo    - AWS_REGION=us-east-1
echo    - S3_BUCKET=classroom-lectures
echo 3. Run: python app.py
echo.
pause
