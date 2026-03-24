"""
CRM VITAO360 — Seed do banco de dados

Lê os JSONs produzidos pelo pipeline motor e popula as tabelas
`clientes` e `agenda_items`.

Uso:
    python -m backend.app.services.seed

Fontes:
    data/output/motor/pipeline_output.json   — 1581 clientes
    data/output/motor/agenda_MANU.json
    data/output/motor/agenda_LARISSA.json
    data/output/motor/agenda_JULIO.json
    data/output/motor/agenda_DAIANE.json

REGRAS:
    R5  — CNPJ sempre String(14), zero-padded, nunca float.
    R8  — Dados ALUCINACAO são ignorados no seed (classificacao_3tier check).
    R4  — faturamento_total: APENAS de registros tipo VENDA (pipeline já garante).
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Ajustar sys.path para rodar como script direto também
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # services/ -> app/ -> backend/ -> root
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from backend.app.database import Base, SessionLocal, engine
from backend.app.models.agenda import AgendaItem
from backend.app.models.cliente import Cliente

# ---------------------------------------------------------------------------
# Caminhos dos arquivos fonte
# ---------------------------------------------------------------------------
_MOTOR_DIR = _PROJECT_ROOT / "data" / "output" / "motor"
_PIPELINE_JSON = _MOTOR_DIR / "pipeline_output.json"
_AGENDA_CONSULTORES = ["MANU", "LARISSA", "JULIO", "DAIANE"]


# ---------------------------------------------------------------------------
# Helpers de normalização
# ---------------------------------------------------------------------------

def _normalizar_cnpj(valor: Any) -> str | None:
    """
    Converte qualquer representação de CNPJ para String(14) zero-padded.
    Retorna None se o valor for vazio ou inválido.

    R5: NUNCA retorna float/int.
    """
    if valor is None:
        return None
    # Se vier como float (ex.: 1.0e13), converter para int primeiro
    if isinstance(valor, float):
        try:
            valor = int(valor)
        except (ValueError, OverflowError):
            return None
    cnpj_str = re.sub(r"\D", "", str(valor))
    if not cnpj_str:
        return None
    return cnpj_str.zfill(14)


def _to_float(valor: Any) -> float | None:
    if valor is None:
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _to_int(valor: Any) -> int | None:
    if valor is None:
        return None
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return None


def _to_bool(valor: Any) -> bool:
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return bool(valor)
    if isinstance(valor, str):
        return valor.lower() in ("true", "1", "yes", "sim")
    return False


def _str_truncate(valor: Any, maxlen: int) -> str | None:
    if valor is None:
        return None
    s = str(valor).strip()
    return s[:maxlen] if s else None


def _parse_data_agenda(texto: str) -> date:
    """
    Parseia data no formato DD/MM/YYYY (padrão das agendas) ou YYYY-MM-DD.
    Retorna hoje em caso de falha.
    """
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, fmt).date()
        except (ValueError, TypeError):
            continue
    return date.today()


# ---------------------------------------------------------------------------
# Seed: Clientes
# ---------------------------------------------------------------------------

def _seed_clientes(session, registros: list[dict]) -> int:
    """
    Insere/atualiza clientes na tabela.  Usa upsert manual:
    - Tenta insert; se CNPJ duplicado, atualiza.
    - Ignora registros ALUCINACAO (R8).
    - Ignora registros sem CNPJ válido.

    Retorna quantidade de registros inseridos/atualizados.
    """
    inseridos = 0
    ignorados_alucinacao = 0
    ignorados_sem_cnpj = 0

    for reg in registros:
        # R8: nunca integrar ALUCINACAO
        classificacao = (reg.get("classificacao_3tier") or "").upper()
        if classificacao == "ALUCINACAO":
            ignorados_alucinacao += 1
            continue

        cnpj = _normalizar_cnpj(reg.get("cnpj_normalizado"))
        if not cnpj:
            ignorados_sem_cnpj += 1
            continue

        # Verificar se já existe
        existente = session.query(Cliente).filter_by(cnpj=cnpj).first()

        dados = {
            "cnpj": cnpj,
            "nome_fantasia": _str_truncate(reg.get("nome_fantasia"), 255),
            "razao_social": _str_truncate(reg.get("razao_social"), 255),
            "uf": _str_truncate(reg.get("uf"), 2),
            "cidade": _str_truncate(reg.get("cidade"), 100),
            "consultor": _str_truncate(reg.get("consultor_normalizado"), 50),
            "situacao": _str_truncate(reg.get("situacao"), 20),
            "dias_sem_compra": _to_int(reg.get("dias_sem_compra")),
            "valor_ultimo_pedido": _to_float(reg.get("valor_ultimo_pedido")),
            "ciclo_medio": _to_float(reg.get("ciclo_medio")),
            "tipo_contato": _str_truncate(reg.get("tipo_contato"), 50),
            "resultado": _str_truncate(reg.get("resultado"), 50),
            "estagio_funil": _str_truncate(reg.get("estagio_funil"), 50),
            "acao_futura": _str_truncate(reg.get("acao_futura"), 100),
            "temperatura": _str_truncate(reg.get("temperatura"), 20),
            "score": _to_float(reg.get("score")),
            "prioridade": _str_truncate(
                reg.get("prioridade") or reg.get("prioridade_v2"), 5
            ),
            "sinaleiro": _str_truncate(reg.get("sinaleiro"), 20),
            "curva_abc": _str_truncate(reg.get("curva_abc"), 1),
            "n_compras": _to_int(reg.get("n_compras")),
            "tipo_cliente": _str_truncate(reg.get("tipo_cliente"), 30),
            "faturamento_total": _to_float(reg.get("faturamento_total")),
            "classificacao_3tier": _str_truncate(classificacao or "REAL", 15),
            # codigo_cliente pode vir como float (ex.: 1000091117.0) — converter para str
            "codigo_cliente": (
                str(int(float(reg["codigo_cliente"])))
                if reg.get("codigo_cliente") is not None
                else None
            ),
            "tipo_cliente_sap": _str_truncate(reg.get("tipo_cliente_sap"), 50),
            "macroregiao": _str_truncate(reg.get("macroregiao"), 50),
            "fase": _str_truncate(reg.get("fase"), 30),
            "followup_dias": _to_int(reg.get("followup_dias")),
            "grupo_dash": _str_truncate(reg.get("grupo_dash"), 50),
            "tipo_acao": _str_truncate(reg.get("tipo_acao"), 50),
            "tentativas": _str_truncate(reg.get("tentativas"), 5),
            "problema_aberto": _to_bool(reg.get("problema_aberto")),
            "followup_vencido": _to_bool(reg.get("followup_vencido")),
            "cs_no_prazo": _to_bool(reg.get("cs_no_prazo")),
            # Campos de projeção — podem não estar no pipeline_output.json atual
            "meta_anual": _to_float(reg.get("meta_anual")),
            "realizado_acumulado": _to_float(reg.get("realizado_acumulado")),
            "pct_alcancado": _to_float(reg.get("pct_alcancado")),
            "gap_valor": _to_float(reg.get("gap_valor")),
            "status_meta": _str_truncate(reg.get("status_meta"), 10),
        }

        # Sanitizar prioridade: se for "#NAME?" (fórmula quebrada), substituir por None
        if dados["prioridade"] and dados["prioridade"].startswith("#"):
            dados["prioridade"] = None

        if existente:
            for k, v in dados.items():
                if k != "cnpj":
                    setattr(existente, k, v)
        else:
            session.add(Cliente(**dados))

        inseridos += 1

    session.commit()

    if ignorados_alucinacao:
        print(f"  Ignorados (ALUCINACAO): {ignorados_alucinacao}")
    if ignorados_sem_cnpj:
        print(f"  Ignorados (sem CNPJ):   {ignorados_sem_cnpj}")

    return inseridos


# ---------------------------------------------------------------------------
# Seed: Agenda
# ---------------------------------------------------------------------------

def _seed_agenda(session, consultor: str, dados_agenda: dict) -> int:
    """
    Insere itens de agenda para um consultor.
    Faz upsert por (consultor, data_agenda, posicao).

    Retorna quantidade inserida/atualizada.
    """
    metadata = dados_agenda.get("metadata", {})
    data_str = metadata.get("data_agenda", "")
    data_ref = _parse_data_agenda(data_str)

    itens = dados_agenda.get("agenda", [])
    inseridos = 0

    for idx, item in enumerate(itens, start=1):
        cnpj = _normalizar_cnpj(item.get("cnpj"))

        existente = (
            session.query(AgendaItem)
            .filter_by(consultor=consultor, data_agenda=data_ref, posicao=idx)
            .first()
        )

        dados = {
            "cnpj": cnpj,
            "consultor": consultor,
            "data_agenda": data_ref,
            "posicao": idx,
            "nome_fantasia": _str_truncate(item.get("nome_fantasia"), 255),
            "situacao": _str_truncate(item.get("situacao"), 20),
            "temperatura": _str_truncate(item.get("temperatura"), 20),
            "score": _to_float(item.get("score")),
            "prioridade": _str_truncate(item.get("prioridade"), 5),
            "sinaleiro": _str_truncate(item.get("sinaleiro"), 20),
            "acao": _str_truncate(item.get("acao_futura"), 200),
            "followup_dias": _to_int(item.get("followup_dias")),
        }

        if existente:
            for k, v in dados.items():
                setattr(existente, k, v)
        else:
            session.add(AgendaItem(**dados))

        inseridos += 1

    session.commit()
    return inseridos


# ---------------------------------------------------------------------------
# Entry point principal
# ---------------------------------------------------------------------------

def main() -> None:
    print("=" * 60)
    print("CRM VITAO360 — Seed do banco de dados")
    print("=" * 60)

    # 1. Criar todas as tabelas (sem Alembic por ora)
    print("\n[1/3] Criando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("  Tabelas criadas (ou já existentes).")

    # 2. Carregar e inserir clientes
    print(f"\n[2/3] Carregando {_PIPELINE_JSON.name}...")
    if not _PIPELINE_JSON.exists():
        print(f"  ERRO: {_PIPELINE_JSON} não encontrado.")
        print("  Execute primeiro: python -m scripts.motor.run_pipeline")
        sys.exit(1)

    with open(_PIPELINE_JSON, encoding="utf-8") as f:
        pipeline_data = json.load(f)

    registros = pipeline_data.get("registros", [])
    print(f"  Registros no JSON: {len(registros)}")

    with SessionLocal() as session:
        qtd_clientes = _seed_clientes(session, registros)
    print(f"  Clientes inseridos/atualizados: {qtd_clientes}")

    # 3. Carregar e inserir agendas
    print("\n[3/3] Carregando agendas dos consultores...")
    total_agenda = 0

    with SessionLocal() as session:
        for consultor in _AGENDA_CONSULTORES:
            arquivo = _MOTOR_DIR / f"agenda_{consultor}.json"
            if not arquivo.exists():
                print(f"  Aviso: {arquivo.name} não encontrado — pulando {consultor}.")
                continue

            with open(arquivo, encoding="utf-8") as f:
                dados_agenda = json.load(f)

            qt = _seed_agenda(session, consultor, dados_agenda)
            total_agenda += qt
            print(f"  {consultor}: {qt} itens de agenda")

    # 4. Sumário final
    print("\n" + "=" * 60)
    print(f"Seed concluído:")
    print(f"  Clientes:     {qtd_clientes}")
    print(f"  Agenda itens: {total_agenda}")

    # Validação rápida de integridade
    with SessionLocal() as session:
        total_db = session.query(Cliente).count()
        total_ag = session.query(AgendaItem).count()
    print(f"  DB clientes:  {total_db}")
    print(f"  DB agenda:    {total_ag}")
    print("=" * 60)


if __name__ == "__main__":
    main()
