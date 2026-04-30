"""
CRM VITAO360 — Tests DDE Engine (Onda 3 — OSCAR)

Cobertura:
  1. Smoke: calcula_dre_comercial retorna ResultadoDDE com 21 linhas DRE + 9 indicadores
  2. L1: SUM(valor_pedido) bate com vendas mock
  3. L11 = L3 − L4 − L5 − L6 − L7 − L8 (numericamente)
  4. L21 = L11 − L14 − L15 − L16 − L17 − L18(0) − L19 − L20
  5. Idempotência: chamar 2x produz mesmo resultado
  6. Cliente sem dados: retorna ResultadoDDE com majority PENDENTE/NULL
  7. Canal scoping: helper retorna False para canal não elegível
  8. CNPJ normalizado internamente (com pontuação → 14 dígitos)
  9. Classificação 3-tier: linhas REAL/SINTETICO/PENDENTE/NULL conforme spec

Pattern: mesmo estilo de test_score.py — SQLite in-memory via conftest fixtures.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy.orm import Session

from backend.app.models.cliente import Cliente
from backend.app.models.cliente_dre import ClienteDrePeriodo
from backend.app.models.cliente_frete import ClienteFretesMensal
from backend.app.models.cliente_promotor import ClientePromotorMensal
from backend.app.models.cliente_verba import ClienteVerbaAnual
from backend.app.models.debito_cliente import DebitoCliente
from backend.app.models.venda import Venda
from backend.app.services.dde_engine import (
    LinhaDRE,
    ResultadoDDE,
    calcula_dre_comercial,
    cliente_elegivel_dde,
    normaliza_cnpj,
)


# ---------------------------------------------------------------------------
# Fixtures auxiliares
# ---------------------------------------------------------------------------

CNPJ_TEST = "12345678000199"
ANO_TEST = 2025


@pytest.fixture
def cliente_dde(db: Session) -> Cliente:
    """Cliente com campos D1 preenchidos e canal mock."""
    c = Cliente(
        cnpj=CNPJ_TEST,
        nome_fantasia="DDE Test Store",
        razao_social="DDE Test Store LTDA",
        uf="SC",
        cidade="Joinville",
        consultor="MANU",
        situacao="ATIVO",
        classificacao_3tier="REAL",
        faturamento_total=50000.0,
        # D1 fields
        desc_comercial_pct=5.0,    # 5%
        desc_financeiro_pct=2.0,   # 2%
        total_bonificacao=1200.00,
        ipi_total=800.00,
        total_devolucao=500.00,
        pct_devolucao=0.01,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


@pytest.fixture
def vendas_dde(db: Session, cliente_dde: Cliente) -> list[Venda]:
    """3 vendas no ANO_TEST para o cliente DDE."""
    vendas = [
        Venda(cnpj=CNPJ_TEST, data_pedido=date(ANO_TEST, 1, 10),
              valor_pedido=10000.00, consultor="MANU", fonte="SAP",
              classificacao_3tier="REAL"),
        Venda(cnpj=CNPJ_TEST, data_pedido=date(ANO_TEST, 6, 15),
              valor_pedido=15000.00, consultor="MANU", fonte="SAP",
              classificacao_3tier="REAL"),
        Venda(cnpj=CNPJ_TEST, data_pedido=date(ANO_TEST, 11, 20),
              valor_pedido=25000.00, consultor="MANU", fonte="SAP",
              classificacao_3tier="REAL"),
    ]
    db.add_all(vendas)
    db.commit()
    return vendas


@pytest.fixture
def frete_dde(db: Session, cliente_dde: Cliente) -> ClienteFretesMensal:
    """Frete anual para o cliente DDE."""
    frete = ClienteFretesMensal(
        cnpj=CNPJ_TEST,
        ano=ANO_TEST,
        mes=1,
        qtd_ctes=12,
        valor_brl=3000.00,
        fonte="LOG_UPLOAD",
        classificacao="REAL",
    )
    db.add(frete)
    db.commit()
    return frete


@pytest.fixture
def verba_dde(db: Session, cliente_dde: Cliente) -> ClienteVerbaAnual:
    """Verba efetivada para o cliente DDE."""
    verba = ClienteVerbaAnual(
        cnpj=CNPJ_TEST,
        ano=ANO_TEST,
        tipo="EFETIVADA",
        valor_brl=5000.00,
        fonte="LOG_UPLOAD",
        classificacao="REAL",
    )
    db.add(verba)
    db.commit()
    return verba


@pytest.fixture
def promotor_dde(db: Session, cliente_dde: Cliente) -> ClientePromotorMensal:
    """Promotor PDV para o cliente DDE."""
    prom = ClientePromotorMensal(
        cnpj=CNPJ_TEST,
        agencia="AGENCIA XYZ",
        ano=ANO_TEST,
        mes=1,
        valor_brl=1500.00,
        fonte="LOG_UPLOAD",
        classificacao="REAL",
    )
    db.add(prom)
    db.commit()
    return prom


@pytest.fixture
def debito_dde(db: Session, cliente_dde: Cliente) -> DebitoCliente:
    """Débito vencido para testar L19."""
    debito = DebitoCliente(
        cnpj=CNPJ_TEST,
        nro_nfe="NF-001",
        parcela="1",
        data_vencimento=date(ANO_TEST, 3, 1),
        valor=2000.00,
        dias_atraso=45,
        status="VENCIDO",
        classificacao_3tier="REAL",
    )
    db.add(debito)
    db.commit()
    return debito


# ---------------------------------------------------------------------------
# 1. SMOKE TEST
# ---------------------------------------------------------------------------

class TestDDESmoke:
    """Smoke: engine retorna estrutura correta."""

    def test_retorna_resultado_dde(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        assert isinstance(r, ResultadoDDE)

    def test_resultado_tem_cnpj_correto(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        assert r.cnpj == CNPJ_TEST

    def test_resultado_tem_ano_correto(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        assert r.ano == ANO_TEST

    def test_tem_pelo_menos_21_linhas_dre(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        # L1..L21 = 21 linhas (L10a, L10b, L10c contam separadas)
        assert len(r.linhas) >= 21

    def test_tem_9_indicadores(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        for i in range(1, 10):
            assert f"I{i}" in r.indicadores, f"Indicador I{i} ausente"

    def test_veredito_nao_vazio(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        assert r.veredito in {
            "SAUDAVEL", "REVISAR", "RENEGOCIAR", "SUBSTITUIR",
            "ALERTA_CREDITO", "SEM_DADOS"
        }

    def test_fase_ativa_A(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        assert r.fase_ativa == "A"

    def test_cada_linha_tem_codigo_e_conta(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        for linha in r.linhas:
            assert linha.codigo, f"Linha sem codigo: {linha}"
            assert linha.conta, f"Linha sem conta: {linha}"

    def test_cada_linha_tem_classificacao_valida(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        valores_validos = {"REAL", "SINTETICO", "PENDENTE", "NULL"}
        for linha in r.linhas:
            assert linha.classificacao in valores_validos, (
                f"Linha {linha.codigo} tem classificacao inválida: {linha.classificacao}"
            )


# ---------------------------------------------------------------------------
# 2. L1 — SUM(valor_pedido)
# ---------------------------------------------------------------------------

class TestDDEL1:
    """L1: faturamento bruto bate com SUM das vendas mock."""

    def test_l1_bate_com_sum_vendas(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l1 = next(l for l in r.linhas if l.codigo == "L1")
        # SUM: 10000 + 15000 + 25000 = 50000
        assert l1.valor == Decimal("50000.00"), f"L1={l1.valor}, esperado=50000.00"

    def test_l1_classificacao_real(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l1 = next(l for l in r.linhas if l.codigo == "L1")
        assert l1.classificacao == "REAL"

    def test_l1_pct_receita_1(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l1 = next(l for l in r.linhas if l.codigo == "L1")
        # L1/L1 = 100%
        assert l1.pct_receita == 1.0

    def test_l1_sem_vendas_e_none(self, db: Session, cliente_dde):
        """Sem vendas no ano, L1=None."""
        r = calcula_dre_comercial(CNPJ_TEST, 1900, db)
        l1 = next(l for l in r.linhas if l.codigo == "L1")
        assert l1.valor is None

    def test_l1_ignora_outros_anos(self, db: Session, cliente_dde, vendas_dde):
        """L1 não conta vendas de outro ano."""
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST - 1, db)
        l1 = next(l for l in r.linhas if l.codigo == "L1")
        assert l1.valor is None


# ---------------------------------------------------------------------------
# 3. L11 = L3 − L4 − L5 − L6 − L7 − L8
# ---------------------------------------------------------------------------

class TestDDEL11:
    """L11: Receita Líquida Comercial calculada corretamente."""

    def test_l11_formula_numerica(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)

        l_map = {l.codigo: l for l in r.linhas}
        l3 = l_map["L3"].valor or Decimal("0")
        l4 = l_map["L4"].valor or Decimal("0")
        l5 = l_map["L5"].valor or Decimal("0")
        l6 = l_map["L6"].valor or Decimal("0")
        l7 = l_map["L7"].valor or Decimal("0")
        l8 = l_map["L8"].valor or Decimal("0")
        l11_esperado = l3 - l4 - l5 - l6 - l7 - l8

        l11 = l_map["L11"].valor
        assert l11 is not None, "L11 deve ser calculado quando L1 existe"
        assert l11 == l11_esperado, f"L11={l11}, esperado={l11_esperado}"

    def test_l11_classificacao_sintetico(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l11 = next(l for l in r.linhas if l.codigo == "L11")
        assert l11.classificacao == "SINTETICO"

    def test_l11_none_quando_l1_none(self, db: Session, cliente_dde):
        """L11 é None quando L1 não existe."""
        r = calcula_dre_comercial(CNPJ_TEST, 1900, db)
        l11 = next(l for l in r.linhas if l.codigo == "L11")
        assert l11.valor is None

    def test_l5_calculo_pct_de_l1(self, db: Session, cliente_dde, vendas_dde):
        """L5 = desc_comercial_pct (5%) × L1 (50000) = 2500."""
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l5 = next(l for l in r.linhas if l.codigo == "L5")
        assert l5.valor == Decimal("2500.00"), f"L5={l5.valor}, esperado=2500.00"

    def test_l6_calculo_pct_de_l1(self, db: Session, cliente_dde, vendas_dde):
        """L6 = desc_financeiro_pct (2%) × L1 (50000) = 1000."""
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l6 = next(l for l in r.linhas if l.codigo == "L6")
        assert l6.valor == Decimal("1000.00"), f"L6={l6.valor}, esperado=1000.00"


# ---------------------------------------------------------------------------
# 4. L21 = L11 − L14 − L15 − L16 − L17 − L18(0) − L19 − L20
# ---------------------------------------------------------------------------

class TestDDEL21:
    """L21: Margem de Contribuição calculada corretamente."""

    def test_l21_formula_numerica(self, db: Session, cliente_dde, vendas_dde,
                                    frete_dde, verba_dde, promotor_dde, debito_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l_map = {l.codigo: l for l in r.linhas}

        def _s(c: str) -> Decimal:
            v = l_map[c].valor
            return v if v is not None else Decimal("0")

        l21_esperado = (
            _s("L11")
            - _s("L14")
            - _s("L15")
            - _s("L16")
            - _s("L17")
            - Decimal("0")  # L18 = PENDENTE
            - _s("L19")
            - _s("L20")
        )
        l21 = l_map["L21"].valor
        assert l21 is not None, "L21 deve ser calculado quando L11 existe"
        assert l21 == l21_esperado, f"L21={l21}, esperado={l21_esperado}"

    def test_l21_classificacao_sintetico(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l21 = next(l for l in r.linhas if l.codigo == "L21")
        assert l21.classificacao == "SINTETICO"

    def test_l21_none_quando_l11_none(self, db: Session, cliente_dde):
        r = calcula_dre_comercial(CNPJ_TEST, 1900, db)
        l21 = next(l for l in r.linhas if l.codigo == "L21")
        assert l21.valor is None

    def test_l19_captura_debito_vencido(self, db: Session, cliente_dde, vendas_dde, debito_dde):
        """L19 deve refletir débito vencido de R$ 2000."""
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l19 = next(l for l in r.linhas if l.codigo == "L19")
        assert l19.valor == Decimal("2000.00"), f"L19={l19.valor}, esperado=2000.00"

    def test_l14_captura_frete(self, db: Session, cliente_dde, vendas_dde, frete_dde):
        """L14 deve refletir frete de R$ 3000."""
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l14 = next(l for l in r.linhas if l.codigo == "L14")
        assert l14.valor == Decimal("3000.00"), f"L14={l14.valor}, esperado=3000.00"

    def test_l16_captura_verba_efetivada(self, db: Session, cliente_dde, vendas_dde, verba_dde):
        """L16 deve refletir verba EFETIVADA de R$ 5000."""
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l16 = next(l for l in r.linhas if l.codigo == "L16")
        assert l16.valor == Decimal("5000.00"), f"L16={l16.valor}, esperado=5000.00"

    def test_l17_captura_promotor(self, db: Session, cliente_dde, vendas_dde, promotor_dde):
        """L17 deve refletir promotor de R$ 1500."""
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l17 = next(l for l in r.linhas if l.codigo == "L17")
        assert l17.valor == Decimal("1500.00"), f"L17={l17.valor}, esperado=1500.00"


# ---------------------------------------------------------------------------
# 5. Idempotência — cache
# ---------------------------------------------------------------------------

class TestDDEIdempotencia:
    """Chamar 2x produz mesmo resultado e popula cache."""

    def test_resultado_identico_segunda_chamada(self, db: Session, cliente_dde, vendas_dde):
        r1 = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        r2 = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)

        # Mesmo veredito
        assert r1.veredito == r2.veredito

        # Mesmos valores para todas as linhas
        for l1_linha, l2_linha in zip(r1.linhas, r2.linhas):
            assert l1_linha.codigo == l2_linha.codigo
            assert l1_linha.valor == l2_linha.valor, (
                f"Linha {l1_linha.codigo}: primeira={l1_linha.valor}, "
                f"segunda={l2_linha.valor}"
            )

    def test_cache_populado_apos_calculo(self, db: Session, cliente_dde, vendas_dde):
        """Após calcular, cliente_dre_periodo deve ter linhas persistidas."""
        calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)

        from backend.app.models.cliente_dre import ClienteDrePeriodo
        cache_linhas = (
            db.query(ClienteDrePeriodo)
            .filter(
                ClienteDrePeriodo.cnpj == CNPJ_TEST,
                ClienteDrePeriodo.ano == ANO_TEST,
            )
            .all()
        )
        assert len(cache_linhas) >= 21, (
            f"Cache deve ter >= 21 linhas, tem {len(cache_linhas)}"
        )

    def test_cache_atualizado_segunda_chamada(self, db: Session, cliente_dde, vendas_dde):
        """Segunda chamada deve atualizar o cache, não duplicar."""
        calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)

        from backend.app.models.cliente_dre import ClienteDrePeriodo
        count1 = (
            db.query(ClienteDrePeriodo)
            .filter(
                ClienteDrePeriodo.cnpj == CNPJ_TEST,
                ClienteDrePeriodo.ano == ANO_TEST,
            )
            .count()
        )

        calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        count2 = (
            db.query(ClienteDrePeriodo)
            .filter(
                ClienteDrePeriodo.cnpj == CNPJ_TEST,
                ClienteDrePeriodo.ano == ANO_TEST,
            )
            .count()
        )
        assert count1 == count2, (
            f"Segunda chamada duplicou cache: {count1} → {count2}"
        )


# ---------------------------------------------------------------------------
# 6. Cliente sem dados
# ---------------------------------------------------------------------------

class TestDDESemDados:
    """Cliente sem vendas: retorna resultado honesto com PENDENTE/NULL."""

    def test_sem_dados_veredito_sem_dados(self, db: Session):
        """CNPJ sem dados = veredito SEM_DADOS."""
        cnpj_vazio = "99999999000199"
        r = calcula_dre_comercial(cnpj_vazio, ANO_TEST, db)
        assert r.veredito == "SEM_DADOS"

    def test_sem_dados_l1_none(self, db: Session):
        cnpj_vazio = "99999999000199"
        r = calcula_dre_comercial(cnpj_vazio, ANO_TEST, db)
        l1 = next(l for l in r.linhas if l.codigo == "L1")
        assert l1.valor is None

    def test_sem_dados_l21_none(self, db: Session):
        cnpj_vazio = "99999999000199"
        r = calcula_dre_comercial(cnpj_vazio, ANO_TEST, db)
        l21 = next(l for l in r.linhas if l.codigo == "L21")
        assert l21.valor is None

    def test_sem_dados_maioria_pendente(self, db: Session):
        """Com CNPJ sem dados, maioria das linhas deve ser PENDENTE ou NULL."""
        cnpj_vazio = "99999999000199"
        r = calcula_dre_comercial(cnpj_vazio, ANO_TEST, db)
        pendentes = [
            l for l in r.linhas
            if l.classificacao in ("PENDENTE", "NULL")
        ]
        # L9, L10a, L10b, L10c, L12, L13, L18 são sempre NULL/PENDENTE Fase B
        # L1, L11, L21 serão PENDENTE sem dados
        assert len(pendentes) >= 10, (
            f"Esperado >= 10 linhas PENDENTE/NULL, tem {len(pendentes)}"
        )

    def test_linhas_fase_b_sao_null(self, db: Session):
        """Linhas Fase B (impostos, CMV) devem ter classificacao NULL."""
        cnpj_vazio = "99999999000199"
        r = calcula_dre_comercial(cnpj_vazio, ANO_TEST, db)
        l_map = {l.codigo: l for l in r.linhas}

        # L9, L10a, L10b, L10c: NULL (SAP fiscal)
        for codigo in ("L9", "L10a", "L10b", "L10c"):
            assert l_map[codigo].classificacao == "NULL", (
                f"Linha {codigo} deve ser NULL (SAP fiscal), é {l_map[codigo].classificacao}"
            )

        # L12, L13: PENDENTE (aguarda D6)
        for codigo in ("L12", "L13"):
            assert l_map[codigo].classificacao == "PENDENTE", (
                f"Linha {codigo} deve ser PENDENTE (aguarda CMV)"
            )


# ---------------------------------------------------------------------------
# 7. Canal scoping
# ---------------------------------------------------------------------------

class TestDDECanalScoping:
    """cliente_elegivel_dde retorna correto por canal."""

    def test_canal_direto_elegivel(self):
        canal = SimpleNamespace(nome="DIRETO")
        c = SimpleNamespace(canal=canal)
        assert cliente_elegivel_dde(c) is True

    def test_canal_indireto_elegivel(self):
        canal = SimpleNamespace(nome="INDIRETO")
        c = SimpleNamespace(canal=canal)
        assert cliente_elegivel_dde(c) is True

    def test_canal_food_service_elegivel(self):
        canal = SimpleNamespace(nome="FOOD_SERVICE")
        c = SimpleNamespace(canal=canal)
        assert cliente_elegivel_dde(c) is True

    def test_canal_farma_nao_elegivel(self):
        canal = SimpleNamespace(nome="FARMA")
        c = SimpleNamespace(canal=canal)
        assert cliente_elegivel_dde(c) is False

    def test_canal_interno_nao_elegivel(self):
        canal = SimpleNamespace(nome="INTERNO")
        c = SimpleNamespace(canal=canal)
        assert cliente_elegivel_dde(c) is False

    def test_canal_digital_nao_elegivel(self):
        canal = SimpleNamespace(nome="DIGITAL")
        c = SimpleNamespace(canal=canal)
        assert cliente_elegivel_dde(c) is False

    def test_sem_canal_nao_elegivel(self):
        c = SimpleNamespace(canal=None)
        assert cliente_elegivel_dde(c) is False


# ---------------------------------------------------------------------------
# 8. CNPJ normalização
# ---------------------------------------------------------------------------

class TestDDECnpjNormalizacao:
    """R5: CNPJ normalizado internamente."""

    def test_normaliza_cnpj_com_pontuacao(self):
        assert normaliza_cnpj("12.345.678/0001-99") == "12345678000199"

    def test_normaliza_cnpj_com_espacos(self):
        assert normaliza_cnpj("  12345678000199  ") == "12345678000199"

    def test_normaliza_cnpj_curto_zero_pad(self):
        assert normaliza_cnpj("12345") == "00000000012345"

    def test_normaliza_cnpj_ja_normalizado(self):
        assert normaliza_cnpj("12345678000100") == "12345678000100"

    def test_engine_aceita_cnpj_com_pontuacao(self, db: Session, cliente_dde, vendas_dde):
        """Engine normaliza CNPJ internamente."""
        # CNPJ com pontuação que equivale a CNPJ_TEST
        cnpj_formatado = "12.345.678/0001-99"
        r = calcula_dre_comercial(cnpj_formatado, ANO_TEST, db)
        assert r.cnpj == CNPJ_TEST
        l1 = next(l for l in r.linhas if l.codigo == "L1")
        assert l1.valor == Decimal("50000.00")


# ---------------------------------------------------------------------------
# 9. Classificação 3-tier por linha
# ---------------------------------------------------------------------------

class TestDDEClassificacao3Tier:
    """Classificação 3-tier correta por tipo de linha."""

    def test_l4_real_quando_total_devolucao_existe(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l4 = next(l for l in r.linhas if l.codigo == "L4")
        assert l4.classificacao == "REAL"

    def test_l5_sintetico_quando_pct_existe(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l5 = next(l for l in r.linhas if l.codigo == "L5")
        assert l5.classificacao == "SINTETICO"

    def test_l9_l10x_null_fase_b(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        for codigo in ("L9", "L10a", "L10b", "L10c"):
            linha = next(l for l in r.linhas if l.codigo == codigo)
            assert linha.classificacao == "NULL", f"{codigo} deve ser NULL"
            assert linha.fase == "B", f"{codigo} deve ser Fase B"

    def test_l12_l13_pendente_fase_b(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        for codigo in ("L12", "L13"):
            linha = next(l for l in r.linhas if l.codigo == codigo)
            assert linha.classificacao == "PENDENTE"
            assert linha.fase == "B"

    def test_l15_sintetico_comissao_default(self, db: Session, cliente_dde, vendas_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l15 = next(l for l in r.linhas if l.codigo == "L15")
        assert l15.classificacao == "SINTETICO"

    def test_l19_real(self, db: Session, cliente_dde, vendas_dde, debito_dde):
        r = calcula_dre_comercial(CNPJ_TEST, ANO_TEST, db)
        l19 = next(l for l in r.linhas if l.codigo == "L19")
        assert l19.classificacao == "REAL"
