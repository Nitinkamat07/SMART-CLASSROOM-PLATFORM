import hashlib
import secrets
from backend.models import User, Student, Faculty, db

class AuthManager:
    def __init__(self):
        self.sessions = {}
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password, hashed_password):
        """Verify password against hash"""
        return self.hash_password(password) == hashed_password
    
    def authenticate(self, username, password):
        """Authenticate user credentials"""
        user = User.query.filter_by(username=username).first()
        
        if user and self.verify_password(password, user.password_hash):
            return user
        
        return None
    
    def create_user(self, username, password, role):
        """Create new user account"""
        if User.query.filter_by(username=username).first():
            return None  # User already exists
        
        hashed_password = self.hash_password(password)
        user = User(
            username=username,
            password_hash=hashed_password,
            role=role
        )
        
        db.session.add(user)
        db.session.commit()
        return user
    
    def generate_session_token(self):
        """Generate secure session token"""
        return secrets.token_urlsafe(32)
    
    def create_session(self, user_id):
        """Create user session"""
        token = self.generate_session_token()
        self.sessions[token] = {
            'user_id': user_id,
            'created_at': datetime.now()
        }
        return token
    
    def validate_session(self, token):
        """Validate session token"""
        if token in self.sessions:
            session = self.sessions[token]
            # Check if session is not older than 24 hours
            if (datetime.now() - session['created_at']).hours < 24:
                return session['user_id']
            else:
                del self.sessions[token]  # Remove expired session
        
        return None
    
    def get_user_role(self, user_id):
        """Get user role by ID"""
        user = User.query.get(user_id)
        return user.role if user else None