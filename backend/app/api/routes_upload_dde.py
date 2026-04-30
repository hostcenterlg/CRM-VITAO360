"""
CRM VITAO360 — routes_upload_dde.py
======================================
Endpoint POST /api/upload/analise-critica — upload de arquivos XLSX DDE/AC.

Recebe arquivo via multipart/form-data, detecta o tipo, despacha para o
parser correto e retorna o resultado do processamento.

Tipos suportados:
  ZSDFAT     — ZSDFAT_<cliente>.xlsx -> cliente_dre_periodo
  VERBAS     — Verbas xxxx.xlsx      -> cliente_verba_anual (tipo=EFETIVADA)
  FRETE      — Frete por Cliente.xlsx -> cliente_frete_mensal
  CONTRATOS  — Controle Contratos.xlsx -> cliente_verba_anual (tipo=CONTRATO)
  PROMOTORES — Despesas Clientes V2.xlsx -> cliente_promotor_mensal

Acesso restrito: gerente ou admin (require_gerente_or_admin).
Onward hook (Onda 3 — OSCAR): recalc_dde será triggado aqui quando implementado.

REGRAS:
  R5  — CNPJ normalizado pelos parsers
  R8  — classificacao='REAL' por padrão (upload CFO)
  R12 — nivel L2: informa resultado ao chamador via JSON
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.api.deps import get_db, require_gerente_or_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/upload", tags=["DDE Upload"])

# Tipos aceitos e seus parsers (lazy import para evitar circular + custo só quando necessário)
_TIPOS_VALIDOS = frozenset({"ZSDFAT", "VERBAS", "FRETE", "CONTRATOS", "PROMOTORES"})


def _get_parser(tipo: str):
    """
    Retorna instância do parser correspondente ao tipo.

    Import lazy para evitar custo de inicialização no startup.
    """
    if tipo == "ZSDFAT":
        from scripts.parsers.parser_zsdfat import ParserZSDFAT
        return ParserZSDFAT()
    if tipo == "VERBAS":
        from scripts.parsers.parser_verbas import ParserVerbas
        return ParserVerbas()
    if tipo == "FRETE":
        from scripts.parsers.parser_frete import ParserFrete
        return ParserFrete()
    if tipo == "CONTRATOS":
        from scripts.parsers.parser_contratos import ParserContratos
        return ParserContratos()
    if tipo == "PROMOTORES":
        from scripts.parsers.parser_promotores import ParserPromotores
        return ParserPromotores()
    raise ValueError(f"Tipo desconhecido: {tipo!r}")


@router.post(
    "/analise-critica",
    summary="Upload de arquivo DDE/AC para processamento",
    description=(
        "Recebe um arquivo XLSX de análise crítica (DDE), detecta o tipo e "
        "persiste os dados nas tabelas correspondentes.\n\n"
        "**Tipos aceitos**: ZSDFAT, VERBAS, FRETE, CONTRATOS, PROMOTORES\n\n"
        "**Acesso**: gerente ou admin"
    ),
    status_code=status.HTTP_200_OK,
)
async def upload_analise_critica(
    tipo: str = Form(
        ...,
        description="Tipo do arquivo: ZSDFAT|VERBAS|FRETE|CONTRATOS|PROMOTORES",
    ),
    file: UploadFile = File(..., description="Arquivo XLSX para processamento"),
    user: Any = Depends(require_gerente_or_admin),
    db: Session = Depends(get_db),
) -> dict:
    """
    Processa upload de arquivo DDE/AC.

    Fluxo:
      1. Valida parâmetros (tipo, extensão do arquivo)
      2. Salva arquivo em tmpfile
      3. Seleciona parser baseado em `tipo`
      4. Executa parser.run(tmpfile, db)
      5. Retorna resultado com status, registros, warnings, errors, fonte
      6. [ONDA 3 — OSCAR] Hook de recalc DDE (placeholder)

    Returns:
      {
        "status": "OK" | "ERRO",
        "tipo": str,
        "arquivo": str,
        "registros": int,
        "warnings": list[str],
        "errors": list[str],
        "fonte": str
      }
    """
    # --- 1. Validar tipo
    tipo_upper = tipo.strip().upper()
    if tipo_upper not in _TIPOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Tipo inválido: {tipo!r}. "
                f"Aceitos: {sorted(_TIPOS_VALIDOS)}"
            ),
        )

    # --- 2. Validar arquivo
    filename = file.filename or "upload.xlsx"
    suffix = Path(filename).suffix.lower()
    if suffix not in {".xlsx", ".xlsm"}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Extensão inválida: {suffix!r}. Envie um arquivo .xlsx",
        )

    logger.info(
        "[UploadDDE] Recebido: tipo=%s arquivo=%s usuario=%s",
        tipo_upper,
        filename,
        getattr(user, "nome", "?"),
    )

    # --- 3. Salvar em arquivo temporário
    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix, delete=False, prefix=f"dde_{tipo_upper}_"
        ) as tmp:
            content = await file.read()
            if not content:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Arquivo enviado está vazio.",
                )
            tmp.write(content)
            tmp_path = tmp.name

        # --- 4. Selecionar e executar parser
        parser = _get_parser(tipo_upper)
        result = parser.run(tmp_path, db)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("[UploadDDE] Erro inesperado processando %s: %s", filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao processar arquivo: {exc}",
        ) from exc
    finally:
        # Garantir remoção do tmpfile mesmo em caso de exceção
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError as e:
                logger.warning("[UploadDDE] Falha ao remover tmpfile %s: %s", tmp_path, e)

    # --- 5. Log do resultado
    logger.info(
        "[UploadDDE] Resultado: tipo=%s status=%s registros=%d warnings=%d",
        tipo_upper,
        result.get("status"),
        result.get("registros", 0),
        len(result.get("warnings", [])),
    )

    # --- 6. [ONDA 3 — OSCAR] Placeholder hook de recalc DDE
    # Quando OSCAR implementar dde_engine.py, chamar aqui:
    #   if result.get("status") == "OK" and result.get("registros", 0) > 0:
    #       from backend.app.services.dde_engine import trigger_recalc_dde
    #       cnpjs_afetados = _extract_cnpjs_from_result(result)
    #       trigger_recalc_dde(cnpjs_afetados, db)

    return {
        "status": result.get("status", "ERRO"),
        "tipo": tipo_upper,
        "arquivo": filename,
        "registros": result.get("registros", 0),
        "warnings": result.get("warnings", []),
        "errors": result.get("errors", []),
        "fonte": result.get("fonte", "LOG_UPLOAD"),
    }
