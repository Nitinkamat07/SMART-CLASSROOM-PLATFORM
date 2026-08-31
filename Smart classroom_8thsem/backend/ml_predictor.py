import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import os
from datetime import datetime, timedelta
from backend.models import ClassroomUsage, Classroom, Schedule, db

class ClassroomPredictor:
    def __init__(self):
        self.usage_model = None
        self.availability_model = None
        self.scaler = StandardScaler()
        self.model_path = 'ml_models/classroom_predictor.pkl'
        self.load_models()
    
    def load_models(self):
        """Load trained models"""
        if os.path.exists(self.model_path):
            with open(self.model_path, 'rb') as f:
                data = pickle.load(f)
                self.usage_model = data.get('usage_model')
                self.availability_model = data.get('availability_model')
                self.scaler = data.get('scaler', StandardScaler())
    
    def save_models(self):
        """Save trained models"""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        data = {
            'usage_model': self.usage_model,
            'availability_model': self.availability_model,
            'scaler': self.scaler
        }
        with open(self.model_path, 'wb') as f:
            pickle.dump(data, f)
    
    def prepare_features(self, datetime_obj, classroom_id=None):
        """Prepare features for prediction"""
        features = [
            datetime_obj.hour,
            datetime_obj.weekday(),
            datetime_obj.day,
            datetime_obj.month,
            1 if datetime_obj.weekday() < 5 else 0,  # is_weekday
        ]
        
        if classroom_id:
            features.append(classroom_id)
        
        return np.array(features).reshape(1, -1)
    
    def train_usage_model(self):
        """Train classroom usage prediction model"""
        # Get historical usage data
        usage_data = db.session.query(ClassroomUsage).all()
        
        if len(usage_data) < 100:  # Need minimum data
            return False
        
        # Prepare training data
        X = []
        y = []
        
        for usage in usage_data:
            datetime_obj = datetime.combine(usage.date, datetime.min.time()) + timedelta(hours=usage.hour)
            features = self.prepare_features(datetime_obj, usage.classroom_id)[0]
            X.append(features)
            y.append(usage.utilization_rate)
        
        X = np.array(X)
        y = np.array(y)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
        
        self.usage_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.usage_model.fit(X_train, y_train)
        
        # Train availability classifier
        y_available = (y < 0.3).astype(int)  # Available if utilization < 30%
        self.availability_model = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.availability_model.fit(X_train, y_available[:-len(y_test)] if len(y_available) > len(y_test) else y_available)
        
        self.save_models()
        return True
    
    def predict_classroom_usage(self, hours_ahead=24):
        """Predict classroom usage for next N hours"""
        if not self.usage_model:
            return {'error': 'Model not trained'}
        
        predictions = []
        current_time = datetime.now()
        
        classrooms = Classroom.query.all()
        
        for hour in range(hours_ahead):
            future_time = current_time + timedelta(hours=hour)
            
            for classroom in classrooms:
                features = self.prepare_features(future_time, classroom.id)
                features_scaled = self.scaler.transform(features)
                
                usage_pred = self.usage_model.predict(features_scaled)[0]
                availability_pred = self.availability_model.predict_proba(features_scaled)[0][1]
                
                predictions.append({
                    'classroom_id': classroom.id,
                    'classroom_name': classroom.name,
                    'datetime': future_time.isoformat(),
                    'predicted_usage': round(usage_pred, 2),
                    'availability_probability': round(availability_pred, 2),
                    'status': 'available' if availability_pred > 0.7 else 'likely_occupied'
                })
        
        return predictions
    
    def get_optimization_suggestions(self):
        """Get AI-powered optimization suggestions"""
        suggestions = []
        
        # Analyze current usage patterns
        current_time = datetime.now()
        
        # Get underutilized classrooms
        underutilized = db.session.query(ClassroomUsage).filter(
            ClassroomUsage.utilization_rate < 0.3,
            ClassroomUsage.date >= current_time.date() - timedelta(days=7)
        ).all()
        
        if underutilized:
            classroom_usage = {}
            for usage in underutilized:
                if usage.classroom_id not in classroom_usage:
                    classroom_usage[usage.classroom_id] = []
                classroom_usage[usage.classroom_id].append(usage.utilization_rate)
            
            for classroom_id, rates in classroom_usage.items():
                avg_rate = np.mean(rates)
                classroom = Classroom.query.get(classroom_id)
                
                if avg_rate < 0.2:
                    suggestions.append({
                        'type': 'underutilized',
                        'classroom': classroom.name,
                        'message': f'{classroom.name} is underutilized (avg {avg_rate:.1%}). Consider reassigning classes.',
                        'priority': 'medium'
                    })
        
        # Find peak hours
        peak_hours = db.session.query(ClassroomUsage.hour, db.func.avg(ClassroomUsage.utilization_rate)).group_by(
            ClassroomUsage.hour
        ).having(db.func.avg(ClassroomUsage.utilization_rate) > 0.8).all()
        
        if peak_hours:
            peak_times = [f"{hour:02d}:00" for hour, _ in peak_hours]
            suggestions.append({
                'type': 'peak_hours',
                'message': f'Peak usage hours: {", ".join(peak_times)}. Consider spreading classes more evenly.',
                'priority': 'high'
            })
        
        return suggestions
    
    def predict_next_available_slot(self, classroom_id):
        """Predict when a classroom will next be available"""
        if not self.availability_model:
            return None
        
        current_time = datetime.now()
        
        for hour in range(1, 48):  # Check next 48 hours
            future_time = current_time + timedelta(hours=hour)
            features = self.prepare_features(future_time, classroom_id)
            features_scaled = self.scaler.transform(features)
            
            availability_prob = self.availability_model.predict_proba(features_scaled)[0][1]
            
            if availability_prob > 0.8:  # 80% chance of being available
                return {
                    'datetime': future_time.isoformat(),
                    'probability': round(availability_prob, 2),
                    'hours_from_now': hour
                }
        
        return None