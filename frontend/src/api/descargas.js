import client from "./client";

/** Descarga un archivo binario desde un endpoint autenticado y dispara el guardado. */
export async function descargarArchivo(url, params, nombreArchivo) {
  const resp = await client.get(url, { params, responseType: "blob" });
  const blob = new Blob([resp.data]);
  const enlace = document.createElement("a");
  enlace.href = URL.createObjectURL(blob);
  enlace.download = nombreArchivo;
  document.body.appendChild(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(enlace.href);
}
