from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import require_profiles
from app.services.cep import consultar_cep

router = APIRouter(prefix="/integracoes", tags=["integracoes"])


@router.get("/cep/{cep}")
async def buscar_cep(cep: str, _usuario=Depends(require_profiles("Comercial", "Clientes"))):
    try:
        return await consultar_cep(cep)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
