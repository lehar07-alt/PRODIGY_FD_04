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
    return jsonify({"messages": [m.to_dict() for m in messages]}), 

from app.models import PrivateConversation


# --- Start (or get existing) a private conversation with another user ---
@chat_bp.route('/conversations/start', methods=['POST'])
@jwt_required()
def start_conversation():
    user_id = int(get_jwt_identity())
    data = request.get_json()

    if not data or not data.get('other_user_id'):
        return jsonify({"error": "other_user_id is required"}), 400

    other_user_id = data.get('other_user_id')

    if other_user_id == user_id:
        return jsonify({"error": "Cannot start a conversation with yourself"}), 400

    other_user = User.query.get(other_user_id)
    if not other_user:
        return jsonify({"error": "User not found"}), 404

    # Normalize order so (A,B) and (B,A) are always stored the same way
    user_one_id, user_two_id = sorted([user_id, other_user_id])

    existing = PrivateConversation.query.filter_by(
        user_one_id=user_one_id, user_two_id=user_two_id
    ).first()

    if existing:
        return jsonify({
            "message": "Conversation already exists",
            "conversation": existing.to_dict(current_user_id=user_id)
        }), 200

    conversation = PrivateConversation(user_one_id=user_one_id, user_two_id=user_two_id)
    db.session.add(conversation)
    db.session.commit()

    return jsonify({
        "message": "Conversation started",
        "conversation": conversation.to_dict(current_user_id=user_id)
    }), 201


# --- List all of the current user's private conversations ---
@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def list_conversations():
    user_id = int(get_jwt_identity())

    conversations = PrivateConversation.query.filter(
        (PrivateConversation.user_one_id == user_id) |
        (PrivateConversation.user_two_id == user_id)
    ).all()

    return jsonify({
        "conversations": [c.to_dict(current_user_id=user_id) for c in conversations]
    }), 200


# --- Get message history for a specific private conversation ---
@chat_bp.route('/conversations/<int:conversation_id>/messages', methods=['GET'])
@jwt_required()
def conversation_messages(conversation_id):
    user_id = int(get_jwt_identity())

    conversation = PrivateConversation.query.get(conversation_id)
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404

    # Only the two participants can view this conversation
    if user_id not in (conversation.user_one_id, conversation.user_two_id):
        return jsonify({"error": "You are not part of this conversation"}), 403

    messages = Message.query.filter_by(conversation_id=conversation_id).order_by(Message.timestamp.asc()).all()
    return jsonify({"messages": [m.to_dict() for m in messages]}), 200