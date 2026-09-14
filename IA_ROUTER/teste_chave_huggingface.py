import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("HUGGINGFACE_API_KEY", "").strip()

print(
    "HUGGINGFACE_API_KEY:",
    "CONFIGURADA" if key else "AUSENTE"
)

if key:
    url = "https://router.huggingface.co/v1/models"

    r = requests.get(
        url,
        headers={
            "Authorization": f"Bearer {key}",
        },
        timeout=20,
    )

    print("STATUS:", r.status_code)

    if r.status_code == 200:
        print("HUGGING FACE: TOKEN ACEITO PELO ROUTER")
    else:
        print("HUGGING FACE: TOKEN SEM PERMISSAO ADEQUADA")
        print("ERRO:", r.text[:1000])
else:
    print("HUGGING FACE: nenhuma chave configurada.")
