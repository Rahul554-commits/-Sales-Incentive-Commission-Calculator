from flask import Flask
from flask_cors import CORS
from config.config import config   # keep this if config/ is at project root
from backend.db import init_db
from backend.auth import init_jwt


def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    CORS(app)
    init_db(app)
    init_jwt(app)
    
    # Register blueprints
    from backend.routes.user_routes import user_bp
    from backend.routes.sales_routes import sales_bp
    from backend.routes.commission_routes import commission_bp
    
    app.register_blueprint(user_bp, url_prefix='/api/users')
    app.register_blueprint(sales_bp, url_prefix='/api/sales')
    app.register_blueprint(commission_bp, url_prefix='/api/commission')
    
    # Health check endpoint
    @app.route('/api/health')
    def health_check():
        return {'status': 'healthy', 'message': 'Sales Incentive Calculator API'}
    
    return app
