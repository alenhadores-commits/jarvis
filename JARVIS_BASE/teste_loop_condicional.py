from habilidades.executor import ExecutorHabilidades

executor = ExecutorHabilidades()

contador = 0

while contador < 3:

    contador += 1

    print(f"JARVIS: Tentativa {contador}")

    executor.ultimo_texto = "Ainda nao encontrei"

    resultado = executor._condicao_se_contem(
        "Palmeiras"
    )

    if resultado:
        print("JARVIS: Encontrado!")
        break

    print("JARVIS: Nao encontrou. Tentando novamente...")

print()
print("TESTE LOOP FINALIZADO")
