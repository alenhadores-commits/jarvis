import asyncio


async def _obter_localizacao_async():
    from winrt.windows.devices.geolocation import (
        Geolocator,
        GeolocationAccessStatus,
        PositionAccuracy,
    )

    acesso = await Geolocator.request_access_async()

    if acesso != GeolocationAccessStatus.ALLOWED:
        raise RuntimeError(
            f"Acesso a localizacao do Windows nao permitido: {acesso}"
        )

    geolocator = Geolocator()

    try:
        geolocator.desired_accuracy = PositionAccuracy.DEFAULT
    except Exception:
        pass

    try:
        geolocator.allow_fallback_to_consentless_positions()
    except Exception:
        pass

    posicao = await geolocator.get_geoposition_async()

    coordenada = posicao.coordinate

    resultado = {
        "latitude": float(coordenada.latitude),
        "longitude": float(coordenada.longitude),
        "precisao_metros": None,
        "fonte": "desconhecida",
    }

    try:
        resultado["precisao_metros"] = float(
            coordenada.accuracy
        )
    except Exception:
        pass

    try:
        resultado["fonte"] = str(
            coordenada.position_source
        )
    except Exception:
        pass

    return resultado


def obter_localizacao():
    try:
        asyncio.get_running_loop()
        dentro_asyncio = True
    except RuntimeError:
        dentro_asyncio = False

    if not dentro_asyncio:
        return asyncio.run(
            _obter_localizacao_async()
        )

    import threading

    resultado = {}
    erro = {}

    def executar():
        try:
            resultado["valor"] = asyncio.run(
                _obter_localizacao_async()
            )
        except Exception as exc:
            erro["valor"] = exc

    thread = threading.Thread(
        target=executar,
        name="JARVIS-Localizacao",
        daemon=True,
    )

    thread.start()
    thread.join()

    if "valor" in erro:
        raise erro["valor"]

    return resultado["valor"]


if __name__ == "__main__":
    print("JARVIS: Detectando localizacao do Windows...")
    print("")

    try:
        localizacao = obter_localizacao()

        print("==============================================")
        print(" LOCALIZACAO DETECTADA")
        print("==============================================")
        print("")
        print(
            f"Latitude : {localizacao['latitude']}"
        )
        print(
            f"Longitude: {localizacao['longitude']}"
        )
        print(
            f"Fonte    : {localizacao['fonte']}"
        )
        print(
            f"Precisao : {localizacao['precisao_metros']} m"
        )

    except Exception as erro:
        print("")
        print("JARVIS: FALHA AO OBTER LOCALIZACAO")
        print(f"ERRO: {erro}")
        raise