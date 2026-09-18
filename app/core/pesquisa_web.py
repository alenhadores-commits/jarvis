from datetime import datetime, timezone
import re
import requests
import unicodedata
import xml.etree.ElementTree as ET
from urllib.parse import quote
from email.utils import parsedate_to_datetime
from html import unescape


FREE_SERP_URL = "https://freeserp.ai/api.php"


def normalizar(texto: str) -> str:
    texto = str(texto or "").lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(
        c for c in texto
        if not unicodedata.combining(c)
    )



def limpar_html(texto: str) -> str:
    texto = re.sub(r'<[^>]+>', ' ', str(texto or ''))
    texto = unescape(texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto


def consulta_temporal(consulta: str) -> bool:
    texto = normalizar(consulta)

    return any(
        termo in texto
        for termo in (
            "proximo",
            "proxima",
            "proximos",
            "proximas",
            "amanha",
            "ultimo",
            "ultima",
            "ultimos",
            "ultimas",
            "hoje",
            "agora",
            "atual",
        )
    )


def consulta_evento_futuro(consulta: str) -> bool:
    texto = normalizar(consulta)

    return any(
        termo in texto
        for termo in (
            "proximo",
            "proxima",
            "proximos",
            "proximas",
            "amanha",
        )
    )


def consulta_atualidade(consulta: str) -> bool:
    texto = normalizar(consulta)

    return any(
        termo in texto
        for termo in (
            "hoje",
            "agora",
            "atual",
        )
    )


def consulta_passado_recente(consulta: str) -> bool:
    texto = normalizar(consulta)

    return any(
        termo in texto
        for termo in (
            "ultimo",
            "ultima",
            "ultimos",
            "ultimas",
            "ontem",
        )
    )


def pesquisar_google_news(
    consulta: str,
    limite: int = 5,
) -> list[dict]:
    consulta_google = consulta

    if consulta_temporal(consulta) and not consulta_evento_futuro(consulta):
        from datetime import datetime, timedelta

        ontem = (
            datetime.now().date()
            - timedelta(days=1)
        )

        consulta_google = (
            consulta
            + " after:"
            + ontem.isoformat()
        )

    url = (
        "https://news.google.com/rss/search?q="
        + quote(consulta_google)
        + "&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    )

    resposta = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20,
    )
    resposta.raise_for_status()

    raiz = ET.fromstring(resposta.text)
    resultados = []

    for item in raiz.findall("./channel/item")[:max(limite, 10)]:
        titulo = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        resumo = limpar_html((item.findtext("description") or "").strip())
        publicada = (item.findtext("pubDate") or "").strip()

        data_iso = ""

        try:
            data_iso = (
                parsedate_to_datetime(publicada)
                .date()
                .isoformat()
            )
        except Exception:
            pass

        fonte = item.find("source")
        dominio = ""

        if fonte is not None:
            dominio = (
                fonte.get("url")
                or ""
            ).strip()

        if titulo or link or resumo:
            resultados.append(
                {
                    "title": titulo,
                    "url": link,
                    "description": resumo,
                    "content": resumo,
                    "domain": dominio,
                    "published": publicada,
                    "source_date": data_iso,
                }
            )

    return resultados


def preparar_consulta(
    consulta: str,
) -> list[str]:
    consulta_original = str(consulta or "").strip()

    if not consulta_original:
        return []

    consulta_normalizada = normalizar(
        consulta_original
    ).strip()

    if not consulta_normalizada:
        return []

    temporal = consulta_temporal(
        consulta_normalizada
    )

    base = re.sub(
        r"[^\w?-?\s]",
        " ",
        consulta_normalizada,
        flags=re.UNICODE,
    )

    base = re.sub(
        r"\s+",
        " ",
        base,
    ).strip()

    if not base:
        return []

    stopwords = {
        "qual",
        "quem",
        "onde",
        "quando",
        "como",
        "por",
        "que",
        "porque",
        "o",
        "a",
        "os",
        "as",
        "um",
        "uma",
        "uns",
        "umas",
        "do",
        "da",
        "dos",
        "das",
        "de",
        "em",
        "no",
        "na",
        "nos",
        "nas",
        "para",
        "pra",
        "com",
        "e",
    }

    palavras = [
        p
        for p in base.split()
        if p not in stopwords
    ]

    if not palavras:
        return [base]

    consultas = []

    def adicionar(valor: str):
        valor = re.sub(
            r"\s+",
            " ",
            str(valor or ""),
        ).strip()

        if valor and valor not in consultas:
            consultas.append(valor)

    adicionar(base)

    if temporal:
        hoje = datetime.now().date()

        ano = hoje.year
        mes = hoje.strftime("%B")

        termos_sem_temporal = [
            p
            for p in palavras
            if p not in {
                "proximo",
                "proxima",
                "proximos",
                "proximas",
                "amanha",
                "ultimo",
                "ultima",
                "ultimos",
                "ultimas",
                "ontem",
                "hoje",
                "agora",
                "atual",
            }
        ]

        base_forte = " ".join(
            termos_sem_temporal
        ).strip()

        if base_forte:

            if consulta_evento_futuro(consulta_normalizada):
                adicionar(
                    f"{base_forte} proximo jogo"
                )

                adicionar(
                    f"{base_forte} proximos jogos"
                )

                adicionar(
                    f"{base_forte} proxima partida"
                )

                adicionar(
                    f"{base_forte} proximo adversario"
                )

                adicionar(
                    f"{base_forte} agenda jogos"
                )

                adicionar(
                    f"{base_forte} calendario"
                )

                adicionar(
                    f"{base_forte} {mes} {ano}"
                )

                adicionar(
                    f"{base_forte} jogos {ano}"
                )

            elif consulta_passado_recente(consulta_normalizada):
                adicionar(
                    f"{base_forte} ultimo jogo"
                )

                adicionar(
                    f"{base_forte} resultado"
                )

                adicionar(
                    f"{base_forte} jogo anterior"
                )

                adicionar(
                    f"{base_forte} {mes} {ano}"
                )

            elif consulta_atualidade(consulta_normalizada):
                adicionar(
                    f"{base_forte} {mes} {ano}"
                )

                adicionar(
                    f"{base_forte} noticias recentes"
                )

    else:
        adicionar(
            " ".join(palavras)
        )

    return consultas[:8]


def pontuar_resultado(
    item: dict,
    termos_busca: list[str],
) -> int:
    titulo = normalizar(
        item.get("title", "")
    )

    url = normalizar(
        item.get("url", "")
    )

    dominio = normalizar(
        item.get("domain", "")
    )

    resumo = normalizar(
        item.get("description", "")
    )

    conteudo = normalizar(
        item.get("content", "")
    )

    texto = " ".join(
        [
            titulo,
            url,
            dominio,
            resumo,
            conteudo,
        ]
    )

    pontos = 0

    termos = []

    for termo in termos_busca:
        termo = normalizar(
            str(termo or "")
        ).strip()

        if termo and termo not in termos:
            termos.append(termo)

    for termo in termos:
        if termo in titulo:
            pontos += 18
        elif termo in resumo:
            pontos += 5
        elif termo in dominio:
            pontos += 4
        elif termo in url:
            pontos += 3
        elif termo in texto:
            pontos += 1

    temporal = any(
        termo in texto
        for termo in (
            "proximo",
            "proxima",
            "proximos",
            "proximas",
            "agenda",
            "calendario",
            "partida",
            "jogo",
            "confronto",
            "adversario",
        )
    )

    palmeiras = "palmeiras" in texto

    if palmeiras:
        pontos += 20

        if "palmeiras" in titulo:
            pontos += 20

    palavras_jogo = (
        "proximo",
        "proxima",
        "proximos",
        "proximas",
        "proximo jogo",
        "proximos jogos",
        "proxima partida",
        "proximas partidas",
        "proximo adversario",
        "agenda",
        "calendario",
        "jogo",
        "partida",
        "confronto",
    )

    encontrou_intencao_jogo = any(
        termo in texto
        for termo in palavras_jogo
    )

    if encontrou_intencao_jogo:
        pontos += 15

        if any(
            termo in titulo
            for termo in (
                "proximo",
                "proxima",
                "proximos",
                "proximas",
                "jogo",
                "partida",
                "agenda",
                "calendario",
                "confronto",
            )
        ):
            pontos += 25

    if (
        palmeiras
        and "jogo" in texto
        and any(
            termo in texto
            for termo in (
                "proximo",
                "proxima",
                "proximos",
                "proximas",
                "agenda",
                "calendario",
                "partida",
                "confronto",
                "adversario",
            )
        )
    ):
        pontos += 35

    historico = any(
        termo in texto
        for termo in (
            "2024",
            "2023",
            "2022",
            "2021",
            "2020",
            "copa libertadores 2024",
            "temporada 2024",
            "temporada 2023",
        )
    )

    if historico:
        pontos -= 30

    url_limpa = url.rstrip("/")

    if url_limpa.count("/") <= 2:
        pontos -= 15

    dominios_genericos = (
        "radiopointweb.com",
        "quadrodemedalhas.com",
    )

    if any(
        dominio.endswith(site)
        for site in dominios_genericos
    ):
        pontos -= 35

    fontes_palmeiras = (
        "nossopalestra.com.br",
        "verdazzo.com.br",
        "verdaoweb.com.br",
        "palmeirasonline.com",
        "portaldopalmeirense.com.br",
    )

    if any(
        dominio.endswith(site)
        for site in fontes_palmeiras
    ):
        pontos += 20

    fontes_esportivas = (
        "ge.globo.com",
        "espn.com.br",
        "gazetaesportiva.com",
        "uol.com.br",
        "terra.com.br",
        "lance.com.br",
        "goal.com",
        "placar.com.br",
    )

    if any(
        dominio.endswith(site)
        for site in fontes_esportivas
    ):
        pontos += 8

    data_fonte = str(
        item.get("source_date", "")
    ).strip()

    if data_fonte:
        try:
            hoje = datetime.now().date()

            data = datetime.fromisoformat(
                data_fonte[:10]
            ).date()

            idade = (
                hoje - data
            ).days

            if idade < 0:
                pontos += 5
            elif idade == 0:
                pontos += 45
            elif idade <= 1:
                pontos += 40
            elif idade <= 3:
                pontos += 32
            elif idade <= 7:
                pontos += 24
            elif idade <= 14:
                pontos += 12
            elif idade <= 30:
                pontos += 4
            elif temporal:
                pontos -= 25

            if temporal and idade > 30:
                pontos -= 40

        except (
            ValueError,
            TypeError,
        ):
            pass

    return pontos



def deve_pesquisar(mensagem: str) -> bool:
    """Determina se a mensagem precisa de pesquisa na web."""
    if not isinstance(mensagem, str):
        return False

    texto = normalizar(mensagem).strip()

    if not texto:
        return False

    termos_pesquisa = (
        "quem",
        "qual",
        "quais",
        "quando",
        "onde",
        "como",
        "quanto",
        "quantos",
        "quantas",
        "por que",
        "porque",
        "pesquise",
        "pesquisar",
        "pesquisa",
        "procure",
        "buscar",
        "busque",
        "noticia",
        "noticias",
        "atual",
        "agora",
        "hoje",
        "ontem",
        "amanha",
        "proximo",
        "proxima",
        "proximos",
        "proximas",
        "ultimo",
        "ultima",
        "ultimos",
        "ultimas",
        "agenda",
        "calendario",
        "jogo",
        "jogos",
        "partida",
        "partidas",
        "confronto",
        "confrontos",
        "resultado",
        "resultados",
        "preco",
        "precos",
        "cotacao",
        "salario",
        "lei",
        "legislacao",
        "decreto",
        "portaria",
    )

    return any(termo in texto for termo in termos_pesquisa)

def verificar_atualidade(resultados, dias_maximos=7):
    """Retorna somente resultados com data dentro da janela de atualidade."""
    if not resultados:
        return []

    hoje = datetime.now().date()
    recentes = []

    for resultado in resultados:
        if not isinstance(resultado, dict):
            continue

        data = (
            resultado.get("source_date")
            or resultado.get("published_at")
            or resultado.get("date")
            or resultado.get("data")
        )

        if not data:
            continue

        try:
            texto_data = str(data).strip()

            match = re.search(
                r"(20\d{2})[-/](\d{1,2})[-/](\d{1,2})",
                texto_data,
            )

            if match:
                ano, mes, dia = map(int, match.groups())
                data_resultado = datetime(ano, mes, dia).date()
            else:
                data_resultado = parsedate_to_datetime(
                    texto_data
                ).date()

            idade = (hoje - data_resultado).days

            if 0 <= idade <= dias_maximos:
                item = dict(resultado)
                item["_idade_dias"] = idade
                recentes.append(item)

        except Exception:
            continue

    recentes.sort(
        key=lambda x: x.get("_idade_dias", 999999)
    )

    return recentes

def pesquisar_web(
    consulta: str,
    limite: int = 5,
) -> list[dict]:
    consultas = preparar_consulta(consulta)

    if not consultas:
        return []

    candidatos = []

    termos_busca = [
        re.sub(
            r"[^\wÀ-ÿ-]",
            "",
            palavra,
        )
        for palavra in normalizar(
            consulta
        ).split()
        if re.sub(
            r"[^\wÀ-ÿ-]",
            "",
            palavra,
        )
        and re.sub(
            r"[^\wÀ-ÿ-]",
            "",
            palavra,
        ) not in {
            "qual",
            "quem",
            "onde",
            "quando",
            "como",
            "por",
            "que",
            "porque",
            "o",
            "a",
            "os",
            "as",
            "do",
            "da",
            "dos",
            "das",
            "de",
            "em",
            "no",
            "na",
            "um",
            "uma",
            "e",
            "proximo",
            "proxima",
        }
    ]

    for tentativa, consulta_teste in enumerate(
        consultas,
        start=1,
    ):
        try:
            resposta = requests.get(
                FREE_SERP_URL,
                params={
                    "q": consulta_teste,
                    "size": max(limite, 10),
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
                continue

            for item in resultados_brutos:
                if not isinstance(item, dict):
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

                conteudo = str(
                    item.get(
                        "content",
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

                if not (
                    titulo
                    or url
                    or resumo
                ):
                    continue

                resultado = {
                    "title": titulo,
                    "url": url,
                    "description": resumo,
                    "content": conteudo,
                    "domain": dominio,
                    "published": publicada,
                    "source_date": publicada,
                }

                resultado["_score"] = pontuar_resultado(
                    resultado,
                    termos_busca,
                )

                candidatos.append(
                    resultado
                )

        except Exception as erro:
            print(
                f"JARVIS WEB: falha FreeSerp: {erro}"
            )

    if not candidatos or (
        consulta_temporal(consulta)
        and not consulta_evento_futuro(consulta)
        and not verificar_atualidade(
            candidatos,
            dias_maximos=7,
        )
    ):
        try:
            news = pesquisar_google_news(
                consulta,
                limite=max(limite, 10),
            )

            for item in news:
                texto_item = normalizar(
                    " ".join(
                        [
                            str(item.get("title", "")),
                            str(item.get("description", "")),
                            str(item.get("domain", "")),
                        ]
                    )
                )

                termos_fortes = [
                    termo
                    for termo in termos_busca
                    if termo not in {
                        "proximo",
                        "proxima",
                        "ultimo",
                        "ultima",
                        "hoje",
                        "agora",
                        "atual",
                        "jogo",
                        "partida",
                        "futebol",
                    }
                ]

                if termos_fortes and not any(
                    termo in texto_item
                    for termo in termos_fortes
                ):
                    continue

                score = pontuar_resultado(
                    item,
                    termos_busca,
                ) + 25

                if item.get("source_date"):
                    try:
                        from datetime import datetime

                        hoje = datetime.now().date()

                        data_fonte = datetime.fromisoformat(
                            str(item["source_date"])[:10]
                        ).date()

                        idade = max(
                            0,
                            (hoje - data_fonte).days,
                        )

                        score += max(
                            0,
                            100 - (idade * 10),
                        )
                    except Exception:
                        pass

                item["_score"] = score
                candidatos.append(item)

            if news:
                print(
                    "JARVIS WEB: fallback Google News -> "
                    f"{len(news)}"
                )

        except Exception as erro:
            print(
                f"JARVIS WEB: falha Google News: {erro}"
            )

    if not candidatos:
        return []

    # Remove URLs duplicadas.
    unicos = {}

    for item in candidatos:
        url = item.get(
            "url",
            "",
        ).strip()

        chave = (
            url.lower()
            if url
            else (
                item.get(
                    "title",
                    "",
                ).strip().lower()
            )
        )

        if not chave:
            continue

        anterior = unicos.get(chave)

        if (
            anterior is None
            or item.get(
                "_score",
                0,
            ) > anterior.get(
                "_score",
                0,
            )
        ):
            unicos[chave] = item

    candidatos = list(
        unicos.values()
    )

    # Consultas temporais devem usar somente fontes recentes.
    # Perguntas históricas/conceituais continuam aceitando fontes antigas.
    if consulta_temporal(consulta) and not consulta_evento_futuro(consulta):
        candidatos_recentes = verificar_atualidade(
            candidatos,
            dias_maximos=7,
        )

        if candidatos_recentes:
            candidatos = candidatos_recentes
            print(
                "JARVIS WEB: filtro temporal -> "
                f"{len(candidatos)} fontes recentes"
            )
        else:
            print(
                "JARVIS WEB: nenhuma fonte recente "
                "encontrada para consulta temporal"
            )
            return []

    candidatos.sort(
        key=lambda item: item.get(
            "_score",
            0,
        ),
        reverse=True,
    )

    resultados_finais = []

    for item in candidatos[:limite]:
        item.pop(
            "_score",
            None,
        )
        item.pop(
            "_idade_dias",
            None,
        )
        resultados_finais.append(
            item
        )

    if resultados_finais:
        print(
            "JARVIS WEB: resultados "
            f"selecionados -> {len(resultados_finais)}"
        )

    return resultados_finais

def montar_contexto_web(
    resultados: list[dict],
) -> str:
    if not resultados:
        return ""

    hoje = datetime.now(
        timezone.utc
    ).date()

    fontes_recentes = verificar_atualidade(
        resultados,
        dias_maximos=7,
    )

    partes = [
        "CONTEXTO DE PESQUISA WEB DO J.A.R.V.I.S.",
        f"Data atual de referência: {hoje.isoformat()}",
        "Os dados abaixo foram obtidos pelo FreeSerp.",
        "",
    ]

    if fontes_recentes:
        partes.extend([
            "As fontes possuem atualização recente.",
            "Use os dados encontrados para responder.",
            "Não invente informações ausentes.",
            "",
        ])
    else:
        partes.extend([
            "ATENÇÃO: as fontes encontradas estão desatualizadas.",
            "Não trate esses dados como informação atual.",
            "Não invente ou estime acontecimentos posteriores à data das fontes.",
            "Quando a pergunta depender de informação atual, informe que as fontes disponíveis não são recentes o suficiente.",
            "",
        ])

    for indice, item in enumerate(
        resultados,
        start=1,
    ):
        titulo = str(
            item.get("title", "")
        ).strip()

        dominio = str(
            item.get("domain", "")
        ).strip()

        url = str(
            item.get("url", "")
        ).strip()

        data_fonte = str(
            item.get("source_date", "")
        ).strip()

        descricao = str(
            item.get("description", "")
        ).strip()

        conteudo = str(
            item.get("content", "")
        ).strip()

        partes.append(
            f"[FONTE {indice}] {titulo}"
        )

        if dominio:
            partes.append(
                f"Domínio: {dominio}"
            )

        if data_fonte:
            partes.append(
                f"Data da fonte: {data_fonte}"
            )

        if url:
            partes.append(
                f"URL: {url}"
            )

        texto_fonte = (
            conteudo
            or descricao
        )

        if texto_fonte:
            texto_fonte = texto_fonte[:6000]
            partes.append(
                f"CONTEÚDO:\n{texto_fonte}"
            )

        partes.append("")

    return "\n".join(partes)








