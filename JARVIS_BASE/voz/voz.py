import queue
import threading
import subprocess

from voz.config import (
    MOTOR_VOZ,
    VOZ_NEURAL_PADRAO,
    PYTHON_XTTS,
    MOTOR_XTTS,
)

_fila_voz = queue.Queue()

_thread_voz = None
_lock_thread = threading.Lock()

_processo_xtts = None
_lock_xtts = threading.Lock()


def _iniciar_xtts():
    global _processo_xtts

    with _lock_xtts:

        if (
            _processo_xtts is not None
            and _processo_xtts.poll() is None
        ):
            return _processo_xtts

        print(
            "JARVIS: Iniciando motor neural XTTS...",
            flush=True
        )

        _processo_xtts = subprocess.Popen(
            [
                PYTHON_XTTS,
                MOTOR_XTTS,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            cwd=r"C:\Users\almei\JARVIS",
        )

        return _processo_xtts


def inicializar_voz():

    if MOTOR_VOZ.lower() != "xtts":
        return

    processo = _iniciar_xtts()

    if processo.poll() is not None:
        raise RuntimeError(
            "O processo XTTS encerrou durante a inicializacao."
        )

    print(
        "JARVIS: Motor neural XTTS iniciado.",
        flush=True
    )


def _falar_xtts(texto):

    processo = _iniciar_xtts()

    if processo.poll() is not None:
        raise RuntimeError(
            "O processo XTTS foi encerrado inesperadamente."
        )

    if processo.stdin is None:
        raise RuntimeError(
            "Entrada do motor XTTS indisponivel."
        )

    if processo.stdout is None:
        raise RuntimeError(
            "Saida do motor XTTS indisponivel."
        )

    comando = (
        f"{VOZ_NEURAL_PADRAO}|"
        f"{texto}\n"
    )

    processo.stdin.write(comando)
    processo.stdin.flush()

    while True:

        linha = processo.stdout.readline()

        if not linha:
            raise RuntimeError(
                "O motor XTTS encerrou antes de confirmar a reproducao."
            )

        linha = linha.strip()

        if not linha:
            continue

        if linha == "__OK__":
            return

        if linha.startswith("__ERRO__:"):
            raise RuntimeError(
                linha
            )

        print(
            linha,
            flush=True
        )


def _worker_voz():

    while True:

        texto = _fila_voz.get()

        try:

            if texto is None:
                break

            texto = str(texto).strip()

            if not texto:
                continue

            if MOTOR_VOZ.lower() == "xtts":

                _falar_xtts(
                    texto
                )

            else:

                print(
                    "JARVIS: Motor de voz nao configurado como XTTS.",
                    flush=True
                )

        except Exception as erro:

            print()
            print(
                "JARVIS: Erro no motor de voz:",
                erro,
                flush=True
            )

        finally:

            _fila_voz.task_done()


def _garantir_thread_voz():

    global _thread_voz

    with _lock_thread:

        if (
            _thread_voz is None
            or not _thread_voz.is_alive()
        ):

            _thread_voz = threading.Thread(
                target=_worker_voz,
                name="JARVIS-Voz",
                daemon=True,
            )

            _thread_voz.start()


def falar(texto):

    texto = str(
        texto or ""
    ).strip()

    if not texto:
        return

    _garantir_thread_voz()

    _fila_voz.put(
        texto
    )
