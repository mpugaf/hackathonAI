import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';
import * as authApi from '../api/auth';
import ToastHost from '../components/ui/Toast';

const AuthContext = createContext(null);

function decodeToken(token) {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    if (!payload.exp || payload.exp <= Date.now() / 1000) {
      return null;
    }
    return payload;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [toasts, setToasts] = useState([]);

  useEffect(() => {
    const token = sessionStorage.getItem('reqflow_token');
    const savedUser = sessionStorage.getItem('reqflow_user');
    const claims = token ? decodeToken(token) : null;
    if (claims && savedUser) {
      setUser(JSON.parse(savedUser));
    } else {
      sessionStorage.removeItem('reqflow_token');
      sessionStorage.removeItem('reqflow_user');
    }
    setIsLoading(false);
  }, []);

  const showToast = useCallback((message, type = 'info') => {
    const id = crypto.randomUUID();
    setToasts((current) => [...current, { id, message, type }]);
    window.setTimeout(() => {
      setToasts((current) => current.filter((toast) => toast.id !== id));
    }, 4000);
  }, []);

  const login = useCallback(async (email, password) => {
    const data = await authApi.login(email, password);
    sessionStorage.setItem('reqflow_token', data.access_token);
    const claims = decodeToken(data.access_token);
    const nextUser = {
      id: claims?.sub,
      email: claims?.email ?? email,
      role: data.role,
      full_name: data.full_name
    };
    sessionStorage.setItem('reqflow_user', JSON.stringify(nextUser));
    setUser(nextUser);
    return data.role;
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Stateless JWT logout may fail after expiration; local cleanup still applies.
    }
    sessionStorage.removeItem('reqflow_token');
    sessionStorage.removeItem('reqflow_user');
    setUser(null);
  }, []);

  const value = useMemo(() => ({
    user,
    isLoading,
    isAuthenticated: user !== null,
    login,
    logout,
    hasRole: (role) => user?.role === role,
    showToast
  }), [user, isLoading, login, logout, showToast]);

  return (
    <AuthContext.Provider value={value}>
      {children}
      <ToastHost toasts={toasts} />
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe usarse dentro de AuthProvider');
  }
  return context;
}

export function useToast() {
  return useAuth();
}
