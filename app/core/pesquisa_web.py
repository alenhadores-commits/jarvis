import requests


FREE_SERP_URL = "https://freeserp.ai/api.php"


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

    if any(
        item in texto
        for item in pessoais
    ):
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

    if any(
        gatilho in texto
        for gatilho in gatilhos
    ):
        return True

    return "?" in texto


def pesquisar_web(
    consulta: str,
    limite: int = 5,
) -> list[dict]:
    consulta = str(
        consulta or ""
    ).strip()

    if not consulta:
        return []

    try:
        resposta = requests.get(
            FREE_SERP_URL,
            params={
                "q": consulta,
                "size": limite,
            },
            timeout=20,
        )

        resposta.raise_for_status()

        dados = resposta.json()

        if not isinstance(
            dados,
            dict,
        ):
            return []

        resultados_brutos = (
            dados.get("results")
            or dados.get("data")
            or dados.get("items")
            or []
        )

        if not isinstance(
            resultados_brutos,
            list,
        ):
            return []

        resultados = []

        for item in resultados_brutos[:limite]:
            if not isinstance(
                item,
                dict,
            ):
                continue

            titulo = str(
                item.get(
                    "title",
                    item.get(
                        "name",
                        "",
                    ),
                )
            ).strip()

            url = str(
                item.get(
                    "url",
                    item.get(
                        "link",
                        "",
                    ),
                )
            ).strip()

            resumo = str(
                item.get(
                    "summary",
                    item.get(
                        "snippet",
                        item.get(
                            "description",
                            "",
                        ),
                    ),
                )
            ).strip()

            dominio = str(
                item.get(
                    "domain",
                    "",
                )
            ).strip()

            data_publicacao = str(
                item.get(
                    "published_at",
                    item.get(
                        "published",
                        item.get(
                            "date",
                            "",
                        ),
                    ),
                )
            ).strip()

            if not (
                titulo
                or url
                or resumo
            ):
                continue

            resultados.append({
                "title": titulo,
                "url": url,
                "description": resumo,
                "domain": dominio,
                "published": data_publicacao,
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
        "Abaixo estão resultados do FreeSerp.",
        "Use-os como fonte externa para responder.",
        "Não invente informações que não estejam "
        "presentes nas fontes.",
        "",
    ]

    for indice, item in enumerate(
        resultados,
        start=1,
    ):
        titulo = item.get(
            "title",
            "",
        )

        url = item.get(
            "url",
            "",
        )

        resumo = item.get(
            "description",
            "",
        )

        dominio = item.get(
            "domain",
            "",
        )

        publicada = item.get(
            "published",
            "",
        )

        partes.append(
            f"[FONTE {indice}] {titulo}"
        )

        if dominio:
            partes.append(
                f"Domínio: {dominio}"
            )

        if publicada:
            partes.append(
                f"Data: {publicada}"
            )

        if url:
            partes.append(
                f"URL: {url}"
            )

        if resumo:
            partes.append(
                f"Resumo: {resumo}"
            )

        partes.append("")

    return "\n".join(partes)
