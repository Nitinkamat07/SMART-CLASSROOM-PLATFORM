
// Mock Socket.IO for app_simple.py
if (typeof window.io === 'undefined') {
    window.io = function() {
        return {
            on: function(event, callback) {},
            emit: function(event, data) {}
        };
    };
}

// Main JavaScript for Smart Classroom Management System

// Initialize Socket.IO connection
const socket = io();

// Global variables
let classroomData = [];
let chatbotVisible = true;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadClassroomData();
    initializeChatbot();
});

function initializeApp() {
    console.log('Smart Classroom Management System initialized');
    
    // Setup real-time updates
    socket.on('connect', function() {
        console.log('Connected to server');
        socket.emit('join_room', {room: 'main'});
    });
    
    socket.on('classroom_status', function(data) {
        updateClassroomStatus(data);
    });
    
    socket.on('attendance_update', function(data) {
        showNotification(`Attendance marked for student ${data.student_id}`, 'success');
    });
}

function setupEventListeners() {
    // Smooth scrolling for navigation links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Chatbot toggle
    const chatbotToggle = document.getElementById('chatbot-toggle');
    if (chatbotToggle) {
        chatbotToggle.addEventListener('click', toggleChatbot);
    }
    
    // Chatbot send message
    const chatbotSend = document.getElementById('chatbot-send');
    const chatbotInput = document.getElementById('chatbot-input');
    
    if (chatbotSend) {
        chatbotSend.addEventListener('click', sendChatMessage);
    }
    
    if (chatbotInput) {
        chatbotInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendChatMessage();
            }
        });
    }
}

async function loadClassroomData() {
    try {
        const response = await fetch('/api/classrooms');
        classroomData = await response.json();
        displayClassrooms(classroomData);
    } catch (error) {
        console.error('Error loading classroom data:', error);
        showNotification('Failed to load classroom data', 'error');
    }
}

function displayClassrooms(classrooms) {
    const classroomGrid = document.getElementById('classroom-grid');
    if (!classroomGrid) return;
    
    classroomGrid.innerHTML = '';
    
    classrooms.forEach(classroom => {
        const classroomCard = createClassroomCard(classroom);
        classroomGrid.appendChild(classroomCard);
    });
}

function createClassroomCard(classroom) {
    const card = document.createElement('div');
    card.className = `classroom-card ${classroom.status === 'occupied' ? 'occupied' : ''}`;
    card.innerHTML = `
        <h3>${classroom.name}</h3>
        <div class="classroom-status">
            <span class="status-indicator ${classroom.status === 'occupied' ? 'occupied' : ''}"></span>
            <span>${classroom.status === 'occupied' ? 'Occupied' : 'Available'}</span>
        </div>
        <p><strong>Capacity:</strong> ${classroom.capacity} students</p>
        ${classroom.current_class ? `<p><strong>Current Class:</strong> ${classroom.current_class}</p>` : ''}
        <div class="classroom-actions">
            <button class="btn btn-sm btn-primary" onclick="viewClassroomDetails(${classroom.id})">
                View Details
            </button>
        </div>
    `;
    return card;
}

function updateClassroomStatus(data) {
    // Update classroom status in real-time
    const classroom = classroomData.find(c => c.id === data.classroom_id);
    if (classroom) {
        classroom.status = data.status;
        classroom.current_class = data.current_class;
        displayClassrooms(classroomData);
    }
}

function viewClassroomDetails(classroomId) {
    // Redirect to detailed view or show modal
    window.location.href = `/classroom/${classroomId}`;
}

// Chatbot functionality
function initializeChatbot() {
    const chatbotWidget = document.getElementById('chatbot-widget');
    if (chatbotWidget) {
        // Position chatbot widget
        chatbotWidget.style.display = 'block';
    }
}

function toggleChatbot() {
    const chatbotBody = document.querySelector('.chatbot-body');
    const toggleIcon = document.querySelector('#chatbot-toggle i');
    
    if (chatbotVisible) {
        chatbotBody.style.display = 'none';
        toggleIcon.className = 'fas fa-plus';
        chatbotVisible = false;
    } else {
        chatbotBody.style.display = 'flex';
        toggleIcon.className = 'fas fa-minus';
        chatbotVisible = true;
    }
}

async function sendChatMessage() {
    const input = document.getElementById('chatbot-input');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';
    
    // Show typing indicator
    showTypingIndicator();
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({message: message})
        });
        
        const data = await response.json();
        
        // Remove typing indicator and add bot response
        removeTypingIndicator();
        addChatMessage(data.response, 'bot');
        
    } catch (error) {
        removeTypingIndicator();
        addChatMessage('Sorry, I encountered an error. Please try again.', 'bot');
        console.error('Chat error:', error);
    }
}

function addChatMessage(message, sender) {
    const messagesContainer = document.getElementById('chatbot-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    messageDiv.innerHTML = `<p>${message}</p>`;
    
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTypingIndicator() {
    const messagesContainer = document.getElementById('chatbot-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message typing-indicator';
    typingDiv.innerHTML = '<p>Typing...</p>';
    typingDiv.id = 'typing-indicator';
    
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Utility functions
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()">&times;</button>
        </div>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

function formatTime(timeString) {
    const time = new Date(`2000-01-01T${timeString}`);
    return time.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true
    });
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Export functions for use in other scripts
window.SmartClassroom = {
    loadClassroomData,
    displayClassrooms,
    updateClassroomStatus,
    showNotification,
    formatTime,
    formatDate
};