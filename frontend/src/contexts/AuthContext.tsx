import React, { createContext, useState, useEffect, useContext, ReactNode } from 'react';
import { jwtDecode } from 'jwt-decode';
import { login as apiLogin, register as apiRegister, User } from '../services/api';

// --- TYPESCRIPT INTERFACES ---

interface AuthContextType {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

interface AuthProviderProps {
  children: ReactNode;
}

interface DecodedToken {
  sub: string;
  exp: number;
}

// --- AUTH CONTEXT ---

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// --- AUTH PROVIDER ---

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('authToken'));
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const initializeAuth = () => {
      if (token) {
        try {
          const decodedToken = jwtDecode<DecodedToken>(token);
          const currentTime = Date.now() / 1000;

          if (decodedToken.exp > currentTime) {
            // Token is valid
            setUser({
              id: 1,
              email: decodedToken.sub,
              role: 'user'
            });
          } else {
            // Token is expired
            localStorage.removeItem('authToken');
            setToken(null);
            setUser(null);
          }
        } catch (e) {
          console.error('Invalid token', e);
          localStorage.removeItem('authToken');
          setToken(null);
          setUser(null);
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, [token]);

  const login = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiLogin(email, password);
      const decoded = jwtDecode<{ sub: string; exp: number }>(data.access_token);

      localStorage.setItem('authToken', data.access_token);
      setToken(data.access_token);
      setUser({
        id: 1,
        email: decoded.sub,
        role: 'user'
      });
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Login failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      await apiRegister(email, password);
      // After successful registration, log the user in
      await login(email, password);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to register';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('authToken');
  };

  const contextValue: AuthContextType = {
    user,
    token,
    isAuthenticated: !!token,
    loading,
    error,
    login,
    register,
    logout,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// --- HOOK FOR USING AUTH ---

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
