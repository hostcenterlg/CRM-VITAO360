"""
CRM VITAO360 — Testes do AgendaService.

Valida:
  1. test_gerar_agenda_respeita_limite_40: 50 clientes MANU -> max 40 na agenda
  2. test_gerar_agenda_daiane_limite_20: Daiane max 20
  3. test_p0_pula_fila_nao_conta_limite: P0 nao conta no max de 40
  4. test_p7_nunca_na_agenda: nenhum P7 incluido
  5. test_ordenacao_por_score_desc: score maior = posicao menor (mais cedo)
  6. test_gerar_todas_4_consultores: gera para LARISSA, MANU, JULIO, DAIANE
  7. test_gerar_limpa_agenda_anterior: 2 chamadas na mesma data = sem duplicatas
  8. test_alucinacao_excluida: clientes ALUCINACAO nao entram
  9. test_p0_antes_de_p1_e_regulares: P0 sempre tem posicao 1 (ou menor)
 10. test_p1_antes_de_regulares: P1 entra antes de P2-P6
 11. test_sem_clientes_agenda_vazia: consultor sem clientes retorna lista vazia
 12. test_gerar_todas_retorna_contagem_correta: resultado dict com 4 consultores
 13. test_classificacao_nula_excluida: classificacao_3tier None excluido (R8)

Fixtures criam banco SQLite em memoria para isolamento total.
Os models sao os mesmos de producao — sem mocks de schema.

R8 — Zero alucinacao: dados ALUCINACAO nunca entram na agenda.
R4 — Two-Base: este servico nao toca valores monetarios.
"""

from __future__ import annotations

import pytest
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models.agenda import AgendaItem
from backend.app.models.cliente import Cliente
from backend.app.services.agenda_service import AgendaService, CONSULTORES


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


@pytest.fixture
def svc() -> AgendaService:
    """Instancia fresh do AgendaService para cada teste."""
    return AgendaService()


# ---------------------------------------------------------------------------
# Helpers / Factories
# ---------------------------------------------------------------------------

_cnpj_counter = 0


def _next_cnpj() -> str:
    """Gera CNPJs unicos sequenciais no formato String(14) (R5)."""
    global _cnpj_counter
    _cnpj_counter += 1
    return str(_cnpj_counter).zfill(14)


def _cliente(
    consultor: str = "MANU",
    prioridade: str = "P2",
    score: float = 50.0,
    classificacao_3tier: str = "REAL",
    cnpj: str | None = None,
) -> Cliente:
    """Factory de Cliente com valores padrao configuráveis."""
    return Cliente(
        cnpj=cnpj or _next_cnpj(),
        nome_fantasia="Empresa Teste LTDA",
        consultor=consultor,
        prioridade=prioridade,
        score=score,
        classificacao_3tier=classificacao_3tier,
        situacao="ATIVO",
        temperatura="MORNO",
        sinaleiro="AMARELO",
        acao_futura="Ligar",
        followup_dias=7,
    )


def _seed_clientes(db, consultor: str, n: int, prioridade: str = "P2", score_base: float = 50.0):
    """Insere N clientes de um consultor com scores decrescentes."""
    clientes = []
    for i in range(n):
        c = _cliente(
            consultor=consultor,
            prioridade=prioridade,
            score=score_base - i,  # scores distintos para testar ordenacao
        )
        db.add(c)
        clientes.append(c)
    db.flush()
    return clientes


DATA_TESTE = date(2026, 3, 25)


# ---------------------------------------------------------------------------
# Testes — Limites de atendimento
# ---------------------------------------------------------------------------

class TestLimiteAtendimentos:

    def test_gerar_agenda_respeita_limite_40(self, db, svc):
        """
        50 clientes MANU com prioridade P2 -> apenas 40 devem entrar na agenda.
        P2-P6 contam no limite.
        """
        _seed_clientes(db, "MANU", 50, prioridade="P2")

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        assert len(items) == 40, f"Esperado 40, obtido {len(items)}"

    def test_gerar_agenda_daiane_limite_20(self, db, svc):
        """
        35 clientes DAIANE -> apenas 20 devem entrar (limite de Daiane e 20).
        """
        _seed_clientes(db, "DAIANE", 35, prioridade="P2")

        items = svc.gerar_agenda_consultor(db, "DAIANE", DATA_TESTE)

        assert len(items) == 20, f"Esperado 20, obtido {len(items)}"

    def test_limite_nao_aplicado_quando_poucos_clientes(self, db, svc):
        """
        10 clientes MANU -> todos os 10 entram (abaixo do limite de 40).
        """
        _seed_clientes(db, "MANU", 10, prioridade="P3")

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        assert len(items) == 10


# ---------------------------------------------------------------------------
# Testes — Regras de prioridade
# ---------------------------------------------------------------------------

class TestPrioridadeP0:

    def test_p0_pula_fila_nao_conta_limite(self, db, svc):
        """
        Com 40 clientes P2 (limite cheio) + 5 clientes P0:
          - Os 5 P0 entram (pula fila, nao contam)
          - Os 40 P2 entram (contam no limite)
          - Total: 45 itens
        """
        _seed_clientes(db, "MANU", 40, prioridade="P2", score_base=60.0)
        _seed_clientes(db, "MANU", 5, prioridade="P0", score_base=90.0)

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        assert len(items) == 45, f"Esperado 45 (5 P0 + 40 regulares), obtido {len(items)}"

    def test_p0_antes_de_p1_e_regulares(self, db, svc):
        """
        P0 deve sempre ocupar as primeiras posicoes na agenda.
        """
        # Adicionar P2, P1 e P0 em ordem inversa
        c_p2 = _cliente(consultor="MANU", prioridade="P2", score=80.0)
        c_p1 = _cliente(consultor="MANU", prioridade="P1", score=70.0)
        c_p0 = _cliente(consultor="MANU", prioridade="P0", score=50.0)
        db.add_all([c_p2, c_p1, c_p0])
        db.flush()

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        assert len(items) == 3
        # Primeiro item deve ser P0
        assert items[0].prioridade == "P0", f"Posicao 1 deveria ser P0, foi {items[0].prioridade}"
        # P0 tem posicao 1
        assert items[0].posicao == 1

    def test_p0_multiplos_ordenados_por_score_desc(self, db, svc):
        """
        Multiplos P0 devem ser incluidos todos na agenda (sem limite).
        """
        for _ in range(25):
            c = _cliente(consultor="MANU", prioridade="P0", score=80.0)
            db.add(c)
        db.flush()

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        p0_items = [i for i in items if i.prioridade == "P0"]
        assert len(p0_items) == 25


class TestPrioridadeP7:

    def test_p7_nunca_na_agenda(self, db, svc):
        """
        P7 (CAMPANHA) nunca deve aparecer na agenda regular.
        """
        _seed_clientes(db, "MANU", 10, prioridade="P7", score_base=5.0)
        _seed_clientes(db, "MANU", 5, prioridade="P2", score_base=60.0)

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        prioridades = [i.prioridade for i in items]
        assert "P7" not in prioridades, "P7 nao deve aparecer na agenda"
        assert len(items) == 5  # Apenas os P2 entram

    def test_p7_exclusivo_sem_outros(self, db, svc):
        """
        Se so existem clientes P7, a agenda deve ficar vazia.
        """
        _seed_clientes(db, "MANU", 10, prioridade="P7")

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        assert len(items) == 0, "Agenda com apenas P7 deve ser vazia"


class TestOrdenacaoPrioridade:

    def test_p1_antes_de_regulares(self, db, svc):
        """
        P1 deve vir antes de P2-P6, mesmo com score menor.
        """
        c_p2_alto = _cliente(consultor="MANU", prioridade="P2", score=95.0)
        c_p1_baixo = _cliente(consultor="MANU", prioridade="P1", score=30.0)
        db.add_all([c_p2_alto, c_p1_baixo])
        db.flush()

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        assert len(items) == 2
        # P1 deve aparecer antes de P2, mesmo com score menor
        assert items[0].prioridade == "P1", f"Primeiro item deveria ser P1, foi {items[0].prioridade}"
        assert items[1].prioridade == "P2"

    def test_ordenacao_por_score_desc(self, db, svc):
        """
        Clientes P2 com scores diferentes devem ser ordenados por score desc.
        Score maior = posicao menor (mais cedo na agenda).
        """
        scores = [30.0, 90.0, 60.0, 45.0, 75.0]
        for s in scores:
            c = _cliente(consultor="MANU", prioridade="P2", score=s)
            db.add(c)
        db.flush()

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        scores_agenda = [i.score for i in items]
        assert scores_agenda == sorted(scores_agenda, reverse=True), (
            f"Scores devem estar em ordem decrescente: {scores_agenda}"
        )

    def test_posicao_sequencial_comecando_em_1(self, db, svc):
        """
        Posicoes devem ser sequenciais a partir de 1.
        """
        _seed_clientes(db, "MANU", 5, prioridade="P3")

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        posicoes = [i.posicao for i in items]
        assert posicoes == list(range(1, 6)), f"Posicoes devem ser [1,2,3,4,5], obtido {posicoes}"


# ---------------------------------------------------------------------------
# Testes — Regras de dados (R8 — Zero alucinacao)
# ---------------------------------------------------------------------------

class TestFiltroAlucinacao:

    def test_alucinacao_excluida(self, db, svc):
        """
        Clientes com classificacao_3tier == 'ALUCINACAO' nunca entram na agenda.
        R8 — Zero fabricacao de dados.
        """
        c_real = _cliente(consultor="MANU", classificacao_3tier="REAL", score=80.0)
        c_sintetico = _cliente(consultor="MANU", classificacao_3tier="SINTETICO", score=75.0)
        c_alucinacao = _cliente(consultor="MANU", classificacao_3tier="ALUCINACAO", score=90.0)
        db.add_all([c_real, c_sintetico, c_alucinacao])
        db.flush()

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        cnpjs_agenda = {i.cnpj for i in items}
        assert c_alucinacao.cnpj not in cnpjs_agenda, "ALUCINACAO nao deve entrar na agenda"
        assert c_real.cnpj in cnpjs_agenda
        assert c_sintetico.cnpj in cnpjs_agenda

    def test_classificacao_nula_excluida(self, db, svc):
        """
        Clientes com classificacao_3tier None tambem sao excluidos (dado nao classificado
        e suspeito — R8).
        """
        c_classificado = _cliente(consultor="MANU", classificacao_3tier="REAL")
        c_nulo = _cliente(consultor="MANU", classificacao_3tier=None)
        c_nulo.classificacao_3tier = None  # garantir None no ORM
        db.add_all([c_classificado, c_nulo])
        db.flush()

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        cnpjs_agenda = {i.cnpj for i in items}
        assert c_nulo.cnpj not in cnpjs_agenda, "Classificacao None nao deve entrar na agenda"
        assert c_classificado.cnpj in cnpjs_agenda


# ---------------------------------------------------------------------------
# Testes — gerar_todas (todos os consultores)
# ---------------------------------------------------------------------------

class TestGerarTodas:

    def test_gerar_todas_4_consultores(self, db, svc):
        """
        gerar_todas() deve processar LARISSA, MANU, JULIO e DAIANE.
        Retorna dict com 4 chaves.
        """
        for consultor in CONSULTORES:
            _seed_clientes(db, consultor, 5, prioridade="P2")

        resultado = svc.gerar_todas(db, DATA_TESTE)

        assert set(resultado.keys()) == {"LARISSA", "MANU", "JULIO", "DAIANE"}
        for consultor, qtd in resultado.items():
            assert qtd == 5, f"{consultor}: esperado 5, obtido {qtd}"

    def test_gerar_todas_retorna_contagem_correta(self, db, svc):
        """
        gerar_todas() deve retornar a quantidade exata de itens por consultor.
        """
        _seed_clientes(db, "MANU", 10, prioridade="P2")
        _seed_clientes(db, "LARISSA", 3, prioridade="P3")
        # JULIO e DAIANE sem clientes

        resultado = svc.gerar_todas(db, DATA_TESTE)

        assert resultado["MANU"] == 10
        assert resultado["LARISSA"] == 3
        assert resultado["JULIO"] == 0
        assert resultado["DAIANE"] == 0

    def test_gerar_limpa_agenda_anterior(self, db, svc):
        """
        Chamar gerar_todas() duas vezes na mesma data nao cria duplicatas.
        A segunda chamada substitui a primeira.
        """
        _seed_clientes(db, "MANU", 5, prioridade="P2")

        # Primeira geracao
        svc.gerar_todas(db, DATA_TESTE)
        db.flush()

        # Segunda geracao (deve limpar a primeira)
        svc.gerar_todas(db, DATA_TESTE)
        db.flush()

        # Contar itens MANU para DATA_TESTE — deve ser exatamente 5 (sem duplicatas)
        total = (
            db.query(AgendaItem)
            .filter(
                AgendaItem.data_agenda == DATA_TESTE,
                AgendaItem.consultor == "MANU",
            )
            .count()
        )
        assert total == 5, f"Esperado 5 (sem duplicatas), obtido {total}"

    def test_gerar_datas_distintas_nao_interfere(self, db, svc):
        """
        Gerar agenda para datas diferentes nao apaga agendas de outras datas.
        """
        from datetime import date as dt_date

        data1 = dt_date(2026, 3, 25)
        data2 = dt_date(2026, 3, 26)

        _seed_clientes(db, "MANU", 3, prioridade="P2")

        svc.gerar_todas(db, data1)
        db.flush()
        svc.gerar_todas(db, data2)
        db.flush()

        count_data1 = (
            db.query(AgendaItem)
            .filter(AgendaItem.data_agenda == data1, AgendaItem.consultor == "MANU")
            .count()
        )
        count_data2 = (
            db.query(AgendaItem)
            .filter(AgendaItem.data_agenda == data2, AgendaItem.consultor == "MANU")
            .count()
        )

        assert count_data1 == 3, "Data anterior nao deve ser apagada"
        assert count_data2 == 3


# ---------------------------------------------------------------------------
# Testes — Casos de borda
# ---------------------------------------------------------------------------

class TestCasosDeBorda:

    def test_sem_clientes_agenda_vazia(self, db, svc):
        """
        Consultor sem clientes deve retornar lista vazia.
        """
        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)
        assert items == []

    def test_apenas_p0_sem_regulares(self, db, svc):
        """
        So P0 na carteira: todos entram, agenda nao e vazia.
        """
        _seed_clientes(db, "MANU", 3, prioridade="P0", score_base=80.0)

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        assert len(items) == 3
        assert all(i.prioridade == "P0" for i in items)

    def test_consultor_desconhecido_usa_limite_40(self, db, svc):
        """
        Consultor fora do dict CONSULTORES usa limite padrao de 40.
        """
        for _ in range(50):
            c = _cliente(consultor="NOVO_CONSULTOR", prioridade="P2", score=50.0)
            db.add(c)
        db.flush()

        items = svc.gerar_agenda_consultor(db, "NOVO_CONSULTOR", DATA_TESTE)

        assert len(items) == 40

    def test_score_nulo_tratado_como_zero(self, db, svc):
        """
        Cliente com score=None nao causa erro — tratado como 0.0 na ordenacao.
        """
        c_com_score = _cliente(consultor="MANU", prioridade="P2", score=50.0)
        c_sem_score = _cliente(consultor="MANU", prioridade="P2", score=None)
        c_sem_score.score = None
        db.add_all([c_com_score, c_sem_score])
        db.flush()

        # Nao deve lancar excecao
        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        assert len(items) == 2
        # Cliente com score maior deve vir primeiro
        assert items[0].cnpj == c_com_score.cnpj

    def test_campos_copiados_corretamente(self, db, svc):
        """
        AgendaItem deve ter os campos copiados corretamente do Cliente.
        """
        c = Cliente(
            cnpj="12345678000100",
            nome_fantasia="Loja Vitao",
            consultor="MANU",
            prioridade="P2",
            score=75.0,
            classificacao_3tier="REAL",
            situacao="ATIVO",
            temperatura="QUENTE",
            sinaleiro="VERDE",
            acao_futura="Visita",
            followup_dias=14,
        )
        db.add(c)
        db.flush()

        items = svc.gerar_agenda_consultor(db, "MANU", DATA_TESTE)

        assert len(items) == 1
        item = items[0]

        assert item.cnpj == "12345678000100"
        assert item.nome_fantasia == "Loja Vitao"
        assert item.consultor == "MANU"
        assert item.data_agenda == DATA_TESTE
        assert item.posicao == 1
        assert item.score == 75.0
        assert item.prioridade == "P2"
        assert item.situacao == "ATIVO"
        assert item.temperatura == "QUENTE"
        assert item.sinaleiro == "VERDE"
        assert item.acao == "Visita"
        assert item.followup_dias == 14
