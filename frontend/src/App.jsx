import { Navigate, Route, Routes, Link, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Carga from "./pages/Carga";
import Dashboard from "./pages/Dashboard";
import CierrePeriodo from "./pages/CierrePeriodo";
import Cargas from "./pages/Cargas";
import Catalogo from "./pages/Catalogo";
import Usuarios from "./pages/Usuarios";
import "./App.css";

function RutaProtegida({ children, rol }) {
  const { usuario, cargando, esCoordinador, esAdministrador } = useAuth();
  if (cargando) return <div className="pantalla-centrada">Cargando…</div>;
  if (!usuario) return <Navigate to="/login" replace />;
  if (rol === "coordinador" && !(esCoordinador || esAdministrador)) {
    return <Navigate to="/tablero" replace />;
  }
  if (rol === "admin" && !esAdministrador) {
    return <Navigate to="/tablero" replace />;
  }
  return children;
}

function Layout({ children }) {
  const { usuario, logout, esCoordinador, esAdministrador } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      <header className="cabecera">
        <div className="marca">Sistema RA · UNIMET</div>
        <nav>
          <Link to="/tablero">Tablero</Link>
          <Link to="/carga">Cargar archivo</Link>
          <Link to="/cargas">Mis cargas</Link>
          {(esCoordinador || esAdministrador) && <Link to="/catalogo">Catálogo</Link>}
          {(esCoordinador || esAdministrador) && <Link to="/cierre">Cierre de periodo</Link>}
          {esAdministrador && <Link to="/usuarios">Usuarios</Link>}
        </nav>
        <div className="usuario-actual">
          <span>{usuario?.first_name || usuario?.username}</span>
          <button onClick={handleLogout}>Salir</button>
        </div>
      </header>
      <main>{children}</main>
    </div>
  );
}

function Protegida({ children, rol }) {
  return (
    <RutaProtegida rol={rol}>
      <Layout>{children}</Layout>
    </RutaProtegida>
  );
}

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/tablero" element={<Protegida><Dashboard /></Protegida>} />
        <Route path="/carga" element={<Protegida><Carga /></Protegida>} />
        <Route path="/cargas" element={<Protegida><Cargas /></Protegida>} />
        <Route path="/catalogo" element={<Protegida rol="coordinador"><Catalogo /></Protegida>} />
        <Route path="/cierre" element={<Protegida rol="coordinador"><CierrePeriodo /></Protegida>} />
        <Route path="/usuarios" element={<Protegida rol="admin"><Usuarios /></Protegida>} />
        <Route path="*" element={<Navigate to="/tablero" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
