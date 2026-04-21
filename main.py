import requests
from bs4 import BeautifulSoup

#ingresamos los datos de perfil
BASE_URL = "https://www.instagram.com/"
TARGET_PROFILE = "kikejav"
PROFILE_URL = f"{BASE_URL}{TARGET_PROFILE}/"

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8"
    ),
    "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    "Referer": "https://www.instagram.com/",
    "Connection": "keep-alive"
}

# PEGA AQUÍ TUS COOKIES DE SESIÓN MANUAL
cookies = {
    "csrftoken": "VszSroq7GdqiNT9UG1ZPSIaaOnDfAKWq",
    "sessionid": "1479405478%3AxnD4qDdFIG0QZD%3A16%3AAYjxn7Irwih-kp3_V6N59ht4RbHdEOzkV9EnO-Pz_20"
}

response = requests.get(PROFILE_URL, headers=headers, cookies=cookies)

print("URL objetivo:", PROFILE_URL)
print("Código de estado:", response.status_code)
print("Tipo de contenido:", response.headers.get("Content-Type"))

html = response.text
soup = BeautifulSoup(html, "lxml")

scripts = soup.find_all("script")

print("\n=== INSPECCIÓN DE SCRIPTS ===")
print("Cantidad de scripts encontrados:", len(scripts))

html_lower = html.lower()

print("\n=== BÚSQUEDA DE PALABRAS CLAVE EN EL HTML ===")
print("Contiene 'graphql':", "graphql" in html_lower)
print("Contiene 'username':", "username" in html_lower)
print("Contiene '/p/':", "/p/" in html)
print("Contiene 'profile_pic_url':", "profile_pic_url" in html)
print("Contiene 'edge_owner_to_timeline_media':", "edge_owner_to_timeline_media" in html)

print("\n=== PRIMEROS 3 SCRIPTS CON TEXTO ===")
contador = 0
for script in scripts:
    contenido = script.get_text(strip=True)
    if contenido:
        contador += 1
        print(f"\n--- SCRIPT {contador} ---")
        print(contenido[:800])
        if contador == 3:
            break