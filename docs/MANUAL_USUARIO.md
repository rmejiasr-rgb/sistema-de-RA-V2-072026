# Manual de usuario — Sistema de Gestión y Análisis de RA · UNIMET

Guía por rol. La interfaz está en español y el acceso siempre es autenticado;
cada usuario ve únicamente los datos que su rol le permite.

---

## Ingreso

1. Abrir `https://<subdominio-unimet>/`.
2. Ingresar con usuario y contraseña (o con "Ingresar con Microsoft" si el SSO
   está habilitado, usando el correo `@unimet.edu.ve`).

---

## Rol Profesor

Un profesor gestiona las cargas de sus materias/secciones y consulta el
tablero filtrado a lo suyo.

### Cargar un archivo de rúbrica
1. Menú **Cargar archivo**.
2. Seleccionar el `.xlsx` de la plantilla RA UNIMET. El nombre debe seguir el
   formato `CODMAT-SECCION-PROFESOR-PERIODO-RA-NIVEL.xlsx`
   (ej. `FPTPI13-1-RICHARD_MEJIAS-2526-3-RA10-IP-N3.xlsx`).
3. **Subir y validar**. Si pasa todas las validaciones, se publica al tablero
   automáticamente.
4. Si el archivo es rechazado, el sistema indica qué celda/valor falló y qué
   hacer (mensaje en español).

### Corregir datos
- **Notas o resultados equivocados**: se corrigen **re-subiendo** el archivo
  corregido. El sistema pide confirmación y crea una **nueva versión**; la
  anterior se conserva consultable.
- **Metadatos** (actividad, fecha, nombres mal escritos): menú **Mis cargas**
  → **Editar**. El cambio exige un **motivo** y queda auditado.

### Consultar el tablero
Menú **Tablero**: semáforos de cumplimiento por RA, desagregación por criterio,
mapas de calor, tendencias, etc. Filtros por periodo, materia, RA y sección.
Botones **Exportar Excel/PDF**.

---

## Rol Coordinador

Todo lo del profesor, más la gestión de su escuela.

### Catálogo Materia → RA
Menú **Catálogo**: define qué RAs y en qué nivel debe evidenciar cada materia
de su escuela. El sistema rechaza cargas con un RA o nivel no catalogado.

### Completitud y cierre de periodo
Menú **Cierre de periodo**: muestra el % de completitud y las combinaciones
materia/sección **incompletas** (con los RAs faltantes). El periodo **no puede
cerrarse** mientras existan incompletos.

### Datos de toda la escuela
El coordinador ve y puede editar metadatos de cualquier carga de su escuela, y
exportar reportes consolidados.

---

## Rol Administrador

Todo lo anterior, más la administración del sistema.

### Gestión de usuarios
Menú **Usuarios**: alta y edición de usuarios, asignación de uno o varios roles
(Profesor, Coordinador, Administrador) y de la escuela. Puede fijar/restablecer
contraseñas. Cada cambio queda auditado.

### Parámetros del sistema
Desde `/admin/` (panel de administración de Django): escuelas, carreras,
periodos, materias, RAs del catálogo, umbrales de semáforo y auditoría.

---

## Notas de privacidad

Los nombres y notas de estudiantes son datos sensibles. El acceso es siempre
autenticado y el filtrado por rol se aplica en el servidor: un profesor jamás
ve las notas de otro. Toda exportación y edición de metadatos queda registrada
(quién y cuándo).
