import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext(null);

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [driver, setDriver] = useState(null);
  const [admin, setAdmin] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      if (token) {
        try {
          const response = await axios.get(`${API}/auth/me`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (response.data.user) setUser(response.data.user);
          if (response.data.driver) setDriver(response.data.driver);
          if (response.data.admin) setAdmin(response.data.admin);
        } catch (error) {
          console.error('Auth init error:', error);
          localStorage.removeItem('token');
          setToken(null);
        }
      }
      setLoading(false);
    };
    initAuth();
  }, [token]);

  const login = async (email, password) => {
    const response = await axios.post(`${API}/auth/login`, { email, password });
    const { token: newToken, user: userData, driver: driverData, admin: adminData } = response.data;
    
    localStorage.setItem('token', newToken);
    setToken(newToken);
    
    if (userData) setUser(userData);
    if (driverData) setDriver(driverData);
    if (adminData) setAdmin(adminData);
    
    return response.data;
  };

  const registerUser = async (data) => {
    const response = await axios.post(`${API}/auth/register/user`, data);
    const { token: newToken, user: userData } = response.data;
    
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setUser(userData);
    
    return response.data;
  };

  const registerDriver = async (data) => {
    const response = await axios.post(`${API}/auth/register/driver`, data);
    const { token: newToken, driver: driverData } = response.data;
    
    localStorage.setItem('token', newToken);
    setToken(newToken);
    setDriver(driverData);
    
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setDriver(null);
    setAdmin(null);
  };

  const refreshUser = async () => {
    if (token) {
      try {
        const response = await axios.get(`${API}/auth/me`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.data.user) setUser(response.data.user);
        if (response.data.driver) setDriver(response.data.driver);
        if (response.data.admin) setAdmin(response.data.admin);
      } catch (error) {
        console.error('Refresh user error:', error);
      }
    }
  };

  const value = {
    user,
    driver,
    admin,
    token,
    loading,
    login,
    registerUser,
    registerDriver,
    logout,
    refreshUser,
    isAuthenticated: !!token,
    role: admin ? 'admin' : driver ? 'driver' : user ? 'user' : null
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
