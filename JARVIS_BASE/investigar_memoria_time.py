from pathlib import Path
import inspect
import json
import traceback

from memoria_retriever import MemoriaRetriever

print()
print("=" * 90)
print("J.A.R.V.I.S — INVESTIGAÇÃO DA FALHA DE MEMÓRIA")
print("=" * 90)

consulta = "Qual é o meu time?"

print()
print("CONSULTA:")
print(consulta)

try:
    r = MemoriaRetriever()

    print()
    print("=" * 90)
    print("1. TIPO INFERIDO")
    print("=" * 90)

    tipo = r.inferir_tipo(consulta)

    print("TIPO:", repr(tipo))

    print()
    print("=" * 90)
    print("2. MÉTODOS DISPONÍVEIS NO RETRIEVER")
    print("=" * 90)

    for nome in dir(r):
        if nome.startswith("_"):
            continue

        try:
            atributo = getattr(r, nome)

            if callable(atributo):
                print(nome, inspect.signature(atributo))
        except Exception:
            pass

    print()
    print("=" * 90)
    print("3. BUSCA BRUTA DO RETRIEVER")
    print("=" * 90)

    resultados = r.buscar(consulta)

    print("TIPO DO RETORNO:", type(resultados).__name__)
    print("QUANTIDADE:", len(resultados) if hasattr(resultados, "__len__") else "?")

    print()

    if isinstance(resultados, list):

        for i, item in enumerate(resultados, 1):

            print("-" * 90)
            print(f"RESULTADO {i}")

            if isinstance(item, dict):

                for chave, valor in item.items():
                    print(f"{chave}: {valor}")

            else:
                print(repr(item))

    else:
        print(repr(resultados))

    print()
    print("=" * 90)
    print("4. CONTEXTO FINAL GERADO")
    print("=" * 90)

    contexto = r.contexto(consulta)

    print(contexto)

    print()
    print("=" * 90)
    print("5. INVESTIGAÇÃO DAS MEMÓRIAS COM PALMEIRAS")
    print("=" * 90)

    memoria = getattr(r, "memoria", None)

    if memoria is None:
        memoria = getattr(r, "memoria_local", None)

    if memoria is None:
        print("Não foi possível localizar o objeto de memória dentro do Retriever.")

    else:

        print("OBJETO MEMÓRIA:", type(memoria).__name__)

        print()
        print("MÉTODOS:")

        for nome in dir(memoria):
            if nome.startswith("_"):
                continue

            try:
                atributo = getattr(memoria, nome)

                if callable(atributo):
                    try:
                        print(nome, inspect.signature(atributo))
                    except Exception:
                        print(nome, "(assinatura indisponível)")

            except Exception:
                pass

        print()
        print("TENTANDO LOCALIZAR BANCO DE MEMÓRIA...")

        bancos = [
            getattr(memoria, "memorias", None),
            getattr(memoria, "dados", None),
            getattr(memoria, "memoria", None),
            getattr(memoria, "itens", None),
        ]

        encontrou = False

        for banco in bancos:

            if banco is None:
                continue

            if isinstance(banco, list):

                encontrou = True

                for item in banco:

                    texto = json.dumps(
                        item,
                        ensure_ascii=False
                    ).lower()

                    if "palmeira" in texto or "time" in texto or "torço" in texto or "torco" in texto:

                        print()
                        print("MEMÓRIA RELACIONADA:")
                        print(
                            json.dumps(
                                item,
                                ensure_ascii=False,
                                indent=2
                            )
                        )

        if not encontrou:
            print("Nenhuma lista interna direta foi encontrada.")

    print()
    print("=" * 90)
    print("6. ANÁLISE DA IMPLEMENTAÇÃO DO RETRIEVER")
    print("=" * 90)

    arquivo = Path("memoria_retriever.py")

    if arquivo.exists():

        texto = arquivo.read_text(
            encoding="utf-8-sig"
        )

        linhas = texto.splitlines()

        palavras = [
            "PESO_SEMANTICO",
            "PESO_CONCEITO",
            "PESO_TIPO",
            "PESO_IMPORTANCIA",
            "inferir_tipo",
            "def buscar",
            "score_final",
            "similaridade",
            "MAPA_TIPO",
            "OUTRO",
            "NOME",
            "time",
            "palmeiras",
            "futebol",
            "torço",
            "torco",
        ]

        for palavra in palavras:

            print()
            print(f">>> {palavra}")

            encontrados = 0

            for numero, linha in enumerate(linhas, 1):

                if palavra.lower() in linha.lower():

                    inicio = max(1, numero - 3)
                    fim = min(len(linhas), numero + 5)

                    for n in range(inicio, fim + 1):
                        print(
                            f"{n:04d}: {linhas[n-1]}"
                        )

                    print("-" * 50)

                    encontrados += 1

                    if encontrados >= 3:
                        break

    print()
    print("=" * 90)
    print("7. RESUMO AUTOMÁTICO")
    print("=" * 90)

    print("Consulta:", consulta)
    print("Tipo inferido:", tipo)
    print("Contexto contém PALMEIRAS:",
          "palmeiras" in str(contexto).lower())
    print("Contexto contém ALEX:",
          "alex" in str(contexto).lower())

    if str(tipo).upper() == "NOME":
        print()
        print("CAUSA PROVÁVEL:")
        print(
            "A classificação temática está errada. "
            "A pergunta sobre TIME está sendo tratada como NOME."
        )

    if "palmeiras" not in str(contexto).lower():
        print()
        print("CAUSA PROVÁVEL:")
        print(
            "Mesmo que a memória exista, o ranking híbrido não está "
            "colocando a memória do time entre os resultados relevantes."
        )

    print()
    print("=" * 90)
    print("FIM DA INVESTIGAÇÃO")
    print("=" * 90)

except Exception as erro:

    print()
    print("=" * 90)
    print("ERRO DURANTE A INVESTIGAÇÃO")
    print("=" * 90)
    print(
        f"{type(erro).__name__}: {erro}"
    )
    print()
    print(traceback.format_exc())
