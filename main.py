import os
import requests
from dotenv import load_dotenv

load_dotenv()

username = os.getenv("TARGET_USER")
url = f"https://www.instagram.com/{username}/"

headers = {
    "User-Agent": "Mozilla/5.0"
}

r = requests.get(url, headers=headers, timeout=20)

print("status:", r.status_code)
print(r.text[:500])