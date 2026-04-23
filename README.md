# SCRAPING-INSTAGRAM
Este proyecto trata de obtener información pública de un perfil de instagram. Estos datos se guardan en un archivo formato .json y estos son pasados a un dashboard html.

SE RECOMIENDA TRABAJAR DENTRO DE UN ENTERNO VIRTUAL PARA NO TENER PROBLEMAS DE CONFLICTOS DE LIBRERIAS.

1. Crear el entorno virtual
  python -m venv venv
2. Activar el entorno
   venv\Scripts\Activate

Instalar las librerias dentro del entorno

3. pip install requests beautifulsoup4 lxml python-dotenv

Por seguridad se crea un .env para guardar los datos sensibles

4. TARGET_USER=nombre del perfil a consultar
5. COOKIES_FILE=nombre del archivo generado de las cookies

Preparacion de las cookies

6. iniciamos sesión en nuestro perfil de instagram
7. la forma más fácil de obtener las cookies, es usando una extensión Cookie - Editor
8. guardamos los datos en formato .json
9. y ese nombre lo ponemos tambien en COOKIES_FILE

La ejecución de este proyecto lo haces de la siguente manera:

10. python nombre.py

Nota: Este proyecto tiene únicamente fines EDUCATIVOS. Respetamos los terminos de uso de la plataforma y la PRIVACIDAD de los usuarios.
