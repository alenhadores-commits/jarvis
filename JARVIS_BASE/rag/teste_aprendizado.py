from rag import RAGManager


rag = RAGManager()

resultado = rag.aprender(
    objetivo="Criar executor automático",
    acao="Implementar executor e executar testes",
    resultado="Primeira tentativa falhou e a segunda funcionou",
    sucesso=True,
    erros=[
        "AttributeError no método de execução"
    ],
    solucao="Corrigir a assinatura do método e executar novamente"
)

print()
print("=" * 60)
print(" APRENDIZAGEM RAG")
print("=" * 60)
print()
print(resultado)
print()
print("Busca da experiência:")
print()

busca = rag.buscar(
    "Já tivemos problema de AttributeError no executor?"
)

print(busca["contexto"])
