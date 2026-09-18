import re, sys

path = r".\IA_ROUTER\api_router.py"

with open(path, "r", encoding="utf-8", newline="") as f:
    conteudo = f.read()

padrao = re.compile(
    r'if system_messages:\s*\n'
    r'\s*system = compact_dialogue_text\(\s*\n'
    r'\s*system_messages\[0\]\.get\("content", ""\),\s*\n'
    r'\s*max_chars=min\(8000, DIALOGUE_MAX_CHARS \* 2\),\s*\n'
    r'\s*\)\s*\n'
    r'\s*\n'
    r'\s*system = f"\{system\}\\n\\n\{DIALOGUE_STYLE\}"'
)

novo_bloco = (
    'if system_messages:\n'
    '        estilo_len = len(DIALOGUE_STYLE)\n'
    '        limite_total = min(8000, DIALOGUE_MAX_CHARS * 2)\n'
    '        orcamento_contexto = max(200, limite_total - estilo_len - 2)\n'
    '\n'
    '        system = compact_dialogue_text(\n'
    '            system_messages[0].get("content", ""),\n'
    '            max_chars=orcamento_contexto,\n'
    '        )\n'
    '\n'
    '        system = f"{system}\\n\\n{DIALOGUE_STYLE}"'
)

resultado, n = padrao.subn(novo_bloco, conteudo, count=1)

if n == 0:
    print("ERRO: padrao nao encontrado. Nenhuma alteracao feita.")
    sys.exit(1)

with open(path + ".bak2", "w", encoding="utf-8", newline="") as f:
    f.write(conteudo)

with open(path, "w", encoding="utf-8", newline="") as f:
    f.write(resultado)

print(f"OK: patch aplicado ({n} substituicao). Backup em {path}.bak2")
