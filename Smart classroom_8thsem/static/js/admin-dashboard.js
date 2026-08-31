
// Mock Socket.IO for app_simple.py
if (typeof window.io === 'undefined') {
    window.io = function() {
        return {
            on: function(event, callback) {},
            emit: function(event, data) {}
        };
    };
}

// Admin Dashboard JavaScript

// Global variables
let currentSection = 'overview';
let studentsData = [];
let classroomsData = [];
let utilizationChart = null;

// Initialize admin dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeAdminDashboard();
    setupEventListeners();
    loadDashboardData();
});

function initializeAdminDashboard() {
    console.log('Admin Dashboard initialized');
    
    // Setup real-time updates
    const socket = io();
    socket.on('connect', function() {
        socket.emit('join_room', {room: 'admin'});
    });
    
    socket.on('attendance_update', function(data) {
        updateAttendanceStats();
        addRecentActivity(`Student ${data.student_id} marked attendance`, 'attendance');
    });
    
    socket.on('classroom_update', function(data) {
        updateClassroomStatus(data);
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
    
    // Add student form
    const addStudentForm = document.getElementById('add-student-form');
    if (addStudentForm) {
        addStudentForm.addEventListener('submit', handleAddStudent);
    }
    
    // Filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            // Apply filter logic here
        });
    });
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
        // Load overview stats
        await Promise.all([
            loadOverviewStats(),
            loadClassroomsData(),
            loadStudentsData(),
            loadRecentActivity()
        ]);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showNotification('Failed to load dashboard data', 'error');
    }
}

async function loadOverviewStats() {
    try {
        // Load basic stats
        const [classroomsRes, studentsRes] = await Promise.all([
            fetch('/api/classrooms'),
            fetch('/api/students')
        ]);
        
        const classrooms = await classroomsRes.json();
        const students = await studentsRes.json();
        
        // Update stats display
        document.getElementById('total-classrooms').textContent = classrooms.length;
        document.getElementById('total-students').textContent = students.length;
        
        // Calculate utilization rate
        const occupiedRooms = classrooms.filter(c => c.status === 'occupied').length;
        const utilizationRate = classrooms.length > 0 ? (occupiedRooms / classrooms.length * 100).toFixed(1) : 0;
        document.getElementById('utilization-rate').textContent = utilizationRate + '%';
        
        // Load attendance stats
        await loadAttendanceStats();
        
    } catch (error) {
        console.error('Error loading overview stats:', error);
    }
}

async function loadAttendanceStats() {
    try {
        const response = await fetch('/api/attendance/stats');
        const stats = await response.json();
        
        document.getElementById('today-attendance').textContent = stats.today_percentage + '%';
    } catch (error) {
        console.error('Error loading attendance stats:', error);
        document.getElementById('today-attendance').textContent = '0%';
    }
}

async function loadClassroomsData() {
    try {
        const response = await fetch('/api/classrooms');
        classroomsData = await response.json();
        
        displayLiveClassrooms(classroomsData);
    } catch (error) {
        console.error('Error loading classrooms data:', error);
    }
}

function displayLiveClassrooms(classrooms) {
    const container = document.getElementById('live-classrooms');
    if (!container) return;
    
    container.innerHTML = '';
    
    classrooms.slice(0, 6).forEach(classroom => {
        const classroomDiv = document.createElement('div');
        classroomDiv.className = 'classroom-status-item';
        classroomDiv.innerHTML = `
            <div class="classroom-info">
                <h4>${classroom.name}</h4>
                <span class="status ${classroom.status}">${classroom.status}</span>
            </div>
            <div class="classroom-details">
                <small>Capacity: ${classroom.capacity}</small>
                ${classroom.current_class ? `<small>Current: ${classroom.current_class}</small>` : ''}
            </div>
        `;
        container.appendChild(classroomDiv);
    });
}

async function loadStudentsData() {
    try {
        const response = await fetch('/api/students');
        studentsData = await response.json();
        
        if (currentSection === 'students') {
            displayStudentsTable(studentsData);
        }
    } catch (error) {
        console.error('Error loading students data:', error);
    }
}

function displayStudentsTable(students) {
    const tbody = document.querySelector('#students-table tbody');
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    students.forEach(student => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${student.student_id}</td>
            <td>${student.name}</td>
            <td>${student.email}</td>
            <td>${student.department}</td>
            <td>
                <span class="badge ${student.face_encoding ? 'success' : 'warning'}">
                    ${student.face_encoding ? 'Yes' : 'No'}
                </span>
            </td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editStudent(${student.id})">Edit</button>
                <button class="btn btn-sm btn-danger" onclick="deleteStudent(${student.id})">Delete</button>
                ${!student.face_encoding ? `<button class="btn btn-sm btn-success" onclick="uploadFace(${student.id})">Upload Face</button>` : ''}
            </td>
        `;
        tbody.appendChild(row);
    });
}

async function loadRecentActivity() {
    const container = document.getElementById('recent-activity');
    if (!container) return;
    
    // Mock recent activity data
    const activities = [
        { type: 'attendance', message: 'Student John Doe marked attendance', time: '2 minutes ago' },
        { type: 'classroom', message: 'Room A101 status changed to occupied', time: '5 minutes ago' },
        { type: 'system', message: 'Face recognition model updated', time: '10 minutes ago' },
        { type: 'attendance', message: 'Student Jane Smith marked attendance', time: '15 minutes ago' }
    ];
    
    container.innerHTML = '';
    
    activities.forEach(activity => {
        const activityDiv = document.createElement('div');
        activityDiv.className = 'activity-item';
        activityDiv.innerHTML = `
            <div class="activity-icon ${activity.type}">
                <i class="fas fa-${getActivityIcon(activity.type)}"></i>
            </div>
            <div class="activity-content">
                <p>${activity.message}</p>
                <small>${activity.time}</small>
            </div>
        `;
        container.appendChild(activityDiv);
    });
}

function getActivityIcon(type) {
    const icons = {
        attendance: 'check-circle',
        classroom: 'door-open',
        system: 'cog',
        student: 'user'
    };
    return icons[type] || 'info-circle';
}

function addRecentActivity(message, type) {
    const container = document.getElementById('recent-activity');
    if (!container) return;
    
    const activityDiv = document.createElement('div');
    activityDiv.className = 'activity-item new';
    activityDiv.innerHTML = `
        <div class="activity-icon ${type}">
            <i class="fas fa-${getActivityIcon(type)}"></i>
        </div>
        <div class="activity-content">
            <p>${message}</p>
            <small>Just now</small>
        </div>
    `;
    
    container.insertBefore(activityDiv, container.firstChild);
    
    // Remove 'new' class after animation
    setTimeout(() => {
        activityDiv.classList.remove('new');
    }, 3000);
}

async function loadSectionData(sectionName) {
    switch (sectionName) {
        case 'students':
            if (studentsData.length === 0) {
                await loadStudentsData();
            }
            displayStudentsTable(studentsData);
            break;
            
        case 'ai-insights':
            await loadAIInsights();
            break;
            
        case 'analytics':
            await loadAnalytics();
            break;
    }
}

async function loadAIInsights() {
    try {
        // Load usage predictions
        const predictionsRes = await fetch('/api/predict-usage');
        const predictions = await predictionsRes.json();
        
        displayUsagePredictions(predictions);
        
        // Load optimization suggestions
        const suggestionsRes = await fetch('/api/optimization-suggestions');
        const suggestions = await suggestionsRes.json();
        
        displayOptimizationSuggestions(suggestions);
        
        // Load utilization chart
        loadUtilizationChart();
        
    } catch (error) {
        console.error('Error loading AI insights:', error);
    }
}

function displayUsagePredictions(predictions) {
    const container = document.getElementById('usage-predictions');
    if (!container) return;
    
    container.innerHTML = '';
    
    // Group predictions by classroom
    const groupedPredictions = {};
    predictions.forEach(pred => {
        if (!groupedPredictions[pred.classroom_name]) {
            groupedPredictions[pred.classroom_name] = [];
        }
        groupedPredictions[pred.classroom_name].push(pred);
    });
    
    Object.keys(groupedPredictions).slice(0, 5).forEach(classroomName => {
        const preds = groupedPredictions[classroomName].slice(0, 3);
        const predDiv = document.createElement('div');
        predDiv.className = 'prediction-item';
        predDiv.innerHTML = `
            <h4>${classroomName}</h4>
            ${preds.map(p => `
                <div class="prediction-detail">
                    <span>${new Date(p.datetime).toLocaleTimeString()}</span>
                    <span class="usage-rate ${p.status}">${(p.predicted_usage * 100).toFixed(1)}%</span>
                </div>
            `).join('')}
        `;
        container.appendChild(predDiv);
    });
}

function displayOptimizationSuggestions(suggestions) {
    const container = document.getElementById('optimization-suggestions');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (suggestions.length === 0) {
        container.innerHTML = '<p>No optimization suggestions at this time.</p>';
        return;
    }
    
    suggestions.forEach(suggestion => {
        const suggestionDiv = document.createElement('div');
        suggestionDiv.className = `suggestion-item ${suggestion.priority}`;
        suggestionDiv.innerHTML = `
            <div class="suggestion-header">
                <i class="fas fa-${getSuggestionIcon(suggestion.type)}"></i>
                <span class="priority ${suggestion.priority}">${suggestion.priority}</span>
            </div>
            <p>${suggestion.message}</p>
        `;
        container.appendChild(suggestionDiv);
    });
}

function getSuggestionIcon(type) {
    const icons = {
        underutilized: 'exclamation-triangle',
        peak_hours: 'clock',
        optimization: 'lightbulb'
    };
    return icons[type] || 'info-circle';
}

function loadUtilizationChart() {
    const ctx = document.getElementById('utilizationChart');
    if (!ctx) return;
    
    // Destroy existing chart
    if (utilizationChart) {
        utilizationChart.destroy();
    }
    
    // Mock data for demonstration
    const data = {
        labels: ['8:00', '9:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00'],
        datasets: [{
            label: 'Classroom Utilization %',
            data: [45, 78, 85, 92, 65, 40, 88, 95, 82, 55],
            borderColor: '#667eea',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            tension: 0.4
        }]
    };
    
    utilizationChart = new Chart(ctx, {
        type: 'line',
        data: data,
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Hourly Classroom Utilization'
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: {
                        callback: function(value) {
                            return value + '%';
                        }
                    }
                }
            }
        }
    });
}

// Modal functions
function showAddStudentModal() {
    document.getElementById('add-student-modal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

async function handleAddStudent(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const studentData = {
        student_id: formData.get('student_id'),
        name: formData.get('name'),
        email: formData.get('email'),
        department: formData.get('department')
    };
    
    try {
        const response = await fetch('/api/admin/students', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(studentData)
        });
        
        if (response.ok) {
            showNotification('Student added successfully', 'success');
            closeModal('add-student-modal');
            e.target.reset();
            
            // Handle face image upload if provided
            const faceImage = formData.get('face_image');
            if (faceImage && faceImage.size > 0) {
                await uploadStudentFace(studentData.student_id, faceImage);
            }
            
            // Reload students data
            await loadStudentsData();
        } else {
            showNotification('Failed to add student', 'error');
        }
    } catch (error) {
        console.error('Error adding student:', error);
        showNotification('Error adding student', 'error');
    }
}

async function uploadStudentFace(studentId, faceImage) {
    const formData = new FormData();
    formData.append('file', faceImage);
    formData.append('student_id', studentId);
    
    try {
        const response = await fetch('/api/admin/upload-face', {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            showNotification('Face image uploaded successfully', 'success');
        } else {
            showNotification('Failed to upload face image', 'error');
        }
    } catch (error) {
        console.error('Error uploading face:', error);
        showNotification('Error uploading face image', 'error');
    }
}

// Utility functions
function refreshData() {
    loadDashboardData();
    showNotification('Data refreshed', 'success');
}

function editStudent(studentId) {
    // Implement edit student functionality
    console.log('Edit student:', studentId);
}

function deleteStudent(studentId) {
    if (confirm('Are you sure you want to delete this student?')) {
        // Implement delete student functionality
        console.log('Delete student:', studentId);
    }
}

function uploadFace(studentId) {
    // Implement face upload functionality
    console.log('Upload face for student:', studentId);
}

function showNotification(message, type = 'info') {
    // Use the notification system from main.js
    if (window.SmartClassroom && window.SmartClassroom.showNotification) {
        window.SmartClassroom.showNotification(message, type);
    } else {
        alert(message);
    }
}

// Close modals when clicking outside
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
};