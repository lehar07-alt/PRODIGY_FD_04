from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models import Room, RoomMembership, User, Message

chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/ping', methods=['GET'])
def ping():
    return jsonify({"message": "Chat routes working!"})


# --- Create a new room ---
@chat_bp.route('/rooms', methods=['POST'])
@jwt_required()
def create_room():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or not data.get('name', '').strip():
        return jsonify({"error": "Room name is required"}), 400

    name = data.get('name').strip()

    if len(name) < 2:
        return jsonify({"error": "Room name must be at least 2 characters"}), 400

    room = Room(name=name, created_by=user_id)
    db.session.add(room)
    db.session.flush()  # lets us get room.id before committing

    # Creator automatically joins their own room
    membership = RoomMembership(user_id=user_id, room_id=room.id)
    db.session.add(membership)
    db.session.commit()

    return jsonify({"message": "Room created", "room": room.to_dict()}), 201


# --- List all rooms (so users can discover and join them) ---
@chat_bp.route('/rooms', methods=['GET'])
@jwt_required()
def list_rooms():
    rooms = Room.query.all()
    return jsonify({"rooms": [r.to_dict() for r in rooms]}), 200


# --- List rooms the CURRENT user has joined ---
@chat_bp.route('/rooms/mine', methods=['GET'])
@jwt_required()
def my_rooms():
    user_id = int(get_jwt_identity())
    memberships = RoomMembership.query.filter_by(user_id=user_id).all()
    rooms = [m.room.to_dict() for m in memberships]
    return jsonify({"rooms": rooms}), 200


# --- Join a room ---
@chat_bp.route('/rooms/<int:room_id>/join', methods=['POST'])
@jwt_required()
def join_room_route(room_id):
    user_id = int(get_jwt_identity())

    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    existing = RoomMembership.query.filter_by(user_id=user_id, room_id=room_id).first()
    if existing:
        return jsonify({"error": "Already a member of this room"}), 409

    membership = RoomMembership(user_id=user_id, room_id=room_id)
    db.session.add(membership)
    db.session.commit()

    return jsonify({"message": f"Joined room '{room.name}'"}), 200


# --- List members of a room ---
@chat_bp.route('/rooms/<int:room_id>/members', methods=['GET'])
@jwt_required()
def room_members(room_id):
    room = Room.query.get(room_id)
    if not room:
        return jsonify({"error": "Room not found"}), 404

    members = [m.room_id and User.query.get(m.user_id).to_dict() for m in room.members]
    return jsonify({"members": members}), 200


# --- Get message history for a room ---
@chat_bp.route('/rooms/<int:room_id>/messages', methods=['GET'])
@jwt_required()
def room_messages(room_id):
    user_id = int(get_jwt_identity())

    # Only members can view a room's history
    membership = RoomMembership.query.filter_by(user_id=user_id, room_id=room_id).first()
    if not membership:
        return jsonify({"error": "You must join this room to view its messages"}), 403

    messages = Message.query.filter_by(room_id=room_id).order_by(Message.timestamp.asc()).all()
    return jsonify({"messages": [m.to_dict() for m in messages]}), 200