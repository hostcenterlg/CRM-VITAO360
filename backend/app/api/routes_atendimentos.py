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
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    cnpjs_permitidos_subquery,
    get_current_user,
    get_user_canal_ids,
    require_consultor_or_admin,
)
from backend.app.database import get_db
from backend.app.models.cliente import Cliente
from backend.app.models.log_interacao import LogInteracao
from backend.app.models.usuario import Usuario
from backend.app.utils.cache import cache
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
        # Invalidar cache de dashboard e notificacoes — novo atendimento afeta KPIs
        cache.invalidate_prefix("/api/dashboard")
        cache.invalidate_prefix("/api/notificacoes")
        cache.invalidate_prefix("/api/sinaleiro")
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


class AtendimentosHistoricoResponse(BaseModel):
    """
    Wrapper paginado retornado pelo GET /api/atendimentos.

    Suporta dois estilos de paginacao:
      - Novo (frontend): page + page_size  → retorna total/page/page_size/itens
      - Legado (backward-compat): limit + offset → page calculado a partir de limit/offset
    """

    total: int = Field(..., description="Total de registros que satisfazem os filtros")
    page: int = Field(..., description="Pagina atual (1-indexed)")
    page_size: int = Field(..., description="Tamanho da pagina")
    itens: list[AtendimentoListItem]


@router.get(
    "",
    response_model=AtendimentosHistoricoResponse,
    summary="Listar atendimentos",
    description=(
        "Lista atendimentos com paginacao e filtros. "
        "Consultores veem apenas os proprios atendimentos (RBAC automatico). "
        "Admins e viewers veem todos. "
        "Suporta page/page_size (novo) ou limit/offset (legado)."
    ),
)
def listar_atendimentos(
    consultor: str | None = Query(None, description="Filtrar por nome do consultor"),
    cnpj: str | None = Query(None, description="Filtrar por CNPJ (14 digitos)"),
    resultado: str | None = Query(None, description="Filtrar por resultado"),
    # Novo estilo — usado pelo frontend (ClienteDetalhe / HistoricoBloco)
    page: int | None = Query(None, ge=1, description="Pagina (1-indexed). Se informado, usa paginacao por pagina."),
    page_size: int | None = Query(None, ge=1, le=200, description="Registros por pagina (max 200). Usado com page."),
    # Legado — backward-compat para clientes que usam limit/offset diretamente
    limit: int = Query(50, ge=1, le=200, description="Quantidade maxima de registros (legado; ignorado quando page e fornecido)"),
    offset: int = Query(0, ge=0, description="Registros a pular (legado; ignorado quando page e fornecido)"),
    user: Usuario = Depends(get_current_user),
    user_canal_ids: list[int] | None = Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> AtendimentosHistoricoResponse:
    """
    Lista atendimentos com filtros opcionais, retornando wrapper paginado.

    RBAC:
      - role=consultor: ve apenas os proprios atendimentos (ignora param consultor)
      - role=admin/viewer: pode filtrar por qualquer consultor

    Paginacao:
      - Novo estilo: ?page=1&page_size=20  → offset=(page-1)*page_size, limit=page_size
      - Legado: ?limit=50&offset=0  → page calculado como offset//limit + 1
    """
    # Resolver parametros de paginacao: novo estilo tem precedencia sobre legado
    if page is not None:
        effective_page_size = page_size if page_size is not None else 20
        effective_offset = (page - 1) * effective_page_size
        effective_limit = effective_page_size
        effective_page = page
    else:
        effective_limit = limit
        effective_offset = offset
        effective_page_size = limit
        # Calcular pagina equivalente para o campo de resposta (1-indexed)
        effective_page = (offset // limit) + 1 if limit > 0 else 1

    q = db.query(LogInteracao)

    # Multi-canal scoping (DECISAO L3): admin sem filtro;
    # demais users restritos a CNPJs cujo cliente esta em canais permitidos.
    cnpjs_sub = cnpjs_permitidos_subquery(user_canal_ids)
    if cnpjs_sub is not None:
        q = q.filter(LogInteracao.cnpj.in_(cnpjs_sub))

    # Filtro automatico por role — consultor (interno ou externo) ve apenas
    # os proprios atendimentos. consultor_nome ja foi normalizado para chave
    # curta DE-PARA (MANU/LARISSA/DAIANE/JULIO).
    if user.role in ("consultor", "consultor_externo") and user.consultor_nome:
        q = q.filter(LogInteracao.consultor == user.consultor_nome)
    elif consultor:
        q = q.filter(LogInteracao.consultor == consultor)

    if cnpj:
        q = q.filter(LogInteracao.cnpj == cnpj)
    if resultado:
        q = q.filter(LogInteracao.resultado == resultado)

    # COUNT antes de aplicar limit/offset (mesma query base, sem ordenacao)
    total: int = q.with_entities(func.count(LogInteracao.id)).scalar() or 0

    logs = q.order_by(desc(LogInteracao.data_interacao)).offset(effective_offset).limit(effective_limit).all()

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

    itens = [
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

    return AtendimentosHistoricoResponse(
        total=total,
        page=effective_page,
        page_size=effective_page_size,
        itens=itens,
    )


# ---------------------------------------------------------------------------
# POST /bulk — Registro de múltiplos atendimentos em lote
# ---------------------------------------------------------------------------

class AtendimentoBulkItem(BaseModel):
    """
    Item de atendimento para registro em batch.

    R4 — Two-Base: LogInteracao NUNCA tem campo de valor monetario (R$ = 0.00).
    R5 — CNPJ: 14 digitos numericos, sem pontuacao.
    """

    cnpj: str = Field(
        ...,
        min_length=14,
        max_length=14,
        description="CNPJ do cliente — 14 digitos numericos, sem pontuacao",
    )
    resultado: str = Field(
        ...,
        description="Resultado da interacao (valores validos: ver RESULTADOS_VALIDOS)",
    )
    descricao: str = Field(
        default="",
        description="Observacoes livres do consultor",
    )
    tipo_contato: str | None = Field(
        default=None,
        description="Canal de comunicacao (LIGACAO/WHATSAPP/VISITA/EMAIL/VIDEOCHAMADA)",
    )


class AtendimentoBulkPayload(BaseModel):
    """
    Payload para registro de múltiplos atendimentos em lote.

    Máximo 50 atendimentos por batch.
    R4 — Two-Base: todos os logs são criados com R$ 0.00 (sem valor monetario).
    """

    atendimentos: list[AtendimentoBulkItem] = Field(
        ...,
        description="Lista de atendimentos a registrar (max 50 por batch)",
    )

    @model_validator(mode="after")
    def validar_batch_size(self):
        if not self.atendimentos:
            raise ValueError("atendimentos nao pode ser vazio")
        if len(self.atendimentos) > 50:
            raise ValueError(f"Maximo 50 atendimentos por batch (recebido: {len(self.atendimentos)})")
        return self


class AtendimentoBulkResponse(BaseModel):
    """Resultado do registro em batch de atendimentos."""

    total_recebidos: int
    total_inseridos: int
    erros: list[dict]
    """Lista de erros: [{index, cnpj, erro}]"""


@router.post(
    "/bulk",
    response_model=AtendimentoBulkResponse,
    status_code=201,
    summary="Registro de multiplos atendimentos em lote (max 50)",
)
def bulk_atendimentos(
    body: AtendimentoBulkPayload,
    user: Usuario = Depends(require_consultor_or_admin),
    db: Session = Depends(get_db),
) -> AtendimentoBulkResponse:
    """
    Registra múltiplos atendimentos em uma única requisição (max 50 por batch).

    Regras:
      - R4 — Two-Base: LogInteracao criada NUNCA tem campo de valor monetário.
      - R5 — CNPJ: 14 dígitos, sem pontuação.
      - Consultor extraído do JWT (mesmo que registrar_atendimento individual).
      - Resultados inválidos geram erro por item, sem abortar o batch.
      - CNPJs não encontrados geram erro por item, sem abortar o batch.
      - Motor de Regras executado para cada atendimento individualmente.
      - Cache invalidado após todos os inserts (somente se houver inserts).

    Retorna contagem de inseridos e lista de erros por índice.
    """
    consultor = user.consultor_nome or "ADMIN"
    total_inseridos = 0
    erros: list[dict] = []

    for idx, item in enumerate(body.atendimentos):
        # Validar resultado
        if item.resultado not in RESULTADOS_VALIDOS:
            erros.append({
                "index": idx,
                "cnpj": item.cnpj,
                "erro": f"Resultado invalido: {item.resultado!r}. Validos: {RESULTADOS_VALIDOS}",
            })
            continue

        # Validar tipo_contato se informado
        if item.tipo_contato is not None:
            tc_upper = item.tipo_contato.upper()
            if tc_upper not in TIPOS_CONTATO_VALIDOS:
                erros.append({
                    "index": idx,
                    "cnpj": item.cnpj,
                    "erro": f"tipo_contato invalido: {item.tipo_contato!r}. Validos: {sorted(TIPOS_CONTATO_VALIDOS)}",
                })
                continue
            tipo_contato_norm: str | None = tc_upper
        else:
            tipo_contato_norm = None

        try:
            log = motor_service.registrar_atendimento(
                db=db,
                cnpj=item.cnpj,
                resultado=item.resultado,
                descricao=item.descricao,
                consultor=consultor,
                user_id=user.id,
                tipo_contato_override=tipo_contato_norm,
            )
            db.flush()  # flush sem commit para manter transacao atomica
            total_inseridos += 1
        except ValueError as exc:
            erros.append({"index": idx, "cnpj": item.cnpj, "erro": str(exc)})
        except Exception as exc:
            erros.append({"index": idx, "cnpj": item.cnpj, "erro": f"Erro interno: {exc!s}"})

    # Commit único para todos os inserts bem-sucedidos
    if total_inseridos > 0:
        try:
            db.commit()
            # Invalidar cache de dashboard e notificacoes
            cache.invalidate_prefix("/api/dashboard")
            cache.invalidate_prefix("/api/notificacoes")
            cache.invalidate_prefix("/api/sinaleiro")
        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao persistir batch: {exc!s}",
            ) from exc
    else:
        # Nenhum insert bem-sucedido — rollback para limpar qualquer estado
        db.rollback()

    return AtendimentoBulkResponse(
        total_recebidos=len(body.atendimentos),
        total_inseridos=total_inseridos,
        erros=erros,
    )


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
    user_canal_ids: list[int] | None = Depends(get_user_canal_ids),
    db: Session = Depends(get_db),
) -> dict:
    """
    Retorna contagens de atendimentos agrupadas por resultado e por consultor.

    Util para o dashboard de producao da equipe comercial.
    Multi-canal: agregados respeitam canais permitidos do usuario.
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

    # Multi-canal scoping
    cnpjs_sub = cnpjs_permitidos_subquery(user_canal_ids)
    if cnpjs_sub is not None:
        q_resultado = q_resultado.filter(LogInteracao.cnpj.in_(cnpjs_sub))
        q_consultor = q_consultor.filter(LogInteracao.cnpj.in_(cnpjs_sub))

    if user.role in ("consultor", "consultor_externo") and user.consultor_nome:
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

    # Restricao por role: consultor (interno/externo) nao pode ver atendimentos de outros
    if (
        user.role in ("consultor", "consultor_externo")
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
