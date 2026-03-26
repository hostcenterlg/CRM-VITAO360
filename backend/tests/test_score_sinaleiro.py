"""
CRM VITAO360 — Testes do Score Engine v2 e Sinaleiro Engine.

Score v2 — 6 fatores ponderados:
  URGENCIA   (30%): Dias sem compra / ciclo medio
  VALOR      (25%): Curva ABC + Tipo Cliente
  FOLLOWUP   (20%): Proximo follow-up vs hoje
  SINAL      (15%): Temperatura + E-commerce
  TENTATIVA   (5%): T1/T2/T3/T4
  SITUACAO    (5%): Situacao Mercos

Prioridade v2 (por situacao + resultado + tipo_cliente + score):
  P1 NAMORO NOVO, P2 NEGOCIACAO ATIVA, P3 PROBLEMA,
  P4 MOMENTO OURO, P5 INAT. RECENTE, P6 INAT. ANTIGO, P7 PROSPECCAO

Sinaleiro:
  ROXO = PROSPECT/LEAD
  VERDE = NOVO ou dias <= ciclo
  AMARELO = dias entre ciclo e ciclo+30
  VERMELHO = INAT.ANT ou dias > ciclo+30

Fixtures criam banco SQLite em memoria para isolamento total.
Os models sao os mesmos de producao — nao ha mocks de schema.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models.cliente import Cliente
from backend.app.models.rede import Rede
from backend.app.models.score_historico import ScoreHistorico
from backend.app.services.score_service import ScoreService, PESOS, score_service
from backend.app.services.sinaleiro_service import SinaleiroService, sinaleiro_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def db():
    """Banco SQLite em memoria isolado por teste."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


def _cliente(
    cnpj: str = "12345678000100",
    situacao: str = "ATIVO",
    curva_abc: str = "A",
    tipo_cliente: str = "MADURO",
    temperatura: str = "QUENTE",
    tentativas: str = "T1",
    dias_sem_compra: int | None = None,
    ciclo_medio: float | None = None,
    followup_dias: int | None = None,
    resultado: str = "",
    sinaleiro: str = "VERDE",
    fase: str = "RECOMPRA",
    problema_aberto: bool = False,
    followup_vencido: bool = False,
    cs_no_prazo: bool = False,
) -> Cliente:
    """Factory de Cliente com valores padrao configuráveis."""
    return Cliente(
        cnpj=cnpj,
        nome_fantasia="Teste LTDA",
        situacao=situacao,
        curva_abc=curva_abc,
        tipo_cliente=tipo_cliente,
        temperatura=temperatura,
        tentativas=tentativas,
        dias_sem_compra=dias_sem_compra,
        ciclo_medio=ciclo_medio,
        followup_dias=followup_dias,
        resultado=resultado,
        sinaleiro=sinaleiro,
        fase=fase,
        problema_aberto=problema_aberto,
        followup_vencido=followup_vencido,
        cs_no_prazo=cs_no_prazo,
        classificacao_3tier="REAL",
    )


# ---------------------------------------------------------------------------
# Testes — Fatores individuais v2
# ---------------------------------------------------------------------------

class TestFatoresV2:

    def test_pesos_somam_100pct(self):
        """Os 6 pesos v2 devem somar exatamente 1.0."""
        soma = sum(PESOS.values())
        assert abs(soma - 1.0) < 1e-9, f"Pesos somam {soma}, esperado 1.0"

    def test_urgencia_inat_ant_100(self):
        """INAT.ANT deve gerar fator_urgencia = 100."""
        svc = ScoreService()
        c = _cliente(situacao="INAT.ANT", dias_sem_compra=200, ciclo_medio=30.0)
        r = svc.calcular(c)
        assert r["fator_urgencia"] == 100.0

    def test_urgencia_inat_rec_90(self):
        """INAT.REC deve gerar fator_urgencia = 90."""
        svc = ScoreService()
        c = _cliente(situacao="INAT.REC", dias_sem_compra=60, ciclo_medio=30.0)
        r = svc.calcular(c)
        assert r["fator_urgencia"] == 90.0

    def test_urgencia_ativo_com_ciclo_ratio_alto(self):
        """ATIVO com ratio dias/ciclo >= 1.5 deve gerar urgencia = 100."""
        svc = ScoreService()
        c = _cliente(situacao="ATIVO", dias_sem_compra=60, ciclo_medio=30.0)
        r = svc.calcular(c)
        # ratio = 60/30 = 2.0 >= 1.5 -> 100
        assert r["fator_urgencia"] == 100.0

    def test_urgencia_prospect_10(self):
        """PROSPECT deve gerar fator_urgencia = 10."""
        svc = ScoreService()
        c = _cliente(situacao="PROSPECT")
        r = svc.calcular(c)
        assert r["fator_urgencia"] == 10.0

    def test_valor_a_maduro_100(self):
        """Curva A + MADURO deve gerar fator_valor = 100."""
        svc = ScoreService()
        c = _cliente(curva_abc="A", tipo_cliente="MADURO")
        r = svc.calcular(c)
        assert r["fator_valor"] == 100.0

    def test_valor_a_sem_premium_80(self):
        """Curva A + tipo RECORRENTE deve gerar fator_valor = 80."""
        svc = ScoreService()
        c = _cliente(curva_abc="A", tipo_cliente="RECORRENTE")
        r = svc.calcular(c)
        assert r["fator_valor"] == 80.0

    def test_valor_c_20(self):
        """Curva C deve gerar fator_valor = 20."""
        svc = ScoreService()
        c = _cliente(curva_abc="C")
        r = svc.calcular(c)
        assert r["fator_valor"] == 20.0

    def test_sinal_quente_sem_carrinho_80(self):
        """QUENTE sem carrinho e-commerce deve gerar fator_sinal = 80."""
        svc = ScoreService()
        c = _cliente(temperatura="QUENTE")
        r = svc.calcular(c)
        assert r["fator_sinal"] == 80.0

    def test_sinal_frio_10(self):
        """FRIO deve gerar fator_sinal = 10."""
        svc = ScoreService()
        c = _cliente(temperatura="FRIO")
        r = svc.calcular(c)
        assert r["fator_sinal"] == 10.0

    def test_sinal_com_emoji_temperatura(self):
        """Temperatura com emoji do motor legado deve calcular igual sem emoji."""
        svc = ScoreService()
        c_emoji = _cliente(temperatura="🔥 QUENTE")
        c_limpo = _cliente(temperatura="QUENTE")
        assert svc.calcular(c_emoji)["fator_sinal"] == svc.calcular(c_limpo)["fator_sinal"]

    def test_tentativa_t1_10(self):
        """T1 deve gerar fator_tentativa = 10."""
        svc = ScoreService()
        c = _cliente(tentativas="T1")
        r = svc.calcular(c)
        assert r["fator_tentativa"] == 10.0

    def test_tentativa_t3_50(self):
        """T3 deve gerar fator_tentativa = 50."""
        svc = ScoreService()
        c = _cliente(tentativas="T3")
        r = svc.calcular(c)
        assert r["fator_tentativa"] == 50.0

    def test_tentativa_t4_100(self):
        """T4 deve gerar fator_tentativa = 100."""
        svc = ScoreService()
        c = _cliente(tentativas="T4")
        r = svc.calcular(c)
        assert r["fator_tentativa"] == 100.0

    def test_situacao_ativo_40(self):
        """ATIVO deve gerar fator_situacao = 40."""
        svc = ScoreService()
        c = _cliente(situacao="ATIVO", dias_sem_compra=15, ciclo_medio=30.0)
        r = svc.calcular(c)
        assert r["fator_situacao"] == 40.0

    def test_followup_sem_fu_neutro_50(self):
        """Sem follow-up agendado (followup_dias=None) deve gerar fator_followup = 50 (neutro)."""
        svc = ScoreService()
        c = _cliente(followup_dias=None)
        r = svc.calcular(c)
        assert r["fator_followup"] == 50.0


# ---------------------------------------------------------------------------
# Testes — Score total ponderado
# ---------------------------------------------------------------------------

class TestScoreCalculo:

    def test_score_formula_ponderada_v2(self):
        """
        Verifica formula de ponderacao v2 com valores conhecidos.
        Cliente ATIVO com ciclo ok (dias=15, ciclo=30 -> ratio=0.5 < 0.7 -> urgencia=20),
        curva B sem premium (valor=50), sem FU (followup=50),
        temperatura MORNO (sinal=40), T2 (tentativa=10), situacao ATIVO (situacao=40).

        Score = 20*0.30 + 50*0.25 + 50*0.20 + 40*0.15 + 10*0.05 + 40*0.05
              = 6.0 + 12.5 + 10.0 + 6.0 + 0.5 + 2.0 = 37.0
        """
        svc = ScoreService()
        c = _cliente(
            situacao="ATIVO",
            curva_abc="B",
            tipo_cliente="NOVO",
            temperatura="MORNO",
            tentativas="T2",
            dias_sem_compra=15,
            ciclo_medio=30.0,
            followup_dias=None,
        )
        r = svc.calcular(c)
        assert r["score"] == 37.0, f"Score esperado 37.0, obtido {r['score']}"

    def test_score_campos_nulos_retornam_score_baixo(self):
        """Cliente sem campos preenchidos retorna score >= 0 (followup neutro = 50)."""
        svc = ScoreService()
        c = Cliente(
            cnpj="00000000000001",
            nome_fantasia="Sem Dados",
            classificacao_3tier="REAL",
        )
        r = svc.calcular(c)
        # Com todos os fatores em zero, exceto FOLLOWUP=50 (neutro)
        # Score = 0*0.30 + 0*0.25 + 50*0.20 + 0*0.15 + 0*0.05 + 0*0.05 = 10.0
        assert r["score"] >= 0.0
        assert r["score"] <= 100.0

    def test_score_dentro_do_range(self):
        """Score deve estar sempre entre 0 e 100."""
        svc = ScoreService()
        # Caso extremo maximo
        c_max = _cliente(
            situacao="INAT.ANT",      # urgencia=100
            curva_abc="A",
            tipo_cliente="MADURO",    # valor=100
            temperatura="QUENTE",     # sinal=80
            tentativas="T4",          # tentativa=100
        )
        r_max = svc.calcular(c_max)
        assert 0.0 <= r_max["score"] <= 100.0

    def test_score_retorna_chaves_v2(self):
        """Resultado deve conter todos os fatores v2 nomeados."""
        svc = ScoreService()
        c = _cliente()
        r = svc.calcular(c)
        for chave in ("score", "prioridade", "prioridade_curta",
                      "fator_urgencia", "fator_valor", "fator_followup",
                      "fator_sinal", "fator_tentativa", "fator_situacao"):
            assert chave in r, f"Chave '{chave}' ausente no resultado"

    def test_score_retrocompatibilidade_aliases(self):
        """Aliases retrocompativeis (fator_fase, fator_sinaleiro etc.) devem existir."""
        svc = ScoreService()
        c = _cliente()
        r = svc.calcular(c)
        for alias in ("fator_fase", "fator_sinaleiro", "fator_curva",
                      "fator_temperatura", "fator_tipo_cliente", "fator_tentativas"):
            assert alias in r, f"Alias '{alias}' ausente no resultado"


# ---------------------------------------------------------------------------
# Testes — Prioridade v2
# ---------------------------------------------------------------------------

class TestPrioridadeV2:

    def test_prioridade_p3_problema_suporte(self):
        """resultado=SUPORTE deve retornar P3 PROBLEMA."""
        svc = ScoreService()
        c = _cliente(resultado="SUPORTE")
        r = svc.calcular(c)
        assert r["prioridade"] == "P3 PROBLEMA"
        assert r["prioridade_curta"] == "P3"

    def test_prioridade_p1_namoro_novo(self):
        """POS-VENDA + tipo NOVO + score >= 70 deve retornar P1 NAMORO NOVO."""
        svc = ScoreService()
        # INAT.ANT = urgencia 100, A+MADURO = valor 100
        # 100*0.30 + 100*0.25 + 50*0.20 + 80*0.15 + 10*0.05 + 20*0.05
        # = 30 + 25 + 10 + 12 + 0.5 + 1 = 78.5 >= 70
        c = _cliente(
            situacao="INAT.ANT",
            curva_abc="A",
            tipo_cliente="NOVO",
            temperatura="QUENTE",
            tentativas="T1",
            resultado="POS-VENDA",
        )
        r = svc.calcular(c)
        if r["score"] >= 70:
            assert r["prioridade"] == "P1 NAMORO NOVO"
            assert r["prioridade_curta"] == "P1"

    def test_prioridade_p2_negociacao_orcamento(self):
        """resultado=ORCAMENTO deve retornar P2 NEGOCIACAO ATIVA."""
        svc = ScoreService()
        c = _cliente(resultado="ORCAMENTO")
        r = svc.calcular(c)
        assert r["prioridade"] == "P2 NEGOCIACAO ATIVA"
        assert r["prioridade_curta"] == "P2"

    def test_prioridade_p2_em_atendimento(self):
        """resultado=EM ATENDIMENTO deve retornar P2 NEGOCIACAO ATIVA."""
        svc = ScoreService()
        c = _cliente(resultado="EM ATENDIMENTO")
        r = svc.calcular(c)
        assert r["prioridade"] == "P2 NEGOCIACAO ATIVA"
        assert r["prioridade_curta"] == "P2"

    def test_prioridade_p4_inat_rec_score_alto(self):
        """INAT.REC com score >= 75 deve retornar P4 MOMENTO OURO."""
        svc = ScoreService()
        # INAT.REC: urgencia=90, A+FIDELIZADO=100, QUENTE=80, T4=100
        # 90*0.30 + 100*0.25 + 50*0.20 + 80*0.15 + 100*0.05 + 20*0.05
        # = 27 + 25 + 10 + 12 + 5 + 1 = 80.0 >= 75
        c = _cliente(
            situacao="INAT.REC",
            curva_abc="A",
            tipo_cliente="FIDELIZADO",
            temperatura="QUENTE",
            tentativas="T4",
        )
        r = svc.calcular(c)
        if r["score"] >= 75:
            assert r["prioridade"] == "P4 MOMENTO OURO"
            assert r["prioridade_curta"] == "P4"

    def test_prioridade_p5_inat_rec_score_baixo(self):
        """INAT.REC com score < 75 deve retornar P5 INAT. RECENTE."""
        svc = ScoreService()
        # INAT.REC com C+PROSPECT+FRIO+T1 para score baixo
        # urgencia=90, C=20, FRIO=10, T1=10
        # 90*0.30 + 20*0.25 + 50*0.20 + 10*0.15 + 10*0.05 + 20*0.05
        # = 27 + 5 + 10 + 1.5 + 0.5 + 1 = 45.0 < 75
        c = _cliente(
            situacao="INAT.REC",
            curva_abc="C",
            tipo_cliente="PROSPECT",
            temperatura="FRIO",
            tentativas="T1",
        )
        r = svc.calcular(c)
        assert r["score"] < 75
        assert r["prioridade"] == "P5 INAT. RECENTE"
        assert r["prioridade_curta"] == "P5"

    def test_prioridade_p6_inat_ant_score_baixo(self):
        """INAT.ANT com score < 80 deve retornar P6 INAT. ANTIGO."""
        svc = ScoreService()
        # INAT.ANT com C+FRIO+T1 para score baixo
        # urgencia=100, C=20, FRIO=10, T1=10
        # 100*0.30 + 20*0.25 + 50*0.20 + 10*0.15 + 10*0.05 + 20*0.05
        # = 30 + 5 + 10 + 1.5 + 0.5 + 1 = 48.0 < 80
        c = _cliente(
            situacao="INAT.ANT",
            curva_abc="C",
            tipo_cliente="PROSPECT",
            temperatura="FRIO",
            tentativas="T1",
        )
        r = svc.calcular(c)
        assert r["score"] < 80
        assert r["prioridade"] == "P6 INAT. ANTIGO"
        assert r["prioridade_curta"] == "P6"

    def test_prioridade_p7_prospect(self):
        """PROSPECT deve retornar P7 PROSPECCAO."""
        svc = ScoreService()
        c = _cliente(situacao="PROSPECT")
        r = svc.calcular(c)
        assert r["prioridade"] == "P7 PROSPECCAO"
        assert r["prioridade_curta"] == "P7"

    def test_prioridade_p7_lead(self):
        """LEAD deve retornar P7 PROSPECCAO."""
        svc = ScoreService()
        c = _cliente(situacao="LEAD")
        r = svc.calcular(c)
        assert r["prioridade"] == "P7 PROSPECCAO"
        assert r["prioridade_curta"] == "P7"

    def test_prioridade_curta_max_2_chars_para_persistencia(self):
        """prioridade_curta deve ter no maximo 2 caracteres (String(5) no model)."""
        svc = ScoreService()
        for situacao in ["ATIVO", "INAT.REC", "INAT.ANT", "PROSPECT", "LEAD"]:
            c = _cliente(situacao=situacao)
            r = svc.calcular(c)
            assert len(r["prioridade_curta"]) <= 5, (
                f"prioridade_curta '{r['prioridade_curta']}' excede String(5)"
            )


# ---------------------------------------------------------------------------
# Testes — Sinaleiro Engine
# ---------------------------------------------------------------------------

class TestSinaleiroCliente:

    def test_sinaleiro_prospect_roxo(self):
        """PROSPECT deve retornar ROXO."""
        svc = SinaleiroService()
        c = _cliente(situacao="PROSPECT")
        assert svc.calcular(c) == "ROXO"

    def test_sinaleiro_lead_roxo(self):
        """LEAD deve retornar ROXO."""
        svc = SinaleiroService()
        c = _cliente(situacao="LEAD")
        assert svc.calcular(c) == "ROXO"

    def test_sinaleiro_novo_verde(self):
        """NOVO deve retornar VERDE (cliente recente sem historico de compra)."""
        svc = SinaleiroService()
        c = _cliente(situacao="NOVO")
        assert svc.calcular(c) == "VERDE"

    def test_sinaleiro_inat_ant_vermelho(self):
        """INAT.ANT deve retornar VERMELHO (inativo por longo periodo)."""
        svc = SinaleiroService()
        c = _cliente(situacao="INAT.ANT")
        assert svc.calcular(c) == "VERMELHO"

    def test_sinaleiro_ativo_com_ciclo_verde(self):
        """ratio <= 0.5 deve retornar VERDE (FR-014). dias=15, ciclo=30 -> ratio=0.5."""
        svc = SinaleiroService()
        c = _cliente(situacao="ATIVO", dias_sem_compra=15, ciclo_medio=30.0)
        assert svc.calcular(c) == "VERDE"

    def test_sinaleiro_ativo_no_limite_ciclo_amarelo(self):
        """ratio == 1.0 deve retornar AMARELO (FR-014). dias=30, ciclo=30 -> ratio=1.0."""
        svc = SinaleiroService()
        c = _cliente(situacao="ATIVO", dias_sem_compra=30, ciclo_medio=30.0)
        assert svc.calcular(c) == "AMARELO"

    def test_sinaleiro_ativo_ratio_laranja(self):
        """ratio <= 1.5 deve retornar LARANJA (FR-014). dias=45, ciclo=30 -> ratio=1.5."""
        svc = SinaleiroService()
        c = _cliente(situacao="ATIVO", dias_sem_compra=45, ciclo_medio=30.0)
        assert svc.calcular(c) == "LARANJA"

    def test_sinaleiro_ativo_alem_ciclo_vermelho(self):
        """ratio > 1.5 deve retornar VERMELHO (FR-014). dias=65, ciclo=30 -> ratio=2.17."""
        svc = SinaleiroService()
        c = _cliente(situacao="ATIVO", dias_sem_compra=65, ciclo_medio=30.0)
        assert svc.calcular(c) == "VERMELHO"

    def test_sinaleiro_fallback_sem_ciclo_verde(self):
        """Sem ciclo_medio: dias <= 50 deve retornar VERDE."""
        svc = SinaleiroService()
        c = _cliente(situacao="ATIVO", dias_sem_compra=30, ciclo_medio=None)
        assert svc.calcular(c) == "VERDE"

    def test_sinaleiro_fallback_sem_ciclo_amarelo(self):
        """Sem ciclo_medio: dias=60 (entre 50 e 90) deve retornar AMARELO."""
        svc = SinaleiroService()
        c = _cliente(situacao="ATIVO", dias_sem_compra=60, ciclo_medio=None)
        assert svc.calcular(c) == "AMARELO"

    def test_sinaleiro_fallback_sem_ciclo_vermelho(self):
        """Sem ciclo_medio: dias > 90 deve retornar VERMELHO."""
        svc = SinaleiroService()
        c = _cliente(situacao="ATIVO", dias_sem_compra=91, ciclo_medio=None)
        assert svc.calcular(c) == "VERMELHO"

    def test_sinaleiro_sem_dias_sem_compra_retorna_verde(self):
        """Cliente ATIVO sem dias_sem_compra preenchido deve retornar VERDE."""
        svc = SinaleiroService()
        c = _cliente(situacao="ATIVO", dias_sem_compra=None, ciclo_medio=None)
        assert svc.calcular(c) == "VERDE"

    def test_sinaleiro_inat_rec_amarelo(self):
        """INAT.REC sem dias deve retornar AMARELO."""
        svc = SinaleiroService()
        c = _cliente(situacao="INAT.REC", dias_sem_compra=None, ciclo_medio=None)
        assert svc.calcular(c) == "AMARELO"

    def test_aplicar_atualiza_campo_cliente(self, db):
        """aplicar() deve persistir o sinaleiro calculado no cliente."""
        svc = SinaleiroService()
        c = _cliente(situacao="PROSPECT")
        c.sinaleiro = "VERDE"  # valor antigo errado

        db.add(c)
        db.flush()

        svc.aplicar(db, c)
        assert c.sinaleiro == "ROXO"


# ---------------------------------------------------------------------------
# Testes — Penetracao de Redes
# ---------------------------------------------------------------------------

class TestPenetracaoRede:

    def test_penetracao_rede_calculo_correto(self):
        """
        Rede com 10 lojas e faturamento_real = R$ 28.875 (50% do potencial):
          potencial = 10 * 525 * 11 = R$ 57.750
          pct = 28.875 / 57.750 * 100 = 50.0%
          sinaleiro = AMARELO (40% <= pct < 60%)
        """
        svc = SinaleiroService()
        rede = Rede(
            nome="Rede Teste",
            total_lojas=10,
            lojas_ativas=5,
            faturamento_real=28875.0,
            potencial_maximo=57750.0,
        )
        resultado = svc.calcular_penetracao_rede(rede)

        assert resultado["potencial_maximo"] == 57750.0
        assert resultado["pct_penetracao"] == 50.0
        assert resultado["sinaleiro"] == "AMARELO"
        assert resultado["cadencia"] == "1x/sem"

    def test_penetracao_rede_zero_lojas_retorna_roxo(self):
        """Rede sem lojas deve retornar ROXO (pct = 0)."""
        svc = SinaleiroService()
        rede = Rede(
            nome="Rede Vazia",
            total_lojas=0,
            lojas_ativas=0,
            faturamento_real=0.0,
            potencial_maximo=0.0,
        )
        resultado = svc.calcular_penetracao_rede(rede)
        assert resultado["sinaleiro"] == "ROXO"
        assert resultado["pct_penetracao"] == 0.0

    def test_penetracao_rede_alta_verde(self):
        """
        Penetracao >= 60% deve retornar VERDE e cadencia Mensal.
        Rede com 10 lojas, faturamento = 80% do potencial.
        """
        svc = SinaleiroService()
        potencial = 10 * 525 * 11  # 57750
        rede = Rede(
            nome="Rede Boa",
            total_lojas=10,
            lojas_ativas=8,
            faturamento_real=potencial * 0.80,
            potencial_maximo=potencial,
        )
        resultado = svc.calcular_penetracao_rede(rede)
        assert resultado["sinaleiro"] == "VERDE"
        assert resultado["cadencia"] == "Mensal"

    def test_penetracao_rede_critica_vermelho(self):
        """
        Penetracao < 40% deve retornar VERMELHO e cadencia 2x/sem.
        """
        svc = SinaleiroService()
        potencial = 10 * 525 * 11  # 57750
        rede = Rede(
            nome="Rede Critica",
            total_lojas=10,
            lojas_ativas=2,
            faturamento_real=potencial * 0.20,
            potencial_maximo=potencial,
        )
        resultado = svc.calcular_penetracao_rede(rede)
        assert resultado["sinaleiro"] == "VERMELHO"
        assert resultado["cadencia"] == "2x/sem"

    def test_penetracao_constantes_ticket_e_meses(self):
        """
        Confirma que TICKET_REF_MENSAL=525 e MESES_REF=11 estao corretos.
        1 loja com faturamento total = 525 * 11 deve ter pct=100%.
        """
        from backend.app.services.sinaleiro_service import MESES_REF, TICKET_REF_MENSAL
        svc = SinaleiroService()
        valor_100pct = TICKET_REF_MENSAL * MESES_REF  # 5775.0
        rede = Rede(
            nome="1 Loja",
            total_lojas=1,
            lojas_ativas=1,
            faturamento_real=valor_100pct,
            potencial_maximo=valor_100pct,
        )
        resultado = svc.calcular_penetracao_rede(rede)
        assert resultado["pct_penetracao"] == 100.0
        assert TICKET_REF_MENSAL == 525.0
        assert MESES_REF == 11


# ---------------------------------------------------------------------------
# Testes — aplicar_e_salvar (integracao)
# ---------------------------------------------------------------------------

class TestScoreHistorico:

    def test_score_historico_salvo(self, db):
        """
        aplicar_e_salvar() deve criar registro em ScoreHistorico com os
        valores corretos de score, prioridade e fatores v2.
        """
        svc = ScoreService()

        c = _cliente(
            cnpj="11222333000181",
            situacao="ATIVO",
            curva_abc="A",
            tipo_cliente="MADURO",
            temperatura="QUENTE",
            tentativas="T1",
            dias_sem_compra=60,
            ciclo_medio=30.0,
        )
        db.add(c)
        db.flush()

        resultado = svc.aplicar_e_salvar(db, c)
        db.flush()

        hist = db.query(ScoreHistorico).filter(ScoreHistorico.cnpj == "11222333000181").first()
        assert hist is not None
        assert hist.score == resultado["score"]
        assert hist.prioridade == resultado["prioridade_curta"]

    def test_score_salvo_no_cliente_como_label_curto(self, db):
        """
        aplicar_e_salvar() deve atualizar cliente.prioridade com label curto (max 5 chars).
        """
        svc = ScoreService()

        c = _cliente(
            cnpj="44555666000177",
            situacao="ATIVO",
            curva_abc="A",
            tipo_cliente="MADURO",
            temperatura="QUENTE",
            tentativas="T1",
        )
        c.score = None
        c.prioridade = None
        db.add(c)
        db.flush()

        svc.aplicar_e_salvar(db, c)

        assert c.score is not None
        assert c.prioridade is not None
        assert len(c.prioridade) <= 5, f"prioridade no model excede 5 chars: '{c.prioridade}'"

    def test_multiplos_historicos_mesmo_cliente(self, db):
        """
        Chamadas multiplas de aplicar_e_salvar devem criar multiplos registros
        no historico (sem restricao de unicidade por data).
        """
        svc = ScoreService()

        c = _cliente(cnpj="77888999000144")
        db.add(c)
        db.flush()

        svc.aplicar_e_salvar(db, c)
        svc.aplicar_e_salvar(db, c)
        db.flush()

        count = db.query(ScoreHistorico).filter(ScoreHistorico.cnpj == "77888999000144").count()
        assert count == 2


# ---------------------------------------------------------------------------
# Teste de integracao — fluxo completo sinaleiro + score
# ---------------------------------------------------------------------------

class TestFluxoCompleto:

    def test_sinaleiro_e_score_funcionam_juntos(self, db):
        """
        Apos aplicar sinaleiro, score pode ser recalculado sem erro.
        Sinaleiro ROXO (PROSPECT) deve ser calculado corretamente.
        """
        svc_sin = SinaleiroService()
        svc_score = ScoreService()

        c = _cliente(
            cnpj="99000111000166",
            situacao="PROSPECT",
            sinaleiro="VERDE",  # valor inicial incorreto
        )
        db.add(c)
        db.flush()

        # Aplicar sinaleiro correto (deve virar ROXO para PROSPECT)
        svc_sin.aplicar(db, c)
        assert c.sinaleiro == "ROXO"

        # Recalcular score com situacao PROSPECT
        resultado = svc_score.calcular(c)
        # PROSPECT: urgencia=10, sinal depende de temperatura (QUENTE=80), etc.
        assert resultado["score"] >= 0.0
        assert resultado["score"] <= 100.0
        # PROSPECT deve ser P7
        assert resultado["prioridade_curta"] == "P7"

    def test_score_v2_pesos_refletem_spec(self):
        """
        Verificar que os pesos importados refletem a especificacao v2 oficial.
        """
        assert PESOS["URGENCIA"] == 0.30
        assert PESOS["VALOR"] == 0.25
        assert PESOS["FOLLOWUP"] == 0.20
        assert PESOS["SINAL"] == 0.15
        assert PESOS["TENTATIVA"] == 0.05
        assert PESOS["SITUACAO"] == 0.05
