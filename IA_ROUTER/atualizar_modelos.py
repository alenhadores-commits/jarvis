from pathlib import Path

p = Path("api_router.py")
s = p.read_text(encoding="utf-8")

alteracoes = {
    "gemini-3.7-flash": "gemini-3.8-flash",
    "meta/llama-3.1-8b-instruct": "meta/llama-3.3-70b-instruct",
    "openai/gpt-oss-120b:fastest": "deepseek-ai/DeepSeek-V3-0324",
}

for antigo, novo in alteracoes.items():
    if antigo in s:
        s = s.replace(antigo, novo)
        print(f"[ALTERADO] {antigo} -> {novo}")
    else:
        print(f"[NAO ENCONTRADO] {antigo}")

p.write_text(s, encoding="utf-8")

print()
print("Modelos atualizados.")
