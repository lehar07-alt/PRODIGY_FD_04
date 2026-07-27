import socketio

sio = socketio.Client()

# --- Paste a fresh token for alice here ---
ALICE_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc4NTE0Mjk1MCwianRpIjoiZWExNTFmZTktMGU2ZC00MTVkLTg0ZjAtZDhmYmIyYTIxMzE1IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3ODUxNDI5NTAsImNzcmYiOiIxYWUyM2JhMS0wZDNiLTQxNjMtYTAyNS1hYTM5ZWE1NDVhN2EiLCJleHAiOjE3ODUxNjQ1NTAsInJvbGUiOiJ1c2VyIiwidXNlcm5hbWUiOiJhbGljZSJ9.SYJYucsTJZEnlg3WT0bbaXysbh6R2naCMoxp68F0WEk"
ROOM_ID = 1  # the room ID you created in Section 5


@sio.event
def connect():
    print("Connected to server!")
    sio.emit('join_room_channel', {'room_id': ROOM_ID, 'token': ALICE_TOKEN})


@sio.event
def joined_room(data):
    print("Joined room event:", data)
    # Send a test message once we've joined
    sio.emit('send_room_message', {
        'room_id': ROOM_ID,
        'token': ALICE_TOKEN,
        'content': 'Hello from alice via WebSocket!'
    })


@sio.event
def new_room_message(data):
    print("New message received:", data)


@sio.event
def error(data):
    print("Error:", data)


sio.connect('http://127.0.0.1:5000')
sio.wait()