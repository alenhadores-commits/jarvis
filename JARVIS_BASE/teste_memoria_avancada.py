# -*- coding: utf-8 -*-

from memoria_retriever import MemoriaRetriever


def main():
    retriever = MemoriaRetriever()

    print("=" * 70)
    print("JARVIS - TESTE MEMORIA E5 + CHROMADB")
    print("=" * 70)

    print()
    print("STATUS")
    print(retriever.memoria.status())

    print()
    print("SINCRONIZANDO")
    print(retriever.memoria.sincronizar_completa())

    consultas = [
        "qual é meu nome?",
        "qual é minha profissão?",
        "qual é minha comida favorita?",
        "qual é meu animal favorito?",
        "qual é meu principal projeto?",
    ]

    for consulta in consultas:
        print()
        print("-" * 70)
        print("CONSULTA:", consulta)
        print("TIPO:", retriever.inferir_tipo(consulta))

        resultados = retriever.buscar(consulta)

        if not resultados:
            print("NENHUMA MEMORIA RELEVANTE")
            continue

        primeiro = resultados[0]

        print("MELHOR RESULTADO:")
        print("TIPO:", primeiro.get("tipo"))
        print("CONTEUDO:", primeiro.get("conteudo"))
        print("SIMILARIDADE:", primeiro.get("similaridade"))
        print("CONCEITO:", primeiro.get("score_conceito"))
        print("TIPO SCORE:", primeiro.get("score_tipo"))
        print("IMPORTANCIA:", primeiro.get("score_importancia"))
        print("SCORE FINAL:", primeiro.get("score_final"))


if __name__ == "__main__":
    main()
