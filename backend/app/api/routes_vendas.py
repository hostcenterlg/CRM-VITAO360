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
  POST /api/vendas              — registrar nova venda (consultor ou admin)
  GET  /api/vendas              — listar com filtros e paginacao
  GET  /api/vendas/totais       — faturamento agregado (somente admin)
  GET  /api/vendas/{id}         — detalhe de uma venda
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_admin, require_consultor_or_admin
from backend.app.database import get_db
from backend.app.models.cliente import Cliente
from backend.app.models.usuario import Usuario
from backend.app.models.venda import Venda
from backend.app.schemas.venda import VendaCreate, VendaResponse, VendaTotais

router = APIRouter(prefix="/api/vendas", tags=["Vendas"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Consultores canonicos conforme DE-PARA do projeto
_CONSULTORES_VALIDOS = {"MANU", "LARISSA", "DAIANE", "JULIO"}

# Classificacoes que entram no calculo de faturamento (R8: excluir ALUCINACAO)
_TIERS_VALIDOS_PARA_CALCULO = ("REAL", "SINTETICO")


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
        cnpj=venda.cnpj,
        nome_fantasia=nome_fantasia,
        data_pedido=venda.data_pedido,
        numero_pedido=venda.numero_pedido,
        valor_pedido=venda.valor_pedido,
        consultor=venda.consultor,
        fonte=venda.fonte,
        classificacao_3tier=venda.classificacao_3tier,
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

    return _montar_venda_response(venda, cliente.nome_fantasia)


# ---------------------------------------------------------------------------
# GET /api/vendas — listar vendas com filtros e paginacao
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[VendaResponse],
    summary="Listar vendas",
    description=(
        "Retorna lista de vendas com filtros opcionais. "
        "Consultores veem apenas seus proprios registros. "
        "Admins veem todos os registros. "
        "Ordenado por data_pedido desc."
    ),
)
def listar_vendas(
    cnpj: Optional[str] = Query(None, description="Filtrar por CNPJ exato (14 digitos)"),
    consultor: Optional[str] = Query(None, description="Filtrar por consultor (MANU, LARISSA, DAIANE, JULIO)"),
    fonte: Optional[str] = Query(None, description="Filtrar por fonte (MERCOS, SAP, MANUAL)"),
    data_inicio: Optional[date] = Query(None, description="Data inicio (YYYY-MM-DD), inclusivo"),
    data_fim: Optional[date] = Query(None, description="Data fim (YYYY-MM-DD), inclusivo"),
    limit: int = Query(default=50, ge=1, le=500, description="Numero maximo de registros por pagina"),
    offset: int = Query(default=0, ge=0, description="Numero de registros a pular (paginacao)"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[VendaResponse]:
    """
    Lista vendas com paginacao e filtros opcionais.

    Isolamento por role:
      - consultor: ve apenas os proprios registros (filtro automatico por consultor)
      - admin:     ve todos os registros sem restricao
      - viewer:    acesso somente leitura (sem filtro de consultor)

    Todos os filtros sao opcionais e combinaveis.
    """
    stmt = select(Venda).order_by(Venda.data_pedido.desc())

    # Isolamento automatico por consultor — consultor ve apenas seus registros
    if usuario.role == "consultor":
        nome_consultor = (usuario.consultor_nome or usuario.nome or "").upper()
        stmt = stmt.where(Venda.consultor == nome_consultor)

    # Filtros opcionais
    if cnpj:
        stmt = stmt.where(Venda.cnpj == cnpj)

    if consultor:
        # Admins podem filtrar por qualquer consultor;
        # consultores ja tem filtro automatico acima — este parametro e ignorado para eles
        if usuario.role != "consultor":
            stmt = stmt.where(Venda.consultor == consultor.upper())

    if fonte:
        stmt = stmt.where(Venda.fonte == fonte.upper())

    if data_inicio:
        stmt = stmt.where(Venda.data_pedido >= data_inicio)

    if data_fim:
        stmt = stmt.where(Venda.data_pedido <= data_fim)

    stmt = stmt.limit(limit).offset(offset)
    vendas = db.scalars(stmt).all()

    # Enriquecer com nome_fantasia via JOIN lazy (relationship ja configurado no model)
    resultado: list[VendaResponse] = []
    for v in vendas:
        nome = v.cliente.nome_fantasia if v.cliente else None
        resultado.append(_montar_venda_response(v, nome))

    return resultado


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
# GET /api/vendas/{id} — detalhe de uma venda
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
