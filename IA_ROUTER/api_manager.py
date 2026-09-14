import os
import sys
import json
import requests
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

ROUTER_URL = os.getenv("ROUTER_URL", "http://127.0.0.1:8765").rstrip("/")
ROUTER_API_KEY = os.getenv("ROUTER_API_KEY", "").strip()


PROVIDERS = {
    "groq": {
        "key": "GROQ_API_KEY",
        "model": "GROQ_MODEL",
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "openai/gpt-oss-120b",
    },
    "gemini": {
        "key": "GEMINI_API_KEY",
        "model": "GEMINI_MODEL",
        "base_url": "https://generativelanguage.googleapis.com/v1beta",
        "default_model": "gemini-3.8-flash",
    },
    "openrouter": {
        "key": "OPENROUTER_API_KEY",
        "model": "OPENROUTER_MODEL",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "nvidia/nemotron-3.5-lightning:free",
    },
    "nvidia": {
        "key": "NVIDIA_API_KEY",
        "model": "NVIDIA_MODEL",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "default_model": "openai/gpt-oss-20b",
    },
    "huggingface": {
        "key": "HUGGINGFACE_API_KEY",
        "model": "HUGGINGFACE_MODEL",
        "base_url": "https://router.huggingface.co/v1",
        "default_model": "deepseek-ai/DeepSeek-V3-0324",
    },
    "cohere": {
        "key": "COHERE_API_KEY",
        "model": "COHERE_MODEL",
        "base_url": "https://api.cohere.com/compatibility/v1",
        "default_model": "command-a-plus-05-2026",
    },
}


def carregar_env():
    if not ENV_PATH.exists():
        return {}

    dados = {}

    for linha in ENV_PATH.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()

        if not linha or linha.startswith("#") or "=" not in linha:
            continue

        chave, valor = linha.split("=", 1)
        dados[chave.strip()] = valor.strip().strip('"').strip("'")

    return dados


def salvar_env(dados):
    linhas = []

    for chave, valor in dados.items():
        linhas.append(f"{chave}={valor}")

    ENV_PATH.write_text(
        "\n".join(linhas) + "\n",
        encoding="utf-8",
    )


def definir_env(chave, valor):
    dados = carregar_env()
    dados[chave] = valor
    salvar_env(dados)


def remover_env(chave):
    dados = carregar_env()

    if chave in dados:
        del dados[chave]

    salvar_env(dados)


def headers():
    h = {}

    if ROUTER_API_KEY:
        h["Authorization"] = f"Bearer {ROUTER_API_KEY}"

    return h


def listar():
    print("\n============================================================")
    print(" APIS CONFIGURADAS")
    print("============================================================")

    dados = carregar_env()

    for nome, cfg in PROVIDERS.items():
        key = dados.get(cfg["key"], "").strip()
        model = dados.get(cfg["model"], cfg["default_model"])

        status = "CONFIGURADA" if key else "SEM API KEY"

        print(
            f"{nome:<14} {status:<14} "
            f"modelo={model}"
        )

    print()


def configurar():
    print("\n============================================================")
    print(" ADICIONAR / CONFIGURAR API")
    print("============================================================")

    nome = input("Nome da API/provedor: ").strip().lower()

    if not nome:
        print("Nome obrigatório.")
        return

    if nome not in PROVIDERS:
        print("\nProvedor ainda não está cadastrado no Router.")
        print("Provedores disponíveis:")

        for p in PROVIDERS:
            print(f"  - {p}")

        print(
            "\nPara adicionar um provedor novo à arquitetura, "
            "primeiro é necessário cadastrá-lo no api_router.py."
        )
        return

    cfg = PROVIDERS[nome]

    print(f"\nAPI selecionada: {nome}")

    api_key = input("API Key: ").strip()

    if not api_key:
        print("API Key obrigatória.")
        return

    modelo_atual = carregar_env().get(
        cfg["model"],
        cfg["default_model"],
    )

    modelo = input(
        f"Nome do modelo [{modelo_atual}]: "
    ).strip()

    if not modelo:
        modelo = modelo_atual

    definir_env(cfg["key"], api_key)
    definir_env(cfg["model"], modelo)
    definir_env(f"{nome.upper()}_ENABLED", "true")

    print("\n[OK] API configurada.")
    print(f"     Provedor: {nome}")
    print(f"     Modelo:   {modelo}")
    print("\nIMPORTANTE: reinicie o IA_ROUTER para carregar a nova configuração.")


def ativar():
    nome = input("Provedor: ").strip().lower()

    if nome not in PROVIDERS:
        print("Provedor não encontrado.")
        return

    definir_env(f"{nome.upper()}_ENABLED", "true")

    print(f"[OK] {nome} ativado.")
    print("Reinicie o IA_ROUTER para aplicar.")


def remover():
    nome = input("Provedor: ").strip().lower()

    if nome not in PROVIDERS:
        print("Provedor não encontrado.")
        return

    cfg = PROVIDERS[nome]

    remover_env(cfg["key"])
    remover_env(cfg["model"])
    definir_env(f"{nome.upper()}_ENABLED", "false")

    print(f"[OK] Configuração de {nome} removida.")
    print("Reinicie o IA_ROUTER para aplicar.")


def status():
    try:
        r = requests.get(
            f"{ROUTER_URL}/status",
            headers=headers(),
            timeout=10,
        )

        r.raise_for_status()

        dados = r.json()

        print(json.dumps(
            dados,
            indent=2,
            ensure_ascii=False,
        ))

        return dados

    except Exception as e:
        print(f"[ERRO] Status: {e}")
        return None


def consumo():
    try:
        r = requests.get(
            f"{ROUTER_URL}/usage",
            headers=headers(),
            timeout=10,
        )

        r.raise_for_status()

        dados = r.json()

        print("\n============================================================")
        print(" CONSUMO")
        print("============================================================")

        print(json.dumps(
            dados,
            indent=2,
            ensure_ascii=False,
        ))

        return dados

    except Exception as e:
        print(f"[ERRO] Consumo: {e}")
        return None


def testar():
    print("\n============================================================")
    print(" TESTE DA IA ROUTER")
    print("============================================================")

    payload = {
        "messages": [
            {
                "role": "user",
                "content": "Responda apenas: OK",
            }
        ],
        "max_tokens": 8,
    }

    try:
        r = requests.post(
            f"{ROUTER_URL}/v1/chat/completions",
            headers={
                **headers(),
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=60,
        )

        print("HTTP:", r.status_code)

        dados = r.json()

        print(json.dumps(
            dados,
            indent=2,
            ensure_ascii=False,
        ))

    except Exception as e:
        print(f"[ERRO] Teste: {e}")


def registrar_quota_router(resultado):
    if not resultado:
        return

    try:
        r = requests.post(
            f"{ROUTER_URL}/quota",
            headers={
                **headers(),
                "Content-Type": "application/json",
            },
            json=resultado,
            timeout=10,
        )

        if r.ok:
            print("[OK] Quota registrada no Router.")
        else:
            print(
                f"[INFO] Router recusou quota: "
                f"HTTP {r.status_code}"
            )

    except Exception as e:
        print(f"[INFO] Não foi possível registrar quota: {e}")


def verificar_quota_provedor(nome):
    nome = nome.lower().strip()

    if nome not in PROVIDERS:
        print(f"[ERRO] Provedor desconhecido: {nome}")
        return None

    cfg = PROVIDERS[nome]
    env = carregar_env()

    api_key = env.get(cfg["key"], "").strip()
    modelo = env.get(cfg["model"], cfg["default_model"])

    if not api_key:
        print(f"[ERRO] {nome}: API Key não configurada.")
        return None

    print("\n============================================================")
    print(f" QUOTA / FREE TIER: {nome.upper()}")
    print("============================================================")
    print(f"Modelo: {modelo}")

    resultado = {
        "provider": nome,
        "model": modelo,
        "checked_at": datetime.now().isoformat(),
        "quota_found": False,
        "source": None,
        "period": None,
        "remaining_tokens": None,
        "limit_tokens": None,
        "remaining_requests": None,
        "limit_requests": None,
        "reset": None,
        "raw": None,
    }

    # --------------------------------------------------------
    # Tentativa 1: endpoint de modelos/conta do próprio serviço
    # --------------------------------------------------------

    try:
        if nome in {
            "groq",
            "openrouter",
            "nvidia",
            "huggingface",
            "cohere",
        }:
            url = cfg["base_url"].rstrip("/") + "/models"

            r = requests.get(
                url,
                headers={
                    "Authorization": f"Bearer {api_key}",
                },
                timeout=20,
            )

            print(f"\nConsulta da API: HTTP {r.status_code}")

            for k, v in r.headers.items():
                lk = k.lower()

                if "ratelimit" in lk or "rate-limit" in lk:
                    print(f"Header quota: {k} = {v}")

                    if "remaining" in lk:
                        resultado["quota_found"] = True
                        resultado["source"] = "headers"

                        if "token" in lk:
                            try:
                                resultado["remaining_tokens"] = float(v)
                            except Exception:
                                pass

                        if "request" in lk:
                            try:
                                resultado["remaining_requests"] = float(v)
                            except Exception:
                                pass

                    elif "limit" in lk:
                        resultado["quota_found"] = True
                        resultado["source"] = "headers"

                        if "token" in lk:
                            try:
                                resultado["limit_tokens"] = float(v)
                            except Exception:
                                pass

                        if "request" in lk:
                            try:
                                resultado["limit_requests"] = float(v)
                            except Exception:
                                pass

                    elif "reset" in lk:
                        resultado["reset"] = v

            if r.status_code == 200:
                resultado["raw"] = "endpoint /models respondeu normalmente"

    except Exception as e:
        print(f"Consulta direta não disponível: {e}")

    # --------------------------------------------------------
    # Tentativa 2: Gemini possui usageMetadata nas respostas
    # --------------------------------------------------------

    if nome == "gemini":
        try:
            url = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{modelo}:generateContent?key={api_key}"
            )

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": "Responda apenas OK."
                            }
                        ]
                    }
                ]
            }

            r = requests.post(
                url,
                json=payload,
                timeout=30,
            )

            print(f"\nConsulta Gemini: HTTP {r.status_code}")

            dados = r.json()

            usage = dados.get("usageMetadata", {})

            if usage:
                resultado["quota_found"] = True
                resultado["source"] = "Gemini usageMetadata"

                resultado["raw"] = usage

                print("usageMetadata encontrado:")
                print(json.dumps(
                    usage,
                    indent=2,
                    ensure_ascii=False,
                ))

        except Exception as e:
            print(f"Consulta Gemini falhou: {e}")

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    print("\n------------------------------------------------------------")
    print(" RESULTADO DA DESCOBERTA")
    print("------------------------------------------------------------")

    if resultado["quota_found"]:
        print("[OK] A API forneceu informações de consumo/quota.")
    else:
        print("[INFO] A API não forneceu quota gratuita diretamente.")
        print("       O Router NÃO vai inventar um limite.")

    registrar_quota_router(resultado)

    print(
        "Tokens restantes:",
        resultado["remaining_tokens"]
    )

    print(
        "Limite de tokens:",
        resultado["limit_tokens"]
    )

    print(
        "Requests restantes:",
        resultado["remaining_requests"]
    )

    print(
        "Limite de requests:",
        resultado["limit_requests"]
    )

    print(
        "Período:",
        resultado["period"] or "não informado"
    )

    print(
        "Reset:",
        resultado["reset"] or "não informado"
    )

    print(
        "Fonte:",
        resultado["source"] or "não informado"
    )

    return resultado


def verificar_quota():
    print("\n============================================================")
    print(" DESCOBRIR QUOTA / FREE TIER")
    print("============================================================")

    print("Provedores:")

    for nome in PROVIDERS:
        print(f"  - {nome}")

    nome = input("\nProvedor: ").strip().lower()

    verificar_quota_provedor(nome)

def verificar_quota_todos():
    resultados = []

    for nome in PROVIDERS:
        try:
            resultado = verificar_quota_provedor(nome)

            if resultado:
                resultados.append(resultado)

        except Exception as e:
            print(f"[ERRO] {nome}: {e}")

    print("\n============================================================")
    print(" RESUMO DE QUOTAS")
    print("============================================================")

    for r in resultados:
        print(
            f"{r['provider']:<14} "
            f"tokens={r['remaining_tokens']} "
            f"requests={r['remaining_requests']} "
            f"periodo={r['period'] or 'desconhecido'}"
        )


def menu():
    while True:
        print("\n============================================================")
        print(" IA ROUTER - GERENCIADOR")
        print("============================================================")
        print("[1] Listar APIs")
        print("[2] Adicionar / configurar API")
        print("[3] Ativar API")
        print("[4] Remover API")
        print("[5] Testar Router")
        print("[6] Verificar quota")
        print("[7] Verificar quota de todas")
        print("[8] Consumo")
        print("[9] Status")
        print("[0] Sair")

        opcao = input("\nEscolha: ").strip()

        if opcao == "1":
            listar()

        elif opcao == "2":
            configurar()

        elif opcao == "3":
            ativar()

        elif opcao == "4":
            remover()

        elif opcao == "5":
            testar()

        elif opcao == "6":
            verificar_quota()

        elif opcao == "7":
            verificar_quota_todos()

        elif opcao == "8":
            consumo()

        elif opcao == "9":
            status()

        elif opcao == "0":
            break

        else:
            print("Opção inválida.")


if __name__ == "__main__":
    menu()

