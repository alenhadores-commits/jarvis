import requests
import unicodedata


FREE_SERP_URL = "https://freeserp.ai/api.php"


def normalizar(texto: str) -> str:
    texto = str(texto or "").lower()
    texto = unicodedata.normalize(
        "NFKD",
        texto,
    )
    return "".join(
        c
        for c in texto
        if not unicodedata.combining(c)
    )


def deve_pesquisar(mensagem: str) -> bool:
    texto = str(
        mensagem or ""
    ).strip()

    if not texto:
        return False

    normalizado = normalizar(texto)

    pessoais = (
        "meu nome",
        "minha comida",
        "minha cor",
        "minha esposa",
        "meu trabalho",
        "minha profissao",
        "o que eu gosto",
        "qual meu",
        "qual minha",
        "quem sou eu",
    )

    if any(
        item in normalizado
        for item in pessoais
    ):
        return False

    # Perguntas factuais comuns.
    gatilhos = (
        "quem ",
        "qual ",
        "onde ",
        "quando ",
        "como ",
        "por que ",
        "porque ",
        "o que ",
        "pesquise",
        "pesquisa",
        "procure",
        "noticia",
        "noticias",
        "atual",
        "hoje",
        "agora",
        "ultimo",
        "ultima",
        "proximo",
        "proxima",
        "jogo",
        "partida",
        "palmeiras",
        "corinthians",
        "flamengo",
        "futebol",
    )

    if any(
        gatilho in normalizado
        for gatilho in gatilhos
    ):
        return True

    if "?" in texto:
        return True

    return False


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

        resultados_brutos = dados.get(
            "results",
            [],
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
                    "",
                )
            ).strip()

            url = str(
                item.get(
                    "url",
                    "",
                )
            ).strip()

            resumo = str(
                item.get(
                    "ai_summary",
                    item.get(
                        "summary",
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

            publicada = str(
                item.get(
                    "went_live",
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
                "published": publicada,
            })

        return resultados

    except Exception as erro:
        print(
            f"JARVIS WEB: falha FreeSerp: {erro}"
        )
        return []


def montar_contexto_web(
    resultados: list[dict],
) -> str:
    if not resultados:
        return ""

    partes = [
        "CONTEXTO DE PESQUISA WEB DO J.A.R.V.I.S.",
        "Os resultados abaixo vieram do FreeSerp.",
        "Use-os para responder perguntas sobre fatos externos.",
        "Quando houver fontes, baseie a resposta nelas.",
        "Não invente dados que não estejam nas fontes.",
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

        if item.get("domain"):
            partes.append(
                f"Domínio: {item['domain']}"
            )

        if item.get("published"):
            partes.append(
                f"Data: {item['published']}"
            )

        if item.get("url"):
            partes.append(
                f"URL: {item['url']}"
            )

        if item.get("description"):
            partes.append(
                f"Resumo: {item['description']}"
            )

        partes.append("")

    return "\n".join(partes)
