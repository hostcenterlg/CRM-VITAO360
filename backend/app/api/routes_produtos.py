"""
CRM VITAO360 — Rotas /api/produtos

Endpoints de catálogo de produtos VITAO Alimentos.

R4 — Two-Base: este módulo lida com o catálogo (tabela de preços/referência),
     não com valores transacionais. Itens de venda ficam em VendaItem.
R8 — Zero fabricação: produtos vêm de importação SAP/Mercos, nunca inventados.

Endpoints:
  GET  /api/produtos                — listar produtos com filtros e paginação
  GET  /api/produtos/categorias     — listar categorias distintas
  GET  /api/produtos/mais-vendidos  — ranking por quantidade vendida
  GET  /api/produtos/{id}           — detalhe com precos_regionais
  POST /api/produtos                — criar produto (somente admin)
  PATCH /api/produtos/{id}          — atualizar produto parcialmente (somente admin)
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from backend.app.api.deps import get_current_user, require_admin
from backend.app.database import get_db
from backend.app.models.produto import Produto
from backend.app.models.usuario import Usuario
from backend.app.models.venda import Venda
from backend.app.models.venda_item import VendaItem
from backend.app.schemas.produto import (
    ProdutoCreate,
    ProdutoListResponse,
    ProdutoMaisVendido,
    ProdutoResponse,
    ProdutoUpdate,
)

router = APIRouter(prefix="/api/produtos", tags=["Produtos"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_produto_ou_404(db: Session, produto_id: int) -> Produto:
    """Busca produto pelo ID. Levanta 404 se não encontrado."""
    produto = db.scalar(
        select(Produto)
        .where(Produto.id == produto_id)
        .options(selectinload(Produto.precos_regionais))
    )
    if produto is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produto com id={produto_id} nao encontrado.",
        )
    return produto


# ---------------------------------------------------------------------------
# GET /api/produtos — listar produtos com filtros e paginação
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[ProdutoListResponse],
    summary="Listar produtos",
    description=(
        "Retorna catálogo de produtos com filtros opcionais. "
        "Por padrão retorna apenas produtos ativos. "
        "Qualquer usuário autenticado pode consultar."
    ),
)
def listar_produtos(
    categoria: Optional[str] = Query(None, description="Filtrar por categoria exata"),
    busca: Optional[str] = Query(
        None, description="Busca textual em nome ou código (parcial, case-insensitive)"
    ),
    ativo: Optional[bool] = Query(
        default=True, description="Filtrar por status ativo (true=ativos, false=inativos, omitir=todos)"
    ),
    limit: int = Query(default=50, ge=1, le=500, description="Máximo de registros por página"),
    offset: int = Query(default=0, ge=0, description="Registros a pular (paginação)"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list[ProdutoListResponse]:
    """
    Lista produtos do catálogo com paginação.

    Filtros combináveis: categoria, busca textual (nome ou código), status ativo.
    Ordenado por nome ascendente.
    """
    stmt = select(Produto).order_by(Produto.nome.asc())

    if ativo is not None:
        stmt = stmt.where(Produto.ativo == ativo)

    if categoria:
        stmt = stmt.where(Produto.categoria == categoria)

    if busca:
        termo = f"%{busca.lower()}%"
        stmt = stmt.where(
            Produto.nome.ilike(termo) | Produto.codigo.ilike(termo)
        )

    stmt = stmt.limit(limit).offset(offset)
    produtos = db.scalars(stmt).all()

    return [ProdutoListResponse.model_validate(p) for p in produtos]


# ---------------------------------------------------------------------------
# GET /api/produtos/categorias — listar categorias distintas
# ---------------------------------------------------------------------------

@router.get(
    "/categorias",
    response_model=list[str],
    summary="Listar categorias de produtos",
    description="Retorna lista ordenada de categorias distintas cadastradas no catálogo.",
)
def listar_categorias(
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list[str]:
    """
    Retorna categorias únicas de produtos ativos, ordenadas alfabeticamente.
    Usado para preencher filtros/dropdowns no frontend.
    """
    rows = db.execute(
        select(Produto.categoria)
        .where(Produto.ativo == True, Produto.categoria.isnot(None))
        .distinct()
        .order_by(Produto.categoria.asc())
    ).scalars().all()

    return list(rows)


# ---------------------------------------------------------------------------
# GET /api/produtos/mais-vendidos — ranking de produtos por volume
# ---------------------------------------------------------------------------

@router.get(
    "/mais-vendidos",
    response_model=list[ProdutoMaisVendido],
    summary="Ranking de produtos mais vendidos",
    description=(
        "Retorna os produtos com maior volume de vendas (soma de VendaItem.quantidade). "
        "Filtros opcionais: consultor, data_inicio, data_fim. "
        "Retorna no máximo 50 produtos por padrão."
    ),
)
def produtos_mais_vendidos(
    consultor: Optional[str] = Query(
        None, description="Filtrar por consultor (MANU, LARISSA, DAIANE, JULIO)"
    ),
    data_inicio: Optional[date] = Query(None, description="Data início (YYYY-MM-DD), inclusivo"),
    data_fim: Optional[date] = Query(None, description="Data fim (YYYY-MM-DD), inclusivo"),
    limit: int = Query(default=20, ge=1, le=50, description="Quantidade máxima no ranking"),
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> list[ProdutoMaisVendido]:
    """
    Ranking de produtos mais vendidos por quantidade total.

    Junta VendaItem → Venda → (filtros opcionais) → agrega por Produto.
    Ordenado por quantidade_total desc.
    """
    stmt = (
        select(
            Produto.id.label("produto_id"),
            Produto.codigo,
            Produto.nome,
            Produto.categoria,
            func.sum(VendaItem.quantidade).label("quantidade_total"),
            func.sum(VendaItem.valor_total).label("valor_total"),
            func.count(func.distinct(VendaItem.venda_id)).label("num_pedidos"),
        )
        .join(VendaItem, VendaItem.produto_id == Produto.id)
        .join(Venda, Venda.id == VendaItem.venda_id)
        .group_by(Produto.id, Produto.codigo, Produto.nome, Produto.categoria)
        .order_by(func.sum(VendaItem.quantidade).desc())
        .limit(limit)
    )

    # Filtros opcionais na Venda
    if consultor:
        stmt = stmt.where(Venda.consultor == consultor.upper())

    if data_inicio:
        stmt = stmt.where(Venda.data_pedido >= data_inicio)

    if data_fim:
        stmt = stmt.where(Venda.data_pedido <= data_fim)

    rows = db.execute(stmt).all()

    return [
        ProdutoMaisVendido(
            produto_id=r.produto_id,
            codigo=r.codigo,
            nome=r.nome,
            categoria=r.categoria,
            quantidade_total=float(r.quantidade_total),
            valor_total=round(float(r.valor_total), 2),
            num_pedidos=int(r.num_pedidos),
        )
        for r in rows
    ]


# ---------------------------------------------------------------------------
# GET /api/produtos/{id} — detalhe com precos_regionais
# ---------------------------------------------------------------------------

@router.get(
    "/{produto_id}",
    response_model=ProdutoResponse,
    summary="Detalhe de um produto",
    description="Retorna os dados completos de um produto incluindo tabela de preços regionais.",
)
def detalhe_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    _: Usuario = Depends(get_current_user),
) -> ProdutoResponse:
    """
    Retorna produto com precos_regionais carregados via selectinload (evita N+1).
    Raises:
      HTTPException 404 — produto não encontrado
    """
    produto = _get_produto_ou_404(db, produto_id)
    return ProdutoResponse.model_validate(produto)


# ---------------------------------------------------------------------------
# POST /api/produtos — criar produto (somente admin)
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ProdutoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar produto (admin)",
    description=(
        "Cadastra um produto no catálogo. Restrito a admin. "
        "O campo codigo deve ser único (chave de negócio SAP/Mercos)."
    ),
)
def criar_produto(
    payload: ProdutoCreate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ProdutoResponse:
    """
    Cria produto com código único.

    Raises:
      HTTPException 409 — código já cadastrado
    """
    # Verificar unicidade do código antes de inserir
    existente = db.scalar(select(Produto).where(Produto.codigo == payload.codigo))
    if existente is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Produto com codigo={payload.codigo!r} ja existe (id={existente.id}).",
        )

    produto = Produto(
        codigo=payload.codigo,
        nome=payload.nome,
        categoria=payload.categoria,
        fabricante=payload.fabricante,
        unidade=payload.unidade,
        preco_tabela=payload.preco_tabela,
        preco_minimo=payload.preco_minimo,
        comissao_pct=payload.comissao_pct,
        ipi_pct=payload.ipi_pct,
        peso=payload.peso,
        ean=payload.ean,
        ativo=payload.ativo,
    )

    db.add(produto)
    db.commit()
    db.refresh(produto)

    # Recarregar com precos_regionais (vazio no create, mas schema exige o campo)
    return detalhe_produto(produto.id, db, _)


# ---------------------------------------------------------------------------
# PATCH /api/produtos/{id} — atualizar produto parcialmente (somente admin)
# ---------------------------------------------------------------------------

@router.patch(
    "/{produto_id}",
    response_model=ProdutoResponse,
    summary="Atualizar produto parcialmente (admin)",
    description=(
        "Atualiza apenas os campos informados no payload. "
        "Campos ausentes mantêm o valor atual. Restrito a admin."
    ),
)
def atualizar_produto(
    produto_id: int,
    payload: ProdutoUpdate,
    db: Session = Depends(get_db),
    _: Usuario = Depends(require_admin),
) -> ProdutoResponse:
    """
    PATCH parcial — aplica apenas os campos não-None do payload.

    Raises:
      HTTPException 404 — produto não encontrado
    """
    produto = _get_produto_ou_404(db, produto_id)

    # Aplicar apenas os campos explicitamente fornecidos
    update_data = payload.model_dump(exclude_none=True)
    for campo, valor in update_data.items():
        setattr(produto, campo, valor)

    db.commit()
    db.refresh(produto)

    # Recarregar com precos_regionais atualizados
    return detalhe_produto(produto_id, db, _)
