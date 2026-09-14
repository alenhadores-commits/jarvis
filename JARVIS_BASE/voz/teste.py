from voz.config import VOZ_ATIVA
from voz.motor import obter_configuracao_voz

config = obter_configuracao_voz()

print("VOZ JARVIS: OK")
print(f"VOZ ATIVA: {VOZ_ATIVA}")
print(f"PASTA: {config['pasta']}")
