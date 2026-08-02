import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getConversationMessages, listConversations } from '../api/chat';
import { getSocket } from '../socket/socket';

function PrivateChat() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}');

  const [messages, setMessages] = useState([]);
  const [otherUsername, setOtherUsername] = useState('');
  const [newMessage, setNewMessage] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    const socket = getSocket();

    const loadData = async () => {
      try {
        const [msgData, convData] = await Promise.all([
          getConversationMessages(token, conversationId),
          listConversations(token),
        ]);
        setMessages(msgData.messages);

        const thisConv = convData.conversations.find((c) => c.id === parseInt(conversationId));
        setOtherUsername(thisConv?.other_user?.username || 'Unknown');
      } catch (err) {
        setError(err.response?.data?.error || 'Failed to load conversation.');
      } finally {
        setLoading(false);
      }
    };
    loadData();

    socket.emit('join_conversation_channel', { conversation_id: parseInt(conversationId), token });

    const handleNewMessage = (message) => {
      if (message.conversation_id === parseInt(conversationId)) {
        setMessages((prev) => [...prev, message]);
      }
    };

    const handleError = (err) => {
      setError(err.message);
    };

    socket.on('new_private_message', handleNewMessage);
    socket.on('error', handleError);

    return () => {
      socket.emit('leave_conversation_channel', { conversation_id: parseInt(conversationId) });
      socket.off('new_private_message', handleNewMessage);
      socket.off('error', handleError);
    };
  }, [conversationId, token]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;

    const socket = getSocket();
    socket.emit('send_private_message', {
      conversation_id: parseInt(conversationId),
      token,
      content: newMessage.trim(),
    });

    setNewMessage('');
  };

  if (loading) return <p className="loading-text">Loading conversation...</p>;

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
        <h3>{otherUsername}</h3>
      </div>

      <div className="messages-list">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`message-bubble ${msg.sender_id === currentUser.id ? 'own-message' : ''}`}
          >
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

export default PrivateChat;