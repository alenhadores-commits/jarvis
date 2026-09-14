from pathlib import Path
import re

p = Path("api_router.py")
s = p.read_text(encoding="utf-8")

# ============================================================
# ALTERAR SOMENTE OS 7 PROVEDORES COM FALHA
# ============================================================

# Gemini
s = re.sub(
    r'("GEMINI_MODEL"\s*,\s*)"[^"]+"',
    r'\1"gemini-3.8-flash"',
    s,
    count=1,
)

# NVIDIA
s = re.sub(
    r'("NVIDIA_MODEL"\s*,\s*)"[^"]+"',
    r'\1"meta/llama-3.3-70b-instruct"',
    s,
    count=1,
)

# Hugging Face
s = re.sub(
    r'("HUGGINGFACE_MODEL"\s*,\s*)"[^"]+"',
    r'\1"deepseek-ai/DeepSeek-V3-0324"',
    s,
    count=1,
)

# ============================================================
# COHERE
# ============================================================
# O 422 pode estar vindo de parâmetro incompatível.
# Para este teste, não enviaremos reasoning_effort.
# Nenhum outro provedor é afetado.

s = s.replace(
'''    elif cfg.name == "cohere":
        payload["reasoning_effort"] = "none"
''',
'''    elif cfg.name == "cohere":
        payload.pop("reasoning_effort", None)
        payload.pop("reasoning", None)
        payload.pop("include_reasoning", None)
''',
1,
)

p.write_text(s, encoding="utf-8")

print("PATCH APLICADO")
print("Arquivo:", p)
print("Backup :", "$backup")
