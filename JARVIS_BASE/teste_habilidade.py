from habilidades.executor import ExecutorHabilidades

executor = ExecutorHabilidades()

habilidade = {
    "nome": "teste navegador",
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
            "tipo": "pressionar_tecla",
            "valor": "Enter"
        }
    ]
}

print(
    executor.executar(
        habilidade
    )
)
