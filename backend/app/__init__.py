import os
from flask import Flask, jsonify
from backend.app.config import config
from backend.app.extensions import db, migrate, cors, limiter

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv("FLASK_CONFIG", "default")
        
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure Database URI in app config
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config.get("DATABASE_URL")
    # Suppress deprecation warning
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)
    limiter.init_app(app)
    
    # Register blueprints
    from backend.app.routes.auth import auth_bp
    from backend.app.routes.user import user_bp
    from backend.app.routes.wallet import wallet_bp
    from backend.app.routes.budget import budget_bp
    from backend.app.routes.goal import goal_bp
    from backend.app.routes.notification import notification_bp
    
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(user_bp, url_prefix="/api/v1/user")
    app.register_blueprint(wallet_bp, url_prefix="/api/v1/wallet")
    app.register_blueprint(budget_bp, url_prefix="/api/v1/budgets")
    app.register_blueprint(goal_bp, url_prefix="/api/v1/goals")
    app.register_blueprint(notification_bp, url_prefix="/api/v1/notifications")
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "reason": "NOT_FOUND",
            "message": "Resource not found."
        }), 404
        
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "reason": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred."
        }), 500

    # Security headers middleware (HTTPS/TLS enforcement and browser protections)
    @app.after_request
    def set_security_headers(response):
        # Enforce HTTPS in production via HSTS
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        # Legacy XSS filter for older browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    return app
