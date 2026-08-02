import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL;

const authHeader = (token) => ({ headers: { Authorization: `Bearer ${token}` } });

// --- Rooms ---
export const createRoom = async (token, name) => {
  const res = await axios.post(`${API_URL}/chat/rooms`, { name }, authHeader(token));
  return res.data;
};

export const listAllRooms = async (token) => {
  const res = await axios.get(`${API_URL}/chat/rooms`, authHeader(token));
  return res.data;
};

export const listMyRooms = async (token) => {
  const res = await axios.get(`${API_URL}/chat/rooms/mine`, authHeader(token));
  return res.data;
};

export const joinRoom = async (token, roomId) => {
  const res = await axios.post(`${API_URL}/chat/rooms/${roomId}/join`, {}, authHeader(token));
  return res.data;
};

export const getRoomMessages = async (token, roomId) => {
  const res = await axios.get(`${API_URL}/chat/rooms/${roomId}/messages`, authHeader(token));
  return res.data;
};

// --- Private conversations ---
export const startConversation = async (token, otherUserId) => {
  const res = await axios.post(`${API_URL}/chat/conversations/start`, { other_user_id: otherUserId }, authHeader(token));
  return res.data;
};

export const listConversations = async (token) => {
  const res = await axios.get(`${API_URL}/chat/conversations`, authHeader(token));
  return res.data;
};

export const getConversationMessages = async (token, conversationId) => {
  const res = await axios.get(`${API_URL}/chat/conversations/${conversationId}/messages`, authHeader(token));
  return res.data;
};

// --- Presence ---
export const getOnlineUsers = async (token) => {
  const res = await axios.get(`${API_URL}/chat/users/online`, authHeader(token));
  return res.data;
};