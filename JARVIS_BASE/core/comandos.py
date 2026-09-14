import subprocess


PROGRAMAS = {
    "bloco de notas": "notepad.exe",
    "notepad": "notepad.exe",
    "calculadora": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
}


def executar_comando(texto):
    texto = texto.lower().strip()

    # Remove formas comuns de falar com o JARVIS
    texto = texto.replace("jarvis", "")
    texto = texto.replace(",", " ").strip()

    for nome, executavel in PROGRAMAS.items():

        if nome in texto:

            subprocess.Popen(executavel)

            return f"Abrindo {nome}."

    return "Comando não reconhecido."


if __name__ == "__main__":

    while True:

        comando = input("Você: ")

        if comando.lower() in ["sair", "fechar", "encerrar"]:
            print("JARVIS: Encerrando.")
            break

        resposta = executar_comando(comando)

        print(f"JARVIS: {resposta}")