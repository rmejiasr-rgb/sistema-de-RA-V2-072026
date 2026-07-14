import { useEffect, useState } from "react";
import client from "../api/client";

export default function Cargas() {
  const [evaluaciones, setEvaluaciones] = useState([]);
  const [cargando, setCargando] = useState(true);
  const [editando, setEditando] = useState(null);
  const [auditoria, setAuditoria] = useState(null);

  const cargar = () => {
    setCargando(true);
    client.get("/uploads/evaluaciones/", { params: { page_size: 100 } })
      .then((r) => setEvaluaciones(r.data.results || r.data))
      .finally(() => setCargando(false));
  };

  useEffect(cargar, []);

  const verAuditoria = (ev) => {
    setAuditoria({ ev, registros: null });
    client.get("/uploads/auditoria/", { params: { entidad: "Evaluacion", entidad_id: ev.id } })
      .then((r) => setAuditoria({ ev, registros: r.data.results || r.data }));
  };

  return (
    <div className="contenedor">
      <h2>Mis cargas</h2>
      <p className="subtitulo">
        Cargas vigentes visibles según su rol. Puede corregir metadatos (actividad, fecha,
        profesor, sección) con auditoría. Las notas se corrigen solo re-subiendo el archivo.
      </p>

      {cargando && <p>Cargando…</p>}

      <table className="tabla">
        <thead>
          <tr><th>Periodo</th><th>Materia</th><th>Sección</th><th>RA</th><th>Actividad</th>
            <th>Fecha</th><th>Versión</th><th>Acciones</th></tr>
        </thead>
        <tbody>
          {evaluaciones.map((ev) => (
            <tr key={ev.id}>
              <td>{ev.periodo_codigo}</td>
              <td>{ev.materia_codigo}</td>
              <td>{ev.seccion}</td>
              <td>{ev.ra_codigo}</td>
              <td>{ev.actividad}</td>
              <td>{ev.fecha_actividad}</td>
              <td>v{ev.version}</td>
              <td>
                <button className="btn-mini" onClick={() => setEditando(ev)}>Editar</button>{" "}
                <button className="btn-mini secundario" onClick={() => verAuditoria(ev)}>Auditoría</button>
              </td>
            </tr>
          ))}
          {!cargando && evaluaciones.length === 0 && (
            <tr><td colSpan={8}>No hay cargas visibles.</td></tr>
          )}
        </tbody>
      </table>

      {editando && (
        <EditarMetadatos
          evaluacion={editando}
          onClose={() => setEditando(null)}
          onSaved={() => { setEditando(null); cargar(); }}
        />
      )}

      {auditoria && (
        <ModalAuditoria data={auditoria} onClose={() => setAuditoria(null)} />
      )}
    </div>
  );
}

function EditarMetadatos({ evaluacion, onClose, onSaved }) {
  const [form, setForm] = useState({
    actividad: evaluacion.actividad,
    fecha_actividad: evaluacion.fecha_actividad,
    profesor_nombre: evaluacion.profesor_nombre,
    seccion: evaluacion.seccion,
    motivo: "",
  });
  const [error, setError] = useState("");
  const [guardando, setGuardando] = useState(false);

  const guardar = () => {
    if (!form.motivo.trim()) { setError("El motivo es obligatorio para auditar el cambio."); return; }
    setGuardando(true);
    setError("");
    client.patch(`/uploads/evaluaciones/${evaluacion.id}/metadatos/`, form)
      .then(onSaved)
      .catch((err) => setError(err.response?.data?.detail || "No fue posible guardar."))
      .finally(() => setGuardando(false));
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Editar metadatos · {evaluacion.materia_codigo} / {evaluacion.ra_codigo}</h3>
        <label>Actividad
          <input value={form.actividad} onChange={(e) => setForm({ ...form, actividad: e.target.value })} />
        </label>
        <label>Fecha de la actividad
          <input type="date" value={form.fecha_actividad} onChange={(e) => setForm({ ...form, fecha_actividad: e.target.value })} />
        </label>
        <label>Profesor
          <input value={form.profesor_nombre} onChange={(e) => setForm({ ...form, profesor_nombre: e.target.value })} />
        </label>
        <label>Sección
          <input value={form.seccion} onChange={(e) => setForm({ ...form, seccion: e.target.value })} />
        </label>
        <label>Motivo del cambio (auditado)
          <input value={form.motivo} onChange={(e) => setForm({ ...form, motivo: e.target.value })} placeholder="Ej. corrección de nombre mal escrito" />
        </label>
        {error && <p className="mensaje-error">{error}</p>}
        <div className="modal-acciones">
          <button className="secundario" onClick={onClose}>Cancelar</button>
          <button onClick={guardar} disabled={guardando}>{guardando ? "Guardando…" : "Guardar"}</button>
        </div>
      </div>
    </div>
  );
}

function ModalAuditoria({ data, onClose }) {
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Auditoría · {data.ev.materia_codigo} / {data.ev.ra_codigo}</h3>
        {!data.registros && <p>Cargando…</p>}
        {data.registros && data.registros.length === 0 && <p>Sin cambios registrados.</p>}
        {data.registros && data.registros.length > 0 && (
          <table className="tabla">
            <thead><tr><th>Fecha</th><th>Usuario</th><th>Campo</th><th>Antes</th><th>Después</th><th>Motivo</th></tr></thead>
            <tbody>
              {data.registros.map((r) => (
                <tr key={r.id}>
                  <td>{new Date(r.timestamp).toLocaleString("es-VE")}</td>
                  <td>{r.usuario_nombre || r.usuario}</td>
                  <td>{r.campo}</td>
                  <td>{r.valor_anterior}</td>
                  <td>{r.valor_nuevo}</td>
                  <td>{r.motivo}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <div className="modal-acciones">
          <button onClick={onClose}>Cerrar</button>
        </div>
      </div>
    </div>
  );
}
