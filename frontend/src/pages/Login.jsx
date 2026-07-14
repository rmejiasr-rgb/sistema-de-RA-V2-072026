import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [enviando, setEnviando] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setEnviando(true);
    try {
      await login(username, password);
      navigate("/tablero");
    } catch {
      setError("Usuario o contraseña incorrectos.");
    } finally {
      setEnviando(false);
    }
  };

  return (
    <div className="pantalla-centrada">
      <form className="tarjeta formulario-login" onSubmit={handleSubmit}>
        <h1>Sistema RA · UNIMET</h1>
        <p className="subtitulo">Gestión y análisis de Resultados de Aprendizaje</p>

        <label>
          Usuario
          <input value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
        </label>
        <label>
          Contraseña
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>

        {error && <p className="mensaje-error">{error}</p>}

        <button type="submit" disabled={enviando}>
          {enviando ? "Ingresando..." : "Ingresar"}
        </button>

        {import.meta.env.VITE_SSO_ENABLED === "true" && (
          <a
            className="boton-sso"
            href={`${(import.meta.env.VITE_API_URL || "").replace(/\/api$/, "")}/accounts/microsoft/login/`}
          >
            Ingresar con Microsoft (@unimet.edu.ve)
          </a>
        )}
      </form>
    </div>
  );
}
