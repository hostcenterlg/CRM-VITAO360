"""
CRM VITAO360 — Rotas /api/rnc

RNC = Registro de Nao Conformidade.

Gerencia ocorrencias de problemas vinculados a clientes — reclamacoes, atrasos,
avarias, erros de nota fiscal, etc.

Endpoints:
  GET   /api/rnc              — lista RNCs com filtros e resumo percentual
  GET   /api/rnc/{id}         — detalhe de uma RNC
  POST  /api/rnc              — criar nova RNC (P0: seta cliente.problema_aberto=True)
  PATCH /api/rnc/{id}         — atualizar status (ABERTO → ... → RESOLVIDO/ENCERRADO)
                                P0: se RESOLVIDO, seta cliente.problema_aberto=False

Ciclo de vida:
  ABERTO → EM_ANDAMENTO → RESOLVIDO
  ABERTO → ENCERRADO

Regras:
  R4  — Two-Base: RNC nao tem valor monetario. Nenhum campo de R$.
  R5  — CNPJ: String(14), zero-padded, NUNCA float.
  R12 — P0: problema_aberto no cliente e atualizado automaticamente ao criar/resolver RNC.

AREA_POR_TIPO (8 categorias PRD FR-028):
  ATRASO ENTREGA (TRANSPORTADORA)       → TRANSPORTADORA
  PRODUTO AVARIADO (FABRICA/TRANSPORTE) → FABRICA/TRANSPORTE
  ERRO SEPARACAO (EXPEDICAO)            → EXPEDICAO
  ERRO NOTA FISCAL (FATURAMENTO)        → FATURAMENTO
  DIVERGENCIA PRECO (FATURAMENTO)       → FATURAMENTO
  COBRANCA INDEVIDA (FINANCEIRO)        → FINANCEIRO
  RUPTURA ESTOQUE (FABRICA/PCP)         → FABRICA/PCP
  PROBLEMA SISTEMA (TI)                 → TI
"""

from __future__ import annotations

import re
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_consultor_or_admin
from backend.app.database import get_db
from backend.app.models.cliente import Cliente
from backend.app.models.rnc import RNC
from backend.app.models.usuario import Usuario

router = APIRouter(prefix="/api/rnc", tags=["RNC"])


# ---------------------------------------------------------------------------
# Constantes de dominio
# ---------------------------------------------------------------------------

# Mapeamento tipo_problema → area_responsavel (PRD FR-028, 8 categorias)
AREA_POR_TIPO: dict[str, str] = {
    "ATRASO ENTREGA (TRANSPORTADORA)": "TRANSPORTADORA",
    "PRODUTO AVARIADO (FABRICA/TRANSPORTE)": "FABRICA/TRANSPORTE",
    "ERRO SEPARACAO (EXPEDICAO)": "EXPEDICAO",
    "ERRO NOTA FISCAL (FATURAMENTO)": "FATURAMENTO",
    "DIVERGENCIA PRECO (FATURAMENTO)": "FATURAMENTO",
    "COBRANCA INDEVIDA (FINANCEIRO)": "FINANCEIRO",
    "RUPTURA ESTOQUE (FABRICA/PCP)": "FABRICA/PCP",
    "PROBLEMA SISTEMA (TI)": "TI",
}

# Status validos e transicoes permitidas
_STATUS_VALIDOS = {"ABERTO", "EM_ANDAMENTO", "RESOLVIDO", "ENCERRADO"}

# Status que indicam problema resolvido/encerrado (para atualizar cliente.problema_aberto)
_STATUS_FECHADOS = {"RESOLVIDO", "ENCERRADO"}


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class RNCCreate(BaseModel):
    """
    Dados necessarios para criar uma nova RNC.

    R4  — Two-Base: nenhum campo de valor monetario nesta rota.
    R5  — cnpj: String(14), apenas digitos numericos, zero-padded.
    R12 — responsavel e derivado automaticamente do tipo_problema (AREA_POR_TIPO).
    """

    cnpj: str = Field(
        ...,
        min_length=14,
        max_length=14,
        description="CNPJ do cliente — 14 digitos numericos, sem pontuacao (R5)",
        examples=["12345678000100"],
    )
    tipo_problema: str = Field(
        ...,
        description=(
            "Categoria do problema (8 opcoes PRD FR-028): "
            "ATRASO ENTREGA (TRANSPORTADORA), PRODUTO AVARIADO (FABRICA/TRANSPORTE), "
            "ERRO SEPARACAO (EXPEDICAO), ERRO NOTA FISCAL (FATURAMENTO), "
            "DIVERGENCIA PRECO (FATURAMENTO), COBRANCA INDEVIDA (FINANCEIRO), "
            "RUPTURA ESTOQUE (FABRICA/PCP), PROBLEMA SISTEMA (TI)"
        ),
        examples=["ATRASO ENTREGA (TRANSPORTADORA)"],
    )
    descricao: str = Field(
        ...,
        min_length=5,
        description="Descricao detalhada do problema relatado pelo cliente",
        examples=["Pedido 1234 nao chegou no prazo combinado de 5 dias uteis."],
    )
    consultor: str = Field(
        ...,
        max_length=50,
        description="Consultor que registra o problema (MANU, LARISSA, DAIANE, JULIO)",
        examples=["MANU"],
    )

    @field_validator("cnpj")
    @classmethod
    def cnpj_deve_ser_numerico(cls, v: str) -> str:
        """R5: CNPJ deve conter apenas digitos numericos."""
        normalizado = re.sub(r"\D", "", v).zfill(14)
        if not normalizado.isdigit() or len(normalizado) != 14:
            raise ValueError(
                f"CNPJ deve conter exatamente 14 digitos numericos. Recebido: {v!r}"
            )
        return normalizado

    @field_validator("tipo_problema")
    @classmethod
    def tipo_problema_valido(cls, v: str) -> str:
        """Valida que o tipo_problema esta entre as 8 categorias PRD FR-028."""
        if v.upper() not in AREA_POR_TIPO:
            categorias = list(AREA_POR_TIPO.keys())
            raise ValueError(
                f"tipo_problema invalido: {v!r}. Categorias validas: {categorias}"
            )
        return v.upper()

    @field_validator("consultor")
    @classmethod
    def consultor_upper(cls, v: str) -> str:
        return v.upper()


class RNCPatch(BaseModel):
    """Campos atualizaveis via PATCH — todos opcionais."""

    status: Optional[str] = Field(
        None,
        description="Novo status: ABERTO | EM_ANDAMENTO | RESOLVIDO | ENCERRADO",
        examples=["EM_ANDAMENTO"],
    )
    resolucao: Optional[str] = Field(
        None,
        description="Descricao da resolucao (obrigatoria quando status=RESOLVIDO)",
        examples=["Transportadora confirmou extravio. Novo pedido enviado."],
    )
    responsavel: Optional[str] = Field(
        None,
        max_length=100,
        description="Responsavel interno pela resolucao",
    )

    @field_validator("status")
    @classmethod
    def status_valido(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v_upper = v.upper()
        if v_upper not in _STATUS_VALIDOS:
            raise ValueError(
                f"Status invalido: {v!r}. Valores permitidos: {sorted(_STATUS_VALIDOS)}"
            )
        return v_upper


class RNCResponse(BaseModel):
    """Representacao completa de uma RNC."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cnpj: str
    tipo_problema: str
    descricao: str
    consultor: str
    status: str
    responsavel: Optional[str] = None
    resolucao: Optional[str] = None
    data_abertura: date
    data_resolucao: Optional[date] = None
    prazo_resolucao: Optional[date] = None

    # Campos calculados (nao persistidos, enriquecidos na rota)
    nome_fantasia: Optional[str] = None


class ResumoRNC(BaseModel):
    """Percentuais de status para o painel resumo."""

    resolvido_pct: float = Field(description="Percentual de RNCs com status RESOLVIDO ou ENCERRADO")
    em_andamento_pct: float = Field(description="Percentual de RNCs com status EM_ANDAMENTO")
    pendente_pct: float = Field(description="Percentual de RNCs com status ABERTO")


class ListaRNCResponse(BaseModel):
    """Resposta paginada de RNCs com resumo percentual."""

    total: int
    resumo: ResumoRNC
    items: list[RNCResponse]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalizar_cnpj(cnpj: str) -> str:
    """R5: normaliza CNPJ para String(14) — remove pontuacao e zero-pad."""
    return re.sub(r"\D", "", str(cnpj)).zfill(14)


def _buscar_cliente_ou_404(db: Session, cnpj: str) -> Cliente:
    """Busca cliente pelo CNPJ normalizado. Levanta 404 se nao encontrado."""
    cliente = db.scalar(select(Cliente).where(Cliente.cnpj == cnpj))
    if cliente is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente com CNPJ {cnpj!r} nao encontrado na base.",
        )
    return cliente


def _montar_rnc_response(rnc: RNC, nome_fantasia: Optional[str]) -> RNCResponse:
    """Constroi RNCResponse a partir de um ORM RNC + nome_fantasia do cliente."""
    return RNCResponse(
        id=rnc.id,
        cnpj=rnc.cnpj,
        tipo_problema=rnc.tipo_problema,
        descricao=rnc.descricao,
        consultor=rnc.consultor,
        status=rnc.status,
        responsavel=rnc.responsavel,
        resolucao=rnc.resolucao,
        data_abertura=rnc.data_abertura,
        data_resolucao=rnc.data_resolucao,
        prazo_resolucao=rnc.prazo_resolucao,
        nome_fantasia=nome_fantasia,
    )


def _calcular_resumo(db: Session, filtros: list) -> ResumoRNC:
    """
    Calcula percentuais de status (resolvido, em_andamento, pendente).

    Aplica os mesmos filtros da listagem para que o resumo reflita o subconjunto filtrado.
    """
    stmt_total = select(func.count()).select_from(RNC)
    stmt_fechados = select(func.count()).select_from(RNC).where(
        RNC.status.in_(_STATUS_FECHADOS)
    )
    stmt_andamento = select(func.count()).select_from(RNC).where(
        RNC.status == "EM_ANDAMENTO"
    )
    stmt_aberto = select(func.count()).select_from(RNC).where(
        RNC.status == "ABERTO"
    )

    # Aplicar filtros de usuario nos subconjuntos
    for f in filtros:
        stmt_total = stmt_total.where(f)
        stmt_fechados = stmt_fechados.where(f)
        stmt_andamento = stmt_andamento.where(f)
        stmt_aberto = stmt_aberto.where(f)

    total = db.scalar(stmt_total) or 0
    if total == 0:
        return ResumoRNC(resolvido_pct=0.0, em_andamento_pct=0.0, pendente_pct=0.0)

    fechados = db.scalar(stmt_fechados) or 0
    andamento = db.scalar(stmt_andamento) or 0
    abertos = db.scalar(stmt_aberto) or 0

    return ResumoRNC(
        resolvido_pct=round(fechados / total * 100, 1),
        em_andamento_pct=round(andamento / total * 100, 1),
        pendente_pct=round(abertos / total * 100, 1),
    )


# ---------------------------------------------------------------------------
# GET /api/rnc — lista RNCs com filtros e resumo
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=ListaRNCResponse,
    summary="Listar RNCs",
    description=(
        "Retorna lista de RNCs com filtros opcionais e resumo de percentuais por status. "
        "Consultores veem apenas suas RNCs. Admins e gerentes veem todas."
    ),
)
def listar_rncs(
    status_filtro: Optional[str] = Query(
        None,
        alias="status",
        description="Filtrar por status: ABERTO | EM_ANDAMENTO | RESOLVIDO | ENCERRADO",
    ),
    tipo_problema: Optional[str] = Query(
        None,
        description="Filtrar por categoria do problema (8 categorias PRD FR-028)",
    ),
    consultor: Optional[str] = Query(
        None,
        description="Filtrar por consultor (MANU / LARISSA / DAIANE / JULIO)",
    ),
    limit: int = Query(default=50, ge=1, le=500, description="Registros por pagina"),
    offset: int = Query(default=0, ge=0, description="Offset para paginacao"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> ListaRNCResponse:
    """
    Lista RNCs com filtros opcionais e resumo percentual de status.

    Isolamento por role:
      - consultor: ve apenas suas RNCs (filtro automatico por consultor_nome)
      - admin / gerente: veem todas as RNCs

    R4: nenhum campo monetario nesta rota (Two-Base Architecture).
    R5: CNPJs retornados sao sempre String(14).
    """
    filtros = []

    # Isolamento automatico para role=consultor
    if usuario.role == "consultor" and usuario.consultor_nome:
        filtros.append(RNC.consultor == usuario.consultor_nome.upper())
    elif consultor:
        filtros.append(RNC.consultor == consultor.upper())

    if status_filtro:
        filtros.append(RNC.status == status_filtro.upper())

    if tipo_problema:
        filtros.append(RNC.tipo_problema == tipo_problema.upper())

    # Resumo calculado sobre o mesmo subconjunto filtrado
    resumo = _calcular_resumo(db, filtros)

    # Query principal com paginacao
    stmt = select(RNC).order_by(RNC.data_abertura.desc(), RNC.id.desc())
    for f in filtros:
        stmt = stmt.where(f)

    # Total (sem paginacao) para o campo total na resposta
    stmt_count = select(func.count()).select_from(RNC)
    for f in filtros:
        stmt_count = stmt_count.where(f)
    total = db.scalar(stmt_count) or 0

    stmt = stmt.limit(limit).offset(offset)
    rncs = db.scalars(stmt).all()

    # Enriquecer com nome_fantasia via lookup no cliente
    items: list[RNCResponse] = []
    for r in rncs:
        cliente = db.scalar(select(Cliente).where(Cliente.cnpj == r.cnpj))
        nome = cliente.nome_fantasia if cliente else None
        items.append(_montar_rnc_response(r, nome))

    return ListaRNCResponse(total=total, resumo=resumo, items=items)


# ---------------------------------------------------------------------------
# GET /api/rnc/{rnc_id} — detalhe de uma RNC
# ---------------------------------------------------------------------------

@router.get(
    "/{rnc_id}",
    response_model=RNCResponse,
    summary="Detalhe de uma RNC",
    description="Retorna os dados completos de uma RNC pelo ID interno.",
)
def detalhe_rnc(
    rnc_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> RNCResponse:
    """
    Retorna uma RNC pelo ID.

    Isolamento por role:
      - consultor: so pode ver RNCs proprias (403 para RNCs de outros consultores)
      - admin / gerente: acesso irrestrito

    Raises:
      HTTPException 404 — RNC nao encontrada
      HTTPException 403 — consultor tentando acessar RNC de outro consultor
    """
    rnc = db.scalar(select(RNC).where(RNC.id == rnc_id))
    if rnc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RNC com id={rnc_id} nao encontrada.",
        )

    # Isolamento: consultores nao podem ver RNCs de outros consultores
    if usuario.role == "consultor":
        nome_consultor = (usuario.consultor_nome or usuario.nome or "").upper()
        if rnc.consultor != nome_consultor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: esta RNC pertence a outro consultor.",
            )

    cliente = db.scalar(select(Cliente).where(Cliente.cnpj == rnc.cnpj))
    nome = cliente.nome_fantasia if cliente else None
    return _montar_rnc_response(rnc, nome)


# ---------------------------------------------------------------------------
# POST /api/rnc — criar nova RNC
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=RNCResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar nova RNC",
    description=(
        "Cria um Registro de Nao Conformidade vinculado a um cliente. "
        "P0: seta cliente.problema_aberto = True imediatamente. "
        "responsavel e derivado automaticamente do tipo_problema (AREA_POR_TIPO). "
        "data_abertura = hoje (data do servidor). "
        "status default = ABERTO. "
        "R4: nenhum valor monetario nesta rota (Two-Base Architecture). "
        "R5: CNPJ normalizado para 14 digitos."
    ),
)
def criar_rnc(
    payload: RNCCreate,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_consultor_or_admin),
) -> RNCResponse:
    """
    Cria uma nova RNC e atualiza cliente.problema_aberto = True.

    Validacoes:
      - CNPJ existe em clientes (404 se nao encontrado)
      - tipo_problema esta entre as 8 categorias PRD FR-028
      - responsavel derivado automaticamente do tipo_problema via AREA_POR_TIPO

    P0 (R12): cliente.problema_aberto = True sinaliza ao sinaleiro que existe
    problema aberto — prioridade maxima no followup.

    Permissao: consultor ou admin.
    """
    # R5: CNPJ ja normalizado pelo validator do schema
    cliente = _buscar_cliente_ou_404(db, payload.cnpj)

    # Derivar area responsavel automaticamente do tipo_problema (PRD FR-028)
    responsavel = AREA_POR_TIPO.get(payload.tipo_problema, "NAO DEFINIDO")

    rnc = RNC(
        cnpj=payload.cnpj,
        tipo_problema=payload.tipo_problema,
        descricao=payload.descricao,
        consultor=payload.consultor,
        status="ABERTO",                     # default
        data_abertura=date.today(),          # data do servidor
        responsavel=responsavel,             # derivado do tipo_problema
    )

    db.add(rnc)

    # P0 (R12): sinalizar problema aberto no cliente — prioridade imediata
    cliente.problema_aberto = True

    db.commit()
    db.refresh(rnc)

    return _montar_rnc_response(rnc, cliente.nome_fantasia)


# ---------------------------------------------------------------------------
# PATCH /api/rnc/{rnc_id} — atualizar status
# ---------------------------------------------------------------------------

@router.patch(
    "/{rnc_id}",
    response_model=RNCResponse,
    summary="Atualizar status de uma RNC",
    description=(
        "Atualiza status e/ou outros campos de uma RNC. "
        "P0: se status = RESOLVIDO, seta cliente.problema_aberto = False "
        "(apenas se nao houver outras RNCs abertas para o mesmo cliente). "
        "Requer autenticacao."
    ),
)
def atualizar_rnc(
    rnc_id: int,
    payload: RNCPatch,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_consultor_or_admin),
) -> RNCResponse:
    """
    Atualiza status, resolucao e/ou responsavel de uma RNC.

    Ao transicionar para RESOLVIDO:
      1. data_resolucao = hoje
      2. Verifica se existem outras RNCs ABERTAS/EM_ANDAMENTO para o mesmo CNPJ
      3. Se nao existirem: seta cliente.problema_aberto = False (P0)

    Ao transicionar para ENCERRADO:
      - Mesmo comportamento de RESOLVIDO para problema_aberto

    Raises:
      HTTPException 404 — RNC nao encontrada
      HTTPException 403 — consultor tentando editar RNC de outro consultor
    """
    rnc = db.scalar(select(RNC).where(RNC.id == rnc_id))
    if rnc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RNC com id={rnc_id} nao encontrada.",
        )

    # Isolamento por role: consultor so edita suas proprias RNCs
    if usuario.role == "consultor":
        nome_consultor = (usuario.consultor_nome or usuario.nome or "").upper()
        if rnc.consultor != nome_consultor:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado: esta RNC pertence a outro consultor.",
            )

    # Aplicar atualizacoes do payload
    novo_status = payload.status
    if novo_status is not None:
        rnc.status = novo_status

        # Ao resolver/encerrar: registrar data de resolucao
        if novo_status in _STATUS_FECHADOS:
            rnc.data_resolucao = date.today()

    if payload.resolucao is not None:
        rnc.resolucao = payload.resolucao

    if payload.responsavel is not None:
        rnc.responsavel = payload.responsavel

    db.flush()  # persiste sem commit para verificar estado consistente

    # P0 (R12): atualizar problema_aberto no cliente se RNC foi resolvida/encerrada
    if novo_status in _STATUS_FECHADOS:
        # Verificar se ainda existem RNCs abertas para este cliente
        outras_rncs_abertas = db.scalar(
            select(func.count())
            .select_from(RNC)
            .where(
                RNC.cnpj == rnc.cnpj,
                RNC.id != rnc.id,
                RNC.status.not_in(_STATUS_FECHADOS),
            )
        ) or 0

        if outras_rncs_abertas == 0:
            cliente = db.scalar(select(Cliente).where(Cliente.cnpj == rnc.cnpj))
            if cliente is not None:
                cliente.problema_aberto = False

    db.commit()
    db.refresh(rnc)

    cliente = db.scalar(select(Cliente).where(Cliente.cnpj == rnc.cnpj))
    nome = cliente.nome_fantasia if cliente else None
    return _montar_rnc_response(rnc, nome)
