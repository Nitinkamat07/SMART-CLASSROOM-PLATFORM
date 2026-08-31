import google.generativeai as genai
import os

class GeminiChatbot:
    def __init__(self):
        # Configure Gemini API
        api_key = os.getenv('GEMINI_API_KEY', 'YOUR_GEMINI_API_KEY_HERE')
        genai.configure(api_key=api_key)
        
        # Initialize model
        self.model = genai.GenerativeModel('gemini-pro')
        
        # System context for classroom management
        self.context = """You are an AI assistant for a Smart Classroom Management System. 
        You help students, faculty, and administrators with:
        - Classroom availability and schedules
        - Attendance information
        - Timetable queries
        - Faculty contact information
        - General academic queries
        
        Be helpful, concise, and professional. If you don't have specific data, provide general guidance."""
        
    def get_response(self, user_message):
        try:
            # Create prompt with context
            prompt = f"{self.context}\n\nUser: {user_message}\nAssistant:"
            
            # Generate response
            response = self.model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            return f"I'm having trouble processing your request. Please try again or contact support. Error: {str(e)}"
    
    def get_classroom_response(self, user_message, classroom_data=None):
        """Enhanced response with classroom data"""
        try:
            context_with_data = self.context
            
            if classroom_data:
                context_with_data += f"\n\nCurrent classroom data: {classroom_data}"
            
            prompt = f"{context_with_data}\n\nUser: {user_message}\nAssistant:"
            response = self.model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            return "I'm currently unable to process your request. Please try again later."
