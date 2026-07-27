import socketio

sio = socketio.Client()

ALICE_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc4NTE2Njk5OCwianRpIjoiYmZkZWU2N2EtZDUxMi00NjBhLThmMGUtMjgzYTg0MWEzMTlkIiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3ODUxNjY5OTgsImNzcmYiOiI1MTkxMTRlNi00NjVkLTQwNGMtODU0MS1hZWJmZjllMjk0Y2MiLCJleHAiOjE3ODUxODg1OTgsInJvbGUiOiJ1c2VyIiwidXNlcm5hbWUiOiJhbGljZSJ9.pWd1qhIQaiy3onTQfagsvVk2MsRlYjZWYl2SLm6225k"
CONVERSATION_ID = 1  # the conversation ID from Section 6


@sio.event
def connect():
    print("Connected to server!")
    sio.emit('join_conversation_channel', {'conversation_id': CONVERSATION_ID, 'token': ALICE_TOKEN})


@sio.event
def joined_conversation(data):
    print("Joined conversation event:", data)
    sio.emit('send_private_message', {
        'conversation_id': CONVERSATION_ID,
        'token': ALICE_TOKEN,
        'content': 'Hey bob, this is a private message!'
    })


@sio.event
def new_private_message(data):
    print("New private message received:", data)


@sio.event
def error(data):
    print("Error:", data)


sio.connect('http://127.0.0.1:5000')
sio.wait()