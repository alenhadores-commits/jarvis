from habilidades.executor import ExecutorHabilidades

executor = ExecutorHabilidades()

executor.ultimo_texto = "Ainda nao encontrei"

acao = {
    "tipo": "loop_condicional",
    "valor": {
        "condicao": {
            "tipo": "se_contem",
            "valor": "Palmeiras"
        },
        "acoes": [
            {
                "tipo": "falar",
                "valor": "Tentando novamente..."
            }
        ],
        "maximo": 3
    }
}

executor._executar_acao(
    acao["tipo"],
    acao["valor"],
    acao
)
