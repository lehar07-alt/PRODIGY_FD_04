import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getCurrentUser, listUsers } from '../api/auth';
import { listAllRooms, listMyRooms, createRoom, joinRoom, startConversation, listConversations, getOnlineUsers } from '../api/chat';
import { getSocket } from '../socket/socket';

function Dashboard() {
  const [user, setUser] = useState(null);
  const [allRooms, setAllRooms] = useState([]);
  const [myRooms, setMyRooms] = useState([]);
  const [users, setUsers] = useState([]);
  const [onlineUserIds, setOnlineUserIds] = useState(new Set());
  const [conversations, setConversations] = useState([]);
  const [newRoomName, setNewRoomName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const navigate = useNavigate();
  const token = localStorage.getItem('token');

  const loadDashboardData = async () => {
    try {
      const [userData, allRoomsData, myRoomsData, usersData, onlineData, convData] = await Promise.all([
        getCurrentUser(token),
        listAllRooms(token),
        listMyRooms(token),
        listUsers(token),
        getOnlineUsers(token),
        listConversations(token),
      ]);

      setUser(userData.user);
      setAllRooms(allRoomsData.rooms);
      setMyRooms(myRoomsData.rooms);
      setUsers(usersData.users);
      setOnlineUserIds(new Set(onlineData.online_users.map((u) => u.id)));
      setConversations(convData.conversations);
    } catch (err) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      navigate('/login');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();

    // Listen for live presence updates
    const socket = getSocket();
    const handlePresence = (data) => {
      setOnlineUserIds((prev) => {
        const updated = new Set(prev);
        if (data.is_online) {
          updated.add(data.user_id);
        } else {
          updated.delete(data.user_id);
        }
        return updated;
      });
    };

    socket.on('presence_update', handlePresence);

    return () => {
      socket.off('presence_update', handlePresence);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleCreateRoom = async (e) => {
    e.preventDefault();
    setError('');
    if (!newRoomName.trim()) return;

    try {
      await createRoom(token, newRoomName.trim());
      setNewRoomName('');
      loadDashboardData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create room');
    }
  };

  const handleJoinRoom = async (roomId) => {
    setError('');
    try {
      await joinRoom(token, roomId);
      loadDashboardData();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to join room');
    }
  };

  const handleStartConversation = async (otherUserId) => {
    setError('');
    try {
      const data = await startConversation(token, otherUserId);
      navigate(`/conversations/${data.conversation.id}`);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start conversation');
    }
  };

  const handleLogout = () => {
    const socket = getSocket();
    socket.disconnect();
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  if (loading) return <p className="loading-text">Loading...</p>;

  const myRoomIds = new Set(myRooms.map((r) => r.id));

  return (
    <div className="dashboard-container">
      <div className="dashboard-header">
        <h2>Welcome, {user.username}</h2>
        <button onClick={handleLogout} className="logout-btn">Logout</button>
      </div>

      {error && <p className="error-message">{error}</p>}

      <div className="dashboard-grid">
        {/* My Rooms */}
        <div className="panel">
          <h3>My Rooms</h3>
          {myRooms.length === 0 && <p className="muted">You haven't joined any rooms yet.</p>}
          <ul className="list">
            {myRooms.map((room) => (
              <li key={room.id} className="list-item clickable" onClick={() => navigate(`/rooms/${room.id}`)}>
                # {room.name} <span className="muted">({room.member_count} members)</span>
              </li>
            ))}
          </ul>
        </div>

        {/* All Rooms (discover/join) */}
        <div className="panel">
          <h3>Discover Rooms</h3>
          <form onSubmit={handleCreateRoom} className="inline-form">
            <input
              type="text"
              placeholder="New room name"
              value={newRoomName}
              onChange={(e) => setNewRoomName(e.target.value)}
            />
            <button type="submit">Create</button>
          </form>
          <ul className="list">
            {allRooms.map((room) => (
              <li key={room.id} className="list-item">
                # {room.name} <span className="muted">({room.member_count} members)</span>
                {!myRoomIds.has(room.id) && (
                  <button className="small-btn" onClick={() => handleJoinRoom(room.id)}>Join</button>
                )}
              </li>
            ))}
          </ul>
        </div>

        {/* Users + presence */}
        <div className="panel">
          <h3>Users</h3>
          <ul className="list">
            {users.map((u) => (
              <li key={u.id} className="list-item">
                <span className={`status-dot ${onlineUserIds.has(u.id) ? 'online' : 'offline'}`}></span>
                {u.username}
                <button className="small-btn" onClick={() => handleStartConversation(u.id)}>Message</button>
              </li>
            ))}
          </ul>
        </div>

        {/* Private conversations */}
        <div className="panel">
          <h3>Private Conversations</h3>
          {conversations.length === 0 && <p className="muted">No conversations yet.</p>}
          <ul className="list">
            {conversations.map((conv) => (
              <li key={conv.id} className="list-item clickable" onClick={() => navigate(`/conversations/${conv.id}`)}>
                {conv.other_user?.username}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;