from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['SECRET_KEY'] = 'sentinel-ot-hackathon-2024'
    
    from app.routes import main_bp
    app.register_blueprint(main_bp)
    
    return app
