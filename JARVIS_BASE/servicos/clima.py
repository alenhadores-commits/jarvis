import json
import ssl
import urllib.parse
import urllib.request

import certifi


URL_OPEN_METEO = "https://api.open-meteo.com/v1/forecast"


def consultar_clima(latitude: float, longitude: float):
    parametros = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "apparent_temperature,"
            "relative_humidity_2m,"
            "precipitation,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "timezone": "auto",
    }

    url = (
        URL_OPEN_METEO
        + "?"
        + urllib.parse.urlencode(parametros)
    )

    requisicao = urllib.request.Request(
        url,
        headers={
            "User-Agent": "JARVIS/1.0"
        },
    )

    contexto_ssl = ssl.create_default_context(
        cafile=certifi.where()
    )

    with urllib.request.urlopen(
        requisicao,
        context=contexto_ssl,
        timeout=15,
    ) as resposta:
        dados = json.loads(
            resposta.read().decode("utf-8")
        )

    atual = dados.get("current", {})

    return {
        "temperatura": atual.get(
            "temperature_2m"
        ),
        "sensacao": atual.get(
            "apparent_temperature"
        ),
        "umidade": atual.get(
            "relative_humidity_2m"
        ),
        "precipitacao": atual.get(
            "precipitation"
        ),
        "codigo_tempo": atual.get(
            "weather_code"
        ),
        "vento_kmh": atual.get(
            "wind_speed_10m"
        ),
        "horario": atual.get("time"),
        "timezone": dados.get("timezone"),
    }


def clima_por_localizacao(localizacao: dict):
    return consultar_clima(
        localizacao["latitude"],
        localizacao["longitude"],
    )


if __name__ == "__main__":
    from localizacao import obter_localizacao

    print("JARVIS: Detectando localizacao...")
    print("")

    localizacao = obter_localizacao()

    print(
        f"Latitude : {localizacao['latitude']}"
    )
    print(
        f"Longitude: {localizacao['longitude']}"
    )

    print("")
    print("JARVIS: Consultando Open-Meteo...")

    clima = clima_por_localizacao(
        localizacao
    )

    print("")
    print("==============================================")
    print(" JARVIS - CLIMA ATUAL")
    print("==============================================")
    print("")
    print(
        f"Temperatura : {clima['temperatura']} °C"
    )
    print(
        f"Sensacao    : {clima['sensacao']} °C"
    )
    print(
        f"Umidade     : {clima['umidade']} %"
    )
    print(
        f"Precipitacao: {clima['precipitacao']} mm"
    )
    print(
        f"Vento       : {clima['vento_kmh']} km/h"
    )
    print(
        f"Horario     : {clima['horario']}"
    )
    print(
        f"Timezone    : {clima['timezone']}"
    )
