import json
import os
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# CONFIGURACIÓN

load_dotenv()

MY_USERNAME   = os.getenv("MY_USERNAME")
TARGET_USER   = os.getenv("TARGET_USER")
COOKIES_FILE  = os.getenv("COOKIES_FILE", "cookies.json")
OUTPUT_FILE   = "resultado.json"

# Headers que Instagram espera ver (imita Chrome)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "es-ES,es;q=0.9",
    "Referer":         "https://www.instagram.com/",
    "x-ig-app-id":     "936619743392459",
}

# ── Funciones auxiliares ──────────────────────────────────────────────────────

def cargar_cookies(ruta: str) -> dict:
    
    if not os.path.exists(ruta):
        raise FileNotFoundError(
            f"No se encontró '{ruta}'.\n"
         
        )

    with open(ruta, encoding="utf-8") as f:
        raw = json.load(f)

    # Cookie-Editor exporta una lista de objetos; extraemos name/value
    if isinstance(raw, list):
        return {c["name"]: c["value"] for c in raw if "name" in c and "value" in c}

    # Si ya es un dict plano lo devolvemos tal cual
    return raw


def obtener_perfil(session: requests.Session, username: str) -> dict:
    
    url = (
        "https://www.instagram.com/api/v1/users/web_profile_info/"
        f"?username={username}"
    )
    r = session.get(url, timeout=20)
    r.raise_for_status()

    # BeautifulSoup para parsear la respuesta (el cuerpo es JSON plano)
    soup = BeautifulSoup(r.text, "lxml")
    texto = soup.get_text()          # extrae el texto del documento
    data  = json.loads(texto)        # lo parsea como JSON
    return data["data"]["user"]

def obtener_ultimas_fotos(session: requests.Session, user_id: str, cantidad: int = 10) -> list:
    
    url = f"https://www.instagram.com/api/v1/feed/user/{user_id}/?count=12"
    fotos = []
    next_max_id = None

    while len(fotos) < cantidad:
        params = {}
        if next_max_id:
            params["max_id"] = next_max_id

        r = session.get(url, params=params, timeout=20)
        r.raise_for_status()

        soup  = BeautifulSoup(r.text, "lxml")
        data  = json.loads(soup.get_text())
        items = data.get("items", [])

        for item in items:
            # media_type 1 = foto, 2 = video, 8 = carrusel
            if item.get("media_type") == 1:
                timestamp = item.get("taken_at")
                fotos.append({
                    "id":           item.get("id"),
                    "fecha":        formatear_fecha(timestamp),
                    "fecha_unix":   timestamp,
                    "likes":        item.get("like_count", 0),
                    "comentarios":  item.get("comment_count", 0),
                    "descripcion":  (
                        item.get("caption", {}).get("text", "")
                        if item.get("caption") else ""
                    ),
                    "url_imagen":   (
                        item.get("image_versions2", {})
                            .get("candidates", [{}])[0]
                            .get("url", "")
                    ),
                    "url_post":     f"https://www.instagram.com/p/{item.get('code', '')}/",
                })

        if not data.get("more_available") or not items:
            break

        next_max_id = data.get("next_max_id")
        time.sleep(1)   # pausa para no saturar la API

    return fotos[:cantidad]


def formatear_fecha(timestamp: int | None) -> str | None:
    if not timestamp:
        return None

    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


# ── Script principal ──────────────────────────────────────────────────────────

def main():
    # Validaciones básicas
    if not MY_USERNAME:
        raise ValueError("Define MY_USERNAME en el archivo .env")
    if not TARGET_USER:
        raise ValueError("Define TARGET_USER en el archivo .env")

    # 1. Cargar cookies y crear sesión autenticada
    print("Cargando cookies...")
    cookies = cargar_cookies(COOKIES_FILE)

    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(cookies)

    # 2. Verificar sesión y obtener datos de MI perfil
    print(f"Obteniendo tu perfil (@{MY_USERNAME})...")
    mi_perfil_raw = obtener_perfil(session, MY_USERNAME)
    mi_perfil = {
        "username":   mi_perfil_raw.get("username"),
        "nombre":     mi_perfil_raw.get("full_name"),
        "seguidores": mi_perfil_raw.get("edge_followed_by", {}).get("count"),
        "siguiendo":  mi_perfil_raw.get("edge_follow", {}).get("count"),
    }
    print(f"Sesión válida: {mi_perfil['nombre']} "
          f"| Seguidores: {mi_perfil['seguidores']} "
          f"| Siguiendo: {mi_perfil['siguiendo']}")

    # 3. Obtener datos del perfil OBJETIVO
    print(f"Obteniendo perfil objetivo (@{TARGET_USER})...")
    time.sleep(1)

    perfil_raw = obtener_perfil(session, TARGET_USER)

    if perfil_raw.get("is_private"):
        raise ValueError(f"El perfil @{TARGET_USER} es privado. Elige un perfil público.")

    perfil_objetivo = {
        "username":         perfil_raw.get("username"),
        "nombre":           perfil_raw.get("full_name"),
        "biografia":        perfil_raw.get("biography"),
        "seguidores":       perfil_raw.get("edge_followed_by", {}).get("count"),
        "siguiendo":        perfil_raw.get("edge_follow", {}).get("count"),
        "total_posts":      perfil_raw.get("edge_owner_to_timeline_media", {}).get("count"),
        "verificado":       perfil_raw.get("is_verified"),
        "es_negocio":       perfil_raw.get("is_business_account"),
        "url_foto_perfil":  perfil_raw.get("profile_pic_url_hd"),
        "user_id":          perfil_raw.get("id"),
    }
    print(f"    {perfil_objetivo['nombre']} "
          f"| Seguidores: {perfil_objetivo['seguidores']} "
          f"| Posts: {perfil_objetivo['total_posts']}")

    # 4. Obtener las últimas 10 fotos del perfil objetivo
    print(f"Obteniendo últimas 10 fotografías de @{TARGET_USER}...")
    time.sleep(1)
    fotos = obtener_ultimas_fotos(session, perfil_objetivo["user_id"], cantidad=10)
    print(f"    {len(fotos)} fotografías obtenidas.")

    # 5. Guardar resultado
    resultado = {
        "mi_perfil":        mi_perfil,
        "perfil_objetivo":  perfil_objetivo,
        "ultimas_fotos":    fotos,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)

    print(f"\nDatos guardados en '{OUTPUT_FILE}'")
    print(f"  Perfil personal: @{mi_perfil['username']}")
    print(f"  Perfil objetivo: @{perfil_objetivo['username']}")
    print(f"  Fotos obtenidas: {len(fotos)}")


if __name__ == "__main__":
    main()
