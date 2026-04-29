"""
CRM VITAO360 — Testes de regressao para filtro de canal em /api/clientes.

Cobre:
  - GET /api/clientes?canal_id=<n> retorna apenas clientes desse canal
  - GET /api/clientes?canal_id=<n> com n inexistente retorna lista vazia (nao 500)
  - Filtro combinado canal_id + consultor funciona corretamente
  - canal_id=None (ausente) retorna todos os clientes (admin)

ROOT CAUSE corrigido: frontend nao passava canal_id para fetchClientes.
Fix: canal_id adicionado a ClientesParams em api.ts e propagado na chamada.
"""

from __future__ import annotations

import pytest

from backend.app.models.canal import Canal
from backend.app.models.cliente import Cliente


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _seed_canal(db, nome: str, status: str = "ATIVO") -> Canal:
    """Insere canal no banco de teste SQLite e retorna o objeto persistido."""
    canal = Canal(nome=nome, status=status)
    db.add(canal)
    db.flush()  # popula canal.id gerado pelo autoincrement
    return canal


def _seed_cliente(db, cnpj: str, canal_id: int | None = None,
                  consultor: str = "MANU", situacao: str = "ATIVO") -> Cliente:
    """Insere cliente no banco de teste SQLite."""
    c = Cliente(
        cnpj=cnpj,
        nome_fantasia=f"Empresa {cnpj[-4:]}",
        consultor=consultor,
        situacao=situacao,
        sinaleiro="VERDE",
        curva_abc="A",
        canal_id=canal_id,
        classificacao_3tier="REAL",
    )
    db.add(c)
    db.flush()
    return c


# ---------------------------------------------------------------------------
# Test 1 — canal_id retorna apenas clientes desse canal
# ---------------------------------------------------------------------------

class TestFiltroCanalId:

    def test_canal_id_retorna_clientes_do_canal(self, client_admin, db):
        """GET /api/clientes?canal_id=<food_id> deve retornar somente clientes desse canal."""
        canal_interno = _seed_canal(db, "INTERNO")
        canal_food    = _seed_canal(db, "FOOD_SERVICE")
        db.commit()

        _seed_cliente(db, "11111111000101", canal_id=canal_interno.id)
        _seed_cliente(db, "22222222000102", canal_id=canal_food.id)
        _seed_cliente(db, "33333333000103", canal_id=canal_food.id)
        _seed_cliente(db, "44444444000104", canal_id=None)
        db.commit()

        resp = client_admin.get(f"/api/clientes?canal_id={canal_food.id}")
        assert resp.status_code == 200
        data = resp.json()

        cnpjs = [r["cnpj"] for r in data["registros"]]
        assert "22222222000102" in cnpjs
        assert "33333333000103" in cnpjs
        assert "11111111000101" not in cnpjs
        assert "44444444000104" not in cnpjs
        assert data["total"] == 2

    def test_canal_id_inexistente_retorna_lista_vazia(self, client_admin, db):
        """GET /api/clientes?canal_id=999 deve retornar lista vazia, nao 500."""
        canal = _seed_canal(db, "INTERNO")
        _seed_cliente(db, "11111111000101", canal_id=canal.id)
        db.commit()

        resp = client_admin.get("/api/clientes?canal_id=99999")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["registros"] == []

    def test_sem_canal_id_retorna_todos(self, client_admin, db):
        """GET /api/clientes sem canal_id (admin) deve retornar todos os clientes."""
        canal_interno = _seed_canal(db, "INTERNO")
        canal_food    = _seed_canal(db, "FOOD_SERVICE")
        db.commit()

        _seed_cliente(db, "11111111000101", canal_id=canal_interno.id)
        _seed_cliente(db, "22222222000102", canal_id=canal_food.id)
        _seed_cliente(db, "33333333000103", canal_id=None)
        db.commit()

        resp = client_admin.get("/api/clientes")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3

    def test_filtro_combinado_canal_e_consultor(self, client_admin, db):
        """GET /api/clientes?canal_id=<n>&consultor=LARISSA deve retornar apenas cruzamento."""
        canal_food = _seed_canal(db, "FOOD_SERVICE")
        db.commit()

        _seed_cliente(db, "11111111000101", canal_id=canal_food.id, consultor="MANU")
        _seed_cliente(db, "22222222000102", canal_id=canal_food.id, consultor="LARISSA")
        _seed_cliente(db, "33333333000103", canal_id=canal_food.id, consultor="LARISSA")
        db.commit()

        resp = client_admin.get(f"/api/clientes?canal_id={canal_food.id}&consultor=LARISSA")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        cnpjs = [r["cnpj"] for r in data["registros"]]
        assert "22222222000102" in cnpjs
        assert "33333333000103" in cnpjs
        assert "11111111000101" not in cnpjs
