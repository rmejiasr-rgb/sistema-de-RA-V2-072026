import { useState } from "react";
import client from "../api/client";

const ESTADO_INICIAL = { estado: "idle", reporte: null, error: null };

export default function Carga() {
  const [archivo, setArchivo] = useState(null);
  const [resultado, setResultado] = useState(ESTADO_INICIAL);
  const [enviando, setEnviando] = useState(false);

  const subir = async (confirmarNuevaVersion = false) => {
    if (!archivo) return;
    setEnviando(true);
    const formData = new FormData();
    formData.append("archivo", archivo);
    if (confirmarNuevaVersion) formData.append("confirmar_nueva_version", "true");

    try {
      const { data } = await client.post("/uploads/cargar/", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResultado({ estado: "aceptado", reporte: data, error: null });
    } catch (err) {
      const data = err.response?.data;
      if (err.response?.status === 409) {
        setResultado({ estado: "requiere_confirmacion", reporte: data, error: null });
      } else if (data?.errores) {
        setResultado({ estado: "rechazado", reporte: data, error: null });
      } else {
        setResultado({ estado: "error", reporte: null, error: "Error de conexión con el servidor." });
      }
    } finally {
      setEnviando(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setResultado(ESTADO_INICIAL);
    subir(false);
  };

  return (
    <div className="contenedor">
      <h2>Cargar archivo de rúbrica RA</h2>
      <p className="subtitulo">
        Sube el archivo .xlsx de la plantilla RA UNIMET. El sistema lo parseará, validará y
        publicará automáticamente en el tablero si pasa todas las validaciones.
      </p>

      <form className="tarjeta" onSubmit={handleSubmit}>
        <input
          type="file"
          accept=".xlsx"
          onChange={(e) => {
            setArchivo(e.target.files[0]);
            setResultado(ESTADO_INICIAL);
          }}
          required
        />
        <button type="submit" disabled={!archivo || enviando}>
          {enviando ? "Procesando..." : "Subir y validar"}
        </button>
      </form>

      {resultado.error && <p className="mensaje-error">{resultado.error}</p>}

      {resultado.estado === "rechazado" && (
        <div className="tarjeta reporte reporte-error">
          <h3>Archivo rechazado</h3>
          <ul>
            {resultado.reporte.errores.map((e, i) => (
              <li key={i}>
                <strong>{e.codigo}:</strong> {e.mensaje}
              </li>
            ))}
          </ul>
        </div>
      )}

      {resultado.estado === "requiere_confirmacion" && (
        <div className="tarjeta reporte reporte-advertencia">
          <h3>Ya existe una versión de esta carga</h3>
          {resultado.reporte.advertencias.map((a, i) => (
            <p key={i}>{a.mensaje}</p>
          ))}
          <button onClick={() => subir(true)} disabled={enviando}>
            {enviando ? "Procesando..." : "Confirmar y re-subir como nueva versión"}
          </button>
        </div>
      )}

      {resultado.estado === "aceptado" && (
        <div className="tarjeta reporte reporte-ok">
          <h3>Carga validada y publicada</h3>
          <p>
            {resultado.reporte.carga.materia_codigo} · Sección {resultado.reporte.carga.seccion} ·{" "}
            {resultado.reporte.carga.ra_codigo} · Versión {resultado.reporte.carga.version}
          </p>
          {resultado.reporte.advertencias?.length > 0 && (
            <ul>
              {resultado.reporte.advertencias.map((a, i) => (
                <li key={i}>{a.mensaje}</li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
