import os
import requests
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("HUGGINGFACE_API_KEY", "").strip()

print()
print("=" * 72)
print("TESTE DE PERMISSAO — HUGGING FACE")
print("=" * 72)

headers = {
    "Authorization": f"Bearer {key}",
}

url = "https://huggingface.co/api/whoami-v2"

try:
    r = requests.get(
        url,
        headers=headers,
        timeout=30,
    )

    print("STATUS:", r.status_code)

    if r.ok:
        dados = r.json()

        print("USUARIO:", dados.get("name") or dados.get("fullname") or "não informado")
        print("ID     :", dados.get("id") or "não informado")

        auth = dados.get("auth", {})

        print()
        print("DADOS DE AUTORIZACAO:")

        if isinstance(auth, dict):
            for chave, valor in auth.items():
                nome = str(chave).lower()

                if "token" in nome or "secret" in nome or "key" in nome:
                    continue

                print(f"  {chave}: {valor}")

        print()
        print("HUGGING FACE: TOKEN ACEITO PELA CONTA")
    else:
        print("CORPO:", r.text[:2000])
        print()
        print("HUGGING FACE: FALHOU AO VALIDAR TOKEN")

except Exception as exc:
    print("ERRO:", repr(exc))

print("=" * 72)
