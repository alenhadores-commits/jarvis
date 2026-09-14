from habilidades.executor import ExecutorHabilidades

executor = ExecutorHabilidades()

executor.ultimo_texto = "Palmeiras esta liderando o campeonato"

acao = {
    "tipo": "condicao",
    "valor": {
        "se": {
            "tipo": "se_contem",
            "valor": "Palmeiras"
        },
        "entao": [
            {
                "tipo": "falar",
                "valor": "Achei o Palmeiras."
            }
        ],
        "senao": [
            {
                "tipo": "falar",
                "valor": "Nao encontrei o Palmeiras."
            }
        ]
    }
}

executor._executar_acao(
    acao["tipo"],
    acao["valor"],
    acao
)
