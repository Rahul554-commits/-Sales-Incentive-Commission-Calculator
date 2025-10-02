from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from backend.db import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with sales
    sales = db.relationship('Sale', backref='salesperson', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    sale_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date())
    commission_rate = db.Column(db.Float, default=0.05)
    commission_amount = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_commission(self):
        """Calculate commission based on amount and rate"""
        self.commission_amount = self.amount * self.commission_rate
        return self.commission_amount
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'salesperson': self.salesperson.username,
            'customer_name': self.customer_name,
            'product_name': self.product_name,
            'amount': self.amount,
            'sale_date': self.sale_date.isoformat(),
            'commission_rate': self.commission_rate,
            'commission_amount': self.commission_amount,
            'created_at': self.created_at.isoformat()
        }

class CommissionRule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rate = db.Column(db.Float, nullable=False)  # Commission rate (e.g., 0.05 for 5%)
    threshold = db.Column(db.Float, default=0)  # Minimum sale amount to qualify
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'rate': self.rate,
            'threshold': self.threshold,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }