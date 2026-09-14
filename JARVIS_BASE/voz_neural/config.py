# Configuração da voz neural do JARVIS

VOZ_PADRAO = 1

VOZES = {
    1: "Damien Black",
    2: "Andrew Chipper",
    3: "Craig Gutsy",
    4: "Zacharie Aimilios",
    5: "Marcos Rudaski",
}

def obter_voz(numero=None):
    numero = VOZ_PADRAO if numero is None else numero

    if numero not in VOZES:
        raise ValueError(
            f"Voz inválida: {numero}. "
            f"Escolha entre: {', '.join(map(str, VOZES.keys()))}"
        )

    return VOZES[numero]
