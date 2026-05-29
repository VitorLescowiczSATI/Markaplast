from app.models.pedido import Pedido
import httpx


def montar_payload_nfe(pedido: Pedido) -> dict:
    valor_unitario = float(pedido.valor or 0) + float(pedido.valorTampa or 0)
    return {
        "natureza_operacao": "Venda de mercadoria",
        "data_emissao": pedido.data.isoformat(),
        "tipo_documento": 1,
        "finalidade_emissao": 1,
        "cliente": {
            "nome": pedido.cliente,
            "cnpj": pedido.cnpj,
            "cep": pedido.cep,
            "logradouro": pedido.logradouro,
            "numero": pedido.numero,
            "bairro": pedido.bairro,
            "cidade": pedido.cidade,
            "uf": pedido.uf,
        },
        "itens": [
            {
                "numero_item": 1,
                "descricao": pedido.produto,
                "quantidade_comercial": pedido.quantidade,
                "valor_unitario_comercial": valor_unitario,
                "valor_total_bruto": valor_unitario * int(pedido.quantidade or 0),
            }
        ],
        "transporte": {
            "modalidade_frete": pedido.tipoFrete,
            "transportadora": pedido.transporte,
        },
        "observacoes": pedido.observacoes,
        "origem": "pre_nfe_giras",
    }


async def enviar_focus_nfe(base_url: str, token: str, referencia: str, payload: dict) -> dict:
    if not token:
        raise ValueError("Token Focus NFe nao configurado")

    async with httpx.AsyncClient(timeout=httpx.Timeout(20.0), auth=(token, "")) as client:
        response = await client.post(
            f"{base_url.rstrip('/')}/nfe",
            params={"ref": referencia},
            json=payload,
            headers={"accept": "application/json", "content-type": "application/json"},
        )
    if response.status_code not in {200, 201, 202}:
        raise RuntimeError(f"Provedor fiscal retornou HTTP {response.status_code}")
    return response.json()
