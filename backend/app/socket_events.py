from flask_socketio import join_room, leave_room, emit
from flask_jwt_extended import decode_token
from app import socketio, db
from app.models import User, Message, RoomMembership, PrivateConversation
from datetime import datetime

# Keep track of which socket connection belongs to which user
# Format: { socket_id: user_id }
connected_users = {}


def get_user_from_token(token):
    """Manually decode a JWT (since WebSocket connections don't use standard headers)."""
    try:
        decoded = decode_token(token)
        user_id = int(decoded['sub'])
        return User.query.get(user_id)
    except Exception:
        return None

@socketio.on('authenticate')
def handle_authenticate(data):
    """
    Client sends this once, right after connecting: { token }
    Marks the user online and tells everyone else.
    """
    from flask import request

    token = data.get('token')
    user = get_user_from_token(token)

    if not user:
        emit('error', {'message': 'Invalid or missing authentication token'})
        return

    connected_users[request.sid] = user.id

    join_room(f"user_{user.id}")

    user.is_online = True
    db.session.commit()

    emit('presence_update', {
        'user_id': user.id,
        'username': user.username,
        'is_online': True
    }, broadcast=True)

    print(f'{user.username} is now online')


@socketio.on('connect')
def handle_connect():
    print('A client connected (awaiting authentication)')


@socketio.on('disconnect')
def handle_disconnect():
    from flask import request
    sid = request.sid

    user_id = connected_users.pop(sid, None)
    if user_id:
        user = User.query.get(user_id)
        if user:
            user.is_online = False
            user.last_seen = datetime.utcnow()
            db.session.commit()

            emit('presence_update', {
                'user_id': user.id,
                'username': user.username,
                'is_online': False,
                'last_seen': user.last_seen.isoformat()
            }, broadcast=True)

            print(f'{user.username} went offline')

@socketio.on('join_room_channel')
def handle_join_room(data):
    """
    Client sends: { room_id, token }
    We verify the user, confirm they're a member of the room, then subscribe
    their socket connection to that room's live channel.
    """
    from flask import request

    token = data.get('token')
    room_id = data.get('room_id')

    user = get_user_from_token(token)
    if not user:
        emit('error', {'message': 'Invalid or missing authentication token'})
        return

    membership = RoomMembership.query.filter_by(user_id=user.id, room_id=room_id).first()
    if not membership:
        emit('error', {'message': 'You are not a member of this room'})
        return

    connected_users[request.sid] = user.id

    room_channel = f"room_{room_id}"
    join_room(room_channel)

    emit('joined_room', {'room_id': room_id, 'username': user.username}, room=room_channel)
    print(f'{user.username} joined room channel {room_channel}')


@socketio.on('leave_room_channel')
def handle_leave_room(data):
    room_id = data.get('room_id')
    room_channel = f"room_{room_id}"
    leave_room(room_channel)


@socketio.on('send_room_message')
def handle_send_room_message(data):
    """
    Client sends: { room_id, token, content }
    We verify, save the message to the database (persistent history),
    then broadcast it live to everyone currently in that room's channel.
    """
    token = data.get('token')
    room_id = data.get('room_id')
    content = data.get('content', '').strip()

    user = get_user_from_token(token)
    if not user:
        emit('error', {'message': 'Invalid or missing authentication token'})
        return

    if not content:
        emit('error', {'message': 'Message content cannot be empty'})
        return

    membership = RoomMembership.query.filter_by(user_id=user.id, room_id=room_id).first()
    if not membership:
        emit('error', {'message': 'You are not a member of this room'})
        return

    # --- Persist to database ---
    message = Message(sender_id=user.id, room_id=room_id, content=content)
    db.session.add(message)
    db.session.commit()

    # --- Broadcast to everyone in the room's live channel ---
    room_channel = f"room_{room_id}"
    emit('new_room_message', message.to_dict(), room=room_channel)

from app.models import PrivateConversation


@socketio.on('join_conversation_channel')
def handle_join_conversation(data):
    """
    Client sends: { conversation_id, token }
    Verifies the user is one of the two participants, then subscribes
    their socket to that conversation's live channel.
    """
    token = data.get('token')
    conversation_id = data.get('conversation_id')

    user = get_user_from_token(token)
    if not user:
        emit('error', {'message': 'Invalid or missing authentication token'})
        return

    conversation = PrivateConversation.query.get(conversation_id)
    if not conversation:
        emit('error', {'message': 'Conversation not found'})
        return

    if user.id not in (conversation.user_one_id, conversation.user_two_id):
        emit('error', {'message': 'You are not part of this conversation'})
        return

    conv_channel = f"conversation_{conversation_id}"
    join_room(conv_channel)

    emit('joined_conversation', {'conversation_id': conversation_id, 'username': user.username}, room=conv_channel)
    print(f'{user.username} joined conversation channel {conv_channel}')


@socketio.on('leave_conversation_channel')
def handle_leave_conversation(data):
    conversation_id = data.get('conversation_id')
    conv_channel = f"conversation_{conversation_id}"
    leave_room(conv_channel)


@socketio.on('send_private_message')
def handle_send_private_message(data):
    """
    Client sends: { conversation_id, token, content }
    Verifies, saves to DB, then broadcasts to both participants
    (if they're currently connected to this conversation's channel).
    """
    token = data.get('token')
    conversation_id = data.get('conversation_id')
    content = data.get('content', '').strip()

    user = get_user_from_token(token)
    if not user:
        emit('error', {'message': 'Invalid or missing authentication token'})
        return

    if not content:
        emit('error', {'message': 'Message content cannot be empty'})
        return

    conversation = PrivateConversation.query.get(conversation_id)
    if not conversation:
        emit('error', {'message': 'Conversation not found'})
        return

    if user.id not in (conversation.user_one_id, conversation.user_two_id):
        emit('error', {'message': 'You are not part of this conversation'})
        return

    # --- Persist to database ---
    message = Message(sender_id=user.id, conversation_id=conversation_id, content=content)
    db.session.add(message)
    db.session.commit()

    # --- Broadcast to both participants ---
    conv_channel = f"conversation_{conversation_id}"
    emit('new_private_message', message.to_dict(), room=conv_channel)

    other_user_id = conversation.user_two_id if user.id == conversation.user_one_id else conversation.user_one_id
    emit('conversation_notification', {
        'conversation_id': conversation_id,
        'message': message.to_dict()
    }, room=f"user_{other_user_id}")