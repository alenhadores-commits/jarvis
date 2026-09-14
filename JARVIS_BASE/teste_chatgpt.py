from playwright.sync_api import sync_playwright


with sync_playwright() as p:

    navegador = p.chromium.launch(headless=False)

    pagina = navegador.new_page()

    pagina.goto(
        "https://chatgpt.com",
        wait_until="domcontentloaded"
    )

    pagina.wait_for_timeout(5000)

    campo = pagina.locator("textarea").first

    campo.fill(
        "Qual é o próximo jogo do Palmeiras?"
    )

    pagina.locator(
        'button[aria-label="Enviar mensagem"]'
    ).first.click()

    print("PERGUNTA ENVIADA.")
    print("AGUARDANDO RESPOSTA...")

    pagina.wait_for_timeout(15000)

    conversa = pagina.locator(
        "section.wm-app-conversation"
    ).inner_text()

    marcador = "O ChatGPT disse:"

    if marcador in conversa:

        resposta = conversa.split(
            marcador,
            1
        )[1].strip()

        print()
        print("=" * 60)
        print("RESPOSTA DO CHATGPT")
        print("=" * 60)
        print(resposta)
        print("=" * 60)

    else:

        print("NÃO ENCONTREI O MARCADOR DA RESPOSTA.")

    input("ENTER para fechar...")

    navegador.close()