import os
import requests


def deve_pesquisar(mensagem: str) -> bool:
    texto = str(
        mensagem or ""
    ).strip().lower()

    if not texto:
        return False

    pessoais = (
        "meu nome",
        "minha comida",
        "minha cor",
        "minha esposa",
        "meu trabalho",
        "minha profissão",
        "o que eu gosto",
        "qual meu",
        "qual minha",
        "quem sou eu",
    )

    if any(item in texto for item in pessoais):
        return False

    gatilhos = (
        "quem foi",
        "quem é",
        "o que é",
        "o que foi",
        "como funciona",
        "quando aconteceu",
        "onde fica",
        "por que",
        "porque",
        "qual é",
        "qual foi",
        "qual a",
        "qual o",
        "sobre ",
        "pesquise",
        "pesquisa",
        "procure",
        "notícia",
        "noticias",
        "atual",
        "hoje",
        "agora",
        "último",
        "última",
        "mais recente",
    )

    if any(gatilho in texto for gatilho in gatilhos):
        return True

    return "?" in texto


def pesquisar_web(
    consulta: str,
    limite: int = 5,
) -> list[dict]:
    chave = os.getenv(
        "BRAVE_SEARCH_API_KEY",
        "",
    ).strip()

    if not chave:
        return []

    try:
        resposta = requests.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={
                "Accept": "application/json",
                "X-Subscription-Token": chave,
            },
            params={
                "q": consulta,
                "count": limite,
                "search_lang": "pt-br",
                "country": "br",
                "safesearch": "moderate",
            },
            timeout=15,
        )

        resposta.raise_for_status()

        dados = resposta.json()

        resultados = []

        for item in (
            dados.get("web", {}).get(
                "results",
                []
            )
        )[:limite]:
            resultados.append({
                "title": str(
                    item.get("title", "")
                ).strip(),
                "url": str(
                    item.get("url", "")
                ).strip(),
                "description": str(
                    item.get("description", "")
                ).strip(),
            })

        return resultados

    except Exception:
        return []


def montar_contexto_web(
    resultados: list[dict],
) -> str:
    if not resultados:
        return ""

    partes = [
        "CONTEXTO DE PESQUISA WEB DO J.A.R.V.I.S.",
        "Use estas fontes para responder com informações "
        "atualizadas e verificáveis.",
        "",
    ]

    for indice, item in enumerate(
        resultados,
        start=1,
    ):
        partes.append(
            f"[FONTE {indice}] "
            f"{item.get('title', '')}"
        )

        partes.append(
            f"URL: {item.get('url', '')}"
        )

        descricao = item.get(
            "description",
            "",
        )

        if descricao:
            partes.append(
                f"Resumo: {descricao}"
            )

        partes.append("")

    return "\n".join(partes)
