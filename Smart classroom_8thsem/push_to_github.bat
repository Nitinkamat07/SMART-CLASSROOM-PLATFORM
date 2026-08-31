@echo off
echo ========================================
echo  Smart Classroom - GitHub Push Script
echo ========================================
echo.

REM Check if Git is installed
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git is not installed!
    echo Please install Git from: https://git-scm.com/download/win
    pause
    exit /b 1
)

echo Step 1: Initializing Git repository...
git init

echo.
echo Step 2: Adding all files...
git add .

echo.
echo Step 3: Creating initial commit...
git commit -m "Initial commit: AI-Based Smart Classroom Management System"

echo.
echo Step 4: Setting up GitHub remote...
echo.
echo Please enter your GitHub repository URL (e.g., https://github.com/username/repo.git):
set /p REPO_URL="> "

if "%REPO_URL%"=="" (
    echo ERROR: Repository URL cannot be empty!
    pause
    exit /b 1
)

git remote add origin %REPO_URL%

echo.
echo Step 5: Pushing to GitHub...
git branch -M main
git push -u origin main

echo.
echo ========================================
echo  Push Complete!
echo ========================================
echo.
echo Your project is now on GitHub at:
echo %REPO_URL%
echo.
pause
