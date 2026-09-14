import pyautogui
import time


def escrever(texto):
    pyautogui.write(texto, interval=0.03)


def pressionar(tecla):
    pyautogui.press(tecla)


if __name__ == "__main__":
    print("Abra o Bloco de Notas manualmente.")
    print("Você tem 3 segundos...")

    time.sleep(3)

    escrever("JARVIS funcionando. Controle de teclado OK!")

    print("TEXTO DIGITADO")