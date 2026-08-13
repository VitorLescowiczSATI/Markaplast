from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.nota_fiscal import NotaFiscalDraft
from app.models.pedido import Pedido
from app.models.pedido_historico import PedidoHistorico
from app.services.estoque import estornar_baixa_do_pedido, itens_do_pedido
from app.services.historico import registrar_historico
import httpx


# Ao excluir a nota o pedido volta para a fila de onde saiu na emissao; "Prontos" e o destino padrao.
STATUS_APOS_ESTORNO = "Prontos"
STATUS_RETORNO_ESTORNO = {"Prontos", "Pronto para retirada", "Pronto para o envio"}


def montar_payload_nfe(pedido: Pedido) -> dict:
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
                "numero_item": numero,
                "descricao": " - ".join(parte for parte in [item.produto, item.cor, item.tampa] if parte),
                "quantidade_comercial": item.quantidade,
                "valor_unitario_comercial": float(item.valor or 0) + float(item.valorTampa or 0),
                "valor_total_bruto": (float(item.valor or 0) + float(item.valorTampa or 0))
                * int(item.quantidade or 0),
            }
            for numero, item in enumerate(itens_do_pedido(pedido), start=1)
        ],
        "transporte": {
            "modalidade_frete": pedido.tipoFrete,
            "transportadora": pedido.transporte,
        },
        "observacoes": pedido.observacoes,
        "origem": "pre_nfe_giras",
    }


def excluir_nota_do_pedido(db: Session, pedido: Pedido | None, origem: str) -> NotaFiscalDraft | None:
    """Apaga o rascunho fiscal do pedido (se existir) e devolve o pedido ao fluxo pre-emissao."""
    nota = None
    if pedido:
        nota = db.scalars(select(NotaFiscalDraft).where(NotaFiscalDraft.pedidoId == pedido.id)).first()
        if nota:
            db.delete(nota)
    estornar_emissao_do_pedido(db, pedido, origem, nota.referencia if nota else "")
    return nota


def reverter_baixa_da_emissao(db: Session, pedido: Pedido) -> None:
    """Desfaz a baixa de estoque feita na emissao quando o pedido deixa "Nota emitida"."""
    if not pedido.dataEmissao:
        return
    pedido.dataEmissao = None
    estornar_baixa_do_pedido(db, pedido)


def status_antes_da_emissao(db: Session, pedido: Pedido) -> str:
    """Le no historico de onde o pedido saiu quando virou "Nota emitida"."""
    registro = db.scalars(
        select(PedidoHistorico)
        .where(
            PedidoHistorico.pedidoId == pedido.id,
            PedidoHistorico.tipo == "Status",
            PedidoHistorico.paraValor == "Nota emitida",
        )
        .order_by(PedidoHistorico.id.desc())
    ).first()
    anterior = (registro.deValor if registro else "") or ""
    return anterior if anterior in STATUS_RETORNO_ESTORNO else STATUS_APOS_ESTORNO


def estornar_emissao_do_pedido(db: Session, pedido: Pedido | None, origem: str, referencia: str = "") -> None:
    """Volta o pedido de "Nota emitida" para a fila anterior e desfaz a baixa de estoque da emissao."""
    if not pedido or pedido.status != "Nota emitida":
        return
    anterior = pedido.status
    pedido.status = status_antes_da_emissao(db, pedido)
    reverter_baixa_da_emissao(db, pedido)
    detalhe = f"Nota {referencia} excluida" if referencia else "Nota excluida"
    registrar_historico(
        db,
        pedido.id,
        "Status",
        anterior,
        pedido.status,
        observacao=f"{detalhe} em {origem}. Estoque e reserva restaurados.",
    )


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
