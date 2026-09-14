from habilidades.executor import ExecutorHabilidades

executor = ExecutorHabilidades()

executor.ultimo_texto = "Corinthians esta liderando o campeonato"

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
                "valor": "E Palmeiras."
            }
        ],
        "senao": [
            {
                "tipo": "condicao",
                "valor": {
                    "se": {
                        "tipo": "se_contem",
                        "valor": "Corinthians"
                    },
                    "entao": [
                        {
                            "tipo": "falar",
                            "valor": "E Corinthians."
                        }
                    ],
                    "senao": [
                        {
                            "tipo": "falar",
                            "valor": "Nao reconheci o time."
                        }
                    ]
                }
            }
        ]
    }
}

executor._executar_acao(
    acao["tipo"],
    acao["valor"],
    acao
)
