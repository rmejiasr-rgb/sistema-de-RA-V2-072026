import { useEffect, useMemo, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import client from "../api/client";
import { descargarArchivo } from "../api/descargas";
import Heatmap from "../components/Heatmap";

const COLOR_SEMAFORO = {
  VERDE: "#1f8a4c", AMARILLO: "#c98a12", ROJO: "#c0392b", SIN_DATOS: "#888888",
};

const BLOQUES = [
  { id: "cumplimiento", label: "1 · Cumplimiento por RA" },
  { id: "criterios", label: "2 · Desagregación por criterio" },
  { id: "heatmaps", label: "3 · Mapas de calor" },
  { id: "carrera", label: "4 · Carrera y grupo" },
  { id: "tendencias", label: "5 · Tendencias" },
  { id: "cobertura", label: "6 · Cobertura y completitud" },
  { id: "riesgo", label: "7 · Riesgo de acreditación" },
  { id: "proxy", label: "Proxy consistencia" },
];

export default function Dashboard() {
  const [periodos, setPeriodos] = useState([]);
  const [materias, setMaterias] = useState([]);
  const [ras, setRas] = useState([]);
  const [escuelas, setEscuelas] = useState([]);

  const [filtros, setFiltros] = useState({ periodo: "", escuela: "", materia: "", ra: "", seccion: "" });
  const [bloque, setBloque] = useState("cumplimiento");

  useEffect(() => {
    client.get("/catalog/periodos/").then((r) => setPeriodos(r.data));
    client.get("/catalog/materias/").then((r) => setMaterias(r.data));
    client.get("/catalog/ras/").then((r) => setRas(r.data));
    client.get("/catalog/escuelas/").then((r) => setEscuelas(r.data));
  }, []);

  const params = useMemo(() => {
    const p = {};
    Object.entries(filtros).forEach(([k, v]) => { if (v) p[k] = v; });
    return p;
  }, [filtros]);

  const [exportando, setExportando] = useState("");
  const exportar = async (formato) => {
    setExportando(formato);
    try {
      await descargarArchivo(
        `/dashboard/export/${formato}/`, params,
        formato === "excel" ? "reporte_ra.xlsx" : "reporte_ra.pdf"
      );
    } finally {
      setExportando("");
    }
  };

  return (
    <div className="contenedor">
      <div className="titulo-con-acciones">
        <h2>Tablero analítico</h2>
        <div className="acciones-export">
          <button className="secundario" onClick={() => exportar("excel")} disabled={!!exportando}>
            {exportando === "excel" ? "Generando…" : "Exportar Excel"}
          </button>
          <button className="secundario" onClick={() => exportar("pdf")} disabled={!!exportando}>
            {exportando === "pdf" ? "Generando…" : "Exportar PDF"}
          </button>
        </div>
      </div>

      <div className="tarjeta filtros">
        <select value={filtros.periodo} onChange={(e) => setFiltros({ ...filtros, periodo: e.target.value })}>
          <option value="">Todos los periodos</option>
          {periodos.map((p) => <option key={p.id} value={p.id}>{p.codigo}</option>)}
        </select>
        <select value={filtros.escuela} onChange={(e) => setFiltros({ ...filtros, escuela: e.target.value })}>
          <option value="">Todas las escuelas</option>
          {escuelas.map((e) => <option key={e.id} value={e.id}>{e.codigo} — {e.nombre}</option>)}
        </select>
        <select value={filtros.materia} onChange={(e) => setFiltros({ ...filtros, materia: e.target.value })}>
          <option value="">Todas las materias</option>
          {materias.map((m) => <option key={m.id} value={m.id}>{m.codigo}</option>)}
        </select>
        <select value={filtros.ra} onChange={(e) => setFiltros({ ...filtros, ra: e.target.value })}>
          <option value="">Todos los RA</option>
          {ras.map((r) => <option key={r.id} value={r.id}>{r.codigo}</option>)}
        </select>
        <input placeholder="Sección" value={filtros.seccion}
          onChange={(e) => setFiltros({ ...filtros, seccion: e.target.value })} />
      </div>

      <div className="tabs">
        {BLOQUES.map((b) => (
          <button key={b.id} className={`tab ${bloque === b.id ? "activa" : ""}`}
            onClick={() => setBloque(b.id)}>{b.label}</button>
        ))}
      </div>

      {bloque === "cumplimiento" && <BloqueCumplimiento params={params} />}
      {bloque === "criterios" && <BloqueCriterios params={params} />}
      {bloque === "heatmaps" && <BloqueHeatmaps params={params} />}
      {bloque === "carrera" && <BloqueCarreraGrupo params={params} />}
      {bloque === "tendencias" && <BloqueTendencias params={params} />}
      {bloque === "cobertura" && <BloqueCobertura params={params} />}
      {bloque === "riesgo" && <BloqueRiesgo params={params} />}
      {bloque === "proxy" && <BloqueProxy params={params} />}
    </div>
  );
}

function useEndpoint(url, params) {
  const [data, setData] = useState(null);
  const [cargando, setCargando] = useState(true);
  const [error, setError] = useState("");
  const key = JSON.stringify(params);
  useEffect(() => {
    setCargando(true);
    setError("");
    client.get(url, { params })
      .then((r) => setData(r.data))
      .catch(() => setError("No fue posible cargar este bloque."))
      .finally(() => setCargando(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, key]);
  return { data, cargando, error };
}

function EstadoCarga({ cargando, error }) {
  if (error) return <p className="mensaje-error">{error}</p>;
  if (cargando) return <p>Cargando…</p>;
  return null;
}

function BloqueCumplimiento({ params }) {
  const { data, cargando, error } = useEndpoint("/dashboard/cumplimiento-ra/", params);
  return (
    <section className="tarjeta">
      <h3>Bloque 1 · Cumplimiento por RA</h3>
      <EstadoCarga cargando={cargando} error={error} />
      {data && (
        <table className="tabla">
          <thead>
            <tr><th>Materia</th><th>Sección</th><th>Profesor</th><th>RA</th><th>Nivel</th>
              <th>% Declarado</th><th>% Recalculado</th><th>Semáforo</th></tr>
          </thead>
          <tbody>
            {data.resultados.map((f) => (
              <tr key={f.evaluacion_id}>
                <td>{f.materia}</td><td>{f.seccion}</td><td>{f.profesor}</td>
                <td>{f.ra}</td><td>{f.nivel}</td>
                <td>{f.pct_aprobados_declarado}%</td>
                <td>{f.pct_aprobados_recalculado}%{f.discrepancia && <span title="Discrepancia"> ⚠️</span>}</td>
                <td><span className="punto-semaforo" style={{ backgroundColor: COLOR_SEMAFORO[f.semaforo] }} title={f.semaforo} /></td>
              </tr>
            ))}
            {data.resultados.length === 0 && <tr><td colSpan={8}>Sin datos.</td></tr>}
          </tbody>
        </table>
      )}
    </section>
  );
}

function BloqueCriterios({ params }) {
  const { data, cargando, error } = useEndpoint("/dashboard/criterios/", params);
  const grafico = (data?.resultados || []).map((c) => ({
    nombre: c.criterio.length > 26 ? c.criterio.slice(0, 26) + "…" : c.criterio,
    Excelente: c.excelente, Satisfactorio: c.satisfactorio, Insatisfactorio: c.insatisfactorio,
  }));
  return (
    <section className="tarjeta">
      <h3>Bloque 2 · Desagregación por criterio</h3>
      <EstadoCarga cargando={cargando} error={error} />
      {data && (
        <>
          <div style={{ width: "100%", height: 340 }}>
            <ResponsiveContainer>
              <BarChart data={grafico}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="nombre" tick={{ fontSize: 11 }} interval={0} angle={-15} textAnchor="end" height={90} />
                <YAxis /><Tooltip /><Legend />
                <Bar dataKey="Excelente" stackId="a" fill="#1f8a4c" />
                <Bar dataKey="Satisfactorio" stackId="a" fill="#c98a12" />
                <Bar dataKey="Insatisfactorio" stackId="a" fill="#c0392b" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <ul className="lista-hallazgos">
            {data.resultados.filter((c) => c.cero_excelente || c.mayoria_insatisfactorio).map((c) => (
              <li key={c.criterio}><strong>{c.criterio}:</strong>{" "}
                {c.cero_excelente && "sin resultados Excelente. "}
                {c.mayoria_insatisfactorio && "mayoría Insatisfactorio."}</li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}

function BloqueHeatmaps({ params }) {
  const mr = useEndpoint("/dashboard/heatmap-materia-ra/", params);
  const cs = useEndpoint("/dashboard/heatmap-criterio-seccion/", params);
  return (
    <>
      <section className="tarjeta">
        <h3>Bloque 3a · Mapa de calor: Materia × RA (% aprobados)</h3>
        <EstadoCarga cargando={mr.cargando} error={mr.error} />
        {mr.data && <Heatmap filas={mr.data.materias} columnas={mr.data.ras}
          celdas={mr.data.celdas} claveFila="materia" claveCol="ra" />}
      </section>
      <section className="tarjeta">
        <h3>Bloque 3b · Mapa de calor: Criterio × Sección (% aprobados)</h3>
        <EstadoCarga cargando={cs.cargando} error={cs.error} />
        {cs.data && <Heatmap filas={cs.data.criterios} columnas={cs.data.secciones}
          celdas={cs.data.celdas} claveFila="criterio" claveCol="seccion" />}
      </section>
    </>
  );
}

function BloqueCarreraGrupo({ params }) {
  const { data, cargando, error } = useEndpoint("/dashboard/carrera-grupo/", params);
  return (
    <section className="tarjeta">
      <h3>Bloque 4 · Desglose por carrera y por grupo</h3>
      <EstadoCarga cargando={cargando} error={error} />
      {data && (
        <div className="dos-columnas">
          <div>
            <h4>Por carrera (nota promedio)</h4>
            <table className="tabla">
              <thead><tr><th>Carrera</th><th>Promedio</th><th>n</th></tr></thead>
              <tbody>{data.por_carrera.map((c) => (
                <tr key={c.carrera}><td>{c.carrera}</td><td>{c.promedio}%</td><td>{c.n}</td></tr>
              ))}</tbody>
            </table>
          </div>
          <div>
            <h4>Por grupo (nota promedio)</h4>
            <table className="tabla">
              <thead><tr><th>Grupo</th><th>Promedio</th><th>n</th></tr></thead>
              <tbody>{data.por_grupo.map((g) => (
                <tr key={g.grupo}><td>{g.grupo}</td><td>{g.promedio}%</td><td>{g.n}</td></tr>
              ))}</tbody>
            </table>
          </div>
        </div>
      )}
      {data?.grupos_extremos?.length > 0 && (
        <ul className="lista-hallazgos">
          {data.grupos_extremos.map((g) => (
            <li key={g.grupo}>Grupo {g.grupo}: desempeño {g.tipo} ({g.promedio}%)</li>
          ))}
        </ul>
      )}
    </section>
  );
}

function BloqueTendencias({ params }) {
  const { data, cargando, error } = useEndpoint("/dashboard/tendencias/", params);
  const grafico = useMemo(() => {
    if (!data) return [];
    return data.periodos.map((p) => {
      const punto = { periodo: p };
      data.por_ra.forEach((serie) => {
        const pt = serie.puntos.find((x) => x.periodo === p);
        punto[serie.nombre] = pt?.pct ?? null;
      });
      return punto;
    });
  }, [data]);
  const colores = ["#003876", "#f37021", "#1f8a4c", "#c0392b", "#8e44ad", "#16a085", "#c98a12", "#2c3e50"];
  return (
    <section className="tarjeta">
      <h3>Bloque 5 · Tendencias históricas (% aprobados por RA)</h3>
      <EstadoCarga cargando={cargando} error={error} />
      {data && (
        <div style={{ width: "100%", height: 380 }}>
          <ResponsiveContainer>
            <LineChart data={grafico}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="periodo" /><YAxis domain={[0, 100]} /><Tooltip /><Legend />
              {data.por_ra.slice(0, 8).map((serie, i) => (
                <Line key={serie.nombre} dataKey={serie.nombre} stroke={colores[i % colores.length]} connectNulls />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}

function BloqueCobertura({ params }) {
  const { data, cargando, error } = useEndpoint("/dashboard/cobertura/", params);
  return (
    <section className="tarjeta">
      <h3>Bloque 6 · Cobertura y completitud</h3>
      <EstadoCarga cargando={cargando} error={error} />
      {data && (
        <>
          <p className="kpi-linea">
            Completitud: <strong>{data.pct_completitud}%</strong>{" "}
            ({data.completas} de {data.total_combinaciones} combinaciones materia/sección completas)
          </p>
          <table className="tabla">
            <thead><tr><th>Periodo</th><th>Materia</th><th>Sección</th><th>Profesor</th>
              <th>Cargados/Esperados</th><th>Faltantes</th><th>Estado</th></tr></thead>
            <tbody>
              {data.detalle.slice(0, 100).map((d, i) => (
                <tr key={i}>
                  <td>{d.periodo}</td><td>{d.materia}</td><td>{d.seccion}</td><td>{d.profesor}</td>
                  <td>{d.cargados}/{d.esperados}</td>
                  <td>{d.faltantes.join(", ") || "—"}</td>
                  <td>{d.completa ? "✅ Completa" : "⚠️ Incompleta"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {data.detalle.length > 100 && <p className="subtitulo">Mostrando 100 de {data.detalle.length} filas.</p>}
        </>
      )}
    </section>
  );
}

function BloqueRiesgo({ params }) {
  const { data, cargando, error } = useEndpoint("/dashboard/riesgo/", params);
  return (
    <section className="tarjeta">
      <h3>Bloque 7 · Riesgo de acreditación</h3>
      <EstadoCarga cargando={cargando} error={error} />
      {data && (
        <>
          <div className="kpi-row">
            <div className="kpi"><span className="kpi-num">{data.resumen.materias_sin_catalogo}</span>Materias sin catálogo</div>
            <div className="kpi"><span className="kpi-num">{data.resumen.ras_sin_evidencia}</span>RAs sin evidencia</div>
            <div className="kpi"><span className="kpi-num">{data.resumen.ras_bajo_umbral_consecutivo}</span>RAs bajo umbral consecutivo</div>
          </div>
          {data.ras_bajo_umbral_consecutivo.length > 0 && (
            <>
              <h4>RAs bajo umbral en periodos consecutivos</h4>
              <table className="tabla">
                <thead><tr><th>Materia</th><th>RA</th><th>Periodos consecutivos</th><th>Periodos</th></tr></thead>
                <tbody>{data.ras_bajo_umbral_consecutivo.map((r, i) => (
                  <tr key={i}><td>{r.materia}</td><td>{r.ra}</td><td>{r.periodos_consecutivos}</td><td>{r.periodos.join(", ")}</td></tr>
                ))}</tbody>
              </table>
            </>
          )}
          {data.ras_sin_evidencia.length > 0 && (
            <>
              <h4>RAs catalogados sin evidencia</h4>
              <ul className="lista-hallazgos">
                {data.ras_sin_evidencia.slice(0, 30).map((r, i) => (
                  <li key={i}>{r.materia} · {r.ra} (Nivel {r.nivel_esperado})</li>
                ))}
              </ul>
            </>
          )}
          {data.materias_sin_catalogo.length > 0 && (
            <>
              <h4>Materias sin catálogo definido</h4>
              <ul className="lista-hallazgos">
                {data.materias_sin_catalogo.map((m, i) => <li key={i}>{m.materia} — {m.nombre}</li>)}
              </ul>
            </>
          )}
        </>
      )}
    </section>
  );
}

function BloqueProxy({ params }) {
  const { data, cargando, error } = useEndpoint("/dashboard/proxy-consistencia/", params);
  return (
    <section className="tarjeta">
      <h3>Proxy de consistencia entre evaluadores</h3>
      <p className="subtitulo">
        Comparación de distribuciones de la misma materia entre secciones/profesores. Es un
        <strong> proxy</strong>: no es consistencia inter-evaluador real (no hay doble calificación
        del mismo trabajo).
      </p>
      <EstadoCarga cargando={cargando} error={error} />
      {data && (
        <table className="tabla">
          <thead><tr><th>Materia</th><th>RA</th><th>Dispersión</th><th>Grupos (sección/profesor · %)</th></tr></thead>
          <tbody>
            {data.resultados.slice(0, 50).map((r, i) => (
              <tr key={i} className={r.alerta ? "fila-alerta" : ""}>
                <td>{r.materia}</td><td>{r.ra}</td>
                <td>{r.dispersion} pts{r.alerta && " ⚠️"}</td>
                <td>{r.grupos.map((g) => `S${g.seccion}: ${g.pct}%`).join(" · ")}</td>
              </tr>
            ))}
            {data.resultados.length === 0 && <tr><td colSpan={4}>Sin materias con múltiples secciones para comparar.</td></tr>}
          </tbody>
        </table>
      )}
    </section>
  );
}
