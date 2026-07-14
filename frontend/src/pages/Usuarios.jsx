import { useEffect, useState } from "react";
import client from "../api/client";

const ROLES = ["PROFESOR", "COORDINADOR", "ADMINISTRADOR"];
const VACIO = { username: "", email: "", first_name: "", last_name: "", escuela: "", password: "", roles_input: [] };

export default function Usuarios() {
  const [usuarios, setUsuarios] = useState([]);
  const [escuelas, setEscuelas] = useState([]);
  const [editando, setEditando] = useState(null);

  const cargar = () => client.get("/auth/usuarios/").then((r) => setUsuarios(r.data));

  useEffect(() => {
    cargar();
    client.get("/catalog/escuelas/").then((r) => setEscuelas(r.data));
  }, []);

  return (
    <div className="contenedor">
      <h2>Gestión de usuarios</h2>
      <p className="subtitulo">Alta de usuarios y asignación de roles (Profesor, Coordinador, Administrador).</p>

      <button onClick={() => setEditando({ ...VACIO })}>+ Nuevo usuario</button>

      <section className="tarjeta" style={{ marginTop: 16 }}>
        <table className="tabla">
          <thead><tr><th>Usuario</th><th>Nombre</th><th>Correo</th><th>Escuela</th><th>Roles</th><th></th></tr></thead>
          <tbody>
            {usuarios.map((u) => (
              <tr key={u.id}>
                <td>{u.username}</td>
                <td>{u.first_name} {u.last_name}</td>
                <td>{u.email}</td>
                <td>{u.escuela_codigo || "—"}</td>
                <td>{(u.roles || []).map((r) => r.rol).join(", ") || "—"}</td>
                <td><button className="btn-mini" onClick={() => setEditando({
                  id: u.id, username: u.username, email: u.email, first_name: u.first_name,
                  last_name: u.last_name, escuela: u.escuela || "", password: "",
                  roles_input: (u.roles || []).map((r) => ({ rol: r.rol, escuela: r.escuela })),
                })}>Editar</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {editando && (
        <EditorUsuario
          usuario={editando} escuelas={escuelas}
          onClose={() => setEditando(null)}
          onSaved={() => { setEditando(null); cargar(); }}
        />
      )}
    </div>
  );
}

function EditorUsuario({ usuario, escuelas, onClose, onSaved }) {
  const [form, setForm] = useState(usuario);
  const [error, setError] = useState("");
  const esNuevo = !usuario.id;

  const toggleRol = (rol) => {
    const existe = form.roles_input.find((r) => r.rol === rol);
    if (existe) {
      setForm({ ...form, roles_input: form.roles_input.filter((r) => r.rol !== rol) });
    } else {
      setForm({ ...form, roles_input: [...form.roles_input, { rol, escuela: form.escuela || null }] });
    }
  };

  const guardar = () => {
    setError("");
    const payload = { ...form, escuela: form.escuela || null };
    if (!esNuevo && !payload.password) delete payload.password;
    const req = esNuevo
      ? client.post("/auth/usuarios/", payload)
      : client.patch(`/auth/usuarios/${form.id}/`, payload);
    req.then(onSaved).catch((err) => {
      const data = err.response?.data;
      setError(typeof data === "object" ? JSON.stringify(data) : "No fue posible guardar.");
    });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>{esNuevo ? "Nuevo usuario" : `Editar ${form.username}`}</h3>
        <label>Usuario<input value={form.username} disabled={!esNuevo}
          onChange={(e) => setForm({ ...form, username: e.target.value })} /></label>
        <label>Correo<input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
        <div className="dos-columnas">
          <label>Nombre<input value={form.first_name} onChange={(e) => setForm({ ...form, first_name: e.target.value })} /></label>
          <label>Apellido<input value={form.last_name} onChange={(e) => setForm({ ...form, last_name: e.target.value })} /></label>
        </div>
        <label>Escuela
          <select value={form.escuela} onChange={(e) => setForm({ ...form, escuela: e.target.value })}>
            <option value="">(sin escuela)</option>
            {escuelas.map((es) => <option key={es.id} value={es.id}>{es.codigo} — {es.nombre}</option>)}
          </select>
        </label>
        <label>{esNuevo ? "Contraseña" : "Nueva contraseña (dejar vacío para no cambiar)"}
          <input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} />
        </label>
        <div>
          <strong style={{ fontSize: 13 }}>Roles</strong>
          <div className="filtros" style={{ marginTop: 6 }}>
            {ROLES.map((rol) => (
              <label key={rol} style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                <input type="checkbox" checked={!!form.roles_input.find((r) => r.rol === rol)}
                  onChange={() => toggleRol(rol)} style={{ width: "auto" }} />
                {rol}
              </label>
            ))}
          </div>
        </div>
        {error && <p className="mensaje-error">{error}</p>}
        <div className="modal-acciones">
          <button className="secundario" onClick={onClose}>Cancelar</button>
          <button onClick={guardar}>Guardar</button>
        </div>
      </div>
    </div>
  );
}
