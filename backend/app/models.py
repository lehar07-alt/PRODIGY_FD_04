from app import db
from datetime import datetime

# --- Association table: which users belong to which rooms ---
class RoomMembership(db.Model):
    __tablename__ = 'room_memberships'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'room_id', name='unique_membership'),)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_online": self.is_online,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat()
        }

    def __repr__(self):
        return f"<User {self.username}>"


class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship('User', foreign_keys=[created_by])
    members = db.relationship('RoomMembership', backref='room', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "member_count": len(self.members)
        }

    def __repr__(self):
        return f"<Room {self.name}>"


class PrivateConversation(db.Model):
    __tablename__ = 'private_conversations'

    id = db.Column(db.Integer, primary_key=True)
    user_one_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_two_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_one = db.relationship('User', foreign_keys=[user_one_id])
    user_two = db.relationship('User', foreign_keys=[user_two_id])

    __table_args__ = (db.UniqueConstraint('user_one_id', 'user_two_id', name='unique_conversation'),)

    def to_dict(self, current_user_id=None):
        # Show the "other" user's info, useful for a conversation list UI
        other_user = self.user_two if self.user_one_id == current_user_id else self.user_one
        return {
            "id": self.id,
            "other_user": other_user.to_dict() if other_user else None,
            "created_at": self.created_at.isoformat()
        }

    def __repr__(self):
        return f"<PrivateConversation {self.user_one_id}-{self.user_two_id}>"


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # A message belongs to EITHER a room OR a private conversation, never both
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('private_conversations.id'), nullable=True)

    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id])

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender_username": self.sender.username if self.sender else None,
            "room_id": self.room_id,
            "conversation_id": self.conversation_id,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }

    def __repr__(self):
        return f"<Message {self.id} from {self.sender_id}>"