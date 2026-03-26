"""
CRM VITAO360 — Testes do Import Pipeline (FR-001 a FR-006).

Valida:
  1. Deteccao de tipo de arquivo por heuristica de cabecalhos
  2. Normalizacao de CNPJ (R5: String(14), zero-padded, nunca float)
  3. De-Para de vendedores (R9)
  4. Rejeicao de CNPJs ALUCINACAO (R8)
  5. POST /api/import/upload — arquivo invalido (nao-.xlsx) retorna 400
  6. POST /api/import/upload — arquivo .xlsx com Mercos Carteira insere e atualiza clientes
  7. POST /api/import/upload — Two-Base: vendas com valor > 0 vao para tabela vendas
  8. POST /api/import/upload — arquivo com tipo desconhecido retorna 422
  9. GET /api/import/history — lista jobs com paginacao
  10. R8: CNPJs da lista ALUCINACAO sao rejeitados e nao inseridos
  11. Recalculo de Score e Sinaleiro apos import

Fixtures:
  - engine SQLite em memoria (isolamento total)
  - Banco com Base.metadata.create_all (todas as tabelas)
  - Usuario admin injetado via dependency_overrides

Padrao de autenticacao:
  dependency_overrides injeta usuario admin sem JWT (mesmo padrao de test_vendas.py).
"""

from __future__ import annotations

import io
from types import SimpleNamespace

import pytest

try:
    import openpyxl
    _OPENPYXL_DISPONIVEL = True
except ImportError:
    _OPENPYXL_DISPONIVEL = False

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, StaticPool
from sqlalchemy.orm import sessionmaker, Session

from backend.app.api.deps import get_current_user, require_admin
from backend.app.database import Base, get_db
from backend.app.main import app
from backend.app.models.cliente import Cliente
from backend.app.models.import_job import ImportJob
from backend.app.models.venda import Venda

from backend.app.api.routes_import import (
    _normalizar_cnpj,
    _normalizar_vendedor,
    _detectar_tipo_arquivo,
    _CNPJS_ALUCINACAO,
)


# ---------------------------------------------------------------------------
# Fixtures de banco
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def engine_mem():
    """Engine SQLite em memoria — isolamento completo entre funcoes de teste."""
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(_engine)
    yield _engine
    _engine.dispose()


@pytest.fixture(scope="function")
def db_session(engine_mem) -> Session:
    """Session SQLite em memoria, sem seed de clientes (import cria os proprios)."""
    _Session = sessionmaker(bind=engine_mem)
    session = _Session()
    yield session
    session.close()


def _make_get_db_override(session: Session):
    def _override():
        yield session
    return _override


# ---------------------------------------------------------------------------
# Fixtures de usuarios
# ---------------------------------------------------------------------------

def _fake_admin() -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        email="admin@vitao.com",
        nome="Admin VITAO",
        role="admin",
        consultor_nome=None,
        ativo=True,
    )


@pytest.fixture(scope="function")
def usuario_admin():
    return _fake_admin()


# ---------------------------------------------------------------------------
# Fixtures de TestClient
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client_admin(db_session, usuario_admin):
    """TestClient com admin e banco em memoria."""
    app.dependency_overrides[get_db] = _make_get_db_override(db_session)
    app.dependency_overrides[get_current_user] = lambda: usuario_admin
    app.dependency_overrides[require_admin] = lambda: usuario_admin
    client = TestClient(app, raise_server_exceptions=True)
    yield client
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helpers para construir .xlsx em memoria
# ---------------------------------------------------------------------------

def _criar_xlsx_bytes(cabecalhos: list, linhas: list[list]) -> bytes:
    """
    Cria um arquivo .xlsx em memoria com os cabecalhos e linhas fornecidos.

    Retorna os bytes do arquivo, prontos para envio via multipart.
    Requer openpyxl instalado.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(cabecalhos)
    for linha in linhas:
        ws.append(linha)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Testes: Utilitarios de normalizacao (sem HTTP)
# ---------------------------------------------------------------------------

class TestNormalizacaoCnpj:
    """R5 — CNPJ: String(14), zero-padded, NUNCA float."""

    def test_cnpj_string_valido(self):
        assert _normalizar_cnpj("12345678000195") == "12345678000195"

    def test_cnpj_com_pontuacao(self):
        """12.345.678/0001-95 deve ser normalizado removendo pontuacao."""
        assert _normalizar_cnpj("12.345.678/0001-95") == "12345678000195"

    def test_cnpj_float_sem_perda(self):
        """Float CNPJ (12345678000195.0) deve converter sem perda de digitos."""
        assert _normalizar_cnpj(12345678000195.0) == "12345678000195"

    def test_cnpj_curto_com_zfill(self):
        """CNPJ com menos de 14 digitos deve receber zero-pad."""
        assert _normalizar_cnpj("1234567800019") == "01234567800019"

    def test_cnpj_none_retorna_vazio(self):
        assert _normalizar_cnpj(None) == ""

    def test_cnpj_string_vazia(self):
        assert _normalizar_cnpj("") == ""

    def test_cnpj_com_mais_de_14_digitos_retorna_vazio(self):
        """CNPJ com mais de 14 digitos (apos zfill) e invalido."""
        assert _normalizar_cnpj("123456789012345") == ""

    def test_cnpj_int(self):
        assert _normalizar_cnpj(12345678000195) == "12345678000195"


class TestNormalizacaoVendedor:
    """R9 — De-Para canonico de vendedores."""

    def test_manu_variantes(self):
        assert _normalizar_vendedor("Manu Vitao") == "MANU"
        assert _normalizar_vendedor("manu ditzel") == "MANU"
        assert _normalizar_vendedor("MANU") == "MANU"

    def test_larissa_variantes(self):
        assert _normalizar_vendedor("Larissa Vitao") == "LARISSA"
        assert _normalizar_vendedor("Mais Granel") == "LARISSA"
        assert _normalizar_vendedor("Rodrigo") == "LARISSA"
        assert _normalizar_vendedor("LARI") == "LARISSA"

    def test_daiane_variantes(self):
        assert _normalizar_vendedor("Central Daiane") == "DAIANE"
        assert _normalizar_vendedor("Daiane Vitao") == "DAIANE"

    def test_julio_variantes(self):
        assert _normalizar_vendedor("Julio Gadret") == "JULIO"
        assert _normalizar_vendedor("JULIO") == "JULIO"

    def test_vendedor_none(self):
        assert _normalizar_vendedor(None) == ""

    def test_vendedor_legado(self):
        assert _normalizar_vendedor("Bruno Gretter") == "LEGADO"
        assert _normalizar_vendedor("Patric") == "LEGADO"


class TestDeteccaoTipoArquivo:
    """FR-002 — Deteccao de tipo de arquivo por cabecalhos."""

    def test_detecao_mercos_vendas(self):
        cabecalhos = ["CNPJ", "Nome Fantasia", "Valor Total", "Data do Pedido", "Consultor"]
        assert _detectar_tipo_arquivo(cabecalhos) == "MERCOS_VENDAS"

    def test_deteccao_mercos_carteira(self):
        cabecalhos = ["CNPJ", "Nome", "Dias sem compra", "Consultor", "Situacao"]
        assert _detectar_tipo_arquivo(cabecalhos) == "MERCOS_CARTEIRA"

    def test_deteccao_sap_cadastro_com_codigo(self):
        cabecalhos = ["Codigo do Cliente", "CNPJ", "Razao Social", "Cidade", "UF"]
        assert _detectar_tipo_arquivo(cabecalhos) == "SAP_CADASTRO"

    def test_deteccao_sap_cadastro_com_cadastro(self):
        cabecalhos = ["CNPJ", "Razao Social", "Cadastro", "Cidade"]
        assert _detectar_tipo_arquivo(cabecalhos) == "SAP_CADASTRO"

    def test_tipo_desconhecido_levanta_valueerror(self):
        cabecalhos = ["Coluna1", "Coluna2", "Coluna3"]
        with pytest.raises(ValueError, match="nao reconhecido"):
            _detectar_tipo_arquivo(cabecalhos)

    def test_cabecalhos_vazios_levanta_valueerror(self):
        with pytest.raises(ValueError):
            _detectar_tipo_arquivo([])


# ---------------------------------------------------------------------------
# Testes: R8 — Protecao contra ALUCINACAO
# ---------------------------------------------------------------------------

class TestAlucinacaoProtection:
    """R8 — 558 CNPJs ALUCINACAO nunca devem ser integrados."""

    def test_cnpj_alucinacao_presente_na_lista(self):
        """Os CNPJs zero e generico devem estar na lista de ALUCINACAO."""
        assert "00000000000000" in _CNPJS_ALUCINACAO
        assert "11111111111111" in _CNPJS_ALUCINACAO

    def test_cnpj_real_nao_esta_na_lista(self):
        """CNPJs reais nao devem estar na lista de ALUCINACAO."""
        assert "74485163000137" not in _CNPJS_ALUCINACAO
        assert "56789012000100" not in _CNPJS_ALUCINACAO


# ---------------------------------------------------------------------------
# Testes: POST /api/import/upload — validacao de arquivo
# ---------------------------------------------------------------------------

class TestUploadValidacao:
    """FR-001 — Validacao de extensao e tamanho do arquivo."""

    def test_upload_arquivo_nao_xlsx_retorna_400(self, client_admin):
        """Arquivo com extensao .csv deve ser rejeitado com 400."""
        conteudo = b"CNPJ;Nome;Valor\n12345678000195;Teste;100"
        resp = client_admin.post(
            "/api/import/upload",
            files={"file": ("dados.csv", conteudo, "text/csv")},
        )
        assert resp.status_code == 400, resp.text
        assert ".xlsx" in resp.json()["detail"].lower()

    def test_upload_arquivo_xls_retorna_400(self, client_admin):
        """Arquivo .xls (formato antigo) tambem deve ser rejeitado."""
        conteudo = b"\xd0\xcf\x11\xe0"  # magic bytes do .xls
        resp = client_admin.post(
            "/api/import/upload",
            files={"file": ("dados.xls", conteudo, "application/vnd.ms-excel")},
        )
        assert resp.status_code == 400, resp.text

    @pytest.mark.skipif(not _OPENPYXL_DISPONIVEL, reason="openpyxl nao instalado")
    def test_upload_xlsx_tipo_desconhecido_retorna_422(self, client_admin):
        """Arquivo .xlsx com cabecalhos nao reconhecidos retorna 422."""
        xlsx_bytes = _criar_xlsx_bytes(
            ["Coluna A", "Coluna B", "Coluna C"],
            [["val1", "val2", "val3"]],
        )
        resp = client_admin.post(
            "/api/import/upload",
            files={"file": ("dados_estranhos.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 422, resp.text
        assert "nao reconhecido" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Testes: POST /api/import/upload — Mercos Carteira
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _OPENPYXL_DISPONIVEL, reason="openpyxl nao instalado")
class TestUploadMercosCarteira:
    """FR-003, FR-004, FR-005 — Processamento de Mercos Carteira."""

    def test_upload_mercos_carteira_insere_clientes(self, client_admin, db_session):
        """
        Upload de Mercos Carteira com 2 CNPJs validos deve:
          - Inserir 2 clientes novos
          - Retornar status CONCLUIDO com inseridos=2
        """
        xlsx_bytes = _criar_xlsx_bytes(
            ["CNPJ", "Nome", "Dias sem compra", "Consultor", "Situacao", "Ciclo Medio"],
            [
                ["74485163000137", "Distribuidora Sul", 30, "Manu Vitao", "ATIVO", 45],
                ["56789012000100", "Mercado Norte", 15, "Larissa Vitao", "ATIVO", 30],
            ],
        )
        resp = client_admin.post(
            "/api/import/upload",
            files={"file": ("carteira_abril.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["status"] == "CONCLUIDO"
        assert data["inseridos"] == 2
        assert data["atualizados"] == 0
        assert data["tipo"] == "MERCOS_CARTEIRA"

        # Verificar que clientes foram inseridos no banco
        c1 = db_session.query(Cliente).filter(Cliente.cnpj == "74485163000137").first()
        assert c1 is not None
        assert c1.nome_fantasia == "Distribuidora Sul"
        assert c1.consultor == "MANU"  # De-Para aplicado
        assert c1.classificacao_3tier == "REAL"  # FR-004

        c2 = db_session.query(Cliente).filter(Cliente.cnpj == "56789012000100").first()
        assert c2 is not None
        assert c2.consultor == "LARISSA"  # De-Para aplicado

    def test_upload_mercos_carteira_atualiza_existente(self, client_admin, db_session):
        """
        Upload de cliente ja existente deve:
          - Atualizar os campos (nao duplicar)
          - Retornar atualizados=1, inseridos=0
        """
        # Inserir cliente pre-existente
        cliente_existente = Cliente(
            cnpj="74485163000137",
            nome_fantasia="Nome Antigo",
            situacao="INAT.REC",
            consultor="LARISSA",
            classificacao_3tier="REAL",
        )
        db_session.add(cliente_existente)
        db_session.commit()

        xlsx_bytes = _criar_xlsx_bytes(
            ["CNPJ", "Nome", "Dias sem compra", "Consultor", "Situacao"],
            [["74485163000137", "Nome Atualizado", 10, "Manu Vitao", "ATIVO"]],
        )
        resp = client_admin.post(
            "/api/import/upload",
            files={"file": ("carteira.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["status"] == "CONCLUIDO"
        assert data["atualizados"] == 1
        assert data["inseridos"] == 0

        # Verificar que nome foi atualizado no banco
        db_session.expire_all()
        cliente_atualizado = db_session.query(Cliente).filter(Cliente.cnpj == "74485163000137").first()
        assert cliente_atualizado.nome_fantasia == "Nome Atualizado"
        assert cliente_atualizado.consultor == "MANU"

    def test_upload_rejeita_cnpj_alucinacao(self, client_admin, db_session):
        """
        R8: CNPJ da lista ALUCINACAO deve ser rejeitado (ignorado).
        O cliente nao deve ser inserido no banco.
        """
        cnpj_alucinacao = "00000000000000"  # Sempre na lista de ALUCINACAO
        xlsx_bytes = _criar_xlsx_bytes(
            ["CNPJ", "Nome", "Dias sem compra", "Consultor", "Situacao"],
            [
                [cnpj_alucinacao, "Cliente Fake", 30, "Manu Vitao", "ATIVO"],
                ["74485163000137", "Cliente Real", 15, "Manu Vitao", "ATIVO"],
            ],
        )
        resp = client_admin.post(
            "/api/import/upload",
            files={"file": ("carteira.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        # Apenas 1 inserido (o real), 1 ignorado (ALUCINACAO)
        assert data["inseridos"] == 1
        assert data["ignorados"] == 1

        # Confirmar que o CNPJ de ALUCINACAO NAO foi inserido
        cliente_fake = db_session.query(Cliente).filter(Cliente.cnpj == cnpj_alucinacao).first()
        assert cliente_fake is None

    def test_upload_normaliza_cnpj_float(self, client_admin, db_session):
        """
        R5: CNPJs lidos como float pelo openpyxl devem ser normalizados para String(14).
        O CNPJ 74485163000137.0 deve virar '74485163000137'.
        """
        # Simular CNPJ como float (como o openpyxl as vezes le de celulas numericas)
        xlsx_bytes = _criar_xlsx_bytes(
            ["CNPJ", "Nome", "Dias sem compra", "Consultor", "Situacao"],
            [[74485163000137.0, "Distribuidora Float", 20, "MANU", "ATIVO"]],
        )
        resp = client_admin.post(
            "/api/import/upload",
            files={"file": ("carteira.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200, resp.text

        # Verificar que cliente foi inserido com CNPJ como string
        cliente = db_session.query(Cliente).filter(Cliente.cnpj == "74485163000137").first()
        assert cliente is not None
        assert isinstance(cliente.cnpj, str)
        assert len(cliente.cnpj) == 14


# ---------------------------------------------------------------------------
# Testes: POST /api/import/upload — Mercos Vendas (Two-Base)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _OPENPYXL_DISPONIVEL, reason="openpyxl nao instalado")
class TestUploadMercosVendas:
    """FR-006 + R1 — Two-Base Architecture: vendas com valor > 0 vao para tabela vendas."""

    def test_upload_mercos_vendas_insere_venda_e_cliente(self, client_admin, db_session):
        """
        Linha com CNPJ valido + valor > 0 + data deve:
          - Inserir/atualizar o cliente
          - Inserir venda na tabela vendas (Two-Base: R4)
        """
        xlsx_bytes = _criar_xlsx_bytes(
            ["CNPJ", "Nome Fantasia", "Valor Total", "Data do Pedido", "Consultor"],
            [["74485163000137", "Distribuidora Sul", 1500.0, "2026-03-15", "Manu Vitao"]],
        )
        resp = client_admin.post(
            "/api/import/upload",
            files={"file": ("vendas_marco.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["status"] == "CONCLUIDO"

        # Verificar venda inserida (Two-Base: valor > 0 vai para vendas)
        venda = db_session.query(Venda).filter(Venda.cnpj == "74485163000137").first()
        assert venda is not None
        assert venda.valor_pedido == 1500.0
        assert venda.fonte == "MERCOS"
        assert venda.classificacao_3tier == "REAL"
        assert venda.consultor == "MANU"

    def test_upload_mercos_vendas_sem_valor_nao_cria_venda(self, client_admin, db_session):
        """
        R4 — Two-Base: linha sem valor (None ou 0) NAO deve criar registro em vendas.
        O cliente pode ser inserido, mas sem a venda correspondente.
        """
        xlsx_bytes = _criar_xlsx_bytes(
            ["CNPJ", "Nome Fantasia", "Valor Total", "Data do Pedido", "Consultor"],
            [["74485163000137", "Distribuidora Sul", None, "2026-03-15", "Manu Vitao"]],
        )
        resp = client_admin.post(
            "/api/import/upload",
            files={"file": ("vendas.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200, resp.text

        # Verificar que NENHUMA venda foi inserida
        vendas = db_session.query(Venda).filter(Venda.cnpj == "74485163000137").all()
        assert len(vendas) == 0

    def test_upload_mercos_vendas_classifica_real(self, client_admin, db_session):
        """FR-004: vendas importadas do Mercos devem ter classificacao_3tier = REAL."""
        xlsx_bytes = _criar_xlsx_bytes(
            ["CNPJ", "Nome Fantasia", "Valor Total", "Data do Pedido", "Consultor"],
            [["74485163000137", "Distribuidora Sul", 2000.0, "2026-02-10", "LARISSA"]],
        )
        client_admin.post(
            "/api/import/upload",
            files={"file": ("vendas.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        venda = db_session.query(Venda).filter(Venda.cnpj == "74485163000137").first()
        assert venda is not None
        assert venda.classificacao_3tier == "REAL"


# ---------------------------------------------------------------------------
# Testes: POST /api/import/upload — SAP Cadastro
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _OPENPYXL_DISPONIVEL, reason="openpyxl nao instalado")
class TestUploadSapCadastro:
    """FR-002 — Processamento de SAP Cadastro."""

    def test_upload_sap_cadastro_insere_clientes(self, client_admin, db_session):
        """
        Upload de SAP Cadastro deve inserir clientes com campos SAP corretos.
        """
        xlsx_bytes = _criar_xlsx_bytes(
            ["Codigo do Cliente", "CNPJ", "Razao Social", "Nome Fantasia", "Cidade", "UF"],
            [["SAP001", "74485163000137", "Distribuidora Sul LTDA", "Dist. Sul", "Curitiba", "PR"]],
        )
        resp = client_admin.post(
            "/api/import/upload",
            files={"file": ("sap_cadastro.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["status"] == "CONCLUIDO"
        assert data["tipo"] == "SAP_CADASTRO"
        assert data["inseridos"] == 1

        # Verificar campos SAP no banco
        cliente = db_session.query(Cliente).filter(Cliente.cnpj == "74485163000137").first()
        assert cliente is not None
        assert cliente.codigo_cliente == "SAP001"
        assert cliente.razao_social == "Distribuidora Sul LTDA"
        assert cliente.cidade == "Curitiba"
        assert cliente.uf == "PR"
        assert cliente.classificacao_3tier == "REAL"


# ---------------------------------------------------------------------------
# Testes: GET /api/import/history
# ---------------------------------------------------------------------------

class TestImportHistory:
    """FR-001 (historico) — GET /api/import/history."""

    def _criar_job_db(self, db: Session, status: str = "CONCLUIDO") -> ImportJob:
        """Helper: insere ImportJob diretamente no banco."""
        job = ImportJob(
            tipo="MERCOS_CARTEIRA",
            arquivo_nome="carteira.xlsx",
            status=status,
            registros_lidos=10,
            registros_inseridos=8,
            registros_atualizados=2,
            registros_ignorados=0,
        )
        db.add(job)
        db.commit()
        return job

    def test_history_retorna_lista_vazia_sem_jobs(self, client_admin):
        """Sem jobs, history deve retornar total=0 e items=[]."""
        resp = client_admin.get("/api/import/history")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_history_retorna_jobs_existentes(self, client_admin, db_session):
        """Com 2 jobs inseridos, history deve retornar total=2."""
        self._criar_job_db(db_session, "CONCLUIDO")
        self._criar_job_db(db_session, "ERRO")

        resp = client_admin.get("/api/import/history")
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_history_campos_presentes(self, client_admin, db_session):
        """Cada item do historico deve ter os campos esperados."""
        self._criar_job_db(db_session)

        resp = client_admin.get("/api/import/history")
        item = resp.json()["items"][0]

        campos_esperados = ["id", "tipo", "arquivo", "status", "registros_lidos",
                            "inseridos", "atualizados", "ignorados", "erro_mensagem"]
        for campo in campos_esperados:
            assert campo in item, f"Campo '{campo}' ausente no historico"

    def test_history_limita_a_20_jobs(self, client_admin, db_session):
        """History deve retornar no maximo 20 itens, mesmo com 25 jobs no banco."""
        for i in range(25):
            job = ImportJob(
                tipo="MERCOS_CARTEIRA",
                arquivo_nome=f"carteira_{i}.xlsx",
                status="CONCLUIDO",
                registros_lidos=i,
                registros_inseridos=i,
                registros_atualizados=0,
                registros_ignorados=0,
            )
            db_session.add(job)
        db_session.commit()

        resp = client_admin.get("/api/import/history")
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["total"] == 25           # total real
        assert len(data["items"]) == 20      # retorna apenas 20


# ---------------------------------------------------------------------------
# Testes: Recalculo de Score e Sinaleiro pos-import
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _OPENPYXL_DISPONIVEL, reason="openpyxl nao instalado")
class TestRecalculoInteligencia:
    """FR-006 — Score + Sinaleiro recalculados apos import."""

    def test_score_calculado_apos_import(self, client_admin, db_session):
        """
        Apos upload de Mercos Carteira, Score e Sinaleiro devem ser calculados.
        Clientes inseridos sem score (None) devem ter score preenchido apos import.
        """
        xlsx_bytes = _criar_xlsx_bytes(
            ["CNPJ", "Nome", "Dias sem compra", "Consultor", "Situacao", "Ciclo Medio"],
            [["74485163000137", "Distribuidora Sul", 30, "MANU", "ATIVO", 45]],
        )
        resp = client_admin.post(
            "/api/import/upload",
            files={"file": ("carteira.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        )
        assert resp.status_code == 200, resp.text

        # Score e sinaleiro devem estar preenchidos
        db_session.expire_all()
        cliente = db_session.query(Cliente).filter(Cliente.cnpj == "74485163000137").first()
        assert cliente is not None
        assert cliente.score is not None
        assert cliente.score >= 0.0
        assert cliente.sinaleiro in ("VERDE", "AMARELO", "LARANJA", "VERMELHO", "ROXO")


# ---------------------------------------------------------------------------
# Testes: Seguranca — autenticacao
# ---------------------------------------------------------------------------

class TestSegurancaImport:
    """Verificacoes de autorizacao — apenas admin acessa os endpoints de import."""

    def test_upload_sem_autenticacao_retorna_401(self):
        """Endpoint de upload sem token deve retornar 401."""
        client = TestClient(app, raise_server_exceptions=True)
        resp = client.post(
            "/api/import/upload",
            files={"file": ("test.xlsx", b"", "application/xlsx")},
        )
        assert resp.status_code == 401, resp.text

    def test_history_sem_autenticacao_retorna_401(self):
        """Endpoint de history sem token deve retornar 401."""
        client = TestClient(app, raise_server_exceptions=True)
        resp = client.get("/api/import/history")
        assert resp.status_code == 401, resp.text
