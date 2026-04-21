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


def extraer_campo(texto, patron, nombre_campo):
    coincidencia = re.search(patron, texto)
    if coincidencia:
        valor = coincidencia.group(1)
        valor = valor.replace("\\/", "/")
        valor = valor.replace('\\"', '"')
        print(f"{nombre_campo}: {valor}")
        return valor
    else:
        print(f"{nombre_campo}: No encontrado")
        return None


print("\n=== DATOS DEL PERFIL ===")

username = extraer_campo(
    html,
    r'"username":"(.*?)"',
    "username"
)

full_name = extraer_campo(
    html,
    r'"full_name":"(.*?)"',
    "full_name"
)

biography = extraer_campo(
    html,
    r'"biography":"(.*?)"',
    "biography"
)

is_private = extraer_campo(
    html,
    r'"is_private":(true|false)',
    "is_private"
)

is_verified = extraer_campo(
    html,
    r'"is_verified":(true|false)',
    "is_verified"
)

profile_pic_url = extraer_campo(
    html,
    r'"profile_pic_url":"(.*?)"',
    "profile_pic_url"
)