from habilidades.executor import ExecutorHabilidades

executor = ExecutorHabilidades()

habilidade = {
    "nome": "teste completo chatgpt",
    "acoes": [
        {
            "tipo": "abrir_programa",
            "valor": "chrome"
        },
        {
            "tipo": "esperar",
            "valor": "3"
        },
        {
            "tipo": "abrir_site",
            "valor": "https://chatgpt.com/"
        },
        {
            "tipo": "esperar_elemento",
            "valor": "caixa de mensagem",
            "timeout": 30
        },
        {
            "tipo": "clicar",
            "valor": "caixa de mensagem"
        },
        {
            "tipo": "digitar",
            "valor": "Qual o proximo jogo do Palmeiras?"
        },
        {
            "tipo": "esperar_elemento",
            "valor": "Receba mensagens mais inteligentes",
            "timeout": 10
        },
        {
            "tipo": "clicar",
            "valor": "Receba mensagens mais inteligentes"
        },
        {
            "tipo": "esperar_elemento",
            "valor": "enviar",
            "timeout": 10
        },
        {
            "tipo": "clicar",
            "valor": "enviar"
        },
        {
            "tipo": "esperar_resposta",
            "valor": "30"
        },
        {
            "tipo": "ler",
            "valor": "pagina"
        }
    ]
}

print(
    executor.executar(
        habilidade
    )
)
