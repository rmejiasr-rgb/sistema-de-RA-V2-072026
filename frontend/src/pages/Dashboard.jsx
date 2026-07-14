import { useEffect, useMemo, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import client from "../api/client";

const COLOR_SEMAFORO = {
  VERDE: "#1f8a4c",
  AMARILLO: "#c98a12",
  ROJO: "#c0392b",
  SIN_DATOS: "#888888",
};

export default function Dashboard() {
  const [periodos, setPeriodos] = useState([]);
  const [materias, setMaterias] = useState([]);
  const [ras, setRas] = useState([]);

  const [filtros, setFiltros] = useState({ periodo: "", materia: "", ra: "", seccion: "" });
  const [cumplimiento, setCumplimiento] = useState([]);
  const [criterios, setCriterios] = useState([]);
  const [cargando, setCargando] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    client.get("/catalog/periodos/").then((r) => setPeriodos(r.data));
    client.get("/catalog/materias/").then((r) => setMaterias(r.data));
    client.get("/catalog/ras/").then((r) => setRas(r.data));
  }, []);

  const queryParams = useMemo(() => {
    const params = {};
    Object.entries(filtros).forEach(([k, v]) => {
      if (v) params[k] = v;
    });
    return params;
  }, [filtros]);

  useEffect(() => {
    setCargando(true);
    setError("");
    Promise.all([
      client.get("/dashboard/cumplimiento-ra/", { params: queryParams }),
      client.get("/dashboard/criterios/", { params: queryParams }),
    ])
      .then(([r1, r2]) => {
        setCumplimiento(r1.data.resultados);
        setCriterios(r2.data.resultados);
      })
      .catch(() => setError("No fue posible cargar el tablero."))
      .finally(() => setCargando(false));
  }, [queryParams]);

  const datosGrafico = criterios.map((c) => ({
    nombre: c.criterio.length > 30 ? c.criterio.slice(0, 30) + "…" : c.criterio,
    Excelente: c.excelente,
    Satisfactorio: c.satisfactorio,
    Insatisfactorio: c.insatisfactorio,
  }));

  return (
    <div className="contenedor">
      <h2>Tablero analítico</h2>

      <div className="tarjeta filtros">
        <select value={filtros.periodo} onChange={(e) => setFiltros({ ...filtros, periodo: e.target.value })}>
          <option value="">Todos los periodos</option>
          {periodos.map((p) => (
            <option key={p.id} value={p.id}>{p.codigo}</option>
          ))}
        </select>
        <select value={filtros.materia} onChange={(e) => setFiltros({ ...filtros, materia: e.target.value })}>
          <option value="">Todas las materias</option>
          {materias.map((m) => (
            <option key={m.id} value={m.id}>{m.codigo} — {m.nombre}</option>
          ))}
        </select>
        <select value={filtros.ra} onChange={(e) => setFiltros({ ...filtros, ra: e.target.value })}>
          <option value="">Todos los RA</option>
          {ras.map((r) => (
            <option key={r.id} value={r.id}>{r.codigo}</option>
          ))}
        </select>
        <input
          placeholder="Sección"
          value={filtros.seccion}
          onChange={(e) => setFiltros({ ...filtros, seccion: e.target.value })}
        />
      </div>

      {error && <p className="mensaje-error">{error}</p>}
      {cargando && <p>Cargando…</p>}

      <section className="tarjeta">
        <h3>Bloque 1 · Cumplimiento por RA</h3>
        <table className="tabla">
          <thead>
            <tr>
              <th>Materia</th><th>Sección</th><th>Profesor</th><th>RA</th><th>Nivel</th>
              <th>% Declarado</th><th>% Recalculado</th><th>Semáforo</th>
            </tr>
          </thead>
          <tbody>
            {cumplimiento.map((fila) => (
              <tr key={fila.evaluacion_id}>
                <td>{fila.materia}</td>
                <td>{fila.seccion}</td>
                <td>{fila.profesor}</td>
                <td>{fila.ra}</td>
                <td>{fila.nivel}</td>
                <td>{fila.pct_aprobados_declarado}%</td>
                <td>
                  {fila.pct_aprobados_recalculado}%
                  {fila.discrepancia && <span title="Discrepancia con el declarado"> ⚠️</span>}
                </td>
                <td>
                  <span
                    className="punto-semaforo"
                    style={{ backgroundColor: COLOR_SEMAFORO[fila.semaforo] }}
                    title={fila.semaforo}
                  />
                </td>
              </tr>
            ))}
            {cumplimiento.length === 0 && !cargando && (
              <tr><td colSpan={8}>Sin datos para los filtros seleccionados.</td></tr>
            )}
          </tbody>
        </table>
      </section>

      <section className="tarjeta">
        <h3>Bloque 2 · Desagregación por criterio</h3>
        <div style={{ width: "100%", height: 320 }}>
          <ResponsiveContainer>
            <BarChart data={datosGrafico}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="nombre" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={80} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="Excelente" stackId="a" fill="#1f8a4c" />
              <Bar dataKey="Satisfactorio" stackId="a" fill="#c98a12" />
              <Bar dataKey="Insatisfactorio" stackId="a" fill="#c0392b" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <ul className="lista-hallazgos">
          {criterios.filter((c) => c.cero_excelente || c.mayoria_insatisfactorio).map((c) => (
            <li key={c.criterio}>
              <strong>{c.criterio}:</strong>{" "}
              {c.cero_excelente && "sin resultados Excelente. "}
              {c.mayoria_insatisfactorio && "mayoría Insatisfactorio."}
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
