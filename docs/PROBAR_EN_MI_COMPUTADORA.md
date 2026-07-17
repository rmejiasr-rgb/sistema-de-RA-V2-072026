# Cómo ver el sistema funcionando en mi computadora

Guía pensada para alguien **sin experiencia en programación**. Sigue los pasos
en orden. Si algo no sale, mira la sección "Si algo falla" al final.

> **Idea general:** vas a instalar **un** programa gratuito (Docker Desktop),
> descargar el proyecto, y escribir **una sola orden**. Después abres el
> navegador y entras al sistema con datos de ejemplo ya cargados.

Tiempo estimado: 20–40 minutos la primera vez (casi todo es esperar descargas).

---

## Paso 1 — Instalar Docker Desktop

Docker es un programa que "enciende" el sistema por ti sin que tengas que
instalar Python, bases de datos ni nada más.

1. Entra a **https://www.docker.com/products/docker-desktop/**
2. Descarga la versión para tu computadora:
   - **Windows**: "Docker Desktop for Windows"
   - **Mac**: elige "Apple Chip" si tu Mac es reciente (M1/M2/M3) o "Intel Chip"
     si es más antigua. (Si no sabes: menú Apple → "Acerca de este Mac".)
3. Instálalo como cualquier programa (siguiente, siguiente, aceptar).
4. **Ábrelo** y espera a que diga que está corriendo (un ícono de ballena queda
   en la barra de tareas). Déjalo abierto.

> En Windows, Docker puede pedir activar "WSL2" o la virtualización. Si aparece
> un error sobre eso y no puedes resolverlo, es normal que necesites ayuda de
> alguien de soporte técnico; no es culpa tuya ni del sistema.

---

## Paso 2 — Descargar el proyecto

1. Entra a la página del proyecto en GitHub (el enlace de tu repositorio).
2. Asegúrate de estar en la rama **`claude/python-postgres-react-system-h9tf8w`**
   (hay un botón/desplegable que dice el nombre de la rama; selecciónala).
3. Busca el botón verde **"Code"** → **"Download ZIP"**.
4. Se descarga un archivo comprimido. **Descomprímelo** (clic derecho →
   "Extraer todo" en Windows, o doble clic en Mac).
5. Te queda una carpeta con el proyecto. Recuerda **dónde la guardaste** (por
   ejemplo, en "Descargas" o en el Escritorio).

---

## Paso 3 — Abrir una "terminal" dentro de esa carpeta

La terminal es una ventanita donde escribes órdenes. Hay que abrirla **dentro
de la carpeta del proyecto**:

**En Windows:**
1. Abre la carpeta del proyecto (donde está el archivo `docker-compose.yml`).
2. Haz clic en la **barra de dirección** de arriba (donde aparece la ruta de la
   carpeta), borra lo que haya, escribe `cmd` y pulsa Enter.
3. Se abre una ventana negra: esa es la terminal, ya ubicada en la carpeta.

**En Mac:**
1. Abre la aplicación **Terminal** (búscala con Spotlight: ⌘ + barra espaciadora,
   escribe "Terminal").
2. Escribe `cd ` (con un espacio al final), **arrastra la carpeta** del proyecto
   a la ventana de Terminal y pulsa Enter.

---

## Paso 4 — Encender el sistema (una sola orden)

En la terminal que abriste, escribe exactamente esto y pulsa Enter:

```
docker compose up --build
```

- La **primera vez** descargará varias cosas: puede tardar varios minutos y
  mostrará mucho texto. Es normal. No cierres la ventana.
- Cuando veas mensajes que ya no cambian y aparezca algo como
  `Starting development server at http://0.0.0.0:8000`, ya está listo.

> El sistema deja preparado automáticamente un usuario y datos de ejemplo, para
> que puedas entrar y ver los tableros de inmediato.

---

## Paso 5 — Entrar al sistema

1. Abre tu navegador (Chrome, Edge, etc.).
2. Ve a: **http://localhost:5173**
3. Inicia sesión con:
   - **Usuario:** `admin`
   - **Clave:** `admin12345`

Verás el tablero con datos de ejemplo (semáforos, mapas de calor, etc.).
Explora los menús de arriba: Tablero, Cargar archivo, Mis cargas, Catálogo,
Cierre de periodo, Usuarios.

> ¿Quieres probar una carga real? En **Cargar archivo** sube uno de los dos
> Excel de ejemplo que están en el proyecto, en la carpeta
> `backend/apps/uploads/tests/fixtures/`.

---

## Paso 6 — Apagar el sistema

Cuando termines:

- Vuelve a la ventana de la terminal y pulsa **Ctrl + C** (Windows) o
  **Control + C** (Mac). Eso lo apaga.
- Para volver a encenderlo otro día: repite solo el Paso 4 (ya no descarga nada,
  arranca en segundos).

---

## Si algo falla

- **"docker: command not found" o similar**: Docker Desktop no está abierto o no
  terminó de instalarse. Ábrelo, espera a que diga que está corriendo, y repite
  el Paso 4.
- **La página http://localhost:5173 no carga**: espera un minuto más (la primera
  vez tarda) y recarga. Verifica que la terminal no muestre errores en rojo.
- **Un error que menciona "port is already allocated" (puerto ocupado)**: ya hay
  algo usando ese puerto. Cierra otros programas o reinicia la computadora y
  repite el Paso 4.
- **Quiero empezar de cero (borrar todo lo de la demo)**: en la terminal, dentro
  de la carpeta, escribe `docker compose down -v` y luego repite el Paso 4.
- **Cualquier otra cosa**: copia el texto del error y compártelo; se puede
  diagnosticar a partir de eso.

---

## Importante

Esto es solo para **verlo y probarlo en tu computadora**. Para usarlo de verdad
en la universidad (con varios profesores, por internet y con seguridad), el paso
correcto es entregarlo a TI UNIMET — ver `docs/ENTREGA_TI.md` y
`docs/DESPLIEGUE.md`.
