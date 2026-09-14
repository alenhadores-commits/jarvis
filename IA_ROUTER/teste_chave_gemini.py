import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("GEMINI_API_KEY", "").strip()

print("GEMINI_API_KEY:", "CONFIGURADA" if key else "AUSENTE")

if key:
    url = (
        "https://generativelanguage.googleapis.com"
        "/v1beta/openai/models/gemini-3.8-flash"
    )

    r = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {key}",
        },
        timeout=20,
    )

    print("STATUS:", r.status_code)

    if r.status_code == 200:
        print("GEMINI: CHAVE ACEITA")
    else:
        print("GEMINI: CHAVE RECUSADA")
        print("ERRO:", r.text[:1000])
else:
    print("GEMINI: nenhuma chave configurada.")
