# Student Attention Detection - Integration Guide

## 📋 Overview
This module adds real-time student attention monitoring using computer vision and AI.

## 🔧 Installation

### 1. Install Required Packages
```bash
pip install opencv-python dlib scipy flask-socketio
```

### 2. Download dlib Model
Download the shape predictor model:
```bash
# Download from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
# Extract to: ml_models/shape_predictor_68_face_landmarks.dat
```

### 3. Update requirements.txt
Add these lines:
```
opencv-python==4.8.1.78
dlib==19.24.2
scipy==1.11.4
flask-socketio==5.3.5
python-socketio==5.10.0
```

## 🔌 Flask App Integration

### 1. Update app.py
```python
from flask import Flask
from flask_socketio import SocketIO
from backend.attention_api import attention_bp

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Register attention blueprint
app.register_blueprint(attention_bp)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
```

### 2. Update models.py
Add these imports at the top:
```python
from sqlalchemy import text
```

### 3. Initialize Database
```bash
psql classroom_management_db < database/attention_schema.sql
```

## 📊 API Endpoints

### Start Monitoring Session
```
POST /api/attention/start-session
Body: { "faculty_id": 1, "class_id": 1 }
Response: { "success": true, "session_id": "...", "log_id": 1 }
```

### Process Frame
```
POST /api/attention/process-frame
Body: { "session_id": "...", "frame": "data:image/jpeg;base64,..." }
Response: { "success": true, "status": "attentive", "confidence": 0.95, "stats": {...} }
```

### End Session
```
POST /api/attention/end-session
Body: { "session_id": "..." }
Response: { "success": true, "stats": {...}, "duration": 3600 }
```

### Get Statistics
```
GET /api/attention/stats/<log_id>
Response: { "id": 1, "attentive_percentage": 80.0, ... }
```

### Get History
```
GET /api/attention/history?faculty_id=1&limit=10
Response: { "history": [...] }
```

## 🎨 Frontend Integration

### 1. Add to Faculty Dashboard (index.html)
```html
<!-- Add button to faculty dashboard -->
<div class="action-btn" onclick="openModal('attentionMonitorModal')">
    <i class="fas fa-eye"></i>
    <p>Monitor Attention</p>
</div>

<!-- Add modal -->
<div id="attentionMonitorModal" class="modal">
    <div class="modal-content" style="max-width: 900px;">
        <span class="close" onclick="closeModal('attentionMonitorModal')">&times;</span>
        <!-- Include attention_monitoring.html content here -->
    </div>
</div>

<!-- Add scripts -->
<script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
<script src="/static/js/attention-monitor.js"></script>
```

### 2. Add CSS Styles
Copy styles from `attention_monitoring.html` to your main CSS file.

## 🧪 Testing

### 1. Test Attention Detection
```python
from backend.attention_detector import AttentionDetector
import cv2

detector = AttentionDetector()
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    status, confidence, details = detector.detect_attention(frame)
    print(f"Status: {status}, Confidence: {confidence}")
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
```

### 2. Test API
```bash
# Start session
curl -X POST http://localhost:5000/api/attention/start-session \
  -H "Content-Type: application/json" \
  -d '{"faculty_id": 1, "class_id": 1}'

# Get history
curl http://localhost:5000/api/attention/history?limit=5
```

## 📈 Features

### Attention States
- **Attentive**: Eyes open, head facing forward
- **Distracted**: Head turned away (>20° yaw/pitch)
- **Sleeping**: Eyes closed for >3 consecutive frames
- **No Face**: No face detected in frame

### Metrics Tracked
- Eye Aspect Ratio (EAR)
- Head Pose (pitch, yaw, roll)
- Confidence Score
- Real-time Statistics
- Session Duration

### Database Tables
- `class_attention_logs`: Overall class statistics
- `student_attention_logs`: Individual student records
- `attention_analytics`: View for reporting

## 🔒 Security Considerations

1. **Camera Permissions**: Requires HTTPS or localhost
2. **Data Privacy**: Store only aggregated statistics
3. **Access Control**: Restrict to faculty role only
4. **Session Management**: Auto-cleanup after timeout

## 🚀 Performance Tips

1. Process frames at 1 FPS (not every frame)
2. Use smaller frame resolution (640x480)
3. Implement frame skipping for multiple students
4. Use WebSocket for real-time updates
5. Cache dlib model in memory

## 📝 Usage Example

```javascript
// Faculty dashboard
const monitor = new AttentionMonitor();

// Start monitoring
await monitor.startMonitoring(facultyId, classId);

// Monitor runs automatically, updates UI via WebSocket

// Stop monitoring
const results = await monitor.stopMonitoring();
console.log('Final stats:', results.stats);
```

## 🐛 Troubleshooting

### dlib Model Not Found
```bash
cd ml_models
wget http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2
bunzip2 shape_predictor_68_face_landmarks.dat.bz2
```

### Camera Not Working
- Use HTTPS or localhost
- Check browser permissions
- Verify camera is not in use

### WebSocket Connection Failed
- Install flask-socketio: `pip install flask-socketio`
- Use socketio.run() instead of app.run()
- Check CORS settings

## 📊 Sample Output

```json
{
  "status": "attentive",
  "confidence": 0.92,
  "stats": {
    "attentive": 75.5,
    "distracted": 18.2,
    "sleeping": 6.3
  },
  "details": {
    "ear": 0.28,
    "head_pose": {
      "pitch": 5.2,
      "yaw": -3.1,
      "roll": 1.8
    }
  }
}
```

## ✅ Checklist

- [ ] Install dependencies
- [ ] Download dlib model
- [ ] Run database schema
- [ ] Register Flask blueprint
- [ ] Add frontend components
- [ ] Test camera access
- [ ] Test API endpoints
- [ ] Configure WebSocket
- [ ] Test end-to-end flow

---

**Module Complete!** 🎉

The attention detection system is now ready to use. Faculty can monitor student attention in real-time during lectures.
