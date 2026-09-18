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
        contexto_web: str,
        mensagem: str,
    ) -> str:
        if not consulta_evento_futuro(mensagem):
            return ""

        data_match = re.search(
            r"Data do evento:\s*(\d{2}/\d{2}/\d{4})",
            contexto_web,
        )

        if not data_match:
            return ""

        data_evento = data_match.group(1)
        data_curta = data_evento[:5]

        inicio = data_match.end()

        proxima_fonte = contexto_web.find(
            "\n[FONTE ",
            inicio,
        )

        if proxima_fonte < 0:
            proxima_fonte = len(contexto_web)

        bloco = contexto_web[
            inicio:proxima_fonte
        ]

        linhas = [
            linha.strip()
            for linha in bloco.splitlines()
            if linha.strip()
        ]

        padrao_confronto = re.compile(
            r"\b([\w?-?.'-]+)\s+[Xx?]\s+([\w?-?.'-]+)\b",
            re.UNICODE,
        )

        confronto = None
        linha_evento = ""

        # Primeiro tenta a linha que cont?m:
        # data + Palmeiras + confronto.
        for linha in linhas:
            linha_normalizada = normalizar(linha)

            if data_curta not in linha:
                continue

            if "palmeiras" not in linha_normalizada:
                continue

            confrontos = padrao_confronto.findall(linha)

            for mandante, visitante in confrontos:
                nomes = normalizar(
                    f"{mandante} {visitante}"
                )

                if "palmeiras" not in nomes:
                    continue

                confronto = (
                    mandante.strip(
                        " |:-,.;"
                    ),
                    visitante.strip(
                        " |:-,.;"
                    ),
                )

                linha_evento = linha
                break

            if confronto:
                break

        if not confronto:
            return ""

        mandante, visitante = confronto

        pos_data = linha_evento.find(
            data_curta
        )

        if pos_data < 0:
            return ""

        trecho = linha_evento[
            pos_data:
            pos_data + 180
        ]

        hora_match = re.search(
            r"\b(\d{1,2})\s*[hH:]\s*(\d{2})\b",
            trecho,
        )

        if not hora_match:
            return ""

        hora = (
            f"{int(hora_match.group(1)):02d}:"
            f"{int(hora_match.group(2)):02d}"
        )

        local_match = re.search(
            r"\bArena\s+(?:do|da|de)\s+"
            r"[\w?-?.'-]+"
            r"(?:\s+[\w?-?.'-]+){0,2}",
            trecho,
            re.IGNORECASE,
        )

        local = (
            local_match.group(0).strip()
            if local_match
            else ""
        )

        resposta = (
            f"O pr?ximo jogo do Palmeiras ? "
            f"{mandante} x {visitante}, "
            f"{data_evento} ?s {hora}."
        )

        if local:
            resposta += (
                f" Local: {local}."
            )

        return resposta

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
