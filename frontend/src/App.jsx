import { Navigate, Route, Routes, Link, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Carga from "./pages/Carga";
import Dashboard from "./pages/Dashboard";
import "./App.css";

function RutaProtegida({ children }) {
  const { usuario, cargando } = useAuth();
  if (cargando) return <div className="pantalla-centrada">Cargando…</div>;
  if (!usuario) return <Navigate to="/login" replace />;
  return children;
}

function Layout({ children }) {
  const { usuario, logout } = useAuth();
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

function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/tablero"
          element={
            <RutaProtegida>
              <Layout>
                <Dashboard />
              </Layout>
            </RutaProtegida>
          }
        />
        <Route
          path="/carga"
          element={
            <RutaProtegida>
              <Layout>
                <Carga />
              </Layout>
            </RutaProtegida>
          }
        />
        <Route path="*" element={<Navigate to="/tablero" replace />} />
      </Routes>
    </AuthProvider>
  );
}

export default App;
