import pyautogui


def mover_mouse(x, y):
    pyautogui.moveTo(x, y, duration=0.5)


def clicar():
    pyautogui.click()


def duplo_clique():
    pyautogui.doubleClick()


if __name__ == "__main__":
    print("Movendo mouse para o centro da tela...")

    largura, altura = pyautogui.size()

    mover_mouse(largura // 2, altura // 2)

    print("Mouse no centro.")
    print("Executando clique...")

    clicar()

    print("CLIQUE OK")