from TTS.api import TTS
import os
import winsound

saida = r"C:\Users\almei\JARVIS\voz_neural\teste_audio_debug.wav"

print("CARREGANDO XTTS...")
modelo = TTS(
    model_name="tts_models/multilingual/multi-dataset/xtts_v2",
    progress_bar=False
)

print("GERANDO WAV...")
modelo.tts_to_file(
    text="Teste de áudio direto do JARVIS. Se você ouvir esta frase, a geração neural está funcionando.",
    speaker="Damien Black",
    language="pt",
    file_path=saida
)

print("ARQUIVO:", saida)
print("EXISTE:", os.path.exists(saida))
print("TAMANHO:", os.path.getsize(saida) if os.path.exists(saida) else 0)

print("REPRODUZINDO WAV...")
winsound.PlaySound(
    saida,
    winsound.SND_FILENAME
)

print("REPRODUÇÃO TERMINADA.")
