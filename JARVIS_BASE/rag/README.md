# JARVIS RAG LOCAL

## Objetivo

Criar uma memória semântica local para o JARVIS.

## Componentes

- ChromaDB: armazenamento vetorial persistente.
- Embeddings locais: representação semântica.
- Chunker: divisão de documentos.
- Indexador: entrada de conhecimento.
- Recuperador: busca semântica.
- Router: escolhe coleções.
- Contexto: prepara informação para a IA.
- Aprendizagem: transforma experiências em memória.

## Coleções

- jarvis_memorias
- jarvis_experiencias
- jarvis_conhecimento
- jarvis_codigo
- jarvis_documentacao
- jarvis_erros
- jarvis_procedimentos
- jarvis_projetos
- jarvis_conversas
- jarvis_aprendizado

## Regra arquitetural

O RAG não substitui o cérebro existente.

Ele fornece contexto para:

JARVIS CORE
    ↓
RAG
    ↓
IA LOCAL
    ↓
PLANEJAMENTO
    ↓
EXECUÇÃO
    ↓
TESTE
    ↓
AVALIAÇÃO
    ↓
APRENDIZAGEM
    ↓
RAG

## Regra de segurança

Nesta primeira fase o RAG é independente do jarvis.py.

A integração com o núcleo principal somente será feita
depois que os testes isolados forem aprovados.
