
// Mock Socket.IO for app_simple.py
if (typeof window.io === 'undefined') {
    window.io = function() {
        return {
            on: function(event, callback) {},
            emit: function(event, data) {}
        };
    };
}

// Attention Monitoring System - Frontend JavaScript

class AttentionMonitor {
    constructor() {
        this.sessionId = null;
        this.isMonitoring = false;
        this.videoStream = null;
        this.socket = null;
        this.stats = { attentive: 0, distracted: 0, sleeping: 0 };
    }

    async startMonitoring(facultyId, classId) {
        try {
            // Start session
            const response = await fetch('/api/attention/start-session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ faculty_id: facultyId, class_id: classId })
            });
            const data = await response.json();
            this.sessionId = data.session_id;

            // Start webcam
            this.videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
            const video = document.getElementById('attentionVideo');
            video.srcObject = this.videoStream;

            // Connect WebSocket
            this.socket = io.connect(location.origin);
            this.socket.on('attention_update', (data) => this.updateUI(data));

            // Start processing frames
            this.isMonitoring = true;
            this.processFrames();

            return { success: true, sessionId: this.sessionId };
        } catch (error) {
            console.error('Error starting monitoring:', error);
            return { success: false, error: error.message };
        }
    }

    async processFrames() {
        const video = document.getElementById('attentionVideo');
        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');

        const processFrame = async () => {
            if (!this.isMonitoring) return;

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            ctx.drawImage(video, 0, 0);

            const frameData = canvas.toDataURL('image/jpeg', 0.8);

            try {
                await fetch('/api/attention/process-frame', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: this.sessionId,
                        frame: frameData
                    })
                });
            } catch (error) {
                console.error('Error processing frame:', error);
            }

            setTimeout(processFrame, 1000); // Process every second
        };

        processFrame();
    }

    async stopMonitoring() {
        this.isMonitoring = false;

        if (this.videoStream) {
            this.videoStream.getTracks().forEach(track => track.stop());
        }

        if (this.socket) {
            this.socket.disconnect();
        }

        if (this.sessionId) {
            const response = await fetch('/api/attention/end-session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.sessionId })
            });
            const data = await response.json();
            return data;
        }
    }

    updateUI(data) {
        this.stats = data.stats;

        // Update status indicator
        const statusEl = document.getElementById('attentionStatus');
        if (statusEl) {
            statusEl.textContent = data.status.toUpperCase();
            statusEl.className = `status-${data.status}`;
        }

        // Update confidence
        const confidenceEl = document.getElementById('attentionConfidence');
        if (confidenceEl) {
            confidenceEl.textContent = `${(data.confidence * 100).toFixed(1)}%`;
        }

        // Update statistics
        this.updateStatsChart();
    }

    updateStatsChart() {
        const attentiveEl = document.getElementById('attentivePercentage');
        const distractedEl = document.getElementById('distractedPercentage');
        const sleepingEl = document.getElementById('sleepingPercentage');

        if (attentiveEl) attentiveEl.textContent = `${this.stats.attentive.toFixed(1)}%`;
        if (distractedEl) distractedEl.textContent = `${this.stats.distracted.toFixed(1)}%`;
        if (sleepingEl) sleepingEl.textContent = `${this.stats.sleeping.toFixed(1)}%`;

        // Update progress bars
        const attentiveBar = document.getElementById('attentiveBar');
        const distractedBar = document.getElementById('distractedBar');
        const sleepingBar = document.getElementById('sleepingBar');

        if (attentiveBar) attentiveBar.style.width = `${this.stats.attentive}%`;
        if (distractedBar) distractedBar.style.width = `${this.stats.distracted}%`;
        if (sleepingBar) sleepingBar.style.width = `${this.stats.sleeping}%`;
    }

    async getHistory(facultyId = null, limit = 10) {
        const url = `/api/attention/history?${facultyId ? `faculty_id=${facultyId}&` : ''}limit=${limit}`;
        const response = await fetch(url);
        const data = await response.json();
        return data.history;
    }
}

// Initialize global instance
const attentionMonitor = new AttentionMonitor();

// UI Functions
function startAttentionMonitoring() {
    const facultyId = currentUser; // From existing auth system
    const classId = document.getElementById('classSelect').value;

    attentionMonitor.startMonitoring(facultyId, classId).then(result => {
        if (result.success) {
            document.getElementById('startAttentionBtn').style.display = 'none';
            document.getElementById('stopAttentionBtn').style.display = 'block';
            document.getElementById('attentionStats').style.display = 'block';
        } else {
            alert('Failed to start monitoring: ' + result.error);
        }
    });
}

function stopAttentionMonitoring() {
    attentionMonitor.stopMonitoring().then(data => {
        document.getElementById('startAttentionBtn').style.display = 'block';
        document.getElementById('stopAttentionBtn').style.display = 'none';
        
        alert(`Session ended!\nAttentive: ${data.stats.attentive.toFixed(1)}%\nDistracted: ${data.stats.distracted.toFixed(1)}%\nSleeping: ${data.stats.sleeping.toFixed(1)}%\nDuration: ${Math.floor(data.duration / 60)} minutes`);
    });
}

function loadAttentionHistory() {
    attentionMonitor.getHistory().then(history => {
        const historyEl = document.getElementById('attentionHistory');
        historyEl.innerHTML = '';

        history.forEach(record => {
            const div = document.createElement('div');
            div.className = 'history-item';
            div.innerHTML = `
                <div class="history-date">${new Date(record.timestamp).toLocaleString()}</div>
                <div class="history-stats">
                    <span class="stat-attentive">✓ ${record.attentive_percentage.toFixed(1)}%</span>
                    <span class="stat-distracted">⚠ ${record.distracted_percentage.toFixed(1)}%</span>
                    <span class="stat-sleeping">😴 ${record.sleeping_percentage.toFixed(1)}%</span>
                </div>
                <div class="history-grade">Grade: ${record.attention_grade}</div>
            `;
            historyEl.appendChild(div);
        });
    });
}
