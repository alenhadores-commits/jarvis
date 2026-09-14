from pathlib import Path

p = Path(".env")
s = p.read_text(encoding="utf-8")

antigo = "NVIDIA_MODEL=meta/llama-3.3-70b-instruct"
novo = "NVIDIA_MODEL=openai/gpt-oss-120b"

if antigo in s:
    s = s.replace(antigo, novo)
    print("[NVIDIA] modelo atualizado:")
    print("         openai/gpt-oss-120b")
else:
    print("[NVIDIA] modelo antigo não encontrado.")
    print("[NVIDIA] verificaremos o valor atual.")

p.write_text(s, encoding="utf-8")
