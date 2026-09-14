# ============================================
# CONFIGURACAO CENTRAL DA VOZ DO JARVIS
# ============================================

# ============================================
# MOTOR
# ============================================

MOTOR_VOZ = "xtts"

# ============================================
# VOZ NEURAL XTTS
# ============================================

VOZ_NEURAL_PADRAO = 1

VOZES_NEURAIS = {
    1: "Damien Black",
    2: "Andrew Chipper",
    3: "Craig Gutsy",
    4: "Zacharie Aimilios",
    5: "Marcos Rudaski",
}

# Python do ambiente dedicado do XTTS
PYTHON_XTTS = (
    r"C:\Users\almei\JARVIS\voz_neural\.venv\Scripts\python.exe"
)

# Motor XTTS
MOTOR_XTTS = (
    r"C:\Users\almei\JARVIS\voz\motor_xtts.py"
)

# ============================================
# COMPATIBILIDADE COM O MOTOR ANTIGO
# ============================================

VOZ_ATIVA = "jarvis"

PASTA_VOZES = r"C:\Users\almei\JARVIS\voz\vozes"

VELOCIDADE = 175
VOLUME = 1.0
