from habilidades.executor import ExecutorHabilidades

executor = ExecutorHabilidades()

habilidade = {
    "nome": "teste variaveis",
    "acoes": [
        {
            "tipo": "definir_variavel",
            "valor": "nome=chefe"
        },
        {
            "tipo": "falar",
            "valor": "Ola {nome}."
        },
        {
            "tipo": "salvar_resultado",
            "valor": "mensagem"
        },
        {
            "tipo": "usar_variavel",
            "valor": "mensagem"
        }
    ]
}

resultado = executor.executar(habilidade)

print()
print("TESTE FINAL:", resultado)
