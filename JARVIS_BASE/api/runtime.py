import io
import threading
from contextlib import redirect_stdout

from ai.classificador_intencao import obter_classificador
from ai.orquestrador import Orquestrador
from ai.executor import Executor
from habilidades.gerenciador import GerenciadorHabilidades
from habilidades.executor import ExecutorHabilidades
from rag.chroma import BancoChroma
from rag.recuperador import Recuperador
from memoria_retriever import MemoriaRetriever
from ai.aprendizado import obter_aprendizado

import jarvis


class JarvisRuntime:

    def __init__(self):
        self.lock = threading.RLock()

        print("API: inicializando núcleo do JARVIS...")

        self.classificador_intencao = obter_classificador()

        self.orquestrador = Orquestrador()
        self.executor = Executor()

        self.aprendizado = obter_aprendizado()
        print("API: aprendizado ativado.")

        self.gerenciador_habilidades = (
            GerenciadorHabilidades()
        )

        self.executor_habilidades = (
            ExecutorHabilidades()
        )

        try:
            self.banco_chroma = BancoChroma()

            self.recuperador = Recuperador(
                self.banco_chroma
            )

            print(
                "API: recuperador Chroma ativado."
            )

        except Exception as erro:
            self.banco_chroma = None
            self.recuperador = None

            print(
                f"API: aviso - Chroma indisponível: {erro}"
            )

        try:
            self.memoria_retriever = MemoriaRetriever()

            print(
                "API: memória semântica ativada."
            )

        except Exception as erro:
            self.memoria_retriever = None

            print(
                f"API: aviso - memória semântica indisponível: {erro}"
            )

    def processar(self, comando: str) -> dict:

        comando = str(comando).strip()

        if not comando:
            return {
                "ok": False,
                "erro": "Comando vazio.",
            }

        with self.lock:

            triagem = None

            try:
                triagem = (
                    self.classificador_intencao.classificar(
                        comando
                    )
                )
            except Exception as erro:
                triagem = {
                    "erro": str(erro)
                }

            captura = io.StringIO()

            try:

                with redirect_stdout(captura):

                    jarvis.processar_comando(
                        comando,
                        self.orquestrador,
                        self.executor,
                        None,
                        self.gerenciador_habilidades,
                        self.executor_habilidades,
                        self.recuperador,
                        triagem,
                        self.memoria_retriever,
                        self.aprendizado,
                    )

                saida = captura.getvalue().strip()

                resposta = self._extrair_resposta(
                    saida
                )

                return {
                    "ok": True,
                    "comando": comando,
                    "triagem": triagem,
                    "resposta": (
                resposta
                or (
                    str(saida).splitlines()[-1].strip()
                    if saida and str(saida).splitlines()
                    else ""
                )
            ),
                    "saida": saida,
                }

            except Exception as erro:

                return {
                    "ok": False,
                    "comando": comando,
                    "triagem": triagem,
                    "erro": str(erro),
                }

    @staticmethod
    def _extrair_resposta(saida: str) -> str:

        if not saida:
            return ""

        linhas = saida.splitlines()
        blocos = []

        indice = 0

        while indice < len(linhas):

            linha = linhas[indice].strip()

            if (
                linha.startswith("JARVIS:")
                and not linha.startswith(
                    "JARVIS recebeu:"
                )
            ):

                texto = linha[
                    len("JARVIS:"):
                ].strip()

                if texto:
                    blocos.append(texto)

                indice += 1

                while indice < len(linhas):

                    proxima = linhas[indice].strip()

                    if (
                        not proxima
                        or proxima.startswith(
                            "JARVIS:"
                        )
                        or proxima.startswith(
                            "CHROMA:"
                        )
                    ):
                        break

                    if proxima.startswith("="):
                        break

                    blocos.append(proxima)
                    indice += 1

                continue

            indice += 1

        return "\n".join(blocos).strip()


runtime = JarvisRuntime()
