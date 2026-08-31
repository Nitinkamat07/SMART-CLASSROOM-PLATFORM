
// Mock Socket.IO for app_simple.py
if (typeof window.io === 'undefined') {
    window.io = function() {
        return {
            on: function(event, callback) {},
            emit: function(event, data) {}
        };
    };
}

// Student Dashboard JavaScript

// Global variables
let currentSection = 'overview';
let video = null;
let canvas = null;
let stream = null;
let attendanceData = [];
let scheduleData = [];

// Initialize student dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeStudentDashboard();
    setupEventListeners();
    loadDashboardData();
});

function initializeStudentDashboard() {
    console.log('Student Dashboard initialized');
    
    // Get video and canvas elements
    video = document.getElementById('video');
    canvas = document.getElementById('canvas');
    
    // Setup real-time updates
    const socket = io();
    socket.on('connect', function() {
        socket.emit('join_room', {room: 'student'});
    });
    
    socket.on('attendance_update', function(data) {
        if (data.student_id === getCurrentStudentId()) {
            updateAttendanceStats();
            showNotification('Attendance marked successfully!', 'success');
        }
    });
}

function setupEventListeners() {
    // Sidebar navigation
    document.querySelectorAll('.menu-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('href').substring(1);
            showSection(section);
        });
    });
    
    // Camera controls
    const startCameraBtn = document.getElementById('start-camera');
    const capturePhotoBtn = document.getElementById('capture-photo');
    const stopCameraBtn = document.getElementById('stop-camera');
    
    if (startCameraBtn) {
        startCameraBtn.addEventListener('click', startCamera);
    }
    
    if (capturePhotoBtn) {
        capturePhotoBtn.addEventListener('click', captureAndMarkAttendance);
    }
    
    if (stopCameraBtn) {
        stopCameraBtn.addEventListener('click', stopCamera);
    }
    
    // Schedule filters
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            
            const day = this.getAttribute('data-day');
            filterSchedule(day);
        });
    });
    
    // Month filter for attendance records
    const monthFilter = document.getElementById('month-filter');
    if (monthFilter) {
        monthFilter.addEventListener('change', function() {
            filterAttendanceRecords(this.value);
        });
    }
}

function showSection(sectionName) {
    // Hide all sections
    document.querySelectorAll('.dashboard-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    const targetSection = document.getElementById(sectionName);
    if (targetSection) {
        targetSection.classList.add('active');
        currentSection = sectionName;
        
        // Update active menu item
        document.querySelectorAll('.menu-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[href="#${sectionName}"]`).classList.add('active');
        
        // Load section-specific data
        loadSectionData(sectionName);
    }
}

async function loadDashboardData() {
    try {
        await Promise.all([
            loadAttendanceStats(),
            loadTodaySchedule(),
            loadScheduleData(),
            loadAttendanceRecords()
        ]);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showNotification('Failed to load dashboard data', 'error');
    }
}

async function loadAttendanceStats() {
    try {
        const studentId = getCurrentStudentId();
        const response = await fetch(`/api/student/${studentId}/attendance-stats`);
        const stats = await response.json();
        
        // Update stats display
        document.getElementById('attendance-percentage').textContent = stats.percentage + '%';
        document.getElementById('classes-attended').textContent = stats.attended;
        
    } catch (error) {
        console.error('Error loading attendance stats:', error);
        // Set default values
        document.getElementById('attendance-percentage').textContent = '0%';
        document.getElementById('classes-attended').textContent = '0';
    }
}

async function loadTodaySchedule() {
    try {
        const studentId = getCurrentStudentId();
        const response = await fetch(`/api/student/${studentId}/today-schedule`);
        const schedule = await response.json();
        
        // Update today's classes count
        document.getElementById('today-classes').textContent = schedule.length;
        
        // Find next class
        const now = new Date();
        const currentTime = now.getHours() * 60 + now.getMinutes();
        
        let nextClass = null;
        for (const classItem of schedule) {
            const classTime = parseTime(classItem.start_time);
            if (classTime > currentTime) {
                nextClass = classItem;
                break;
            }
        }
        
        if (nextClass) {
            document.getElementById('next-class').textContent = nextClass.start_time;
        } else {
            document.getElementById('next-class').textContent = 'No more classes';
        }
        
        // Display today's schedule
        displayTodaySchedule(schedule);
        
    } catch (error) {
        console.error('Error loading today schedule:', error);
        document.getElementById('today-classes').textContent = '0';
        document.getElementById('next-class').textContent = '--:--';
    }
}

function displayTodaySchedule(schedule) {
    const container = document.getElementById('today-schedule');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (schedule.length === 0) {
        container.innerHTML = '<p>No classes scheduled for today.</p>';
        return;
    }
    
    schedule.forEach(classItem => {
        const scheduleDiv = document.createElement('div');
        scheduleDiv.className = 'schedule-item';
        scheduleDiv.innerHTML = `
            <div class="schedule-time">
                <strong>${classItem.start_time} - ${classItem.end_time}</strong>
            </div>
            <div class="schedule-details">
                <h4>${classItem.subject}</h4>
                <p>Room: ${classItem.classroom_name}</p>
                <p>Faculty: ${classItem.faculty_name}</p>
            </div>
        `;
        container.appendChild(scheduleDiv);
    });
}

async function loadScheduleData() {
    try {
        const studentId = getCurrentStudentId();
        const response = await fetch(`/api/student/${studentId}/schedule`);
        scheduleData = await response.json();
        
        if (currentSection === 'schedule') {
            displaySchedule(scheduleData);
        }
    } catch (error) {
        console.error('Error loading schedule data:', error);
    }
}

function displaySchedule(schedule) {
    const container = document.getElementById('schedule-grid');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Group schedule by day
    const groupedSchedule = {};
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    
    schedule.forEach(item => {
        const dayName = days[item.day_of_week];
        if (!groupedSchedule[dayName]) {
            groupedSchedule[dayName] = [];
        }
        groupedSchedule[dayName].push(item);
    });
    
    // Display schedule for each day
    days.forEach(day => {
        if (groupedSchedule[day] && groupedSchedule[day].length > 0) {
            const dayDiv = document.createElement('div');
            dayDiv.className = 'schedule-day';
            dayDiv.innerHTML = `
                <h3>${day}</h3>
                <div class="day-classes">
                    ${groupedSchedule[day].map(item => `
                        <div class="class-item">
                            <div class="class-time">${item.start_time} - ${item.end_time}</div>
                            <div class="class-info">
                                <h4>${item.subject}</h4>
                                <p>Room: ${item.classroom_name}</p>
                                <p>Faculty: ${item.faculty_name}</p>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
            container.appendChild(dayDiv);
        }
    });
}

function filterSchedule(day) {
    if (day === 'all') {
        displaySchedule(scheduleData);
    } else {
        const filteredSchedule = scheduleData.filter(item => item.day_of_week == day);
        displaySchedule(filteredSchedule);
    }
}

async function loadAttendanceRecords() {
    try {
        const studentId = getCurrentStudentId();
        const response = await fetch(`/api/student/${studentId}/attendance-records`);
        attendanceData = await response.json();
        
        if (currentSection === 'records') {
            displayAttendanceRecords(attendanceData);
        }
    } catch (error) {
        console.error('Error loading attendance records:', error);
    }
}

function displayAttendanceRecords(records) {
    const tbody = document.querySelector('#attendance-table tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5">No attendance records found.</td></tr>';
        return;
    }
    
    records.forEach(record => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatDate(record.date)}</td>
            <td>${record.subject}</td>
            <td>${record.start_time} - ${record.end_time}</td>
            <td>
                <span class="badge ${record.status === 'present' ? 'success' : record.status === 'late' ? 'warning' : 'danger'}">
                    ${record.status}
                </span>
            </td>
            <td>${record.classroom_name}</td>
        `;
        tbody.appendChild(row);
    });
}

function filterAttendanceRecords(month) {
    if (!month) {
        displayAttendanceRecords(attendanceData);
    } else {
        const filteredRecords = attendanceData.filter(record => {
            const recordMonth = new Date(record.date).getMonth() + 1;
            return recordMonth == month;
        });
        displayAttendanceRecords(filteredRecords);
    }
}

// Camera and Face Recognition Functions
async function startCamera() {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: 400, 
                height: 300,
                facingMode: 'user'
            } 
        });
        
        video.srcObject = stream;
        
        // Update button visibility
        document.getElementById('start-camera').style.display = 'none';
        document.getElementById('capture-photo').style.display = 'inline-block';
        document.getElementById('stop-camera').style.display = 'inline-block';
        
        updateAttendanceStatus('Camera started. Position your face in the frame.', 'info');
        
    } catch (error) {
        console.error('Error starting camera:', error);
        updateAttendanceStatus('Failed to start camera. Please check permissions.', 'error');
    }
}

function stopCamera() {
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
        video.srcObject = null;
    }
    
    // Update button visibility
    document.getElementById('start-camera').style.display = 'inline-block';
    document.getElementById('capture-photo').style.display = 'none';
    document.getElementById('stop-camera').style.display = 'none';
    
    updateAttendanceStatus('Camera stopped.', 'info');
}

async function captureAndMarkAttendance() {
    if (!video || !canvas) {
        updateAttendanceStatus('Camera not available.', 'error');
        return;
    }
    
    updateAttendanceStatus('Capturing image and processing...', 'info');
    
    // Set canvas dimensions
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    
    // Convert canvas to base64 image
    const imageData = canvas.toDataURL('image/jpeg', 0.8);
    
    try {
        // Get current schedule to determine which class to mark attendance for
        const currentSchedule = await getCurrentClassSchedule();
        
        if (!currentSchedule) {
            updateAttendanceStatus('No class scheduled at this time.', 'warning');
            return;
        }
        
        // Send image for face recognition
        const response = await fetch('/api/attendance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                image: imageData,
                schedule_id: currentSchedule.id
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            updateAttendanceStatus('Attendance marked successfully!', 'success');
            stopCamera();
            
            // Refresh attendance stats
            await loadAttendanceStats();
            await loadAttendanceRecords();
        } else {
            updateAttendanceStatus(result.message || 'Face not recognized. Please try again.', 'error');
        }
        
    } catch (error) {
        console.error('Error marking attendance:', error);
        updateAttendanceStatus('Failed to mark attendance. Please try again.', 'error');
    }
}

async function getCurrentClassSchedule() {
    try {
        const studentId = getCurrentStudentId();
        const response = await fetch(`/api/student/${studentId}/current-class`);
        
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        console.error('Error getting current class:', error);
        return null;
    }
}

function updateAttendanceStatus(message, type) {
    const statusElement = document.getElementById('attendance-status');
    if (statusElement) {
        statusElement.textContent = message;
        statusElement.className = `status-message ${type}`;
    }
}

async function loadSectionData(sectionName) {
    switch (sectionName) {
        case 'schedule':
            if (scheduleData.length === 0) {
                await loadScheduleData();
            }
            displaySchedule(scheduleData);
            break;
            
        case 'records':
            if (attendanceData.length === 0) {
                await loadAttendanceRecords();
            }
            displayAttendanceRecords(attendanceData);
            break;
            
        case 'attendance':
            // Reset camera state when entering attendance section
            stopCamera();
            updateAttendanceStatus('Ready to mark attendance', 'info');
            break;
    }
}

// Utility functions
function getCurrentStudentId() {
    // This would typically come from session or authentication
    // For demo purposes, return a mock student ID
    return 1;
}

function parseTime(timeString) {
    const [hours, minutes] = timeString.split(':').map(Number);
    return hours * 60 + minutes;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function showNotification(message, type = 'info') {
    // Use the notification system from main.js
    if (window.SmartClassroom && window.SmartClassroom.showNotification) {
        window.SmartClassroom.showNotification(message, type);
    } else {
        alert(message);
    }
}

// Cleanup when page is unloaded
window.addEventListener('beforeunload', function() {
    stopCamera();
});