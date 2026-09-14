from playwright.sync_api import Page


def abrir(page: Page, url: str):
    page.goto(url, wait_until="domcontentloaded")
    return f"Página aberta: {page.url}"


def clicar(page: Page, texto: str):
    elemento = page.get_by_text(texto, exact=True)

    if elemento.count() == 0:
        return f"Elemento não encontrado: {texto}"

    elemento.first.click()
    return f"Clique executado: {texto}"


def preencher(page: Page, seletor: str, texto: str):
    campo = page.locator(seletor)

    if campo.count() == 0:
        return f"Campo não encontrado: {seletor}"

    campo.first.fill(texto)
    return f"Campo preenchido: {seletor}"


def voltar(page: Page):
    page.go_back()
    return f"Voltou para: {page.url}"


def avancar(page: Page):
    page.go_forward()
    return f"Avançou para: {page.url}"
