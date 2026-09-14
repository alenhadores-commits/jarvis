from playwright.sync_api import Page


def ler_pagina(page: Page):

    resultado = {
        "url": page.url,
        "titulo": page.title(),
        "texto": page.locator("body").inner_text(),
        "links": [],
        "botoes": [],
        "campos": [],
        "scripts": []
    }

    # LINKS
    links = page.locator("a")

    for i in range(links.count()):
        elemento = links.nth(i)

        resultado["links"].append({
            "texto": elemento.inner_text().strip(),
            "href": elemento.get_attribute("href")
        })

    # BOTÕES
    botoes = page.locator(
        "button, input[type='submit'], input[type='button']"
    )

    for i in range(botoes.count()):
        elemento = botoes.nth(i)

        tag = elemento.evaluate("(e) => e.tagName")

        if tag == "BUTTON":
            texto = elemento.inner_text().strip()
        else:
            texto = elemento.get_attribute("value") or ""

        resultado["botoes"].append({
            "texto": texto,
            "tipo": elemento.get_attribute("type")
        })

    # CAMPOS
    campos = page.locator("input, textarea, select")

    for i in range(campos.count()):
        elemento = campos.nth(i)

        resultado["campos"].append({
            "tag": elemento.evaluate("(e) => e.tagName"),
            "tipo": elemento.get_attribute("type"),
            "nome": elemento.get_attribute("name"),
            "id": elemento.get_attribute("id"),
            "placeholder": elemento.get_attribute("placeholder")
        })

    # SCRIPTS
    scripts = page.locator("script")

    for i in range(scripts.count()):
        elemento = scripts.nth(i)
        conteudo = elemento.text_content() or ""

        if conteudo.strip():
            resultado["scripts"].append(conteudo[:5000])

    return resultado