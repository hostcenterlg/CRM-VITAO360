"""
CRM VITAO360 — Testes de unicidade de venda_itens (Pré-Fase MASTER_PLAN_v3).

Contexto: Audit B4 (sessao 29/Abr/2026) detectou 2.159 pares duplicados em
venda_itens (2.922 linhas extras). Migration 4ac6e4064fa0 removeu as duplicatas
e adicionou UNIQUE constraint (venda_id, produto_id).

Este arquivo verifica:
  Test 1: banco PROD (Neon) nao tem pares duplicados apos migration
  Test 2: inserir par duplicado levanta IntegrityError (constraint ativa)
  Test 3: ON CONFLICT DO NOTHING no ingest_sales_hunter nao levanta excecao
          ao tentar inserir par ja existente (idempotencia defensiva)

Padrão de fixtures: SQLite in-memory para testes 2 e 3 (isolamento).
Teste 1 usa DATABASE_URL real via env var — skipado se nao disponivel.
"""

from __future__ import annotations

import os
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import StaticPool, create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from backend.app.database import Base
from backend.app.models.cliente import Cliente
from backend.app.models.produto import Produto
from backend.app.models.venda import Venda
from backend.app.models.venda_item import VendaItem


# ---------------------------------------------------------------------------
# Fixtures compartilhadas — SQLite in-memory
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def engine_sqlite():
    """Isolated SQLite in-memory engine with full schema."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine_sqlite) -> Session:
    """SQLAlchemy session over the in-memory engine."""
    _Session = sessionmaker(bind=engine_sqlite)
    session = _Session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def seed_venda(db_session) -> tuple[Venda, Produto]:
    """Semeia 1 cliente, 1 produto e 1 venda para uso nos testes de itens."""
    cliente = Cliente(
        cnpj="12345678000199",
        nome_fantasia="Test Loja",
        razao_social="Test Loja LTDA",
        uf="PR",
        cidade="Curitiba",
        consultor="MANU",
        situacao="ATIVO",
        classificacao_3tier="REAL",
        curva_abc="A",
        tipo_cliente="MADURO",
        temperatura="QUENTE",
        sinaleiro="VERDE",
        score=70.0,
        prioridade="P4",
        faturamento_total=5000.0,
        dias_sem_compra=10,
        ciclo_medio=30.0,
        n_compras=5,
    )
    db_session.add(cliente)
    db_session.flush()

    produto = Produto(
        codigo="PROD-001",
        nome="Produto Teste",
        fabricante="VITAO",
        unidade="UN",
        preco_tabela=100.0,
        preco_minimo=80.0,
        comissao_pct=5.0,
        ipi_pct=0.0,
        ativo=True,
    )
    db_session.add(produto)
    db_session.flush()

    venda = Venda(
        cnpj=cliente.cnpj,
        data_pedido=date(2026, 4, 1),
        numero_pedido="PED-UNIQUE-001",
        valor_pedido=500.0,
        consultor="MANU",
        fonte="SAP",
        classificacao_3tier="REAL",
        mes_referencia="2026-04",
    )
    db_session.add(venda)
    db_session.commit()
    db_session.refresh(venda)
    db_session.refresh(produto)

    return venda, produto


# ---------------------------------------------------------------------------
# Test 1 — PROD: zero pares duplicados apos migration
# ---------------------------------------------------------------------------

class TestProdNoDuplicates:
    """Conecta ao Neon PROD e verifica que nao ha pares duplicados.

    Skipado automaticamente se DATABASE_URL_UNPOOLED nao estiver definido
    (ex.: ambientes CI sem acesso ao banco remoto).
    """

    @pytest.mark.skipif(
        not (os.environ.get("DATABASE_URL_UNPOOLED") or os.environ.get("DATABASE_URL")),
        reason="DATABASE_URL nao disponivel — teste PROD skipado",
    )
    def test_no_duplicate_pairs_in_prod(self):
        """Garante que pares_duplicados = 0 apos migration 4ac6e4064fa0."""
        # Carregar .env.local se existir (ambiente local)
        env_local = Path(__file__).resolve().parents[2] / ".env.local"
        if env_local.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(str(env_local), override=False)
            except ImportError:
                pass

        db_url = os.environ.get("DATABASE_URL_UNPOOLED") or os.environ.get("DATABASE_URL")
        # Remove aspas caso venham do .env.local
        db_url = db_url.strip('"').strip("'")

        engine = create_engine(db_url, pool_pre_ping=True)
        with engine.connect() as conn:
            pares_dup = conn.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT venda_id, produto_id
                    FROM venda_itens
                    GROUP BY venda_id, produto_id
                    HAVING COUNT(*) > 1
                ) AS dup
            """)).scalar()

            linhas_extras = conn.execute(text("""
                SELECT COUNT(*) FROM venda_itens vi
                WHERE vi.id > (
                    SELECT MIN(id) FROM venda_itens v2
                    WHERE v2.venda_id = vi.venda_id
                      AND v2.produto_id = vi.produto_id
                )
            """)).scalar()

        assert pares_dup == 0, (
            f"FALHA: {pares_dup} pares duplicados encontrados em venda_itens PROD. "
            "Migration 4ac6e4064fa0 deveria ter removido todas as duplicatas."
        )
        assert linhas_extras == 0, (
            f"FALHA: {linhas_extras} linhas extras encontradas em venda_itens PROD."
        )
        engine.dispose()


# ---------------------------------------------------------------------------
# Test 2 — IntegrityError ao inserir par duplicado
# ---------------------------------------------------------------------------

class TestUniqueConstraintEnforcement:
    """Verifica que a UNIQUE constraint (venda_id, produto_id) esta ativa."""

    def test_duplicate_insert_raises_integrity_error(self, db_session, seed_venda):
        """Inserir dois VendaItems com mesmo (venda_id, produto_id) levanta IntegrityError."""
        venda, produto = seed_venda

        item1 = VendaItem(
            venda_id=venda.id,
            produto_id=produto.id,
            quantidade=2.0,
            preco_unitario=100.0,
            desconto_pct=0.0,
            valor_total=200.0,
        )
        db_session.add(item1)
        db_session.commit()

        # Segunda insercao com o mesmo par (venda_id, produto_id)
        item2 = VendaItem(
            venda_id=venda.id,
            produto_id=produto.id,
            quantidade=1.0,
            preco_unitario=100.0,
            desconto_pct=0.0,
            valor_total=100.0,
        )
        db_session.add(item2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_different_pairs_allowed(self, db_session, seed_venda):
        """Dois produtos diferentes na mesma venda sao permitidos."""
        venda, produto1 = seed_venda

        produto2 = Produto(
            codigo="PROD-002",
            nome="Produto Teste 2",
            fabricante="VITAO",
            unidade="UN",
            preco_tabela=50.0,
            preco_minimo=40.0,
            comissao_pct=5.0,
            ipi_pct=0.0,
            ativo=True,
        )
        db_session.add(produto2)
        db_session.flush()

        item1 = VendaItem(
            venda_id=venda.id,
            produto_id=produto1.id,
            quantidade=2.0,
            preco_unitario=100.0,
            desconto_pct=0.0,
            valor_total=200.0,
        )
        item2 = VendaItem(
            venda_id=venda.id,
            produto_id=produto2.id,
            quantidade=1.0,
            preco_unitario=50.0,
            desconto_pct=0.0,
            valor_total=50.0,
        )
        db_session.add_all([item1, item2])
        db_session.commit()

        count = db_session.execute(
            text("SELECT COUNT(*) FROM venda_itens WHERE venda_id = :vid"),
            {"vid": venda.id},
        ).scalar()
        assert count == 2, f"Esperado 2 itens distintos, encontrado {count}"


# ---------------------------------------------------------------------------
# Test 3 — ON CONFLICT DO NOTHING (idempotencia defensiva)
# ---------------------------------------------------------------------------

class TestOnConflictDoNothing:
    """Verifica que ON CONFLICT DO NOTHING nao levanta excecao em SQLite.

    SQLite suporta INSERT OR IGNORE (equivalente semantico).
    Este teste usa raw SQL para simular o comportamento do ingest.
    """

    def test_on_conflict_do_nothing_is_idempotent(self, db_session, seed_venda):
        """Inserir o mesmo par duas vezes com ON CONFLICT nao levanta erro."""
        venda, produto = seed_venda

        insert_sql = text("""
            INSERT OR IGNORE INTO venda_itens
              (venda_id, produto_id, quantidade, preco_unitario, desconto_pct, valor_total)
            VALUES
              (:venda_id, :produto_id, :qtd, :preco, 0.0, :total)
        """)

        params = {
            "venda_id": venda.id,
            "produto_id": produto.id,
            "qtd": 3.0,
            "preco": 100.0,
            "total": 300.0,
        }

        # Primeira insercao — deve persistir
        db_session.execute(insert_sql, params)
        db_session.commit()

        # Segunda insercao do mesmo par — deve ser silenciada (nao levanta erro)
        db_session.execute(insert_sql, params)
        db_session.commit()

        count = db_session.execute(
            text("SELECT COUNT(*) FROM venda_itens WHERE venda_id = :vid AND produto_id = :pid"),
            {"vid": venda.id, "pid": produto.id},
        ).scalar()
        assert count == 1, (
            f"Esperado exatamente 1 registro apos ON CONFLICT DO NOTHING, encontrado {count}"
        )
