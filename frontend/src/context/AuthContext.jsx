import { createContext, useCallback, useContext, useEffect, useState } from "react";
import client, { estaAutenticado, login as apiLogin, logout as apiLogout } from "../api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [usuario, setUsuario] = useState(null);
  const [cargando, setCargando] = useState(true);

  const cargarUsuario = useCallback(async () => {
    if (!estaAutenticado()) {
      setUsuario(null);
      setCargando(false);
      return;
    }
    try {
      const { data } = await client.get("/auth/me/");
      setUsuario(data);
    } catch {
      setUsuario(null);
    } finally {
      setCargando(false);
    }
  }, []);

  useEffect(() => {
    cargarUsuario();
  }, [cargarUsuario]);

  const login = async (username, password) => {
    await apiLogin(username, password);
    await cargarUsuario();
  };

  const logout = () => {
    apiLogout();
    setUsuario(null);
  };

  return (
    <AuthContext.Provider value={{ usuario, cargando, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de AuthProvider");
  return ctx;
}
