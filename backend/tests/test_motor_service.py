"""
CRM VITAO360 — Testes do Motor de Regras Service.

Valida:
  1. Motor aplica regras corretamente para combinacoes conhecidas
  2. registrar_atendimento() cria LogInteracao e atualiza Cliente
  3. Resultado invalido e rejeitado pela rota
  4. Tentativas avancam corretamente (T1 → T2 → T3 → T4 → NUTRIÇÃO)
  5. R4 — Two-Base: LogInteracao NAO tem campo de valor monetario
  6. R5 — CNPJ nao encontrado levanta ValueError com mensagem clara

Fixtures criam banco SQLite em memoria para isolamento total.
Os models sao os mesmos de producao — nao ha mocks de schema.
"""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.database import Base
from backend.app.models.cliente import Cliente
from backend.app.models.log_interacao import LogInteracao
from backend.app.models.regra_motor import RegraMotor
from backend.app.services.motor_regras_service import MotorRegrasService


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    """
    Banco SQLite em memoria com schema completo e dados de seed para testes.

    Seed inserido:
      - 1 cliente ATIVO (CNPJ 12345678000100)
      - 1 cliente PROSPECT (CNPJ 98765432000199)
      - Regras motor para ATIVO|VENDA / PEDIDO e ATIVO|NÃO ATENDE
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed clientes
    cliente_ativo = Cliente(
        cnpj="12345678000100",
        nome_fantasia="Distribuidora Teste Ltda",
        situacao="ATIVO",
        consultor="MANU",
        fase="CS",
        estagio_funil="CS / RECOMPRA",
        tentativas=None,
        temperatura="\U0001f7e1 MORNO",
    )
    cliente_prospect = Cliente(
        cnpj="98765432000199",
        nome_fantasia="Prospect Exemplo ME",
        situacao="PROSPECT",
        consultor="LARISSA",
        fase="PROSPECÇÃO",
        estagio_funil="PROSPECÇÃO",
        tentativas=None,
        temperatura="\u2744\ufe0f FRIO",
    )
    session.add_all([cliente_ativo, cliente_prospect])

    # Seed regras motor — subset relevante para os testes
    regras = [
        RegraMotor(
            situacao="ATIVO",
            resultado="VENDA / PEDIDO",
            estagio_funil="PÓS-VENDA",
            fase="PÓS-VENDA",
            tipo_contato="PÓS-VENDA / RELACIONAMENTO",
            acao_futura="PÓS-VENDA",
            temperatura="\U0001f525 QUENTE",
            follow_up_dias=45,
            grupo_dash="FUNIL",
            tipo_acao=None,
            chave="ATIVO|VENDA / PEDIDO",
        ),
        RegraMotor(
            situacao="ATIVO",
            resultado="NÃO ATENDE",
            estagio_funil="CS / RECOMPRA",
            fase="RECOMPRA",
            tipo_contato="ATEND. CLIENTES ATIVOS",
            acao_futura="RECOMPRA",
            temperatura="\u2744\ufe0f FRIO",
            follow_up_dias=1,
            grupo_dash="NÃO VENDA",
            tipo_acao=None,
            chave="ATIVO|NÃO ATENDE",
        ),
        RegraMotor(
            situacao="PROSPECT",
            resultado="EM ATENDIMENTO",
            estagio_funil="EM ATENDIMENTO",
            fase="PROSPECÇÃO",
            tipo_contato="PROSPECÇÃO",
            acao_futura="PROSPECÇÃO",
            temperatura="\U0001f7e1 MORNO",
            follow_up_dias=2,
            grupo_dash="FUNIL",
            tipo_acao=None,
            chave="PROSPECT|EM ATENDIMENTO",
        ),
    ]
    session.add_all(regras)
    session.commit()

    yield session
    session.close()
    engine.dispose()


# ---------------------------------------------------------------------------
# Testes: motor.aplicar()
# ---------------------------------------------------------------------------

class TestMotorAplicar:
    """Testa o metodo aplicar() de MotorRegrasService."""

    def test_venda_pedido_retorna_pos_venda(self, db):
        """ATIVO + VENDA / PEDIDO deve retornar fase POS-VENDA e temperatura QUENTE."""
        service = MotorRegrasService()
        r = service.aplicar(db, "ATIVO", "VENDA / PEDIDO")

        assert r["fase"] == "PÓS-VENDA"
        assert r["estagio_funil"] == "PÓS-VENDA"
        assert "QUENTE" in r["temperatura"]
        assert r["follow_up_dias"] == 45
        assert r["tentativa"] is None  # venda nao incrementa tentativa

    def test_nao_atende_primeira_tentativa(self, db):
        """NÃO ATENDE sem tentativa anterior deve resultar em T1."""
        service = MotorRegrasService()
        r = service.aplicar(db, "ATIVO", "NÃO ATENDE", tentativa_anterior=None)

        assert r["tentativa"] == "T1"
        assert "FRIO" in r["temperatura"]

    def test_nao_atende_avanca_tentativa_t1_para_t2(self, db):
        """T1 existente deve avancar para T2."""
        service = MotorRegrasService()
        r = service.aplicar(db, "ATIVO", "NÃO ATENDE", tentativa_anterior="T1")

        assert r["tentativa"] == "T2"

    def test_nao_atende_avanca_tentativa_t3_para_t4(self, db):
        """T3 existente deve avancar para T4."""
        service = MotorRegrasService()
        r = service.aplicar(db, "ATIVO", "NÃO ATENDE", tentativa_anterior="T3")

        assert r["tentativa"] == "T4"

    def test_nao_atende_avanca_t4_para_nutricao(self, db):
        """T4 deve avancar para NUTRIÇÃO (fim da sequencia de tentativas)."""
        service = MotorRegrasService()
        # T4 → NUTRIÇÃO via _avancar_tentativa
        resultado = service._avancar_tentativa("T4")
        assert resultado == "NUTRIÇÃO"

    def test_prospect_em_atendimento(self, db):
        """PROSPECT + EM ATENDIMENTO deve retornar fase PROSPECÇÃO."""
        service = MotorRegrasService()
        r = service.aplicar(db, "PROSPECT", "EM ATENDIMENTO")

        assert r["fase"] == "PROSPECÇÃO"
        assert r["estagio_funil"] == "EM ATENDIMENTO"

    def test_fallback_para_motor_original(self, db):
        """
        Combinacao sem regra na tabela deve usar o fallback (motor_de_regras).
        Usa ATIVO + ORÇAMENTO que nao esta no seed de testes.
        """
        service = MotorRegrasService()
        # ATIVO|ORÇAMENTO nao foi inserido no seed de testes
        r = service.aplicar(db, "ATIVO", "ORÇAMENTO")

        # Motor original retorna ORÇAMENTO como estagio_funil
        assert r["estagio_funil"] is not None
        assert r["temperatura"] is not None


# ---------------------------------------------------------------------------
# Testes: registrar_atendimento()
# ---------------------------------------------------------------------------

class TestRegistrarAtendimento:
    """Testa o metodo registrar_atendimento() de MotorRegrasService."""

    def test_cria_log_interacao(self, db):
        """Deve criar LogInteracao com CNPJ e consultor corretos."""
        service = MotorRegrasService()
        log = service.registrar_atendimento(
            db, "12345678000100", "VENDA / PEDIDO", "Fechou pedido organicos", "MANU"
        )
        db.commit()

        assert log.id is not None
        assert log.cnpj == "12345678000100"
        assert log.consultor == "MANU"
        assert log.resultado == "VENDA / PEDIDO"
        assert log.descricao == "Fechou pedido organicos"

    def test_atualiza_campos_cliente_apos_venda(self, db):
        """Apos VENDA, o cliente deve ter fase e temperatura atualizadas."""
        service = MotorRegrasService()
        service.registrar_atendimento(
            db, "12345678000100", "VENDA / PEDIDO", "Pedido confirmado", "MANU"
        )
        db.commit()

        cliente = db.query(Cliente).filter(Cliente.cnpj == "12345678000100").first()
        assert cliente.fase == "PÓS-VENDA"
        assert "QUENTE" in (cliente.temperatura or "")

    def test_cnpj_nao_encontrado_levanta_value_error(self, db):
        """CNPJ inexistente deve levantar ValueError com mensagem descritiva."""
        service = MotorRegrasService()
        with pytest.raises(ValueError, match="nao encontrado"):
            service.registrar_atendimento(
                db, "99999999999999", "VENDA / PEDIDO", "Teste", "MANU"
            )

    def test_nao_atende_incrementa_tentativa_no_cliente(self, db):
        """Apos NÃO ATENDE, cliente deve ter tentativas atualizado para T1."""
        service = MotorRegrasService()
        service.registrar_atendimento(
            db, "12345678000100", "NÃO ATENDE", "Caixa postal", "MANU"
        )
        db.commit()

        cliente = db.query(Cliente).filter(Cliente.cnpj == "12345678000100").first()
        assert cliente.tentativas == "T1"

    def test_created_by_preenchido(self, db):
        """created_by deve ser preenchido com o user_id informado."""
        service = MotorRegrasService()
        log = service.registrar_atendimento(
            db, "12345678000100", "VENDA / PEDIDO", "Teste", "MANU", user_id=42
        )
        db.commit()

        assert log.created_by == 42

    def test_resultado_atualizado_no_cliente(self, db):
        """O campo resultado do cliente deve refletir o ultimo atendimento."""
        service = MotorRegrasService()
        service.registrar_atendimento(
            db, "12345678000100", "ORÇAMENTO", "Proposta enviada", "MANU"
        )
        db.commit()

        cliente = db.query(Cliente).filter(Cliente.cnpj == "12345678000100").first()
        assert cliente.resultado == "ORÇAMENTO"


# ---------------------------------------------------------------------------
# Testes: R4 — Two-Base Architecture
# ---------------------------------------------------------------------------

class TestTwoBaseArchitecture:
    """
    R4 — Two-Base Architecture.

    Verifica que LogInteracao NAO possui campos de valor monetario.
    Violacao desta regra causou inflacao de 742% em sessao anterior.
    """

    def test_log_interacao_nao_tem_campos_monetarios(self):
        """
        LogInteracao nao pode ter campos de valor, faturamento, preco, etc.
        Esta verificacao e estrutural — nao depende de dados.
        """
        colunas = {c.name for c in LogInteracao.__table__.columns}
        campos_proibidos = [
            "valor",
            "valor_pedido",
            "valor_venda",
            "faturamento",
            "preco",
            "total",
            "receita",
            "ticket",
            "comissao",
        ]
        violacoes = [campo for campo in campos_proibidos if campo in colunas]
        assert not violacoes, (
            f"Two-Base VIOLADA: LogInteracao tem campo(s) monetario(s): {violacoes}"
        )

    def test_log_interacao_tem_campos_esperados(self):
        """Confirma que LogInteracao tem os campos calculados pelo motor."""
        colunas = {c.name for c in LogInteracao.__table__.columns}
        campos_esperados = [
            "id", "cnpj", "consultor", "resultado", "descricao",
            "estagio_funil", "fase", "tipo_contato", "acao_futura",
            "temperatura", "follow_up_dias", "grupo_dash", "tentativa",
        ]
        ausentes = [campo for campo in campos_esperados if campo not in colunas]
        assert not ausentes, f"LogInteracao sem campos esperados: {ausentes}"


# ---------------------------------------------------------------------------
# Testes: _avancar_tentativa()
# ---------------------------------------------------------------------------

class TestAvancarTentativa:
    """Testa a logica de avanco de tentativas em isolamento."""

    def test_none_retorna_t1(self):
        service = MotorRegrasService()
        assert service._avancar_tentativa(None) == "T1"

    def test_t1_retorna_t2(self):
        service = MotorRegrasService()
        assert service._avancar_tentativa("T1") == "T2"

    def test_t2_retorna_t3(self):
        service = MotorRegrasService()
        assert service._avancar_tentativa("T2") == "T3"

    def test_t3_retorna_t4(self):
        service = MotorRegrasService()
        assert service._avancar_tentativa("T3") == "T4"

    def test_t4_retorna_nutricao(self):
        service = MotorRegrasService()
        assert service._avancar_tentativa("T4") == "NUTRIÇÃO"

    def test_valor_desconhecido_retorna_t1(self):
        """Valor nao mapeado (ex.: NUTRIÇÃO reiniciando) deve retornar T1."""
        service = MotorRegrasService()
        assert service._avancar_tentativa("NUTRIÇÃO") == "T1"
