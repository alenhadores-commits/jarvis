from playwright.sync_api import sync_playwright


def clicar_botao(pagina, texto):
    botoes = pagina.locator(
        "button, input[type='submit'], input[type='button']"
    )

    for i in range(botoes.count()):
        botao = botoes.nth(i)

        tag = botao.evaluate("(e) => e.tagName")

        if tag == "BUTTON":
            nome = botao.inner_text().strip()
        else:
            nome = botao.get_attribute("value") or ""

        if nome.lower().strip() == texto.lower().strip():
            botao.click()
            return True

    return False


def executar_ordem(url, ordem):
    with sync_playwright() as p:
        navegador = p.chromium.launch(headless=False)
        pagina = navegador.new_page()

        pagina.goto(url, wait_until="domcontentloaded")

        print("\nJARVIS: Analisando a página...")

        ordem = ordem.lower()

        if "clique" in ordem and "login" in ordem:

            sucesso = clicar_botao(pagina, "Login")

            if sucesso:
                print("JARVIS: Botão Login encontrado.")
                print("JARVIS: Clique executado.")
            else:
                print("JARVIS: Botão Login não encontrado.")

        else:
            print("JARVIS: Ordem ainda não reconhecida.")

        input("\nPressione ENTER para fechar...")
        navegador.close()


if __name__ == "__main__":

    ordem = input("Você: ")

    executar_ordem(
        "https://quotes.toscrape.com/login",
        ordem
    )