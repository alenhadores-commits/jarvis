import os
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests


UNLOB_URL = "https://api.unlob.com/search"
FREE_SERP_URL = "https://freeserp.ai/api.php"


# ============================================================
# UTILITARIOS
# ============================================================

def _texto(valor) -> str:
    return str(valor or "").strip()


def _data_unlob(valor) -> str:
    if valor in (None, ""):
        return ""

    try:
        if isinstance(valor, (int, float)):
            return datetime.fromtimestamp(
                float(valor),
                tz=timezone.utc,
            ).date().isoformat()

        texto = str(valor).strip()

        if texto.isdigit():
            return datetime.fromtimestamp(
                float(texto),
                tz=timezone.utc,
            ).date().isoformat()

        return texto[:10]

    except Exception:
        return ""


def _dominio(
    url: str,
    fallback: str = "",
) -> str:
    if fallback:
        return fallback.strip()

    try:
        return urlparse(url).netloc
    except Exception:
        return ""


def _valido(item: dict) -> bool:
    if not isinstance(item, dict):
        return False

    return bool(
        _texto(item.get("title"))
        or _texto(item.get("url"))
        or _texto(item.get("description"))
        or _texto(item.get("content"))
    )


# ============================================================
# PROVEDOR 1 — UNLOB
# ============================================================

def pesquisar_unlob(
    consulta: str,
    limite: int = 5,
    dias: int | None = None,
) -> list[dict]:

    chave = os.getenv(
        "UNLOB_API_KEY",
        "",
    ).strip()

    if not chave:
        print(
            "JARVIS WEB: Unlob indisponivel "
            "(UNLOB_API_KEY nao configurada)"
        )
        return []

    try:
        resposta = requests.get(
            UNLOB_URL,
            headers={
                "x-api-key": chave,
            },
            params={
                "q": consulta,
                "mode": "hybrid",
                "limit": max(limite, 5),
                "collapse": "page",
            },
            timeout=20,
        )

        resposta.raise_for_status()

        dados = resposta.json()

        resultados = dados.get(
            "results",
            [],
        )

        if not isinstance(
            resultados,
            list,
        ):
            return []

        finais = []

        for item in resultados:

            if not isinstance(
                item,
                dict,
            ):
                continue

            titulo = _texto(
                item.get("title")
            )

            url = _texto(
                item.get("url")
            )

            descricao = _texto(
                item.get("snippet")
                or item.get("description")
            )

            dominio = _texto(
                item.get("host")
            )

            publicada = _data_unlob(
                item.get("published_at")
            )

            resultado = {
                "title": titulo,
                "url": url,
                "description": descricao,
                "content": descricao,
                "domain": _dominio(
                    url,
                    dominio,
                ),
                "published": publicada,
                "source_date": publicada,
                "provider": "unlob",
            }

            if _valido(resultado):
                finais.append(resultado)

        print(
            "JARVIS WEB: Unlob -> "
            f"{len(finais)} resultados"
        )

        return finais[:limite]

    except Exception as erro:

        print(
            f"JARVIS WEB: falha Unlob: {erro}"
        )

        return []


# ============================================================
# PROVEDOR 2 — TAVILY
# ============================================================

def pesquisar_tavily(
    consulta: str,
    limite: int = 5,
    dias: int | None = None,
) -> list[dict]:

    chave = os.getenv(
        "TAVILY_API_KEY",
        "",
    ).strip()

    if not chave:
        print(
            "JARVIS WEB: Tavily indisponivel "
            "(TAVILY_API_KEY nao configurada)"
        )
        return []

    try:

        from tavily import TavilyClient

        cliente = TavilyClient(
            api_key=chave
        )

        argumentos = {
            "query": consulta,
            "search_depth": "basic",
            "max_results": max(
                limite,
                5,
            ),
            "include_answer": False,
            "include_raw_content": False,
        }

        if dias is not None:
            argumentos["days"] = dias

        dados = cliente.search(
            **argumentos
        )

        resultados = dados.get(
            "results",
            [],
        )

        if not isinstance(
            resultados,
            list,
        ):
            return []

        finais = []

        for item in resultados:

            if not isinstance(
                item,
                dict,
            ):
                continue

            titulo = _texto(
                item.get("title")
            )

            url = _texto(
                item.get("url")
            )

            conteudo = _texto(
                item.get("content")
            )

            publicada = _texto(
                item.get("published_date")
            )

            resultado = {
                "title": titulo,
                "url": url,
                "description": conteudo,
                "content": conteudo,
                "domain": _dominio(url),
                "published": publicada,
                "source_date": publicada[:10],
                "provider": "tavily",
            }

            if _valido(resultado):
                finais.append(resultado)

        print(
            "JARVIS WEB: Tavily -> "
            f"{len(finais)} resultados"
        )

        return finais[:limite]

    except Exception as erro:

        print(
            f"JARVIS WEB: falha Tavily: {erro}"
        )

        return []


# ============================================================
# PROVEDOR 3 — LANGCHAIN / DUCKDUCKGO
# ============================================================

def pesquisar_langchain(
    consulta: str,
    limite: int = 5,
    dias: int | None = None,
) -> list[dict]:

    try:

        from langchain_community.tools import (
            DuckDuckGoSearchResults,
        )

        ferramenta = DuckDuckGoSearchResults(
            max_results=max(
                limite,
                5,
            ),
            output_format="list",
        )

        dados = ferramenta.invoke(
            consulta
        )

        if not isinstance(
            dados,
            list,
        ):
            return []

        finais = []

        for item in dados:

            if not isinstance(
                item,
                dict,
            ):
                continue

            titulo = _texto(
                item.get("title")
            )

            url = _texto(
                item.get("link")
                or item.get("url")
            )

            descricao = _texto(
                item.get("snippet")
                or item.get("description")
            )

            resultado = {
                "title": titulo,
                "url": url,
                "description": descricao,
                "content": descricao,
                "domain": _dominio(url),
                "published": "",
                "source_date": "",
                "provider": "langchain",
            }

            if _valido(resultado):
                finais.append(resultado)

        print(
            "JARVIS WEB: LangChain/DuckDuckGo -> "
            f"{len(finais)} resultados"
        )

        return finais[:limite]

    except Exception as erro:

        print(
            f"JARVIS WEB: falha LangChain: {erro}"
        )

        return []


# ============================================================
# PROVEDOR 4 — FREESERP
# ============================================================

def pesquisar_freeserp(
    consulta: str,
    limite: int = 5,
    dias: int | None = None,
) -> list[dict]:

    try:

        resposta = requests.get(
            FREE_SERP_URL,
            params={
                "q": consulta,
                "size": max(
                    limite,
                    10,
                ),
                "content": 1,
                "content_max": 12000,
            },
            timeout=20,
        )

        resposta.raise_for_status()

        dados = resposta.json()

        resultados_brutos = dados.get(
            "results",
            [],
        )

        if not isinstance(
            resultados_brutos,
            list,
        ):
            return []

        finais = []

        for item in resultados_brutos:

            if not isinstance(
                item,
                dict,
            ):
                continue

            titulo = _texto(
                item.get("title")
            )

            url = _texto(
                item.get("url")
            )

            conteudo = _texto(
                item.get("content")
            )

            resumo = _texto(
                item.get("ai_summary")
                or item.get("summary")
                or item.get("description")
            )

            dominio = _texto(
                item.get("domain")
            )

            publicada = _texto(
                item.get("published")
                or item.get("date")
                or item.get("went_live")
            )

            resultado = {
                "title": titulo,
                "url": url,
                "description": resumo,
                "content": conteudo,
                "domain": _dominio(
                    url,
                    dominio,
                ),
                "published": publicada,
                "source_date": publicada,
                "provider": "freeserp",
            }

            if _valido(resultado):
                finais.append(resultado)

        print(
            "JARVIS WEB: FreeSerp -> "
            f"{len(finais)} resultados"
        )

        return finais[:limite]

    except Exception as erro:

        print(
            f"JARVIS WEB: falha FreeSerp: {erro}"
        )

        return []


# ============================================================
# REGISTRO CENTRAL
# ============================================================
#
# A ORDEM DEFINE O FALLBACK.
#
# Para adicionar outro provedor:
#
# 1. crie pesquisar_novo_provedor()
# 2. garanta a assinatura:
#
#       consulta
#       limite
#       dias
#
# 3. adicione UMA linha abaixo.
#
# NENHUMA alteracao em pesquisa_web.py sera necessaria.
# ============================================================

PROVEDORES = [
    (
        "Unlob",
        pesquisar_unlob,
    ),
    (
        "Tavily",
        pesquisar_tavily,
    ),
    (
        "LangChain",
        pesquisar_langchain,
    ),
    (
        "FreeSerp",
        pesquisar_freeserp,
    ),
]


# ============================================================
# EXECUTOR GENERICO DE FALLBACK
# ============================================================

def pesquisar_com_fallback(
    consultas: list[str],
    limite: int = 5,
    temporal: bool = False,
    verificar_atualidade=None,
) -> list[dict]:

    limite_busca = max(
        limite,
        10,
    )

    dias = (
        7
        if temporal
        else None
    )

    for nome, funcao in PROVEDORES:

        print(
            "JARVIS WEB: tentando provedor -> "
            f"{nome}"
        )

        for consulta in consultas:

            try:

                resultados = funcao(
                    consulta,
                    limite=limite_busca,
                    dias=dias,
                )

            except Exception as erro:

                print(
                    "JARVIS WEB: erro no "
                    f"provedor {nome}: {erro}"
                )

                resultados = []

            if not resultados:
                continue

            validos = [
                item
                for item in resultados
                if _valido(item)
            ]

            if not validos:
                continue

            if (
                temporal
                and verificar_atualidade is not None
                and not verificar_atualidade(
                    validos,
                    dias_maximos=7,
                )
            ):

                print(
                    "JARVIS WEB: "
                    f"{nome} retornou "
                    "fontes desatualizadas"
                )

                continue

            print(
                "JARVIS WEB: provedor "
                "selecionado -> "
                f"{nome}"
            )

            return validos

    print(
        "JARVIS WEB: nenhum provedor "
        "retornou resultados validos"
    )

    return []


# ============================================================
# INFORMACAO DO REGISTRO
# ============================================================

def listar_provedores() -> list[str]:
    return [
        nome
        for nome, _ in PROVEDORES
    ]
