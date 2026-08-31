@echo off
echo ========================================
echo  Installing Attention Detection Module
echo ========================================
echo.

cd /d "c:\Users\MANOJ P\Downloads\final project"

echo Step 1: Installing scipy...
pip install scipy==1.11.4

echo.
echo Step 2: Installing dlib (this may take a while)...
pip install dlib==19.24.2

echo.
echo Step 3: Downloading dlib face model...
if not exist "ml_models" mkdir ml_models
cd ml_models

echo Downloading shape_predictor_68_face_landmarks.dat.bz2...
curl -L -O http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2

echo Extracting...
tar -xf shape_predictor_68_face_landmarks.dat.bz2
del shape_predictor_68_face_landmarks.dat.bz2

cd ..

echo.
echo ========================================
echo  Installation Complete!
echo ========================================
echo.
echo Files installed:
echo - scipy
echo - dlib
echo - shape_predictor_68_face_landmarks.dat
echo.
pause
