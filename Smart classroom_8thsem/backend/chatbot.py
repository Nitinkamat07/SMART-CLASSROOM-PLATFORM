import nltk
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
from datetime import datetime, timedelta
from backend.models import Classroom, Schedule, Student, Faculty, Attendance, db

class SmartChatbot:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', lowercase=True)
        self.intents = self.load_intents()
        self.train_model()
    
    def load_intents(self):
        """Load chatbot intents and responses"""
        return {
            'greeting': {
                'patterns': ['hello', 'hi', 'hey', 'good morning', 'good afternoon'],
                'responses': ['Hello! How can I help you today?', 'Hi there! What can I assist you with?']
            },
            'classroom_availability': {
                'patterns': ['is classroom available', 'classroom status', 'free classroom', 'available room'],
                'responses': ['Let me check classroom availability for you.']
            },
            'attendance_query': {
                'patterns': ['my attendance', 'attendance status', 'how many classes attended'],
                'responses': ['I can help you check your attendance records.']
            },
            'schedule_query': {
                'patterns': ['class schedule', 'timetable', 'when is my class', 'faculty schedule'],
                'responses': ['I can provide schedule information.']
            },
            'exam_room': {
                'patterns': ['exam room', 'examination hall', 'where is my exam'],
                'responses': ['Let me find your exam room details.']
            },
            'faculty_info': {
                'patterns': ['faculty contact', 'professor email', 'teacher information'],
                'responses': ['I can provide faculty contact information.']
            }
        }
    
    def train_model(self):
        """Train the chatbot model"""
        all_patterns = []
        self.intent_labels = []
        
        for intent, data in self.intents.items():
            for pattern in data['patterns']:
                all_patterns.append(pattern)
                self.intent_labels.append(intent)
        
        if all_patterns:
            self.vectorizer.fit(all_patterns)
            self.pattern_vectors = self.vectorizer.transform(all_patterns)
    
    def classify_intent(self, message):
        """Classify user message intent"""
        message_vector = self.vectorizer.transform([message.lower()])
        similarities = cosine_similarity(message_vector, self.pattern_vectors)[0]
        
        if len(similarities) > 0:
            best_match_idx = np.argmax(similarities)
            confidence = similarities[best_match_idx]
            
            if confidence > 0.3:  # Threshold for intent recognition
                return self.intent_labels[best_match_idx], confidence
        
        return 'unknown', 0.0
    
    def extract_entities(self, message):
        """Extract entities from user message"""
        entities = {}
        
        # Extract classroom names/numbers
        classroom_pattern = r'\b(?:room|classroom|hall)\s*([A-Z]?\d+[A-Z]?)\b'
        classroom_match = re.search(classroom_pattern, message, re.IGNORECASE)
        if classroom_match:
            entities['classroom'] = classroom_match.group(1)
        
        # Extract time references
        time_patterns = [
            r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b',
            r'\b(\d{1,2})\s*(am|pm)\b',
            r'\b(now|today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b'
        ]
        
        for pattern in time_patterns:
            time_match = re.search(pattern, message, re.IGNORECASE)
            if time_match:
                entities['time'] = time_match.group(0)
                break
        
        return entities
    
    def get_response(self, message, user_id=None):
        """Generate response to user message"""
        intent, confidence = self.classify_intent(message)
        entities = self.extract_entities(message)
        
        try:
            if intent == 'classroom_availability':
                return self.handle_classroom_availability(entities)
            elif intent == 'attendance_query':
                return self.handle_attendance_query(user_id)
            elif intent == 'schedule_query':
                return self.handle_schedule_query(entities, user_id)
            elif intent == 'exam_room':
                return self.handle_exam_room_query(user_id)
            elif intent == 'faculty_info':
                return self.handle_faculty_info(entities)
            elif intent == 'greeting':
                return np.random.choice(self.intents[intent]['responses'])
            else:
                return self.handle_general_query(message)
        except Exception as e:
            return "I'm sorry, I encountered an error processing your request. Please try again."
    
    def handle_classroom_availability(self, entities):
        """Handle classroom availability queries"""
        if 'classroom' in entities:
            classroom_name = entities['classroom']
            classroom = Classroom.query.filter_by(name=classroom_name).first()
            
            if classroom:
                current_time = datetime.now()
                
                # Check current schedule
                current_schedule = Schedule.query.filter(
                    Schedule.classroom_id == classroom.id,
                    Schedule.day_of_week == current_time.weekday(),
                    Schedule.start_time <= current_time.time(),
                    Schedule.end_time >= current_time.time()
                ).first()
                
                if current_schedule:
                    return f"Classroom {classroom_name} is currently occupied by {current_schedule.subject} until {current_schedule.end_time.strftime('%H:%M')}."
                else:
                    # Find next class
                    next_schedule = Schedule.query.filter(
                        Schedule.classroom_id == classroom.id,
                        Schedule.day_of_week == current_time.weekday(),
                        Schedule.start_time > current_time.time()
                    ).order_by(Schedule.start_time).first()
                    
                    if next_schedule:
                        return f"Classroom {classroom_name} is currently available. Next class: {next_schedule.subject} at {next_schedule.start_time.strftime('%H:%M')}."
                    else:
                        return f"Classroom {classroom_name} is available for the rest of the day."
            else:
                return f"I couldn't find classroom {classroom_name}. Please check the classroom name."
        else:
            # Show all available classrooms
            available_classrooms = Classroom.query.filter_by(status='available').all()
            if available_classrooms:
                classroom_list = ', '.join([c.name for c in available_classrooms])
                return f"Currently available classrooms: {classroom_list}"
            else:
                return "No classrooms are currently available."
    
    def handle_attendance_query(self, user_id):
        """Handle attendance queries"""
        if not user_id:
            return "Please log in to check your attendance."
        
        student = Student.query.filter_by(id=user_id).first()
        if not student:
            return "I couldn't find your student record."
        
        # Get attendance statistics
        total_classes = db.session.query(Schedule).count()
        attended_classes = db.session.query(Attendance).filter_by(
            student_id=student.id,
            status='present'
        ).count()
        
        if total_classes > 0:
            attendance_percentage = (attended_classes / total_classes) * 100
            return f"Your attendance: {attended_classes}/{total_classes} classes ({attendance_percentage:.1f}%)"
        else:
            return "No attendance records found."
    
    def handle_schedule_query(self, entities, user_id):
        """Handle schedule queries"""
        current_time = datetime.now()
        
        if 'time' in entities:
            time_ref = entities['time'].lower()
            
            if time_ref in ['today', 'now']:
                schedules = Schedule.query.filter_by(day_of_week=current_time.weekday()).all()
            elif time_ref == 'tomorrow':
                tomorrow = (current_time + timedelta(days=1)).weekday()
                schedules = Schedule.query.filter_by(day_of_week=tomorrow).all()
            else:
                # Try to parse specific day
                days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
                if time_ref in days:
                    day_num = days.index(time_ref)
                    schedules = Schedule.query.filter_by(day_of_week=day_num).all()
                else:
                    schedules = Schedule.query.filter_by(day_of_week=current_time.weekday()).all()
        else:
            schedules = Schedule.query.filter_by(day_of_week=current_time.weekday()).all()
        
        if schedules:
            schedule_text = "Schedule:\n"
            for schedule in schedules[:5]:  # Limit to 5 results
                schedule_text += f"• {schedule.subject} - {schedule.classroom.name} ({schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')})\n"
            return schedule_text
        else:
            return "No classes scheduled for the requested time."
    
    def handle_exam_room_query(self, user_id):
        """Handle exam room queries"""
        # This would typically integrate with an exam management system
        return "For exam room information, please check the exam notice board or contact the examination office."
    
    def handle_faculty_info(self, entities):
        """Handle faculty information queries"""
        faculty_list = Faculty.query.limit(5).all()
        
        if faculty_list:
            info_text = "Faculty Information:\n"
            for faculty in faculty_list:
                info_text += f"• {faculty.name} - {faculty.department} ({faculty.email})\n"
            return info_text
        else:
            return "No faculty information available."
    
    def handle_general_query(self, message):
        """Handle general queries with keyword matching"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['help', 'what can you do', 'features']):
            return """I can help you with:
• Classroom availability and status
• Your attendance records
• Class schedules and timetables
• Faculty contact information
• General college information

Just ask me anything!"""
        
        elif any(word in message_lower for word in ['thank', 'thanks']):
            return "You're welcome! Is there anything else I can help you with?"
        
        else:
            return "I'm not sure how to help with that. You can ask me about classroom availability, schedules, attendance, or faculty information."