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

html = response.text

print("Código de estado:", response.status_code)
print("Longitud total del HTML:", len(html))

palabras = [
    "username",
    "profile_pic_url",
    "graphql"
]

for palabra in palabras:
    print(f"\n=== BUSCANDO: {palabra} ===")
    posicion = html.find(palabra)

    if posicion == -1:
        print("No encontrada")
    else:
        inicio = max(0, posicion - 300)
        fin = min(len(html), posicion + 800)

        print("Posición:", posicion)
        print("Contexto encontrado:\n")
        print(html[inicio:fin])

with open("instagram_html_debug.txt", "w", encoding="utf-8") as archivo:
    archivo.write(html)

print("\nSe guardó el HTML completo en: instagram_html_debug.txt")