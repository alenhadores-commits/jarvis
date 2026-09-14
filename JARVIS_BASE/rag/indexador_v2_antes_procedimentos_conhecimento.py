# -*- coding: utf-8 -*-

import hashlib
import json
from datetime import datetime
from pathlib import Path

import chromadb

from .config import DADOS
from .embeddings import EmbeddingsLocais
from .chunker import Chunker


class IndexadorV2:
    """
    Indexador incremental da RAG V2.1.

    Melhorias:
    - embedding inicializado uma única vez
    - processamento em lotes
    - manifest para evitar reindexação
    - hash SHA256 por arquivo
    - separação código/documentação
    - progresso visível
    - arquivos removidos são eliminados do índice
    """

    EXTENSOES_CODIGO = {
        ".py", ".js", ".ts", ".tsx", ".jsx",
        ".yaml", ".yml", ".toml",
        ".ini", ".cfg", ".bat", ".ps1",
        ".html", ".css", ".sql", ".sh"
    }

    EXTENSOES_DOCUMENTACAO = {
        ".md", ".txt"
    }

    IGNORAR = {
        ".git",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "node_modules",
        ".idea",
        ".vscode",
        "backup",
        "backups",
        "dados"
    }

    def __init__(self, raiz_projeto=None):
        self.raiz = Path(raiz_projeto or Path.cwd()).resolve()
        self.diretorio_dados = Path(DADOS)
        self.diretorio_dados.mkdir(parents=True, exist_ok=True)

        self.manifest_path = self.diretorio_dados / "rag_manifest.json"

        self.client = chromadb.PersistentClient(
            path=str(self.diretorio_dados / "chromadb")
        )

        self.embedding = EmbeddingsLocais()
        self.chunker = Chunker()

        self.colecao_codigo = self.client.get_or_create_collection(
            name="jarvis_codigo",
            embedding_function=self.embedding
        )

        self.colecao_memorias = self.client.get_or_create_collection(
            name="jarvis_memorias",
            embedding_function=self.embedding
        )

        self.colecao_conversas = self.client.get_or_create_collection(
            name="jarvis_conversas",
            embedding_function=self.embedding
        )

        self.colecao_documentacao = self.client.get_or_create_collection(
            name="jarvis_documentacao",
            embedding_function=self.embedding
        )

        self.manifest = self._carregar_manifest()

    # ---------------------------------------------------------
    # MANIFEST
    # ---------------------------------------------------------

    def _carregar_manifest(self):
        if not self.manifest_path.exists():
            return {}

        try:
            with open(self.manifest_path, "r", encoding="utf-8") as arquivo:
                dados = json.load(arquivo)

            return dados if isinstance(dados, dict) else {}

        except Exception:
            return {}

    def _salvar_manifest(self):
        temporario = self.manifest_path.with_suffix(".tmp")

        with open(temporario, "w", encoding="utf-8") as arquivo:
            json.dump(
                self.manifest,
                arquivo,
                ensure_ascii=False,
                indent=2
            )

        temporario.replace(self.manifest_path)

    # ---------------------------------------------------------
    # UTILITÁRIOS
    # ---------------------------------------------------------

    def _ignorar(self, caminho):
        try:
            relativo = caminho.resolve().relative_to(self.raiz)
        except ValueError:
            return True

        partes = set(relativo.parts)

        if partes.intersection(self.IGNORAR):
            return True

        for parte in relativo.parts:
            parte_lower = parte.lower()
            if (
                "backup" in parte_lower
                or parte_lower.startswith(("browser_profile", "chrome_jarvis", "dados_chrome", "dados_chromium"))
            ):
                return True

        return False

    def _hash_arquivo(self, caminho):
        sha = hashlib.sha256()

        with open(caminho, "rb") as arquivo:
            while True:
                bloco = arquivo.read(1024 * 1024)

                if not bloco:
                    break

                sha.update(bloco)

        return sha.hexdigest()

    def _tipo_arquivo(self, caminho):
        nome = caminho.name.lower()
        extensao = caminho.suffix.lower()

        # Histórico de conversas
        if nome == "historico_conversas.json":
            return "conversas"

        # Memórias permanentes
        if nome == "memorias_permanentes.json":
            return "memorias"

        # Documentação
        if extensao in self.EXTENSOES_DOCUMENTACAO:
            return "documentacao"

        # Código
        if extensao in self.EXTENSOES_CODIGO:
            return "codigo"

        return None

    def _colecao(self, tipo):
        if tipo == "codigo":
            return self.colecao_codigo

        if tipo == "memorias":
            return self.colecao_memorias

        if tipo == "conversas":
            return self.colecao_conversas

        return self.colecao_documentacao

    def _ler_arquivo(self, caminho):
        try:
            return caminho.read_text(
                encoding="utf-8",
                errors="ignore"
            )
        except Exception:
            return ""

    def _id_chunk(self, caminho, indice, conteudo):
        base = (
            f"{caminho}|"
            f"{indice}|"
            f"{conteudo}"
        )

        return hashlib.sha256(
            base.encode("utf-8")
        ).hexdigest()

    # ---------------------------------------------------------
    # INDEXAÇÃO
    # ---------------------------------------------------------

    def _indexar_lote(
        self,
        collection,
        ids,
        documentos,
        metadados
    ):
        if not ids:
            return 0

        collection.upsert(
            ids=ids,
            documents=documentos,
            metadatas=metadados
        )

        return len(ids)

    def _indexar_arquivo(self, caminho, collection, hash_atual):

        texto = self._ler_arquivo(caminho)

        if not texto.strip():
            return 0

        chunks = self.chunker.dividir(texto)

        if not chunks:
            return 0

        agora = datetime.now().isoformat()

        total = 0
        tamanho_lote = 8

        for inicio in range(0, len(chunks), tamanho_lote):

            lote = chunks[inicio:inicio + tamanho_lote]

            ids = []
            documentos = []
            metadados = []

            for deslocamento, chunk in enumerate(lote):

                indice = inicio + deslocamento

                ids.append(
                    self._id_chunk(
                        caminho,
                        indice,
                        chunk
                    )
                )

                documentos.append(chunk)

                metadados.append({
                    "arquivo": str(caminho),
                    "nome": caminho.name,
                    "extensao": caminho.suffix.lower(),
                    "colecao_tipo": self._tipo_arquivo(caminho),
                    "hash_arquivo": hash_atual,
                    "indice_chunk": indice,
                    "indexado_em": agora
                })

            total += self._indexar_lote(
                collection,
                ids,
                documentos,
                metadados
            )

        return total

    def indexar_arquivo(self, caminho, forcar=False):

        caminho = Path(caminho).resolve()

        if self._ignorar(caminho):
            return {
                "arquivo": str(caminho),
                "status": "ignorado",
                "chunks": 0
            }

        tipo = self._tipo_arquivo(caminho)

        if tipo is None:
            return {
                "arquivo": str(caminho),
                "status": "ignorado",
                "chunks": 0
            }

        hash_atual = self._hash_arquivo(caminho)
        chave = str(caminho)

        anterior = self.manifest.get(chave)

        if (
            not forcar
            and anterior
            and anterior.get("hash") == hash_atual
            and anterior.get("tipo") == tipo
        ):
            return {
                "arquivo": str(caminho),
                "status": "inalterado",
                "chunks": anterior.get("chunks", 0)
            }

        collection = self._colecao(tipo)

        if anterior:
            try:
                collection.delete(
                    where={
                        "arquivo": str(caminho)
                    }
                )
            except Exception:
                pass

        quantidade = self._indexar_arquivo(
            caminho,
            collection,
            hash_atual
        )

        self.manifest[chave] = {
            "hash": hash_atual,
            "tipo": tipo,
            "chunks": quantidade,
            "atualizado_em": datetime.now().isoformat()
        }

        self._salvar_manifest()

        return {
            "arquivo": str(caminho),
            "status": "indexado",
            "chunks": quantidade
        }

    # ---------------------------------------------------------
    # PROJETO COMPLETO
    # ---------------------------------------------------------

    def _arquivos_projeto(self):

        arquivos = []

        for caminho in self.raiz.rglob("*"):

            if not caminho.is_file():
                continue

            if self._ignorar(caminho):
                continue

            if self._tipo_arquivo(caminho) is None:
                continue

            arquivos.append(caminho)

        return sorted(
            arquivos,
            key=lambda x: str(x).lower()
        )

    def indexar_projeto(self, forcar=False):

        arquivos = self._arquivos_projeto()

        resultado = {
            "total_arquivos": len(arquivos),
            "indexados": 0,
            "inalterados": 0,
            "ignorados": 0,
            "erros": 0,
            "chunks": 0
        }

        print()
        print("=" * 70)
        print(" JARVIS RAG V2.1 — INDEXAÇÃO DO PROJETO")
        print("=" * 70)
        print(f" Arquivos encontrados: {len(arquivos)}")
        print()

        for numero, caminho in enumerate(arquivos, 1):

            relativo = caminho.relative_to(self.raiz)

            print(
                f"[{numero:03d}/{len(arquivos):03d}] "
                f"{relativo}",
                flush=True
            )

            try:

                item = self.indexar_arquivo(
                    caminho,
                    forcar=forcar
                )

                status = item["status"]
                chunks = item["chunks"]

                if status == "indexado":
                    resultado["indexados"] += 1
                    resultado["chunks"] += chunks

                    print(
                        f"      -> INDEXADO ({chunks} chunks)",
                        flush=True
                    )

                elif status == "inalterado":
                    resultado["inalterados"] += 1

                    print(
                        f"      -> INALTERADO ({chunks} chunks)",
                        flush=True
                    )

                else:
                    resultado["ignorados"] += 1

            except KeyboardInterrupt:
                self._salvar_manifest()

                print()
                print("INDEXAÇÃO INTERROMPIDA PELO USUÁRIO.")
                print("Manifesto salvo. Pode continuar depois.")

                raise

            except Exception as erro:

                resultado["erros"] += 1

                print(
                    f"      -> ERRO: {erro}",
                    flush=True
                )

        self._remover_arquivos_excluidos(arquivos)
        self._salvar_manifest()

        print()
        print("=" * 70)
        print(" RESUMO")
        print("=" * 70)
        print(f" Total:       {resultado['total_arquivos']}")
        print(f" Indexados:   {resultado['indexados']}")
        print(f" Inalterados: {resultado['inalterados']}")
        print(f" Ignorados:   {resultado['ignorados']}")
        print(f" Erros:       {resultado['erros']}")
        print(f" Chunks:      {resultado['chunks']}")
        print("=" * 70)

        return resultado

    # ---------------------------------------------------------
    # LIMPEZA DE ARQUIVOS REMOVIDOS
    # ---------------------------------------------------------

    def _remover_arquivos_excluidos(self, arquivos_atuais):

        atuais = {
            str(Path(x).resolve())
            for x in arquivos_atuais
        }

        removidos = []

        for caminho in list(self.manifest.keys()):

            if caminho in atuais:
                continue

            tipo = self.manifest[caminho].get("tipo")

            if tipo not in {
                "codigo",
                "documentacao"
            }:
                continue

            try:

                collection = self._colecao(tipo)

                collection.delete(
                    where={
                        "arquivo": caminho
                    }
                )

                removidos.append(caminho)

            except Exception:
                pass

        for caminho in removidos:
            self.manifest.pop(caminho, None)

    # ---------------------------------------------------------
    # ESTATÍSTICAS
    # ---------------------------------------------------------

    def estatisticas(self):

        return {
            "codigo": self.colecao_codigo.count(),
            "memorias": self.colecao_memorias.count(),
            "conversas": self.colecao_conversas.count(),
            "documentacao": self.colecao_documentacao.count(),
            "manifesto": len(self.manifest)
        }






