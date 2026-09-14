from pathlib import Path

from .config import VOZ_ATIVA, PASTA_VOZES


def obter_configuracao_voz():
    pasta = Path(PASTA_VOZES) / VOZ_ATIVA

    return {
        "nome": VOZ_ATIVA,
        "pasta": pasta,
    }
