# SCRAPING-INSTAGRAM

## Objetivo

El script realiza tres tareas principales:

1. Consulta el perfil objetivo.
2. Obtiene sus ultimas fotos con metricas basicas.
3. Genera:
  - `resultado.json` con los datos estructurados.
  - `dashboard.html` para visualizar perfil y publicaciones.

## Que se uso?

- Python 3.10+
- `requests`
- `beautifulsoup4`
- `lxml`
- `python-dotenv`

Archivos creados para el proyecto:

- `main.py`
- `.env`
- `cookies.json`
- `resultado.json` (se genera al ejecutar)
- `dashboard.html` (se genera al ejecutar)

# Configuracion paso a paso

1. Crear y activar entorno virtual

python -m venv venv
venv\Scripts\Activate

2. Instalar dependencias

pip install requests beautifulsoup4 lxml python-dotenv

3. Configurar variables en `.env`

Crear un archivo `.env` con:

TARGET_USER=nombre_del_perfil_objetivo
COOKIES_FILE=cookies.json

# Preparacion de cookies

1. Iniciamos sesion en Instagram desde el navegador.
2. Exportamos las cookies con una extension como Cookie-Editor.
3. Guardamos el archivo en formato JSON (por ejemplo: `cookies.json`).
4. Importante, verificar que `COOKIES_FILE` en `.env` apunte a ese archivo.

# Ejecucion

python main.py

Al terminar, se generan:

- `resultado.json`
- `dashboard.html`

# Logica implementada

El flujo interno en `main.py` esta pensado para ser mas estable frente a bloqueos temporales y respuestas incompletas.

1. carga de cookies

Se leen cookies desde el archivo JSON y se cargan en una sesion `requests.Session()` para reutilizar autenticacion y headers.

2. Resolucion del perfil objetivo

Se usa una estrategia por etapas:

1. Buscar usuario por `topsearch` para obtener datos base y `user_id`.
2. Con ese `user_id`, consultar endpoint de detalle:
  - seguidores
  - seguidos
  - total de posts
3. Si algun campo no llega completo, pasa por fallback con parseo adicional.

Esta estrategia evita depender de un solo endpoint que puede responder con error 429 (error para demasiadas solicitudes).

3. Obtencion de fotos recientes

Con el `user_id` del perfil objetivo se consulta el feed del usuario y se filtran publicaciones de tipo foto.
Por cada foto se extrae:

- id
- fecha
- likes
- comentarios
- descripcion
- url de imagen
- url del post

4. Salida en JSON

Se construye un objeto con dos bloques:

- `perfil_objetivo`
- `ultimas_fotos`

Ese objeto se guarda en `resultado.json`.

5. Generacion del dashboard HTML

Desde el JSON se construye una vista estatica en `dashboard.html` con:

- Cabecera del perfil (foto, nombre, biografia)
- Tarjetas de metricas (seguidores, seguidos, posts)
- Grid de publicaciones con imagenes embebidas (no solo links)

## Solucion de problemas

- Error 429 (Too Many Requests)

- Espera unos minutos y vuelve a ejecutar.
- Evita ejecutar el script en bucle continuo.
- Verifica que las cookies esten vigentes.

### `None` en seguidores o posts

- Hay que conciderar que el perfil exista y sea localizable por username.
- Verifica que las cookies correspondan a una sesion activa.
- Reintenta mas tarde por posibles limites temporales del endpoint.

- IMPORTANTE

- No se sube el archivo `.env` ni cookies al repositorio.
- Mantener el proyecto dentro del entorno virtual.
- Rotar cookies si dejan de funcionar.

# ADVERTENCIA

Este proyecto es solo con fines educativos. Siempre se respeto los terminos de uso de la plataforma y la privacidad de terceros.
