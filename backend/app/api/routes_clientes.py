"""
CRM VITAO360 — Rotas /api/clientes

Endpoints:
  GET    /api/clientes               — lista com filtros + paginacao
  GET    /api/clientes/stats         — agregados (count por situacao, consultor, sinaleiro)
  GET    /api/clientes/por-consultor — resumo de clientes e faturamento por consultor
  PATCH  /api/clientes/redistribuir  — redistribuicao em lote de carteira entre consultores (admin)
  GET    /api/clientes/{cnpj}        — detalhe de um cliente
  PATCH  /api/clientes/{cnpj}        — edicao inline (consultor, rede_regional) — admin/gerente
  GET    /api/clientes/{cnpj}/score  — breakdown do score v2 com 6 fatores ponderados
  GET    /api/clientes/{cnpj}/score-history — historico de score (ultimos 30)
  GET    /api/clientes/{cnpj}/timeline — historico unificado (vendas + interacoes)

Todos os filtros sao opcionais e cumulativos.
Paginacao padrao: limit=50, offset=0.

Consultores com role='consultor' tem a carteira filtrada automaticamente
pelo proprio nome (consultor_nome do JWT). Admins veem todos.

Todos os endpoints requerem autenticacao JWT (Bearer token).
"""

from __future__ import annotations

import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user, require_admin, require_admin_or_gerente
from backend.app.database import get_db
from backend.app.models.audit_log import AuditLog
from backend.app.models.cliente import Cliente
from backend.app.models.log_interacao import LogInteracao
from backend.app.models.usuario import Usuario
from backend.app.models.venda import Venda
from backend.app.schemas.pagination import PaginationParams, PaginatedResponse
from backend.app.services.score_service import PESOS, score_service

router = APIRouter(prefix="/api/clientes", tags=["Clientes"])


# ---------------------------------------------------------------------------
# Schemas Pydantic (resposta)
# ---------------------------------------------------------------------------

class ClienteResumo(BaseModel):
    """Campos retornados na listagem — subconjunto leve."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    cnpj: str
    nome_fantasia: Optional[str]
    uf: Optional[str]
    cidade: Optional[str]
    consultor: Optional[str]
    situacao: Optional[str]
    temperatura: Optional[str]
    score: Optional[float]
    prioridade: Optional[str]
    sinaleiro: Optional[str]
    curva_abc: Optional[str]
    faturamento_total: Optional[float]
    tipo_cliente: Optional[str]
    fase: Optional[str]


class ClienteDetalhe(ClienteResumo):
    """Todos os campos — retornado no endpoint /{cnpj}."""

    razao_social: Optional[str]
    rede_regional: Optional[str]
    codigo_cliente: Optional[str]
    tipo_cliente_sap: Optional[str]
    macroregiao: Optional[str]
    dias_sem_compra: Optional[int]
    valor_ultimo_pedido: Optional[float]
    ciclo_medio: Optional[float]
    n_compras: Optional[int]
    tipo_contato: Optional[str]
    resultado: Optional[str]
    estagio_funil: Optional[str]
    acao_futura: Optional[str]
    followup_dias: Optional[int]
    grupo_dash: Optional[str]
    tipo_acao: Optional[str]
    tentativas: Optional[str]
    problema_aberto: Optional[bool]
    followup_vencido: Optional[bool]
    cs_no_prazo: Optional[bool]
    classificacao_3tier: Optional[str]
    # Projeção
    meta_anual: Optional[float]
    realizado_acumulado: Optional[float]
    pct_alcancado: Optional[float]
    gap_valor: Optional[float]
    status_meta: Optional[str]


class ListagemResponse(BaseModel):
    """
    Resposta de listagem de clientes com paginação.

    Mantém backward compatibility com limit/offset enquanto expõe
    o formato page/per_page padronizado.
    """
    total: int
    limit: int
    offset: int
    # Campos de paginação padronizada (adicionados sem quebrar o frontend existente)
    page: int = 1
    per_page: int = 50
    pages: int = 1
    has_next: bool = False
    has_prev: bool = False
    registros: list[ClienteResumo]


class StatsDistribuicao(BaseModel):
    label: str
    quantidade: int


class StatsResponse(BaseModel):
    total_clientes: int
    por_situacao: list[StatsDistribuicao]
    por_consultor: list[StatsDistribuicao]
    por_sinaleiro: list[StatsDistribuicao]
    por_curva_abc: list[StatsDistribuicao]
    por_prioridade: list[StatsDistribuicao]


class ClientePatchInput(BaseModel):
    """Payload para edicao inline de cliente via PATCH.

    Campos editaveis:
      - consultor:     reatribuicao de carteira (DE-PARA: MANU/LARISSA/DAIANE/JULIO)
      - rede_regional: alteracao da rede/franquia do cliente
      - telefone:      telefone de contato (String, max 20 chars)
      - email:         e-mail de contato (String, max 255 chars)
      - cidade:        cidade do cliente (String, max 100 chars)
      - uf:            unidade federativa (String, 2 chars, maiusculo)

    Nota: contato_principal nao existe na tabela clientes — omitido intencionalmente.

    Todos os campos sao opcionais — somente os enviados serao atualizados.
    """

    consultor: Optional[str] = None
    rede_regional: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    cidade: Optional[str] = None
    uf: Optional[str] = None


class ClientePatchResponse(BaseModel):
    """Retorno do PATCH com cliente atualizado e resumo da auditoria."""

    cnpj: str
    campos_alterados: list[str]
    cliente: ClienteDetalhe


# Consultores validos (DE-PARA definido na CLAUDE.md)
_CONSULTORES_VALIDOS = {"MANU", "LARISSA", "DAIANE", "JULIO"}


class RedistribuirPayload(BaseModel):
    """Payload para redistribuicao em lote de carteira entre consultores.

    R12 — L3: operacao aprovada pelo Leandro (licenca maternidade Manu Q2 2026).
    R5: CNPJs validados e normalizados para 14 digitos.
    """

    cnpjs: list[str]
    """Lista de CNPJs a reatribuir (aceita com ou sem pontuacao)."""

    novo_consultor: str
    """Nome do consultor destino. Valido: MANU, LARISSA, DAIANE, JULIO."""


class RedistribuirResponse(BaseModel):
    """Resultado da operacao de redistribuicao em lote."""

    total_processados: int
    """Total de CNPJs recebidos no payload."""

    total_atualizados: int
    """CNPJs que tiveram o consultor efetivamente alterado."""

    erros: list[str]
    """CNPJs nao encontrados ou com erro de processamento."""


class ConsultorResumo(BaseModel):
    """Resumo de clientes e faturamento agrupados por consultor."""

    consultor: str
    total: int
    faturamento: float


# ---------------------------------------------------------------------------
# Schemas para bulk operations
# ---------------------------------------------------------------------------

# Campos permitidos para atualização em massa (subconjunto do PATCH individual)
_CAMPOS_BULK_PERMITIDOS = {
    "consultor",
    "rede_regional",
    "telefone",
    "email",
    "cidade",
    "uf",
    "situacao",
    "temperatura",
}


class BulkUpdatePayload(BaseModel):
    """
    Payload para atualização em massa de clientes (admin only).

    R5: CNPJs normalizados para 14 dígitos (aceita com ou sem pontuação).
    R12 — L3: operação de massa requer role=admin (aprovado Leandro).

    Campos atualizáveis em massa:
      consultor, rede_regional, telefone, email, cidade, uf, situacao, temperatura

    Operações que alteram dados de faturamento ou estrutura de tabela NÃO são
    permitidas via bulk (R12 — L3): usar endpoints individuais.
    """

    cnpjs: list[str]
    """Lista de CNPJs a atualizar (1 a 200 por batch)."""

    updates: dict[str, str]
    """Campos a atualizar: {campo: novo_valor}. Campos inválidos são ignorados."""

    @model_validator(mode="after")
    def validar_batch(self):
        if not self.cnpjs:
            raise ValueError("cnpjs nao pode ser vazio")
        if len(self.cnpjs) > 200:
            raise ValueError(f"Maximo 200 CNPJs por batch (recebido: {len(self.cnpjs)})")
        if not self.updates:
            raise ValueError("updates nao pode ser vazio")
        campos_invalidos = set(self.updates.keys()) - _CAMPOS_BULK_PERMITIDOS
        if campos_invalidos:
            raise ValueError(
                f"Campos nao permitidos em bulk: {campos_invalidos}. "
                f"Permitidos: {_CAMPOS_BULK_PERMITIDOS}"
            )
        return self


class BulkUpdateResponse(BaseModel):
    """Resultado da operação de bulk update."""

    total_recebidos: int
    total_atualizados: int
    erros: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=ListagemResponse, summary="Listar clientes")
def listar_clientes(
    consultor: Optional[str] = Query(None, description="Filtrar por consultor (MANU/LARISSA/DAIANE/JULIO)"),
    situacao: Optional[str] = Query(None, description="Filtrar por situacao (ATIVO/PROSPECT/INAT.REC/INAT.ANT)"),
    sinaleiro: Optional[str] = Query(None, description="Filtrar por sinaleiro (VERDE/AMARELO/VERMELHO/ROXO)"),
    curva_abc: Optional[str] = Query(None, description="Filtrar por curva ABC (A/B/C)"),
    temperatura: Optional[str] = Query(None, description="Filtrar por temperatura (QUENTE/MORNO/FRIO/CRITICO)"),
    prioridade: Optional[str] = Query(None, description="Filtrar por prioridade (P0-P7)"),
    uf: Optional[str] = Query(None, description="Filtrar por UF (ex.: SP, RS, RJ)"),
    busca: Optional[str] = Query(None, description="Busca por nome fantasia ou razao social (contem)"),
    # Paginacao padronizada (page/per_page) — preferida
    page: Optional[int] = Query(None, ge=1, description="Pagina atual (1-based). Tem precedencia sobre offset."),
    per_page: Optional[int] = Query(None, ge=1, le=200, description="Itens por pagina (max 200). Tem precedencia sobre limit."),
    # Paginacao legada (limit/offset) — mantida para backward compat com frontend existente
    limit: int = Query(50, ge=1, le=500, description="Registros por pagina (legado: usar per_page)"),
    offset: int = Query(0, ge=0, description="Offset para paginacao (legado: usar page)"),
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ListagemResponse:
    """
    Retorna lista paginada de clientes com filtros opcionais cumulativos.

    Todos os filtros sao case-insensitive para strings de controle
    (consultor, situacao, sinaleiro, curva_abc, temperatura, prioridade).

    Consultores com role='consultor' tem a carteira filtrada automaticamente
    pelo proprio consultor_nome; nao podem ver carteira alheia.
    Admins e viewers veem todos (sujeito ao filtro manual de consultor).

    Requer autenticacao JWT.
    """
    # Resolver parametros de paginacao: page/per_page tem precedencia sobre limit/offset
    pagination = PaginationParams.from_limit_offset(
        limit=limit,
        offset=offset,
        per_page=per_page,
        page=page,
    )

    stmt = select(Cliente)

    # Filtro automatico por carteira para role=consultor
    if user.role == "consultor" and user.consultor_nome:
        stmt = stmt.where(Cliente.consultor == user.consultor_nome.upper())
    elif consultor:
        stmt = stmt.where(Cliente.consultor == consultor.upper())
    if situacao:
        stmt = stmt.where(Cliente.situacao == situacao.upper())
    if sinaleiro:
        stmt = stmt.where(Cliente.sinaleiro == sinaleiro.upper())
    if curva_abc:
        stmt = stmt.where(Cliente.curva_abc == curva_abc.upper())
    if temperatura:
        stmt = stmt.where(Cliente.temperatura == temperatura.upper())
    if prioridade:
        stmt = stmt.where(Cliente.prioridade == prioridade.upper())
    if uf:
        stmt = stmt.where(Cliente.uf == uf.upper())
    if busca:
        termo = f"%{busca}%"
        stmt = stmt.where(
            Cliente.nome_fantasia.ilike(termo) | Cliente.razao_social.ilike(termo)
        )

    # Total antes da paginação
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    # Ordenação padrão: score desc para surfar os mais prioritários primeiro
    stmt = stmt.order_by(Cliente.score.desc().nulls_last(), Cliente.nome_fantasia)
    stmt = stmt.limit(pagination.limit).offset(pagination.offset)

    clientes = db.scalars(stmt).all()

    import math
    pages = max(math.ceil(total / pagination.per_page) if pagination.per_page else 1, 1)

    return ListagemResponse(
        total=total,
        limit=pagination.per_page,
        offset=pagination.offset,
        page=pagination.page,
        per_page=pagination.per_page,
        pages=pages,
        has_next=pagination.page < pages,
        has_prev=pagination.page > 1,
        registros=[ClienteResumo.model_validate(c) for c in clientes],
    )


@router.get("/stats", response_model=StatsResponse, summary="Agregados por dimensao")
def stats_clientes(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StatsResponse:
    """
    Retorna contagens agrupadas por situacao, consultor, sinaleiro,
    curva ABC e prioridade. Usado pelo dashboard de distribuicao.

    Requer autenticacao JWT.
    """

    def _contar(coluna):
        rows = db.execute(
            select(coluna, func.count().label("qt"))
            .group_by(coluna)
            .order_by(func.count().desc())
        ).all()
        return [StatsDistribuicao(label=r[0] or "—", quantidade=r[1]) for r in rows]

    total = db.scalar(select(func.count()).select_from(Cliente))

    return StatsResponse(
        total_clientes=total or 0,
        por_situacao=_contar(Cliente.situacao),
        por_consultor=_contar(Cliente.consultor),
        por_sinaleiro=_contar(Cliente.sinaleiro),
        por_curva_abc=_contar(Cliente.curva_abc),
        por_prioridade=_contar(Cliente.prioridade),
    )


@router.get(
    "/por-consultor",
    response_model=list[ConsultorResumo],
    summary="Resumo de clientes e faturamento por consultor",
)
def por_consultor(
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConsultorResumo]:
    """
    Retorna lista com total de clientes e faturamento acumulado por consultor.

    Util para visualizar a distribuicao atual da carteira antes de uma
    redistribuicao (FR-022 — Licenca Maternidade Manu Q2 2026).

    R4 — Two-Base: faturamento_total vem APENAS de registros tipo VENDA.
    Requer autenticacao JWT.
    """
    rows = db.execute(
        select(
            Cliente.consultor,
            func.count().label("total"),
            func.coalesce(func.sum(Cliente.faturamento_total), 0.0).label("faturamento"),
        )
        .where(Cliente.consultor.isnot(None))
        .group_by(Cliente.consultor)
        .order_by(func.count().desc())
    ).all()

    return [
        ConsultorResumo(
            consultor=r.consultor,
            total=r.total,
            faturamento=float(r.faturamento),
        )
        for r in rows
    ]


@router.patch(
    "/redistribuir",
    response_model=RedistribuirResponse,
    summary="Redistribuir clientes entre consultores (admin)",
)
def redistribuir_carteira(
    body: RedistribuirPayload,
    user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> RedistribuirResponse:
    """
    Reatribui em lote uma lista de clientes para um novo consultor.

    Regras:
      - Somente role=admin pode executar esta operacao (R12 — L3 aprovado Leandro).
      - novo_consultor deve ser um dos valores validos: MANU, LARISSA, DAIANE, JULIO.
      - Cada CNPJ e normalizado (R5) antes da busca.
      - CNPJs nao encontrados sao retornados na lista de erros sem abortar o lote.
      - Cada alteracao gera registro em audit_logs (campo=consultor).
      - Nao gera log quando o consultor ja e o mesmo (evita audit noise).

    FR-022 — Redistribuicao de Carteira (licenca maternidade Manu Q2 2026).

    Returns:
        RedistribuirResponse com totais processados, atualizados e lista de erros.
    """
    # Validar consultor destino
    novo_consultor = body.novo_consultor.strip().upper()
    if novo_consultor not in _CONSULTORES_VALIDOS:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Consultor '{novo_consultor}' invalido. "
                f"Valores aceitos: {', '.join(sorted(_CONSULTORES_VALIDOS))}"
            ),
        )

    total_processados = len(body.cnpjs)
    total_atualizados = 0
    erros: list[str] = []

    for cnpj_raw in body.cnpjs:
        # R5: normalizar CNPJ — remover pontuacao e zero-pad para 14 digitos
        cnpj_n = re.sub(r"\D", "", str(cnpj_raw)).zfill(14)

        cliente = db.scalar(select(Cliente).where(Cliente.cnpj == cnpj_n))
        if not cliente:
            erros.append(f"CNPJ {cnpj_n} nao encontrado")
            continue

        # Sem mudanca real — pular sem gerar audit noise
        if cliente.consultor == novo_consultor:
            total_atualizados += 1
            continue

        valor_anterior = cliente.consultor
        cliente.consultor = novo_consultor
        total_atualizados += 1

        # Registrar auditoria (R12 — quem, quando, o que mudou)
        audit = AuditLog(
            cnpj=cnpj_n,
            campo="consultor",
            valor_anterior=str(valor_anterior) if valor_anterior is not None else None,
            valor_novo=novo_consultor,
            usuario_id=user.id,
            usuario_nome=getattr(user, "nome", None) or getattr(user, "email", None),
        )
        db.add(audit)

    db.commit()

    return RedistribuirResponse(
        total_processados=total_processados,
        total_atualizados=total_atualizados,
        erros=erros,
    )


# ---------------------------------------------------------------------------
# POST /api/clientes/bulk-update — atualização em massa (admin only)
# ---------------------------------------------------------------------------

# Normalizadores por campo (aplicados nos updates do bulk)
_CAMPO_NORMALIZADORES: dict[str, object] = {
    "consultor": str.upper,
    "rede_regional": lambda v: v.strip(),
    "telefone": lambda v: v.strip()[:20],
    "email": lambda v: v.strip()[:255],
    "cidade": lambda v: v.strip()[:100],
    "uf": lambda v: v.strip().upper()[:2],
    "situacao": str.upper,
    "temperatura": str.upper,
}


@router.post(
    "/bulk-update",
    response_model=BulkUpdateResponse,
    status_code=200,
    summary="Atualizacao em massa de clientes (admin only)",
)
def bulk_update_clientes(
    body: BulkUpdatePayload,
    user: Usuario = Depends(require_admin),
    db: Session = Depends(get_db),
) -> BulkUpdateResponse:
    """
    Atualiza múltiplos clientes em uma única operação (admin only).

    Regras:
      - Máximo 200 CNPJs por batch.
      - Campos permitidos: consultor, rede_regional, telefone, email, cidade, uf, situacao, temperatura.
      - R5: CNPJs normalizados para 14 dígitos.
      - Cada campo alterado gera registro em audit_logs.
      - CNPJs não encontrados são listados em erros sem abortar o batch.
      - R12 — L3: operação aprovada pelo Leandro (admin only).

    Retorna contagem de atualizados e lista de erros por CNPJ.
    """
    total_recebidos = len(body.cnpjs)
    total_atualizados = 0
    erros: list[str] = []

    # Filtrar campos válidos e normalizar valores
    updates_validos: dict[str, str] = {}
    for campo, valor in body.updates.items():
        if campo not in _CAMPOS_BULK_PERMITIDOS:
            continue
        normalizador = _CAMPO_NORMALIZADORES.get(campo, lambda v: v)
        updates_validos[campo] = normalizador(valor)

    if not updates_validos:
        raise HTTPException(
            status_code=422,
            detail=f"Nenhum campo valido em updates. Campos permitidos: {_CAMPOS_BULK_PERMITIDOS}",
        )

    for cnpj_raw in body.cnpjs:
        # R5: normalizar CNPJ
        cnpj_n = re.sub(r"\D", "", str(cnpj_raw)).zfill(14)

        try:
            cliente = db.scalar(select(Cliente).where(Cliente.cnpj == cnpj_n))
            if not cliente:
                erros.append(f"CNPJ {cnpj_n} nao encontrado")
                continue

            campos_alterados = []
            for campo, valor_novo in updates_validos.items():
                valor_anterior = getattr(cliente, campo, None)
                if valor_anterior == valor_novo:
                    continue  # sem mudanca real — evitar audit noise

                setattr(cliente, campo, valor_novo)
                campos_alterados.append(campo)

                audit = AuditLog(
                    cnpj=cnpj_n,
                    campo=campo,
                    valor_anterior=str(valor_anterior) if valor_anterior is not None else None,
                    valor_novo=valor_novo,
                    usuario_id=user.id,
                    usuario_nome=getattr(user, "nome", None) or getattr(user, "email", None),
                )
                db.add(audit)

            if campos_alterados:
                total_atualizados += 1

        except Exception as exc:
            erros.append(f"CNPJ {cnpj_n} erro: {exc!s}")
            continue

    db.commit()

    return BulkUpdateResponse(
        total_recebidos=total_recebidos,
        total_atualizados=total_atualizados,
        erros=erros,
    )


@router.get("/{cnpj}", response_model=ClienteDetalhe, summary="Detalhe de um cliente")
def detalhe_cliente(
    cnpj: str,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ClienteDetalhe:
    """
    Retorna todos os campos de um cliente pelo seu CNPJ (14 digitos, sem pontuacao).
    Retorna 404 se o CNPJ nao existir na base.

    Requer autenticacao JWT.
    """
    # R5: normalizar CNPJ — remover pontuacao e zero-pad para 14 digitos
    cnpj_normalizado = re.sub(r"\D", "", cnpj).zfill(14)

    cliente = db.scalar(select(Cliente).where(Cliente.cnpj == cnpj_normalizado))
    if not cliente:
        raise HTTPException(status_code=404, detail=f"Cliente CNPJ {cnpj_normalizado} nao encontrado.")

    return ClienteDetalhe.model_validate(cliente)


@router.patch(
    "/{cnpj}",
    response_model=ClientePatchResponse,
    summary="Edicao inline de campos do cliente (admin/gerente)",
)
def patch_cliente(
    cnpj: str,
    payload: ClientePatchInput,
    user: Usuario = Depends(require_admin_or_gerente),
    db: Session = Depends(get_db),
) -> ClientePatchResponse:
    """
    Atualiza campos editaveis do cliente inline.

    Campos permitidos:
      - consultor:     reatribuicao de carteira (normalizado para UPPERCASE)
      - rede_regional: alteracao da rede/franquia
      - telefone:      telefone de contato (max 20 chars)
      - email:         e-mail de contato (max 255 chars)
      - cidade:        cidade do cliente (max 100 chars)
      - uf:            unidade federativa (normalizado para UPPERCASE, max 2 chars)

    Cada campo alterado gera um registro em audit_logs com:
      campo, valor_anterior, valor_novo, usuario_id, usuario_nome, created_at

    R5: CNPJ normalizado para 14 digitos.
    R12 — L3: reatribuicao de carteira requer role=admin ou role=gerente.

    Requer autenticacao JWT com role 'admin' ou 'gerente'.

    Returns:
        ClientePatchResponse com cnpj, campos_alterados e cliente atualizado.
    """
    cnpj_n = re.sub(r"\D", "", cnpj).zfill(14)

    cliente = db.scalar(select(Cliente).where(Cliente.cnpj == cnpj_n))
    if not cliente:
        raise HTTPException(status_code=404, detail=f"Cliente CNPJ {cnpj_n} nao encontrado.")

    # Campos editaveis: nome_payload -> (nome_model, normalizador)
    _CAMPOS_EDITAVEIS: dict[str, tuple[str, object]] = {
        "consultor": ("consultor", str.upper),
        "rede_regional": ("rede_regional", lambda v: v.strip()),
        "telefone": ("telefone", lambda v: v.strip()[:20]),
        "email": ("email", lambda v: v.strip()[:255]),
        "cidade": ("cidade", lambda v: v.strip()[:100]),
        "uf": ("uf", lambda v: v.strip().upper()[:2]),
    }

    campos_alterados: list[str] = []

    for campo_payload, (campo_model, normalizar) in _CAMPOS_EDITAVEIS.items():
        valor_enviado = getattr(payload, campo_payload)
        if valor_enviado is None:
            # Campo nao enviado no payload — ignorar
            continue

        valor_normalizado = normalizar(valor_enviado)
        valor_anterior = getattr(cliente, campo_model)

        if valor_anterior == valor_normalizado:
            # Sem mudanca real — nao gerar log desnecessario
            continue

        # Aplicar alteracao no model
        setattr(cliente, campo_model, valor_normalizado)
        campos_alterados.append(campo_payload)

        # Registrar auditoria (R12 — quem, quando, o que mudou)
        audit = AuditLog(
            cnpj=cnpj_n,
            campo=campo_payload,
            valor_anterior=str(valor_anterior) if valor_anterior is not None else None,
            valor_novo=valor_normalizado,
            usuario_id=user.id,
            usuario_nome=getattr(user, "nome", None) or getattr(user, "email", None),
        )
        db.add(audit)

    if campos_alterados:
        db.commit()
        db.refresh(cliente)

    return ClientePatchResponse(
        cnpj=cnpj_n,
        campos_alterados=campos_alterados,
        cliente=ClienteDetalhe.model_validate(cliente),
    )


@router.get(
    "/{cnpj}/score",
    summary="Score atual com breakdown dos 6 fatores v2",
)
def score_breakdown_cliente(
    cnpj: str,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """
    Retorna o score atual do cliente com breakdown completo dos 6 fatores v2.

    Estrutura de resposta:
      score_total: float (0-100)
      prioridade:  string (P0-P7)
      fatores:
        urgencia:  {valor, peso, contribuicao}   — 30% do score
        valor:     {valor, peso, contribuicao}   — 25% do score
        followup:  {valor, peso, contribuicao}   — 20% do score
        sinal:     {valor, peso, contribuicao}   — 15% do score
        tentativa: {valor, peso, contribuicao}   —  5% do score
        situacao:  {valor, peso, contribuicao}   —  5% do score

    Recalcula on-the-fly a partir dos campos atuais do cliente.
    Nao persiste — apenas exibe o calculo atual para visualizacao no frontend.

    R5: CNPJ normalizado para 14 digitos antes da consulta.
    Requer autenticacao JWT.
    """
    cnpj_n = re.sub(r"\D", "", cnpj).zfill(14)
    cliente = db.scalar(select(Cliente).where(Cliente.cnpj == cnpj_n))
    if not cliente:
        raise HTTPException(status_code=404, detail=f"Cliente CNPJ {cnpj_n} nao encontrado.")

    resultado = score_service.calcular(cliente)

    def _fator(nome_fator: str, chave_resultado: str) -> dict:
        """Monta dict {valor, peso, contribuicao} para um fator."""
        valor = resultado[chave_resultado]
        peso = PESOS[nome_fator]
        return {
            "valor": valor,
            "peso": peso,
            "contribuicao": round(valor * peso, 2),
        }

    return {
        "cnpj": cnpj_n,
        "score_total": resultado["score"],
        "prioridade": resultado["prioridade_curta"],
        "fatores": {
            "urgencia": _fator("URGENCIA", "fator_urgencia"),
            "valor": _fator("VALOR", "fator_valor"),
            "followup": _fator("FOLLOWUP", "fator_followup"),
            "sinal": _fator("SINAL", "fator_sinal"),
            "tentativa": _fator("TENTATIVA", "fator_tentativa"),
            "situacao": _fator("SITUACAO", "fator_situacao"),
        },
    }


@router.get(
    "/{cnpj}/score-history",
    summary="Evolucao do score ao longo do tempo",
)
def score_history(
    cnpj: str,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Retorna o historico de score de um cliente ordenado por data decrescente.

    Exibe os ultimos 30 calculos com score, prioridade, sinaleiro e todos os
    fatores de composicao para rastreabilidade e analise de tendencia.

    R5: CNPJ normalizado para 14 digitos antes da consulta.

    Requer autenticacao JWT.
    """
    from backend.app.models.score_historico import ScoreHistorico  # noqa: PLC0415

    cnpj_n = re.sub(r"\D", "", cnpj).zfill(14)

    historico = (
        db.query(ScoreHistorico)
        .filter(ScoreHistorico.cnpj == cnpj_n)
        .order_by(ScoreHistorico.data_calculo.desc())
        .limit(30)
        .all()
    )

    return [
        {
            "data": h.data_calculo.isoformat(),
            "score": h.score,
            "prioridade": h.prioridade,
            "sinaleiro": h.sinaleiro,
            "fator_fase": h.fator_fase,
            "fator_sinaleiro": h.fator_sinaleiro,
            "fator_curva": h.fator_curva,
            "fator_temperatura": h.fator_temperatura,
            "fator_tipo_cliente": h.fator_tipo_cliente,
            "fator_tentativas": h.fator_tentativas,
        }
        for h in historico
    ]


@router.get(
    "/{cnpj}/timeline",
    summary="Timeline unificada: vendas + interacoes de um cliente",
)
def timeline_cliente(
    cnpj: str,
    user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[dict]:
    """
    Retorna a timeline unificada de um cliente ordenada por data decrescente.

    Combina dois tipos de evento:
      - VENDA: registros da tabela vendas (valor_pedido, data_pedido)
      - INTERACAO: registros de log_interacoes (resultado, descricao, temperatura)

    R4 — Two-Base Architecture: vendas e interacoes ficam em tabelas separadas.
    Esta rota apenas EXIBE os dois tipos juntos; nao mistura valores monetarios.
    R5: CNPJ normalizado para 14 digitos antes da consulta.

    Requer autenticacao JWT.
    """
    # R5: normalizar CNPJ
    cnpj_n = re.sub(r"\D", "", cnpj).zfill(14)

    # Verificar existencia do cliente (retorna 404 limpo)
    existe = db.scalar(select(func.count()).select_from(Cliente).where(Cliente.cnpj == cnpj_n))
    if not existe:
        raise HTTPException(status_code=404, detail=f"Cliente CNPJ {cnpj_n} nao encontrado.")

    vendas = db.query(Venda).filter(Venda.cnpj == cnpj_n).all()
    logs = db.query(LogInteracao).filter(LogInteracao.cnpj == cnpj_n).all()

    timeline: list[dict] = []

    for v in vendas:
        timeline.append({
            "tipo": "VENDA",
            "data": v.data_pedido.isoformat() if v.data_pedido else None,
            "valor": v.valor_pedido,
            "consultor": v.consultor,
            "descricao": f"Pedido {v.numero_pedido or ''} - R$ {v.valor_pedido:,.2f}".strip(),
            "fonte": v.fonte,
            "classificacao": v.classificacao_3tier,
        })

    for l in logs:
        timeline.append({
            "tipo": "INTERACAO",
            "data": l.data_interacao.isoformat() if l.data_interacao else None,
            "resultado": l.resultado,
            "consultor": l.consultor,
            "descricao": l.descricao or l.resultado,
            "fase": l.fase,
            "temperatura": l.temperatura,
            "estagio_funil": l.estagio_funil,
        })

    # Ordenar por data decrescente; eventos sem data ficam no fim
    timeline.sort(key=lambda x: x.get("data") or "", reverse=True)

    return timeline
