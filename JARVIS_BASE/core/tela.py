from PIL import ImageGrab


def capturar_tela():
    imagem = ImageGrab.grab()
    imagem.save("tela_teste.png")
    return imagem


if __name__ == "__main__":
    print("Capturando tela...")

    capturar_tela()

    print("CAPTURA OK")
    print("Arquivo salvo: tela_teste.png")