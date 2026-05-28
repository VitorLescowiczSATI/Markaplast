import httpx


def normalizar_cep(cep: str) -> str:
    return "".join(char for char in str(cep or "") if char.isdigit())


async def consultar_cep(cep: str) -> dict:
    cep_limpo = normalizar_cep(cep)
    if len(cep_limpo) != 8:
        raise ValueError("CEP deve conter 8 digitos")

    timeout = httpx.Timeout(6.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        viacep = await client.get(f"https://viacep.com.br/ws/{cep_limpo}/json/")
        if viacep.status_code == 200:
            data = viacep.json()
            if not data.get("erro"):
                return {
                    "cep": data.get("cep", cep_limpo),
                    "logradouro": data.get("logradouro", ""),
                    "bairro": data.get("bairro", ""),
                    "cidade": data.get("localidade", ""),
                    "uf": data.get("uf", ""),
                    "ibge": data.get("ibge", ""),
                    "origem": "ViaCEP",
                }

        brasilapi = await client.get(f"https://brasilapi.com.br/api/cep/v2/{cep_limpo}")
        if brasilapi.status_code == 200:
            data = brasilapi.json()
            return {
                "cep": data.get("cep", cep_limpo),
                "logradouro": data.get("street", ""),
                "bairro": data.get("neighborhood", ""),
                "cidade": data.get("city", ""),
                "uf": data.get("state", ""),
                "ibge": data.get("city_ibge", ""),
                "origem": "BrasilAPI",
            }

    raise LookupError("CEP nao encontrado")
