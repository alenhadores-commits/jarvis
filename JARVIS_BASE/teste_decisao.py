from habilidades.executor import ExecutorHabilidades

executor = ExecutorHabilidades()

executor.ultimo_texto = "Palmeiras esta liderando o campeonato"

condicao = executor._condicao_se_contem("Palmeiras")

print()
print("RESULTADO DA CONDICAO:", condicao)

if condicao:
    print("ENTAO: condicao verdadeira")
else:
    print("SENAO: condicao falsa")
