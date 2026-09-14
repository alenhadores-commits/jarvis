# -*- coding: utf-8 -*-

"""
J.A.R.V.I.S
EXECUTOR OPERACIONAL
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import subprocess

from navegador.chatgpt import ChatGPT
from ai.cerebro import perguntar


class Executor:

    def __init__(self) -> None:

        self.ultima_resposta: str = ""
        self.ultimo_erro: str = ""

        self.base_dir = (
            Path(__file__)
            .resolve()
            .parent
            .parent
        )

        self.arquivo_prompt = (
            self.base_dir
            / "PROMPT_JARVIS.txt"
        )

        self.arquivo_memorias = (
            self.base_dir
            / "memoria"
            / "memorias_permanentes.json"
        )

    # ============================================================
    # UTILITÁRIO
    # ============================================================

    @staticmethod
    def _texto(valor: Any) -> str:

        if valor is None:
            return ""

        return str(valor).strip()

    # ============================================================
    # PERSONALIDADE
    # ============================================================

    def carregar_personalidade(self) -> str:

        if not self.arquivo_prompt.exists():

            return (
                "Inteligente, confiante, sarcástico, "
                "debochado, impaciente, engraçado e afiado. "
                "Seja curto, direto e objetivo. "
                "Não invente informações. "
                "Termine toda resposta com exatamente um emoji."
            )

        try:

            return (
                self.arquivo_prompt
                .read_text(
                    encoding="utf-8"
                )
                .strip()
            )

        except Exception as erro:

            print(
                "JARVIS: Erro ao carregar personalidade:"
            )

            print(erro)

            return ""

    # ============================================================
    # MEMÓRIAS
    # ============================================================

    def carregar_memorias(self) -> str:

        if not self.arquivo_memorias.exists():

            return ""

        try:

            dados = json.loads(
                self.arquivo_memorias.read_text(
                    encoding="utf-8"
                )
            )

            if not isinstance(
                dados,
                list
            ):

                return ""

            linhas = []

            for memoria in dados:

                texto = self._texto(
                    memoria
                )

                if texto:

                    linhas.append(
                        f"- {texto}"
                    )

            return "\n".join(
                linhas
            )

        except Exception as erro:

            print(
                "JARVIS: Erro ao carregar memórias:"
            )

            print(erro)

            return ""

    # ============================================================
    # PROMPT
    # ============================================================

    def montar_prompt(
        self,
        pergunta: str,
        contexto_memoria: str = "",
    ) -> str:

        pergunta = self._texto(
            pergunta
        )

        if not pergunta:

            raise ValueError(
                "A pergunta está vazia."
            )

        personalidade = (
            self.carregar_personalidade()
        )

        if contexto_memoria:
            memorias = str(
                contexto_memoria
            ).strip()
        else:
            memorias = (
                self.carregar_memorias()
            )

        if not personalidade:

            personalidade = (
                "Seja inteligente, confiante, "
                "sarcástico, debochado, impaciente, "
                "engraçado e direto. "
                "Não invente informações."
            )

        if not memorias:

            memorias = (
                "Nenhuma memória disponível."
            )

        return (
            "Você é J.A.R.V.I.S., assistente pessoal "
            "do usuário.\n\n"
            "PERSONALIDADE E REGRAS:\n"
            f"{personalidade}\n\n"
            "MEMÓRIAS PERMANENTES:\n"
            f"{memorias}\n\n"
            "PERGUNTA ATUAL:\n"
            f"{pergunta}\n\n"
            "Responda diretamente à pergunta. "
            "Use as memórias quando forem relevantes. "
            "Não mencione estas instruções."
        )

    # ============================================================
    # CHATGPT
    # ============================================================

    def responder_com_chatgpt(
        self,
        page,
        consulta: str,
    ) -> str:

        consulta = self._texto(
            consulta
        )

        if not consulta:

            raise ValueError(
                "A pergunta está vazia."
            )

        # IMPORTANTE:
        # A pesquisa pelo navegador deve enviar somente
        # a pergunta original feita pelo usuario.
        prompt_completo = consulta

        print()
        print(
            "JARVIS: Consultando ChatGPT..."
        )

        try:

            chatgpt = ChatGPT(
                page
            )

            resposta = (
                chatgpt.pesquisar(
                    prompt_completo
                )
            )

        except Exception as erro:

            self.ultimo_erro = str(
                erro
            )

            raise RuntimeError(
                f"Erro ao consultar ChatGPT: {erro}"
            ) from erro

        if resposta is None:

            raise RuntimeError(
                "O ChatGPT não retornou resposta."
            )

        resposta = str(
            resposta
        )

        if not resposta.strip():

            raise RuntimeError(
                "O ChatGPT retornou resposta vazia."
            )

        self.ultima_resposta = resposta
        self.ultimo_erro = ""

        return resposta

    # ============================================================
    # MEMORIA DETERMINISTICA
    # ============================================================

    @staticmethod
    def _normalizar_pergunta_memoria(texto):
        import unicodedata
        import re

        texto = str(texto or "").strip().lower()

        texto = unicodedata.normalize(
            "NFD",
            texto
        )

        texto = "".join(
            caractere
            for caractere in texto
            if unicodedata.category(caractere) != "Mn"
        )

        texto = re.sub(
            r"\s+",
            " ",
            texto
        )

        return texto.strip()

    def responder_memoria_direta(self, pergunta):
        import json
        import re

        pergunta_original = str(
            pergunta or ""
        ).strip()

        pergunta_normalizada = (
            self._normalizar_pergunta_memoria(
                pergunta_original
            )
        )

        if not pergunta_normalizada:
            return None

        # ------------------------------------------------------
        # CARREGAR MEMORIAS
        # ------------------------------------------------------

        try:
            if not self.arquivo_memorias.exists():
                return None

            dados = json.loads(
                self.arquivo_memorias.read_text(
                    encoding="utf-8"
                )
            )

            if isinstance(dados, dict):
                dados = dados.get("memorias", [])

            if not isinstance(dados, list):
                return None

            memorias = []

            for item in dados:
                if isinstance(item, dict):
                    conteudo = item.get("conteudo", "")
                else:
                    conteudo = item

                conteudo = str(conteudo).strip()

                if conteudo:
                    memorias.append(conteudo)

        except Exception:
            return None

        if not memorias:
            return None

        # ------------------------------------------------------
        # NOME
        # ------------------------------------------------------

        perguntas_nome = (
            "qual meu nome",
            "qual e meu nome",
            "como eu me chamo",
            "como me chamo",
            "quem sou eu",
        )

        if any(
            frase in pergunta_normalizada
            for frase in perguntas_nome
        ):

            for memoria in memorias:

                match = re.search(
                    r"MEU NOME[ ÉE]+([^,.;]+)",
                    memoria,
                    flags=re.IGNORECASE
                )

                if match:

                    nome = match.group(1).strip()

                    if nome:
                        return (
                            f"Seu nome é {nome.title()}."
                        )

        # ------------------------------------------------------
        # TIME
        # ------------------------------------------------------

        perguntas_time = (
            "qual meu time",
            "qual e meu time",
            "para qual time eu torco",
            "pra qual time eu torco",
            "para que time eu torco",
            "qual meu time de coracao",
            "qual e meu time de coracao",
            "time do coracao",
        )

        if any(
            frase in pergunta_normalizada
            for frase in perguntas_time
        ):

            for memoria in memorias:

                memoria_normalizada = (
                    self._normalizar_pergunta_memoria(
                        memoria
                    )
                )

                if (
                    memoria_normalizada.startswith(
                        "torco para "
                    )
                    or memoria_normalizada.startswith(
                        "torco pelo "
                    )
                    or memoria_normalizada.startswith(
                        "torco pelo "
                    )
                ):

                    partes = re.split(
                        r"\b(?:para|pelo)\b",
                        memoria,
                        maxsplit=1,
                        flags=re.IGNORECASE
                    )

                    if len(partes) == 2:

                        time = (
                            partes[1]
                            .strip()
                            .rstrip(".")
                        )

                        if time:
                            return (
                                f"Você torce para {time.title()}."
                            )

        # ------------------------------------------------------
        # CASAMENTO / ESPOSA
        # ------------------------------------------------------

        perguntas_casamento = (
            "com quem sou casado",
            "com quem eu sou casado",
            "quem e minha esposa",
            "quem é minha esposa",
            "qual o nome da minha esposa",
            "qual e o nome da minha esposa",
        )

        if any(
            frase in pergunta_normalizada
            for frase in perguntas_casamento
        ):

            for memoria in memorias:

                match = re.search(
                    r"SOU CASADO COM\s+([^,.;]+)",
                    memoria,
                    flags=re.IGNORECASE
                )

                if match:

                    nome = match.group(1).strip()

                    if nome:
                        return (
                            f"Você é casado com {nome.title()}."
                        )

        # ------------------------------------------------------
        # MEMORIA GERAL DO USUARIO
        # ------------------------------------------------------

        perguntas_gerais = (
            "o que voce sabe sobre mim",
            "o que você sabe sobre mim",
            "quais informacoes voce tem sobre mim",
            "quais informações você tem sobre mim",
            "o que sabe sobre mim",
        )

        if any(
            frase in pergunta_normalizada
            for frase in perguntas_gerais
        ):

            return (
                "Estas são as memórias que tenho sobre você:\n"
                + "\n".join(
                    f"- {memoria}"
                    for memoria in memorias
                )
            )

        return None

    # ============================================================
    # AÇÃO: IA
    # ============================================================

    def executar_ia(
        self,
        page,
        acao: dict,
    ) -> str:

        consulta = (
            acao.get("texto")
            or acao.get("consulta")
            or acao.get("pergunta")
            or acao.get("prompt")
            or ""
        )

        consulta = self._texto(
            consulta
        )

        if not consulta:
            raise ValueError(
                "A acao de IA nao contem uma pergunta."
            )

        # ======================================================
        # PRIMEIRA CAMADA: MEMORIA DETERMINISTICA
        # ======================================================

        resposta_memoria = (
            self.responder_memoria_direta(
                consulta
            )
        )

        if resposta_memoria:
            self.ultima_resposta = (
                resposta_memoria
            )

            self.ultimo_erro = ""

            return resposta_memoria

        contexto_memoria = str(
            acao.get("memoria_contexto")
            or ""
        ).strip()

        if contexto_memoria:
            memorias = contexto_memoria
        else:
            memorias = self.carregar_memorias()

        try:
            resposta = perguntar(
                consulta,
                memorias
            )

            resposta = self._texto(
                resposta
            )

            if not resposta:
                raise RuntimeError(
                    "O cerebro local nao retornou resposta."
                )

            self.ultima_resposta = resposta
            self.ultimo_erro = ""

            return resposta

        except Exception as erro:
            self.ultimo_erro = str(
                erro
            )

            raise RuntimeError(
                f"Erro ao consultar cerebro local: {erro}"
            ) from erro
    # ============================================================
    # AÇÃO: PESQUISA
    # ============================================================

    def executar_pesquisa(
        self,
        page,
        acao: dict,
    ) -> str:

        consulta = (
            acao.get("consulta")
            or acao.get("texto")
            or acao.get("pergunta")
            or ""
        )

        consulta = self._texto(
            consulta
        )

        if not consulta:

            raise ValueError(
                "A pesquisa está vazia."
            )

        return self.responder_com_chatgpt(
            page,
            consulta
        )

    # ============================================================
    # AÇÃO: ABRIR PROGRAMA
    # ============================================================

    def abrir_programa(
        self,
        acao: dict,
    ) -> str:

        programa = (
            acao.get("programa")
            or acao.get("valor")
            or acao.get("nome")
            or ""
        )

        programa = self._texto(
            programa
        )

        if not programa:

            raise ValueError(
                "Programa não informado."
            )

        programas = {
            "calculadora": "calc.exe",
            "notepad": "notepad.exe",
            "bloco de notas": "notepad.exe",
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "msedge": "msedge.exe",
            "edge": "msedge.exe",
            "microsoft edge": "msedge.exe",
            "explorer": "explorer.exe",
            "explorador": "explorer.exe",
            "explorador de arquivos": "explorer.exe",
            "taskmgr": "taskmgr.exe",
            "gerenciador de tarefas": "taskmgr.exe",
            "cmd": "cmd.exe",
            "prompt": "cmd.exe",
            "powershell": "powershell.exe",
        }

        comando = programas.get(
            programa.lower(),
            programa
        )

        print()
        print(
            f"JARVIS: Abrindo programa: {comando}"
        )

        try:

            subprocess.Popen(
                comando,
                shell=True
            )

        except Exception as erro:

            self.ultimo_erro = str(
                erro
            )

            raise RuntimeError(
                f"Não foi possível abrir '{programa}': {erro}"
            ) from erro

        return (
            f"Programa '{programa}' iniciado."
        )

    # ============================================================
    # AÇÃO: ABRIR URL
    # ============================================================

    def abrir_url(
        self,
        page,
        acao: dict,
    ) -> str:

        url = (
            acao.get("url")
            or acao.get("endereco")
            or acao.get("site")
            or ""
        )

        url = self._texto(
            url
        )

        if not url:

            raise ValueError(
                "URL não informada."
            )

        if not url.startswith(
            ("http://", "https://")
        ):

            url = "https://" + url

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        return (
            f"Página aberta: {page.url}"
        )

    # ============================================================
    # VOLTAR
    # ============================================================

    def voltar(
        self,
        page,
    ) -> str:

        page.go_back(
            wait_until="domcontentloaded",
            timeout=30000,
        )

        return (
            f"Página atual: {page.url}"
        )

    # ============================================================
    # AVANÇAR
    # ============================================================

    def avancar(
        self,
        page,
    ) -> str:

        page.go_forward(
            wait_until="domcontentloaded",
            timeout=30000,
        )

        return (
            f"Página atual: {page.url}"
        )

    # ============================================================
    # RECARREGAR
    # ============================================================

    def recarregar(
        self,
        page,
    ) -> str:

        page.reload(
            wait_until="domcontentloaded",
            timeout=30000,
        )

        return (
            f"Página recarregada: {page.url}"
        )

    # ============================================================
    # LER PÁGINA
    # ============================================================

    def ler_pagina(
        self,
        page,
    ) -> dict:

        titulo = ""

        try:

            titulo = page.title()

        except Exception:
            pass

        texto = ""

        try:

            texto = page.locator(
                "body"
            ).inner_text(
                timeout=5000
            )

        except Exception:
            pass

        links = []

        try:

            elementos = page.locator(
                "a"
            )

            quantidade = elementos.count()

            for indice in range(
                min(
                    quantidade,
                    100
                )
            ):

                elemento = (
                    elementos.nth(
                        indice
                    )
                )

                try:

                    links.append(
                        {
                            "texto":
                                elemento.inner_text(
                                    timeout=1000
                                ).strip(),

                            "href":
                                elemento.get_attribute(
                                    "href"
                                ) or "",
                        }
                    )

                except Exception:
                    continue

        except Exception:
            pass

        botoes = []

        try:

            elementos = page.locator(
                "button"
            )

            quantidade = elementos.count()

            for indice in range(
                min(
                    quantidade,
                    100
                )
            ):

                elemento = (
                    elementos.nth(
                        indice
                    )
                )

                try:

                    botoes.append(
                        {
                            "texto":
                                elemento.inner_text(
                                    timeout=1000
                                ).strip(),

                            "tipo":
                                elemento.get_attribute(
                                    "type"
                                ) or "",
                        }
                    )

                except Exception:
                    continue

        except Exception:
            pass

        campos = []

        try:

            elementos = page.locator(
                "input, textarea, "
                "[contenteditable='true']"
            )

            quantidade = elementos.count()

            for indice in range(
                min(
                    quantidade,
                    100
                )
            ):

                elemento = (
                    elementos.nth(
                        indice
                    )
                )

                try:

                    campos.append(
                        {
                            "tag":
                                elemento.evaluate(
                                    "(el) => el.tagName"
                                ),

                            "tipo":
                                elemento.get_attribute(
                                    "type"
                                ) or "",

                            "nome":
                                elemento.get_attribute(
                                    "name"
                                ) or "",

                            "id":
                                elemento.get_attribute(
                                    "id"
                                ) or "",

                            "placeholder":
                                elemento.get_attribute(
                                    "placeholder"
                                ) or "",
                        }
                    )

                except Exception:
                    continue

        except Exception:
            pass

        return {
            "url": page.url,
            "titulo": titulo,
            "links": links,
            "botoes": botoes,
            "campos": campos,
            "scripts": [],
            "texto": texto,
        }

    # ============================================================
    # AÇÃO: POWERSHELL
    # ============================================================

    def executar_powershell(
        self,
        acao: dict,
    ) -> str:

        comando = (
            acao.get("valor")
            or acao.get("comando")
            or acao.get("script")
            or ""
        )

        comando = self._texto(
            comando
        )

        if not comando:
            raise ValueError(
                "Comando PowerShell não informado."
            )

        print()
        print(
            f"JARVIS: Executando PowerShell: {comando}"
        )

        try:

            subprocess.Popen(
                [
                    "powershell.exe",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    comando,
                ],
                shell=False,
            )

        except Exception as erro:

            self.ultimo_erro = str(
                erro
            )

            raise RuntimeError(
                f"Não foi possível executar PowerShell: {erro}"
            ) from erro

        self.ultimo_erro = ""

        return "Comando PowerShell executado."


    # ============================================================
    # EXECUTAR HABILIDADE
    # ============================================================

    def executar_habilidade(
        self,
        page,
        habilidade: dict,
    ) -> str | dict:

        acoes = habilidade.get("acoes", [])

        if not isinstance(acoes, list):
            raise TypeError(
                "Ações da habilidade devem ser uma lista."
            )

        if not acoes:
            return "A habilidade não possui ações."

        resultados = []

        print()
        print(
            f"JARVIS: Executando habilidade: "
            f"{habilidade.get('nome', 'sem nome')}"
        )

        for acao in acoes:

            if not isinstance(acao, dict):
                continue

            resultado = self.executar(
                page,
                acao
            )

            resultados.append(resultado)

        return resultados



    # ============================================================
    # ============================================================
    # AÇÃO: CLIMA
    # ============================================================

    def executar_clima(self) -> str:
        try:
            from servicos.localizacao import obter_localizacao
            from servicos.clima import clima_por_localizacao

            localizacao = obter_localizacao()
            clima = clima_por_localizacao(localizacao)

            temperatura = clima.get("temperatura")
            sensacao = clima.get("sensacao")
            umidade = clima.get("umidade")
            precipitacao = clima.get("precipitacao")
            vento = clima.get("vento_kmh")

            partes = []

            if temperatura is not None:
                partes.append(
                    f"Temperatura: {temperatura:.1f} °C"
                )

            if sensacao is not None:
                partes.append(
                    f"sensação: {sensacao:.1f} °C"
                )

            if umidade is not None:
                partes.append(
                    f"umidade: {umidade:.0f}%"
                )

            if precipitacao is not None:
                partes.append(
                    f"precipitação: {precipitacao:.1f} mm"
                )

            if vento is not None:
                partes.append(
                    f"vento: {vento:.1f} km/h"
                )

            if not partes:
                resposta = (
                    "Não consegui obter os dados atuais do clima."
                )
            else:
                resposta = "; ".join(partes) + "."

            self.ultima_resposta = resposta
            self.ultimo_erro = ""


            return resposta

        except Exception as erro:
            self.ultimo_erro = str(erro)

            print(
                f"JARVIS: Erro ao consultar clima: {erro}"
            )

            return "Não consegui consultar o clima agora."

    # EXECUTAR
    # ============================================================

    def executar(
        self,
        page,
        acao: dict,
    ) -> str | dict:

        if not isinstance(
            acao,
            dict
        ):

            raise TypeError(
                "Ação inválida: esperado dict."
            )

        tipo_acao = (
            acao.get("acao")
            or acao.get("tipo")
            or ""
        )

        tipo_acao = self._texto(
            tipo_acao
        ).lower()

        if tipo_acao in {
            "habilidade",
            "skill",
        }:

            return self.executar_habilidade(
                page,
                acao
            )



        if tipo_acao == "clima":
            return self.executar_clima()


        if tipo_acao == "ia":

            return self.executar_ia(
                page,
                acao
            )


        if tipo_acao in {
            "powershell",
            "power_shell",
            "ps",
        }:

            return self.executar_powershell(
                acao
            )

        if tipo_acao in {
            "pesquisar_google",
            "pesquisar",
            "pesquisa",
            "buscar",
        }:

            return self.executar_pesquisa(
                page,
                acao
            )

        if tipo_acao in {
            "programa",
            "abrir_programa",
        }:

            return self.abrir_programa(
                acao
            )

        if tipo_acao in {
            "abrir",
            "abrir_url",
            "url",
        }:

            return self.abrir_url(
                page,
                acao
            )

        if tipo_acao == "voltar":

            return self.voltar(
                page
            )

        if tipo_acao in {
            "avancar",
            "avançar",
        }:

            return self.avancar(
                page
            )

        if tipo_acao in {
            "recarregar",
            "reload",
        }:

            return self.recarregar(
                page
            )

        if tipo_acao in {
            "ler",
            "ler_pagina",
            "analisar",
        }:

            return self.ler_pagina(
                page
            )

        return (
            "Ação desconhecida: "
            f"{tipo_acao}"
        )


if __name__ == "__main__":

    executor = Executor()

    print()
    print("=" * 60)
    print(" JARVIS - EXECUTOR")
    print("=" * 60)

    print()
    print("Personalidade:")

    print(
        executor.carregar_personalidade()
        or "NÃO ENCONTRADA"
    )

    print()
    print("Memórias:")

    print(
        executor.carregar_memorias()
        or "NENHUMA"
    )






