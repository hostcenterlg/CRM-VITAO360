"""
CRM VITAO360 — Rotas /api/vendas

Endpoints para registro e consulta de vendas (metade VENDA do Two-Base).

R4 — TWO-BASE ARCHITECTURE (SAGRADA):
  Esta rota manipula APENAS registros com valor_pedido > 0.
  Nunca misturar com log_interacoes / atendimentos (inflacao de 742%).

R5 — CNPJ: String(14), zero-padded, NUNCA float.
R7 — Faturamento baseline: R$ 2.091.000 (CORRIGIDO 2026-03-23).
R8 — classificacao_3tier = REAL por padrao. ALUCINACAO nunca em producao.

Endpoints:
  POST  /api/vendas              — registrar nova venda (consultor ou admin)
  GET   /api/vendas              — listar com filtros e paginacao
  GET   /api/vendas/totais       — faturamento agregado (somente admin)
  GET   /api/vendas/por-status   — contagem de pedidos por status_pedido (admin)
  GET   /api/vendas/{id}         — detalhe de uma venda
  PATCH /api/vendas/{id}/status  — transicao de status do pedido (admin/gerente)
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import (
    get_current_user,
    require_admin,
    require_admin_or_gerente,
    require_consultor_or_admin,
)
from backend.app.schemas.pagination import PaginationParams, PaginatedResponse
from backend.app.database import get_db
from backend.app.models.audit_log import AuditLog
from backend.app.models.cliente import Cliente
from backend.app.models.usuario import Usuario
from backend.app.models.venda import Venda
from backend.app.utils.cache import cache
from backend.app.schemas.venda import (
    VendaCreate,
    VendaPorStatus,
    VendaResponse,
    VendaStatusTransition,
    VendaTotais,
)

router = APIRouter(prefix="/api/vendas", tags=["Vendas"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Consultores canonicos conforme DE-PARA do projeto
_CONSULTORES_VALIDOS = {"MANU", "LARISSA", "DAIANE", "JULIO"}

# Classificacoes que entram no calculo de faturamento (R8: excluir ALUCINACAO)
_TIERS_VALIDOS_PARA_CALCULO = ("REAL", "SINTETICO")

# Mapa de transicoes validas de status_pedido:
#   chave   = status atual
#   valor   = set de status para os quais pode transitar
# Regras de negocio:
#   DIGITADO  → LIBERADO   (admin ou gerente aprovam o pedido)
#   LIBERADO  → FATURADO   (admin emite NF no SAP)
#   FATURADO  → ENTREGUE   (admin confirma entrega)
#   qualquer  → CANCELADO  (admin, estado terminal)
#   CANCELADO → (nenhum)   (terminal, nao pode reabrir)
_TRANSICOES_VALIDAS: dict[str, set[str]] = {
    "DIGITADO":  {"LIBERADO", "CANCELADO"},
    "LIBERADO":  {"FATURADO", "CANCELADO"},
    "FATURADO":  {"ENTREGUE", "CANCELADO"},
    "ENTREGUE":  {"CANCELADO"},
    "CANCELADO": set(),  # terminal
}

# Transicoes que exigem role admin (gerente nao pode executar)
_REQUER_ADMIN = {"FATURADO", "ENTREGUE"}


def _resolver_consultor(payload_consultor: str | None, usuario: Usuario) -> str:
    """
    Determina o consultor final da venda:
      - Se payload informa consultor → usa o payload (admin pode informar outro)
      - Se payload e None → prefere consultor_nome (campo DE-PARA do Usuario)
      - Fallback final: nome do usuario logado (uppercased)

    A funcao NAO valida se o consultor existe no banco — apenas normaliza.
    consultor_nome e o campo canônico do DE-PARA (MANU, LARISSA, DAIANE, JULIO).
    """
    if payload_consultor:
        return payload_consultor.upper()
    # Prefere consultor_nome que ja esta no formato DE-PARA canonico
    if usuario.consultor_nome:
        return usuario.consultor_nome.upper()
    # Fallback: primeiro token do nome do usuario
    return (usuario.nome or "DESCONHECIDO").upper()


def _buscar_cliente_ou_404(db: Session, cnpj: str) -> Cliente:
    """
    Busca cliente pelo CNPJ. Levanta 404 se nao encontrado.

    R5: CNPJ deve ter 14 digitos. Validacao de formato ja ocorreu no schema Pydantic.
    """
    cliente = db.scalar(select(Cliente).where(Cliente.cnpj == cnpj))
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente com CNPJ {cnpj!r} nao encontrado na base.",
        )
    return cliente


def _montar_venda_response(venda: Venda, nome_fantasia: str | None) -> VendaResponse:
    """Constroi VendaResponse a partir de um ORM Venda + nome_fantasia do cliente."""
    return VendaResponse(
        id=venda.id,
        cnpj=venda.cnpj or "",
        nome_fantasia=nome_fantasia,
        data_pedido=venda.data_pedido,
        numero_pedido=venda.numero_pedido,
        valor_pedido=venda.valor_pedido or 0,
        consultor=venda.consultor,
        fonte=venda.fonte,
        classificacao_3tier=venda.classificacao_3tier or "REAL",
        mes_referencia=venda.mes_referencia,
        created_at=venda.created_at,
    )


# ---------------------------------------------------------------------------
# POST /api/vendas — registrar nova venda
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=VendaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar nova venda",
    description=(
        "Registra um pedido de venda (Two-Base: valor_pedido > 0 obrigatorio). "
        "O CNPJ deve existir na tabela de clientes. "
        "classificacao_3tier = REAL por padrao (R8). "
        "mes_referencia derivado automaticamente de data_pedido (formato AAAA-MM)."
    ),
)
def registrar_venda(
    payload: VendaCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_consultor_or_admin),
) -> VendaResponse:
    """
    Cria um registro de venda com enforcement da Two-Base Architecture.

    Validacoes:
      - valor_pedido > 0 (Pydantic + CheckConstraint no banco)
      - CNPJ existe em clientes (404 se nao encontrado)
      - Consultor resolvido a partir do payload ou usuario logado
      - mes_referencia derivado de data_pedido automaticamente

    Permissao: consultor ou admin.
    """
    # Verificar CNPJ na base de clientes
    cliente = _buscar_cliente_ou_404(db, payload.cnpj)

    # Resolver consultor responsavel pela venda
    consultor = _resolver_consultor(payload.consultor, usuario)

    # Derivar mes_referencia de data_pedido (ex.: 2026-03-15 → "2026-03")
    # ATENCAO R6: Mercos MENTE nos nomes de arquivo — sempre usar data_pedido
    # verificada nas linhas 6-7 do relatorio (Data inicial / Data final)
    mes_referencia = payload.data_pedido.strftime("%Y-%m")

    venda = Venda(
        cnpj=payload.cnpj,
        data_pedido=payload.data_pedido,
        numero_pedido=payload.numero_pedido,
        valor_pedido=payload.valor_pedido,        # R4: > 0, Pydantic ja validou
        consultor=consultor,
        fonte=payload.fonte,
        classificacao_3tier="REAL",               # R8: padrao sempre REAL em insercao manual
        mes_referencia=mes_referencia,
    )

    db.add(venda)
    db.commit()
    db.refresh(venda)
    # Invalidar todo o cache — nova venda afeta faturamento, KPIs, sinaleiro, projecao
    cache.clear()

    return _montar_venda_response(venda, cliente.nome_fantasia)


# ---------------------------------------------------------------------------
# GET /api/vendas — listar vendas com filtros e paginacao
# ---------------------------------------------------------------------------

class VendasPaginatedResponse(PaginatedResponse[VendaResponse]):
    """Resposta paginada de vendas (envelope padronizado)."""


@router.get(
    "",
    response_model=VendasPaginatedResponse,
    summary="Listar vendas",
    description=(
        "Retorna lista paginada de vendas com filtros opcionais. "
        "Consultores veem apenas seus proprios registros. "
        "Admins veem todos os registros. "
        "Ordenado por data_pedido desc. "
        "Aceita page/per_page (preferido) ou limit/offset (backward compat)."
    ),
)
def listar_vendas(
    cnpj: Optional[str] = Query(None, description="Filtrar por CNPJ exato (14 digitos)"),
    consultor: Optional[str] = Query(None, description="Filtrar por consultor (MANU, LARISSA, DAIANE, JULIO)"),
    fonte: Optional[str] = Query(None, description="Filtrar por fonte (MERCOS, SAP, MANUAL)"),
    status_pedido: Optional[str] = Query(
        None,
        alias="status",
        description="Filtrar por status_pedido (DIGITADO, LIBERADO, FATURADO, ENTREGUE, CANCELADO)",
    ),
    busca: Optional[str] = Query(
        None,
        min_length=1,
        description="Busca livre por numero_pedido, nome_fantasia ou CNPJ",
    ),
    data_inicio: Optional[date] = Query(None, description="Data inicio (YYYY-MM-DD), inclusivo"),
    data_fim: Optional[date] = Query(None, description="Data fim (YYYY-MM-DD), inclusivo"),
    # Paginacao padronizada (page/per_page) — preferida
    page: Optional[int] = Query(None, ge=1, description="Pagina atual (1-based). Tem precedencia sobre offset."),
    per_page: Optional[int] = Query(None, ge=1, le=200, description="Itens por pagina (max 200). Tem precedencia sobre limit."),
    # Paginacao legada (limit/offset) — mantida para backward compat
    limit: int = Query(default=50, ge=1, le=500, description="Numero maximo de registros por pagina (legado: usar per_page)"),
    offset: int = Query(default=0, ge=0, description="Numero de registros a pular (legado: usar page)"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> VendasPaginatedResponse:
    """
    Lista vendas com paginacao padronizada e filtros opcionais.

    Isolamento por role:
      - consultor: ve apenas os proprios registros (filtro automatico por consultor)
      - admin:     ve todos os registros sem restricao
      - viewer:    acesso somente leitura (sem filtro de consultor)

    Paginacao: aceita page/per_page (padrao) ou limit/offset (backward compat).
    Todos os filtros sao opcionais e combinaveis.
    """
    # Resolver parametros de paginacao
    pagination = PaginationParams.from_limit_offset(
        limit=limit,
        offset=offset,
        per_page=per_page,
        page=page,
    )

    # Query base (sem paginacao — para contar total)
    base_stmt = select(Venda).order_by(Venda.data_pedido.desc())

    # Isolamento automatico por consultor — consultor ve apenas seus registros
    if usuario.role == "consultor":
        nome_consultor = (usuario.consultor_nome or usuario.nome or "").upper()
        base_stmt = base_stmt.where(Venda.consultor == nome_consultor)

    # Filtros opcionais
    if cnpj:
        base_stmt = base_stmt.where(Venda.cnpj == cnpj)

    if consultor:
        # Admins podem filtrar por qualquer consultor;
        # consultores ja tem filtro automatico acima — este parametro e ignorado para eles
        if usuario.role != "consultor":
            base_stmt = base_stmt.where(Venda.consultor == consultor.upper())

    if fonte:
        base_stmt = base_stmt.where(Venda.fonte == fonte.upper())

    if status_pedido:
        base_stmt = base_stmt.where(Venda.status_pedido == status_pedido.upper())

    if busca:
        from sqlalchemy import or_
        termo = f"%{busca.strip()}%"
        # Cnpjs cujo nome_fantasia bate (batch lookup p/ evitar JOIN aqui)
        cnpjs_por_nome = list(
            db.scalars(
                select(Cliente.cnpj).where(Cliente.nome_fantasia.ilike(termo))
            ).all()
        )
        clauses = [
            Venda.numero_pedido.ilike(termo),
            Venda.cnpj.ilike(termo),
        ]
        if cnpjs_por_nome:
            clauses.append(Venda.cnpj.in_(cnpjs_por_nome))
        base_stmt = base_stmt.where(or_(*clauses))

    if data_inicio:
        base_stmt = base_stmt.where(Venda.data_pedido >= data_inicio)

    if data_fim:
        base_stmt = base_stmt.where(Venda.data_pedido <= data_fim)

    # Total para calculo de paginas
    total = db.scalar(select(func.count()).select_from(base_stmt.subquery())) or 0

    # Aplicar paginacao
    paginated_stmt = base_stmt.limit(pagination.limit).offset(pagination.offset)
    vendas = db.scalars(paginated_stmt).all()

    # Batch lookup para nome_fantasia — evita N+1 e falha em orphaned vendas
    # (vendas cujo CNPJ nao existe na tabela clientes causam erro no lazy load)
    cnpjs = list({v.cnpj for v in vendas})
    clientes_map: dict[str, str | None] = {}
    if cnpjs:
        rows = db.query(Cliente.cnpj, Cliente.nome_fantasia).filter(Cliente.cnpj.in_(cnpjs)).all()
        clientes_map = {row.cnpj: row.nome_fantasia for row in rows}

    items = [_montar_venda_response(v, clientes_map.get(v.cnpj)) for v in vendas]

    return VendasPaginatedResponse.build(items=items, total=total, params=pagination)


# ---------------------------------------------------------------------------
# GET /api/vendas/totais — faturamento agregado (somente admin)
# ---------------------------------------------------------------------------

@router.get(
    "/totais",
    response_model=VendaTotais,
    summary="Faturamento agregado (admin)",
    description=(
        "Retorna totais de faturamento: soma, contagem, ticket medio, "
        "breakdown por consultor e por mes. "
        "Apenas registros REAL e SINTETICO entram no calculo (R8). "
        "Baseline de referencia: R$ 2.091.000 (R7). "
        "Restrito a administradores."
    ),
)
def totais_faturamento(
    data_inicio: Optional[date] = Query(None, description="Inicio do periodo (YYYY-MM-DD)"),
    data_fim: Optional[date] = Query(None, description="Fim do periodo (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> VendaTotais:
    """
    Agrega faturamento total com breakdown por consultor e por mes.

    R8: Apenas classificacao_3tier IN (REAL, SINTETICO). ALUCINACAO excluido.
    R7: Baseline = R$ 2.091.000. Divergencia > 0.5% deve ser investigada.

    Permissao: somente admin.
    """
    # Filtro base: apenas dados confiaveis (R8)
    filtro_tier = Venda.classificacao_3tier.in_(_TIERS_VALIDOS_PARA_CALCULO)

    # Filtro opcional de periodo
    filtros_periodo = []
    if data_inicio:
        filtros_periodo.append(Venda.data_pedido >= data_inicio)
    if data_fim:
        filtros_periodo.append(Venda.data_pedido <= data_fim)

    # Total de faturamento e contagem
    stmt_totais = (
        select(
            func.coalesce(func.sum(Venda.valor_pedido), 0.0).label("faturamento"),
            func.count().label("total"),
        )
        .where(filtro_tier, *filtros_periodo)
    )
    row_totais = db.execute(stmt_totais).one()
    faturamento_total = float(row_totais.faturamento)
    total_vendas = int(row_totais.total)
    ticket_medio = round(faturamento_total / total_vendas, 2) if total_vendas > 0 else 0.0

    # Breakdown por consultor — ordenado por faturamento desc
    stmt_consultor = (
        select(
            Venda.consultor,
            func.sum(Venda.valor_pedido).label("faturamento"),
            func.count().label("qtd"),
        )
        .where(filtro_tier, *filtros_periodo)
        .group_by(Venda.consultor)
        .order_by(func.sum(Venda.valor_pedido).desc())
    )
    rows_consultor = db.execute(stmt_consultor).all()
    por_consultor = [
        {
            "consultor": r.consultor,
            "faturamento": round(float(r.faturamento), 2),
            "qtd": int(r.qtd),
        }
        for r in rows_consultor
    ]

    # Breakdown por mes — ordenado por mes desc (formato AAAA-MM)
    stmt_mes = (
        select(
            Venda.mes_referencia,
            func.sum(Venda.valor_pedido).label("faturamento"),
            func.count().label("qtd"),
        )
        .where(filtro_tier, *filtros_periodo)
        .group_by(Venda.mes_referencia)
        .order_by(Venda.mes_referencia.desc())
    )
    rows_mes = db.execute(stmt_mes).all()
    por_mes = [
        {
            "mes": r.mes_referencia or "—",
            "faturamento": round(float(r.faturamento), 2),
            "qtd": int(r.qtd),
        }
        for r in rows_mes
    ]

    return VendaTotais(
        faturamento_total=round(faturamento_total, 2),
        total_vendas=total_vendas,
        ticket_medio=ticket_medio,
        por_consultor=por_consultor,
        por_mes=por_mes,
    )


# ---------------------------------------------------------------------------
# GET /api/vendas/por-status — contagem de pedidos por status (admin)
# NOTE: This MUST be registered BEFORE /{venda_id} to avoid FastAPI treating
#       "por-status" as a path parameter (int) and returning a 422 type error.
# ---------------------------------------------------------------------------

@router.get(
    "/por-status",
    response_model=list[VendaPorStatus],
    summary="Contagem de pedidos por status (admin)",
    description=(
        "Retorna contagem e valor total de pedidos agrupados por status_pedido. "
        "Restrito a administradores."
    ),
)
def vendas_por_status(
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> list[VendaPorStatus]:
    """
    Agrega vendas por status_pedido.

    Útil para o painel gerencial monitorar o funil de pedidos:
    quantos estão em DIGITADO, LIBERADO, FATURADO, ENTREGUE, CANCELADO.
    """
    stmt = (
        select(
            Venda.status_pedido.label("status"),
            func.count().label("quantidade"),
            func.coalesce(func.sum(Venda.valor_pedido), 0.0).label("valor_total"),
        )
        .group_by(Venda.status_pedido)
        .order_by(Venda.status_pedido.asc())
    )
    rows = db.execute(stmt).all()

    return [
        VendaPorStatus(
            status=r.status,
            quantidade=int(r.quantidade),
            valor_total=round(float(r.valor_total), 2),
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# PATCH /api/vendas/{id}/status — transicao de status do pedido
# ---------------------------------------------------------------------------

@router.patch(
    "/{venda_id}/status",
    response_model=VendaResponse,
    summary="Transicao de status do pedido",
    description=(
        "Realiza uma transicao de status_pedido com validacao de fluxo. "
        "Transicoes validas: DIGITADO→LIBERADO, LIBERADO→FATURADO, "
        "FATURADO→ENTREGUE, qualquer→CANCELADO. "
        "Requer admin ou gerente. CANCELADO e estado terminal."
    ),
)
def transicionar_status(
    venda_id: int,
    payload: VendaStatusTransition,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_admin_or_gerente),
) -> VendaResponse:
    """
    Transiciona o status_pedido de uma venda com validacao de fluxo.

    Regras de autorização:
      - gerente pode aprovar DIGITADO → LIBERADO e cancelar
      - admin pode executar todas as transicoes
      - Transicoes para FATURADO e ENTREGUE exigem admin

    Cada transicao gera um registro em AuditLog para rastreabilidade.

    Raises:
      HTTPException 404 — venda nao encontrada
      HTTPException 422 — transicao invalida (fluxo ou autorizacao)
    """
    venda = db.scalar(select(Venda).where(Venda.id == venda_id))
    if venda is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Venda com id={venda_id} nao encontrada.",
        )

    status_atual = venda.status_pedido
    novo_status = payload.novo_status

    # Validar se a transicao e permitida no fluxo
    transicoes_permitidas = _TRANSICOES_VALIDAS.get(status_atual, set())
    if novo_status not in transicoes_permitidas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=(
                f"Transicao invalida: {status_atual!r} → {novo_status!r}. "
                f"Transicoes permitidas a partir de {status_atual!r}: "
                f"{sorted(transicoes_permitidas) or 'nenhuma (estado terminal)'}."
            ),
        )

    # Validar autorizacao extra para transicoes que exigem admin
    if novo_status in _REQUER_ADMIN and usuario.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Transicao para {novo_status!r} requer role 'admin'. "
                f"Usuario {usuario.nome!r} tem role {usuario.role!r}."
            ),
        )

    # Motivo obrigatorio para cancelamento
    if novo_status == "CANCELADO" and not payload.motivo:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Campo 'motivo' e obrigatorio para cancelamento de pedido.",
        )

    # Executar a transicao
    venda.status_pedido = novo_status
    if payload.motivo:
        # Acrescentar motivo nas observacoes sem sobrescrever observacoes existentes
        prefixo = f"[{novo_status}] {payload.motivo}"
        venda.observacao = (
            f"{venda.observacao}\n{prefixo}" if venda.observacao else prefixo
        )

    # Registrar em AuditLog para rastreabilidade (R12)
    audit = AuditLog(
        cnpj=venda.cnpj,
        campo="status_pedido",
        valor_anterior=status_atual,
        valor_novo=novo_status,
        usuario_id=usuario.id,
        usuario_nome=usuario.nome,
    )
    db.add(audit)

    db.commit()
    db.refresh(venda)

    nome_fantasia = venda.cliente.nome_fantasia if venda.cliente else None
    return _montar_venda_response(venda, nome_fantasia)


# ---------------------------------------------------------------------------
# GET /api/vendas/{id} — detalhe de uma venda
# NOTE: Registered LAST among GET routes so static paths (/totais, /por-status)
#       are matched first. FastAPI would try to cast "por-status" to int and
#       raise a 422 if this were registered before those routes.
# ---------------------------------------------------------------------------

@router.get(
    "/{venda_id}",
    response_model=VendaResponse,
    summary="Detalhe de uma venda",
    description="Retorna os dados completos de uma venda pelo seu ID interno.",
)
def detalhe_venda(
    venda_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> VendaResponse:
    """
    Retorna uma venda pelo ID.

    Isolamento por role:
      - consultor: so pode ver vendas proprias (403 para vendas de outros consultores)
      - admin/viewer: acesso irrestrito

    Raises:
      HTTPException 404 — venda nao encontrada
      HTTPException 403 — consultor tentando acessar venda de outro consultor
    """
    venda = db.scalar(select(Venda).where(Venda.id == venda_id))
    if venda is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Venda com id={venda_id} nao encontrada.",
        )

    # Isolamento: consultores nao podem ver vendas de outros consultores
    if usuario.role == "consultor":
        nome_consultor = (usuario.consultor_nome or usuario.nome or "").upper()
        if venda.consultor != nome_consultor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: esta venda pertence a outro consultor.",
            )

    nome_fantasia = venda.cliente.nome_fantasia if venda.cliente else None
    return _montar_venda_response(venda, nome_fantasia)
