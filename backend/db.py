from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def init_db(app):
    """Initialize database with app"""
    db.init_app(app)
    migrate.init_app(app, db)
    
    with app.app_context():
        # Import models to ensure they're registered
        from backend.models import User, Sale, CommissionRule
        
        # Create all tables
        db.create_all()
        
        # Create default admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin_user = User(
                username='admin',
                email='admin@company.com',
                role='admin'
            )
            # Set password using model method (ensure User has set_password)
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            
            # Create default commission rule
            default_rule = CommissionRule(
                name='Standard Commission',
                rate=0.05,  # 5%
                threshold=0,
                description='Standard 5% commission on all sales',
                is_active=True
            )
            db.session.add(default_rule)
            
            # Commit changes
            db.session.commit()
