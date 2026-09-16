import requests
import unicodedata


FREE_SERP_URL = "https://freeserp.ai/api.php"


def normalizar(texto: str) -> str:
    texto = str(texto or "").lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )


def preparar_consulta(consulta: str) -> list[str]:
    original = " ".join(str(consulta or "").split()).strip()

    if not original:
        return []

    sem_prefixo = original

    prefixos = (
        "qual ",
        "quem ",
        "onde ",
        "quando ",
        "como ",
        "por que ",
        "porque ",
        "o que ",
        "me diga ",
        "me mostre ",
        "pesquise ",
        "pesquisa ",
        "procure ",
        "quero saber ",
    )

    for prefixo in prefixos:
        if sem_prefixo.lower().startswith(prefixo):
            sem_prefixo = sem_prefixo[len(prefixo):].strip()
            break

    palavras = [
        palavra
        for palavra in sem_prefixo.split()
        if palavra.lower() not in {
            "o", "a", "os", "as",
            "do", "da", "dos", "das",
            "de", "em", "no", "na",
            "um", "uma", "e",
        }
    ]

    consultas = []

    def adicionar(valor: str):
        valor = " ".join(str(valor or "").split()).strip()
        if valor and valor not in consultas:
            consultas.append(valor)

    adicionar(original)

    clubes = (
        "Palmeiras",
        "Corinthians",
        "Flamengo",
        "Santos",
        "São Paulo",
        "Vasco",
        "Grêmio",
        "Internacional",
        "Cruzeiro",
        "Atlético Mineiro",
        "Botafogo",
        "Fluminense",
        "Bahia",
        "Fortaleza",
    )

    termos = {
        "proximo": "próximo",
        "proxima": "próxima",
        "ultimo": "último",
        "ultima": "última",
        "noticias": "notícias",
        "noticia": "notícia",
        "ultimos": "últimos",
        "ultimas": "últimas",
        "jogos": "jogos",
        "futebol": "futebol",
    }

    palavras_acentuadas = [
        termos.get(
            palavra.lower(),
            palavra,
        )
        for palavra in palavras
    ]

    consulta_acentuada = " ".join(palavras_acentuadas)

    if consulta_acentuada:
        for clube in clubes:
            clube_norm = normalizar(clube)

            if clube_norm in normalizar(consulta_acentuada):
                restantes = [
                    palavra
                    for palavra in palavras_acentuadas
                    if normalizar(palavra) != clube_norm
                ]

                if restantes:
                    adicionar(
                        f"{clube} {' '.join(restantes)}"
                    )

                break

        adicionar(consulta_acentuada)
        adicionar(" ".join(palavras))

    return consultas

def deve_pesquisar(mensagem: str) -> bool:
    texto = str(mensagem or "").strip()

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

    if any(item in normalizado for item in pessoais):
        return False

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

    if any(gatilho in normalizado for gatilho in gatilhos):
        return True

    return "?" in texto


def pesquisar_web(
    consulta: str,
    limite: int = 5,
) -> list[dict]:
    consultas = preparar_consulta(consulta)

    if not consultas:
        return []

    for tentativa, consulta_teste in enumerate(consultas, start=1):
        try:
            resposta = requests.get(
                FREE_SERP_URL,
                params={
                    "q": consulta_teste,
                    "size": limite,
                },
                timeout=20,
            )

            resposta.raise_for_status()
            dados = resposta.json()

            resultados_brutos = dados.get("results", [])

            if not isinstance(resultados_brutos, list):
                continue

            resultados = []

            for item in resultados_brutos[:limite]:
                if not isinstance(item, dict):
                    continue

                titulo = str(
                    item.get("title", "")
                ).strip()

                url = str(
                    item.get("url", "")
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
                    item.get("domain", "")
                ).strip()

                publicada = str(
                    item.get(
                        "published",
                        item.get(
                            "date",
                            item.get(
                                "went_live",
                                "",
                            ),
                        ),
                    )
                ).strip()

                if not (titulo or url or resumo):
                    continue

                resultados.append({
                    "title": titulo,
                    "url": url,
                    "description": resumo,
                    "domain": dominio,
                    "published": publicada,
                })

            if resultados:
                if tentativa > 1:
                    print(
                        f"JARVIS WEB: consulta ajustada -> {consulta_teste}"
                    )
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




