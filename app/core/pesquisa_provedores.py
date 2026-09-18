import os
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import urlparse

import requests


def _texto(valor):
    if valor is None:
        return ""
    return str(valor).strip()


def _data_unlob(valor):
    if not valor:
        return None

    texto = _texto(valor)

    try:
        if texto.endswith("Z"):
            texto = texto[:-1] + "+00:00"

        data = datetime.fromisoformat(texto)

        if data.tzinfo is None:
            data = data.replace(tzinfo=timezone.utc)

        return data
    except Exception:
        return None


def _dominio(url):
    try:
        return urlparse(_texto(url)).netloc.lower()
    except Exception:
        return ""


def _valido(item):
    if not isinstance(item, dict):
        return False

    url = _texto(item.get("url"))

    if not url:
        return False

    if not url.startswith(("http://", "https://")):
        return False

    return True


def _normalizar_texto(valor):
    texto = _texto(valor).lower()

    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )

    texto = re.sub(r"[^a-z0-9\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto)

    return texto.strip()


def _termos_relevantes(consulta):
    stopwords = {
        "qual",
        "quais",
        "que",
        "quem",
        "onde",
        "quando",
        "como",
        "porque",
        "por",
        "para",
        "com",
        "sem",
        "uma",
        "umas",
        "um",
        "uns",
        "o",
        "a",
        "os",
        "as",
        "do",
        "da",
        "dos",
        "das",
        "de",
        "no",
        "na",
        "nos",
        "nas",
        "e",
        "ou",
        "em",
        "ao",
        "aos",
        "se",
        "me",
        "te",
        "seu",
        "sua",
        "seus",
        "suas",
        "proximo",
        "proxima",
        "atual",
        "agora",
        "hoje",
    }

    tokens = _normalizar_texto(consulta).split()

    resultado = []

    for token in tokens:
        if len(token) < 3:
            continue

        if token in stopwords:
            continue

        if token not in resultado:
            resultado.append(token)

    return resultado


def _texto_resultado(item):
    partes = [
        item.get("title"),
        item.get("description"),
        item.get("snippet"),
        item.get("content"),
        item.get("url"),
        item.get("domain"),
    ]

    return _normalizar_texto(" ".join(_texto(parte) for parte in partes))


def _pontuacao_relevancia(consulta, item):
    termos = _termos_relevantes(consulta)

    titulo = _normalizar_texto(item.get("title"))
    descricao = _normalizar_texto(item.get("description"))
    snippet = _normalizar_texto(item.get("snippet"))
    conteudo = _normalizar_texto(item.get("content"))
    url = _normalizar_texto(item.get("url"))

    pontuacao = 0

    for termo in termos:
        if termo in titulo:
            pontuacao += 4
            continue

        if termo in descricao or termo in snippet:
            pontuacao += 2
            continue

        if termo in conteudo:
            pontuacao += 1
            continue

        if termo in url:
            pontuacao += 1

    return pontuacao


def _parece_consulta_evento_futuro(consulta):
    texto = _normalizar_texto(consulta)

    indicadores = {
        "proximo",
        "proxima",
        "seguinte",
        "proximos",
        "proximas",
        "quando sera",
        "quando vai",
        "quando acontece",
        "data do",
        "data da",
        "horario do",
        "horario da",
    }

    return any(indicador in texto for indicador in indicadores)


def _tem_evidencia_evento_futuro(consulta, item):
    texto = _texto_resultado(item)

    if not texto:
        return False

    # Datas explícitas:
    # 20/09/2026
    # 20-09-2026
    # 20.09.2026
    data_numerica = re.search(
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        texto,
    )

    # Datas por extenso:
    # 20 setembro 2026
    meses = (
        "janeiro",
        "fevereiro",
        "marco",
        "abril",
        "maio",
        "junho",
        "julho",
        "agosto",
        "setembro",
        "outubro",
        "novembro",
        "dezembro",
    )

    data_extenso = any(
        re.search(
            rf"\b\d{{1,2}}\s+{mes}\s+\d{{4}}\b",
            texto,
        )
        for mes in meses
    )

    # Horários:
    # 11:00 / 20h30 / 20h
    horario = bool(
        re.search(
            r"\b\d{1,2}(?::\d{2}|h\d{0,2})\b",
            texto,
        )
    )

    indicadores_evento = [
        "jogo",
        "partida",
        "confronto",
        "enfrenta",
        "enfrentara",
        "x ",
        "versus",
        "vs ",
        "estadio",
        "arena",
        "rodada",
        "campeonato",
        "competicao",
        "show",
        "evento",
        "voo",
        "embarque",
        "chegada",
    ]

    possui_evento = any(
        indicador in texto
        for indicador in indicadores_evento
    )

    return (
        (data_numerica or data_extenso or horario)
        and possui_evento
    )


def _qualidade_resultados(consulta, resultados):
    validos = [
        item
        for item in resultados
        if _valido(item)
    ]

    if not validos:
        return False, 0.0

    termos = _termos_relevantes(consulta)

    if not termos:
        return True, 100.0

    pontuacoes = [
        _pontuacao_relevancia(consulta, item)
        for item in validos
    ]

    relevantes = [
        item
        for item, pontuacao in zip(validos, pontuacoes)
        if pontuacao >= 3
    ]

    percentual = (
        len(relevantes) / len(validos)
    ) * 100

    melhor_pontuacao = max(
        pontuacoes,
        default=0,
    )

    if melhor_pontuacao < 3:
        return False, percentual

    # Para consultas sobre eventos futuros,
    # relevância lexical sozinha não basta.
    if _parece_consulta_evento_futuro(consulta):
        evidencias = [
            item
            for item in relevantes
            if _tem_evidencia_evento_futuro(
                consulta,
                item,
            )
        ]

        percentual_evidencia = (
            len(evidencias) / len(validos)
        ) * 100

        print(
            "JARVIS WEB: "
            f"Evidencia de evento -> "
            f"{percentual_evidencia:.0f}%"
        )

        # Exige pelo menos uma evidência concreta
        # e, com 3+ resultados, pelo menos 20%.
        if not evidencias:
            return False, percentual_evidencia

        if len(validos) >= 3 and percentual_evidencia < 20:
            return False, percentual_evidencia

        return True, percentual_evidencia

    if len(validos) >= 3 and percentual < 20:
        return False, percentual

    return True, percentual


def _aceitar_resultados(consulta, resultados):
    aprovado, percentual = _qualidade_resultados(
        consulta,
        resultados,
    )

    estado = "APROVADO" if aprovado else "REJEITADO"

    print(
        "JARVIS WEB: "
        f"Quality Gate -> {estado} "
        f"({percentual:.0f}% relevantes)"
    )

    return aprovado


def pesquisar_unlob(
    consulta: str,
    limite: int = 5,
    dias: int | None = None,
):
    chave = os.getenv("UNLOB_API_KEY")

    if not chave:
        print("JARVIS WEB: Unlob -> API key ausente")
        return []

    try:
        resposta = requests.get(
            "https://api.unlob.com/search",
            headers={
                "x-api-key": chave,
            },
            params={
                "q": consulta,
                "mode": "hybrid",
                "limit": max(limite, 5),
                "collapse": "page",
            },
            timeout=30,
        )

        resposta.raise_for_status()

        dados = resposta.json()

        if isinstance(dados, dict):
            resultados_brutos = (
                dados.get("results")
                or dados.get("data")
                or []
            )
        elif isinstance(dados, list):
            resultados_brutos = dados
        else:
            resultados_brutos = []

        resultados = []

        for item in resultados_brutos:
            if not isinstance(item, dict):
                continue

            url = (
                item.get("url")
                or item.get("link")
                or ""
            )

            titulo = (
                item.get("title")
                or ""
            )

            descricao = (
                item.get("snippet")
                or item.get("description")
                or ""
            )

            resultados.append(
                {
                    "title": _texto(titulo),
                    "url": _texto(url),
                    "description": _texto(descricao),
                    "snippet": _texto(
                        item.get("snippet")
                    ),
                    "content": _texto(
                        item.get("content")
                    ),
                    "domain": _dominio(url),
                    "published_at": _data_unlob(
                        item.get("published_at")
                        or item.get("published")
                        or item.get("date")
                    ),
                    "provider": "unlob",
                    "fetched_at": datetime.now(
                        timezone.utc
                    ),
                }
            )

        return resultados

    except Exception as erro:
        print(
            "JARVIS WEB: "
            f"Unlob erro -> {erro}"
        )
        return []


def pesquisar_tavily(
    consulta: str,
    limite: int = 5,
    dias: int | None = None,
):
    chave = os.getenv("TAVILY_API_KEY")

    if not chave:
        print("JARVIS WEB: Tavily -> API key ausente")
        return []

    try:
        from tavily import TavilyClient

        cliente = TavilyClient(
            api_key=chave
        )

        parametros = {
            "query": consulta,
            "search_depth": "basic",
            "max_results": max(limite, 5),
            "include_answer": False,
            "include_raw_content": False,
        }

        if dias is not None:
            parametros["days"] = dias

        resposta = cliente.search(
            **parametros
        )

        resultados = []

        for item in resposta.get(
            "results",
            [],
        ):
            url = _texto(
                item.get("url")
            )

            resultados.append(
                {
                    "title": _texto(
                        item.get("title")
                    ),
                    "url": url,
                    "description": _texto(
                        item.get("content")
                    ),
                    "snippet": _texto(
                        item.get("content")
                    ),
                    "content": _texto(
                        item.get("content")
                    ),
                    "domain": _dominio(url),
                    "published_at": None,
                    "provider": "tavily",
                    "fetched_at": datetime.now(
                        timezone.utc
                    ),
                }
            )

        return resultados

    except Exception as erro:
        print(
            "JARVIS WEB: "
            f"Tavily erro -> {erro}"
        )
        return []


def pesquisar_langchain(
    consulta: str,
    limite: int = 5,
    dias: int | None = None,
):
    try:
        from langchain_community.tools import (
            DuckDuckGoSearchResults,
        )

        ferramenta = DuckDuckGoSearchResults(
            output_format="list"
        )

        dados = ferramenta.invoke(
            consulta
        )

        if not isinstance(dados, list):
            return []

        resultados = []

        for item in dados[: max(limite, 5)]:
            if not isinstance(item, dict):
                continue

            url = _texto(
                item.get("link")
                or item.get("url")
            )

            resultados.append(
                {
                    "title": _texto(
                        item.get("title")
                    ),
                    "url": url,
                    "description": _texto(
                        item.get("snippet")
                        or item.get("description")
                    ),
                    "snippet": _texto(
                        item.get("snippet")
                    ),
                    "content": _texto(
                        item.get("snippet")
                    ),
                    "domain": _dominio(url),
                    "published_at": None,
                    "provider": "langchain",
                    "fetched_at": datetime.now(
                        timezone.utc
                    ),
                }
            )

        return resultados

    except Exception as erro:
        print(
            "JARVIS WEB: "
            f"LangChain erro -> {erro}"
        )
        return []


def pesquisar_freeserp(
    consulta: str,
    limite: int = 5,
    dias: int | None = None,
):
    try:
        resposta = requests.get(
            "https://freeserp.ai/api.php",
            params={
                "q": consulta,
            },
            timeout=30,
        )

        resposta.raise_for_status()

        dados = resposta.json()

        if isinstance(dados, dict):
            brutos = (
                dados.get("results")
                or dados.get("organic_results")
                or []
            )
        elif isinstance(dados, list):
            brutos = dados
        else:
            brutos = []

        resultados = []

        for item in brutos[: max(limite, 5)]:
            if not isinstance(item, dict):
                continue

            url = _texto(
                item.get("url")
                or item.get("link")
            )

            resultados.append(
                {
                    "title": _texto(
                        item.get("title")
                    ),
                    "url": url,
                    "description": _texto(
                        item.get("snippet")
                        or item.get("description")
                    ),
                    "snippet": _texto(
                        item.get("snippet")
                    ),
                    "content": _texto(
                        item.get("content")
                    ),
                    "domain": _dominio(url),
                    "published_at": None,
                    "provider": "freeserp",
                    "fetched_at": datetime.now(
                        timezone.utc
                    ),
                }
            )

        return resultados

    except Exception as erro:
        print(
            "JARVIS WEB: "
            f"FreeSerp erro -> {erro}"
        )
        return []


PROVEDORES = [
    ("Unlob", pesquisar_unlob),
    ("Tavily", pesquisar_tavily),
    ("LangChain", pesquisar_langchain),
    ("FreeSerp", pesquisar_freeserp),
]


def pesquisar_com_fallback(
    consultas,
    limite: int = 5,
    temporal: bool = False,
    verificar_atualidade=None,
):
    for consulta in consultas:
        for nome, funcao in PROVEDORES:
            print(
                "JARVIS WEB: "
                f"tentando provedor -> {nome}"
            )

            try:
                resultados = funcao(
                    consulta,
                    limite=limite,
                )
            except TypeError:
                resultados = funcao(
                    consulta,
                    limite,
                )
            except Exception as erro:
                print(
                    "JARVIS WEB: "
                    f"{nome} erro -> {erro}"
                )
                continue

            print(
                "JARVIS WEB: "
                f"{nome} -> "
                f"{len(resultados)} resultados"
            )

            validos = [
                item
                for item in resultados
                if _valido(item)
            ]

            if not validos:
                print(
                    "JARVIS WEB: "
                    f"{nome} sem resultados validos"
                )
                continue

            if not _aceitar_resultados(
                consulta,
                validos,
            ):
                print(
                    "JARVIS WEB: "
                    f"{nome} rejeitado pelo "
                    "Quality Gate"
                )
                continue

            if (
                temporal
                and verificar_atualidade is not None
            ):
                try:
                    atual = verificar_atualidade(
                        validos,
                        dias_maximos=7,
                    )
                except TypeError:
                    atual = verificar_atualidade(
                        validos
                    )
                except Exception as erro:
                    print(
                        "JARVIS WEB: "
                        "erro verificando atualidade -> "
                        f"{erro}"
                    )
                    atual = False

                if not atual:
                    print(
                        "JARVIS WEB: "
                        f"{nome} rejeitado por "
                        "atualidade"
                    )
                    continue

            print(
                "JARVIS WEB: "
                f"provedor selecionado -> {nome}"
            )

            return validos[:limite]

    print(
        "JARVIS WEB: "
        "nenhum provedor conseguiu resultados validos"
    )

    return []
