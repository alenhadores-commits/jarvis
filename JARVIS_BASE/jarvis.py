# -*- coding: utf-8 -*-

"""
J.A.R.V.I.S Ã¢â‚¬â€ NÃƒÅ¡CLEO OPERACIONAL

Loop principal:
recebe comando (voz ou texto)
        Ã¢â€ â€œ
Orquestrador
        Ã¢â€ â€œ
Executor
        Ã¢â€ â€œ
resultado

O navegador do ChatGPT Ã© iniciado junto com o JARVIS
e permanece aberto durante toda a execuÃ§Ã£o.

A sessÃ£o do ChatGPT Ã© persistente atravÃ©s do perfil:

C:\\Users\\almei\\JARVIS\\browser_profile

As credenciais, quando configuradas, sÃ£o armazenadas
pelo Windows Credential Manager atravÃ©s do keyring.

A senha NÃƒÆ’O fica armazenada neste arquivo.
"""

from __future__ import annotations

import os
import socket
import subprocess
import time

from ai.compreensao_spacy import analisar_texto
import os
import re
import traceback
import io
import sys

from playwright.sync_api import (
    sync_playwright,
    BrowserContext,
    Page,
)

from ai.cerebro import (
    decidir_habilidade,
    perguntar,
)
from memoria_local import MemoriaLocal
from memoria_classificador import classificar_memoria
from memoria_retriever import MemoriaRetriever
from contextlib import redirect_stdout

from ai.orquestrador import Orquestrador
from ai.executor import Executor
from ai.langgraph_jarvis import criar_grafo_jarvis
from ai.aprendizado import obter_aprendizado
from ai.classificador_intencao import (
    classificar_intencao,
    obter_classificador,
)
from voz.reconhecimento import ouvir
from voz.voz import falar, inicializar_voz

from credenciais import (
    obter_email,
    obter_senha,
    garantir_credenciais,
)
from habilidades.gerenciador import (
    GerenciadorHabilidades,
)

from habilidades.executor import (
    ExecutorHabilidades,
)
from habilidades.ensino_natural import EnsinoNatural
from rag.chroma import BancoChroma
from rag.recuperador import Recuperador
from rag.indexador_v2 import IndexadorV2


# ================================================================
# CONFIGURAÃƒâ€¡ÃƒÆ’O
# ================================================================

COMANDOS_SAIDA = {
    "sair",
    "fechar",
    "encerrar",
}

MAX_ERROS_SEGUIDOS = 5

MODO_CONVERSA = None


# ================================================================
# PERFIL PERSISTENTE DO CHATGPT
# ================================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

PERFIL_NAVEGADOR = os.path.join(
    BASE_DIR,
    "browser_profile_test"
)

URL_CHATGPT = "https://chatgpt.com/"

URL_LOGIN = "https://chatgpt.com/auth/login"


# ================================================================
# EXIBIÃƒâ€¡ÃƒÆ’O DE PÃGINA
# ================================================================

def mostrar_pagina(resultado: dict) -> None:

    print("\n" + "=" * 50)
    print(" JARVIS - ANÃLISE DA PÃGINA")
    print("=" * 50)

    print("\nURL:")
    print(resultado.get("url", "Ã¢â‚¬â€"))

    print("\nTÃTULO:")
    print(resultado.get("titulo", "Ã¢â‚¬â€"))

    links = resultado.get("links", [])

    print("\nLINKS:", len(links))

    for link in links:

        print(
            f"  Texto: {link.get('texto', '')}"
        )

        print(
            f"  Href:  {link.get('href', '')}"
        )

    botoes = resultado.get("botoes", [])

    print("\nBOTÃƒâ€¢ES:", len(botoes))

    for botao in botoes:

        print(
            f"  Texto: {botao.get('texto', '')}"
        )

        print(
            f"  Tipo:  {botao.get('tipo', '')}"
        )

    campos = resultado.get("campos", [])

    print("\nCAMPOS:", len(campos))

    for campo in campos:

        print(
            f"  Tag:         {campo.get('tag', '')}"
        )

        print(
            f"  Tipo:        {campo.get('tipo', '')}"
        )

        print(
            f"  Nome:        {campo.get('nome', '')}"
        )

        print(
            f"  ID:          {campo.get('id', '')}"
        )

        print(
            f"  Placeholder: {campo.get('placeholder', '')}"
        )

    scripts = resultado.get("scripts", [])

    print(
        "\nSCRIPTS:",
        len(scripts)
    )

    print("\nTEXTO DA PÃGINA:")
    print("-" * 50)

    texto = resultado.get("texto") or ""

    print(texto[:3000])

    print("=" * 50)


# ================================================================
# ENTRADA DO USUÃRIO
# ================================================================

def obter_comando() -> str:

    global MODO_CONVERSA

    # --------------------------------------------------------
    # ESCOLHA DO MODO - SOMENTE NO INICIO DA CONVERSA
    # --------------------------------------------------------

    if MODO_CONVERSA is None:

        while True:

            print()
            print("=" * 50)
            print(" J.A.R.V.I.S")
            print("=" * 50)
            print("[1] Voz")
            print("[2] Texto")
            print("[3] Aprendizado")
            print("[4] Sair")
            print()

            try:

                opcao = input(
                    "Escolha: "
                ).strip()

            except EOFError:

                return "sair"

            if opcao == "1":

                MODO_CONVERSA = "voz"

                print()
                print(
                    "JARVIS: Modo voz ativado."
                )

                break

            if opcao == "2":

                MODO_CONVERSA = "texto"

                print()
                print(
                    "JARVIS: Modo texto ativado."
                )

                break

            if opcao == "3":

                try:
                    from habilidades.gerenciador import GerenciadorHabilidades

                    gerenciador = GerenciadorHabilidades()
                    gerenciador.menu()

                except Exception as erro:
                    print()
                    print(
                        f"JARVIS: Falha ao abrir o aprendizado: {erro}"
                    )

                continue

            if opcao == "4":

                return "sair"

            print(
                "JARVIS: Op??o inv?lida."
            )

    # CHAT CONTINUO
    # --------------------------------------------------------

    if MODO_CONVERSA == "voz":

        print()
        print(
            "JARVIS: Ouvindo..."
        )

        try:

            comando = ouvir()

            return (
                comando or ""
            ).strip()

        except Exception as erro:

            print(
                "JARVIS: NÃ£o consegui usar "
                "o microfone."
            )

            print(
                f"ERRO: {erro}"
            )

            return ""

    try:

        return input(
            "VocÃª: "
        ).strip()

    except EOFError:

        return "sair"


# ================================================================
# GERENCIADOR DO NAVEGADOR
# ================================================================

class NavegadorManager:

    def __init__(
        self,
        playwright,
        headless: bool = False,
    ):

        self._p = playwright

        self._headless = headless

        self.contexto: BrowserContext | None = None

        self.pagina: Page | None = None

        self._iniciar_navegador()

        self._criar_pagina()



    # ============================================================
    # INICIAR NAVEGADOR
    # ============================================================

    def _iniciar_navegador(self) -> None:

        print(
            "JARVIS: Inicializando Google Chrome..."
        )

        print(
            "JARVIS: Perfil:",
            PERFIL_NAVEGADOR
        )

        os.makedirs(
            PERFIL_NAVEGADOR,
            exist_ok=True
        )

        candidatos_chrome = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(
                r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"
            ),
        ]

        executavel_chrome = None

        for caminho in candidatos_chrome:

            if os.path.exists(caminho):

                executavel_chrome = caminho
                break

        if executavel_chrome is None:

            raise RuntimeError(
                "Google Chrome nao encontrado."
            )

        self.contexto = (
            self._p.chromium.launch_persistent_context(
                user_data_dir=PERFIL_NAVEGADOR,
                executable_path=executavel_chrome,
                headless=False,
                args=[
                    "--start-minimized",
                ],
            )
        )

        print(
            "JARVIS: Google Chrome iniciado."
        )


    # ============================================================
    # CRIAR / REUTILIZAR PÃGINA
    # ============================================================

    def _criar_pagina(self) -> None:

        if self.contexto is None:

            raise RuntimeError(
                "Contexto do navegador nÃ£o estÃ¡ disponÃ­vel."
            )

        paginas = [
            pagina
            for pagina in self.contexto.pages
            if not pagina.is_closed()
        ]

        # ========================================================
        # PROCURAR CHATGPT JÃ ABERTO
        # ========================================================

        for pagina in paginas:

            try:

                url = pagina.url.lower()

            except Exception:

                continue

            if "chatgpt.com" in url:

                self.pagina = pagina

                print(
                    "JARVIS: PÃ¡gina do ChatGPT reutilizada:",
                    pagina.url
                )

                return

        # ========================================================
        # REUTILIZAR UMA PÃGINA EXISTENTE
        # ========================================================

        if paginas:

            self.pagina = paginas[0]

            print(
                "JARVIS: PÃ¡gina existente reutilizada:",
                self.pagina.url
            )

            try:

                self.pagina.goto(
                    "https://chatgpt.com/",
                    wait_until="domcontentloaded",
                    timeout=30000,
                )

                print(
                    "JARVIS: ChatGPT aberto na pÃ¡gina existente."
                )

            except Exception as erro:

                print(
                    "JARVIS: NÃ£o consegui abrir o ChatGPT."
                )

                print(
                    f"ERRO: {erro}"
                )

            return

        # ========================================================
        # CRIAR PÃGINA NOVA
        # ========================================================

        self.pagina = (
            self.contexto.new_page()
        )

        try:

            self.pagina.goto(
                "https://chatgpt.com/",
                wait_until="domcontentloaded",
                timeout=30000,
            )

            print(
                "JARVIS: PÃ¡gina do ChatGPT criada."
            )

        except Exception as erro:

            print(
                "JARVIS: NÃ£o consegui abrir o ChatGPT."
            )

            print(
                f"ERRO: {erro}"
            )



    # ============================================================
    # VERIFICAR SE ESTÃ LOGADO
    # ============================================================

    def esta_logado(self) -> bool:

        if self.pagina is None:

            return False

        try:

            self.pagina.wait_for_load_state(
                "domcontentloaded",
                timeout=10000,
            )

        except Exception:

            pass

        url = self.pagina.url.lower()

        if (
            "/auth/" in url
            or "/login" in url
        ):

            return False

        try:

            campo = self.pagina.locator(
                "textarea[placeholder='Pergunte ao ChatGPT']"
            )

            if campo.count() > 0:

                if campo.first.is_visible(
                    timeout=3000
                ):

                    return True

        except Exception:

            pass

        try:

            campo = self.pagina.locator(
                "textarea"
            )

            if campo.count() > 0:

                if campo.first.is_visible(
                    timeout=3000
                ):

                    return True

        except Exception:

            pass

        return False


    # ============================================================
    # LOCALIZAR BOTÃƒÆ’O DE LOGIN
    # ============================================================

    def _botao_login(self):

        if self.pagina is None:

            return None

        seletores = [
            "button:has-text('Log in')",
            "button:has-text('Log In')",
            "button:has-text('Entrar')",
            "a:has-text('Log in')",
            "a:has-text('Entrar')",
        ]

        for seletor in seletores:

            try:

                locator = self.pagina.locator(
                    seletor
                )

                if locator.count() > 0:

                    if locator.first.is_visible(
                        timeout=2000
                    ):

                        return locator.first

            except Exception:

                continue

        return None


    # ============================================================
    # TENTAR LOGIN AUTOMÃTICO
    # ============================================================

    def _login_automatico(self) -> bool:

        if self.pagina is None:

            return False

        email = obter_email()

        senha = obter_senha()

        if not email or not senha:

            print(
                "JARVIS: Credenciais nÃ£o configuradas."
            )

            return False

        print(
            "JARVIS: Tentando autenticaÃ§Ã£o automÃ¡tica..."
        )

        try:

            self.pagina.goto(
                URL_LOGIN,
                wait_until="domcontentloaded",
                timeout=30000,
            )

        except Exception as erro:

            print(
                "JARVIS: Erro ao abrir autenticaÃ§Ã£o."
            )

            print(
                f"ERRO: {erro}"
            )

            return False

        try:

            self.pagina.wait_for_timeout(
                2000
            )

            # ----------------------------------------------------
            # CAMPO DE E-MAIL
            # ----------------------------------------------------

            seletores_email = [
                "input[type='email']",
                "input[name='email']",
                "input[autocomplete='username']",
            ]

            campo_email = None

            for seletor in seletores_email:

                locator = self.pagina.locator(
                    seletor
                )

                if locator.count() > 0:

                    try:

                        if locator.first.is_visible(
                            timeout=1500
                        ):

                            campo_email = locator.first

                            break

                    except Exception:

                        continue

            if campo_email is not None:

                campo_email.fill(email)

                print(
                    "JARVIS: E-mail preenchido."
                )

                # ------------------------------------------------
                # CONTINUAR
                # ------------------------------------------------

                botoes = [
                    "button:has-text('Continue')",
                    "button:has-text('Continuar')",
                    "button[type='submit']",
                ]

                clicou = False

                for seletor in botoes:

                    try:

                        botao = self.pagina.locator(
                            seletor
                        )

                        if botao.count() > 0:

                            if botao.first.is_visible(
                                timeout=1500
                            ):

                                botao.first.click()

                                clicou = True

                                break

                    except Exception:

                        continue

                if clicou:

                    self.pagina.wait_for_timeout(
                        1500
                    )

            # ----------------------------------------------------
            # CAMPO DE SENHA
            # ----------------------------------------------------

            seletores_senha = [
                "input[type='password']",
                "input[name='password']",
                "input[autocomplete='current-password']",
            ]

            campo_senha = None

            for seletor in seletores_senha:

                locator = self.pagina.locator(
                    seletor
                )

                if locator.count() > 0:

                    try:

                        if locator.first.is_visible(
                            timeout=2000
                        ):

                            campo_senha = locator.first

                            break

                    except Exception:

                        continue

            if campo_senha is None:

                print(
                    "JARVIS: A etapa de senha "
                    "nÃ£o apareceu automaticamente."
                )

                print(
                    "JARVIS: Verifique o navegador."
                )

                return False

            campo_senha.fill(senha)

            print(
                "JARVIS: Senha preenchida."
            )

            # ----------------------------------------------------
            # BOTÃƒÆ’O FINAL
            # ----------------------------------------------------

            botoes_final = [
                "button[type='submit']",
                "button:has-text('Continue')",
                "button:has-text('Continuar')",
                "button:has-text('Log in')",
                "button:has-text('Entrar')",
            ]

            clicou_final = False

            for seletor in botoes_final:

                try:

                    botao = self.pagina.locator(
                        seletor
                    )

                    if botao.count() > 0:

                        if botao.first.is_visible(
                            timeout=1500
                        ):

                            botao.first.click()

                            clicou_final = True

                            break

                except Exception:

                    continue

            if not clicou_final:

                print(
                    "JARVIS: NÃ£o encontrei o "
                    "botÃ£o final de autenticaÃ§Ã£o."
                )

                return False

            print(
                "JARVIS: AutenticaÃ§Ã£o enviada."
            )

            self.pagina.wait_for_timeout(
                5000
            )

            # ----------------------------------------------------
            # VERIFICAÃƒâ€¡ÃƒÆ’O FINAL
            # ----------------------------------------------------

            if self.esta_logado():

                print(
                    "JARVIS: CHATGPT AUTENTICADO."
                )

                return True

            print(
                "JARVIS: AutenticaÃ§Ã£o adicional "
                "pode ser necessÃ¡ria."
            )

            print(
                "JARVIS: Se aparecer 2FA, CAPTCHA "
                "ou passkey, conclua manualmente."
            )

            return False

        except Exception as erro:

            print(
                "JARVIS: NÃ£o foi possÃ­vel concluir "
                "o login automÃ¡tico."
            )

            print(
                f"ERRO: {erro}"
            )

            return False


    # ============================================================
    # PREPARAR CHATGPT
    # ============================================================

    def _preparar_chatgpt(self) -> None:

        if self.pagina is None:

            raise RuntimeError(
                "PÃ¡gina do navegador nÃ£o estÃ¡ disponÃ­vel."
            )

        print(
            "JARVIS: Preparando ChatGPT..."
        )

        try:

            self.pagina.goto(
                URL_CHATGPT,
                wait_until="domcontentloaded",
                timeout=30000,
            )

            self.pagina.wait_for_timeout(
                2000
            )

        except Exception as erro:

            print(
                "JARVIS: NÃ£o foi possÃ­vel carregar "
                "o ChatGPT agora."
            )

            print(
                f"ERRO: {erro}"
            )

            return

        # --------------------------------------------------------
        # JÃ ESTÃ LOGADO
        # --------------------------------------------------------

        if self.esta_logado():

            print(
                "JARVIS: CHATGPT: ONLINE."
            )

            print(
                "JARVIS: SESSÃƒÆ’O: AUTENTICADA."
            )

            print(
                "JARVIS: Navegador permanece "
                "ativo em segundo plano."
            )

            return

        # --------------------------------------------------------
        # NÃƒÆ’O ESTÃ LOGADO
        # --------------------------------------------------------

        print(
            "JARVIS: CHATGPT nÃ£o estÃ¡ autenticado."
        )

        if not garantir_credenciais():

            print(
                "JARVIS: Nenhuma credencial disponÃ­vel."
            )

            print(
                "JARVIS: O login deverÃ¡ ser "
                "feito manualmente."
            )

            return

        # --------------------------------------------------------
        # LOGIN AUTOMÃTICO
        # --------------------------------------------------------

        if self._login_automatico():

            return

        # --------------------------------------------------------
        # AGUARDAR LOGIN MANUAL
        # --------------------------------------------------------

        print()
        print("=" * 50)
        print(" JARVIS - AUTENTICAÃƒâ€¡ÃƒÆ’O")
        print("=" * 50)
        print(
            "JARVIS: Conclua a autenticaÃ§Ã£o "
            "na janela do navegador."
        )
        print(
            "JARVIS: Aguardando login..."
        )

        for _ in range(60):

            try:

                if self.esta_logado():

                    print(
                        "JARVIS: LOGIN CONFIRMADO."
                    )

                    print(
                        "JARVIS: CHATGPT ONLINE."
                    )

                    return

            except Exception:

                pass

            self.pagina.wait_for_timeout(
                1000
            )

        print(
            "JARVIS: Tempo de autenticaÃ§Ã£o "
            "esgotado."
        )


    # ============================================================
    # GARANTIR PÃGINA
    # ============================================================

    def garantir_pagina(self) -> Page:

        contexto_ok = (
            self.contexto is not None
        )

        pagina_ok = (
            self.pagina is not None
            and not self.pagina.is_closed()
        )

        if contexto_ok and pagina_ok:

            return self.pagina

        print(
            "JARVIS: PÃ¡gina atual invÃ¡lida."
        )

        print(
            "JARVIS: Tentando recuperar navegador..."
        )

        try:

            if self.contexto is not None:

                paginas = self.contexto.pages

                for pagina in paginas:

                    if not pagina.is_closed():

                        self.pagina = pagina

                        print(
                            "JARVIS: PÃ¡gina recuperada."
                        )

                        return pagina

        except Exception:

            pass

        self._fechar_contexto_silencioso()

        self._iniciar_navegador()

        self._criar_pagina()

        self._preparar_chatgpt()

        if self.pagina is None:

            raise RuntimeError(
                "NÃ£o foi possÃ­vel recuperar "
                "a pÃ¡gina do ChatGPT."
            )

        return self.pagina


    # ============================================================
    # FECHAR CONTEXTO
    # ============================================================

    def _fechar_contexto_silencioso(self) -> None:

        if self.contexto is not None:

            try:

                self.contexto.close()

            except Exception:

                pass

        self.contexto = None

        self.pagina = None


    # ============================================================
    # FECHAR TUDO
    # ============================================================

    def fechar(self) -> None:

        print(
            "JARVIS: Encerrando navegador..."
        )

        self._fechar_contexto_silencioso()

        print(
            "JARVIS: Navegador encerrado."
        )



# ================================================================
# CENTRO DE ENSINO
# ================================================================


def listar_comandos(
    gerenciador: GerenciadorHabilidades
) -> None:

    habilidades = gerenciador.listar()

    print()
    print("=" * 50)
    print(" JARVIS - COMANDOS CADASTRADOS")
    print("=" * 50)

    if not habilidades:

        print()
        print("JARVIS: Nenhum comando ensinado.")

        return

    print()

    for indice, habilidade in enumerate(
        habilidades,
        start=1
    ):

        print(
            f"[{indice}] {habilidade.get('nome', 'Sem nome')}"
        )

        print(
            "    Gatilhos:",
            ", ".join(
                habilidade.get(
                    "gatilhos",
                    []
                )
            )
        )

        print(
            "    AÃ§Ãµes:",
            len(
                habilidade.get(
                    "acoes",
                    []
                )
            )
        )

        print()


def editar_comando(
    gerenciador: GerenciadorHabilidades
) -> None:

    habilidades = gerenciador.listar()

    if not habilidades:

        print()
        print("JARVIS: Nenhum comando para editar.")

        return

    print()
    print("=" * 50)
    print(" JARVIS - EDITAR COMANDO")
    print("=" * 50)

    print()

    for indice, habilidade in enumerate(
        habilidades,
        start=1
    ):

        print(
            f"[{indice}] {habilidade.get('nome', 'Sem nome')}"
        )

    print()

    try:

        escolha = int(
            input(
                "NÃºmero do comando: "
            ).strip()
        ) - 1

    except ValueError:

        print(
            "JARVIS: NÃºmero invÃ¡lido."
        )

        return

    if escolha < 0 or escolha >= len(habilidades):

        print(
            "JARVIS: Comando inexistente."
        )

        return

    atual = habilidades[escolha]

    nome_antigo = atual.get(
        "nome",
        ""
    )

    print()
    print(
        f"Nome atual: {nome_antigo}"
    )

    novo_nome = input(
        "Novo nome (Enter mantÃ©m): "
    ).strip()

    if not novo_nome:

        novo_nome = nome_antigo

    print()
    print(
        "Gatilhos atuais:",
        ", ".join(
            atual.get(
                "gatilhos",
                []
            )
        )
    )

    entrada = input(
        "Novos gatilhos separados por | (Enter mantÃ©m): "
    ).strip()

    if entrada:

        gatilhos = [
            item.strip()
            for item in entrada.split("|")
            if item.strip()
        ]

    else:

        gatilhos = atual.get(
            "gatilhos",
            []
        )

    nova_habilidade = {
        "nome": novo_nome,
        "gatilhos": gatilhos,
        "acoes": atual.get(
            "acoes",
            []
        ),
        "ativa": atual.get(
            "ativa",
            True
        ),
    }

    if gerenciador.atualizar(
        nome_antigo,
        nova_habilidade
    ):

        print()
        print(
            "JARVIS: Comando atualizado."
        )

    else:

        print()
        print(
            "JARVIS: NÃ£o foi possÃ­vel atualizar."
        )


def apagar_comando(
    gerenciador: GerenciadorHabilidades
) -> None:

    habilidades = gerenciador.listar()

    if not habilidades:

        print()
        print("JARVIS: Nenhum comando para apagar.")

        return

    print()
    print("=" * 50)
    print(" JARVIS - APAGAR COMANDO")
    print("=" * 50)

    print()

    for indice, habilidade in enumerate(
        habilidades,
        start=1
    ):

        print(
            f"[{indice}] {habilidade.get('nome', 'Sem nome')}"
        )

    print()

    try:

        escolha = int(
            input(
                "NÃºmero do comando: "
            ).strip()
        ) - 1

    except ValueError:

        print(
            "JARVIS: NÃºmero invÃ¡lido."
        )

        return

    if escolha < 0 or escolha >= len(habilidades):

        print(
            "JARVIS: Comando inexistente."
        )

        return

    nome = habilidades[escolha].get(
        "nome",
        ""
    )

    print()
    print(
        f"Comando selecionado: {nome}"
    )

    confirmacao = input(
        "Digite SIM para apagar: "
    ).strip().lower()

    if confirmacao != "sim":

        print(
            "JARVIS: OperaÃ§Ã£o cancelada."
        )

        return

    if gerenciador.remover(nome):

        print()
        print(
            "JARVIS: Comando apagado."
        )

    else:

        print()
        print(
            "JARVIS: NÃ£o foi possÃ­vel apagar."
        )


def gerenciar_comandos(
    gerenciador: GerenciadorHabilidades
) -> None:

    while True:

        print()
        print("=" * 50)
        print(" JARVIS - GERENCIADOR DE COMANDOS")
        print("=" * 50)

        print()
        print("[1] Ensinar novo comando")
        print("[2] Ver comandos")
        print("[3] Editar comando")
        print("[4] Apagar comando")
        print("[5] Voltar ao menu")
        print()

        escolha = input(
            "Escolha: "
        ).strip()

        if escolha == "1":

            ensinar_comando(
                gerenciador
            )

            continue

        if escolha == "2":

            listar_comandos(
                gerenciador
            )

            input(
                "\nPressione ENTER para continuar..."
            )

            continue

        if escolha == "3":

            editar_comando(
                gerenciador
            )

            input(
                "\nPressione ENTER para continuar..."
            )

            continue

        if escolha == "4":

            apagar_comando(
                gerenciador
            )

            input(
                "\nPressione ENTER para continuar..."
            )

            continue

        if escolha == "5":

            return

        print()
        print(
            "JARVIS: OpÃ§Ã£o invÃ¡lida."
        )

def ensinar_frase_natural(
    gerenciador: GerenciadorHabilidades
) -> None:

    print()
    print("=" * 60)
    print(" JARVIS - ENSINO NATURAL")
    print("=" * 60)

    print()
    print(
        "JARVIS: Explique em uma Ãºnica frase o que devo aprender."
    )

    print()
    print(
        "Exemplo:"
    )
    print(
        "quando eu disser estudar, abra o chrome, espere 2 segundos e fale estou pronto"
    )

    print()

    descricao = input(
        "Frase: "
    ).strip()

    if not descricao:
        print(
            "JARVIS: Nenhuma frase informada."
        )
        return

    interpretador = EnsinoNatural()

    resultado = interpretador.interpretar(
        descricao
    )

    if not resultado:
        print()
        print(
            "JARVIS: NÃ£o consegui interpretar essa frase."
        )
        return

    gatilho = str(
        resultado.get("gatilho", "")
    ).strip()

    acoes = resultado.get(
        "acoes",
        []
    )

    if not gatilho or not acoes:
        print(
            "JARVIS: A habilidade ficou incompleta."
        )
        return

    habilidade = gerenciador.adicionar(
        gatilho,
        [gatilho],
        acoes
    )

    print()
    print("=" * 60)
    print(" HABILIDADE APRENDIDA")
    print("=" * 60)

    print(
        "Nome:",
        habilidade["nome"]
    )

    print(
        "Gatilho:",
        gatilho
    )

    print(
        "AÃ§Ãµes:"
    )

    for indice, acao in enumerate(
        acoes,
        start=1
    ):
        print(
            f"  {indice}. "
            f"{acao.get('tipo', '')} -> "
            f"{acao.get('valor', '')}"
        )

    try:

        indexador = IndexadorV2(
            raiz_projeto=BASE_DIR
        )

        caminho_habilidades = os.path.join(
            BASE_DIR,
            "habilidades",
            "habilidades.json"
        )

        resultado_indexacao = (
            indexador.indexar_arquivo(
                caminho_habilidades,
                forcar=True
            )
        )

        print()
        print(
            "JARVIS: Habilidade registrada no Chroma."
        )

        print(
            f"JARVIS: Status RAG: "
            f"{resultado_indexacao.get('status')}"
        )

        print(
            f"JARVIS: Chunks: "
            f"{resultado_indexacao.get('chunks', 0)}"
        )

    except Exception as erro:

        print()
        print(
            f"JARVIS: Habilidade salva, "
            f"mas falha ao indexar no Chroma: {erro}"
        )

    print()
    print(
        "JARVIS: Aprendi essa habilidade."
    )


def ensinar_comando(
    gerenciador: GerenciadorHabilidades
) -> None:

    print()
    print("=" * 60)
    print(" JARVIS - CENTRO DE ENSINO")
    print("=" * 60)

    print()
    print(
        "JARVIS: Vamos ensinar uma nova habilidade."
    )

    print()
    print(
        "[1] Ensino por frase natural"
    )
    print(
        "[2] Ensino manual"
    )
    print()

    modo = input(
        "Escolha: "
    ).strip()

    if modo == "1":

        ensinar_frase_natural(
            gerenciador
        )

        return

    if modo != "2":

        print(
            "JARVIS: OpÃ§Ã£o invÃ¡lida."
        )

        return

    nome = input(
        "Nome da habilidade: "
    ).strip()

    if not nome:
        print(
            "JARVIS: Nome obrigatorio."
        )
        return

    print()
    print(
        "Digite as frases que devem ativar essa habilidade."
    )
    print(
        "Deixe vazio para terminar."
    )

    gatilhos = []

    while True:

        gatilho = input(
            "Gatilho: "
        ).strip()

        if not gatilho:
            break

        gatilhos.append(
            gatilho
        )

    if not gatilhos:
        print(
            "JARVIS: Nenhum gatilho informado."
        )
        return

    mapa_acoes = {
        "1": "abrir_programa",
        "2": "abrir_site",
        "4": "esperar",
        "5": "falar",
        "6": "localizar_elemento",
        "7": "esperar_elemento",
        "8": "clicar",
        "9": "digitar",
        "10": "pressionar_tecla",
        "11": "ler",
        "12": "rolar",
        "13": "mover_mouse",
        "14": "copiar",
        "15": "colar",
        "16": "selecionar_tudo",
        "17": "clicar_tela",
        "18": "duplo_clique",
        "19": "clique_direito",
        "20": "mover_mouse_tela",
        "21": "arrastar_mouse",
        "22": "combinacao_teclas",
    }

    acoes = []

    while True:

        print()
        print("-" * 60)
        print(" ACOES DISPONIVEIS")
        print("-" * 60)

        print("1  - abrir_programa")
        print("2  - abrir_site")
        print("4  - esperar")
        print("5  - falar")
        print("6  - localizar_elemento")
        print("7  - esperar_elemento")
        print("8  - clicar")
        print("9  - digitar")
        print("10 - pressionar_tecla")
        print("11 - ler")
        print("12 - rolar")
        print("13 - mover_mouse")
        print("14 - copiar")
        print("15 - colar")
        print("16 - selecionar_tudo")
        print("17 - clicar_tela")
        print("18 - duplo_clique")
        print("19 - clique_direito")
        print("20 - mover_mouse_tela")
        print("21 - arrastar_mouse")
        print("22 - combinacao_teclas")

        print()
        print("0  - finalizar e salvar")

        opcao = input(
            "Escolha a acao: "
        ).strip()

        if opcao == "0":
            break

        tipo = mapa_acoes.get(
            opcao
        )

        if tipo is None:
            print(
                "JARVIS: Opcao invalida."
            )
            continue

        acoes_sem_valor = {
            "copiar",
            "colar",
            "selecionar_tudo",
        }

        if tipo in acoes_sem_valor:

            acoes.append(
                {
                    "tipo": tipo,
                    "valor": ""
                }
            )

            print(
                f"JARVIS: Acao '{tipo}' adicionada."
            )

        else:

            exemplos = {
                "abrir_programa": "Exemplo: chrome",
                "abrir_site": "Exemplo: https://google.com",
                "esperar": "Exemplo: 2",
                "falar": "Texto que o JARVIS devera falar",
                "localizar_elemento": "Exemplo: nome do elemento",
                "esperar_elemento": "Exemplo: nome do elemento",
                "clicar": "Exemplo: nome ou seletor",
                "digitar": "Texto que devera ser digitado",
                "pressionar_tecla": "Exemplo: ENTER",
                "ler": "Exemplo: pagina",
                "rolar": "Exemplo: baixo",
                "mover_mouse": "Exemplo: x y",
                "clicar_tela": "Exemplo: 800 500",
                "duplo_clique": "Exemplo: 800 500",
                "clique_direito": "Exemplo: 800 500",
                "mover_mouse_tela": "Exemplo: 800 500",
                "arrastar_mouse": "Exemplo: 500 300 800 300",
                "combinacao_teclas": "Exemplo: ctrl c ou ctrl shift esc",
            }

            exemplo = exemplos.get(
                tipo,
                ""
            )

            if exemplo:
                print()
                print(
                    "JARVIS:",
                    exemplo
                )

            valor = input(
                f"Valor para {tipo}: "
            ).strip()

            if not valor:
                print(
                    "JARVIS: Valor obrigatorio."
                )
                continue

            acoes.append(
                {
                    "tipo": tipo,
                    "valor": valor,
                }
            )

            print(
                f"JARVIS: Acao '{tipo}' adicionada."
            )

        print()

        continuar = input(
            "Adicionar outra acao? [s/n]: "
        ).strip().lower()

        if continuar != "s":
            break

    if not acoes:
        print()
        print(
            "JARVIS: Nenhuma acao criada."
        )
        return

    habilidade = gerenciador.adicionar(
        nome,
        gatilhos,
        acoes
    )

    # --------------------------------------------------------
    # INDEXAR NOVA HABILIDADE NO CHROMA
    # --------------------------------------------------------

    try:

        indexador = IndexadorV2(
            raiz_projeto=BASE_DIR
        )

        caminho_habilidades = os.path.join(
            BASE_DIR,
            "habilidades",
            "habilidades.json"
        )

        resultado_indexacao = (
            indexador.indexar_arquivo(
                caminho_habilidades,
                forcar=True
            )
        )

        print()
        print(
            "JARVIS: Habilidade registrada no Chroma."
        )

        print(
            f"JARVIS: Status RAG: "
            f"{resultado_indexacao.get('status')}"
        )

        print(
            f"JARVIS: Chunks: "
            f"{resultado_indexacao.get('chunks', 0)}"
        )

    except Exception as erro:

        print()
        print(
            f"JARVIS: Habilidade salva, "
            f"mas falha ao indexar no Chroma: {erro}"
        )

    print()
    print("=" * 60)
    print(" HABILIDADE APRENDIDA")
    print("=" * 60)

    print(
        "Nome:",
        habilidade["nome"]
    )

    print(
        "Gatilhos:",
        ", ".join(
            habilidade["gatilhos"]
        )
    )

    print(
        "Acoes:"
    )

    for indice, acao in enumerate(
        habilidade["acoes"],
        start=1
    ):

        print(
            f"  {indice}. "
            f"{acao.get('tipo', '')} -> "
            f"{acao.get('valor', '')}"
        )

    print()

    print(
        "JARVIS: Pronto. Aprendi essa habilidade."
    )


# PROCESSAMENTO DO COMANDO
# ================================================================

def central_configuracoes(
    gerenciador: GerenciadorHabilidades
) -> None:

    while True:

        print()
        print("=" * 50)
        print(" JARVIS - CONFIGURACOES")
        print("=" * 50)
        print("[1] Habilidades e comandos")
        print("[2] Voz")
        print("[3] Inteligencia artificial")
        print("[4] Memoria")
        print("[5] Navegador")
        print("[6] Sistema")
        print("[0] Voltar")
        print()

        escolha = input(
            "Escolha: "
        ).strip()

        if escolha == "1":

            gerenciar_comandos(
                gerenciador
            )

        elif escolha == "2":

            print()
            print(
                "JARVIS: Configuracoes de voz ainda serao "
                "adicionadas aqui."
            )

        elif escolha == "3":

            print()
            print(
                "JARVIS: Configuracoes de IA ainda serao "
                "adicionadas aqui."
            )

        elif escolha == "4":

            print()
            print(
                "JARVIS: Configuracoes de memoria ainda serao "
                "adicionadas aqui."
            )

        elif escolha == "5":

            print()
            print(
                "JARVIS: Configuracoes do navegador ainda serao "
                "adicionadas aqui."
            )

        elif escolha == "6":

            print()
            print(
                "JARVIS: Configuracoes do sistema ainda serao "
                "adicionadas aqui."
            )

        elif escolha == "0":

            print()
            print(
                "JARVIS: Voltando ao chat."
            )

            return

        else:

            print(
                "JARVIS: Opcao invalida."
            )


def processar_comando(
    comando: str,
    orquestrador: Orquestrador,
    executor: Executor,
    nav: NavegadorManager | None,
    gerenciador_habilidades: GerenciadorHabilidades,
    executor_habilidades: ExecutorHabilidades,
    recuperador: Recuperador | None = None,
    triagem: dict | None = None,
    memoria_retriever: MemoriaRetriever | None = None,
    aprendizado=None,
) -> None:

    comando = str(comando).strip()

    if not comando:
        return

    # ------------------------------------------------------------
    # COMANDOS ADMINISTRATIVOS DO JARVIS
    # ------------------------------------------------------------

    comando_admin = str(
        comando
    ).strip()

    comando_admin_normalizado = (
        comando_admin.lower()
        .replace("Ã¡", "a")
        .replace("Ã ", "a")
        .replace("Ã£", "a")
        .replace("Ã¢", "a")
        .replace("Ã©", "e")
        .replace("Ãª", "e")
        .replace("Ã­", "i")
        .replace("Ã³", "o")
        .replace("Ã´", "o")
        .replace("Ãµ", "o")
        .replace("Ãº", "u")
        .replace("Ã§", "c")
    )

    if comando_admin_normalizado.startswith(
        "jarvis,"
    ):
        comando_admin_normalizado = (
            comando_admin_normalizado[7:]
            .strip()
        )

    elif comando_admin_normalizado.startswith(
        "jarvis "
    ):
        comando_admin_normalizado = (
            comando_admin_normalizado[7:]
            .strip()
        )

    # CONFIGURACOES
    if (
        "abrir minhas configuracoes"
        in comando_admin_normalizado
        or "abrir configuracoes"
        in comando_admin_normalizado
        or "abrir configuracao"
        in comando_admin_normalizado
        or comando_admin_normalizado
        == "configuracoes"
        or comando_admin_normalizado
        == "configuracao"
    ):

        print()
        print(
            "JARVIS: Abrindo minhas configuraÃ§Ãµes..."
        )

        central_configuracoes(
            gerenciador_habilidades
        )

        return

    # GERENCIAR COMANDOS
    if (
        "gerenciar comandos"
        in comando_admin_normalizado
        or "gerenciar habilidades"
        in comando_admin_normalizado
        or "gerenciar meus comandos"
        in comando_admin_normalizado
    ):

        print()
        print(
            "JARVIS: Abrindo o Gerenciador de Comandos..."
        )

        gerenciar_comandos(
            gerenciador_habilidades
        )

        return

    # ENSINAR HABILIDADE
    if (
        "ensinar uma habilidade"
        in comando_admin_normalizado
        or "ensinar habilidade"
        in comando_admin_normalizado
        or "ensinar um comando"
        in comando_admin_normalizado
        or "ensinar comando"
        in comando_admin_normalizado
        or "quero ensinar"
        in comando_admin_normalizado
    ):

        print()
        print(
            "JARVIS: Abrindo o Centro de Ensino..."
        )

        ensinar_comando(
            gerenciador_habilidades
        )

        return

    # LISTAR COMANDOS
    if (
        "listar comandos"
        in comando_admin_normalizado
        or "mostrar comandos"
        in comando_admin_normalizado
        or "meus comandos"
        == comando_admin_normalizado
        or "listar habilidades"
        in comando_admin_normalizado
    ):

        listar_comandos(
            gerenciador_habilidades
        )

        return

    # ------------------------------------------------------------
    # 1. GATILHO EXATO
    # ------------------------------------------------------------

    # Recarrega as habilidades para refletir ativacao/desativacao feita no gerenciador.

    try:

        gerenciador_habilidades.habilidades = gerenciador_habilidades.carregar()

    except Exception:

        pass



    habilidade_cadastrada = (
        gerenciador_habilidades.encontrar_cadastrada(
            comando
        )
    )

    if habilidade_cadastrada is not None:

        if not habilidade_cadastrada.get(
            "ativa",
            True
        ):

            print()
            print(
                f"JARVIS: A habilidade "
                f"'{habilidade_cadastrada.get('nome', '')}' "
                "estÃ¡ desativada."
            )

            print(
                "JARVIS: Ative-a no Gerenciador de Comandos "
                "para poder executÃ¡-la."
            )

            return

        habilidade = habilidade_cadastrada

    else:

        habilidade = None

    if habilidade is not None:

        print()
        print(
            "JARVIS: Habilidade aprendida encontrada."
        )

        resultado = executor_habilidades.executar(
            habilidade
        )

        print()
        print(
            "JARVIS:",
            resultado
        )

        print(
            "JARVIS: Comando realizado, chefe."
        )

        return

    # ------------------------------------------------------------
    # 1.5. CHROMA
    # ------------------------------------------------------------
    # O Chroma continua sendo usado para RAG/procedimentos.
    # Ele nao executa habilidades por similaridade semantica.
    # A execucao fica protegida pelo gatilho exato ou decisor.
    
    # ------------------------------------------------------------
    # 2. HABILIDADE DIRETA DO GERENCIADOR
    # ------------------------------------------------------------

    try:

        habilidade_direta = (
            gerenciador_habilidades.encontrar(
                str(comando).strip()
            )
        )

        if habilidade_direta is not None:

            print()
            print(
                "JARVIS: Habilidade cadastrada encontrada."
            )

            print(
                f"JARVIS: {habilidade_direta.get('nome', 'Sem nome')}"
            )

            resultado = (
                executor_habilidades.executar(
                    habilidade_direta
                )
            )

            print()
            print(
                "JARVIS:",
                resultado
            )

            print(
                "JARVIS: Comando realizado, chefe."
            )

            return

    except Exception as erro:

        print()
        print(
            f"JARVIS: Falha ao verificar habilidade cadastrada: {erro}"
        )

    # ------------------------------------------------------------
    # 2.45. COMPREENS?O LINGU?STICA - SPACY

    try:

        analise_spacy = analisar_texto(
            comando
        )

        if isinstance(
            analise_spacy,
            dict
        ):

            entidades_spacy = (
                analise_spacy.get(
                    "entidades",
                    []
                )
            )

            verbo_spacy = (
                analise_spacy.get(
                    "verbo_principal",
                    ""
                )
            )

            entidades_jarvis = []

            for entidade in entidades_spacy:

                texto_entidade = str(
                    entidade.get(
                        "texto",
                        ""
                    )
                ).strip()

                tipo_entidade = str(
                    entidade.get(
                        "tipo",
                        ""
                    )
                ).upper().strip()

                if not texto_entidade:
                    continue

                texto_normalizado = (
                    texto_entidade.lower()
                )

                # Corrige programas que o modelo
                # pode classificar incorretamente.
                if texto_normalizado in {
                    "chrome",
                    "google chrome",
                    "edge",
                    "microsoft edge",
                    "firefox",
                    "notepad",
                    "bloco de notas",
                    "vscode",
                    "visual studio code",
                    "whatsapp",
                }:

                    tipo_entidade = "PROGRAMA"

                elif tipo_entidade in {
                    "LOC",
                    "GPE",
                    "FAC",
                }:

                    tipo_entidade = "LOCAL"

                entidades_jarvis.append(
                    {
                        "texto": texto_entidade,
                        "tipo": tipo_entidade,
                    }
                )

        else:

            analise_spacy = {}
            entidades_spacy = []
            entidades_jarvis = []
            verbo_spacy = ""

    except Exception:

        analise_spacy = {}
        entidades_spacy = []
        entidades_jarvis = []
        verbo_spacy = ""

    # 2.5. MEMORIA DETERMINISTICA
    # ------------------------------------------------------------

    try:

        resposta_memoria_direta = (
            executor.responder_memoria_direta(
                comando
            )
        )

    except Exception as erro_memoria_direta:

        resposta_memoria_direta = None

        print()
        print(
            f"JARVIS: Aviso - falha na memoria direta: {erro_memoria_direta}"
        )

    if resposta_memoria_direta:

        print()
        print(
            "JARVIS:",
            resposta_memoria_direta
        )

        return

    # ------------------------------------------------------------
    # 2.6. MEMORIA SEMANTICA
    # ------------------------------------------------------------
    # A memoria apenas fornece contexto relevante ao Qwen.
    # ------------------------------------------------------------

    contexto_memoria = ""

    if memoria_retriever is not None:

        try:

            resultados_memoria = memoria_retriever.buscar(
                comando
            )

            memorias_relevantes = []

            for item in resultados_memoria:

                if not isinstance(item, dict):
                    continue

                conteudo = str(
                    item.get("conteudo", "")
                ).strip()

                if not conteudo:
                    continue

                similaridade = float(
                    item.get("similaridade", 0.0)
                )

                score_final = float(
                    item.get("score_final", 0.0)
                )

                if (
                    similaridade >= 0.88
                    and score_final >= 0.55
                ):

                    tipo = str(
                        item.get("tipo", "OUTRO")
                    ).strip().upper()

                    if tipo:
                        memorias_relevantes.append(
                            "[" + tipo + "] " + conteudo
                        )
                    else:
                        memorias_relevantes.append(
                            conteudo
                        )

            if memorias_relevantes:
                contexto_memoria = "\n".join(
                    memorias_relevantes[:5]
                )

        except Exception as erro_memoria_semantica:

            print()
            print(
                "JARVIS: Aviso - memoria semantica indisponivel:",
                erro_memoria_semantica
            )

            contexto_memoria = ""

    # ------------------------------------------------------------
    # 3. CENTRO DE TRIAGEM -> ROTEAMENTO
    # ------------------------------------------------------------

    intencao_triagem = ""

    if isinstance(triagem, dict):
        intencao_triagem = str(
            triagem.get(
                "intencao",
                ""
            )
        ).strip()

    # ------------------------------------------------------------
    # ------------------------------------------------------------
    # CLIMA - PRIORIDADE OPERACIONAL
    # ------------------------------------------------------------

    if hasattr(orquestrador, "eh_comando_clima") and orquestrador.eh_comando_clima(comando):

        print()
        print(
            "JARVIS: Consultando clima atual..."
        )

        try:

            acao_clima = {
                "acao": "clima",
                "texto": comando
            }

            resultado_clima = executor.executar(
                None,
                acao_clima
            )

            if resultado_clima:
                print()
                print(
                    "JARVIS:",
                    str(resultado_clima)
                )

            return

        except Exception as erro_clima:

            print()
            print(
                f"JARVIS: Falha ao consultar clima: {erro_clima}"
            )

            return
    # PESQUISA
    # ------------------------------------------------------------

    if intencao_triagem in {
        "pesquisa_atualidade",
        "pesquisa_geral",
    }:

        decisao = {
            "tipo": "resposta",
            "texto": (
                "Nao sei. Posso pesquisar "
                "para tentar encontrar a informacao correta."
            ),
        }

    # ------------------------------------------------------------
    # MEMORIA
    # ------------------------------------------------------------

    elif intencao_triagem == "memoria":

        # A memoria fornece contexto para a IA.
        # A resposta final continua sendo gerada pela IA,
        # usando o contexto semantico recuperado.

        try:

            resposta_memoria = perguntar(
                comando,
                contexto_memoria
            )

            decisao = {
                "tipo": "resposta",
                "texto": str(
                    resposta_memoria or ""
                ).strip()
            }

        except Exception as erro_memoria:

            print()
            print(
                f"JARVIS: Falha ao responder consulta de memoria: {erro_memoria}"
            )

            decisao = {
                "tipo": "resposta",
                "texto": ""
            }


    # ------------------------------------------------------------
    # CONVERSA NORMAL
    # ------------------------------------------------------------

    elif intencao_triagem == "conversa_geral":

        # --------------------------------------------------------
        # CONVERSA DIRETA
        #
        # Conversa normal nao precisa passar por
        # decidir_habilidade(). Essa funcao e reservada para
        # decidir e executar habilidades operacionais.
        #
        # Fluxo:
        # TRIAGEM -> MEMORIA -> QWEN -> RESPOSTA
        # --------------------------------------------------------

        try:

            resposta_direta = perguntar(
                comando,
                contexto_memoria
            )

            decisao = {
                "tipo": "resposta",
                "texto": str(
                    resposta_direta or ""
                ).strip()
            }

        except Exception as erro:

            print()
            print(
                f"JARVIS: Falha ao responder: {erro}"
            )

            decisao = {
                "tipo": "resposta",
                "texto": ""
            }


    # ------------------------------------------------------------
    # RESPOSTAS GERADAS PELA IA
    # ------------------------------------------------------------
    #
    # Memoria e conversa geral ja possuem uma resposta pronta.
    # Nao devem continuar para o executor de habilidades.
    # ------------------------------------------------------------

    if intencao_triagem in (
        "memoria",
        "conversa_geral",
    ):

        texto_resposta = str(
            decisao.get("texto", "")
            if isinstance(decisao, dict)
            else ""
        ).strip()

        if texto_resposta:
            print(texto_resposta)

            try:
                falar(texto_resposta)
            except Exception as erro_voz:
                print()
                print("JARVIS: Aviso - nao consegui falar a resposta.")
                print(f"ERRO VOZ: {erro_voz}")

        return

    # COMANDOS OPERACIONAIS
    # ------------------------------------------------------------

    else:

        try:

            habilidades_disponiveis = (
                gerenciador_habilidades.listar()
            )

            decisao = decidir_habilidade(
                comando,
                habilidades_disponiveis
            )

        except Exception as erro:

            print()
            print(
                f"JARVIS: Falha na anÃ¡lise de habilidades: {erro}"
            )

            decisao = {
                "tipo": "resposta",
                "texto": ""
            }

    # ============================================================
    # MULTIPLAS HABILIDADES
    # ============================================================

    partes_comando = re.split(
        r"\s+(?:e\s+depois|depois|e\s+ent[aÃ£]o|ent[aÃ£]o)\s+",
        str(comando).strip(),
        flags=re.IGNORECASE
    )

    partes_comando = [
        parte.strip()
        for parte in partes_comando
        if parte.strip()
    ]

    if len(partes_comando) > 1:

        habilidades_executadas = []

        for parte in partes_comando:

            try:
                decisao_parte = decidir_habilidade(
                    parte,
                    habilidades_disponiveis
                )
            except Exception:
                decisao_parte = {
                    "tipo": "resposta",
                    "texto": ""
                }

            if decisao_parte.get(
                "tipo"
            ) != "habilidade":
                continue

            nome_parte = str(
                decisao_parte.get(
                    "nome",
                    ""
                )
            ).strip()

            habilidade_parte = None

            for item in habilidades_disponiveis:

                if not isinstance(
                    item,
                    dict
                ):
                    continue

                if not item.get(
                    "ativa",
                    True
                ):
                    continue

                nome_item = str(
                    item.get(
                        "nome",
                        ""
                    )
                ).strip()

                if nome_item == nome_parte:
                    habilidade_parte = item
                    break

            if habilidade_parte is None:
                continue

            print()
            print(
                "JARVIS: Entendi. Vou executar "
                f"'{nome_parte}'".replace("''", "'")
            )

            resultado_parte = executor_habilidades.executar(
                habilidade_parte
            )

            print()
            print(
                "JARVIS:",
                resultado_parte
            )

            habilidades_executadas.append(
                habilidade_parte
            )

        if habilidades_executadas:

            descricoes_multiplas = []

            mapa_resumo_multiplas = {
                "abrir_programa": "abri o programa",
                "abrir_site": "abri o site",
                "esperar": "aguardei",
                "falar": "enviei uma fala",
                "localizar_elemento": "localizei um elemento",
                "esperar_elemento": "aguardei um elemento",
                "clicar": "cliquei em um elemento",
                "digitar": "digitei um texto",
                "pressionar_tecla": "pressionei uma tecla",
                "ler": "li a pÃ¡gina",
                "rolar": "rolei a pÃ¡gina",
                "mover_mouse": "movi o mouse no navegador",
                "copiar": "copiei",
                "colar": "colei",
                "selecionar_tudo": "selecionei tudo",
                "clicar_tela": "cliquei na tela",
                "duplo_clique": "dei um duplo clique na tela",
                "clique_direito": "dei um clique direito na tela",
                "mover_mouse_tela": "movi o mouse na tela",
                "arrastar_mouse": "arrastei o mouse",
                "combinacao_teclas": "usei uma combinaÃ§Ã£o de teclas",
            }

            for habilidade_executada in habilidades_executadas:

                for acao in habilidade_executada.get(
                    "acoes",
                    []
                ):

                    if not isinstance(
                        acao,
                        dict
                    ):
                        continue

                    tipo = str(
                        acao.get(
                            "tipo",
                            ""
                        )
                    ).strip()

                    valor = str(
                        acao.get(
                            "valor",
                            ""
                        )
                    ).strip()

                    descricao = mapa_resumo_multiplas.get(
                        tipo,
                        ""
                    )

                    if not descricao:
                        continue

                    if tipo == "combinacao_teclas" and valor:
                        descricoes_multiplas.append(
                            f"usei {valor}"
                        )

                    elif tipo in {
                        "clicar_tela",
                        "duplo_clique",
                        "clique_direito",
                        "mover_mouse_tela",
                        "arrastar_mouse",
                    } and valor:
                        descricoes_multiplas.append(
                            f"{descricao} em {valor}"
                        )

                    elif tipo == "digitar" and valor:
                        descricoes_multiplas.append(
                            f"digitei '{valor}'"
                        )

                    else:
                        descricoes_multiplas.append(
                            descricao
                        )

            if len(descricoes_multiplas) == 1:
                resumo_multiplas = descricoes_multiplas[0] + "."

            elif len(descricoes_multiplas) == 2:
                resumo_multiplas = (
                    descricoes_multiplas[0]
                    + " e "
                    + descricoes_multiplas[1]
                    + "."
                )

            elif descricoes_multiplas:
                resumo_multiplas = (
                    ", ".join(descricoes_multiplas[:-1])
                    + " e "
                    + descricoes_multiplas[-1]
                    + "."
                )

            else:
                resumo_multiplas = "executei as habilidades solicitadas."

            print()
            print(
                "JARVIS: Resumo:",
                resumo_multiplas
            )

            print(
                "JARVIS: Comando realizado, chefe."
            )

            return

    if decisao.get(
        "tipo"
    ) == "habilidade":

        nome_habilidade = str(
            decisao.get(
                "nome",
                ""
            )
        ).strip()

        habilidade_qwen = None

        for item in habilidades_disponiveis:

            if not isinstance(
                item,
                dict
            ):
                continue

            if not item.get(
                "ativa",
                True
            ):
                continue

            nome_item = str(
                item.get(
                    "nome",
                    ""
                )
            ).strip()

            if nome_item == nome_habilidade:

                habilidade_qwen = item
                break

        if habilidade_qwen is not None:

            print()
            print(
                "JARVIS: Entendi. Vou executar "
                f"'{nome_habilidade}'."
            )

            resultado = executor_habilidades.executar(
                habilidade_qwen
            )

            print()
            print(
                "JARVIS:",
                resultado
            )

            acoes_executadas = habilidade_qwen.get(
                "acoes",
                []
            )

            descricoes = []

            mapa_resumo = {
                "abrir_programa": "abri o programa",
                "abrir_site": "abri o site",
                "esperar": "aguardei",
                "falar": "enviei uma fala",
                "localizar_elemento": "localizei um elemento",
                "esperar_elemento": "aguardei um elemento",
                "clicar": "cliquei em um elemento",
                "digitar": "digitei um texto",
                "pressionar_tecla": "pressionei uma tecla",
                "ler": "li a pÃ¡gina",
                "rolar": "rolei a pÃ¡gina",
                "mover_mouse": "movi o mouse no navegador",
                "copiar": "copiei",
                "colar": "colei",
                "selecionar_tudo": "selecionei tudo",
                "clicar_tela": "cliquei na tela",
                "duplo_clique": "dei um duplo clique na tela",
                "clique_direito": "dei um clique direito na tela",
                "mover_mouse_tela": "movi o mouse na tela",
                "arrastar_mouse": "arrastei o mouse",
                "combinacao_teclas": "usei uma combinaÃ§Ã£o de teclas",
            }

            for acao in acoes_executadas:

                if not isinstance(
                    acao,
                    dict
                ):
                    continue

                tipo = str(
                    acao.get(
                        "tipo",
                        ""
                    )
                ).strip()

                valor = str(
                    acao.get(
                        "valor",
                        ""
                    )
                ).strip()

                descricao = mapa_resumo.get(
                    tipo,
                    ""
                )

                if not descricao:
                    continue

                if tipo == "abrir_programa" and valor:
                    descricoes.append(
                        f"abri o {valor}"
                    )

                elif tipo == "abrir_site" and valor:
                    descricoes.append(
                        f"abri {valor}"
                    )

                elif tipo == "digitar" and valor:
                    descricoes.append(
                        f"digitei '{valor}'"
                    )

                elif tipo == "pressionar_tecla" and valor:
                    descricoes.append(
                        f"pressionei {valor}"
                    )

                elif tipo == "combinacao_teclas" and valor:
                    descricoes.append(
                        f"usei {valor}"
                    )

                elif tipo in {
                    "clicar_tela",
                    "duplo_clique",
                    "clique_direito",
                    "mover_mouse_tela",
                    "arrastar_mouse",
                } and valor:
                    descricoes.append(
                        f"{descricao} em {valor}"
                    )

                elif tipo == "esperar" and valor:
                    descricoes.append(
                        f"aguardei {valor} segundo(s)"
                    )

                else:
                    descricoes.append(
                        descricao
                    )

            if descricoes:

                if len(descricoes) == 1:

                    resumo = (
                        descricoes[0]
                        + "."
                    )

                elif len(descricoes) == 2:

                    resumo = (
                        descricoes[0]
                        + " e "
                        + descricoes[1]
                        + "."
                    )

                else:

                    resumo = (
                        ", ".join(
                            descricoes[:-1]
                        )
                        + " e "
                        + descricoes[-1]
                        + "."
                    )

            else:

                resumo = (
                    f"executei a habilidade "
                    f"'{nome_habilidade}'."
                )

            print()
            print(
                "JARVIS: Resumo:",
                resumo
            )

            print(
                "JARVIS: Comando realizado, chefe."
            )

            return

            return

    # ------------------------------------------------------------
    # 3. QWEN RESPONDE NORMALMENTE
    # ------------------------------------------------------------

    if decisao.get(
        "tipo"
    ) == "resposta":

        resposta = str(
            decisao.get(
                "texto",
                ""
            )
        ).strip()

        if resposta:

            # ------------------------------------------------
            # DETECCAO DE INCERTEZA
            # ------------------------------------------------

            resposta_normalizada = (
                resposta
                .lower()
                .replace("Ã¡", "a")
                .replace("Ã ", "a")
                .replace("Ã£", "a")
                .replace("Ã¢", "a")
                .replace("Ã©", "e")
                .replace("Ãª", "e")
                .replace("Ã­", "i")
                .replace("Ã³", "o")
                .replace("Ã´", "o")
                .replace("Ãµ", "o")
                .replace("Ãº", "u")
                .replace("Ã§", "c")
            )

            marcadores_nao_sei = (
                "nao sei",
                "nao tenho informacao",
                "nao tenho essa informacao",
                "nao conheco",
                "nao consigo confirmar",
                "nao posso confirmar",
                "nao tenho como confirmar",
                "nao sei informar",
                "informacao insuficiente",
                "nao tenho dados suficientes",
            )

            # ------------------------------------------------
            # CENTRO DE TRIAGEM -> DECISAO DE PESQUISA
            # ------------------------------------------------

            intencao_triagem = ""

            if isinstance(triagem, dict):
                intencao_triagem = str(
                    triagem.get("intencao", "")
                ).strip()

            precisa_pesquisar = (
                intencao_triagem
                in {
                    "pesquisa_atualidade",
                    "pesquisa_geral",
                }
            )

            # Fallback de seguranca caso a triagem falhe.
            if not triagem:
                precisa_pesquisar = any(
                    marcador in resposta_normalizada
                    for marcador in marcadores_nao_sei
                )

                if (
                    "posso pesquisar" in resposta_normalizada
                    or "posso verificar" in resposta_normalizada
                ):
                    precisa_pesquisar = True

            if precisa_pesquisar:

                print()
                print(
                    "JARVIS: NÃ£o tenho essa informaÃ§Ã£o com seguranÃ§a."
                )

                print(
                    "JARVIS: Vou pesquisar no ChatGPT."
                )

                playwright_pesquisa = None
                navegador_pesquisa = None

                try:

                    playwright_pesquisa = (
                        sync_playwright().start()
                    )

                    navegador_pesquisa = (
                        NavegadorManager(
                            playwright_pesquisa,
                            headless=False
                        )
                    )

                    pagina_pesquisa = (
                        navegador_pesquisa.pagina
                    )

                    resultado_pesquisa = (
                        executor.responder_com_chatgpt(
                            pagina_pesquisa,
                            comando
                        )
                    )

                    resultado_pesquisa = str(
                        resultado_pesquisa or ""
                    ).strip()

                    if resultado_pesquisa:

                        print()
                        print(
                            "JARVIS:",
                            resultado_pesquisa
                        )

                        return

                    print()
                    print(
                        "JARVIS: NÃ£o consegui verificar "
                        "essa informaÃ§Ã£o pela pesquisa."
                    )

                    return

                except Exception as erro_pesquisa:

                    print()
                    print(
                        "JARVIS: NÃ£o consegui realizar "
                        "a pesquisa agora."
                    )

                    print(
                        f"ERRO: {erro_pesquisa}"
                    )

                    return

                finally:

                    try:

                        if navegador_pesquisa is not None:
                            if (
                                navegador_pesquisa.contexto
                                is not None
                            ):
                                navegador_pesquisa.contexto.close()

                    except Exception:
                        pass

                    try:

                        if playwright_pesquisa is not None:
                            playwright_pesquisa.stop()

                    except Exception:
                        pass

            print()
            try:
                falar(resposta)
            except Exception as erro_voz:
                print()
                print("JARVIS: Aviso - nao consegui falar a resposta.")
                print(f"ERRO VOZ: {erro_voz}")
            return

    # ------------------------------------------------------------
    # 4. ORQUESTRADOR OPERACIONAL
    # ------------------------------------------------------------

    acao = orquestrador.interpretar(
        comando
    )

    print(
        "ACAO:",
        acao
    )

    tipo_acao = acao.get(
        "acao"
    )

    if tipo_acao == "desconhecida":

        print()
        print(
            "JARVIS:",
            "Ainda nao sei executar esse comando."
        )

        return

    pagina = None

    resultado = executor.executar(
        pagina,
        acao
    )

    # ------------------------------------------------------------
    # APRENDIZADO - REGISTRO DA EXPERIENCIA
    # ------------------------------------------------------------

    try:
        aprendizado.registrar_experiencia(
            comando=comando,
            intencao=str(tipo_acao or ""),
            acao=str(tipo_acao or ""),
            estrategia=str(acao.get("programa", acao.get("nome", "")) or ""),
            resultado=resultado,
            sucesso=True,
            tentativa=1,
        )
    except Exception as erro_aprendizado:
        print()
        print("JARVIS: Aviso - aprendizado nao registrado.")
        print(f"ERRO APRENDIZADO: {erro_aprendizado}")

    if (
        isinstance(resultado, dict)
        and tipo_acao == "ler"
    ):

        mostrar_pagina(
            resultado
        )

        return

    print()
    print(
        "JARVIS:",
        resultado
    )

# LOOP PRINCIPAL
# ================================================================

# ==========================================================
# PROMOCAO DE MEMORIA TEMPORARIA PARA PERMANENTE
# ==========================================================


def promover_memoria_permanente(
    memoria_local,
    comando
) -> None:

    try:

        texto_original = str(
            comando or ""
        ).strip()

        if not texto_original:
            return

        # ------------------------------------------------------
        # MEMORIA PERMANENTE SOMENTE COM PEDIDO EXPLICITO
        # ------------------------------------------------------

        import unicodedata

        def normalizar_texto_memoria(valor):
            texto = str(
                valor or ""
            ).strip().lower()

            texto = unicodedata.normalize(
                "NFD",
                texto
            )

            texto = "".join(
                caractere
                for caractere in texto
                if unicodedata.category(caractere) != "Mn"
            )

            return texto

        texto_normalizado = normalizar_texto_memoria(
            texto_original
        )

        # ------------------------------------------------------
        # SOMENTE COMANDOS EXPLICITOS DE MEMORIA
        # ------------------------------------------------------

        prefixos_memoria = (
            "jarvis salve ",
            "jarvis salva ",
            "jarvis lembre ",
            "jarvis lembra ",
            "jarvis memorize ",
            "jarvis memoriza ",
            "jarvis guarde ",
            "jarvis guarda ",
            "jarvis anote ",
            "jarvis anota ",
            "jarvis registre ",
            "jarvis registra ",
            "jarvis nao esqueca ",
            "jarvis tenha em mente ",
        )

        pedido_explicito = None

        # Forma:
        # JARVIS salve ...
        # JARVIS lembre ...
        # JARVIS memorize ...

        for prefixo in prefixos_memoria:

            if texto_normalizado.startswith(
                prefixo
            ):

                pedido_explicito = (
                    texto_original[
                        len(prefixo):
                    ].strip()
                )

                break

        # Forma:
        # JARVIS, salve ...
        # JARVIS, lembre ...
        # JARVIS, memorize ...

        if pedido_explicito is None:

            if texto_normalizado.startswith(
                "jarvis,"
            ):

                depois_jarvis = (
                    texto_original[7:].strip()
                )

                depois_jarvis_normalizado = (
                    normalizar_texto_memoria(
                        depois_jarvis
                    )
                )

                prefixos_diretos = (
                    "salve ",
                    "salva ",
                    "lembre ",
                    "lembra ",
                    "memorize ",
                    "memoriza ",
                    "guarde ",
                    "guarda ",
                    "anote ",
                    "anota ",
                    "registre ",
                    "registra ",
                    "nao esqueca ",
                    "tenha em mente ",
                )

                for prefixo in prefixos_diretos:

                    if depois_jarvis_normalizado.startswith(
                        prefixo
                    ):

                        pedido_explicito = (
                            depois_jarvis[
                                len(prefixo):
                            ].strip()
                        )

                        break

        # Nenhum pedido explicito:
        # NAO SALVAR MEMORIA PERMANENTE.

        if pedido_explicito is None:
            return

        conteudo = (
            pedido_explicito
            .strip()
        )

        # Aceita:
        # JARVIS, salve que ...
        # JARVIS, lembre que ...
        # JARVIS, memorize que ...

        conteudo_normalizado = (
            normalizar_texto_memoria(
                conteudo
            )
        )

        if conteudo_normalizado.startswith(
            "que "
        ):

            conteudo = (
                conteudo[4:]
                .strip()
            )

        if not conteudo:
            return

        # ------------------------------------------------------
        # MEMORIAS ENCONTRADAS
        # ------------------------------------------------------

        memorias = []


        # ------------------------------------------------------
        # 1. NOME DO USUARIO
        # ------------------------------------------------------

        import re

        match_nome = re.search(
            r"\bmeu\s+nome\s+e\s+([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)",
            conteudo,
            re.IGNORECASE
        )

        if not match_nome:
            match_nome = re.search(
                r"\bme\s+chamo\s+([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)",
                conteudo,
                re.IGNORECASE
            )

        if match_nome:
            nome = match_nome.group(1).strip()

            if nome:
                memorias.append({
                    "conteudo": f"Meu nome ? {nome}.",
                    "tipo": "NOME",
                    "importancia": 9,
                })

        # ------------------------------------------------------
        # 2. COMO O USUARIO QUER SER CHAMADO
        # ------------------------------------------------------

        padroes_chamar = [
            r"\bquero\s+que\s+voce\s+me\s+chame\s+de\s+([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)",
            r"\bquero\s+que\s+me\s+chame\s+de\s+([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)",
            r"\bme\s+chame\s+de\s+([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)",
            r"\bpode\s+me\s+chamar\s+de\s+([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)",
            r"\bpode\s+chamar\s+de\s+([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)",
            r"\bprefiro\s+ser\s+chamado\s+de\s+([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)",
            r"\bprefiro\s+que\s+me\s+chame\s+de\s+([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)",
        ]

        tratamento = None

        for padrao in padroes_chamar:

            match = re.search(
                padrao,
                conteudo,
                re.IGNORECASE
            )

            if match:
                tratamento = match.group(1).strip()
                break

        if tratamento:

            memorias.append({
                "conteudo": (
                    f"O usu?rio prefere ser chamado de "
                    f"{tratamento}."
                ),
                "tipo": "COMO_CHAMAR",
                "importancia": 10,
            })

        # ------------------------------------------------------
        # 3. PET
        # ------------------------------------------------------

        padroes_pet = [
            (
                r"\bmeu\s+cachorro\s+se\s+chama\s+"
                r"([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)"
            ),
            (
                r"\bo\s+nome\s+do\s+meu\s+cachorro\s+e\s+"
                r"([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)"
            ),
            (
                r"\bminha\s+cachorra\s+se\s+chama\s+"
                r"([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)"
            ),
            (
                r"\bo\s+nome\s+da\s+minha\s+cachorra\s+e\s+"
                r"([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)"
            ),
            (
                r"\bmeu\s+gato\s+se\s+chama\s+"
                r"([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)"
            ),
            (
                r"\bo\s+nome\s+do\s+meu\s+gato\s+e\s+"
                r"([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)"
            ),
            (
                r"\bminha\s+gata\s+se\s+chama\s+"
                r"([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)"
            ),
            (
                r"\bo\s+nome\s+da\s+minha\s+gata\s+e\s+"
                r"([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)"
            ),
            (
                r"\bmeu\s+pet\s+se\s+chama\s+"
                r"([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)"
            ),
            (
                r"\bo\s+nome\s+do\s+meu\s+pet\s+e\s+"
                r"([A-Za-z?-?][A-Za-z?-?\s'-]*?)(?=\.\s+|,\s+|$)"
            ),
        ]

        pet_nome = None

        for padrao in padroes_pet:

            match = re.search(
                padrao,
                conteudo,
                re.IGNORECASE
            )

            if match:
                pet_nome = match.group(1).strip()
                break

        if pet_nome:

            memorias.append({
                "conteudo": (
                    f"O nome do meu cachorro ? {pet_nome}."
                    if "cachorro" in conteudo.lower()
                    else f"O nome do meu pet ? {pet_nome}."
                ),
                "tipo": "PET",
                "importancia": 9,
            })

        # ------------------------------------------------------
        # 4. MEMORIA CLASSIFICADA NORMALMENTE
        # ------------------------------------------------------

        classificacao = classificar_memoria(
            conteudo
        )

        # S? usamos a classifica??o normal quando
        # nenhuma mem?ria estruturada espec?fica foi encontrada.
        if not memorias:

            if not classificacao.get(
                "permanente",
                False
            ):
                return

            conteudo_classificado = str(
                classificacao.get(
                    "conteudo",
                    conteudo
                )
            ).strip()

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
                "n?o esque?a que ",
            )

            conteudo_normalizado = (
                conteudo_classificado.lower()
            )

            for prefixo in prefixos:

                if conteudo_normalizado.startswith(
                    prefixo
                ):

                    conteudo_classificado = (
                        conteudo_classificado[
                            len(prefixo):
                        ].strip()
                    )

                    break

            if not conteudo_classificado:
                return

            memorias.append({
                "conteudo": conteudo_classificado,
                "tipo": str(
                    classificacao.get(
                        "tipo",
                        "OUTRO"
                    )
                ).strip(),
                "importancia": int(
                    classificacao.get(
                        "importancia",
                        5
                    )
                ),
            })

        # ------------------------------------------------------
        # 5. SALVAR TODAS AS MEMORIAS ENCONTRADAS
        # ------------------------------------------------------

        salvas = 0

        for memoria in memorias:

            memoria_local.salvar_memoria(
                conteudo=memoria["conteudo"],
                tipo=memoria["tipo"],
                importancia=memoria["importancia"],
                duracao="PERMANENTE"
            )

            salvas += 1

        # ------------------------------------------------------
        # 6. CHROMADB
        # ------------------------------------------------------
        # A sincronizacao ja e feita pelo MemoriaRetriever.
        # Nao criar outro retriever nem sincronizar novamente aqui.
    except Exception as erro:

        print(
            "JARVIS: Aviso - falha ao promover "
            f"mem?ria permanente: {erro}"
        )


def iniciar_ia_router():
    try:
        with socket.create_connection(("127.0.0.1", 8765), timeout=1):
            print("IA ROUTER: já está ativo.")
            return
    except OSError:
        pass

    print("IA ROUTER: iniciando...")

    subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api_router:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8765",
        ],
        cwd=r"C:\Users\almei\IA_ROUTER",
        creationflags=subprocess.CREATE_NO_WINDOW,
    )

    for _ in range(20):
        try:
            with socket.create_connection(("127.0.0.1", 8765), timeout=1):
                print("IA ROUTER: ONLINE.")
                return
        except OSError:
            time.sleep(0.5)

    print("IA ROUTER: falha ao iniciar.")

def main() -> None:
    inicializar_voz()
    iniciar_ia_router()


    # --------------------------------------------------------
    # CENTRO DE TRIAGEM INTELIGENTE
    # --------------------------------------------------------

    classificador_intencao = obter_classificador()

    orquestrador = Orquestrador()

    executor = Executor()
    aprendizado = obter_aprendizado()

    gerenciador_habilidades = (
        GerenciadorHabilidades()
    )

    executor_habilidades = (
        ExecutorHabilidades()
    )

    # --------------------------------------------------------
    # RAG / CHROMA
    # --------------------------------------------------------

    try:

        banco_chroma = BancoChroma()

        recuperador = Recuperador(
            banco_chroma
        )

        print(
            "CHROMA: Recuperador de procedimentos ativado."
        )

    except Exception as erro:

        recuperador = None

        print(
            f"CHROMA: Falha ao inicializar RAG: {erro}"
        )

    memoria_local = (
        MemoriaLocal()
    )

    # --------------------------------------------------------
    # MEMORIA SEMANTICA
    # --------------------------------------------------------

    try:

        memoria_retriever = MemoriaRetriever()

        print(
            "JARVIS: Memoria semantica ativada."
        )

    except Exception as erro:

        memoria_retriever = None

        print(
            "JARVIS: Aviso - memoria semantica indisponivel:",
            erro
        )

    print("=" * 50)
    print(" J.A.R.V.I.S - NUCLEO OPERACIONAL")
    print("=" * 50)
    print("Voz e texto ativados.")
    print()

    erros_seguidos = 0

    while True:

        # --------------------------------------------------------
        # ENTRADA
        # --------------------------------------------------------

        try:

            comando = obter_comando()

        except KeyboardInterrupt:

            print()
            print(
                "JARVIS: Interrompido pelo usuario. Encerrando."
            )

            break

        # --------------------------------------------------------
        # COMANDO VAZIO
        # --------------------------------------------------------

        if not comando:
            continue

        # --------------------------------------------------------
        # CENTRO DE TRIAGEM INTELIGENTE
        # --------------------------------------------------------

        try:

            triagem = classificador_intencao.classificar(
                comando
            )

            print()

        except Exception as erro_triagem:

            print()
            print(
                "JARVIS: Aviso - falha na triagem:",
                erro_triagem
            )

        # --------------------------------------------------------
        # GERENCIADOR DE COMANDOS
        # --------------------------------------------------------

        if comando == "__ENSINAR_COMANDO__":

            gerenciar_comandos(
                gerenciador_habilidades
            )

            continue

        # --------------------------------------------------------
        # ENCERRAR CONVERSA
        # --------------------------------------------------------

        comando_normalizado = (
            str(comando)
            .strip()
            .lower()
        )

        if comando_normalizado.startswith(
            "jarvis,"
        ):
            comando_normalizado = (
                comando_normalizado[7:]
                .strip()
            )

        elif comando_normalizado.startswith(
            "jarvis "
        ):
            comando_normalizado = (
                comando_normalizado[7:]
                .strip()
            )

        if comando_normalizado in {
            "encerrar conversa",
            "encerrar o chat",
            "terminar conversa",
            "terminar o chat",
            "fechar conversa",
            "sair da conversa",
        }:

            global MODO_CONVERSA

            MODO_CONVERSA = None

            print()
            print(
                "JARVIS: Conversa encerrada."
            )

            print(
                "JARVIS: Voltando ao menu inicial."
            )

            print()

            continue

        # --------------------------------------------------------
        # SAIDA COMPLETA DO JARVIS
        # --------------------------------------------------------

        if comando.lower() in COMANDOS_SAIDA:

            print(
                "JARVIS: Encerrando."
            )

            break

        # --------------------------------------------------------
        # RECEBIMENTO
        # --------------------------------------------------------

        # --------------------------------------------------------
        # MEMORIA TEMPORARIA ? HISTORICO DA CONVERSA
        # --------------------------------------------------------

        try:
            memoria_local.registrar_conversa(
                usuario=comando,
                jarvis=""
            )
        except Exception as erro_memoria:
            print(
                f"JARVIS: Aviso ? n?o consegui registrar "
                f"o hist?rico: {erro_memoria}"
            )

        # --------------------------------------------------------
        # EXECUCAO
        # --------------------------------------------------------

        try:

            # ------------------------------------------------
            # CAPTURA DA RESPOSTA DO JARVIS
            # ------------------------------------------------

            saida_javis = io.StringIO()

            class SaidaDuplicada:

                def __init__(self, original, captura):
                    self.original = original
                    self.captura = captura

                def write(self, texto):
                    self.original.write(texto)
                    self.captura.write(texto)

                def flush(self):
                    self.original.flush()
                    self.captura.flush()

            saida_original = sys.stdout

            with redirect_stdout(
                SaidaDuplicada(
                    saida_original,
                    saida_javis
                )
            ):

                processar_comando(
                    comando,
                    orquestrador,
                    executor,
                    None,
                    gerenciador_habilidades,
                    executor_habilidades,
                    recuperador,
                    triagem,
                    memoria_retriever,
                    aprendizado,
                )

            texto_saida = (
                saida_javis
                .getvalue()
                .strip()
            )

            resposta_memoria = ""

            # ------------------------------------------------
            # EXTRAI A RESPOSTA COMPLETA DO JARVIS
            # ------------------------------------------------

            blocos_jarvis = []

            linhas_saida = (
                texto_saida.splitlines()
            )

            indice = 0

            while indice < len(linhas_saida):

                linha_limpa = (
                    linhas_saida[indice].strip()
                )

                if (
                    linha_limpa.startswith(
                        "JARVIS:"
                    )
                    and not linha_limpa.startswith(
                        "JARVIS recebeu:"
                    )
                ):

                    inicio = (
                        linha_limpa[
                            len("JARVIS:"):
                        ].strip()
                    )

                    bloco = []

                    if inicio:
                        bloco.append(
                            inicio
                        )

                    indice += 1

                    while indice < len(linhas_saida):

                        proxima = (
                            linhas_saida[indice]
                            .strip()
                        )

                        if (
                            proxima.startswith(
                                "JARVIS:"
                            )
                        ):
                            break

                        if proxima.startswith(
                            "=" * 10
                        ):
                            break

                        bloco.append(
                            linhas_saida[indice]
                        )

                        indice += 1

                    texto_bloco = (
                        "\n".join(bloco)
                        .strip()
                    )

                    if texto_bloco:
                        blocos_jarvis.append(
                            texto_bloco
                        )

                    continue

                indice += 1

            if blocos_jarvis:

                resumo_memoria = None

                for bloco in blocos_jarvis:

                    if bloco.startswith(
                        "Resumo:"
                    ):

                        resumo_memoria = (
                            bloco[
                                len("Resumo:"):
                            ].strip()
                        )

                if resumo_memoria:

                    resposta_memoria = (
                        resumo_memoria
                    )

                else:

                    resposta_memoria = (
                        blocos_jarvis[-1]
                    )

            else:

                resposta_memoria = (
                    texto_saida
                )

            # ------------------------------------------------
            # ATUALIZA O MESMO REGISTRO DA CONVERSA
            # ------------------------------------------------

            try:

                memoria_local.atualizar_ultima_conversa(
                    resposta_memoria
                )

            except Exception as erro_memoria:

                print(
                    f"JARVIS: Aviso â€” nÃ£o consegui "
                    f"atualizar o histÃ³rico: "
                    f"{erro_memoria}"
                )

            # ------------------------------------------------
            # PROMOCAO AUTOMATICA PARA MEMORIA PERMANENTE
            # ------------------------------------------------

            promover_memoria_permanente(
                memoria_local,
                comando
            )

            erros_seguidos = 0

        except Exception as erro:

            erros_seguidos += 1

            print()
            print(
                "JARVIS: Erro durante a execucao."
            )

            print(
                f"ERRO: {erro}"
            )

            traceback.print_exc()

            # ----------------------------------------------------
            # PROTECAO CONTRA LOOP DE ERROS
            # ----------------------------------------------------

            if erros_seguidos >= MAX_ERROS_SEGUIDOS:

                print()
                print(
                    f"JARVIS: {MAX_ERROS_SEGUIDOS} erros seguidos."
                )

                print(
                    "JARVIS: Encerrando para evitar loop infinito."
                )

                break

        print()


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":
    main()



















