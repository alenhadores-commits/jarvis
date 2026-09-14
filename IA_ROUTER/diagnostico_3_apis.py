import os
import requests
from dotenv import load_dotenv

load_dotenv()

MENSAGENS = [
    {
        "role": "user",
        "content": "Responda somente: OK",
    }
]

print()
print("=" * 78)
print("DIAGNOSTICO DIRETO DAS APIS")
print("=" * 78)

# ============================================================
# GEMINI
# ============================================================

print()
print("-" * 78)
print("GEMINI")
print("-" * 78)

gemini_key = os.getenv("GEMINI_API_KEY")
gemini_model = os.getenv("GEMINI_MODEL")

gemini_url = (
    "https://generativelanguage.googleapis.com"
    "/v1beta/openai/chat/completions"
)

gemini_payload = {
    "model": gemini_model,
    "messages": MENSAGENS,
}

try:
    r = requests.post(
        gemini_url,
        headers={
            "Authorization": f"Bearer {gemini_key}",
            "Content-Type": "application/json",
        },
        json=gemini_payload,
        timeout=30,
    )

    print("URL    :", gemini_url)
    print("MODELO :", gemini_model)
    print("STATUS :", r.status_code)
    print("CORPO  :", r.text[:2000])

except Exception as exc:
    print("ERRO   :", repr(exc))


# ============================================================
# NVIDIA
# ============================================================

print()
print("-" * 78)
print("NVIDIA")
print("-" * 78)

nvidia_key = os.getenv("NVIDIA_API_KEY")
nvidia_model = os.getenv("NVIDIA_MODEL")

nvidia_url = (
    "https://integrate.api.nvidia.com"
    "/v1/chat/completions"
)

nvidia_payload = {
    "model": nvidia_model,
    "messages": MENSAGENS,
    "temperature": 0.2,
    "max_tokens": 64,
}

try:
    r = requests.post(
        nvidia_url,
        headers={
            "Authorization": f"Bearer {nvidia_key}",
            "Content-Type": "application/json",
        },
        json=nvidia_payload,
        timeout=30,
    )

    print("URL    :", nvidia_url)
    print("MODELO :", nvidia_model)
    print("STATUS :", r.status_code)
    print("CORPO  :", r.text[:2000])

except Exception as exc:
    print("ERRO   :", repr(exc))


# ============================================================
# HUGGING FACE
# ============================================================

print()
print("-" * 78)
print("HUGGING FACE")
print("-" * 78)

hf_key = os.getenv("HUGGINGFACE_API_KEY")
hf_model = os.getenv("HUGGINGFACE_MODEL")

hf_url = (
    "https://router.huggingface.co"
    "/v1/chat/completions"
)

hf_payload = {
    "model": hf_model,
    "messages": MENSAGENS,
    "max_tokens": 64,
}

try:
    r = requests.post(
        hf_url,
        headers={
            "Authorization": f"Bearer {hf_key}",
            "Content-Type": "application/json",
        },
        json=hf_payload,
        timeout=30,
    )

    print("URL    :", hf_url)
    print("MODELO :", hf_model)
    print("STATUS :", r.status_code)
    print("CORPO  :", r.text[:2000])

except Exception as exc:
    print("ERRO   :", repr(exc))


print()
print("=" * 78)
print("FIM DO DIAGNOSTICO")
print("=" * 78)
