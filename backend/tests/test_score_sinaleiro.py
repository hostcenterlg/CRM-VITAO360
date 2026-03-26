"""
CRM VITAO360 — Testes do Score Engine e Sinaleiro Engine.

Valida:
  1. Calculo correto de score ponderado com 6 fatores
  2. Prioridade P0 para cliente com problema_aberto
  3. Prioridade P1 para followup_vencido + cs_no_prazo
  4. Prioridade P7 para score muito baixo (NUTRICAO)
  5. Sinaleiro ROXO para PROSPECT e LEAD
  6. Sinaleiro VERDE para situacao NOVO
  7. Sinaleiro VERDE quando dias <= ciclo_medio
  8. Sinaleiro VERMELHO quando dias > ciclo_medio + 30
  9. Sinaleiro AMARELO via fallback sem ciclo (dias=60)
  10. Calculo correto de penetracao de rede (TICKET_REF=525, MESES=11)
  11. ScoreHistorico criado apos aplicar_e_salvar

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
from backend.app.services.score_service import ScoreService, score_service
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
    fase: str = "RECOMPRA",
    sinaleiro: str = "VERMELHO",
    curva_abc: str = "A",
    temperatura: str = "QUENTE",
    tipo_cliente: str = "MADURO",
    tentativas: str = "T1",
    dias_sem_compra: int | None = None,
    ciclo_medio: float | None = None,
    problema_aberto: bool = False,
    followup_vencido: bool = False,
    cs_no_prazo: bool = False,
) -> Cliente:
    """Factory de Cliente com valores padrao configuráveis."""
    return Cliente(
        cnpj=cnpj,
        nome_fantasia="Teste LTDA",
        situacao=situacao,
        fase=fase,
        sinaleiro=sinaleiro,
        curva_abc=curva_abc,
        temperatura=temperatura,
        tipo_cliente=tipo_cliente,
        tentativas=tentativas,
        dias_sem_compra=dias_sem_compra,
        ciclo_medio=ciclo_medio,
        problema_aberto=problema_aberto,
        followup_vencido=followup_vencido,
        cs_no_prazo=cs_no_prazo,
        classificacao_3tier="REAL",
    )


# ---------------------------------------------------------------------------
# Testes — Score Engine
# ---------------------------------------------------------------------------

class TestScoreCalculo:

    def test_score_calculo_basico(self):
        """
        Cliente ATIVO com fase RECOMPRA, sinaleiro VERMELHO, ABC A deve
        ter score alto (maximo possivel com esses fatores).
        """
        svc = ScoreService()
        c = _cliente(
            fase="RECOMPRA",       # 100 * 0.25 = 25.0
            sinaleiro="VERMELHO",  # 100 * 0.20 = 20.0
            curva_abc="A",         # 100 * 0.20 = 20.0
            temperatura="QUENTE",  # 100 * 0.15 = 15.0
            tipo_cliente="MADURO", # 100 * 0.10 = 10.0
            tentativas="T1",       # 100 * 0.10 = 10.0
        )
        resultado = svc.calcular(c)

        assert resultado["score"] == 100.0
        assert resultado["fator_fase"] == 100.0
        assert resultado["fator_sinaleiro"] == 100.0
        assert resultado["fator_curva"] == 100.0
        assert resultado["fator_temperatura"] == 100.0
        assert resultado["fator_tipo_cliente"] == 100.0
        assert resultado["fator_tentativas"] == 100.0

    def test_score_formula_ponderada(self):
        """
        Verifica formula de ponderacao com valores conhecidos.
        NUTRIÇÃO = 10, fallback = 0 para campos sem match.
        Score = 10*0.25 + 0*0.20 + 60*0.20 + 60*0.15 + 15*0.10 + 5*0.10
              = 2.5 + 0 + 12 + 9 + 1.5 + 0.5 = 25.5
        """
        svc = ScoreService()
        c = _cliente(
            fase="NUTRIÇÃO",       # 10 * 0.25 = 2.5
            sinaleiro="ROXO",      # 0  * 0.20 = 0.0
            curva_abc="B",         # 60 * 0.20 = 12.0
            temperatura="MORNO",   # 60 * 0.15 = 9.0
            tipo_cliente="LEAD",   # 15 * 0.10 = 1.5
            tentativas="NUTRIÇÃO", # 5  * 0.10 = 0.5
        )
        resultado = svc.calcular(c)
        assert resultado["score"] == 25.5

    def test_score_com_emoji_temperatura(self):
        """
        Campo temperatura pode vir com emoji do motor legado.
        '🔥 QUENTE' deve retornar mesmo score que 'QUENTE'.
        """
        svc = ScoreService()
        c_com_emoji = _cliente(temperatura="🔥 QUENTE")
        c_sem_emoji = _cliente(temperatura="QUENTE")

        r_emoji = svc.calcular(c_com_emoji)
        r_limpo = svc.calcular(c_sem_emoji)

        assert r_emoji["fator_temperatura"] == r_limpo["fator_temperatura"]
        assert r_emoji["score"] == r_limpo["score"]

    def test_score_campos_nulos_retornam_zero(self):
        """Cliente sem campos preenchidos deve retornar score 0."""
        svc = ScoreService()
        c = Cliente(
            cnpj="00000000000001",
            nome_fantasia="Sem Dados",
            classificacao_3tier="REAL",
        )
        resultado = svc.calcular(c)
        assert resultado["score"] == 0.0

    def test_score_variantes_acentuadas(self):
        """
        As tabelas de lookup aceitam variantes acentuadas e nao-acentuadas.
        NEGOCIAÇÃO e NEGOCIACAO devem retornar mesmo fator.
        """
        svc = ScoreService()
        c1 = _cliente(fase="NEGOCIAÇÃO")
        c2 = _cliente(fase="NEGOCIACAO")
        assert svc.calcular(c1)["fator_fase"] == svc.calcular(c2)["fator_fase"] == 80.0


class TestPrioridade:

    def test_prioridade_p0_suporte(self):
        """problema_aberto=True deve retornar P0 independente do score."""
        svc = ScoreService()
        c = _cliente(problema_aberto=True)
        resultado = svc.calcular(c)
        assert resultado["prioridade"] == "P0"

    def test_prioridade_p1_followup(self):
        """followup_vencido=True + cs_no_prazo=True deve retornar P1."""
        svc = ScoreService()
        c = _cliente(followup_vencido=True, cs_no_prazo=True)
        resultado = svc.calcular(c)
        assert resultado["prioridade"] == "P1"

    def test_prioridade_p1_requer_ambas_flags(self):
        """Apenas followup_vencido sem cs_no_prazo nao deve ser P1."""
        svc = ScoreService()
        c = _cliente(followup_vencido=True, cs_no_prazo=False)
        resultado = svc.calcular(c)
        assert resultado["prioridade"] != "P1"

    def test_prioridade_p2_score_alto(self):
        """Score 100 deve retornar P2 (faixa 80-100)."""
        svc = ScoreService()
        c = _cliente(
            fase="RECOMPRA", sinaleiro="VERMELHO", curva_abc="A",
            temperatura="QUENTE", tipo_cliente="MADURO", tentativas="T1",
        )
        resultado = svc.calcular(c)
        assert resultado["score"] == 100.0
        assert resultado["prioridade"] == "P2"

    def test_prioridade_p7_nutricao(self):
        """Score muito baixo deve retornar P7 (faixa 0-14.9)."""
        svc = ScoreService()
        # Score = 10*0.25 + 0 + 0 + 0 + 0 + 5*0.10 = 2.5 + 0.5 = 3.0
        c = _cliente(
            fase="NUTRIÇÃO", sinaleiro="ROXO", curva_abc="C",
            temperatura="PERDIDO", tipo_cliente="PROSPECT", tentativas="NUTRIÇÃO",
        )
        resultado = svc.calcular(c)
        assert resultado["score"] < 15.0
        assert resultado["prioridade"] == "P7"

    def test_prioridade_p0_tem_precedencia_sobre_p1(self):
        """P0 (problema_aberto) tem precedencia sobre qualquer outra flag."""
        svc = ScoreService()
        c = _cliente(problema_aberto=True, followup_vencido=True, cs_no_prazo=True)
        resultado = svc.calcular(c)
        assert resultado["prioridade"] == "P0"


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
        """dias_sem_compra <= ciclo_medio deve retornar VERDE."""
        svc = SinaleiroService()
        c = _cliente(situacao="ATIVO", dias_sem_compra=25, ciclo_medio=30.0)
        assert svc.calcular(c) == "VERDE"

    def test_sinaleiro_ativo_no_limite_ciclo_verde(self):
        """dias_sem_compra == ciclo_medio deve retornar VERDE (limite inclusivo)."""
        svc = SinaleiroService()
        c = _cliente(situacao="ATIVO", dias_sem_compra=30, ciclo_medio=30.0)
        assert svc.calcular(c) == "VERDE"

    def test_sinaleiro_ativo_alem_ciclo_amarelo(self):
        """dias_sem_compra entre ciclo e ciclo+30 deve retornar AMARELO."""
        svc = SinaleiroService()
        c = _cliente(situacao="ATIVO", dias_sem_compra=45, ciclo_medio=30.0)
        assert svc.calcular(c) == "AMARELO"

    def test_sinaleiro_ativo_alem_ciclo_vermelho(self):
        """dias_sem_compra > ciclo_medio + 30 deve retornar VERMELHO."""
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
        valores corretos de score, prioridade, sinaleiro e fatores.
        """
        svc = ScoreService()

        c = _cliente(
            cnpj="11222333000181",
            situacao="ATIVO",
            fase="RECOMPRA",
            sinaleiro="VERDE",
            curva_abc="A",
            temperatura="QUENTE",
            tipo_cliente="MADURO",
            tentativas="T1",
        )
        db.add(c)
        db.flush()

        resultado = svc.aplicar_e_salvar(db, c)
        db.flush()

        # Verificar que o historico foi criado
        hist = db.query(ScoreHistorico).filter(ScoreHistorico.cnpj == "11222333000181").first()
        assert hist is not None
        assert hist.score == resultado["score"]
        assert hist.prioridade == resultado["prioridade"]
        assert hist.fator_fase == resultado["fator_fase"]
        assert hist.fator_curva == resultado["fator_curva"]

    def test_score_salvo_no_cliente(self, db):
        """
        aplicar_e_salvar() deve atualizar cliente.score e cliente.prioridade.
        """
        svc = ScoreService()

        c = _cliente(
            cnpj="44555666000177",
            fase="RECOMPRA",
            sinaleiro="VERMELHO",
            curva_abc="A",
            temperatura="QUENTE",
            tipo_cliente="MADURO",
            tentativas="T1",
        )
        c.score = None
        c.prioridade = None
        db.add(c)
        db.flush()

        svc.aplicar_e_salvar(db, c)

        assert c.score == 100.0
        assert c.prioridade == "P2"

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

    def test_sinaleiro_atualiza_fator_sinaleiro_no_score(self, db):
        """
        Apos aplicar sinaleiro, o score recalculado deve refletir o novo
        valor de sinaleiro. Muda ROXO (fator=0) para VERMELHO (fator=100).
        """
        svc_sin = SinaleiroService()
        svc_score = ScoreService()

        # Criar cliente PROSPECT (sinaleiro sera ROXO)
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

        # Recalcular score com o novo sinaleiro
        resultado = svc_score.calcular(c)
        # Fator sinaleiro para ROXO = 0
        assert resultado["fator_sinaleiro"] == 0.0
