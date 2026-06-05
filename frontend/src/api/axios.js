import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? '/api',
  timeout: 35000
});

api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('reqflow_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    if (status === 401) {
      sessionStorage.removeItem('reqflow_token');
      sessionStorage.removeItem('reqflow_user');
      if (window.location.pathname !== '/login') {
        window.location = '/login';
      }
    }
    if (status === 502 || status === 504) {
      return Promise.reject(new Error('La IA no respondio. Intenta nuevamente.'));
    }
    return Promise.reject(new Error(error.response?.data?.detail ?? 'Error inesperado'));
  }
);

export default api;
