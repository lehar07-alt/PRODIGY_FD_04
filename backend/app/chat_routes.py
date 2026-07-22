from flask import Blueprint, jsonify

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "Chat routes working!"})