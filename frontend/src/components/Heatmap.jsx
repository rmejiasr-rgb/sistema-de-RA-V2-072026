const COLOR = {
  VERDE: "#1f8a4c",
  AMARILLO: "#c98a12",
  ROJO: "#c0392b",
  SIN_DATOS: "#d0d3d8",
};

/**
 * Mapa de calor genérico. filas/columnas son arrays de etiquetas; celdas es un
 * array de { [claveFila]: ..., [claveCol]: ..., pct, semaforo }.
 */
export default function Heatmap({ filas, columnas, celdas, claveFila, claveCol }) {
  const mapa = {};
  celdas.forEach((c) => {
    mapa[`${c[claveFila]}||${c[claveCol]}`] = c;
  });

  if (!filas.length || !columnas.length) {
    return <p className="subtitulo">Sin datos para los filtros seleccionados.</p>;
  }

  return (
    <div className="heatmap-scroll">
      <table className="heatmap">
        <thead>
          <tr>
            <th />
            {columnas.map((col) => (
              <th key={col} title={col}>{col.length > 18 ? col.slice(0, 18) + "…" : col}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {filas.map((fila) => (
            <tr key={fila}>
              <th title={fila}>{fila.length > 24 ? fila.slice(0, 24) + "…" : fila}</th>
              {columnas.map((col) => {
                const celda = mapa[`${fila}||${col}`];
                return (
                  <td
                    key={col}
                    style={{ backgroundColor: celda ? COLOR[celda.semaforo] : "transparent", color: celda ? "#fff" : "inherit" }}
                    title={celda ? `${celda.pct}% (n=${celda.n})` : "sin datos"}
                  >
                    {celda ? `${celda.pct}%` : "—"}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
