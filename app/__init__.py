import os
from flask import Flask, jsonify, render_template
from app.config import config_by_name, Config

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'production')

    app = Flask(
        __name__,
        static_folder='static',
        template_folder='templates'
    )
    
    app_config = config_by_name.get(config_name, Config)
    app.config.from_object(app_config)

    # Register blueprints
    from app.routes.gnss_routes import gnss_bp
    from app.routes.chang_routes import chang_bp

    app.register_blueprint(gnss_bp)
    app.register_blueprint(chang_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Sahifa yoki resurs topilmadi", "status": 404}), 404

    @app.errorhandler(500)
    def server_error(e):
        return jsonify({"error": "Server ichki xatosi yuz berdi", "status": 500}), 500

    return app
