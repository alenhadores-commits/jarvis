# -*- coding: utf-8 -*-

import os
import time
import unicodedata
import asyncio
from concurrent.futures import ThreadPoolExecutor


class ChatGPT:

    URL = "https://chatgpt.com/"

    def __init__(self, page):
        if page is None:
            raise ValueError(
                "A página do navegador não foi fornecida."
            )

        self.page = page

    # ==========================================================
    # CAMPO DE MENSAGEM
    # ==========================================================

    def _obter_campo_mensagem(self):

        page = self.page

        seletores = [
            "textarea[placeholder='Pergunte ao ChatGPT']",
            "textarea[aria-label='Chat com o ChatGPT']",
            "textarea[placeholder*='ChatGPT']",
            "textarea",
        ]

        ultimo_erro = None

        for seletor in seletores:

            try:

                campo = page.locator(
                    seletor
                ).first

                if campo.count() == 0:
                    continue

                campo.wait_for(
                    state="visible",
                    timeout=5000
                )

                if (
                    campo.is_visible()
                    and campo.is_enabled()
                ):

                    print(
                        f"JARVIS: Campo encontrado: {seletor}"
                    )

                    return campo

            except Exception as erro:

                ultimo_erro = erro

        raise RuntimeError(
            "Não encontrei o campo de mensagem do ChatGPT."
        ) from ultimo_erro

    # ==========================================================
    # DETECTAR EMOJI
    # ==========================================================

    def _eh_emoji(self, caractere):

        if not caractere:
            return False

        codigo = ord(caractere)

        # ------------------------------------------------------
        # Principais blocos Unicode utilizados por emojis
        # ------------------------------------------------------

        blocos = [
            (0x1F000, 0x1FAFF),
            (0x1FC00, 0x1FFFD),
            (0x2600, 0x27BF),
            (0x2300, 0x23FF),
            (0x2B00, 0x2BFF),
            (0xFE00, 0xFE0F),
            (0x1F1E6, 0x1F1FF),
        ]

        for inicio, fim in blocos:

            if inicio <= codigo <= fim:
                return True

        # ------------------------------------------------------
        # Símbolos Unicode classificados como símbolos
        # ------------------------------------------------------

        categoria = unicodedata.category(
            caractere
        )

        if categoria in (
            "So",
            "Sk",
        ):

            return True

        return False

    # ==========================================================
    # LOCALIZAR ÚLTIMO EMOJI
    # ==========================================================

    def _ultimo_emoji(self, texto):

        if not texto:
            return -1

        texto = texto.rstrip()

        if not texto:
            return -1

        # ------------------------------------------------------
        # Procurar de trás para frente.
        #
        # Isso é importante porque o emoji final pode ser:
        #
        # 😂
        # 🐷💚
        # 👨‍💻
        # 🇧🇷
        #
        # ------------------------------------------------------

        for indice in range(
            len(texto) - 1,
            -1,
            -1
        ):

            caractere = texto[indice]

            if self._eh_emoji(
                caractere
            ):

                return indice

        return -1

    # ==========================================================
    # VERIFICAR SE RESPOSTA TERMINA EM EMOJI
    # ==========================================================

    def _termina_com_emoji(self, texto):

        if not texto:
            return False

        texto = texto.rstrip()

        if not texto:
            return False

        ultimo = texto[-1]

        # ------------------------------------------------------
        # Caso normal
        # ------------------------------------------------------

        if self._eh_emoji(
            ultimo
        ):
            return True

        # ------------------------------------------------------
        # Emoji com variation selector
        # ------------------------------------------------------

        if len(texto) >= 2:

            if (
                ord(texto[-1]) == 0xFE0F
                and self._eh_emoji(
                    texto[-2]
                )
            ):

                return True

        # ------------------------------------------------------
        # Emoji com modificador de pele
        # ------------------------------------------------------

        if len(texto) >= 2:

            codigo = ord(
                texto[-1]
            )

            if (
                0x1F3FB <= codigo <= 0x1F3FF
                and self._eh_emoji(
                    texto[-2]
                )
            ):

                return True

        return False

    # ==========================================================
    # CORTAR RESPOSTA NO ÚLTIMO EMOJI
    # ==========================================================

    def _cortar_no_emoji(self, texto):

        if not texto:
            return ""

        texto = texto.strip()

        if not texto:
            return ""

        # ------------------------------------------------------
        # Se já termina em emoji, preservar exatamente a
        # resposta completa.
        # ------------------------------------------------------

        if self._termina_com_emoji(
            texto
        ):

            return texto

        # ------------------------------------------------------
        # Caso exista conteúdo depois do emoji, localizar o
        # último emoji encontrado.
        #
        # Isso protege contra algum conteúdo residual capturado
        # depois da resposta.
        # ------------------------------------------------------

        indice = self._ultimo_emoji(
            texto
        )

        if indice < 0:
            return texto

        fim = indice + 1

        # ------------------------------------------------------
        # Preservar variation selector.
        # ------------------------------------------------------

        while (
            fim < len(texto)
            and ord(texto[fim]) in (
                0xFE0E,
                0xFE0F,
            )
        ):

            fim += 1

        # ------------------------------------------------------
        # Preservar modificador de pele.
        # ------------------------------------------------------

        if fim < len(texto):

            codigo = ord(
                texto[fim]
            )

            if (
                0x1F3FB <= codigo <= 0x1F3FF
            ):

                fim += 1

        return texto[:fim].strip()

    # ==========================================================
    # LOCALIZAR RESPOSTAS DO ASSISTENTE
    # ==========================================================

    def _obter_respostas_assistente(self):

        page = self.page

        # ------------------------------------------------------
        # IMPORTANTE:
        #
        # Captura estrutural.
        #
        # NÃO utilizar:
        #
        # body
        # main
        # .markdown genérico
        # article genérico
        #
        # porque esses elementos podem conter textos da
        # interface do ChatGPT.
        # ------------------------------------------------------

        seletor = (
            "[data-message-author-role='assistant']"
        )

        try:

            elementos = page.locator(
                seletor
            )

            quantidade = elementos.count()

            if quantidade > 0:

                return elementos

        except Exception:

            pass

        return None

    # ==========================================================
    # OBTER TEXTO DA ÚLTIMA RESPOSTA
    # ==========================================================

    def _obter_texto_ultima_resposta(self):

        respostas = (
            self._obter_respostas_assistente()
        )

        if respostas is None:
            return ""

        try:

            quantidade = respostas.count()

            if quantidade == 0:
                return ""

            # --------------------------------------------------
            # Começar pela última mensagem do assistente.
            # --------------------------------------------------

            for indice in range(
                quantidade - 1,
                -1,
                -1
            ):

                try:

                    elemento = respostas.nth(
                        indice
                    )

                    if not elemento.is_visible():
                        continue

                    texto = elemento.inner_text(
                        timeout=3000
                    ).strip()

                    if not texto:
                        continue

                    return texto

                except Exception:

                    continue

        except Exception:

            pass

        return ""

    # ==========================================================
    # ENVIAR PERGUNTA
    # ==========================================================

    def _enviar_pergunta(self, campo):

        page = self.page

        # ------------------------------------------------------
        # ENTER
        # ------------------------------------------------------

        try:

            campo.press(
                "Enter"
            )

            page.wait_for_timeout(
                1200
            )

            try:

                valor = campo.input_value()

                if not valor.strip():

                    return True

            except Exception:

                return True

        except Exception as erro:

            print(
                f"JARVIS: Enter falhou: {erro}"
            )

        # ------------------------------------------------------
        # BOTÃO ENVIAR
        # ------------------------------------------------------

        botoes = [

            "button[data-testid='send-button']",

            "button[aria-label='Enviar']",

            "button[aria-label*='Enviar']",

            "button[aria-label='Send']",

            "button[aria-label*='Send']",

        ]

        for seletor in botoes:

            try:

                lista = page.locator(
                    seletor
                )

                quantidade = lista.count()

                for i in range(
                    quantidade
                ):

                    try:

                        botao = lista.nth(
                            i
                        )

                        if (
                            botao.is_visible()
                            and botao.is_enabled()
                        ):

                            botao.click(
                                timeout=10000
                            )

                            page.wait_for_timeout(
                                1000
                            )

                            return True

                    except Exception:

                        continue

            except Exception:

                continue

        return False

    # ==========================================================
    # AGUARDAR RESPOSTA
    # ==========================================================

    def _aguardar_resposta(
        self,
        texto_anterior="",
        timeout=90
    ):
        inicio = time.time()

        ultimo_texto = ""
        estabilidade = 0
        resposta_detectada = False

        print(
            "JARVIS: Monitorando resposta do ChatGPT..."
        )

        while (
            time.time() - inicio
            < timeout
        ):
            texto = (
                self._obter_texto_ultima_resposta()
            )

            if texto:
                # ------------------------------------------------
                # IGNORAR RESPOSTA ANTERIOR
                # ------------------------------------------------

                if (
                    texto_anterior
                    and texto == texto_anterior
                    and not resposta_detectada
                ):
                    try:
                        self.page.wait_for_timeout(
                            500
                        )
                    except Exception:
                        pass

                    continue

                resposta_detectada = True

                # ------------------------------------------------
                # RESPOSTA MUDOU
                # ------------------------------------------------

                if texto != ultimo_texto:
                    ultimo_texto = texto
                    estabilidade = 0

                    print(
                        "JARVIS: Resposta atualizada."
                    )

                else:
                    estabilidade += 1

                # ------------------------------------------------
                # RESPOSTA ESTÁVEL
                #
                # Não depender de emoji.
                # ------------------------------------------------

                if estabilidade >= 6:
                    resposta_final = (
                        texto.strip()
                    )

                    if resposta_final:
                        print(
                            "JARVIS: Resposta estabilizada."
                        )

                        return resposta_final

            try:
                self.page.wait_for_timeout(
                    500
                )
            except Exception:
                time.sleep(
                    0.5
                )

        # --------------------------------------------------------
        # ÚLTIMA TENTATIVA
        # --------------------------------------------------------

        texto = (
            self._obter_texto_ultima_resposta()
        )

        if texto:
            if (
                not texto_anterior
                or texto != texto_anterior
            ):
                return texto.strip()

        raise RuntimeError(
            "O ChatGPT não apresentou uma resposta válida dentro do tempo esperado."
        )
    # ==========================================================
    # LIMPAR RESPOSTA
    # ==========================================================

    def _limpar_resposta(self, texto):

        if not texto:
            return ""

        texto = texto.strip()

        marcadores = [
            "O ChatGPT disse:",
            "ChatGPT:",
        ]

        for marcador in marcadores:

            if texto.startswith(
                marcador
            ):

                texto = texto[
                    len(marcador):
                ].strip()

        return texto

    # ==========================================================
    # PESQUISAR / CONVERSAR
    # ==========================================================

    def pesquisar(
        self,
        consulta: str
    ):

        consulta = str(
            consulta or ""
        ).strip()

        if not consulta:

            raise ValueError(
                "A consulta está vazia."
            )

        page = self.page

        print()
        print(
            "JARVIS: Preparando ChatGPT..."
        )

        # ------------------------------------------------------
        # VERIFICAR URL
        # ------------------------------------------------------

        try:

            url_atual = page.url

        except Exception:

            url_atual = ""

        if "chatgpt.com" not in url_atual:

            print(
                "JARVIS: Abrindo ChatGPT..."
            )

            page.goto(
                self.URL,
                wait_until="domcontentloaded",
                timeout=60000
            )

        page.wait_for_timeout(
            3000
        )

        print(
            "JARVIS: Página carregada."
        )

        # ------------------------------------------------------
        # RESPOSTA EXISTENTE
        # ------------------------------------------------------

        texto_anterior = (
            self._obter_texto_ultima_resposta()
        )

        if texto_anterior:

            print(
                "JARVIS: Resposta anterior identificada."
            )

        else:

            print(
                "JARVIS: Nenhuma resposta anterior encontrada."
            )

        # ------------------------------------------------------
        # CAMPO
        # ------------------------------------------------------

        print(
            "JARVIS: Localizando campo de mensagem..."
        )

        campo = (
            self._obter_campo_mensagem()
        )

        print(
            "JARVIS: Clicando no campo..."
        )

        campo.click(
            timeout=10000
        )

        # ------------------------------------------------------
        # LIMPAR CAMPO
        # ------------------------------------------------------

        print(
            "JARVIS: Limpando campo..."
        )

        try:

            campo.press(
                "Control+A"
            )

            campo.press(
                "Backspace"
            )

        except Exception:

            pass

        # ------------------------------------------------------
        # ESCREVER
        # ------------------------------------------------------

        print(
            "JARVIS: Escrevendo pergunta..."
        )

        try:

            campo.fill(
                consulta,
                timeout=10000
            )

        except Exception:

            campo.click()

            campo.press(
                "Control+A"
            )

            campo.press(
                "Backspace"
            )

            campo.type(
                consulta,
                delay=5
            )

        print(
            "JARVIS: Pergunta escrita corretamente."
        )

        # ------------------------------------------------------
        # ENVIAR
        # ------------------------------------------------------

        print(
            "JARVIS: Enviando pergunta..."
        )

        enviado = (
            self._enviar_pergunta(
                campo
            )
        )

        if not enviado:

            raise RuntimeError(
                "Não consegui enviar a pergunta para o ChatGPT."
            )

        print(
            "JARVIS: Pergunta enviada."
        )

        # ------------------------------------------------------
        # AGUARDAR
        # ------------------------------------------------------

        print(
            "JARVIS: Aguardando resposta..."
        )

        resposta = (
            self._aguardar_resposta(
                texto_anterior=texto_anterior,
                timeout=90
            )
        )

        # ------------------------------------------------------
        # LIMPAR
        # ------------------------------------------------------

        resposta = (
            self._limpar_resposta(
                resposta
            )
        )

        if not resposta:

            raise RuntimeError(
                "O ChatGPT retornou uma resposta vazia."
            )

        # ------------------------------------------------------
        # IMPORTANTE:
        # NÃO imprimir a resposta aqui.
        #
        # O executor/jarvis.py recebe o retorno e imprime.
        # ------------------------------------------------------

        print(
            "JARVIS: Resposta recebida."
        )

        return resposta


# ==============================================================
# FUNÇÃO DE COMPATIBILIDADE
# ==============================================================

def _consultar_chatgpt_sync(
    consulta: str
) -> str:

    consulta = str(
        consulta or ""
    ).strip()

    if not consulta:

        raise ValueError(
            "A consulta está vazia."
        )

    try:

        from playwright.sync_api import sync_playwright

        base_dir = os.path.dirname(
            os.path.dirname(
                os.path.abspath(__file__)
            )
        )

        perfil = os.path.join(
            base_dir,
            "dados_chromium"
        )

        with sync_playwright() as playwright:

            contexto = (
                playwright.chromium.launch_persistent_context(
                    user_data_dir=perfil,
                    headless=False,
                    viewport={
                        "width": 1400,
                        "height": 900
                    }
                )
            )

            try:

                if contexto.pages:

                    page = contexto.pages[0]

                else:

                    page = contexto.new_page()

                cliente = ChatGPT(
                    page
                )

                return cliente.pesquisar(
                    consulta
                )

            finally:

                contexto.close()

    except Exception as erro:

        raise RuntimeError(
            f"Erro ao consultar ChatGPT: {erro}"
        ) from erro


def consultar_chatgpt(
    consulta: str
) -> str:

    consulta = str(
        consulta or ""
    ).strip()

    if not consulta:

        raise ValueError(
            "A consulta está vazia."
        )

    # ========================================================
    # VERIFICAR SE JA EXISTE UM EVENT LOOP
    # ========================================================

    try:

        asyncio.get_running_loop()

        dentro_asyncio = True

    except RuntimeError:

        dentro_asyncio = False

    # ========================================================
    # FORA DO ASYNCIO
    #
    # Pode usar Playwright Sync normalmente.
    # ========================================================

    if not dentro_asyncio:

        return _consultar_chatgpt_sync(
            consulta
        )

    # ========================================================
    # DENTRO DO ASYNCIO
    #
    # Playwright Sync nao pode ser iniciado nesta thread.
    # Executar toda a operacao em uma thread separada.
    # ========================================================

    print(
        "JARVIS: asyncio detectado."
    )

    print(
        "JARVIS: Executando navegador ChatGPT em thread separada..."
    )

    with ThreadPoolExecutor(
        max_workers=1,
        thread_name_prefix="JARVIS-ChatGPT"
    ) as executor:

        futuro = executor.submit(
            _consultar_chatgpt_sync,
            consulta
        )

        return futuro.result()