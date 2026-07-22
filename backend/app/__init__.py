from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from app.config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    CORS(app)
    socketio.init_app(app)

    from app.auth_routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/api/auth')

    from app.chat_routes import chat_bp
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    from app import models
    from app import socket_events

    with app.app_context():
        db.create_all()

    return app