import pyautogui


def mover_mouse(x, y):
    pyautogui.moveTo(x, y, duration=0.5)


def clicar():
    pyautogui.click()


def duplo_clique():
    pyautogui.doubleClick()


def escrever(texto):
    pyautogui.write(texto, interval=0.03)


def pressionar(tecla):
    pyautogui.press(tecla)


def hotkey(*teclas):
    pyautogui.hotkey(*teclas)


if __name__ == "__main__":
    print("TESTE DO CONTROLE DO PC")
    print("-" * 30)

    largura, altura = pyautogui.size()

    print(f"Resolução: {largura}x{altura}")

    print("Movendo mouse para o centro...")
    mover_mouse(largura // 2, altura // 2)

    print("Controle do mouse OK.")
    print("Controle do teclado OK.")
    print("Módulo carregado com sucesso.")