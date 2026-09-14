# -*- coding: utf-8 -*-

import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel


DISPOSITIVO = 5
TAXA_AMOSTRAGEM = 48000
TEMPO_GRAVACAO = 5

modelo = None


def obter_modelo():

    global modelo

    if modelo is None:

        print(
            "JARVIS: Carregando modelo de reconhecimento de voz..."
        )

        modelo = WhisperModel(
            "small",
            device="cpu",
            compute_type="int8"
        )

        print(
            "JARVIS: Modelo de voz carregado."
        )

    return modelo


def ouvir():

    print("JARVIS: Estou ouvindo...")

    arquivo = "voz_teste.wav"

    audio = sd.rec(
        int(TEMPO_GRAVACAO * TAXA_AMOSTRAGEM),
        samplerate=TAXA_AMOSTRAGEM,
        channels=1,
        dtype="float32",
        device=DISPOSITIVO
    )

    sd.wait()

    sf.write(
        arquivo,
        audio,
        TAXA_AMOSTRAGEM
    )

    modelo_voz = obter_modelo()

    segmentos, _ = modelo_voz.transcribe(
        arquivo,
        language="pt",
        beam_size=5,
        vad_filter=False
    )

    texto = " ".join(
        segmento.text.strip()
        for segmento in segmentos
    )

    return texto.strip()


if __name__ == "__main__":

    texto = ouvir()

    print()
    print("JARVIS ENTENDEU:")
    print(texto)