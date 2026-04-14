"""
CRM VITAO360 — Schemas de paginação padronizada.

Define o contrato de paginação server-side consistente para todos os endpoints
de listagem do CRM. O formato segue o padrão 1-based (page=1 é a primeira página).

Backward compatibility:
  Os endpoints que já aceitam limit/offset continuam aceitando esses parâmetros.
  Quando page/per_page são informados, têm precedência sobre limit/offset.
  Quando apenas limit/offset são informados, são convertidos internamente para
  page/per_page equivalente.

Uso:
    from backend.app.schemas.pagination import PaginationParams, paginate_query

    params = PaginationParams(page=2, per_page=25)
    result = paginate_query(query, db, params)  # -> PaginatedResponse[T]
"""

from __future__ import annotations

import math
from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, Field, model_validator

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Parâmetros de paginação
# ---------------------------------------------------------------------------

class PaginationParams(BaseModel):
    """
    Parâmetros de paginação server-side padronizados.

    Aceita page/per_page (padrão) ou limit/offset (backward compat).
    page é 1-based: page=1 retorna os primeiros per_page itens.
    """

    page: int = Field(default=1, ge=1, description="Página atual (1-based)")
    per_page: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Itens por página (máximo 200)",
    )

    @property
    def offset(self) -> int:
        """Calcula o offset SQL equivalente."""
        return (self.page - 1) * self.per_page

    @property
    def limit(self) -> int:
        """Alias para per_page (compatibilidade interna)."""
        return self.per_page

    @classmethod
    def from_limit_offset(
        cls,
        limit: int = 50,
        offset: int = 0,
        per_page: Optional[int] = None,
        page: Optional[int] = None,
    ) -> "PaginationParams":
        """
        Constrói PaginationParams a partir de qualquer combinação de parâmetros.

        Prioridade: page/per_page > limit/offset.
        Permite que endpoints aceitem ambas as convenções sem duplicar lógica.
        """
        if page is not None or per_page is not None:
            return cls(
                page=page or 1,
                per_page=per_page or 50,
            )
        # Converter limit/offset para page/per_page
        effective_limit = min(max(limit, 1), 200)
        effective_page = (offset // effective_limit) + 1 if effective_limit else 1
        return cls(page=effective_page, per_page=effective_limit)


# ---------------------------------------------------------------------------
# Resposta paginada
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel, Generic[T]):
    """
    Envelope de resposta paginada padronizado.

    Campos:
      items:    lista de itens da página atual
      total:    total de itens (sem paginação)
      page:     página atual (1-based)
      per_page: itens por página solicitados
      pages:    total de páginas = ceil(total / per_page)
      has_next: True se há página seguinte
      has_prev: True se há página anterior

    Compatibilidade de leitura: o frontend que usa limit/offset pode ignorar
    page/per_page e usar apenas items + total; o comportamento é idêntico.
    """

    items: list[T]
    total: int
    page: int
    per_page: int
    pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def build(
        cls,
        items: list[T],
        total: int,
        params: PaginationParams,
    ) -> "PaginatedResponse[T]":
        """
        Constrói PaginatedResponse a partir de items, total e params.

        Garante que pages >= 1 mesmo quando total == 0.
        """
        pages = max(math.ceil(total / params.per_page) if params.per_page else 1, 1)
        return cls(
            items=items,
            total=total,
            page=params.page,
            per_page=params.per_page,
            pages=pages,
            has_next=params.page < pages,
            has_prev=params.page > 1,
        )
