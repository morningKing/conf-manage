"""
WebSocket module for real-time collaboration
"""
from flask_socketio import SocketIO
from config import Config

socketio = SocketIO(cors_allowed_origins=Config.CORS_ORIGINS)

__all__ = ['socketio']