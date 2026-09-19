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

    termos = (
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
        "atualmente",
        "recentemente",
        "recentes",
    )

    if any(
        termo in texto
        for termo in termos
    ):
        return True

    return bool(
        re.search(
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b",
            texto,
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
    from datetime import timedelta

    consulta_original = str(
        consulta or ""
    ).strip()

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

    data_absoluta = None

    match_data = re.search(
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",
        consulta_normalizada,
    )

    if match_data:
        try:
            data_absoluta = datetime(
                int(match_data.group(3)),
                int(match_data.group(2)),
                int(match_data.group(1)),
            ).date()
        except ValueError:
            data_absoluta = None

    base = re.sub(
        r"[^\w\s]",
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
        "foi",
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
        ontem = hoje - timedelta(days=1)
        amanha = hoje + timedelta(days=1)

        ano = hoje.year

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

        mes = meses[
            hoje.month - 1
        ]

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
                "atualmente",
                "recentemente",
                "recentes",
            }
        ]

        base_forte = " ".join(
            termos_sem_temporal
        ).strip()

        if base_forte:

            if consulta_evento_futuro(
                consulta_normalizada
            ):

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

                if "amanha" in consulta_normalizada:

                    data_ref = amanha

                    adicionar(
                        f"{base_forte} "
                        f"{data_ref.strftime('%d/%m/%Y')}"
                    )

                    adicionar(
                        f"{base_forte} "
                        f"{data_ref.day} "
                        f"{meses[data_ref.month - 1]} "
                        f"{data_ref.year}"
                    )

                adicionar(
                    f"{base_forte} {mes} {ano}"
                )

                adicionar(
                    f"{base_forte} jogos {ano}"
                )

            elif consulta_passado_recente(
                consulta_normalizada
            ):

                adicionar(
                    f"{base_forte} ultimo jogo"
                )

                adicionar(
                    f"{base_forte} resultado"
                )

                adicionar(
                    f"{base_forte} jogo anterior"
                )

                if "ontem" in consulta_normalizada:

                    data_ref = ontem

                    data_numerica = (
                        data_ref.strftime(
                            "%d/%m/%Y"
                        )
                    )

                    nome_mes = meses[
                        data_ref.month - 1
                    ]

                    adicionar(
                        f"{base_forte} "
                        f"resultado {data_numerica}"
                    )

                    adicionar(
                        f"{base_forte} "
                        f"jogo {data_numerica}"
                    )

                    adicionar(
                        f"{base_forte} "
                        f"partida {data_numerica}"
                    )

                    adicionar(
                        f"{base_forte} "
                        f"resultados "
                        f"{data_ref.day} "
                        f"{nome_mes} "
                        f"{data_ref.year}"
                    )

                elif data_absoluta is not None:

                    adicionar(
                        f"{base_forte} "
                        f"resultado "
                        f"{data_absoluta.strftime('%d/%m/%Y')}"
                    )

                else:

                    adicionar(
                        f"{base_forte} "
                        f"{mes} {ano}"
                    )

            elif consulta_atualidade(
                consulta_normalizada
            ):

                if "hoje" in consulta_normalizada:

                    adicionar(
                        f"{base_forte} "
                        f"{hoje.strftime('%d/%m/%Y')}"
                    )

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
    """Determina se a mensagem realmente precisa de pesquisa na web."""
    if not isinstance(mensagem, str):
        return False

    texto = normalizar(mensagem).strip()

    if not texto:
        return False

    # 1. Pesquisa explicitamente solicitada pelo usuario.
    termos_explicitos = (
        "pesquise",
        "pesquisar",
        "pesquisa",
        "procure",
        "buscar",
        "busque",
        "pesquisa na internet",
        "pesquisa na web",
        "consulte na internet",
        "consulte na web",
    )

    if any(termo in texto for termo in termos_explicitos):
        return True

    # 2. Informacao dinamica ou temporal.
    termos_temporais = (
        "hoje",
        "agora",
        "ontem",
        "amanha",
        "atual",
        "atualmente",
        "neste momento",
        "nesse momento",
        "recentemente",
        "recentes",
        "ultima",
        "ultimo",
        "ultimas",
        "ultimos",
        "proxima",
        "proximo",
        "proximas",
        "proximos",
    )

    if any(termo in texto for termo in termos_temporais):
        return True

    # 3. Categorias que normalmente dependem de dados atuais.
    termos_dinamicos = (
        "noticia",
        "noticias",
        "preco",
        "precos",
        "cotacao",
        "cotacoes",
        "salario",
        "salarios",
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
        "placar",
        "placares",
        "classificacao",
        "tabela",
        "ranking",
        "evento",
        "eventos",
        "horario",
        "horarios",
    )

    if any(termo in texto for termo in termos_dinamicos):
        return True

    # 4. Consultas sobre pessoas/cargos que explicitamente pedem
    #    situacao atual.
    termos_cargo_atual = (
        "atual presidente",
        "atual governador",
        "atual prefeito",
        "atual ministro",
        "atual presidente",
        "quem e o presidente atual",
        "quem e o governador atual",
        "quem e o prefeito atual",
    )

    if any(termo in texto for termo in termos_cargo_atual):
        return True

    # 5. Leis e normas podem mudar e devem ser verificadas na web.
    termos_juridicos = (
        "lei atual",
        "lei vigente",
        "legislacao atual",
        "legislacao vigente",
        "decreto atual",
        "decreto vigente",
        "portaria atual",
        "portaria vigente",
        "norma atual",
        "norma vigente",
    )

    if any(termo in texto for termo in termos_juridicos):
        return True

    # 6. Perguntas factuais estaveis ficam com a IA.
    #    Exemplos:
    #      "qual a capital do Brasil"
    #      "quem foi Albert Einstein"
    #      "quanto e 2 + 2"
    #      "como funciona um motor eletrico"
    #
    #    Isso reduz chamadas web e consumo de tokens sem impedir
    #    pesquisas explicitamente solicitadas ou informacoes atuais.

    return False

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

    consultas = preparar_consulta(
        consulta
    )

    if not consultas:
        return []

    from app.core.pesquisa_provedores import (
        pesquisar_com_fallback,
    )

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

    temporal = (
        consulta_temporal(
            consulta
        )
        and not consulta_evento_futuro(
            consulta
        )
    )

    candidatos = pesquisar_com_fallback(
        consultas=consultas,
        limite=limite,
        temporal=temporal,
        verificar_atualidade=verificar_atualidade,
    )

    if not candidatos:
        return []

    # ========================================================
    # RANKING
    # ========================================================

    for item in candidatos:

        item["_score"] = pontuar_resultado(
            item,
            termos_busca,
        )

    # ========================================================
    # DEDUPLICACAO
    # ========================================================

    unicos = {}

    for item in candidatos:

        url = str(
            item.get(
                "url",
                "",
            )
        ).strip()

        chave = (
            url.lower()
            if url
            else str(
                item.get(
                    "title",
                    "",
                )
            ).strip().lower()
        )

        if not chave:
            continue

        anterior = unicos.get(
            chave
        )

        if (
            anterior is None
            or item.get(
                "_score",
                0,
            )
            > anterior.get(
                "_score",
                0,
            )
        ):
            unicos[chave] = item

    candidatos = list(
        unicos.values()
    )

    # ========================================================
    # FILTRO TEMPORAL
    # ========================================================

    if (
        consulta_temporal(
            consulta
        )
        and not consulta_evento_futuro(
            consulta
        )
    ):

        candidatos_recentes = (
            verificar_atualidade(
                candidatos,
                dias_maximos=7,
            )
        )

        if candidatos_recentes:

            candidatos = (
                candidatos_recentes
            )

            print(
                "JARVIS WEB: filtro "
                "temporal -> "
                f"{len(candidatos)} "
                "fontes recentes"
            )

        else:

            print(
                "JARVIS WEB: nenhuma "
                "fonte recente encontrada"
            )

            return []

    # ========================================================
    # ORDENACAO FINAL
    # ========================================================

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

    print(
        "JARVIS WEB: resultados "
        f"selecionados -> "
        f"{len(resultados_finais)}"
    )

    return resultados_finais

def _extrair_primeiro_evento_futuro(
    texto: str,
    hoje,
):
    padrao_data = re.compile(
        r"(?<!\d)"
        r"(\d{1,2})[/-]"
        r"(\d{1,2})"
        r"(?:[/-](20\d{2}))?"
        r"(?!\d)"
    )

    candidatos = []

    linhas = [
        linha.strip()
        for linha in str(texto or "").splitlines()
        if linha.strip()
    ]

    for indice_linha, linha in enumerate(linhas):

        linha_normalizada = normalizar(
            linha
        )

        # A linha precisa mencionar Palmeiras.
        if "palmeiras" not in linha_normalizada:
            continue

        # Precisa parecer uma linha de partida/confronto.
        tem_evento = any(
            sinal in linha_normalizada
            for sinal in (
                " x ",
                "×",
                " vs ",
                "vs.",
                " contra ",
                " enfrenta ",
                " jogo ",
                " partida ",
                " confronto ",
            )
        )

        if not tem_evento:
            continue

        for correspondencia in padrao_data.finditer(
            linha
        ):

            dia = int(
                correspondencia.group(1)
            )

            mes = int(
                correspondencia.group(2)
            )

            ano_texto = correspondencia.group(3)

            if ano_texto:

                ano = int(
                    ano_texto
                )

            else:

                ano = hoje.year

            try:

                data_evento = datetime(
                    ano,
                    mes,
                    dia,
                    tzinfo=timezone.utc,
                ).date()

            except ValueError:

                continue

            if data_evento < hoje:
                continue

            candidatos.append(
                (
                    data_evento,
                    indice_linha,
                    correspondencia.start(),
                    correspondencia.end(),
                    linha,
                )
            )

    if not candidatos:
        return None

    candidatos.sort(
        key=lambda item: (
            item[0],
            item[1],
            item[2],
        )
    )

    escolhido = candidatos[0]

    return (
        escolhido[0],
        escolhido[2],
        escolhido[3],
    )


def _limpar_datas_do_trecho(
    trecho: str,
    hoje,
    data_selecionada,
):
    padrao = re.compile(
        r"(?<!\d)"
        r"(\d{1,2})[/-]"
        r"(\d{1,2})"
        r"(?:[/-](20\d{2}))?"
        r"(?!\d)"
    )

    def substituir(
        correspondencia,
    ):
        dia = int(
            correspondencia.group(1)
        )

        mes = int(
            correspondencia.group(2)
        )

        ano_texto = correspondencia.group(3)

        ano = (
            int(ano_texto)
            if ano_texto
            else hoje.year
        )

        try:
            data_encontrada = datetime(
                ano,
                mes,
                dia,
                tzinfo=timezone.utc,
            ).date()
        except ValueError:
            return "[data omitida]"

        if data_encontrada == data_selecionada:
            return correspondencia.group(0)

        return "[outra data omitida]"

    return padrao.sub(
        substituir,
        trecho,
    )


def _priorizar_resultados_evento_futuro(
    resultados: list[dict],
    hoje,
) -> list[dict]:
    candidatos = []

    for item in resultados:
        titulo = str(
            item.get(
                "title",
                "",
            )
        ).strip()

        descricao = str(
            item.get(
                "description",
                "",
            )
        ).strip()

        conteudo = str(
            item.get(
                "content",
                "",
            )
        ).strip()

        dominio = str(
            item.get(
                "domain",
                "",
            )
        ).strip().lower()

        texto_item = " ".join(
            (
                titulo,
                descricao,
                conteudo,
            )
        )

        evento = _extrair_primeiro_evento_futuro(
            texto_item,
            hoje,
        )

        if evento is None:
            continue

        data_evento = evento[0]
        inicio_data = evento[1]
        fim_data = evento[2]

        inicio_trecho = max(
            0,
            inicio_data - 400,
        )

        fim_trecho = min(
            len(texto_item),
            fim_data + 900,
        )

        trecho = texto_item[
            inicio_trecho:fim_trecho
        ].strip()

        trecho = _limpar_datas_do_trecho(
            trecho,
            hoje,
            data_evento,
        )

        texto_normalizado = normalizar(
            texto_item
        )

        score = 0

        if (
            dominio == "palmeiras.com.br"
            or dominio.endswith(
                ".palmeiras.com.br"
            )
        ):
            score += 20

        if "palmeiras" in texto_normalizado:
            score += 5

        if any(
            termo in texto_normalizado
            for termo in (
                "jogo",
                "partida",
                "confronto",
                "enfrenta",
                "arena",
                "rodada",
            )
        ):
            score += 5

        if re.search(
            r"\b\d{1,2}\s*[h:]\s*\d{2}\b",
            trecho,
            re.IGNORECASE,
        ):
            score += 4

        candidatos.append(
            {
                "score": score,
                "data_evento": data_evento,
                "titulo": titulo,
                "dominio": dominio,
                "url": str(
                    item.get(
                        "url",
                        "",
                    )
                ).strip(),
                "source_date": str(
                    item.get(
                        "source_date",
                        "",
                    )
                ).strip(),
                "trecho_evento": trecho,
            }
        )

    if not candidatos:
        return []

    menor_data = min(
        item["data_evento"]
        for item in candidatos
    )

    candidatos = [
        item
        for item in candidatos
        if item["data_evento"] == menor_data
    ]

    candidatos.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    resultados_filtrados = []

    for item in candidatos[:3]:
        resultados_filtrados.append(
            {
                "title": item["titulo"],
                "domain": item["dominio"],
                "url": item["url"],
                "source_date": item["source_date"],
                "content": (
                    "EVENTO FUTURO IDENTIFICADO:\n"
                    f"Data do evento: "
                    f"{item['data_evento'].strftime('%d/%m/%Y')}\n"
                    "Trecho relevante da fonte:\n"
                    f"{item['trecho_evento']}"
                ),
            }
        )

    return resultados_filtrados


def montar_contexto_web(
    resultados: list[dict],
    consulta: str = "",
) -> str:
    if not resultados:
        return ""

    hoje = datetime.now(
        timezone.utc
    ).date()

    evento_futuro = consulta_evento_futuro(
        consulta
    )

    if evento_futuro:
        resultados = _priorizar_resultados_evento_futuro(
            resultados,
            hoje,
        )

        if not resultados:
            return ""

    fontes_recentes = verificar_atualidade(
        resultados,
        dias_maximos=7,
    )

    partes = [
        "CONTEXTO DE PESQUISA WEB DO J.A.R.V.I.S.",
        f"Data atual de refer\u00eancia: {hoje.isoformat()}",
        "Os dados abaixo foram obtidos por pesquisa web.",
        "",
    ]

    if evento_futuro:
        partes.extend([
            "A consulta trata de um evento futuro.",
            "Foram selecionadas as fontes cujo primeiro "
            "evento futuro coincide com a data mais pr\u00f3xima "
            "encontrada nas fontes.",
            "Datas anteriores ao dia atual n\u00e3o devem ser "
            "usadas como resposta.",
            "Quando houver fonte oficial do Palmeiras, "
            "ela tem prioridade em caso de conflito.",
            "Use exclusivamente os eventos apresentados "
            "abaixo.",
            "N\u00e3o invente informa\u00e7\u00f5es ausentes.",
            "",
        ])

    elif fontes_recentes:
        partes.extend([
            "As fontes possuem atualiza\u00e7\u00e3o recente.",
            "Use os dados encontrados para responder.",
            "N\u00e3o invente informa\u00e7\u00f5es ausentes.",
            "",
        ])

    else:
        partes.extend([
            "ATEN\u00c7\u00c3O: as fontes encontradas est\u00e3o desatualizadas.",
            "N\u00e3o trate esses dados como informa\u00e7\u00e3o atual.",
            "N\u00e3o invente ou estime acontecimentos posteriores "
            "\u00e0 data das fontes.",
            "Quando a pergunta depender de informa\u00e7\u00e3o atual, "
            "informe que as fontes dispon\u00edveis n\u00e3o s\u00e3o "
            "recentes o suficiente.",
            "",
        ])

    for indice, item in enumerate(
        resultados,
        start=1,
    ):
        titulo = str(
            item.get(
                "title",
                "",
            )
        ).strip()

        dominio = str(
            item.get(
                "domain",
                "",
            )
        ).strip()

        url = str(
            item.get(
                "url",
                "",
            )
        ).strip()

        data_fonte = str(
            item.get(
                "source_date",
                "",
            )
        ).strip()

        descricao = str(
            item.get(
                "description",
                "",
            )
        ).strip()

        conteudo = str(
            item.get(
                "content",
                "",
            )
        ).strip()

        partes.append(
            f"[FONTE {indice}] {titulo}"
        )

        if dominio:
            partes.append(
                f"Dom\u00ednio: {dominio}"
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
            texto_fonte = texto_fonte[:4000]

            partes.append(
                f"CONTE\u00daDO:\n{texto_fonte}"
            )

        partes.append("")

    return "\n".join(partes)
