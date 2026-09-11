import { createContext, useContext, useState, useEffect } from "react";
import api from "../api/axios";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem("token"));
  const [user, setUser] = useState(null);

  useEffect(() => {
    // Optional: decode token to extract user info if needed
    // For now we simply keep the token
  }, [token]);

  const login = async (email, password) => {
    const response = await api.post("/auth/login", { email, password });
    const accessToken = response.data.access_token;
    setToken(accessToken);
    localStorage.setItem("token", accessToken);
    return accessToken;
  };

  const signup = async (email, password, name, branch, cgpa) => {
    const response = await api.post("/auth/signup", {
      email,
      password,
      name,
      branch,
      cgpa,
    });
    const accessToken = response.data.access_token;
    setToken(accessToken);
    localStorage.setItem("token", accessToken);
    return accessToken;
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("token");
  };

  // Attach token to each request via interceptor
  useEffect(() => {
    const interceptor = api.interceptors.request.use((config) => {
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
    return () => {
      api.interceptors.request.eject(interceptor);
    };
  }, [token]);

  return (
    <AuthContext.Provider value={{ token, user, login, signup, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
