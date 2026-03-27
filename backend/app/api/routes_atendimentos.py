"""
CRM VITAO360 — Rotas de atendimentos (core operacional do CRM).

Endpoints:
  POST   /api/atendimentos           — Registrar nova interacao (Motor de Regras executa)
  GET    /api/atendimentos           — Listar com filtros (RBAC: consultor ve apenas os seus)
  GET    /api/atendimentos/stats     — Contagens por resultado e consultor
  GET    /api/atendimentos/{id}      — Detalhe de um atendimento

Fluxo do POST:
  1. Valida resultado contra lista de valores permitidos
  2. Extrai consultor do JWT (consultor usa proprio nome; admin especifica no body futuro)
  3. motor_service.registrar_atendimento() → cria LogInteracao + atualiza Cliente
  4. Commit e retorna log + 9 dimensoes do motor

R4 — Two-Base: LogInteracao criada aqui NUNCA tem campo de valor monetario.
R5 — CNPJ: validado em AtendimentoCreate (min/max 14 chars).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_consultor_or_admin
from backend.app.database import get_db
from backend.app.models.cliente import Cliente
from backend.app.models.log_interacao import LogInteracao
from backend.app.models.usuario import Usuario
from backend.app.schemas.atendimento import (
    AtendimentoCreate,
    AtendimentoListItem,
    AtendimentoResponse,
    MotorResultado,
    TIPOS_CONTATO_VALIDOS,
)
from backend.app.services.motor_regras_service import motor_service

router = APIRouter(prefix="/api/atendimentos", tags=["Atendimentos"])

# Resultados validos — alinhados com scripts/motor_regras.py e seed_auth.py
RESULTADOS_VALIDOS = [
    "VENDA / PEDIDO",
    "ORÇAMENTO",
    "EM ATENDIMENTO",
    "CADASTRO",
    "RELACIONAMENTO",
    "FOLLOW UP 7",
    "FOLLOW UP 15",
    "SUPORTE",
    "NÃO ATENDE",
    "NÃO RESPONDE",
    "RECUSOU LIGAÇÃO",
    "PERDA / FECHOU LOJA",
    "PÓS-VENDA",
    "CS (SUCESSO DO CLIENTE)",
]

# Constantes expostas para uso interno em motor_regras_service (fallback sem scripts/)
FOLLOW_UP_DIAS: dict[str, int] = {
    "EM ATENDIMENTO": 2,
    "ORÇAMENTO": 1,
    "CADASTRO": 2,
    "VENDA / PEDIDO": 45,
    "RELACIONAMENTO": 7,
    "FOLLOW UP 7": 7,
    "FOLLOW UP 15": 15,
    "SUPORTE": 0,
    "NÃO ATENDE": 1,
    "NÃO RESPONDE": 1,
    "RECUSOU LIGAÇÃO": 2,
    "PERDA / FECHOU LOJA": 0,
}

GRUPO_DASH: dict[str, str] = {
    "EM ATENDIMENTO": "FUNIL",
    "ORÇAMENTO": "FUNIL",
    "CADASTRO": "FUNIL",
    "VENDA / PEDIDO": "FUNIL",
    "RELACIONAMENTO": "RELAC.",
    "FOLLOW UP 7": "RELAC.",
    "FOLLOW UP 15": "RELAC.",
    "SUPORTE": "RELAC.",
    "NÃO ATENDE": "NÃO VENDA",
    "NÃO RESPONDE": "NÃO VENDA",
    "RECUSOU LIGAÇÃO": "NÃO VENDA",
    "PERDA / FECHOU LOJA": "NÃO VENDA",
}


# ---------------------------------------------------------------------------
# POST — Registrar atendimento
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=AtendimentoResponse,
    status_code=201,
    summary="Registrar atendimento",
    description=(
        "Registra uma interacao com cliente. "
        "O Motor de Regras e executado automaticamente calculando "
        "estagio_funil, fase, temperatura, tentativa e mais 5 dimensoes."
    ),
)
def registrar_atendimento(
    body: AtendimentoCreate,
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> AtendimentoResponse:
    """
    Registra interacao com cliente. Motor de Regras executa automaticamente.

    - Consultores registram em nome proprio (consultor_nome do JWT).
    - Admins registram como 'ADMIN' (pode ser expandido no futuro).
    - Resultado invalido retorna 400.
    - CNPJ nao encontrado retorna 404.
    """
    # Validar resultado antes de qualquer operacao no banco
    if body.resultado not in RESULTADOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail={
                "erro": "Resultado invalido",
                "recebido": body.resultado,
                "validos": RESULTADOS_VALIDOS,
            },
        )

    # Consultor vem do JWT; admin usa "ADMIN" como fallback
    consultor = user.consultor_nome or "ADMIN"

    # Validate tipo_contato if provided by the frontend
    if body.tipo_contato is not None:
        tc_upper = body.tipo_contato.upper()
        if tc_upper not in TIPOS_CONTATO_VALIDOS:
            raise HTTPException(
                status_code=400,
                detail={
                    "erro": "tipo_contato invalido",
                    "recebido": body.tipo_contato,
                    "validos": sorted(TIPOS_CONTATO_VALIDOS),
                },
            )
        body = body.model_copy(update={"tipo_contato": tc_upper})

    try:
        log = motor_service.registrar_atendimento(
            db=db,
            cnpj=body.cnpj,
            resultado=body.resultado,
            descricao=body.descricao,
            consultor=consultor,
            user_id=user.id,
            tipo_contato_override=body.tipo_contato,
        )
        db.commit()
        db.refresh(log)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro interno: {exc}") from exc

    return AtendimentoResponse(
        id=log.id,
        cnpj=log.cnpj,
        consultor=log.consultor,
        resultado=log.resultado,
        descricao=log.descricao,
        data_interacao=log.data_interacao,
        motor=MotorResultado(
            estagio_funil=log.estagio_funil,
            fase=log.fase,
            tipo_contato=log.tipo_contato,
            acao_futura=log.acao_futura,
            temperatura=log.temperatura,
            follow_up_dias=log.follow_up_dias,
            grupo_dash=log.grupo_dash,
            tentativa=log.tentativa,
        ),
    )


# ---------------------------------------------------------------------------
# GET — Listar atendimentos com filtros
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[AtendimentoListItem],
    summary="Listar atendimentos",
    description=(
        "Lista atendimentos com paginacao e filtros. "
        "Consultores veem apenas os proprios atendimentos (RBAC automatico). "
        "Admins e viewers veem todos."
    ),
)
def listar_atendimentos(
    consultor: str | None = Query(None, description="Filtrar por nome do consultor"),
    cnpj: str | None = Query(None, description="Filtrar por CNPJ (14 digitos)"),
    resultado: str | None = Query(None, description="Filtrar por resultado"),
    limit: int = Query(50, ge=1, le=200, description="Quantidade maxima de registros"),
    offset: int = Query(0, ge=0, description="Registros a pular (paginacao)"),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AtendimentoListItem]:
    """
    Lista atendimentos com filtros opcionais.

    RBAC:
      - role=consultor: ve apenas os proprios atendimentos (ignora param consultor)
      - role=admin/viewer: pode filtrar por qualquer consultor
    """
    q = db.query(LogInteracao)

    # Filtro automatico por role — consultor ve apenas os seus
    if user.role == "consultor" and user.consultor_nome:
        q = q.filter(LogInteracao.consultor == user.consultor_nome)
    elif consultor:
        q = q.filter(LogInteracao.consultor == consultor)

    if cnpj:
        q = q.filter(LogInteracao.cnpj == cnpj)
    if resultado:
        q = q.filter(LogInteracao.resultado == resultado)

    logs = q.order_by(desc(LogInteracao.data_interacao)).offset(offset).limit(limit).all()

    # Buscar nomes de clientes em lote para evitar N+1
    cnpjs = list({log.cnpj for log in logs})
    clientes_map: dict[str, str | None] = {}
    if cnpjs:
        rows = (
            db.query(Cliente.cnpj, Cliente.nome_fantasia)
            .filter(Cliente.cnpj.in_(cnpjs))
            .all()
        )
        clientes_map = {row.cnpj: row.nome_fantasia for row in rows}

    return [
        AtendimentoListItem(
            id=log.id,
            cnpj=log.cnpj,
            nome_fantasia=clientes_map.get(log.cnpj),
            consultor=log.consultor,
            resultado=log.resultado,
            descricao=log.descricao,
            data_interacao=log.data_interacao,
            estagio_funil=log.estagio_funil,
            fase=log.fase,
            temperatura=log.temperatura,
            tentativa=log.tentativa,
        )
        for log in logs
    ]


# ---------------------------------------------------------------------------
# GET /stats — Agregacoes por resultado e consultor
# ---------------------------------------------------------------------------

@router.get(
    "/stats",
    summary="Estatisticas de atendimentos",
    description="Contagens por resultado e por consultor. Consultores veem apenas os seus.",
)
def stats_atendimentos(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Retorna contagens de atendimentos agrupadas por resultado e por consultor.

    Util para o dashboard de producao da equipe comercial.
    """
    # Contagem por resultado
    q_resultado = db.query(
        LogInteracao.resultado,
        func.count(LogInteracao.id).label("total"),
    ).group_by(LogInteracao.resultado)

    # Contagem por consultor (admin ve todos; consultor ve apenas os seus)
    q_consultor = db.query(
        LogInteracao.consultor,
        func.count(LogInteracao.id).label("total"),
    ).group_by(LogInteracao.consultor)

    if user.role == "consultor" and user.consultor_nome:
        q_resultado = q_resultado.filter(LogInteracao.consultor == user.consultor_nome)
        q_consultor = q_consultor.filter(LogInteracao.consultor == user.consultor_nome)

    por_resultado = {row.resultado: row.total for row in q_resultado.all()}
    por_consultor = {row.consultor: row.total for row in q_consultor.all()}

    return {
        "total": sum(por_resultado.values()),
        "por_resultado": por_resultado,
        "por_consultor": por_consultor,
    }


# ---------------------------------------------------------------------------
# GET /{id} — Detalhe de um atendimento
# ---------------------------------------------------------------------------

@router.get(
    "/{atendimento_id}",
    response_model=AtendimentoListItem,
    summary="Detalhe de atendimento",
)
def detalhe_atendimento(
    atendimento_id: int,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AtendimentoListItem:
    """
    Retorna os detalhes de um atendimento pelo ID.

    Consultores so podem ver atendimentos proprios.
    Admins e viewers veem qualquer atendimento.
    """
    log = db.query(LogInteracao).filter(LogInteracao.id == atendimento_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Atendimento nao encontrado")

    # Restricao por role: consultor nao pode ver atendimentos de outros
    if (
        user.role == "consultor"
        and user.consultor_nome
        and log.consultor != user.consultor_nome
    ):
        raise HTTPException(status_code=403, detail="Acesso negado a este atendimento")

    cliente = db.query(Cliente).filter(Cliente.cnpj == log.cnpj).first()

    return AtendimentoListItem(
        id=log.id,
        cnpj=log.cnpj,
        nome_fantasia=cliente.nome_fantasia if cliente else None,
        consultor=log.consultor,
        resultado=log.resultado,
        descricao=log.descricao,
        data_interacao=log.data_interacao,
        estagio_funil=log.estagio_funil,
        fase=log.fase,
        temperatura=log.temperatura,
        tentativa=log.tentativa,
    )
