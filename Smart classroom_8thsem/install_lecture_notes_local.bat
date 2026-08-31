@echo off
echo ========================================
echo  Installing Lecture Notes (Local Mode)
echo ========================================
echo.

cd /d "c:\Users\MANOJ P\Downloads\final project"

echo Installing dependencies...
pip install PyAudio==0.2.13
pip install reportlab==4.0.4
pip install transformers==4.33.2
pip install SpeechRecognition==3.10.0

echo.
echo Creating directories...
if not exist "uploads\lectures" mkdir uploads\lectures

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo LOCAL MODE - No AWS required!
echo Uses Google Speech Recognition (free)
echo.
echo Run: python app.py
echo.
pause
