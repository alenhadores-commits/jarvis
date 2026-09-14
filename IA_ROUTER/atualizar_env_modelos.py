from pathlib import Path

p = Path(".env")
s = p.read_text(encoding="utf-8")

alteracoes = {
    "GEMINI_MODEL=gemini-3.7-flash": "GEMINI_MODEL=gemini-3.8-flash",
    "NVIDIA_MODEL=meta/llama-3.1-8b-instruct": "NVIDIA_MODEL=meta/llama-3.3-70b-instruct",
    "HUGGINGFACE_MODEL=openai/gpt-oss-120b:fastest": "HUGGINGFACE_MODEL=deepseek-ai/DeepSeek-V3-0324",
}

for antigo, novo in alteracoes.items():
    if antigo in s:
        s = s.replace(antigo, novo)
        print(f"[ALTERADO] {novo}")
    else:
        print(f"[NAO ENCONTRADO] {antigo}")

p.write_text(s, encoding="utf-8")

print()
print("ENV ATUALIZADO.")
