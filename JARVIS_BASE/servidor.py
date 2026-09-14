# -*- coding: utf-8 -*-

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from ai.executor import Executor
from ai.orquestrador import Orquestrador

try:
    import psutil
except ImportError:
    psutil = None


HOST = "127.0.0.1"
PORTA = 8000

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIRETORIO_INTERFACE = os.path.join(BASE_DIR, "interface")


# ============================================================
# JARVIS CORE
# ============================================================

orquestrador = Orquestrador()
executor = Executor()


# ============================================================
# ESTADO GLOBAL
# ============================================================

estado = {
    "status": "ready",
    "descricao": "Aguardando comando",
    "ultimo_comando": "",
    "ultima_resposta": "",
    "inicio": time.time(),
    "atividade": [
        {
            "texto": "Sistema iniciado",
            "cor": "green",
            "tempo": "Agora"
        },
        {
            "texto": "Interface pronta",
            "cor": "blue",
            "tempo": "Agora"
        }
    ]
}


estado_lock = threading.Lock()

# Playwright Sync API não deve ser usado simultaneamente
# por múltiplas threads.
exec_lock = threading.Lock()


# ============================================================
# ESTADO DO NAVEGADOR
# ============================================================

class ApplicationState:

    def __init__(self):
        self.page = None
        self.playwright = None
        self.browser = None


application_state = ApplicationState()


# ============================================================
# ATIVIDADE
# ============================================================

def adicionar_atividade(texto, cor="blue"):

    with estado_lock:

        estado["atividade"].insert(
            0,
            {
                "texto": texto,
                "cor": cor,
                "tempo": "Agora"
            }
        )

        estado["atividade"] = estado["atividade"][:8]


# ============================================================
# STATUS
# ============================================================

def definir_estado(status, descricao):

    with estado_lock:

        estado["status"] = status
        estado["descricao"] = descricao


# ============================================================
# STATUS DO COMPUTADOR
# ============================================================

def obter_status_sistema():

    cpu = None
    ram = None

    if psutil is not None:

        try:

            cpu = round(
                psutil.cpu_percent(
                    interval=0.05
                )
            )

            ram = round(
                psutil.virtual_memory().percent
            )

        except Exception:
            pass

    return {
        "cpu": cpu,
        "ram": ram,
        "network": "LOCAL CORE",
        "uptime": int(
            time.time() - estado["inicio"]
        )
    }


# ============================================================
# NAVEGADOR
# ============================================================

def obter_pagina():

    if application_state.page is not None:

        try:

            if not application_state.page.is_closed():

                return application_state.page

        except Exception:

            application_state.page = None

    try:

        from playwright.sync_api import sync_playwright

    except ImportError as erro:

        raise RuntimeError(
            "Playwright não está instalado. "
            "Instale com: pip install playwright"
        ) from erro

    pasta_perfil = os.path.join(
        BASE_DIR,
        "dados_chromium"
    )

    application_state.playwright = (
        sync_playwright().start()
    )

    try:

        application_state.browser = (
            application_state.playwright
            .chromium
            .launch_persistent_context(
                user_data_dir=pasta_perfil,
                headless=False,
                viewport={
                    "width": 1400,
                    "height": 900
                }
            )
        )

        if application_state.browser.pages:

            application_state.page = (
                application_state.browser.pages[0]
            )

        else:

            application_state.page = (
                application_state.browser.new_page()
            )

        adicionar_atividade(
            "Navegador conectado",
            "green"
        )

        return application_state.page

    except Exception:

        try:

            if application_state.browser is not None:

                application_state.browser.close()

        except Exception:
            pass

        application_state.browser = None

        try:

            if application_state.playwright is not None:

                application_state.playwright.stop()

        except Exception:
            pass

        application_state.playwright = None
        application_state.page = None

        raise


# ============================================================
# FECHAR NAVEGADOR
# ============================================================

def fechar_navegador():

    try:

        if application_state.browser is not None:

            application_state.browser.close()

    except Exception:
        pass

    finally:

        application_state.browser = None
        application_state.page = None

    try:

        if application_state.playwright is not None:

            application_state.playwright.stop()

    except Exception:
        pass

    finally:

        application_state.playwright = None


# ============================================================
# EXECUÇÃO DO COMANDO
# ============================================================

def executar_comando(comando):

    if (
        not isinstance(comando, str)
        or not comando.strip()
    ):

        return {
            "ok": False,
            "message": "Comando vazio.",
            "status": "attention"
        }

    comando = comando.strip()

    with exec_lock:

        definir_estado(
            "thinking",
            "Entendendo seu comando"
        )

        adicionar_atividade(
            "Comando recebido",
            "blue"
        )

        with estado_lock:

            estado["ultimo_comando"] = comando

        try:

            print()
            print("=" * 60)
            print("JARVIS - COMANDO")
            print("=" * 60)
            print(comando)
            print("=" * 60)

            acao = orquestrador.interpretar(
                comando
            )

            if not isinstance(acao, dict):

                raise RuntimeError(
                    "O orquestrador retornou um resultado inválido."
                )

            tipo = acao.get(
                "acao",
                "ia"
            )

            adicionar_atividade(
                f"Intenção: {tipo}",
                "purple"
            )

            if tipo in {
                "programa",
                "abrir",
                "clicar",
                "preencher",
                "voltar",
                "avancar",
                "pesquisar_google"
            }:

                definir_estado(
                    "executing",
                    "Executando tarefa"
                )

            elif tipo == "ia":

                definir_estado(
                    "thinking",
                    "Consultando a inteligência artificial"
                )

            else:

                definir_estado(
                    "executing",
                    "Executando comando"
                )

            page = None

            if tipo in {
                "abrir",
                "clicar",
                "preencher",
                "voltar",
                "avancar",
                "pesquisar_google",
                "ia"
            }:

                page = obter_pagina()

            resultado = executor.executar(
                page,
                acao
            )

            resposta = str(resultado)

            definir_estado(
                "speaking",
                "Resposta pronta"
            )

            adicionar_atividade(
                "Tarefa concluída",
                "green"
            )

            with estado_lock:

                estado["ultima_resposta"] = resposta

            print("JARVIS - RESPOSTA:")
            print(resposta)
            print("=" * 60)
            print()

            return {
                "ok": True,
                "message": resposta,
                "status": "speaking",
                "action": acao
            }

        except Exception as erro:

            mensagem = str(erro)

            definir_estado(
                "attention",
                "Ocorreu um erro"
            )

            adicionar_atividade(
                "Erro na execução",
                "purple"
            )

            with estado_lock:

                estado["ultima_resposta"] = mensagem

            print()
            print("=" * 60)
            print("JARVIS - ERRO")
            print("=" * 60)
            print(mensagem)
            print("=" * 60)
            print()

            return {
                "ok": False,
                "message": (
                    "Não consegui concluir o comando: "
                    f"{mensagem}"
                ),
                "status": "attention"
            }


# ============================================================
# HTTP HANDLER
# ============================================================

class JarvisHandler(BaseHTTPRequestHandler):

    server_version = "JARVIS/1.0"


    # ========================================================
    # LOG
    # ========================================================

    def log_message(self, formato, *args):

        print(
            f"[HTTP] {self.address_string()} - "
            f"{formato % args}"
        )


    # ========================================================
    # JSON
    # ========================================================

    def enviar_json(self, dados, status=200):

        corpo = json.dumps(
            dados,
            ensure_ascii=False
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Content-Length",
            str(len(corpo))
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Cache-Control",
            "no-store"
        )

        self.end_headers()

        self.wfile.write(
            corpo
        )


    # ========================================================
    # OPTIONS
    # ========================================================

    def do_OPTIONS(self):

        self.send_response(204)

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.end_headers()


    # ========================================================
    # GET
    # ========================================================

    def do_GET(self):

        caminho = urlparse(
            self.path
        ).path


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if caminho == "/api/status":

            with estado_lock:

                dados_estado = dict(
                    estado
                )

            dados_estado["system"] = (
                obter_status_sistema()
            )

            self.enviar_json(
                dados_estado
            )

            return


        # ----------------------------------------------------
        # HEALTH
        # ----------------------------------------------------

        if caminho == "/api/health":

            self.enviar_json(
                {
                    "ok": True,
                    "service": "JARVIS",
                    "port": PORTA
                }
            )

            return


        # ----------------------------------------------------
        # INTERFACE
        # ----------------------------------------------------

        self.servir_arquivo(
            caminho
        )


    # ========================================================
    # POST
    # ========================================================

    def do_POST(self):

        caminho = urlparse(
            self.path
        ).path


        if caminho != "/api/comando":

            self.enviar_json(
                {
                    "ok": False,
                    "message": "Endpoint não encontrado."
                },
                404
            )

            return


        try:

            tamanho = int(
                self.headers.get(
                    "Content-Length",
                    "0"
                )
            )

            corpo = self.rfile.read(
                tamanho
            )

            dados = json.loads(
                corpo.decode("utf-8")
            )

            if not isinstance(dados, dict):

                raise ValueError(
                    "O corpo da requisição deve ser um objeto JSON."
                )


            # =================================================
            # CORREÇÃO
            #
            # A interface atual envia:
            #
            # {
            #     "comando": "..."
            # }
            #
            # Também aceitamos:
            #
            # {
            #     "command": "..."
            # }
            #
            # =================================================

            comando = dados.get(
                "comando",
                dados.get(
                    "command",
                    ""
                )
            )


            print(
                f"[API] Comando recebido: {comando}"
            )


        except Exception as erro:

            self.enviar_json(
                {
                    "ok": False,
                    "message": f"JSON inválido: {erro}"
                },
                400
            )

            return


        resposta = executar_comando(
            comando
        )


        self.enviar_json(
            resposta,
            200 if resposta.get("ok") else 500
        )


    # ========================================================
    # SERVIR INTERFACE
    # ========================================================

    def servir_arquivo(self, caminho):

        # ----------------------------------------------------
        # RAIZ
        # ----------------------------------------------------

        if caminho == "/":

            caminho = "/index.html"


        # ----------------------------------------------------
        # CORREÇÃO PRINCIPAL
        #
        # A interface pode solicitar:
        #
        # /interface/style.css
        # /interface/app.js
        #
        # Mas os arquivos estão fisicamente em:
        #
        # interface/style.css
        # interface/app.js
        #
        # Portanto removemos o prefixo /interface/.
        # ----------------------------------------------------

        prefixo_interface = "/interface"

        if caminho == prefixo_interface:

            caminho = "/index.html"

        elif caminho.startswith(
            prefixo_interface + "/"
        ):

            caminho = caminho[
                len(prefixo_interface):
            ]


        # ----------------------------------------------------
        # NORMALIZAÇÃO
        # ----------------------------------------------------

        caminho = caminho.lstrip("/")

        raiz_interface = os.path.abspath(
            DIRETORIO_INTERFACE
        )

        caminho_absoluto = os.path.abspath(
            os.path.join(
                raiz_interface,
                caminho
            )
        )


        # ----------------------------------------------------
        # PROTEÇÃO PATH TRAVERSAL
        # ----------------------------------------------------

        if (
            caminho_absoluto != raiz_interface
            and not caminho_absoluto.startswith(
                raiz_interface + os.sep
            )
        ):

            self.enviar_json(
                {
                    "ok": False,
                    "message": "Acesso negado."
                },
                403
            )

            return


        # ----------------------------------------------------
        # ARQUIVO NÃO EXISTE
        # ----------------------------------------------------

        if not os.path.isfile(
            caminho_absoluto
        ):

            self.enviar_json(
                {
                    "ok": False,
                    "message": (
                        "Arquivo não encontrado: "
                        f"{caminho}"
                    )
                },
                404
            )

            return


        # ----------------------------------------------------
        # MIME TYPES
        # ----------------------------------------------------

        extensoes = {

            ".html":
                "text/html; charset=utf-8",

            ".css":
                "text/css; charset=utf-8",

            ".js":
                "application/javascript; charset=utf-8",

            ".json":
                "application/json; charset=utf-8",

            ".png":
                "image/png",

            ".jpg":
                "image/jpeg",

            ".jpeg":
                "image/jpeg",

            ".svg":
                "image/svg+xml",

            ".ico":
                "image/x-icon"
        }


        extensao = os.path.splitext(
            caminho_absoluto
        )[1].lower()


        content_type = extensoes.get(
            extensao,
            "application/octet-stream"
        )


        # ----------------------------------------------------
        # LER ARQUIVO
        # ----------------------------------------------------

        with open(
            caminho_absoluto,
            "rb"
        ) as arquivo:

            conteudo = arquivo.read()


        # ----------------------------------------------------
        # RESPONDER
        # ----------------------------------------------------

        self.send_response(200)

        self.send_header(
            "Content-Type",
            content_type
        )

        self.send_header(
            "Content-Length",
            str(len(conteudo))
        )

        self.send_header(
            "Cache-Control",
            "no-store"
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.end_headers()

        self.wfile.write(
            conteudo
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)

    print(
        " J.A.R.V.I.S - SERVIDOR LOCAL"
    )

    print("=" * 60)

    print(
        f"Interface: http://{HOST}:{PORTA}"
    )

    print(
        f"API:       http://{HOST}:{PORTA}/api/comando"
    )

    print(
        f"Status:    http://{HOST}:{PORTA}/api/status"
    )

    print()

    print(
        "JARVIS: Navegador será iniciado somente "
        "quando uma ação precisar dele."
    )

    print()

    servidor = HTTPServer(
        (HOST, PORTA),
        JarvisHandler
    )

    print(
        "JARVIS: Sistema online."
    )

    print(
        "JARVIS: Abra a interface no navegador."
    )

    print(
        "JARVIS: Pressione CTRL+C para encerrar."
    )

    print()

    try:

        servidor.serve_forever()

    except KeyboardInterrupt:

        print()

        print(
            "JARVIS: Encerrando..."
        )

    finally:

        servidor.server_close()

        fechar_navegador()

        print(
            "JARVIS: Servidor encerrado."
        )


# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    main()