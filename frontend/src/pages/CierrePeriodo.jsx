import { useEffect, useState } from "react";
import client from "../api/client";

export default function CierrePeriodo() {
  const [periodos, setPeriodos] = useState([]);
  const [periodoId, setPeriodoId] = useState("");
  const [resumen, setResumen] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [mensaje, setMensaje] = useState(null);

  useEffect(() => {
    client.get("/catalog/periodos/").then((r) => setPeriodos(r.data));
  }, []);

  const cargarCompletitud = (id) => {
    setPeriodoId(id);
    setResumen(null);
    setMensaje(null);
    if (!id) return;
    setCargando(true);
    client.get(`/catalog/periodos/${id}/completitud/`)
      .then((r) => setResumen(r.data))
      .catch(() => setMensaje({ tipo: "error", texto: "No fue posible cargar la completitud." }))
      .finally(() => setCargando(false));
  };

  const cerrar = () => {
    setMensaje(null);
    client.post(`/catalog/periodos/${periodoId}/cerrar/`)
      .then((r) => {
        setMensaje({ tipo: "ok", texto: r.data.detail });
        cargarCompletitud(periodoId);
        client.get("/catalog/periodos/").then((res) => setPeriodos(res.data));
      })
      .catch((err) => {
        const data = err.response?.data;
        if (err.response?.status === 409) {
          setMensaje({ tipo: "error", texto: `${data.detail} (${data.n_incompletas} incompletas)` });
          setResumen((prev) => prev && { ...prev, incompletas: data.incompletas });
        } else {
          setMensaje({ tipo: "error", texto: data?.detail || "No fue posible cerrar el periodo." });
        }
      });
  };

  return (
    <div className="contenedor">
      <h2>Cobertura y cierre de periodo</h2>
      <p className="subtitulo">
        El cierre de periodo lista las combinaciones materia/sección incompletas y no permite
        cerrar mientras existan RAs faltantes.
      </p>

      <div className="tarjeta filtros">
        <select value={periodoId} onChange={(e) => cargarCompletitud(e.target.value)}>
          <option value="">Seleccione un periodo…</option>
          {periodos.map((p) => (
            <option key={p.id} value={p.id}>{p.codigo} ({p.estado})</option>
          ))}
        </select>
      </div>

      {mensaje && (
        <p className={mensaje.tipo === "ok" ? "mensaje-ok" : "mensaje-error"}>{mensaje.texto}</p>
      )}
      {cargando && <p>Cargando…</p>}

      {resumen && (
        <>
          <div className="tarjeta">
            <div className="kpi-row">
              <div className="kpi"><span className="kpi-num">{resumen.pct_completitud}%</span>Completitud</div>
              <div className="kpi"><span className="kpi-num">{resumen.n_completas}</span>Completas</div>
              <div className="kpi"><span className="kpi-num">{resumen.n_incompletas}</span>Incompletas</div>
            </div>
            {resumen.estado === "CERRADO" ? (
              <p className="mensaje-ok">Este periodo ya está cerrado.</p>
            ) : (
              <button onClick={cerrar} disabled={!resumen.puede_cerrarse}>
                {resumen.puede_cerrarse ? "Cerrar periodo" : "No se puede cerrar (hay incompletas)"}
              </button>
            )}
          </div>

          {resumen.incompletas?.length > 0 && (
            <section className="tarjeta">
              <h3>Combinaciones incompletas</h3>
              <table className="tabla">
                <thead><tr><th>Materia</th><th>Sección</th><th>Profesor</th>
                  <th>Cargados/Esperados</th><th>Faltantes</th></tr></thead>
                <tbody>
                  {resumen.incompletas.map((d, i) => (
                    <tr key={i}>
                      <td>{d.materia}</td><td>{d.seccion}</td><td>{d.profesor}</td>
                      <td>{d.cargados}/{d.esperados}</td>
                      <td>{d.faltantes.join(", ")}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}
        </>
      )}
    </div>
  );
}
