import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("NVIDIA_API_KEY", "").strip()
model = os.getenv("NVIDIA_MODEL", "").strip()

print()
print("=" * 72)
print("TESTE NVIDIA")
print("=" * 72)
print("CHAVE :", "CONFIGURADA" if key else "AUSENTE")
print("MODELO:", model)

url = "https://integrate.api.nvidia.com/v1/chat/completions"

payload = {
    "model": model,
    "messages": [
        {
            "role": "user",
            "content": "Responda somente: NVIDIA OK",
        }
    ],
    "temperature": 0.2,
    "max_tokens": 64,
}

try:
    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=30,
    )

    print("STATUS:", r.status_code)
    print("CORPO :", r.text[:2000])

    if r.ok:
        print()
        print("NVIDIA: APROVADA")
    else:
        print()
        print("NVIDIA: FALHOU")

except Exception as exc:
    print("ERRO:", repr(exc))

print("=" * 72)
