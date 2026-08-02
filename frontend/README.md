# Real-Time Chat Application

A full-stack real-time chat application built with WebSockets, supporting group chat rooms and private 1-to-1 conversations with persistent history and live user presence — built for Prodigy InfoTech internship (Task-04).

## Features

- User registration and secure login (JWT-based, bcrypt password hashing)
- Real-time messaging via WebSockets (Flask-SocketIO + Socket.IO client)
- Group chat rooms — create, discover, and join rooms
- Private 1-to-1 conversations between any two users
- Persistent chat history — all messages stored in the database and reloaded on demand
- Live user presence — see who's online/offline in real time, no refresh needed
- Access control — only room members can view/send in a room; only conversation participants can view/send privately

## Tech Stack

**Backend:** Python, Flask, Flask-SocketIO, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-Bcrypt, Eventlet, SQLite
**Frontend:** React (Vite), Socket.IO Client, React Router, Axios

## Project Structure

```
realtime-chat-app/
├── backend/
│   ├── app/
│   │   ├── __init__.py        # App factory, SocketIO setup
│   │   ├── config.py
│   │   ├── models.py          # User, Room, RoomMembership, PrivateConversation, Message
│   │   ├── auth_routes.py     # Register, login, /me, /users
│   │   ├── chat_routes.py     # Rooms + private conversations REST APIs
│   │   └── socket_events.py   # Real-time WebSocket event handlers
│   ├── run.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/                # auth.js, chat.js — REST API wrappers
│   │   ├── socket/socket.js    # Singleton Socket.IO connection
│   │   ├── pages/               # Register, Login, Dashboard, RoomChat, PrivateChat
│   │   ├── components/ProtectedRoute.jsx
│   │   └── App.jsx
│   └── package.json
└── README.md
```

## REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|--------------|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login, receive JWT |
| GET | `/api/auth/me` | Current user's profile |
| GET | `/api/auth/users` | List other registered users |
| POST | `/api/chat/rooms` | Create a room |
| GET | `/api/chat/rooms` | List all rooms |
| GET | `/api/chat/rooms/mine` | List rooms the user has joined |
| POST | `/api/chat/rooms/<id>/join` | Join a room |
| GET | `/api/chat/rooms/<id>/members` | List room members |
| GET | `/api/chat/rooms/<id>/messages` | Room message history |
| POST | `/api/chat/conversations/start` | Start/get a private conversation |
| GET | `/api/chat/conversations` | List user's private conversations |
| GET | `/api/chat/conversations/<id>/messages` | Private message history |
| GET | `/api/chat/users/online` | List currently online users |

## WebSocket Events

| Event | Direction | Purpose |
|-------|-----------|---------|
| `authenticate` | Client → Server | Mark user online after connecting |
| `presence_update` | Server → Client | Broadcast when a user comes online/offline |
| `join_room_channel` | Client → Server | Subscribe to a room's live channel |
| `send_room_message` | Client → Server | Send a message to a room |
| `new_room_message` | Server → Client | Broadcast a new room message |
| `join_conversation_channel` | Client → Server | Subscribe to a private conversation channel |
| `send_private_message` | Client → Server | Send a private message |
| `new_private_message` | Server → Client | Broadcast a new private message |

## Setup Instructions

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Windows
source venv/bin/activate    # Mac/Linux
pip install -r requirements.txt
python run.py
```
Runs on `http://127.0.0.1:5000`

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Runs on `http://localhost:5173`

## Security Notes

- Passwords hashed with bcrypt, never stored in plain text
- JWT tokens verified on every REST request and every WebSocket event (connections aren't trusted just because they're open)
- Room and conversation access enforced server-side — membership is checked before any message can be read or sent, both via REST and WebSocket
- Generic login error messages to prevent username enumeration

## Possible Future Improvements

- Typing indicators
- Read receipts
- Multimedia/file sharing in messages
- Push notifications for new messages while offline
- Message editing/deletion