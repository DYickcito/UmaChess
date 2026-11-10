# Ajedrez en la terminal

Juego local para dos personas, compatible con Python 3.12. `python-chess` valida los movimientos, incluidos enroque, captura al paso, coronación, jaque, mate y tablas.

## Instalación y ejecución

```sh
python -m pip install -r requirements.txt
python ajedrez.py
```

En Windows, si `python` no apunta a Python 3.12, utiliza `py -3.12` en ambos comandos.

Introduce jugadas por coordenadas (`e2e4`, `e7e8q`) o en notación algebraica estándar (`Nf3`, `O-O`, `e8=Q`). Escribe `ayuda` dentro del juego para ver todos los comandos. Las letras mayúsculas del tablero son piezas blancas; las minúsculas, negras. La notación algebraica usa letras inglesas para las piezas.

## Interfaz gráfica (independiente del juego de terminal)

Instala las dependencias anteriores y abre la ventana con:

```sh
python ajedrez_grafico.py
```

Haz clic en una pieza y luego en una casilla resaltada para moverla. La interfaz incluye selección de coronación, historial, partida nueva, deshacer y reclamación de tablas. En Windows, puedes usar `py -3.12` en lugar de `python`.

Las hojas originales están en `Sprites/`, agrupadas por personaje. Los doce fotogramas **ya recortados** están en `assets/piezas/`: una imagen a color (blancas) y otra en escala de grises (negras) por personaje. Para regenerarlos sin modificar las hojas originales, ejecuta `python generar_piezas.py`. La selección de hojas y poses está en `generar_piezas.py`. Si faltan los recortes, aparecen piezas provisionales. No hay animaciones de movimiento.

## Jugar online

La versión web permite jugar con un amigo desde dos navegadores: el creador de la sala es blancas; quien abra primero el enlace compartido será negras. También se puede entrar como espectador. Admite coronación, tablas reglamentarias, rendición, reconexión y revancha. **Las jugadas se validan en el servidor.**

Para ejecutarla localmente:

```sh
python -m pip install -r requirements-web.txt
python -m uvicorn servidor_web:app --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000` en el navegador. Para que otra persona juegue desde Internet, despliega el servicio: localhost solo funciona en tu equipo.

### Despliegue en Render

1. Sube el proyecto a un repositorio Git (incluyendo `assets/piezas/`, `web/`, `Dockerfile` y `render.yaml`; `.gitignore` excluye las hojas originales de `Sprites/`).
2. En Render, elige **New → Blueprint**, conecta el repositorio y aplica `render.yaml`. Se desplegará el frontend y el backend juntos en un único servicio web.
3. Abre la URL HTTPS que asigne Render, crea una sala y comparte el enlace de invitación. La página conectará por WSS automáticamente.

### Publicar también el frontend en Vercel

1. Despliega primero Render y copia su URL HTTPS (por ejemplo `https://uma-chess.onrender.com`).
2. Importa el mismo repositorio en Vercel. En las variables de entorno del proyecto, configura `RENDER_BACKEND_URL` con esa URL HTTPS, **sin barra final**. `vercel.json` construye el frontend estático y lo enlaza al backend de Render.
3. Cuando sepas el dominio de Vercel, añade en las variables de entorno de **Render** `ALLOWED_ORIGINS=https://tu-sitio.vercel.app` (sin barra final). Reinicia/despliega el servicio Render. Si tienes un dominio personalizado, añade también su origen, separado por coma.

Ambas URLs mostrarán el juego; las partidas se alojan siempre en Render. Comparte el enlace de invitación desde el **mismo sitio** en el que creaste la sala para que el invitado vea ese frontend. Render gratuito puede suspender servicios inactivos. Las salas se guardan **en memoria**: se pierden cuando el servicio reinicia o se duerme. Usa una sola instancia / un solo worker. Para persistencia y escalado entre instancias haría falta añadir una base de datos y coordinación (por ejemplo Redis). Vercel por sí solo no ejecuta el backend de WebSockets persistentes.

Para ejecutar todas las pruebas: `python -m pip install -r requirements-dev.txt` y `python -m unittest -q`.
