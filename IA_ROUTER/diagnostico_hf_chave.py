import os
from dotenv import load_dotenv

load_dotenv()

key = os.getenv("HUGGINGFACE_API_KEY", "").strip()

print()
print("=" * 72)
print("DIAGNOSTICO HUGGING FACE")
print("=" * 72)

print("CHAVE CONFIGURADA:", bool(key))
print("TAMANHO DA CHAVE :", len(key))

if key:
    print("PREFIXO          :", key[:8] + "...")
    print("SUFIXO           :", "..." + key[-4:])

    if key.startswith("hf_"):
        print("FORMATO           : token Hugging Face válido")
    else:
        print("FORMATO           : inesperado")
else:
    print("FORMATO           : nenhuma chave encontrada")

print()
print("IMPORTANTE:")
print("A chave NAO será exibida.")
print("Nenhum token será enviado para este terminal além da própria API.")
print("=" * 72)
