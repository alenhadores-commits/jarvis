# -*- coding: utf-8 -*-

"""
J.A.R.V.I.S
EXECUTOR DE HABILIDADES

ACOES:

1  - abrir_programa
2  - abrir_site
3  - powershell
4  - esperar
5  - falar
6  - localizar_elemento
7  - esperar_elemento
8  - clicar
9  - digitar
10 - pressionar_tecla
11 - ler
12 - rolar
13 - mover_mouse
14 - loop
15 - copiar
16 - colar
17 - selecionar_tudo
"""

from __future__ import annotations

import subprocess
import time
from typing import Any

import pyautogui

from playwright.sync_api import (
    sync_playwright,
    Browser,
    BrowserContext,
    Page,
)


class ExecutorHabilidades:

    def __init__(self) -> None:

        self.playwright = None
        self.browser: Browser | None = None
        self.contexto: BrowserContext | None = None
        self.pagina: Page | None = None
        self.elemento = None

        self.porta_chrome = 9222

        self.perfil_chrome = (
            r"C:\Users\almei\JARVIS\browser_profile_habilidades"
        )

        self.ultimo_texto = ""
        self.ultimo_resultado = None
        self.variaveis: dict[str, Any] = {}

    # ============================================================
    # EXECUTAR
    # ============================================================

    def executar(
        self,
        habilidade: dict[str, Any]
    ) -> str:

        nome = str(
            habilidade.get(
                "nome",
                "habilidade"
            )
        ).strip()

        acoes = habilidade.get(
            "acoes",
            []
        )

        print()
        print("=" * 60)
        print(
            f" JARVIS - HABILIDADE: {nome}"
        )
        print("=" * 60)

        if not isinstance(
            acoes,
            list
        ) or not acoes:

            return (
                "A habilidade nao possui acoes."
            )

        try:

            self._executar_lista(
                acoes
            )

        except Exception as erro:

            print()
            print(
                "JARVIS: Falha na habilidade."
            )

            print(
                f"ERRO: {erro}"
            )

            return (
                f"A habilidade '{nome}' falhou: {erro}"
            )

        finally:

            self.elemento = None

        print()
        print("=" * 60)

        return (
            f"Habilidade '{nome}' executada "
            f"com sucesso."
        )

    # ============================================================
    # EXECUTAR LISTA DE ACOES
    # ============================================================

    def _executar_lista(
        self,
        acoes: list[dict[str, Any]]
    ) -> None:

        indice = 0

        while indice < len(acoes):

            acao = acoes[indice]

            if not isinstance(
                acao,
                dict
            ):

                raise ValueError(
                    f"Acao {indice + 1} invalida."
                )

            tipo = str(
                acao.get(
                    "tipo",
                    ""
                )
            ).strip().lower()

            valor = acao.get(
                "valor",
                ""
            )

            if isinstance(
                valor,
                str
            ):

                valor = valor.strip()

            print()
            print(
                f"[{indice + 1}] {tipo}: {valor}"
            )

            self._executar_acao(
                tipo,
                valor,
                acao
            )

            indice += 1

    # ============================================================
    # VARIAVEIS
    # ============================================================

    def _resolver_valor(
        self,
        valor: Any
    ) -> Any:

        if not isinstance(
            valor,
            str
        ):
            return valor

        texto = valor

        texto = texto.replace(
            "{ultimo_texto}",
            self.ultimo_texto
        )

        texto = texto.replace(
            "{ultimo_resultado}",
            ""
            if self.ultimo_resultado is None
            else str(self.ultimo_resultado)
        )

        for nome, valor_variavel in self.variaveis.items():

            texto = texto.replace(
                "{" + str(nome) + "}",
                str(valor_variavel)
            )

        return texto

    def _definir_variavel(
        self,
        valor: Any
    ) -> None:

        if isinstance(
            valor,
            dict
        ):

            nome = str(
                valor.get(
                    "nome",
                    ""
                )
            ).strip()

            conteudo = valor.get(
                "valor",
                ""
            )

        else:

            texto = str(
                valor
            )

            if "=" not in texto:

                raise ValueError(
                    "Use: nome=valor"
                )

            nome, conteudo = texto.split(
                "=",
                1
            )

            nome = nome.strip()
            conteudo = conteudo.strip()

        if not nome:

            raise ValueError(
                "Nome da variavel nao informado."
            )

        conteudo = self._resolver_valor(
            conteudo
        )

        self.variaveis[nome] = conteudo
        self.ultimo_resultado = conteudo

        print(
            f"JARVIS: Variavel '{nome}' definida."
        )

    def _salvar_resultado(
        self,
        valor: Any
    ) -> None:

        nome = str(
            valor
        ).strip()

        if not nome:

            raise ValueError(
                "Nome da variavel nao informado."
            )

        resultado = self.ultimo_resultado

        if resultado is None:

            resultado = self.ultimo_texto

        self.variaveis[nome] = (
            resultado
        )

        print(
            f"JARVIS: Resultado salvo em '{nome}'."
        )

    def _usar_variavel(
        self,
        valor: Any
    ) -> None:

        nome = str(
            valor
        ).strip()

        if (
            nome.startswith("{")
            and nome.endswith("}")
        ):

            nome = nome[1:-1].strip()

        if nome not in self.variaveis:

            raise ValueError(
                f"Variavel nao encontrada: {nome}"
            )

        resultado = self.variaveis[nome]

        self.ultimo_resultado = resultado

        print()
        print(
            "JARVIS:",
            resultado
        )
    # ============================================================
    # CONDICOES
    # ============================================================

    def _obter_texto_comparacao(
        self,
        valor: Any
    ) -> str:

        valor = self._resolver_valor(
            valor
        )

        if valor is None:
            return ""

        return str(
            valor
        ).strip()

    def _condicao_se_existir(
        self,
        valor: Any
    ) -> None:

        texto = self._obter_texto_comparacao(
            valor
        )

        if not texto:
            raise ValueError(
                "Texto da condicao nao informado."
            )

        pagina = self._garantir_pagina()

        encontrado = False

        try:

            loc = pagina.get_by_text(
                texto,
                exact=False
            )

            quantidade = loc.count()

            for indice in range(
                quantidade
            ):

                item = loc.nth(
                    indice
                )

                try:

                    if item.is_visible(
                        timeout=500
                    ):
                        encontrado = True
                        break

                except Exception:
                    continue

        except Exception:
            encontrado = False

        self.ultimo_resultado = encontrado

        if encontrado:

            print(
                f"JARVIS: Condicao verdadeira: '{texto}' existe."
            )

        else:

            print(
                f"JARVIS: Condicao falsa: '{texto}' nao existe."
            )

    def _condicao_se_nao_existir(
        self,
        valor: Any
    ) -> None:

        self._condicao_se_existir(
            valor
        )

        resultado = bool(
            self.ultimo_resultado
        )

        self.ultimo_resultado = not resultado

        texto = self._obter_texto_comparacao(
            valor
        )

        if self.ultimo_resultado:

            print(
                f"JARVIS: Condicao verdadeira: '{texto}' nao existe."
            )

        else:

            print(
                f"JARVIS: Condicao falsa: '{texto}' existe."
            )

    def _condicao_se_contem(
        self,
        valor: Any
    ) -> None:

        texto = self._obter_texto_comparacao(
            valor
        )

        origem = self.ultimo_texto

        if not origem:
            origem = str(
                self.ultimo_resultado
                if self.ultimo_resultado is not None
                else ""
            )

        resultado = (
            texto.lower()
            in origem.lower()
        )

        self.ultimo_resultado = resultado
        return resultado

        if resultado:

            print(
                f"JARVIS: O texto contem '{texto}'."
            )

        else:

            print(
                f"JARVIS: O texto nao contem '{texto}'."
            )

    def _condicao_se_igual(
        self,
        valor: Any
    ) -> None:

        texto = self._obter_texto_comparacao(
            valor
        )

        origem = self.ultimo_texto

        if not origem:
            origem = str(
                self.ultimo_resultado
                if self.ultimo_resultado is not None
                else ""
            )

        resultado = (
            origem.strip().lower()
            == texto.strip().lower()
        )

        self.ultimo_resultado = resultado
        return resultado

        if resultado:

            print(
                f"JARVIS: Comparacao verdadeira."
            )

        else:

            print(
                f"JARVIS: Comparacao falsa."
            )
    # ============================================================
    def _condicao(
        self,
        valor: Any
    ) -> None:

        if not isinstance(valor, dict):
            print("JARVIS: Condicao invalida.")
            return

        definicao = valor.get("se")
        entao = valor.get("entao", [])
        senao = valor.get("senao", [])

        if not isinstance(definicao, dict):
            print("JARVIS: Definicao da condicao invalida.")
            return

        tipo_condicao = definicao.get("tipo")
        valor_condicao = definicao.get("valor")

        if not tipo_condicao:
            print("JARVIS: Tipo da condicao nao informado.")
            return

        self._executar_acao(
            tipo_condicao,
            valor_condicao,
            definicao
        )

        resultado = bool(self.ultimo_resultado)

        if resultado:
            print("JARVIS: Condicao verdadeira. Executando ENTao.")

            if isinstance(entao, list):
                self._executar_lista(entao)

        else:
            print("JARVIS: Condicao falsa. Executando SENAO.")

            if isinstance(senao, list):
                self._executar_lista(senao)

    def _loop_condicional(
        self,
        valor: Any
    ) -> None:

        if not isinstance(valor, dict):
            print("JARVIS: Loop condicional invalido.")
            return

        condicao = valor.get("condicao")
        acoes = valor.get("acoes", [])
        maximo = valor.get("maximo", 10)

        if not isinstance(condicao, dict):
            print("JARVIS: Condicao do loop invalida.")
            return

        if not isinstance(acoes, list):
            print("JARVIS: Acoes do loop invalidas.")
            return

        try:
            maximo = int(maximo)
        except (TypeError, ValueError):
            maximo = 10

        maximo = max(1, min(maximo, 100))

        for tentativa in range(1, maximo + 1):

            print(
                f"JARVIS: Loop condicional - tentativa {tentativa}/{maximo}."
            )

            tipo_condicao = condicao.get("tipo")
            valor_condicao = condicao.get("valor")

            if not tipo_condicao:
                print("JARVIS: Tipo da condicao nao informado.")
                return

            self._executar_acao(
                tipo_condicao,
                valor_condicao,
                condicao
            )

            if bool(self.ultimo_resultado):
                print(
                    "JARVIS: Condicao satisfeita. Loop encerrado."
                )
                return

            if acoes:
                self._executar_lista(acoes)

        print(
            "JARVIS: Limite maximo de tentativas atingido."
        )
    # ROTEADOR
    # ============================================================

    def _executar_acao(
        self,
        tipo: str,
        valor: Any,
        acao: dict[str, Any],
    ) -> None:

        valor = self._resolver_valor(
            valor
        )

        if tipo == "se_existir":

            self._condicao_se_existir(
                valor
            )

            return

        if tipo == "se_nao_existir":

            self._condicao_se_nao_existir(
                valor
            )

            return

        if tipo == "se_contem":

            self._condicao_se_contem(
                valor
            )

            return

        if tipo == "se_igual":

            self._condicao_se_igual(
                valor
            )

            return

        if tipo == "condicao":

            self._condicao(
                valor
            )

            return

        if tipo == "loop_condicional":

            self._loop_condicional(
                valor
            )

            return
        if tipo == "definir_variavel":

            self._definir_variavel(
                valor
            )

            return

        if tipo == "salvar_resultado":

            self._salvar_resultado(
                valor
            )

            return

        if tipo == "usar_variavel":

            self._usar_variavel(
                valor
            )

            return

        if tipo == "abrir_programa":

            self._abrir_programa(
                str(valor)
            )

            return

        if tipo == "abrir_site":

            self._abrir_site(
                str(valor)
            )

            return

        if tipo == "powershell":

            self._powershell(
                str(valor)
            )

            return

        if tipo == "esperar":

            self._esperar(
                valor
            )

            return

        if tipo == "falar":

            print()
            print(
                "JARVIS:",
                valor
            )

            return

        if tipo == "localizar_elemento":

            self._localizar_elemento(
                str(valor)
            )

            return

        if tipo == "esperar_elemento":

            self._esperar_elemento(
                str(valor),
                acao
            )

            return

        if tipo == "clicar":

            self._clicar(
                str(valor)
            )

            return

        if tipo == "digitar":

            self._digitar(
                str(valor)
            )

            return

        if tipo == "pressionar_tecla":

            self._pressionar_tecla(
                str(valor)
            )

            return

        if tipo == "ler":

            self._ler(
                str(valor)
            )

            return

        if tipo == "rolar":

            self._rolar(
                str(valor)
            )

            return

        if tipo == "mover_mouse":

            self._mover_mouse(
                str(valor)
            )

            return

        if tipo == "clique_direito":

            self._clique_direito(
                str(valor)
            )

            return

        if tipo == "clicar_tela":

            self._clicar_tela(
                str(valor)
            )

            return

        if tipo == "duplo_clique":

            self._duplo_clique(
                str(valor)
            )

            return

        if tipo == "mover_mouse_tela":

            self._mover_mouse_tela(
                str(valor)
            )

            return

        if tipo == "arrastar_mouse":

            self._arrastar_mouse(
                str(valor)
            )

            return

        if tipo == "combinacao_teclas":

            self._combinacao_teclas(
                str(valor)
            )

            return

        if tipo == "loop":

            self._loop(
                valor
            )

            return

        if tipo == "copiar":

            self._copiar()

            return

        if tipo == "colar":

            self._colar()

            return

        if tipo == "selecionar_tudo":

            self._selecionar_tudo()

            return

        raise ValueError(
            f"Acao desconhecida: {tipo}"
        )

    # ============================================================
    # ESPERAR
    # ============================================================

    def _esperar(
        self,
        valor: Any
    ) -> None:

        segundos = float(
            valor
        )

        if segundos < 0:

            raise ValueError(
                "Tempo nao pode ser negativo."
            )

        time.sleep(
            segundos
        )

    # ============================================================
    # CHROME
    # ============================================================

    def _abrir_programa(
        self,
        programa: str
    ) -> None:

        programa = programa.strip()

        if not programa:

            raise ValueError(
                "Programa nao informado."
            )

        if programa.lower() in {
            "chrome",
            "google chrome",
            "chrome.exe",
        }:

            self._abrir_chrome()

            return

        subprocess.Popen(
            programa,
            shell=True
        )

    def _abrir_chrome(self) -> None:

        print(
            "JARVIS: Iniciando Chrome para automacao..."
        )

        argumentos = [
            "--remote-debugging-port=9222",
            f"--user-data-dir={self.perfil_chrome}",
            "--no-first-run",
            "--no-default-browser-check",
        ]

        candidatos = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            "chrome.exe",
        ]

        processo = None

        ultimo_erro = None

        for caminho in candidatos:

            try:

                processo = subprocess.Popen(
                    [
                        caminho,
                        *argumentos
                    ],
                    shell=False
                )

                break

            except Exception as erro:

                ultimo_erro = erro

        if processo is None:

            raise RuntimeError(
                "Nao foi possivel iniciar o Chrome: "
                f"{ultimo_erro}"
            )

        self._conectar_chrome()

    # ============================================================
    # CONEXAO
    # ============================================================

    def _conectar_chrome(
        self
    ) -> None:

        if self.playwright is None:

            self.playwright = (
                sync_playwright().start()
            )

        ultimo_erro = None

        for _ in range(40):

            try:

                self.browser = (
                    self.playwright
                    .chromium
                    .connect_over_cdp(
                        "http://127.0.0.1:9222"
                    )
                )

                contextos = (
                    self.browser.contexts
                )

                if not contextos:

                    time.sleep(0.5)

                    continue

                self.contexto = (
                    contextos[0]
                )

                paginas = [
                    pagina
                    for pagina in self.contexto.pages
                    if not pagina.is_closed()
                ]

                if paginas:

                    self.pagina = paginas[-1]

                else:

                    self.pagina = (
                        self.contexto.new_page()
                    )

                print(
                    "JARVIS: Chrome conectado."
                )

                return

            except Exception as erro:

                ultimo_erro = erro

                time.sleep(0.5)

        raise RuntimeError(
            "Nao foi possivel conectar ao Chrome "
            f"na porta 9222: {ultimo_erro}"
        )

    def _garantir_pagina(
        self
    ) -> Page:

        if self.pagina is not None:

            try:

                if not self.pagina.is_closed():

                    return self.pagina

            except Exception:

                pass

        # Tentar conectar ao Chrome que ja esteja rodando.

        try:

            self._conectar_chrome()

        except Exception:

            # Se a porta 9222 nao estiver ativa,
            # iniciar o Chrome proprio das habilidades.

            print(
                "JARVIS: Chrome de habilidades nao esta conectado."
            )

            print(
                "JARVIS: Iniciando Chrome..."
            )

            self._abrir_chrome()

        if self.pagina is None:

            raise RuntimeError(
                "Nenhuma pagina disponivel."
            )

        return self.pagina
    def _abrir_site(
        self,
        url: str
    ) -> None:

        url = url.strip()

        if not url:

            raise ValueError(
                "URL nao informada."
            )

        if not url.startswith(
            (
                "http://",
                "https://"
            )
        ):

            url = (
                "https://"
                + url
            )

        pagina = (
            self._garantir_pagina()
        )

        pagina.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        print(
            f"JARVIS: Pagina aberta: {pagina.url}"
        )

    # ============================================================
    # LOCALIZAR ELEMENTO
    # ============================================================

    def _localizar_elemento(
        self,
        alvo: str
    ) -> None:

        alvo = alvo.strip()

        if not alvo:

            raise ValueError(
                "Elemento nao informado."
            )

        pagina = (
            self._garantir_pagina()
        )

        self.elemento = None

        alvo_normalizado = (
            alvo.lower()
        )

        # --------------------------------------------------------
        # CAIXA DE MENSAGEM
        # --------------------------------------------------------

        if alvo_normalizado in {
            "caixa de mensagem",
            "caixa mensagem",
            "campo de mensagem",
            "mensagem",
        }:

            seletores = [
                "textarea",
                "[contenteditable='true']",
                "[role='textbox']",
            ]

            for seletor in seletores:

                try:

                    elementos = pagina.locator(
                        seletor
                    )

                    quantidade = elementos.count()

                    for indice in range(
                        quantidade
                    ):

                        loc = elementos.nth(
                            indice
                        )

                        if loc.is_visible(
                            timeout=1000
                        ):

                            self.elemento = loc

                            print(
                                "JARVIS: Caixa de mensagem localizada."
                            )

                            return

                except Exception:

                    continue

            raise RuntimeError(
                "Caixa de mensagem nao encontrada."
            )

        # --------------------------------------------------------
        # ENVIAR
        # --------------------------------------------------------

        if alvo_normalizado in {
            "enviar",
            "botao enviar",
            "send",
        }:

            seletores = [
                "button[aria-label*='Enviar']",
                "button[aria-label*='enviar']",
                "button[data-testid*='send']",
                "button[type='submit']",
            ]

            for seletor in seletores:

                try:

                    loc = pagina.locator(
                        seletor
                    ).first

                    if loc.count() > 0 and loc.is_visible(
                        timeout=1000
                    ):

                        self.elemento = loc

                        print(
                            "JARVIS: Botao enviar localizado."
                        )

                        return

                except Exception:

                    continue

            # Busca por texto/aria-label

            try:

                botoes = pagina.locator(
                    "button"
                )

                quantidade = botoes.count()

                for indice in range(
                    quantidade
                ):

                    botao = botoes.nth(
                        indice
                    )

                    try:

                        texto = (
                            botao.inner_text(
                                timeout=500
                            )
                            .strip()
                            .lower()
                        )

                        aria = (
                            botao.get_attribute(
                                "aria-label"
                            )
                            or ""
                        ).lower()

                        if (
                            "enviar" in texto
                            or "send" in texto
                            or "enviar" in aria
                            or "send" in aria
                        ):

                            if botao.is_visible(
                                timeout=500
                            ):

                                self.elemento = botao

                                return

                    except Exception:

                        continue

            except Exception:

                pass

            raise RuntimeError(
                "Botao enviar nao encontrado."
            )

        # --------------------------------------------------------
        # TEXTO VISIVEL
        # --------------------------------------------------------

        try:

            loc = pagina.get_by_text(
                alvo,
                exact=False
            ).first

            if loc.count() > 0:

                if loc.is_visible(
                    timeout=1000
                ):

                    self.elemento = loc

                    print(
                        f"JARVIS: Elemento localizado: {alvo}"
                    )

                    return

        except Exception:

            pass

        # --------------------------------------------------------
        # ARIA LABEL
        # --------------------------------------------------------

        try:

            loc = pagina.locator(
                "[aria-label]"
            )

            quantidade = loc.count()

            for indice in range(
                quantidade
            ):

                item = loc.nth(
                    indice
                )

                try:

                    aria = (
                        item.get_attribute(
                            "aria-label"
                        )
                        or ""
                    ).lower()

                    if (
                        alvo_normalizado
                        in aria
                    ):

                        if item.is_visible(
                            timeout=500
                        ):

                            self.elemento = item

                            print(
                                "JARVIS: Elemento localizado por aria-label."
                            )

                            return

                except Exception:

                    continue

        except Exception:

            pass

        raise RuntimeError(
            f"Elemento nao encontrado: {alvo}"
        )

    # ============================================================
    # ESPERAR ELEMENTO
    # ============================================================

    def _esperar_elemento(
        self,
        alvo: str,
        acao: dict[str, Any],
    ) -> None:

        timeout = float(
            acao.get(
                "timeout",
                30
            )
        )

        if timeout <= 0:

            timeout = 30

        inicio = time.time()

        while (
            time.time() - inicio
        ) < timeout:

            try:

                self._localizar_elemento(
                    alvo
                )

                return

            except Exception:

                time.sleep(
                    0.5
                )

        raise RuntimeError(
            f"Tempo esgotado esperando elemento: {alvo}"
        )

    # ============================================================
    # CLICAR
    # ============================================================

    def _clicar(
        self,
        valor: str
    ) -> None:

        valor = valor.strip()

        botao = "left"
        alvo = valor

        if valor.lower().startswith(
            "direito:"
        ):

            botao = "right"
            alvo = valor[
                len("direito:"):
            ].strip()

        elif valor.lower().startswith(
            "esquerdo:"
        ):

            botao = "left"
            alvo = valor[
                len("esquerdo:"):
            ].strip()

        elif valor.lower() in {
            "direito",
            "right",
        }:

            botao = "right"
            alvo = ""

        elif valor.lower() in {
            "esquerdo",
            "left",
        }:

            botao = "left"
            alvo = ""

        if alvo:

            self._localizar_elemento(
                alvo
            )

        if self.elemento is None:

            raise RuntimeError(
                "Nenhum elemento para clicar."
            )

        print(
            f"JARVIS: Clique {botao}."
        )

        self.elemento.click(
            button=botao,
            timeout=10000
        )

    # ============================================================
    # DIGITAR
    # ============================================================

    def _digitar(
        self,
        texto: str
    ) -> None:

        pagina = (
            self._garantir_pagina()
        )

        if self.elemento is None:

            self._localizar_elemento(
                "caixa de mensagem"
            )

        if self.elemento is None:

            raise RuntimeError(
                "Nenhum elemento selecionado."
            )

        print(
            "JARVIS: Digitando."
        )

        try:

            self.elemento.fill(
                texto,
                timeout=10000
            )

        except Exception:

            self.elemento.click(
                timeout=10000
            )

            pagina.keyboard.type(
                texto
            )

    # ============================================================
    # TECLADO
    # ============================================================

    def _pressionar_tecla(
        self,
        tecla: str
    ) -> None:

        pagina = (
            self._garantir_pagina()
        )

        tecla = str(tecla).strip()

        if not tecla:
            raise ValueError(
                "Tecla nao informada."
            )

        mapa_teclas = {
            "ENTER": "Enter",
            "ESC": "Escape",
            "ESCAPE": "Escape",
            "TAB": "Tab",
            "BACKSPACE": "Backspace",
            "DELETE": "Delete",
            "INSERT": "Insert",
            "HOME": "Home",
            "END": "End",
            "PAGEUP": "PageUp",
            "PAGEDOWN": "PageDown",
            "ARROWUP": "ArrowUp",
            "ARROWDOWN": "ArrowDown",
            "ARROWLEFT": "ArrowLeft",
            "ARROWRIGHT": "ArrowRight",
            "SPACE": " ",
            "SHIFT": "Shift",
            "CONTROL": "Control",
            "CTRL": "Control",
            "ALT": "Alt",
            "META": "Meta",
            "WINDOWS": "Meta",
            "F1": "F1",
            "F2": "F2",
            "F3": "F3",
            "F4": "F4",
            "F5": "F5",
            "F6": "F6",
            "F7": "F7",
            "F8": "F8",
            "F9": "F9",
            "F10": "F10",
            "F11": "F11",
            "F12": "F12",
        }

        tecla_original = tecla

        tecla_normalizada = mapa_teclas.get(
            tecla_original.upper(),
            tecla_original
        )

        print(
            f"JARVIS: Pressionando: {tecla_normalizada}"
        )

        pagina.keyboard.press(
            tecla_normalizada
        )
    def _ler(
        self,
        alvo: str
    ) -> None:

        pagina = (
            self._garantir_pagina()
        )

        alvo = alvo.strip().lower()

        if alvo in {
            "",
            "pagina",
            "página",
            "tela",
            "conteudo",
            "conteúdo",
        }:

            texto = pagina.locator(
                "body"
            ).inner_text(
                timeout=10000
            ).strip()

        else:

            try:

                self._localizar_elemento(
                    alvo
                )

                if self.elemento is None:

                    raise RuntimeError(
                        "Elemento nao localizado."
                    )

                texto = (
                    self.elemento.inner_text(
                        timeout=5000
                    )
                    .strip()
                )

            except Exception:

                texto = pagina.locator(
                    "body"
                ).inner_text(
                    timeout=10000
                ).strip()

        if not texto:

            raise RuntimeError(
                "Nenhum texto encontrado."
            )

        self.ultimo_texto = texto

        print()
        print(
            "=" * 60
        )
        print(
            " JARVIS - LEITURA"
        )
        print(
            "=" * 60
        )
        print(texto)
        print(
            "=" * 60
        )

    # ============================================================
    # ROLAR
    # ============================================================

    def _rolar(
        self,
        valor: str
    ) -> None:

        pagina = (
            self._garantir_pagina()
        )

        texto = valor.strip().lower()

        if not texto:

            texto = "baixo 600"

        partes = texto.split()

        direcao = partes[0]

        distancia = 600

        if len(partes) >= 2:

            try:

                distancia = int(
                    partes[1]
                )

            except ValueError:

                raise ValueError(
                    "Distancia de rolagem invalida."
                )

        if direcao in {
            "baixo",
            "down",
            "descendo",
        }:

            delta = abs(
                distancia
            )

        elif direcao in {
            "cima",
            "up",
            "subir",
        }:

            delta = -abs(
                distancia
            )

        else:

            raise ValueError(
                "Use 'cima' ou 'baixo'."
            )

        pagina.mouse.wheel(
            0,
            delta
        )

    # ============================================================
    # MOVER MOUSE
    # ============================================================

    def _mover_mouse(
        self,
        valor: str
    ) -> None:

        partes = valor.replace(
            ",",
            " "
        ).split()

        if len(partes) != 2:

            raise ValueError(
                "Use: x y"
            )

        try:

            x = float(
                partes[0]
            )

            y = float(
                partes[1]
            )

        except ValueError:

            raise ValueError(
                "Coordenadas invalidas."
            )

        pagina = (
            self._garantir_pagina()
        )

        pagina.mouse.move(
            x,
            y
        )

    # ============================================================
    # CLICAR NA TELA
    # Formato: x y
    # ============================================================

    # ============================================================
    # CLIQUE DIREITO NA TELA
    # Formato: x y
    # ============================================================

    def _clique_direito(
        self,
        valor: str
    ) -> None:

        partes = valor.replace(
            ",",
            " "
        ).split()

        if len(partes) != 2:
            raise ValueError(
                "Use: x y"
            )

        try:
            x = int(float(partes[0]))
            y = int(float(partes[1]))
        except ValueError as erro:
            raise ValueError(
                "Coordenadas invalidas."
            ) from erro

        print(
            f"JARVIS: Clique direito na tela em ({x}, {y})."
        )

        pyautogui.rightClick(
            x=x,
            y=y
        )

    # ============================================================
    # CLICAR NA TELA

    def _clicar_tela(
        self,
        valor: str
    ) -> None:

        partes = valor.replace(
            ",",
            " "
        ).split()

        if len(partes) != 2:
            raise ValueError(
                "Use: x y"
            )

        try:
            x = int(float(partes[0]))
            y = int(float(partes[1]))
        except ValueError as erro:
            raise ValueError(
                "Coordenadas invalidas."
            ) from erro

        print(
            f"JARVIS: Clique na tela em ({x}, {y})."
        )

        pyautogui.click(
            x=x,
            y=y
        )

    # ============================================================
    # DUPLO CLIQUE
    # Formato: x y
    # ============================================================

    def _duplo_clique(
        self,
        valor: str
    ) -> None:

        partes = valor.replace(
            ",",
            " "
        ).split()

        if len(partes) != 2:
            raise ValueError(
                "Use: x y"
            )

        try:
            x = int(float(partes[0]))
            y = int(float(partes[1]))
        except ValueError as erro:
            raise ValueError(
                "Coordenadas invalidas."
            ) from erro

        print(
            f"JARVIS: Duplo clique na tela em ({x}, {y})."
        )

        pyautogui.doubleClick(
            x=x,
            y=y,
            interval=0.1
        )

    # ============================================================
    # MOVER MOUSE NA TELA
    # Formato: x y
    # ============================================================

    def _mover_mouse_tela(
        self,
        valor: str
    ) -> None:

        partes = valor.replace(
            ",",
            " "
        ).split()

        if len(partes) != 2:
            raise ValueError(
                "Use: x y"
            )

        try:
            x = int(float(partes[0]))
            y = int(float(partes[1]))
        except ValueError as erro:
            raise ValueError(
                "Coordenadas invalidas."
            ) from erro

        print(
            f"JARVIS: Movendo mouse para ({x}, {y})."
        )

        pyautogui.moveTo(
            x=x,
            y=y,
            duration=0.2
        )

    # ============================================================
    # ARRASTAR MOUSE
    # Formato: x1 y1 x2 y2
    # ============================================================

    def _arrastar_mouse(
        self,
        valor: str
    ) -> None:

        partes = valor.replace(
            ",",
            " "
        ).split()

        if len(partes) != 4:
            raise ValueError(
                "Use: x1 y1 x2 y2"
            )

        try:
            x1 = int(float(partes[0]))
            y1 = int(float(partes[1]))
            x2 = int(float(partes[2]))
            y2 = int(float(partes[3]))
        except ValueError as erro:
            raise ValueError(
                "Coordenadas invalidas."
            ) from erro

        print(
            f"JARVIS: Arrastando de ({x1}, {y1}) para ({x2}, {y2})."
        )

        pyautogui.moveTo(
            x=x1,
            y=y1,
            duration=0.2
        )

        pyautogui.dragTo(
            x=x2,
            y=y2,
            duration=0.5,
            button="left"
        )

    # ============================================================
    # ============================================================
    # COMBINACAO DE TECLAS
    # Exemplos:
    # ctrl c
    # ctrl+v
    # alt tab
    # ctrl shift esc
    # ============================================================

    def _combinacao_teclas(
        self,
        valor: str
    ) -> None:

        teclas = [
            tecla.strip().lower()
            for tecla in valor.replace(
                "+",
                " "
            ).split()
            if tecla.strip()
        ]

        if not teclas:
            raise ValueError(
                "Teclas nao informadas."
            )

        print(
            f"JARVIS: Pressionando: {' + '.join(teclas)}"
        )

        pyautogui.hotkey(
            *teclas
        )

    # ============================================================
    # COPIAR
    # ============================================================

    def _copiar(
        self
    ) -> None:

        pagina = (
            self._garantir_pagina()
        )

        pagina.keyboard.press(
            "Control+C"
        )

    # ============================================================
    # COLAR
    # ============================================================

    def _colar(
        self
    ) -> None:

        pagina = (
            self._garantir_pagina()
        )

        pagina.keyboard.press(
            "Control+V"
        )

    # ============================================================
    # SELECIONAR TUDO
    # ============================================================

    def _selecionar_tudo(
        self
    ) -> None:

        pagina = (
            self._garantir_pagina()
        )

        pagina.keyboard.press(
            "Control+A"
        )

    # ============================================================
    # LOOP
    # ============================================================

    def _loop(
        self,
        valor: Any
    ) -> None:

        """
        O loop pode receber:

        loop:
            {
                "vezes": 5,
                "acoes": [...]
            }

        ou diretamente:

        valor:
            [
                {...},
                {...}
            ]

        Quando usar o Centro de Ensino, o formato recomendado e:

        {
            "vezes": 5,
            "acoes": [...]
        }
        """

        if isinstance(
            valor,
            dict
        ):

            vezes = int(
                valor.get(
                    "vezes",
                    1
                )
            )

            acoes = valor.get(
                "acoes",
                []
            )

        elif isinstance(
            valor,
            list
        ):

            vezes = 1
            acoes = valor

        else:

            partes = str(
                valor
            ).split(
                "|",
                1
            )

            try:

                vezes = int(
                    partes[0]
                )

            except ValueError:

                vezes = 1

            acoes = []

            if len(partes) > 1:

                raise ValueError(
                    "Loop simples precisa de lista de acoes."
                )

        if vezes < 1:

            return

        if not isinstance(
            acoes,
            list
        ):

            raise ValueError(
                "Acoes do loop devem ser uma lista."
            )

        print(
            f"JARVIS: Executando loop {vezes} vez(es)."
        )

        for repeticao in range(
            vezes
        ):

            print(
                f"JARVIS: Loop {repeticao + 1}/{vezes}"
            )

            self._executar_lista(
                acoes
            )

    # ============================================================
    # POWERSHELL
    # ============================================================

    def _powershell(
        self,
        comando: str
    ) -> None:

        print()
        print(
            "JARVIS: A habilidade solicitou "
            "execucao de PowerShell."
        )


        subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                comando
            ],
            shell=False
        )

    # ============================================================
    # FECHAR
    # ============================================================

    def fechar_conexao(
        self
    ) -> None:

        try:

            if self.browser is not None:

                self.browser.close()

        except Exception:

            pass

        try:

            if self.playwright is not None:

                self.playwright.stop()

        except Exception:

            pass

        self.playwright = None
        self.browser = None
        self.contexto = None
        self.pagina = None
        self.elemento = None




















