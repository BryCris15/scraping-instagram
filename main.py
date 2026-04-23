import json
import os
import re
import time
from datetime import datetime
from html import escape

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# CONFIGURACIÓN

load_dotenv()

TARGET_USER   = os.getenv("TARGET_USER")
COOKIES_FILE  = os.getenv("COOKIES_FILE", "cookies.json")
OUTPUT_FILE   = "resultado.json"
DASHBOARD_FILE = "dashboard.html"

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
            f"No se encontró '{ruta}'.\n")

    with open(ruta, encoding="utf-8") as f:
        raw = json.load(f)

    # Cookie-Editor exporta una lista de objetos; extraemos name/value
    if isinstance(raw, list):
        return {c["name"]: c["value"] for c in raw if "name" in c and "value" in c}

    # Si ya es un dict plano lo devolvemos tal cual
    return raw


def obtener_perfil(session: requests.Session, username: str) -> dict:
    
    search_url = "https://www.instagram.com/web/search/topsearch/"
    r = session.get(search_url, params={"query": username}, timeout=20)
    r.raise_for_status()

    data = r.json()
    usuario = None

    for entry in data.get("users", []):
        candidato = entry.get("user", {})
        if candidato.get("username", "").lower() == username.lower():
            usuario = candidato
            break

    if not usuario:
        raise ValueError(f"No se encontró el perfil público @{username}.")

    seguidores = None
    contexto_social = usuario.get("search_social_context") or usuario.get("social_context")
    if contexto_social:
        match_followers = re.search(r"([\d.,]+)\s*(mil|millones)?\s+seguidores", contexto_social, re.IGNORECASE)
        if match_followers:
            base = float(match_followers.group(1).replace(",", "."))
            escala = (match_followers.group(2) or "").lower()
            if escala == "mil":
                seguidores = int(base * 1_000)
            elif escala == "millones":
                seguidores = int(base * 1_000_000)
            else:
                seguidores = int(base)

    detalle_url = f"https://www.instagram.com/api/v1/users/{usuario.get('pk') or usuario.get('id')}/info/"
    detalle_usuario = {}
    try:
        detalle_response = session.get(detalle_url, timeout=30)
        detalle_response.raise_for_status()
        detalle_usuario = detalle_response.json().get("user", {})
    except requests.RequestException:
        detalle_usuario = {}

    perfil = {
        "username": detalle_usuario.get("username", usuario.get("username")),
        "full_name": detalle_usuario.get("full_name", usuario.get("full_name")),
        "biography": detalle_usuario.get("biography", usuario.get("biography", "")),
        "edge_followed_by": {"count": detalle_usuario.get("follower_count", seguidores)},
        "edge_follow": {"count": detalle_usuario.get("following_count")},
        "edge_owner_to_timeline_media": {"count": detalle_usuario.get("media_count")},
        "is_verified": detalle_usuario.get("is_verified", usuario.get("is_verified")),
        "is_business_account": detalle_usuario.get("is_business"),
        "profile_pic_url_hd": detalle_usuario.get("hd_profile_pic_url_info", {}).get("url", usuario.get("profile_pic_url")),
        "id": detalle_usuario.get("pk") or detalle_usuario.get("id") or usuario.get("pk") or usuario.get("id"),
        "is_private": detalle_usuario.get("is_private", usuario.get("is_private")),
    }

    html_url = f"https://www.instagram.com/{username}/"
    html_response = session.get(html_url, timeout=20)
    if html_response.ok:
        soup = BeautifulSoup(html_response.text, "lxml")
        script_content = "\n".join(
            script.get_text(" ", strip=False)
            for script in soup.find_all("script")
        )
        pattern = re.compile(
            r'\["PolarisViewer",\[\],\{"data":(\{.*?"username":"'
            + re.escape(username)
            + r'".*?\}),"id":"\d+"\}'
        )
        match = pattern.search(script_content)
        if match:
            enriched = json.loads(match.group(1))
            perfil.update({
                "full_name": enriched.get("full_name", perfil["full_name"]),
                "biography": enriched.get("biography", perfil["biography"]),
                "is_business_account": enriched.get("is_business_account", perfil["is_business_account"]),
                "profile_pic_url_hd": enriched.get("profile_pic_url_hd", perfil["profile_pic_url_hd"]),
                "id": enriched.get("id", perfil["id"]),
                "is_private": enriched.get("is_private", perfil["is_private"]),
            })

    return perfil

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


def formatear_numero(valor: int | None) -> str:
        if valor is None:
                return "No disponible"
        return f"{valor:,}".replace(",", ".")


def generar_dashboard_html(resultado: dict) -> str:
        perfil = resultado.get("perfil_objetivo", {})
        fotos = resultado.get("ultimas_fotos", [])

        tarjetas_fotos = []
        for foto in fotos:
                descripcion = escape(foto.get("descripcion") or "Sin descripcion")
                fecha = escape(foto.get("fecha") or "Sin fecha")
                url_imagen = escape(foto.get("url_imagen") or "")
                url_post = escape(foto.get("url_post") or "#")
                likes = formatear_numero(foto.get("likes"))
                comentarios = formatear_numero(foto.get("comentarios"))

                tarjetas_fotos.append(
                        f"""
                        <article class=\"post-card\">
                            <a class=\"post-image-link\" href=\"{url_post}\" target=\"_blank\" rel=\"noopener noreferrer\">
                                <img class=\"post-image\" src=\"{url_imagen}\" alt=\"Publicacion de {escape(perfil.get('username', 'instagram'))}\" loading=\"lazy\">
                            </a>
                            <div class=\"post-body\">
                                <div class=\"post-meta\">
                                    <span>{fecha}</span>
                                    <a href=\"{url_post}\" target=\"_blank\" rel=\"noopener noreferrer\">Ver post</a>
                                </div>
                                <p class=\"post-description\">{descripcion}</p>
                                <div class=\"post-stats\">
                                    <span>Likes: {likes}</span>
                                    <span>Comentarios: {comentarios}</span>
                                </div>
                            </div>
                        </article>
                        """.strip()
                )

        biografia = escape(perfil.get("biografia") or "Sin biografia")
        biografia = biografia.replace("\n", "<br>")

        return f"""
<!DOCTYPE html>
<html lang=\"es\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>Dashboard Instagram - {escape(perfil.get('username', 'perfil'))}</title>
    <style>
        :root {{
            --bg: #f4efe6;
            --panel: rgba(255, 251, 245, 0.82);
            --panel-strong: #fffaf2;
            --text: #1f1a17;
            --muted: #6b625c;
            --accent: #c84c2a;
            --accent-soft: #f1c7a8;
            --line: rgba(31, 26, 23, 0.1);
            --shadow: 0 20px 45px rgba(80, 46, 24, 0.14);
        }}

        * {{ box-sizing: border-box; }}

        body {{
            margin: 0;
            font-family: "Space Grotesk", "Segoe UI", sans-serif;
            color: var(--text);
            background:
                radial-gradient(circle at top left, rgba(200, 76, 42, 0.14), transparent 28%),
                radial-gradient(circle at top right, rgba(111, 148, 112, 0.18), transparent 22%),
                linear-gradient(180deg, #f8f2e8 0%, var(--bg) 55%, #efe6da 100%);
            min-height: 100vh;
        }}

        .shell {{
            width: min(1180px, calc(100% - 32px));
            margin: 0 auto;
            padding: 32px 0 48px;
        }}

        .hero {{
            display: grid;
            grid-template-columns: 140px 1fr;
            gap: 24px;
            align-items: center;
            background: var(--panel);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.55);
            border-radius: 28px;
            padding: 28px;
            box-shadow: var(--shadow);
        }}

        .avatar {{
            width: 140px;
            height: 140px;
            border-radius: 28px;
            object-fit: cover;
            border: 4px solid rgba(255, 255, 255, 0.9);
            box-shadow: 0 14px 24px rgba(0, 0, 0, 0.12);
            background: #e8ddd0;
        }}

        .hero h1 {{
            margin: 0;
            font-size: clamp(2rem, 4vw, 3.6rem);
            line-height: 0.95;
            letter-spacing: -0.04em;
        }}

        .username {{
            margin-top: 8px;
            color: var(--accent);
            font-size: 1rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        .bio {{
            margin-top: 16px;
            color: var(--muted);
            line-height: 1.7;
            max-width: 68ch;
        }}

        .stats {{
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 16px;
            margin-top: 28px;
        }}

        .stat {{
            background: var(--panel-strong);
            border-radius: 22px;
            padding: 18px;
            border: 1px solid var(--line);
        }}

        .stat-label {{
            display: block;
            color: var(--muted);
            font-size: 0.84rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }}

        .stat-value {{
            display: block;
            margin-top: 10px;
            font-size: 1.5rem;
            font-weight: 700;
        }}

        .section-title {{
            margin: 34px 0 18px;
            font-size: 1.3rem;
            letter-spacing: -0.03em;
        }}

        .posts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 18px;
        }}

        .post-card {{
            overflow: hidden;
            background: var(--panel);
            border-radius: 26px;
            border: 1px solid rgba(255, 255, 255, 0.6);
            box-shadow: var(--shadow);
            backdrop-filter: blur(10px);
        }}

        .post-image-link {{
            display: block;
            aspect-ratio: 4 / 5;
            background: #e9dfd4;
        }}

        .post-image {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: block;
        }}

        .post-body {{
            padding: 18px;
        }}

        .post-meta, .post-stats {{
            display: flex;
            justify-content: space-between;
            gap: 12px;
            color: var(--muted);
            font-size: 0.9rem;
            flex-wrap: wrap;
        }}

        .post-meta a {{
            color: var(--accent);
            text-decoration: none;
            font-weight: 700;
        }}

        .post-description {{
            margin: 14px 0 16px;
            line-height: 1.65;
            color: var(--text);
            display: -webkit-box;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 5;
            overflow: hidden;
        }}

        @media (max-width: 760px) {{
            .hero {{
                grid-template-columns: 1fr;
                text-align: center;
            }}

            .avatar {{
                margin: 0 auto;
            }}

            .stats {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}
    </style>
</head>
<body>
    <main class=\"shell\">
        <section class=\"hero\">
            <img class=\"avatar\" src=\"{escape(perfil.get('url_foto_perfil') or '')}\" alt=\"Foto de perfil de {escape(perfil.get('username') or 'perfil')}\">
            <div>
                <h1>{escape(perfil.get('nombre') or 'Perfil objetivo')}</h1>
                <div class=\"username\">@{escape(perfil.get('username') or '')}</div>
                <p class=\"bio\">{biografia}</p>
                <div class=\"stats\">
                    <div class=\"stat\"><span class=\"stat-label\">Seguidores</span><span class=\"stat-value\">{formatear_numero(perfil.get('seguidores'))}</span></div>
                    <div class=\"stat\"><span class=\"stat-label\">Siguiendo</span><span class=\"stat-value\">{formatear_numero(perfil.get('siguiendo'))}</span></div>
                    <div class=\"stat\"><span class=\"stat-label\">Posts</span><span class=\"stat-value\">{formatear_numero(perfil.get('total_posts'))}</span></div>
                    <div class=\"stat\"><span class=\"stat-label\">Tipo</span><span class=\"stat-value\">{'Negocio' if perfil.get('es_negocio') else 'Cuenta'}</span></div>
                </div>
            </div>
        </section>

        <h2 class=\"section-title\">Ultimas fotografias</h2>
        <section class=\"posts-grid\">
            {''.join(tarjetas_fotos)}
        </section>
    </main>
</body>
</html>
        """.strip()


# Script principal 

def main():
    # Validaciones básicas
    if not TARGET_USER:
        raise ValueError("Define TARGET_USER en el archivo .env")

    # 1. Cargar cookies y crear sesión autenticada
    print("Cargando cookies...")
    cookies = cargar_cookies(COOKIES_FILE)

    session = requests.Session()
    session.headers.update(HEADERS)
    session.cookies.update(cookies)

    # 2. Obtener datos del perfil objetivo
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

    # 3. Obtener las últimas 10 fotos del perfil objetivo
    print(f"Obteniendo últimas 10 fotografías de @{TARGET_USER}...")
    time.sleep(1)
    fotos = obtener_ultimas_fotos(session, perfil_objetivo["user_id"], cantidad=10)
    print(f"    {len(fotos)} fotografías obtenidas.")

    # 4. Guardar resultado
    resultado = {
        "perfil_objetivo":  perfil_objetivo,
        "ultimas_fotos":    fotos,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=4)

    dashboard_html = generar_dashboard_html(resultado)
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(dashboard_html)

    print(f"\nDatos guardados en '{OUTPUT_FILE}'")
    print(f"Dashboard generado en '{DASHBOARD_FILE}'")
    print(f"  Perfil objetivo: @{perfil_objetivo['username']}")
    print(f"  Fotos obtenidas: {len(fotos)}")


if __name__ == "__main__":
    main()