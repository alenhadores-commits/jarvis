import sys
import json
import time
import urllib.request
import urllib.error
from datetime import datetime

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QTextEdit,
    QGridLayout,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

API = "http://127.0.0.1:8000"




# ============================================================
# UTILITÁRIOS
# ============================================================

def api_get(endpoint):
    try:
        with urllib.request.urlopen(
            API + endpoint,
            timeout=2
        ) as resposta:

            return json.loads(
                resposta.read().decode("utf-8")
            )

    except Exception:
        return None


def api_post(endpoint, dados):
    try:
        corpo = json.dumps(dados).encode("utf-8")

        requisicao = urllib.request.Request(
            API + endpoint,
            data=corpo,
            headers={
                "Content-Type": "application/json"
            },
            method="POST"
        )

        with urllib.request.urlopen(
            requisicao,
            timeout=30
        ) as resposta:

            return json.loads(
                resposta.read().decode("utf-8")
            )

    except Exception as erro:
        return {
            "ok": False,
            "message": str(erro)
        }


# ============================================================
# CARD
# ============================================================

class Card(QFrame):

    def __init__(self, titulo, valor="--"):
        super().__init__()

        self.setObjectName("Card")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)

        self.titulo = QLabel(titulo)
        self.titulo.setObjectName("CardTitle")

        self.valor = QLabel(valor)
        self.valor.setObjectName("CardValue")

        layout.addWidget(self.titulo)
        layout.addWidget(self.valor)


# ============================================================
# JANELA PRINCIPAL
# ============================================================

class JarvisPC(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("J.A.R.V.I.S — Command Center")

        self.resize(1400, 850)

        self.setMinimumSize(1100, 700)

        self.setStyleSheet("""
        
        QMainWindow {
            background: #070b12;
        }

        QWidget {
            color: #d8e2f0;
            font-family: Segoe UI;
        }

        QFrame#Header {
            background: #0b111b;
            border-bottom: 1px solid #1b2a3d;
        }

        QFrame#Panel {
            background: #0b111b;
            border: 1px solid #172337;
            border-radius: 8px;
        }

        QFrame#Card {
            background: #0c1420;
            border: 1px solid #1a2a40;
            border-radius: 8px;
        }

        QLabel#Logo {
            color: #70b7ff;
            font-size: 30px;
            font-weight: 700;
            letter-spacing: 4px;
        }

        QLabel#Subtitle {
            color: #64758b;
            font-size: 11px;
            letter-spacing: 2px;
        }

        QLabel#StatusOnline {
            color: #53e69b;
            font-weight: 700;
        }

        QLabel#StatusOffline {
            color: #ff647c;
            font-weight: 700;
        }

        QLabel#PanelTitle {
            color: #7890aa;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 2px;
        }

        QLabel#BigStatus {
            color: #53e69b;
            font-size: 25px;
            font-weight: 700;
        }

        QLabel#CardTitle {
            color: #687d96;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
        }

        QLabel#CardValue {
            color: #dce9f7;
            font-size: 24px;
            font-weight: 600;
        }

        QLabel#Service {
            color: #b7c5d5;
            font-size: 13px;
        }

        QLabel#ServiceOK {
            color: #53e69b;
            font-size: 13px;
        }

        QTextEdit {
            background: #070c13;
            border: 1px solid #172337;
            border-radius: 6px;
            color: #a9bbcf;
            padding: 8px;
            font-family: Consolas;
            font-size: 12px;
        }

        QLineEdit {
            background: #080e17;
            border: 1px solid #24364e;
            border-radius: 6px;
            padding: 13px;
            color: #e4edf8;
            font-size: 14px;
        }

        QLineEdit:focus {
            border: 1px solid #4285c7;
        }

        QPushButton {
            background: #14243a;
            border: 1px solid #27415f;
            border-radius: 6px;
            padding: 12px 22px;
            color: #bcd5ed;
            font-weight: 600;
        }

        QPushButton:hover {
            background: #1a3150;
            border: 1px solid #3970a5;
        }

        QPushButton:pressed {
            background: #0d1b2c;
        }

        """)

        self.criar_interface()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.atualizar)
        self.timer.start(1000)

        self.atualizar()


    # ========================================================
    # INTERFACE
    # ========================================================

    def criar_interface(self):

        central = QWidget()

        self.setCentralWidget(central)

        principal = QVBoxLayout(central)

        principal.setContentsMargins(
            18,
            18,
            18,
            18
        )

        principal.setSpacing(14)


        # ----------------------------------------------------
        # HEADER
        # ----------------------------------------------------

        header = QFrame()
        header.setObjectName("Header")

        header_layout = QHBoxLayout(header)

        header_layout.setContentsMargins(
            18,
            12,
            18,
            12
        )


        esquerda = QVBoxLayout()

        self.logo = QLabel("J.A.R.V.I.S")
        self.logo.setObjectName("Logo")

        self.subtitle = QLabel(
            "PERSONAL ARTIFICIAL INTELLIGENCE • COMMAND CENTER"
        )

        self.subtitle.setObjectName("Subtitle")

        esquerda.addWidget(self.logo)
        esquerda.addWidget(self.subtitle)


        header_layout.addLayout(esquerda)

        header_layout.addStretch()


        self.status = QLabel("● OFFLINE")
        self.status.setObjectName("StatusOffline")

        header_layout.addWidget(self.status)

        self.clock = QLabel("--:--:--")

        self.clock.setStyleSheet("""
            color: #8295aa;
            font-family: Consolas;
            font-size: 13px;
        """)

        header_layout.addWidget(self.clock)


        principal.addWidget(header)


        # ----------------------------------------------------
        # LINHA PRINCIPAL
        # ----------------------------------------------------

        linha = QHBoxLayout()

        linha.setSpacing(14)


        # ----------------------------------------------------
        # PAINEL ESQUERDO
        # ----------------------------------------------------

        painel_status = QFrame()
        painel_status.setObjectName("Panel")

        layout_status = QVBoxLayout(painel_status)

        layout_status.setContentsMargins(
            20,
            20,
            20,
            20
        )


        titulo = QLabel("STATUS DO SISTEMA")
        titulo.setObjectName("PanelTitle")

        layout_status.addWidget(titulo)

        layout_status.addSpacing(20)


        self.big_status = QLabel("OFFLINE")
        self.big_status.setObjectName("BigStatus")

        layout_status.addWidget(self.big_status)


        layout_status.addSpacing(15)


        self.descricao = QLabel(
            "Aguardando conexão com o núcleo."
        )

        self.descricao.setWordWrap(True)

        self.descricao.setStyleSheet(
            "color: #71849b; font-size: 12px;"
        )

        layout_status.addWidget(self.descricao)


        layout_status.addSpacing(25)


        self.usuario = QLabel(
            "USUÁRIO\nCHEFE"
        )

        self.usuario.setStyleSheet("""
            color: #9eb1c7;
            font-size: 12px;
            line-height: 150%;
        """)

        layout_status.addWidget(self.usuario)


        self.uptime = QLabel(
            "UPTIME\n--"
        )

        self.uptime.setStyleSheet("""
            color: #9eb1c7;
            font-size: 12px;
        """)

        layout_status.addWidget(self.uptime)


        layout_status.addStretch()


        linha.addWidget(
            painel_status,
            1
        )


        # ----------------------------------------------------
        # TELEMETRIA
        # ----------------------------------------------------

        painel_telemetria = QFrame()
        painel_telemetria.setObjectName("Panel")

        layout_tel = QVBoxLayout(painel_telemetria)

        layout_tel.setContentsMargins(
            20,
            20,
            20,
            20
        )


        titulo_tel = QLabel("TELEMETRIA")
        titulo_tel.setObjectName("PanelTitle")

        layout_tel.addWidget(titulo_tel)


        grid = QGridLayout()

        grid.setSpacing(10)


        self.card_cpu = Card(
            "CPU",
            "--"
        )

        self.card_ram = Card(
            "RAM",
            "--"
        )

        self.card_gpu = Card(
            "GPU",
            "--"
        )

        self.card_vram = Card(
            "VRAM",
            "--"
        )


        grid.addWidget(
            self.card_cpu,
            0,
            0
        )

        grid.addWidget(
            self.card_ram,
            0,
            1
        )

        grid.addWidget(
            self.card_gpu,
            1,
            0
        )

        grid.addWidget(
            self.card_vram,
            1,
            1
        )


        layout_tel.addLayout(grid)

        layout_tel.addStretch()


        linha.addWidget(
            painel_telemetria,
            2
        )


        principal.addLayout(linha)


        # ----------------------------------------------------
        # SEGUNDA LINHA
        # ----------------------------------------------------

        linha2 = QHBoxLayout()

        linha2.setSpacing(14)


        # ----------------------------------------------------
        # SERVIÇOS
        # ----------------------------------------------------

        painel_servicos = QFrame()
        painel_servicos.setObjectName("Panel")

        servicos_layout = QVBoxLayout(painel_servicos)

        servicos_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )


        titulo_serv = QLabel("SERVIÇOS")
        titulo_serv.setObjectName("PanelTitle")

        servicos_layout.addWidget(titulo_serv)

        servicos_layout.addSpacing(12)


        servicos = [
            "NÚCLEO JARVIS",
            "API LOCAL",
            "INTELIGÊNCIA ARTIFICIAL",
            "SISTEMA DE VOZ",
            "NAVEGADOR",
            "POSTGRESQL",
            "N8N",
        ]


        for nome in servicos:

            linha_serv = QHBoxLayout()

            bolinha = QLabel("●")

            bolinha.setObjectName(
                "ServiceOK"
            )

            texto = QLabel(nome)

            texto.setObjectName(
                "Service"
            )

            linha_serv.addWidget(
                bolinha
            )

            linha_serv.addWidget(
                texto
            )

            linha_serv.addStretch()

            servicos_layout.addLayout(
                linha_serv
            )


        servicos_layout.addStretch()


        linha2.addWidget(
            painel_servicos,
            1
        )


        # ----------------------------------------------------
        # ATIVIDADE
        # ----------------------------------------------------

        painel_atividade = QFrame()
        painel_atividade.setObjectName("Panel")

        atividade_layout = QVBoxLayout(
            painel_atividade
        )

        atividade_layout.setContentsMargins(
            20,
            20,
            20,
            20
        )


        titulo_atividade = QLabel(
            "ATIVIDADE"
        )

        titulo_atividade.setObjectName(
            "PanelTitle"
        )

        atividade_layout.addWidget(
            titulo_atividade
        )


        self.log = QTextEdit()

        self.log.setReadOnly(True)

        atividade_layout.addWidget(
            self.log
        )


        linha2.addWidget(
            painel_atividade,
            2
        )


        principal.addLayout(linha2, 2)


        # ----------------------------------------------------
        # COMANDO
        # ----------------------------------------------------

        comando_layout = QHBoxLayout()

        self.comando = QLineEdit()

        self.comando.setPlaceholderText(
            "> Digite um comando para o JARVIS..."
        )


        self.comando.returnPressed.connect(
            self.enviar_comando
        )


        botao = QPushButton(
            "EXECUTAR"
        )

        botao.clicked.connect(
            self.enviar_comando
        )


        comando_layout.addWidget(
            self.comando
        )

        comando_layout.addWidget(
            botao
        )


        principal.addLayout(
            comando_layout
        )


    # ========================================================
    # LOG
    # ========================================================

    def adicionar_log(self, texto):

        hora = datetime.now().strftime(
            "%H:%M:%S"
        )

        self.log.append(
            f"[{hora}] {texto}"
        )


    # ========================================================
    # STATUS
    # ========================================================

    def atualizar(self):

        self.clock.setText(
            datetime.now().strftime(
                "%H:%M:%S"
            )
        )


        dados = api_get(
            "/api/status"
        )


        if not dados:

            self.status.setText(
                "● OFFLINE"
            )

            self.status.setObjectName(
                "StatusOffline"
            )

            self.big_status.setText(
                "OFFLINE"
            )

            self.big_status.setStyleSheet(
                "color: #ff647c;"
            )

            self.descricao.setText(
                "Servidor JARVIS não encontrado."
            )

            return


        # ----------------------------------------------------
        # ONLINE
        # ----------------------------------------------------

        self.status.setText(
            "● ONLINE"
        )

        self.status.setStyleSheet(
            "color: #53e69b; font-weight: 700;"
        )


        status = dados.get(
            "status",
            "ready"
        )


        descricao = dados.get(
            "descricao",
            ""
        )


        self.big_status.setText(
            status.upper()
        )

        self.big_status.setStyleSheet(
            "color: #53e69b; font-size: 25px; font-weight: 700;"
        )


        self.descricao.setText(
            descricao
        )


        # ----------------------------------------------------
        # TELEMETRIA
        # ----------------------------------------------------

        sistema = dados.get(
            "sistema",
            {}
        )


        cpu = sistema.get(
            "cpu",
            None
        )

        ram = sistema.get(
            "ram",
            None
        )

        uptime = sistema.get(
            "uptime",
            None
        )


        if cpu is not None:

            self.card_cpu.valor.setText(
                f"{cpu}%"
            )


        if ram is not None:

            self.card_ram.valor.setText(
                f"{ram}%"
            )


        self.card_gpu.valor.setText(
            "--"
        )

        self.card_vram.valor.setText(
            "--"
        )


        if uptime:

            self.uptime.setText(
                f"UPTIME\n{uptime}"
            )


        # ----------------------------------------------------
        # ÚLTIMA ATIVIDADE
        # ----------------------------------------------------

        atividades = dados.get(
            "atividade",
            []
        )


        if atividades:

            ultimo = atividades[-1]

            if isinstance(
                ultimo,
                dict
            ):

                mensagem = (
                    ultimo.get("texto")
                    or ultimo.get("descricao")
                    or str(ultimo)
                )

            else:

                mensagem = str(
                    ultimo
                )

            # evita poluir a tela
            texto_atual = self.log.toPlainText()

            if mensagem not in texto_atual:

                self.adicionar_log(
                    mensagem
                )


    # ========================================================
    # ENVIAR COMANDO
    # ========================================================

    def enviar_comando(self):

        comando = self.comando.text().strip()


        if not comando:

            return


        self.adicionar_log(
            f"> {comando}"
        )


        self.comando.clear()


        resposta = api_post(
            "/api/comando",
            {
                "comando": comando
            }
        )


        if not resposta:

            self.adicionar_log(
                "ERRO: servidor não respondeu."
            )

            return


        if resposta.get(
            "ok",
            False
        ):

            mensagem = resposta.get(
                "message",
                ""
            )

            self.adicionar_log(
                f"JARVIS: {mensagem}"
            )

        else:

            erro = resposta.get(
                "message",
                "Erro desconhecido."
            )

            self.adicionar_log(
                f"ERRO: {erro}"
            )


# ============================================================
# MAIN
# ============================================================

def main():

    app = QApplication(
        sys.argv
    )

    app.setApplicationName(
        "JARVIS"
    )

    janela = JarvisPC()

    janela.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":

    main()