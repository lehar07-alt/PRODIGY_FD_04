from flask_socketio import join_room, leave_room, emit
from flask_jwt_extended import decode_token
from app import socketio, db
from app.models import User, Message, RoomMembership

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


@socketio.on('connect')
def handle_connect():
    print('A client connected (awaiting authentication)')


@socketio.on('disconnect')
def handle_disconnect():
    from flask import request
    sid = request.sid

    user_id = connected_users.pop(sid, None)
    if user_id:
        print(f'User {user_id} disconnected')


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