from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

DADOS = ROOT / "dados"

CHROMA_PATH = DADOS / "chromadb"

COLLECTIONS = {
    "memorias": "jarvis_memorias",
    "experiencias": "jarvis_experiencias",
    "conhecimento": "jarvis_conhecimento",
    "codigo": "jarvis_codigo",
    "documentacao": "jarvis_documentacao",
    "erros": "jarvis_erros",
    "procedimentos": "jarvis_procedimentos",
    "projetos": "jarvis_projetos",
    "conversas": "jarvis_conversas",
    "aprendizado": "jarvis_aprendizado",
}

DEFAULT_TOP_K = 5

MAX_RESULTS = 20

CHUNK_SIZE = 1800

CHUNK_OVERLAP = 250

EXTENSOES_CODIGO = {
    ".py",
    ".js",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ps1",
    ".bat",
    ".cmd",
    ".md",
    ".txt",
}

IGNORAR_DIRETORIOS = {
    ".git",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "node_modules",
    ".idea",
    ".vscode",
    "backup",
    "backups",
}

VERSAO = "1.0.0"
