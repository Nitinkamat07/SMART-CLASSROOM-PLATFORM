import cv2
import numpy as np
import face_recognition
import pickle
import os
from PIL import Image
import base64
import io
from backend.models import Student, db
import json

class FaceRecognitionSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.model_path = 'ml_models/face_recognition_model.pkl'
        self.load_model()
    
    def load_model(self):
        """Load existing face recognition model"""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.known_face_encodings = data['encodings']
                self.known_face_names = data['names']
    
    def save_model(self):
        """Save face recognition model"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        data = {
            'encodings': self.known_face_encodings,
            'names': self.known_face_names
        }
        with open(self.model_path, 'wb') as f:
            pickle.dump(data, f)
    
    def add_face(self, student_id, image_path):
        """Add a new face to the recognition system"""
        try:
            # Load image
            image = face_recognition.load_image_file(image_path)
            
            # Get face encodings
            face_encodings = face_recognition.face_encodings(image)
            
            if len(face_encodings) > 0:
                face_encoding = face_encodings[0]
                
                # Add to known faces
                self.known_face_encodings.append(face_encoding)
                self.known_face_names.append(student_id)
                
                # Save to database
                student = Student.query.filter_by(student_id=student_id).first()
                if student:
                    student.face_encoding = json.dumps(face_encoding.tolist())
                    db.session.commit()
                
                # Save model
                self.save_model()
                return True
            
            return False
        except Exception as e:
            print(f"Error adding face: {e}")
            return False
    
    def recognize_face(self, image_data):
        """Recognize face from base64 image data"""
        try:
            # Decode base64 image
            image_data = image_data.split(',')[1]  # Remove data:image/jpeg;base64,
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB array
            rgb_image = np.array(image.convert('RGB'))
            
            # Find face locations and encodings
            face_locations = face_recognition.face_locations(rgb_image)
            face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
            
            for face_encoding in face_encodings:
                # Compare with known faces
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    
                    if matches[best_match_index] and face_distances[best_match_index] < 0.6:
                        student_id = self.known_face_names[best_match_index]
                        confidence = 1 - face_distances[best_match_index]
                        
                        # Get student database ID
                        student = Student.query.filter_by(student_id=student_id).first()
                        if student:
                            return student.id
            
            return None
        except Exception as e:
            print(f"Error recognizing face: {e}")
            return None
    
    def train_from_database(self):
        """Train model from all faces stored in database"""
        students = Student.query.filter(Student.face_encoding.isnot(None)).all()
        
        self.known_face_encodings = []
        self.known_face_names = []
        
        for student in students:
            try:
                encoding = json.loads(student.face_encoding)
                self.known_face_encodings.append(np.array(encoding))
                self.known_face_names.append(student.student_id)
            except Exception as e:
                print(f"Error loading encoding for student {student.student_id}: {e}")
        
        self.save_model()
        return len(self.known_face_encodings)
    
    def get_face_count(self):
        """Get number of registered faces"""
        return len(self.known_face_encodings)