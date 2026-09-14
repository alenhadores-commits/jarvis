import sys
import os
import tempfile
import winsound

# Limita o uso excessivo de threads
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")
os.environ.setdefault("NUMBA_NUM_THREADS", "1")

from TTS.api import TTS


MODELO = "tts_models/multilingual/multi-dataset/xtts_v2"

VOZES = {
    1: "Damien Black",
    2: "Andrew Chipper",
    3: "Craig Gutsy",
    4: "Zacharie Aimilios",
    5: "Marcos Rudaski",
}


def carregar_modelo():
    print("JARVIS: Carregando XTTS V2...", flush=True)

    modelo = TTS(
        model_name=MODELO,
        progress_bar=False
    )

    print("JARVIS: XTTS V2 carregado.", flush=True)

    return modelo


def gerar_audio(modelo, texto, numero_voz):
    voz = VOZES.get(
        numero_voz,
        VOZES[1]
    )

    arquivo = os.path.join(
        tempfile.gettempdir(),
        "jarvis_xtts.wav"
    )

    modelo.tts_to_file(
        text=texto,
        speaker=voz,
        language="pt",
        file_path=arquivo
    )

    return arquivo


def main():
    modelo = carregar_modelo()

    for linha in sys.stdin:
        texto = linha.strip()

        if not texto:
            continue

        if texto == "__SAIR__":
            break

        try:
            if texto.startswith("__VOZ__:"):
                numero = int(
                    texto.split(":", 1)[1]
                )

                if numero in VOZES:
                    print(
                        f"JARVIS: Voz neural selecionada: {VOZES[numero]}",
                        flush=True
                    )

                continue

            partes = texto.split("|", 1)

            if len(partes) != 2:
                continue

            numero_voz = int(partes[0])
            texto_fala = partes[1].strip()

            if not texto_fala:
                continue

            arquivo = gerar_audio(
                modelo,
                texto_fala,
                numero_voz
            )

            winsound.PlaySound(
                arquivo,
                winsound.SND_FILENAME
            )

            try:
                os.remove(arquivo)
            except Exception:
                pass

            print("__OK__", flush=True)

        except Exception as erro:
            print(
                f"__ERRO__:{erro}",
                flush=True
            )


if __name__ == "__main__":
    main()
