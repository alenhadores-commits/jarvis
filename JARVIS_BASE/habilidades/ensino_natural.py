# -*- coding: utf-8 -*-

import re


class EnsinoNatural:

    def interpretar(self, descricao):

        texto = descricao.strip()

        if not texto:
            return None

        gatilho = self._extrair_gatilho(texto)

        if not gatilho:
            return None

        acoes_texto = self._extrair_acoes(texto, gatilho)

        if not acoes_texto:
            return None

        acoes = []

        for trecho in acoes_texto:

            acao = self._interpretar_acao(trecho)

            if acao is not None:
                acoes.append(acao)

        if not acoes:
            return None

        return {
            "gatilho": gatilho,
            "acoes": acoes,
        }

    def _extrair_gatilho(self, texto):

        padroes = [
            r'quando eu disser\s+"([^"]+)"',
            r"quando eu disser\s+'([^']+)'",
            r'quando eu falar\s+"([^"]+)"',
            r"quando eu falar\s+'([^']+)'",
            r'quando eu disser\s+(.+?)(?:,\s*abra|\s+abra|\s+espere|\s+fale|\s+diga|\s+execute|\s+rode)',
            r'quando eu falar\s+(.+?)(?:,\s*abra|\s+abra|\s+espere|\s+fale|\s+diga|\s+execute|\s+rode)',
        ]

        for padrao in padroes:

            match = re.search(
                padrao,
                texto,
                re.IGNORECASE
            )

            if match:

                gatilho = match.group(1).strip()

                gatilho = gatilho.rstrip(
                    " ,."
                )

                if gatilho:
                    return gatilho

        return None

    def _extrair_acoes(self, texto, gatilho):

        pos = texto.lower().find(
            gatilho.lower()
        )

        if pos == -1:
            return []

        restante = texto[
            pos + len(gatilho):
        ]

        restante = restante.lstrip(
            " ,:"
        )

        restante = re.sub(
            r'^(?:e\s+)?(?:depois\s+|então\s+|e\s+depois\s+)',
            '',
            restante,
            flags=re.IGNORECASE
        )

        separador_acoes = (
            r',\s*'
            r'|\s+e\s+(?='
            r'abra\b|abrir\b|acesse\b|acessar\b|'
            r'entre\b|espere\b|esperar\b|aguarde\b|aguardar\b|'
            r'fale\b|falar\b|diga\b|dizer\b|'
            r'execute\b|executar\b|rode\b|rodar\b'
            r')'
            r'|\s+e\s+depois\s+'
            r'|\s+depois\s+'
            r'|\s+então\s+'
        )

        partes = re.split(
            separador_acoes,
            restante,
            flags=re.IGNORECASE
        )

        return [
            parte.strip(" ,.")
            for parte in partes
            if parte.strip(" ,.")
        ]

    def _interpretar_acao(self, trecho):

        texto = trecho.strip()

        # ==========================================================
        # POWERSHELL
        # ==========================================================

        powershell_match = re.search(
            r'(?:execute|executar|rode|rodar)\s+(?:no\s+)?powershell\s+(.+)',
            texto,
            re.IGNORECASE
        )

        if powershell_match:

            valor = powershell_match.group(1).strip()

            return {
                "tipo": "powershell",
                "valor": valor,
            }

        # ==========================================================
        # ABRIR SITE
        # ==========================================================

        url_match = re.search(
            r'(https?://[^\s,]+|www\.[^\s,]+)',
            texto,
            re.IGNORECASE
        )

        if url_match:

            url = url_match.group(1).rstrip(
                ".,!?"
            )

            if not url.lower().startswith(
                ("http://", "https://")
            ):
                url = "https://" + url

            return {
                "tipo": "abrir_site",
                "valor": url,
            }

        sites = {
            "google": "https://www.google.com",
            "youtube": "https://www.youtube.com",
            "chatgpt": "https://chatgpt.com/",
            "facebook": "https://www.facebook.com",
            "instagram": "https://www.instagram.com",
            "whatsapp": "https://web.whatsapp.com",
        }

        abrir_match = re.search(
            r'(?:abra|abrir|acesse|acessar|entre no|entre em)\s+(?:o\s+|a\s+)?(.+)',
            texto,
            re.IGNORECASE
        )

        if abrir_match:

            alvo = abrir_match.group(1).strip().lower()

            alvo = alvo.rstrip(
                ".,!?"
            )

            if alvo in sites:

                return {
                    "tipo": "abrir_site",
                    "valor": sites[alvo],
                }

            # ======================================================
            # ABRIR PROGRAMA
            # ======================================================

            return {
                "tipo": "abrir_programa",
                "valor": alvo,
            }

        # ==========================================================
        # ESPERAR
        # ==========================================================

        espera_match = re.search(
            r'(?:espere|esperar|aguarde|aguardar)\s+(\d+(?:[.,]\d+)?)\s*(?:segundos?|s)?',
            texto,
            re.IGNORECASE
        )

        if espera_match:

            valor = espera_match.group(1).replace(
                ",",
                "."
            )

            return {
                "tipo": "esperar",
                "valor": valor,
            }

        # ==========================================================
        # FALAR / DIZER
        # ==========================================================

        falar_match = re.search(
            r'(?:fale|falar|diga|dizer)\s+(.+)',
            texto,
            re.IGNORECASE
        )

        if falar_match:

            valor = falar_match.group(1).strip()

            valor = valor.strip(
                '"\''
            )

            if valor:

                return {
                    "tipo": "falar",
                    "valor": valor,
                }

        return None
