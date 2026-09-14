from playwright.sync_api import sync_playwright

PERFIL = r"C:\Users\almei\JARVIS\dados_chrome"

with sync_playwright() as p:

    contexto = p.chromium.launch_persistent_context(
        user_data_dir=PERFIL,
        channel="chrome",
        headless=False,
        args=["--start-maximized"],
        ignore_default_args=["--no-sandbox"],
    )

    page = contexto.pages[0] if contexto.pages else contexto.new_page()

    page.goto(
        "https://chatgpt.com/",
        wait_until="domcontentloaded",
        timeout=60000,
    )

    page.wait_for_timeout(5000)

    print("\n" + "=" * 60)
    print("DIAGNOSTICO CHATGPT")
    print("=" * 60)

    print("\nURL:")
    print(page.url)

    print("\nTEXTAREAS:")
    print(page.locator("textarea").count())

    print("\nASSISTANT data-message-author-role:")
    print(
        page.locator(
            "[data-message-author-role='assistant']"
        ).count()
    )

    print("\nELEMENTOS article assistant:")
    print(
        page.locator(
            "article[data-message-author-role='assistant']"
        ).count()
    )

    print("\nELEMENTOS com markdown:")
    print(
        page.locator(".markdown").count()
    )

    print("\n--- TEXTOS DA PAGINA ---\n")

    texto = page.locator("body").inner_text()

    print(texto[:8000])

    print("\n" + "=" * 60)
    print("FIM DO DIAGNOSTICO")
    print("=" * 60)

    input("\nPressione ENTER para fechar...")
    contexto.close()