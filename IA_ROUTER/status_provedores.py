from dotenv import load_dotenv
import os

load_dotenv()

APROVADOS = {
    "groq",
    "openrouter",
    "cohere",
    "nvidia",
}

PENDENTES = {
    "cerebras",
    "gemini",
    "mistral",
    "huggingface",
    "sambanova",
}

MODELOS = {
    "groq": os.getenv("GROQ_MODEL", ""),
    "openrouter": os.getenv("OPENROUTER_MODEL", ""),
    "cohere": os.getenv("COHERE_MODEL", ""),
    "nvidia": os.getenv("NVIDIA_MODEL", ""),
    "cerebras": os.getenv("CEREBRAS_MODEL", ""),
    "gemini": os.getenv("GEMINI_MODEL", ""),
    "mistral": os.getenv("MISTRAL_MODEL", ""),
    "huggingface": os.getenv("HUGGINGFACE_MODEL", ""),
    "sambanova": os.getenv("SAMBANOVA_MODEL", ""),
}

print()
print("=" * 72)
print("POOL OFICIAL IA_ROUTER")
print("=" * 72)

print()
print("APROVADOS:")
for nome in sorted(APROVADOS):
    print(f"  [OK] {nome:<12} {MODELOS.get(nome, '')}")

print()
print("PENDENTES:")
for nome in sorted(PENDENTES):
    print(f"  [..] {nome:<12} {MODELOS.get(nome, '')}")

print()
print("TOTAL APROVADOS :", len(APROVADOS))
print("TOTAL PENDENTES :", len(PENDENTES))
print("=" * 72)
