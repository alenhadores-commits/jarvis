import pytesseract
from PIL import ImageGrab

# Caminho do Tesseract no Windows
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def ler_tela():
    """
    Captura a tela inteira e retorna o texto identificado pelo OCR.
    """

    imagem = ImageGrab.grab()

    texto = pytesseract.image_to_string(
        imagem,
        lang="por"
    )

    return texto.strip()


if __name__ == "__main__":
    print("JARVIS: Lendo a tela...")
    
    texto = ler_tela()

    print("\n--- TEXTO IDENTIFICADO ---")
    print(texto)
    print("--------------------------")