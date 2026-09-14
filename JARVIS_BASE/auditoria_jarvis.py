# -*- coding: utf-8 -*-

from pathlib import Path
import re
import ast
import sys

ROOT = Path(r"C:\Users\almei\JARVIS")

IGNORAR_DIRS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    "site-packages",
    "browser_profile",
    "chrome_jarvis",
    "dados_chrome",
    "dados_chromium",
}

IGNORAR_ARQUIVOS = {
    "auditoria_jarvis.py",
    "auditoria_jarvis_resultado.txt",
}

EXTENSOES = {
    ".py",
    ".txt",
    ".json",
    ".yaml",
    ".yml",
    ".ini",
    ".cfg",
    ".toml",
}

def ignorar(path):
    if any(parte in IGNORAR_DIRS for parte in path.parts):
        return True

    if path.name in IGNORAR_ARQUIVOS:
        return True

    nome = path.name.lower()

    if (
        "backup" in nome
        or nome.endswith(".bak")
        or nome.endswith(".old")
    ):
        return True

    return False


arquivos = []

for p in ROOT.rglob("*"):
    if not p.is_file():
        continue

    if ignorar(p):
        continue

    if p.suffix.lower() not in EXTENSOES:
        continue

    arquivos.append(p)


def mostrar(titulo):
    print()
    print("=" * 110)
    print(titulo)
    print("=" * 110)


def procurar(padroes, categorias=None):
    encontrados = []

    for arquivo in arquivos:
        try:
            texto = arquivo.read_text(
                encoding="utf-8",
                errors="replace"
            )
        except Exception:
            continue

        for numero, linha in enumerate(texto.splitlines(), 1):

            for categoria, lista in padroes.items():

                for padrao in lista:

                    if re.search(
                        padrao,
                        linha,
                        re.IGNORECASE
                    ):
                        encontrados.append(
                            (
                                categoria,
                                arquivo.relative_to(ROOT),
                                numero,
                                linha.strip()
                            )
                        )
                        break

    return encontrados


print("=" * 110)
print(" J.A.R.V.I.S - AUDITORIA FORENSE DE ORIGEM DOS ERROS")
print("=" * 110)

print()
print("RAIZ:", ROOT)
print("ARQUIVOS ANALISADOS:", len(arquivos))

# ------------------------------------------------------------------
# IDENTIDADE
# ------------------------------------------------------------------

mostrar("1. IDENTIDADE - CHATGPT / JARVIS / STRAK")

padroes_identidade = {
    "CHATGPT": [
        r"\bChatGPT\b",
        r"Sou o ChatGPT",
        r"Sou ChatGPT",
        r"meu nome.*ChatGPT",
        r"nome.*ChatGPT",
    ],

    "JARVIS": [
        r"\bJARVIS\b",
        r"Sou Jarvis",
        r"Sou JARVIS",
        r"meu nome.*Jarvis",
        r"nome.*Jarvis",
    ],

    "STRAK": [
        r"\bSTRAK\b",
        r"\bSTRAK-AI\b",
        r"Sou Strak",
        r"meu nome.*Strak",
        r"nome.*Strak",
    ],
}

for categoria, arquivo, numero, linha in procurar(
    padroes_identidade
):
    print(
        f"[{categoria}] "
        f"{arquivo}:{numero}: {linha}"
    )

# ------------------------------------------------------------------
# PROMPTS
# ------------------------------------------------------------------

mostrar("2. PROMPTS / PERSONALIDADE / SYSTEM")

padroes_prompt = {
    "PROMPT": [
        r"PROMPT",
        r"prompt",
        r"personalidade",
        r"PERSONALIDADE",
        r"system_prompt",
        r"system prompt",
        r"mensagem.*sistema",
        r"system.*message",
    ]
}

for categoria, arquivo, numero, linha in procurar(
    padroes_prompt
):
    print(
        f"{arquivo}:{numero}: {linha}"
    )

# ------------------------------------------------------------------
# GERADORES DE RESPOSTA
# ------------------------------------------------------------------

mostrar("3. PONTOS QUE PODEM GERAR RESPOSTAS")

padroes_resposta = {
    "IA": [
        r"\bperguntar\s*\(",
        r"\bexecutar_ia\s*\(",
        r"\bgerar_resposta\s*\(",
        r"\bgerar_resposta",
        r"\bresponder\s*\(",
        r"\bresponse\s*=",
        r"\bresposta\s*=",
        r"\banswer\s*=",
    ],

    "ROTEADOR": [
        r"\bIA_ROUTER\b",
        r"\brouter\b",
        r"\bprovedor\b",
        r"\bprovider\b",
    ],
}

for categoria, arquivo, numero, linha in procurar(
    padroes_resposta
):
    print(
        f"[{categoria}] "
        f"{arquivo}:{numero}: {linha}"
    )

# ------------------------------------------------------------------
# VOZ
# ------------------------------------------------------------------

mostrar("4. XTTS / TTS / FALA")

padroes_voz = {
    "XTTS": [
        r"\bXTTS\b",
        r"XTTS V2",
        r"xtts_v2",
        r"tts_to_file",
        r"get_conditioning_latents",
        r"tts_with_vc",
    ],

    "FALA": [
        r"\bfalar\s*\(",
        r"\bfala\s*\(",
        r"\bspeak\s*\(",
        r"\bsay\s*\(",
        r"pyttsx",
        r"sounddevice",
        r"soundfile",
    ],
}

for categoria, arquivo, numero, linha in procurar(
    padroes_voz
):
    print(
        f"[{categoria}] "
        f"{arquivo}:{numero}: {linha}"
    )

# ------------------------------------------------------------------
# MEMORIA
# ------------------------------------------------------------------

mostrar("5. MEMORIA / CHROMA / EMBEDDINGS")

padroes_memoria = {
    "CHROMA": [
        r"chromadb",
        r"BancoChroma",
        r"MemoriaChroma",
        r"Chroma",
    ],

    "EMBEDDING": [
        r"SentenceTransformer",
        r"MODELO_EMBEDDING",
        r"carregar_embedding",
        r"embedding_consulta",
        r"_embedding_passage",
    ],

    "MEMORIA": [
        r"memoria",
        r"Memoria",
        r"memorias",
    ],
}

for categoria, arquivo, numero, linha in procurar(
    padroes_memoria
):
    print(
        f"[{categoria}] "
        f"{arquivo}:{numero}: {linha}"
    )

# ------------------------------------------------------------------
# IMPORTS
# ------------------------------------------------------------------

mostrar("6. IMPORTS DOS MODULOS PRINCIPAIS")

for arquivo in arquivos:

    if arquivo.suffix.lower() != ".py":
        continue

    try:
        arvore = ast.parse(
            arquivo.read_text(
                encoding="utf-8",
                errors="replace"
            )
        )
    except Exception as erro:
        print(
            f"ERRO AST: "
            f"{arquivo.relative_to(ROOT)} -> {erro}"
        )
        continue

    imports = set()

    for node in ast.walk(arvore):

        if isinstance(node, ast.Import):

            for item in node.names:
                imports.add(item.name)

        elif isinstance(node, ast.ImportFrom):

            if node.module:
                imports.add(node.module)

    if imports:
        print()
        print(
            f"[{arquivo.relative_to(ROOT)}]"
        )

        for item in sorted(imports):
            print("  ->", item)

# ------------------------------------------------------------------
# HARDCODED
# ------------------------------------------------------------------

mostrar("7. TEXTOS HARDCODED DE IDENTIDADE")

termos = [
    "Sou o ChatGPT",
    "Sou ChatGPT",
    "Sou Jarvis",
    "Sou JARVIS",
    "Sou o Jarvis",
    "STRAK-AI",
    "Meu nome é",
    "meu nome é",
    "Seu nome é",
    "Sou ",
]

for arquivo in arquivos:

    if arquivo.suffix.lower() not in {
        ".py",
        ".txt",
    }:
        continue

    try:
        texto = arquivo.read_text(
            encoding="utf-8",
            errors="replace"
        )
    except Exception:
        continue

    for numero, linha in enumerate(
        texto.splitlines(),
        1
    ):

        for termo in termos:

            if termo.lower() in linha.lower():

                print(
                    f"{arquivo.relative_to(ROOT)}:"
                    f"{numero}: "
                    f"{linha.strip()}"
                )

                break

# ------------------------------------------------------------------
# CONFIGURAÇÃO DE IA
# ------------------------------------------------------------------

mostrar("8. MODELOS / PROVIDERS / CONFIGURACOES")

padroes_modelos = {
    "MODELO": [
        r"MODELO_",
        r"modelo\s*=",
        r"model\s*=",
        r"model_name",
    ],

    "PROVIDER": [
        r"provider",
        r"provedor",
        r"IA_ROUTER",
    ],

    "HUGGINGFACE": [
        r"HuggingFace",
        r"huggingface",
        r"hf_",
    ],

    "OPENAI": [
        r"OpenAI",
        r"openai",
    ],

    "ANTHROPIC": [
        r"Anthropic",
        r"anthropic",
    ],

    "GEMINI": [
        r"Gemini",
        r"gemini",
    ],

    "CHATGPT": [
        r"chatgpt",
        r"ChatGPT",
    ],
}

for categoria, arquivo, numero, linha in procurar(
    padroes_modelos
):
    print(
        f"[{categoria}] "
        f"{arquivo}:{numero}: {linha}"
    )

# ------------------------------------------------------------------
# RESUMO DE ARQUIVOS PRINCIPAIS
# ------------------------------------------------------------------

mostrar("9. ARQUIVOS PRINCIPAIS DO PIPELINE")

principais = [
    "jarvis.py",
    "memoria_chroma.py",
    "memoria_modelos.py",
    "memoria_retriever.py",
    "PROMPT_JARVIS.txt",
]

for nome in principais:

    caminho = ROOT / nome

    if caminho.exists():

        print(
            f"[EXISTE] {nome} "
            f"({caminho.stat().st_size} bytes)"
        )

    else:

        print(
            f"[NAO ENCONTRADO] {nome}"
        )

# ------------------------------------------------------------------
# ARQUIVOS DE BACKUP
# ------------------------------------------------------------------

mostrar("10. BACKUPS ENCONTRADOS - NAO PARTICIPAM DA EXECUCAO")

backups = []

for p in ROOT.rglob("*"):

    if not p.is_file():
        continue

    if any(
        parte in IGNORAR_DIRS
        for parte in p.parts
    ):
        continue

    nome = p.name.lower()

    if (
        "backup" in nome
        or nome.endswith(".bak")
        or nome.endswith(".old")
    ):
        backups.append(
            p.relative_to(ROOT)
        )

if backups:

    for item in sorted(backups):
        print(item)

else:

    print("Nenhum backup encontrado.")

# ------------------------------------------------------------------
# FINAL
# ------------------------------------------------------------------

mostrar("11. AUDITORIA CONCLUIDA")

print()
print(
    "IMPORTANTE:"
)
print(
    "Esta auditoria apenas LEU os arquivos."
)
print(
    "Nenhum arquivo do JARVIS foi alterado."
)
print()
print(
    "Quantidade de arquivos analisados:",
    len(arquivos)
)
print()
