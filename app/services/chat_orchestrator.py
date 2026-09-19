import os
import re
import requests
from JARVIS_BASE.memoria_classificador import classificar_memoria
from app.core.memoria_persistente import MemoriaPersistente
from app.core.pesquisa_web import (
    consulta_evento_futuro,
    deve_pesquisar,
    montar_contexto_web,
    normalizar,
    pesquisar_web,
    verificar_atualidade,
)
class ChatOrchestrator:
    def __init__(self):
        self.memoria = MemoriaPersistente()
    def processar(self, mensagem: str) -> str:
        mensagem = str(mensagem or "").strip()
        if not mensagem:
            raise ValueError("Mensagem vazia.")
        self.salvar_memoria_se_aplicavel(
            mensagem
        )
        contexto_sistema = []
        contexto_memoria = self.recuperar_memoria(
            mensagem
        )
        if contexto_memoria:
            contexto_sistema.append(
                contexto_memoria
            )
        contexto_web = self.obter_contexto_web(
            mensagem
        )
        if contexto_web:
            contexto_sistema.append(
                contexto_web
            )
            resposta_evento = (
                self.extrair_resposta_evento_futuro(
                    contexto_web,
                    mensagem,
                )
            )
            if resposta_evento:
                return resposta_evento
        mensagens = self.montar_mensagens(
            mensagem,
            contexto_sistema,
        )
        return self.chamar_ia_router(
            mensagens
        )
    def salvar_memoria_se_aplicavel(
        self,
        mensagem: str,
    ) -> None:
        try:
            classificacao = classificar_memoria(
                mensagem
            )
            if not classificacao.get(
                "permanente",
                False,
            ):
                return
            conteudo = str(
                classificacao.get(
                    "conteudo",
                    mensagem,
                )
            ).strip()
            if not conteudo:
                return
            prefixos = (
                "lembre que ",
                "lembra que ",
                "guarde que ",
                "memorize que ",
                "salve que ",
                "anote que ",
                "registre que ",
                "tenha em mente que ",
                "nao esqueca que ",
                "não esqueça que ",
            )
            normalizado = conteudo.lower()
            for prefixo in prefixos:
                if normalizado.startswith(prefixo):
                    conteudo = (
                        conteudo[
                            len(prefixo):
                        ].strip()
                    )
                    break
            if not conteudo:
                return
            self.memoria.salvar_memoria(
                conteudo=conteudo,
                tipo=str(
                    classificacao.get(
                        "tipo",
                        "OUTRO",
                    )
                ).strip() or "OUTRO",
                importancia=int(
                    classificacao.get(
                        "importancia",
                        5,
                    )
                ),
                duracao="PERMANENTE",
            )
        except Exception:
            return
    def recuperar_memoria(
        self,
        mensagem: str,
    ) -> str:
        try:
            resultados = self.memoria.buscar_memorias(
                mensagem,
                limite=8,
            )
            if not resultados:
                return ""
            partes = [
                "CONTEXTO DE MEMÓRIA DO J.A.R.V.I.S.",
                "Use somente quando for relevante.",
                "",
            ]
            for item in resultados:
                tipo = str(
                    item.get(
                        "tipo",
                        "MEMORIA",
                    )
                ).strip()
                conteudo = str(
                    item.get(
                        "conteudo",
                        "",
                    )
                ).strip()
                if conteudo:
                    partes.append(
                        f"[{tipo}] {conteudo}"
                    )
            return "\n".join(partes)
        except Exception:
            return ""
    def obter_contexto_web(
        self,
        mensagem: str,
    ) -> str:
        if not deve_pesquisar(mensagem):
            return ""
        resultados_web = pesquisar_web(
            mensagem,
            limite=5,
        )
        if self.exige_atualidade(
            mensagem
        ):
            if (
                resultados_web
                and not verificar_atualidade(
                    resultados_web,
                    dias_maximos=7,
                )
            ):
                datas = sorted(
                    {
                        str(
                            item.get(
                                "source_date",
                                "",
                            )
                        ).strip()
                        for item in resultados_web
                        if item.get(
                            "source_date",
                            "",
                        )
                    }
                )
                ultima_data = (
                    datas[-1]
                    if datas
                    else "desconhecida"
                )
                raise InformacaoDesatualizada(
                    "Encontrei fontes sobre esse assunto, "
                    "mas a informação disponível está "
                    f"desatualizada. A fonte mais recente "
                    f"encontrada é de {ultima_data}. "
                    "Não vou inventar o dado atual."
                )
        return montar_contexto_web(
            resultados_web,
            mensagem,
        )
    def exige_atualidade(
        self,
        mensagem: str,
    ) -> bool:
        if consulta_evento_futuro(
            mensagem
        ):
            return False
        texto = mensagem.lower()
        return any(
            palavra in texto
            for palavra in (
                "hoje",
                "agora",
                "atual",
                "atualmente",
                "ultimo",
                "último",
                "ultima",
                "última",
                "ontem",
            )
        )

    def extrair_resposta_evento_futuro(
        self,
        contexto: str,
        consulta: str,
    ) -> str:
        import re
        from datetime import datetime

        if not contexto:
            return ""

        match_data = re.search(
            r"Data do evento:\s*(\d{2}/\d{2}/\d{4})",
            contexto,
            re.IGNORECASE,
        )

        if not match_data:
            return ""

        try:
            data_evento = datetime.strptime(
                match_data.group(1),
                "%d/%m/%Y",
            ).date()
        except ValueError:
            return ""

        data_curta = (
            f"{data_evento.day:02d}/"
            f"{data_evento.month:02d}"
        )

        data_completa = data_evento.strftime("%d/%m/%Y")

        if not re.search(
            r"\bpalmeiras\b",
            consulta,
            re.IGNORECASE,
        ):
            return ""

        separador_re = re.compile(
            r"\s+(?:x|×|vs\.?|contra|enfrenta)\s+",
            re.IGNORECASE,
        )

        linhas = contexto.splitlines()

        candidatos = []

        for indice, linha in enumerate(linhas):
            original = linha.strip()

            if not original:
                continue

            baixo = original.lower()

            if (
                data_curta not in baixo
                and data_completa not in baixo
            ):
                continue

            if "palmeiras" not in baixo:
                continue

            separador = separador_re.search(original)

            if not separador:
                continue

            match_data_linha = re.search(
                rf"\b{re.escape(data_curta)}(?:/{data_evento.year})?\b",
                original,
                re.IGNORECASE,
            )

            if match_data_linha:
                evento_linha = original[
                    match_data_linha.end():
                ].strip(" ·•|_-–—")
            else:
                evento_linha = original

            separador = separador_re.search(evento_linha)

            if not separador:
                continue

            lado_esquerdo = evento_linha[
                :separador.start()
            ].strip(" ·•|_-–—")

            lado_direito = evento_linha[
                separador.end():
            ].strip(" ·•|_-–—")

            def limpar_time(
                trecho: str,
                time_alvo: str = "Palmeiras",
            ) -> str:
                texto = re.sub(
                    r"\s+",
                    " ",
                    trecho.strip(),
                )

                if not texto:
                    return ""

                alvo = re.search(
                    rf"\b{re.escape(time_alvo)}\b",
                    texto,
                    re.IGNORECASE,
                )

                if alvo:
                    return time_alvo

                texto = re.sub(
                    r"\s+(?:Arena|Allianz Parque|"
                    r"Estádio|Estadio)\b.*$",
                    "",
                    texto,
                    flags=re.IGNORECASE,
                )

                texto = re.split(
                    r"\s*[·•|]\s*"
                    r"|\s+\d{1,2}(?:h|:)\d{2}\b",
                    texto,
                    maxsplit=1,
                    flags=re.IGNORECASE,
                )[0]

                texto = re.sub(
                    r"^\d+\s+",
                    "",
                    texto,
                )

                return texto.strip(" ·•|_-–—")

            mandante = limpar_time(
                lado_esquerdo
            )

            visitante = limpar_time(
                lado_direito
            )

            if not mandante or not visitante:
                continue

            if (
                "palmeiras" not in mandante.lower()
                and "palmeiras" not in visitante.lower()
            ):
                continue

            match_hora = re.search(
                r"\b((?:[01]?\d|2[0-3]))"
                r"(?:h|:)"
                r"([0-5]\d)\b",
                original,
                re.IGNORECASE,
            )

            hora = ""

            if match_hora:
                hora = (
                    f"{int(match_hora.group(1)):02d}:"
                    f"{match_hora.group(2)}"
                )

            match_local = re.search(
                r"\b("
                r"(?:Arena|Allianz Parque|"
                r"Estádio|Estadio)"
                r"[^·|]*?"
                r")(?=\s*(?:·|•|"
                r"(?:[01]?\d|2[0-3])(?:h|:)[0-5]\d\b"
                r"|$))",
                evento_linha,
                re.IGNORECASE,
            )

            local = ""

            if match_local:
                local = re.sub(
                    r"\s+",
                    " ",
                    match_local.group(1),
                ).strip(" ·•|_-–—")

            dias_semana = {
                0: "segunda-feira",
                1: "terça-feira",
                2: "quarta-feira",
                3: "quinta-feira",
                4: "sexta-feira",
                5: "sábado",
                6: "domingo",
            }

            dia_semana = dias_semana[
                data_evento.weekday()
            ]

            if hora:
                resposta = (
                    f"O próximo jogo do Palmeiras é "
                    f"{mandante} x {visitante}, "
                    f"{dia_semana}, "
                    f"{data_completa} às {hora}."
                )
            else:
                resposta = (
                    f"O próximo jogo do Palmeiras é "
                    f"{mandante} x {visitante}, "
                    f"{dia_semana}, "
                    f"{data_completa}."
                )

            if local:
                resposta += f" Local: {local}."

            candidatos.append(
                (
                    data_evento,
                    indice,
                    resposta,
                )
            )

        if not candidatos:
            return ""

        candidatos.sort(
            key=lambda item: (
                item[0],
                item[1],
            )
        )

        return candidatos[0][2]


    def montar_mensagens(
        self,
        mensagem: str,
        contexto_sistema: list[str],
    ) -> list[dict]:
        mensagens = []
        if contexto_sistema:
            mensagens.append(
                {
                    "role": "system",
                    "content": "\n\n".join(
                        contexto_sistema
                    ),
                }
            )
        mensagens.append(
            {
                "role": "user",
                "content": mensagem,
            }
        )
        return mensagens
    def obter_url_router(self) -> str:
        port = os.getenv(
            "PORT",
            "8000",
        )
        return (
            f"http://127.0.0.1:{port}"
            "/ia-router/v1/chat/completions"
        )
    def chamar_ia_router(
        self,
        mensagens: list[dict],
    ) -> str:
        payload = {
            "messages": mensagens,
        }
        try:
            resposta = requests.post(
                self.obter_url_router(),
                json=payload,
                timeout=120,
            )
            if resposta.status_code >= 400:
                raise IARouterError(
                    "IA Router retornou "
                    f"HTTP {resposta.status_code}."
                )
            dados = resposta.json()
            try:
                return dados[
                    "choices"
                ][0][
                    "message"
                ][
                    "content"
                ]
            except (
                KeyError,
                IndexError,
                TypeError,
            ):
                return str(dados)
        except requests.RequestException as erro:
            raise IARouterError(
                "Falha ao comunicar com "
                f"o IA Router: {erro}"
            ) from erro
class InformacaoDesatualizada(
    Exception
):
    pass
class IARouterError(Exception):
    pass
