import cv2
import numpy as np
import dlib
from scipy.spatial import distance
from collections import deque
import time

class AttentionDetector:
    def __init__(self):
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor('ml_models/shape_predictor_68_face_landmarks.dat')
        
        # Eye aspect ratio threshold
        self.EYE_AR_THRESH = 0.25
        self.EYE_AR_CONSEC_FRAMES = 3
        
        # Head pose thresholds
        self.HEAD_POSE_THRESH = 20
        
        # Tracking
        self.eye_counter = 0
        self.attention_history = deque(maxlen=30)  # Last 30 frames
        
    def eye_aspect_ratio(self, eye):
        """Calculate eye aspect ratio"""
        A = distance.euclidean(eye[1], eye[5])
        B = distance.euclidean(eye[2], eye[4])
        C = distance.euclidean(eye[0], eye[3])
        ear = (A + B) / (2.0 * C)
        return ear
    
    def get_head_pose(self, shape, frame_shape):
        """Estimate head pose angle"""
        image_points = np.array([
            shape[30],  # Nose tip
            shape[8],   # Chin
            shape[36],  # Left eye left corner
            shape[45],  # Right eye right corner
            shape[48],  # Left mouth corner
            shape[54]   # Right mouth corner
        ], dtype="double")
        
        model_points = np.array([
            (0.0, 0.0, 0.0),
            (0.0, -330.0, -65.0),
            (-225.0, 170.0, -135.0),
            (225.0, 170.0, -135.0),
            (-150.0, -150.0, -125.0),
            (150.0, -150.0, -125.0)
        ])
        
        focal_length = frame_shape[1]
        center = (frame_shape[1] / 2, frame_shape[0] / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype="double")
        
        dist_coeffs = np.zeros((4, 1))
        
        success, rotation_vector, translation_vector = cv2.solvePnP(
            model_points, image_points, camera_matrix, dist_coeffs,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
        
        rotation_mat, _ = cv2.Rodrigues(rotation_vector)
        pose_mat = cv2.hconcat((rotation_mat, translation_vector))
        _, _, _, _, _, _, euler_angles = cv2.decomposeProjectionMatrix(pose_mat)
        
        pitch, yaw, roll = euler_angles.flatten()[:3]
        return pitch, yaw, roll
    
    def detect_attention(self, frame):
        """Detect student attention level from frame"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector(gray, 0)
        
        if len(faces) == 0:
            return 'no_face', 0.0, {}
        
        results = []
        for face in faces:
            shape = self.predictor(gray, face)
            shape = np.array([[p.x, p.y] for p in shape.parts()])
            
            # Extract eye coordinates
            left_eye = shape[36:42]
            right_eye = shape[42:48]
            
            # Calculate eye aspect ratio
            left_ear = self.eye_aspect_ratio(left_eye)
            right_ear = self.eye_aspect_ratio(right_eye)
            ear = (left_ear + right_ear) / 2.0
            
            # Get head pose
            pitch, yaw, roll = self.get_head_pose(shape, frame.shape)
            
            # Classify attention
            status = 'attentive'
            confidence = 1.0
            
            # Check if sleeping (eyes closed)
            if ear < self.EYE_AR_THRESH:
                self.eye_counter += 1
                if self.eye_counter >= self.EYE_AR_CONSEC_FRAMES:
                    status = 'sleeping'
                    confidence = 0.9
            else:
                self.eye_counter = 0
            
            # Check if distracted (head turned away)
            if abs(yaw) > self.HEAD_POSE_THRESH or abs(pitch) > self.HEAD_POSE_THRESH:
                status = 'distracted'
                confidence = 0.8
            
            results.append({
                'status': status,
                'confidence': confidence,
                'ear': ear,
                'head_pose': {'pitch': pitch, 'yaw': yaw, 'roll': roll},
                'bbox': (face.left(), face.top(), face.width(), face.height())
            })
        
        # Aggregate results
        if results:
            statuses = [r['status'] for r in results]
            avg_confidence = np.mean([r['confidence'] for r in results])
            
            # Majority vote
            status_counts = {s: statuses.count(s) for s in set(statuses)}
            final_status = max(status_counts, key=status_counts.get)
            
            self.attention_history.append(final_status)
            
            return final_status, avg_confidence, results[0]
        
        return 'no_face', 0.0, {}
    
    def get_attention_stats(self):
        """Get attention statistics from history"""
        if not self.attention_history:
            return {'attentive': 0, 'distracted': 0, 'sleeping': 0}
        
        total = len(self.attention_history)
        stats = {
            'attentive': self.attention_history.count('attentive') / total * 100,
            'distracted': self.attention_history.count('distracted') / total * 100,
            'sleeping': self.attention_history.count('sleeping') / total * 100
        }
        return stats
    
    def process_video_stream(self, video_source=0):
        """Process video stream and yield attention data"""
        cap = cv2.VideoCapture(video_source)
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            status, confidence, details = self.detect_attention(frame)
            stats = self.get_attention_stats()
            
            yield {
                'status': status,
                'confidence': confidence,
                'stats': stats,
                'timestamp': time.time(),
                'details': details
            }
        
        cap.release()
