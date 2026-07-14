import { useEffect, useState } from "react";
import client from "../api/client";

export default function Catalogo() {
  const [materias, setMaterias] = useState([]);
  const [ras, setRas] = useState([]);
  const [materiaRas, setMateriaRas] = useState([]);
  const [materiaSel, setMateriaSel] = useState("");
  const [nuevo, setNuevo] = useState({ ra: "", nivel_esperado: 1 });
  const [error, setError] = useState("");

  const cargarCatalogo = (materiaId) => {
    const params = materiaId ? { materia: materiaId } : {};
    client.get("/catalog/materia-ras/", { params }).then((r) => setMateriaRas(r.data));
  };

  useEffect(() => {
    client.get("/catalog/materias/").then((r) => setMaterias(r.data));
    client.get("/catalog/ras/").then((r) => setRas(r.data));
    cargarCatalogo("");
  }, []);

  const seleccionarMateria = (id) => {
    setMateriaSel(id);
    setError("");
    cargarCatalogo(id);
  };

  const agregar = () => {
    setError("");
    if (!materiaSel) { setError("Seleccione una materia primero."); return; }
    if (!nuevo.ra) { setError("Seleccione un RA."); return; }
    client.post("/catalog/materia-ras/", {
      materia: materiaSel, ra: nuevo.ra, nivel_esperado: Number(nuevo.nivel_esperado),
    })
      .then(() => { setNuevo({ ra: "", nivel_esperado: 1 }); cargarCatalogo(materiaSel); })
      .catch((err) => setError(err.response?.data?.detail || "No fue posible agregar (¿ya existe o no es su escuela?)."));
  };

  const eliminar = (id) => {
    client.delete(`/catalog/materia-ras/${id}/`)
      .then(() => cargarCatalogo(materiaSel))
      .catch((err) => setError(err.response?.data?.detail || "No fue posible eliminar."));
  };

  const filtrados = materiaSel
    ? materiaRas.filter((mr) => String(mr.materia) === String(materiaSel))
    : materiaRas;

  return (
    <div className="contenedor">
      <h2>Catálogo Materia → RA</h2>
      <p className="subtitulo">
        Define qué RAs y en qué nivel debe evidenciar cada materia. El sistema rechaza cargas
        con un RA o nivel no catalogado. Solo puede gestionar materias de su escuela.
      </p>

      <div className="tarjeta filtros">
        <select value={materiaSel} onChange={(e) => seleccionarMateria(e.target.value)}>
          <option value="">Todas las materias</option>
          {materias.map((m) => <option key={m.id} value={m.id}>{m.codigo} — {m.nombre}</option>)}
        </select>
      </div>

      {materiaSel && (
        <div className="tarjeta">
          <h3>Agregar RA a la materia</h3>
          <div className="filtros">
            <select value={nuevo.ra} onChange={(e) => setNuevo({ ...nuevo, ra: e.target.value })}>
              <option value="">Seleccione RA…</option>
              {ras.map((r) => <option key={r.id} value={r.id}>{r.codigo} — {r.nombre}</option>)}
            </select>
            <select value={nuevo.nivel_esperado} onChange={(e) => setNuevo({ ...nuevo, nivel_esperado: e.target.value })}>
              <option value={1}>Nivel 1</option>
              <option value={2}>Nivel 2</option>
              <option value={3}>Nivel 3</option>
            </select>
            <button onClick={agregar}>Agregar</button>
          </div>
          {error && <p className="mensaje-error">{error}</p>}
        </div>
      )}

      <section className="tarjeta">
        <h3>RAs catalogados</h3>
        <table className="tabla">
          <thead><tr><th>Materia</th><th>RA</th><th>Nivel esperado</th><th>Acciones</th></tr></thead>
          <tbody>
            {filtrados.map((mr) => (
              <tr key={mr.id}>
                <td>{mr.materia_codigo}</td>
                <td>{mr.ra_codigo}</td>
                <td>Nivel {mr.nivel_esperado}</td>
                <td><button className="btn-mini secundario" onClick={() => eliminar(mr.id)}>Eliminar</button></td>
              </tr>
            ))}
            {filtrados.length === 0 && <tr><td colSpan={4}>Sin RAs catalogados.</td></tr>}
          </tbody>
        </table>
      </section>
    </div>
  );
}
