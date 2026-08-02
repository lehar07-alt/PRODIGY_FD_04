import { useEffect } from 'react';
import { Navigate } from 'react-router-dom';
import { getSocket } from '../socket/socket';

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');

  useEffect(() => {
    if (token) {
      const socket = getSocket();
      if (!socket.connected) {
        socket.connect();
        socket.emit('authenticate', { token });
      }
    }
  }, [token]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

export default ProtectedRoute;