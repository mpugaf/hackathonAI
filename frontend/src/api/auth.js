import api from './axios';

export async function login(email, password) {
  const response = await api.post('/auth/login', { email, password });
  return response.data;
}

export async function logout() {
  const response = await api.post('/auth/logout');
  return response.data;
}
