from habilidades.executor import ExecutorHabilidades

executor = ExecutorHabilidades()

executor._definir_variavel({
    "nome": "texto_teste",
    "valor": "Palmeiras lidera o Brasileirao"
})

executor.ultimo_texto = executor.variaveis["texto_teste"]

print()
print("=== TESTE se_contem ===")

executor._condicao_se_contem("Palmeiras")

print("Resultado:", executor.ultimo_resultado)

print()
print("=== TESTE se_igual ===")

executor.ultimo_texto = "Palmeiras"

executor._condicao_se_igual("Palmeiras")

print("Resultado:", executor.ultimo_resultado)
