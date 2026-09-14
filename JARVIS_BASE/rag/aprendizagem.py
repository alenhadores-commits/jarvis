from datetime import datetime
import hashlib


class AprendizagemRAG:

    def __init__(self, banco, indexador):
        self.banco = banco
        self.indexador = indexador

    def _origem(self, prefixo, texto):
        agora = datetime.now().isoformat()

        bruto = (
            f"{prefixo}|"
            f"{agora}|"
            f"{texto}"
        )

        identificador = hashlib.sha256(
            bruto.encode("utf-8")
        ).hexdigest()[:20]

        return f"{prefixo}_{identificador}"

    def registrar_experiencia(
        self,
        objetivo,
        acao,
        resultado,
        sucesso,
        erros=None,
        solucao=None
    ):

        erros = erros or []

        data = datetime.now().isoformat()

        texto = f"""
EXPERIÊNCIA DO JARVIS

OBJETIVO:
{objetivo}

AÇÃO:
{acao}

RESULTADO:
{resultado}

SUCESSO:
{sucesso}

ERROS:
{erros}

SOLUÇÃO:
{solucao or "Não registrada."}

DATA:
{data}
""".strip()

        metadata = {
            "objetivo": str(objetivo)[:500],
            "sucesso": str(bool(sucesso)),
            "data": data,
            "origem_tipo": "experiencia",
        }

        origem = self._origem(
            "experiencia_jarvis",
            objetivo
        )

        quantidade = self.indexador.indexar_texto(
            texto=texto,
            colecao="experiencias",
            origem=origem,
            metadata=metadata
        )

        if erros:

            texto_erro = f"""
ERRO DETECTADO PELO JARVIS

OBJETIVO:
{objetivo}

ERROS:
{erros}

SOLUÇÃO:
{solucao or "Ainda não resolvido."}

RESULTADO:
{resultado}

DATA:
{data}
""".strip()

            origem_erro = self._origem(
                "erro_jarvis",
                str(erros)
            )

            self.indexador.indexar_texto(
                texto=texto_erro,
                colecao="erros",
                origem=origem_erro,
                metadata={
                    **metadata,
                    "origem_tipo": "erro",
                }
            )

        return {
            "experiencia_salva": True,
            "chunks": quantidade,
            "data": data,
        }

    def registrar_procedimento(
        self,
        nome,
        procedimento,
        origem="aprendizado_jarvis"
    ):

        texto = (
            f"PROCEDIMENTO: {nome}\n\n"
            f"{procedimento}"
        )

        quantidade = self.indexador.indexar_texto(
            texto=texto,
            colecao="procedimentos",
            origem=self._origem(
                origem,
                nome
            ),
            metadata={
                "nome": nome,
                "tipo": "procedimento",
            }
        )

        return quantidade
