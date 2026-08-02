import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getRoomMessages } from '../api/chat';
import { getSocket } from '../socket/socket';

function RoomChat() {
  const { roomId } = useParams();
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const currentUser = JSON.parse(localStorage.getItem('user'));

  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    const socket = getSocket();

    // Load persistent history first
    const loadHistory = async () => {
      try {
        const data = await getRoomMessages(token, roomId);
        setMessages(data.messages);
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load room. You may not be a member.');
      } finally {
        setLoading(false);
      }
    };
    loadHistory();

    // Join the room's live channel
    socket.emit('join_room_channel', { room_id: parseInt(roomId), token });

    const handleNewMessage = (message) => {
      if (message.room_id === parseInt(roomId)) {
        setMessages((prev) => [...prev, message]);
      }
    };

    const handleError = (err) => {
      setError(err.message);
    };

    socket.on('new_room_message', handleNewMessage);
    socket.on('error', handleError);

    // Cleanup: leave the room channel and remove listeners when navigating away
    return () => {
      socket.emit('leave_room_channel', { room_id: parseInt(roomId) });
      socket.off('new_room_message', handleNewMessage);
      socket.off('error', handleError);
    };
  }, [roomId, token]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    const socket = getSocket();
    socket.emit('send_room_message', {
      room_id: parseInt(roomId),
      token,
      content: newMessage.trim(),
    });

    setNewMessage('');
  };

  if (loading) return <p className="loading-text">Loading room...</p>;

  if (error) {
    return (
      <div className="chat-container">
        <p className="error-message">{error}</p>
        <button onClick={() => navigate('/dashboard')}>Back to Dashboard</button>
      </div>
    );
  }

  return (
    <div className="chat-container">
      <div className="chat-header">
        <button className="back-btn" onClick={() => navigate('/dashboard')}>← Back</button>
        <h3>Room Chat</h3>
      </div>

      <div className="messages-list">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message-bubble ${msg.sender_id === currentUser.id ? 'own-message' : ''}`}
          >
            <div className="message-sender">{msg.sender_username}</div>
            <div className="message-content">{msg.content}</div>
            <div className="message-time">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSend} className="message-input-form">
        <input
          type="text"
          value={newMessage}
          onChange={(e) => setNewMessage(e.target.value)}
          placeholder="Type a message..."
          autoFocus
        />
        <button type="submit">Send</button>
      </form>
    </div>
  );
}

export default RoomChat;