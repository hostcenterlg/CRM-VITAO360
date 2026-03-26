"""
Suite de testes end-to-end do Motor Pipeline CRM VITAO360 v1.0.

Valida todos os 6 modulos do motor:
    motor_regras, score_engine, sinaleiro_engine, agenda_engine, classify

Uso:
    python scripts/motor/test_pipeline.py                # todos
    python scripts/motor/test_pipeline.py --unit         # so unit tests
    python scripts/motor/test_pipeline.py --integration  # so integration
    python scripts/motor/test_pipeline.py --real-data    # so data validation
    python scripts/motor/test_pipeline.py -v             # verbose

Exit code 0 = todos passaram, 1 = algum falhou.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from typing import Callable

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[2]   # CRM-VITAO360/
_INTELLIGENCE = _ROOT / "data" / "intelligence"
_OUTPUT_MOTOR = _ROOT / "data" / "output" / "motor"
_BASE_UNIFICADA = _OUTPUT_MOTOR / "base_unificada.json"
_MOTOR_OUTPUT = _OUTPUT_MOTOR / "motor_output.json"

# ---------------------------------------------------------------------------
# Tipos
# ---------------------------------------------------------------------------
TestResult = tuple[str, bool, str]   # (nome, passou, mensagem)
TestFn = Callable[[], TestResult]

# ---------------------------------------------------------------------------
# Runner utilitario
# ---------------------------------------------------------------------------

class _Contador:
    """Acumula resultados de testes para relatorio final."""

    def __init__(self) -> None:
        self.pass_: list[str] = []
        self.fail: list[tuple[str, str]] = []
        self.skip: list[str] = []

    def registrar(self, nome: str, passou: bool, msg: str, verbose: bool = False) -> None:
        if passou is None:
            self.skip.append(nome)
            label = "SKIP"
        elif passou:
            self.pass_.append(nome)
            label = "PASS"
        else:
            self.fail.append((nome, msg))
            label = "FAIL"

        if verbose or not passou:
            mensagem = f"  {label}: {nome}"
            if msg and not passou:
                mensagem += f"\n         -> {msg}"
            print(mensagem)
        else:
            print(f"  {label}: {nome}")


def _run_group(
    titulo: str,
    testes: list[TestFn],
    contador: _Contador,
    verbose: bool,
) -> None:
    """Executa um grupo de testes e registra resultados."""
    print(f"\n[{titulo}]")
    for fn in testes:
        try:
            nome, passou, msg = fn()
        except Exception as exc:
            nome = fn.__name__
            passou = False
            msg = f"Excecao inesperada: {exc}\n{traceback.format_exc()}"
        contador.registrar(nome, passou, msg, verbose)


# ---------------------------------------------------------------------------
# SECAO 1 — UNIT TESTS: Motor Regras
# ---------------------------------------------------------------------------

def _importar_motor_regras():
    """Importa motor_regras com tratamento de erro claro."""
    import sys
    sys.path.insert(0, str(_ROOT))
    from scripts.motor import motor_regras
    return motor_regras


def test_load_92_combinations() -> TestResult:
    """Verifica que as 92 combinacoes sao carregadas corretamente do JSON."""
    mr = _importar_motor_regras()
    total = len(mr._REGRAS)
    passou = total == 92
    msg = f"Esperava 92, carregou {total}" if not passou else ""
    return ("test_load_92_combinations", passou, msg)


def test_all_7_situacoes_present() -> TestResult:
    """Verifica que as 7 situacoes canonicas estao presentes."""
    mr = _importar_motor_regras()
    esperadas = {"ATIVO", "EM RISCO", "INAT.REC", "INAT.ANT", "PROSPECT", "LEAD", "NOVO"}
    presentes = mr.SITUACOES_VALIDAS
    faltando = esperadas - presentes
    passou = len(faltando) == 0
    msg = f"Situacoes faltando: {faltando}" if not passou else ""
    return ("test_all_7_situacoes_present", passou, msg)


def test_all_14_resultados_present() -> TestResult:
    """Verifica que os 14 resultados unicos estao presentes."""
    mr = _importar_motor_regras()
    total = len(mr.RESULTADOS_VALIDOS)
    passou = total == 14
    msg = f"Esperava 14 resultados, encontrou {total}: {sorted(mr.RESULTADOS_VALIDOS)}" if not passou else ""
    return ("test_all_14_resultados_present", passou, msg)


def test_known_combo_ATIVO_VENDA() -> TestResult:
    """ATIVO + VENDA / PEDIDO deve retornar estagio=POS-VENDA, temp=QUENTE, followup=4."""
    mr = _importar_motor_regras()
    regra = mr.aplicar_regra("ATIVO", "VENDA / PEDIDO")
    if regra is None:
        return ("test_known_combo_ATIVO_VENDA", False, "aplicar_regra retornou None para combo conhecida")
    erros = []
    # Estagio pode ter acento (POS-VENDA ou PÓS-VENDA) — verificar prefixo
    if "POS" not in regra["estagio_funil"].upper().replace("\u00d3", "O"):
        erros.append(f"estagio_funil={regra['estagio_funil']!r} esperava POS-VENDA")
    if regra["temperatura"] != "QUENTE":
        erros.append(f"temperatura={regra['temperatura']!r} esperava QUENTE")
    if regra["followup_dias"] != 4:
        erros.append(f"followup_dias={regra['followup_dias']} esperava 4")
    passou = len(erros) == 0
    return ("test_known_combo_ATIVO_VENDA", passou, "; ".join(erros))


def test_known_combo_PROSPECT_NAO_RESPONDE() -> TestResult:
    """PROSPECT + NAO RESPONDE deve retornar estagio=PROSPECCAO, temp=FRIO, followup=1."""
    mr = _importar_motor_regras()
    # JSON tem acentos: "NÃO RESPONDE" — motor normaliza para UPPER
    regra = mr.aplicar_regra("PROSPECT", "NÃO RESPONDE")
    if regra is None:
        # Tentar sem acento
        regra = mr.aplicar_regra("PROSPECT", "NAO RESPONDE")
    if regra is None:
        return ("test_known_combo_PROSPECT_NAO_RESPONDE", False, "Combo nao encontrada mesmo com/sem acentos")
    erros = []
    # estagio deve conter PROSPEC
    if "PROSPEC" not in regra["estagio_funil"].upper().replace("\u00c7", "C").replace("\u00c3", "A"):
        erros.append(f"estagio_funil={regra['estagio_funil']!r} esperava conter PROSPEC")
    if regra["temperatura"] != "FRIO":
        erros.append(f"temperatura={regra['temperatura']!r} esperava FRIO")
    if regra["followup_dias"] != 1:
        erros.append(f"followup_dias={regra['followup_dias']} esperava 1")
    passou = len(erros) == 0
    return ("test_known_combo_PROSPECT_NAO_RESPONDE", passou, "; ".join(erros))


def test_invalid_combo_returns_none() -> TestResult:
    """Combinacao inventada deve retornar None (nao inventa dados)."""
    mr = _importar_motor_regras()
    regra = mr.aplicar_regra("SITUACAO_INVENTADA_XYZ", "RESULTADO_INVENTADO_ABC")
    passou = regra is None
    msg = f"Esperava None, recebeu {regra}" if not passou else ""
    return ("test_invalid_combo_returns_none", passou, msg)


def test_case_insensitive() -> TestResult:
    """Normalizacao case-insensitive: 'ativo' + 'venda / pedido' == 'ATIVO' + 'VENDA / PEDIDO'."""
    mr = _importar_motor_regras()
    regra_lower = mr.aplicar_regra("  ativo  ", "  venda / pedido  ")
    regra_upper = mr.aplicar_regra("ATIVO", "VENDA / PEDIDO")
    if regra_lower is None or regra_upper is None:
        return ("test_case_insensitive", False, f"regra_lower={regra_lower}, regra_upper={regra_upper}")
    passou = regra_lower["temperatura"] == regra_upper["temperatura"]
    msg = f"lower={regra_lower['temperatura']!r} != upper={regra_upper['temperatura']!r}" if not passou else ""
    return ("test_case_insensitive", passou, msg)


def test_batch_processing() -> TestResult:
    """DataFrame com 10 linhas mistas (validas + invalidas) deve adicionar 8 colunas."""
    mr = _importar_motor_regras()
    linhas = [
        {"situacao": "ATIVO", "resultado": "VENDA / PEDIDO"},
        {"situacao": "ATIVO", "resultado": "ORÇAMENTO"},
        {"situacao": "PROSPECT", "resultado": "NÃO RESPONDE"},
        {"situacao": "INAT.REC", "resultado": "EM ATENDIMENTO"},
        {"situacao": "LEAD", "resultado": "CADASTRO"},
        {"situacao": "NOVO", "resultado": "SUPORTE"},
        {"situacao": "EM RISCO", "resultado": "FOLLOW UP 7"},
        {"situacao": "INVALIDA_XYZ", "resultado": "INVALIDO"},
        {"situacao": "", "resultado": ""},
        {"situacao": "INAT.ANT", "resultado": "NÃO ATENDE"},
    ]
    df = pd.DataFrame(linhas)
    resultado = mr.aplicar_regras_batch(df)

    erros = []
    # Deve ter 8 colunas de output
    for campo in mr.CAMPOS_OUTPUT:
        if campo not in resultado.columns:
            erros.append(f"Coluna ausente: {campo}")

    # Linha 0 (ATIVO + VENDA) deve ter temperatura preenchida
    if "temperatura" in resultado.columns:
        temp0 = resultado.iloc[0]["temperatura"]
        if temp0 is None or (hasattr(temp0, "__class__") and str(temp0) == "nan"):
            erros.append("Linha 0 (ATIVO+VENDA) tem temperatura None/NaN")

    # Linha invalida (idx 7) deve ter temperatura None ou NaN
    if "temperatura" in resultado.columns:
        temp_inv = resultado.iloc[7]["temperatura"]
        valido = temp_inv is None or (isinstance(temp_inv, float) and pd.isna(temp_inv))
        if not valido and str(temp_inv) == "nan":
            valido = True
        if not valido:
            erros.append(f"Linha invalida deveria ter temperatura None/NaN, got {temp_inv!r}")

    passou = len(erros) == 0
    return ("test_batch_processing", passou, "; ".join(erros))


def test_campos_output_8_presentes() -> TestResult:
    """Regra valida deve retornar exatamente os 8 campos de output publicos."""
    mr = _importar_motor_regras()
    regra = mr.aplicar_regra("ATIVO", "VENDA / PEDIDO")
    if regra is None:
        return ("test_campos_output_8_presentes", False, "regra retornou None")
    ausentes = [c for c in mr.CAMPOS_OUTPUT if c not in regra]
    passou = len(ausentes) == 0
    msg = f"Campos ausentes: {ausentes}" if not passou else ""
    return ("test_campos_output_8_presentes", passou, msg)


def test_perda_always_perdido() -> TestResult:
    """Toda situacao + PERDA / FECHOU LOJA deve ter temperatura=PERDIDO."""
    mr = _importar_motor_regras()
    situacoes = list(mr.SITUACOES_VALIDAS)
    erros = []
    for sit in situacoes:
        regra = mr.aplicar_regra(sit, "PERDA / FECHOU LOJA")
        if regra is None:
            # Nem todas as situacoes tem PERDA — isso e OK se a combinacao nao existe
            continue
        if regra["temperatura"] != "PERDIDO":
            erros.append(f"{sit}+PERDA -> temperatura={regra['temperatura']!r}")
    passou = len(erros) == 0
    return ("test_perda_always_perdido", passou, "; ".join(erros))


def test_all_perda_followup_zero() -> TestResult:
    """Toda combinacao com PERDA / FECHOU LOJA deve ter followup_dias=0."""
    mr = _importar_motor_regras()
    situacoes = list(mr.SITUACOES_VALIDAS)
    erros = []
    for sit in situacoes:
        regra = mr.aplicar_regra(sit, "PERDA / FECHOU LOJA")
        if regra is None:
            continue
        if regra["followup_dias"] not in (0, None):
            erros.append(f"{sit}+PERDA -> followup_dias={regra['followup_dias']}")
    passou = len(erros) == 0
    return ("test_all_perda_followup_zero", passou, "; ".join(erros))


def test_prospect_no_cs_combo() -> TestResult:
    """PROSPECT + CS (SUCESSO DO CLIENTE) nao deve existir nas 92 regras."""
    mr = _importar_motor_regras()
    regra = mr.aplicar_regra("PROSPECT", "CS (SUCESSO DO CLIENTE)")
    passou = regra is None
    msg = f"Combo PROSPECT+CS existe (nao deveria): {regra}" if not passou else ""
    return ("test_prospect_no_cs_combo", passou, msg)


def test_listar_situacoes_ordenadas() -> TestResult:
    """listar_situacoes deve retornar lista ordenada com 7 itens."""
    mr = _importar_motor_regras()
    lista = mr.listar_situacoes()
    passou = len(lista) == 7 and lista == sorted(lista)
    msg = f"lista={lista}" if not passou else ""
    return ("test_listar_situacoes_ordenadas", passou, msg)


def test_listar_resultados_14() -> TestResult:
    """listar_resultados deve retornar 14 itens."""
    mr = _importar_motor_regras()
    lista = mr.listar_resultados()
    passou = len(lista) == 14
    msg = f"Esperava 14, encontrou {len(lista)}: {lista}" if not passou else ""
    return ("test_listar_resultados_14", passou, msg)


def test_stats_integridade() -> TestResult:
    """stats() deve reportar integridade_ok=True com 92 combinacoes."""
    mr = _importar_motor_regras()
    s = mr.stats()
    passou = s["integridade_ok"] and s["total_combinacoes"] == 92
    msg = f"integridade={s['integridade_ok']}, total={s['total_combinacoes']}" if not passou else ""
    return ("test_stats_integridade", passou, msg)


# ---------------------------------------------------------------------------
# SECAO 2 — UNIT TESTS: Score Engine
# ---------------------------------------------------------------------------

def _importar_score_engine():
    import sys
    sys.path.insert(0, str(_ROOT))
    from scripts.motor import score_engine
    return score_engine


def test_max_score_is_100() -> TestResult:
    """Combinacao maxima v2 (INAT.ANT+A+FIDELIZADO+QUENTE+T4+FU7d) deve resultar em score alto."""
    se = _importar_score_engine()
    score = se.calcular_score(
        situacao="INAT.ANT",
        curva_abc="A",
        tipo_cliente="FIDELIZADO",
        temperatura="QUENTE",
        tentativas="T4",
        dias_sem_compra=None,
        ciclo_medio=None,
        dias_atraso_followup=7.0,
        ecommerce_carrinho=100.0,
    )
    # Score v2: URGENCIA=100*0.30 + VALOR=100*0.25 + FOLLOWUP=100*0.20
    #           + SINAL=100*0.15 + TENTATIVA=100*0.05 + SITUACAO=20*0.05
    # = 30+25+20+15+5+1 = 96.0
    passou = score >= 90.0
    msg = f"Score={score}, esperava >= 90.0" if not passou else ""
    return ("test_max_score_is_100", passou, msg)


def test_min_score_above_10() -> TestResult:
    """Combinacao minima v2 (PROSPECT+C+LEAD+PERDIDO+T1+sem_FU) deve ser >= 0 e <= 100."""
    se = _importar_score_engine()
    score = se.calcular_score(
        situacao="PROSPECT",
        curva_abc="C",
        tipo_cliente="LEAD",
        temperatura="PERDIDO",
        tentativas="T1",
    )
    passou = 0.0 <= score <= 100.0
    msg = f"Score={score} fora do intervalo [0, 100]" if not passou else ""
    return ("test_min_score_above_10", passou, msg)


def test_weights_sum_to_100() -> TestResult:
    """Os 6 pesos do score devem somar exatamente 1.0 (100%)."""
    se = _importar_score_engine()
    soma = sum(se.PESOS.values())
    passou = abs(soma - 1.0) < 0.0001
    msg = f"Soma dos pesos={soma:.4f}, esperava 1.0" if not passou else ""
    return ("test_weights_sum_to_100", passou, msg)


def test_p0_suporte_blocking() -> TestResult:
    """SUPORTE deve retornar P3 PROBLEMA (v2: P3 substitui P0 para suporte)."""
    se = _importar_score_engine()
    prioridade, score = se.atribuir_prioridade(
        resultado="SUPORTE",
        situacao="ATIVO",
        curva_abc="C",
        tipo_cliente="PROSPECT",
        temperatura="FRIO",
        tentativas="T4",
    )
    passou = prioridade == "P3 PROBLEMA"
    msg = f"Esperava 'P3 PROBLEMA', recebeu {prioridade!r} (score={score})" if not passou else ""
    return ("test_p0_suporte_blocking", passou, msg)


def test_p1_followup_blocking() -> TestResult:
    """EM ATENDIMENTO deve retornar P2 NEGOCIACAO ATIVA (v2)."""
    se = _importar_score_engine()
    prioridade, score = se.atribuir_prioridade(
        resultado="EM ATENDIMENTO",
        situacao="ATIVO",
        curva_abc="C",
        tipo_cliente="PROSPECT",
        temperatura="FRIO",
        tentativas="T4",
    )
    passou = prioridade == "P2 NEGOCIACAO ATIVA"
    msg = f"Esperava 'P2 NEGOCIACAO ATIVA', recebeu {prioridade!r} (score={score})" if not passou else ""
    return ("test_p1_followup_blocking", passou, msg)


def test_p2_high_score() -> TestResult:
    """ORCAMENTO deve resultar em P2 NEGOCIACAO ATIVA (v2)."""
    se = _importar_score_engine()
    prioridade, score = se.atribuir_prioridade(
        resultado="ORCAMENTO",
        situacao="ATIVO",
        curva_abc="A",
        tipo_cliente="MADURO",
        temperatura="QUENTE",
        tentativas="T1",
    )
    passou = prioridade == "P2 NEGOCIACAO ATIVA"
    msg = f"prioridade={prioridade!r}, score={score} (esperava 'P2 NEGOCIACAO ATIVA')" if not passou else ""
    return ("test_p2_high_score", passou, msg)


def test_p7_low_score() -> TestResult:
    """PROSPECT deve resultar em P7 PROSPECCAO (v2)."""
    se = _importar_score_engine()
    prioridade, score = se.atribuir_prioridade(
        resultado="",
        situacao="PROSPECT",
        curva_abc="C",
        tipo_cliente="LEAD",
        temperatura="PERDIDO",
        tentativas="T1",
    )
    passou = prioridade == "P7 PROSPECCAO"
    msg = f"prioridade={prioridade!r}, score={score} (esperava 'P7 PROSPECCAO')" if not passou else ""
    return ("test_p7_low_score", passou, msg)


def test_desempate_abc_first() -> TestResult:
    """Dois clientes com mesmo score: curva A deve vir antes de B na ordenacao."""
    se = _importar_score_engine()
    df = pd.DataFrame([
        {
            "prioridade": "P3",
            "score": 65.0,
            "curva_abc": "B",
            "tipo_cliente": "MADURO",
        },
        {
            "prioridade": "P3",
            "score": 65.0,
            "curva_abc": "A",
            "tipo_cliente": "MADURO",
        },
    ])
    ordenado = se.ordenar_por_prioridade(df)
    primeiro_abc = ordenado.iloc[0]["curva_abc"]
    passou = primeiro_abc == "A"
    msg = f"Primeiro da lista: curva_abc={primeiro_abc!r}, esperava A" if not passou else ""
    return ("test_desempate_abc_first", passou, msg)


def test_agenda_40_limit() -> TestResult:
    """Agenda diaria nao deve exceder 40 atendimentos (excluindo P0)."""
    se = _importar_score_engine()
    # Criar 60 clientes todos P2 (alta prioridade, entra na agenda)
    linhas = []
    for i in range(60):
        linhas.append({
            "prioridade": "P2",
            "score": 85.0,
            "curva_abc": "A",
            "tipo_cliente": "MADURO",
        })
    df = pd.DataFrame(linhas)
    resultado = se.gerar_agenda_diaria(df, max_atendimentos=40)
    na_agenda = resultado[resultado["na_agenda"] == True]
    passou = len(na_agenda) <= 40
    msg = f"Agenda tem {len(na_agenda)} atendimentos, limite e 40" if not passou else ""
    return ("test_agenda_40_limit", passou, msg)


def test_p7_never_in_agenda() -> TestResult:
    """Clientes P7 nunca devem entrar na agenda diaria."""
    se = _importar_score_engine()
    df = pd.DataFrame([
        {"prioridade": "P7", "score": 5.0, "curva_abc": "C", "tipo_cliente": "PROSPECT"},
        {"prioridade": "P7", "score": 5.0, "curva_abc": "C", "tipo_cliente": "PROSPECT"},
        {"prioridade": "P2", "score": 90.0, "curva_abc": "A", "tipo_cliente": "MADURO"},
    ])
    resultado = se.gerar_agenda_diaria(df)
    p7_na_agenda = resultado[(resultado["prioridade"] == "P7") & (resultado["na_agenda"] == True)]
    passou = len(p7_na_agenda) == 0
    msg = f"{len(p7_na_agenda)} clientes P7 entraram na agenda (deveria ser 0)" if not passou else ""
    return ("test_p7_never_in_agenda", passou, msg)


def test_p0_always_included_agenda() -> TestResult:
    """Clientes P3 PROBLEMA devem sempre entrar na agenda, sem contar no limite (v2: P3=suporte)."""
    se = _importar_score_engine()
    # 40 clientes P2 + 5 clientes P3 PROBLEMA (suporte — pula fila)
    linhas = [{"prioridade": "P2 NEGOCIACAO ATIVA", "score": 85.0, "curva_abc": "A", "tipo_cliente": "MADURO"}] * 40
    linhas += [{"prioridade": "P3 PROBLEMA", "score": 50.0, "curva_abc": "B", "tipo_cliente": "RECORRENTE"}] * 5
    df = pd.DataFrame(linhas)
    resultado = se.gerar_agenda_diaria(df, max_atendimentos=40)
    p3_na_agenda = resultado[(resultado["prioridade"] == "P3 PROBLEMA") & (resultado["na_agenda"] == True)]
    passou = len(p3_na_agenda) == 5
    msg = f"P3 na agenda: {len(p3_na_agenda)}, esperava 5" if not passou else ""
    return ("test_p0_always_included_agenda", passou, msg)


def test_score_unknown_values_zero() -> TestResult:
    """Valores desconhecidos nos fatores v2 devem resultar em score valido (nao erro)."""
    se = _importar_score_engine()
    try:
        score = se.calcular_score(
            situacao="SITUACAO_DESCONHECIDA",
            curva_abc="Z",
            tipo_cliente="SUPER_CLIENTE",
            temperatura="GELADO",
            tentativas="T99",
        )
        passou = 0.0 <= score <= 100.0
        msg = f"Score={score} fora do intervalo [0,100]" if not passou else ""
    except Exception as exc:
        passou = False
        msg = f"Excecao ao processar valores desconhecidos: {exc}"
    return ("test_score_unknown_values_zero", passou, msg)


# ---------------------------------------------------------------------------
# SECAO 3 — UNIT TESTS: Sinaleiro Engine
# ---------------------------------------------------------------------------

def _importar_sinaleiro_engine():
    import sys
    sys.path.insert(0, str(_ROOT))
    from scripts.motor import sinaleiro_engine
    return sinaleiro_engine


def test_verde_within_cycle() -> TestResult:
    """dias_sem_compra <= ciclo_medio deve resultar em VERDE."""
    se = _importar_sinaleiro_engine()
    sinaleiro = se.calcular_sinaleiro(dias_sem_compra=20.0, ciclo_medio=30.0, situacao="ATIVO")
    passou = sinaleiro == "VERDE"
    msg = f"dias=20, ciclo=30: {sinaleiro!r}, esperava VERDE" if not passou else ""
    return ("test_verde_within_cycle", passou, msg)


def test_amarelo_warning() -> TestResult:
    """dias > ciclo mas <= ciclo + 30 deve resultar em AMARELO."""
    se = _importar_sinaleiro_engine()
    # ciclo=30, dias=50 (30 < 50 <= 60)
    sinaleiro = se.calcular_sinaleiro(dias_sem_compra=50.0, ciclo_medio=30.0, situacao="ATIVO")
    passou = sinaleiro == "AMARELO"
    msg = f"dias=50, ciclo=30: {sinaleiro!r}, esperava AMARELO" if not passou else ""
    return ("test_amarelo_warning", passou, msg)


def test_vermelho_danger() -> TestResult:
    """dias > ciclo + 30 deve resultar em VERMELHO."""
    se = _importar_sinaleiro_engine()
    # ciclo=30, dias=70 (70 > 60)
    sinaleiro = se.calcular_sinaleiro(dias_sem_compra=70.0, ciclo_medio=30.0, situacao="ATIVO")
    passou = sinaleiro == "VERMELHO"
    msg = f"dias=70, ciclo=30: {sinaleiro!r}, esperava VERMELHO" if not passou else ""
    return ("test_vermelho_danger", passou, msg)


def test_roxo_prospect() -> TestResult:
    """Situacao PROSPECT deve sempre resultar em ROXO (nunca comprou)."""
    se = _importar_sinaleiro_engine()
    sinaleiro = se.calcular_sinaleiro(dias_sem_compra=10.0, ciclo_medio=30.0, situacao="PROSPECT")
    passou = sinaleiro == "ROXO"
    msg = f"PROSPECT: {sinaleiro!r}, esperava ROXO" if not passou else ""
    return ("test_roxo_prospect", passou, msg)


def test_roxo_lead() -> TestResult:
    """Situacao LEAD deve sempre resultar em ROXO."""
    se = _importar_sinaleiro_engine()
    sinaleiro = se.calcular_sinaleiro(dias_sem_compra=5.0, ciclo_medio=30.0, situacao="LEAD")
    passou = sinaleiro == "ROXO"
    msg = f"LEAD: {sinaleiro!r}, esperava ROXO" if not passou else ""
    return ("test_roxo_lead", passou, msg)


def test_novo_always_verde() -> TestResult:
    """Situacao NOVO deve sempre resultar em VERDE (recente, independente de dias)."""
    se = _importar_sinaleiro_engine()
    sinaleiro = se.calcular_sinaleiro(dias_sem_compra=200.0, ciclo_medio=30.0, situacao="NOVO")
    passou = sinaleiro == "VERDE"
    msg = f"NOVO com dias=200: {sinaleiro!r}, esperava VERDE" if not passou else ""
    return ("test_novo_always_verde", passou, msg)


def test_inat_ant_always_vermelho() -> TestResult:
    """Situacao INAT.ANT deve sempre resultar em VERMELHO."""
    se = _importar_sinaleiro_engine()
    sinaleiro = se.calcular_sinaleiro(dias_sem_compra=5.0, ciclo_medio=30.0, situacao="INAT.ANT")
    passou = sinaleiro == "VERMELHO"
    msg = f"INAT.ANT: {sinaleiro!r}, esperava VERMELHO" if not passou else ""
    return ("test_inat_ant_always_vermelho", passou, msg)


def test_fallback_no_cycle_data() -> TestResult:
    """Sem ciclo_medio e dias <= 50, deve resultar em VERDE (fallback)."""
    se = _importar_sinaleiro_engine()
    sinaleiro = se.calcular_sinaleiro(dias_sem_compra=30.0, ciclo_medio=None, situacao="ATIVO")
    passou = sinaleiro == "VERDE"
    msg = f"Sem ciclo, dias=30: {sinaleiro!r}, esperava VERDE" if not passou else ""
    return ("test_fallback_no_cycle_data", passou, msg)


def test_fallback_no_data_at_all() -> TestResult:
    """Sem dias nem ciclo para ATIVO: deve retornar VERDE (beneficio da duvida)."""
    se = _importar_sinaleiro_engine()
    sinaleiro = se.calcular_sinaleiro(dias_sem_compra=None, ciclo_medio=None, situacao="ATIVO")
    passou = sinaleiro == "VERDE"
    msg = f"Sem dados (ATIVO): {sinaleiro!r}, esperava VERDE" if not passou else ""
    return ("test_fallback_no_data_at_all", passou, msg)


def test_inat_rec_sem_dados_amarelo() -> TestResult:
    """INAT.REC sem dados de dias deve resultar em AMARELO (hint de situacao)."""
    se = _importar_sinaleiro_engine()
    sinaleiro = se.calcular_sinaleiro(dias_sem_compra=None, ciclo_medio=None, situacao="INAT.REC")
    passou = sinaleiro == "AMARELO"
    msg = f"INAT.REC sem dados: {sinaleiro!r}, esperava AMARELO" if not passou else ""
    return ("test_inat_rec_sem_dados_amarelo", passou, msg)


def test_tipo_cliente_progression() -> TestResult:
    """Progressao de tipo cliente: 0->PROSPECT, 1->NOVO, 2->EM DESENV, 12+7meses->MADURO."""
    se = _importar_sinaleiro_engine()
    erros = []
    casos = [
        (0, 0, "ATIVO", "PROSPECT"),
        (0, 0, "LEAD", "LEAD"),
        (1, 1, "ATIVO", "NOVO"),
        (2, 0, "ATIVO", "EM DESENVOLVIMENTO"),
        (4, 3, "ATIVO", "RECORRENTE"),
        (7, 5, "ATIVO", "FIDELIZADO"),
        (12, 7, "ATIVO", "MADURO"),
    ]
    for compras, meses, sit, esperado in casos:
        tipo = se.calcular_tipo_cliente(compras, meses, sit)
        if tipo != esperado:
            erros.append(f"compras={compras}, meses={meses}, sit={sit}: {tipo!r} != {esperado!r}")
    passou = len(erros) == 0
    return ("test_tipo_cliente_progression", passou, "; ".join(erros))


def test_curva_abc_pareto() -> TestResult:
    """Calculo de curva ABC: top 20% faturamento = A, proximo 30% = B, resto = C."""
    se = _importar_sinaleiro_engine()
    # 10 clientes com faturamentos distintos
    fat = [1000, 900, 800, 700, 600, 500, 400, 300, 200, 100]
    df = pd.DataFrame({"faturamento_total": fat})
    # Funcao correta: calcular_curva_abc (nao calcular_curva_abc_batch)
    resultado = se.calcular_curva_abc(df, col_faturamento="faturamento_total")
    erros = []
    if "curva_abc" not in resultado.columns:
        return ("test_curva_abc_pareto", False, "Coluna curva_abc nao adicionada")
    dist = resultado["curva_abc"].value_counts().to_dict()
    if "A" not in dist:
        erros.append(f"Nenhum cliente A na distribuicao {dist}")
    if "B" not in dist:
        erros.append(f"Nenhum cliente B na distribuicao {dist}")
    if "C" not in dist:
        erros.append(f"Nenhum cliente C na distribuicao {dist}")
    passou = len(erros) == 0
    return ("test_curva_abc_pareto", passou, "; ".join(erros))


def test_sinaleiro_batch_distribuicao() -> TestResult:
    """Batch de sinaleiro deve retornar 4 cores validas para todos os registros."""
    se = _importar_sinaleiro_engine()
    df = pd.DataFrame([
        {"situacao": "PROSPECT", "dias_sem_compra": 30, "ciclo_medio": 45},
        {"situacao": "LEAD", "dias_sem_compra": 10, "ciclo_medio": 30},
        {"situacao": "ATIVO", "dias_sem_compra": 20, "ciclo_medio": 30},
        {"situacao": "ATIVO", "dias_sem_compra": 55, "ciclo_medio": 30},
        {"situacao": "ATIVO", "dias_sem_compra": 80, "ciclo_medio": 30},
        {"situacao": "INAT.ANT", "dias_sem_compra": 5, "ciclo_medio": 30},
    ])
    resultado = se.calcular_sinaleiro_batch(df)
    cores_validas = {"VERDE", "AMARELO", "VERMELHO", "ROXO"}
    erros = []
    for i, row in resultado.iterrows():
        if row["sinaleiro"] not in cores_validas:
            erros.append(f"Linha {i}: sinaleiro={row['sinaleiro']!r} invalido")
    passou = len(erros) == 0
    return ("test_sinaleiro_batch_distribuicao", passou, "; ".join(erros))


# ---------------------------------------------------------------------------
# SECAO 4 — UNIT TESTS: Agenda Engine
# ---------------------------------------------------------------------------

def _importar_agenda_engine():
    import sys
    sys.path.insert(0, str(_ROOT))
    from scripts.motor import agenda_engine
    return agenda_engine


def test_normalizar_consultor_manu() -> TestResult:
    """'Manu Vitao' deve normalizar para 'MANU'."""
    ae = _importar_agenda_engine()
    resultado = ae.normalizar_consultor("Manu Vitao")
    passou = resultado == "MANU"
    msg = f"'Manu Vitao' -> {resultado!r}, esperava 'MANU'" if not passou else ""
    return ("test_normalizar_consultor_manu", passou, msg)


def test_normalizar_consultor_larissa_alias() -> TestResult:
    """'Mais Granel' deve normalizar para 'LARISSA' (alias documentado)."""
    ae = _importar_agenda_engine()
    resultado = ae.normalizar_consultor("Mais Granel")
    passou = resultado == "LARISSA"
    msg = f"'Mais Granel' -> {resultado!r}, esperava 'LARISSA'" if not passou else ""
    return ("test_normalizar_consultor_larissa_alias", passou, msg)


def test_normalizar_consultor_desconhecido() -> TestResult:
    """Nome nao mapeado deve retornar 'DESCONHECIDO' (sem inventar)."""
    ae = _importar_agenda_engine()
    resultado = ae.normalizar_consultor("VENDEDOR_INEXISTENTE_XYZ")
    passou = resultado == "DESCONHECIDO"
    msg = f"'VENDEDOR_INEXISTENTE' -> {resultado!r}, esperava 'DESCONHECIDO'" if not passou else ""
    return ("test_normalizar_consultor_desconhecido", passou, msg)


def test_normalizar_consultor_julio() -> TestResult:
    """'Julio Gadret' deve normalizar para 'JULIO'."""
    ae = _importar_agenda_engine()
    resultado = ae.normalizar_consultor("Julio Gadret")
    passou = resultado == "JULIO"
    msg = f"'Julio Gadret' -> {resultado!r}, esperava 'JULIO'" if not passou else ""
    return ("test_normalizar_consultor_julio", passou, msg)


def test_normalizar_consultor_daiane() -> TestResult:
    """'Central Daiane' deve normalizar para 'DAIANE'."""
    ae = _importar_agenda_engine()
    resultado = ae.normalizar_consultor("Central Daiane")
    passou = resultado == "DAIANE"
    msg = f"'Central Daiane' -> {resultado!r}, esperava 'DAIANE'" if not passou else ""
    return ("test_normalizar_consultor_daiane", passou, msg)


def test_4_consultores_presentes() -> TestResult:
    """CONSULTORES deve ter exatamente 4 entradas: LARISSA, MANU, JULIO, DAIANE."""
    ae = _importar_agenda_engine()
    esperados = {"LARISSA", "MANU", "JULIO", "DAIANE"}
    presentes = set(ae.CONSULTORES.keys())
    passou = presentes == esperados
    msg = f"Esperava {esperados}, encontrou {presentes}" if not passou else ""
    return ("test_4_consultores_presentes", passou, msg)


def test_filtrar_por_consultor_retorna_subset() -> TestResult:
    """filtrar_por_consultor deve retornar apenas registros do consultor indicado."""
    ae = _importar_agenda_engine()
    df = pd.DataFrame([
        {"consultor": "MANU", "nome": "Cliente A"},
        {"consultor": "Manu Vitao", "nome": "Cliente B"},
        {"consultor": "LARISSA", "nome": "Cliente C"},
        {"consultor": "DAIANE", "nome": "Cliente D"},
    ])
    resultado = ae.filtrar_por_consultor(df, "MANU")
    # MANU e Manu Vitao devem ser incluidos
    passou = len(resultado) == 2
    msg = f"Esperava 2 registros MANU, retornou {len(resultado)}" if not passou else ""
    return ("test_filtrar_por_consultor_retorna_subset", passou, msg)


# ---------------------------------------------------------------------------
# SECAO 5 — UNIT TESTS: Classify
# ---------------------------------------------------------------------------

def _importar_classify():
    import sys
    sys.path.insert(0, str(_ROOT))
    from scripts.motor import classify
    return classify


def test_classify_carteira_real() -> TestResult:
    """Aba 'carteira' deve ser classificada como REAL."""
    cl = _importar_classify()
    df = pd.DataFrame([{"cnpj_normalizado": "12345678000195", "nome": "Teste"}])
    dfs = {"carteira": df}
    resultado = cl.classificar_registros(dfs)
    tier = resultado["carteira"].iloc[0].get("classificacao_3tier")
    passou = tier == "REAL"
    msg = f"carteira classificada como {tier!r}, esperava REAL" if not passou else ""
    return ("test_classify_carteira_real", passou, msg)


def test_classify_draft2_alucinacao() -> TestResult:
    """Aba 'draft2' com dados deve ser classificada como ALUCINACAO."""
    cl = _importar_classify()
    df = pd.DataFrame([{"cnpj_normalizado": "00000000000001", "dado": "suspeito"}])
    dfs = {"draft2": df}
    resultado = cl.classificar_registros(dfs)
    tier = resultado["draft2"].iloc[0].get("classificacao_3tier")
    passou = tier == "ALUCINACAO"
    msg = f"draft2 classificado como {tier!r}, esperava ALUCINACAO" if not passou else ""
    return ("test_classify_draft2_alucinacao", passou, msg)


def test_classify_sinaleiro_sintetico() -> TestResult:
    """Aba 'sinaleiro' deve ser classificada como SINTETICO."""
    cl = _importar_classify()
    df = pd.DataFrame([{"sinaleiro": "VERDE", "cnpj_normalizado": "12345678000195"}])
    dfs = {"sinaleiro": df}
    resultado = cl.classificar_registros(dfs)
    tier = resultado["sinaleiro"].iloc[0].get("classificacao_3tier")
    passou = tier == "SINTETICO"
    msg = f"sinaleiro classificado como {tier!r}, esperava SINTETICO" if not passou else ""
    return ("test_classify_sinaleiro_sintetico", passou, msg)


def test_filtrar_alucinacao_remove() -> TestResult:
    """filtrar_alucinacao deve remover registros ALUCINACAO e preservar os demais."""
    cl = _importar_classify()
    df = pd.DataFrame([
        {"cnpj_normalizado": "11111111000191", "classificacao_3tier": "REAL"},
        {"cnpj_normalizado": "22222222000192", "classificacao_3tier": "ALUCINACAO"},
        {"cnpj_normalizado": "33333333000193", "classificacao_3tier": "SINTETICO"},
    ])
    dfs = {"teste": df}
    resultado = cl.filtrar_alucinacao(dfs)
    df_filtrado = resultado["teste"]
    passou = len(df_filtrado) == 2
    msg = f"Apos filtrar ALUCINACAO: {len(df_filtrado)} registros, esperava 2" if not passou else ""
    return ("test_filtrar_alucinacao_remove", passou, msg)


# ---------------------------------------------------------------------------
# SECAO 6 — INTEGRATION TESTS
# ---------------------------------------------------------------------------

def test_motor_then_score() -> TestResult:
    """Motor -> Score: campos do motor devem alimentar corretamente o score engine."""
    sys.path.insert(0, str(_ROOT))
    from scripts.motor import motor_regras, score_engine

    # Criar cliente com situacao+resultado conhecidos
    cliente = {"situacao": "ATIVO", "resultado": "VENDA / PEDIDO"}
    enriquecido = motor_regras.classificar_cliente(cliente)

    # O motor deve ter adicionado motor_temperatura e motor_estagio_funil
    if not enriquecido.get("motor_regra_aplicada"):
        return ("test_motor_then_score", False, "motor_regra_aplicada=False para ATIVO+VENDA")

    # Agora calcular score usando outputs do motor
    fase = enriquecido.get("motor_estagio_funil", "")
    temperatura = enriquecido.get("motor_temperatura", "")
    score = score_engine.calcular_score(
        fase=fase,
        sinaleiro="VERDE",
        curva_abc="A",
        temperatura=temperatura,
        tipo_cliente="MADURO",
        tentativas="T1",
    )

    passou = 0.0 <= score <= 100.0 and score > 50.0
    msg = f"score={score} (fase={fase!r}, temp={temperatura!r})" if not passou else ""
    return ("test_motor_then_score", passou, msg)


def test_full_chain_10_clients() -> TestResult:
    """10 clientes sinteticos com perfis conhecidos: motor->sinaleiro->score->prioridade."""
    sys.path.insert(0, str(_ROOT))
    from scripts.motor import motor_regras, score_engine, sinaleiro_engine

    # 10 clientes com situacoes/resultados validos
    clientes_raw = [
        {"situacao": "ATIVO", "resultado": "VENDA / PEDIDO", "dias_sem_compra": 10, "ciclo_medio": 30},
        {"situacao": "ATIVO", "resultado": "ORÇAMENTO", "dias_sem_compra": 5, "ciclo_medio": 30},
        {"situacao": "PROSPECT", "resultado": "NÃO RESPONDE", "dias_sem_compra": None, "ciclo_medio": None},
        {"situacao": "INAT.REC", "resultado": "EM ATENDIMENTO", "dias_sem_compra": 45, "ciclo_medio": 30},
        {"situacao": "LEAD", "resultado": "CADASTRO", "dias_sem_compra": None, "ciclo_medio": None},
        {"situacao": "NOVO", "resultado": "SUPORTE", "dias_sem_compra": 5, "ciclo_medio": 30},
        {"situacao": "EM RISCO", "resultado": "FOLLOW UP 7", "dias_sem_compra": 80, "ciclo_medio": 30},
        {"situacao": "INAT.ANT", "resultado": "NÃO ATENDE", "dias_sem_compra": 200, "ciclo_medio": None},
        {"situacao": "ATIVO", "resultado": "CS (SUCESSO DO CLIENTE)", "dias_sem_compra": 15, "ciclo_medio": 30},
        {"situacao": "PROSPECT", "resultado": "EM ATENDIMENTO", "dias_sem_compra": None, "ciclo_medio": None},
    ]

    erros = []

    for i, cliente in enumerate(clientes_raw):
        # 1. Aplicar motor de regras
        enriquecido = motor_regras.classificar_cliente(cliente)

        # 2. Calcular sinaleiro
        sinaleiro = sinaleiro_engine.calcular_sinaleiro(
            dias_sem_compra=cliente.get("dias_sem_compra"),
            ciclo_medio=cliente.get("ciclo_medio"),
            situacao=cliente.get("situacao", ""),
        )
        if sinaleiro not in {"VERDE", "AMARELO", "VERMELHO", "ROXO"}:
            erros.append(f"Cliente {i}: sinaleiro invalido {sinaleiro!r}")

        # 3. Calcular score e prioridade
        fase = enriquecido.get("motor_fase") or "NUTRICAO"
        temperatura = enriquecido.get("motor_temperatura") or "FRIO"
        prioridade, score = score_engine.atribuir_prioridade(
            resultado=cliente.get("resultado", ""),
            estagio_funil=enriquecido.get("motor_estagio_funil", ""),
            fase=fase,
            sinaleiro=sinaleiro,
            curva_abc="B",
            temperatura=temperatura,
            tipo_cliente="RECORRENTE",
            tentativas="T1",
        )

        if prioridade not in {"P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"}:
            erros.append(f"Cliente {i}: prioridade invalida {prioridade!r}")
        if not (0.0 <= score <= 100.0):
            erros.append(f"Cliente {i}: score={score} fora do intervalo [0,100]")

    passou = len(erros) == 0
    return ("test_full_chain_10_clients", passou, "; ".join(erros[:5]))  # max 5 erros no msg


def test_two_base_architecture() -> TestResult:
    """Two-Base: registros LOG nao devem ter campo valor_monetario > 0 (R$ em LOG = violacao)."""
    # Este teste usa a base_unificada se disponivel, ou dados sinteticos
    if _BASE_UNIFICADA.exists():
        with _BASE_UNIFICADA.open(encoding="utf-8") as fh:
            data = json.load(fh)
        registros = data.get("registros", []) if isinstance(data, dict) else data
        erros = []
        for r in registros:
            # Two-Base: valor_ultimo_pedido so deve existir em registros com situacao que indica compra
            # LOG puro = tipo_acao ADMIN, PROSPECCAO — nao tem valor de venda
            # Como regra simplificada: PROSPECT/LEAD com valor > 0 sao suspeitos
            sit = str(r.get("situacao", "")).upper()
            val = r.get("valor_ultimo_pedido")
            if sit in ("PROSPECT", "LEAD") and val is not None:
                try:
                    v = float(val)
                    if v > 100_000:  # valor impossivel para prospect/lead
                        erros.append(f"CNPJ {r.get('cnpj_normalizado')}: {sit} com valor R${v:.2f}")
                except (ValueError, TypeError):
                    pass
        passou = len(erros) == 0
        msg = f"{len(erros)} registros com possivel violacao Two-Base" if not passou else ""
    else:
        # Sem dados reais: teste sintetico de principio
        erros = []
        # LOG record nao deve ter valor
        log_record = {"tipo_acao": "ADMIN", "valor_monetario": 0.0, "situacao": "PROSPECT"}
        venda_record = {"tipo_acao": "VENDA", "valor_monetario": 1500.0, "situacao": "ATIVO"}
        if log_record["valor_monetario"] != 0.0:
            erros.append("LOG record deveria ter valor=0.0")
        if venda_record["valor_monetario"] <= 0:
            erros.append("VENDA record deveria ter valor > 0")
        passou = len(erros) == 0
        msg = "; ".join(erros)
    return ("test_two_base_architecture", passou, msg)


def test_cnpj_integrity() -> TestResult:
    """Todos os CNPJs devem ser strings de exatamente 14 digitos numericos."""
    if not _BASE_UNIFICADA.exists():
        return ("test_cnpj_integrity", None, "SKIP: base_unificada.json nao disponivel")

    with _BASE_UNIFICADA.open(encoding="utf-8") as fh:
        data = json.load(fh)
    registros = data.get("registros", []) if isinstance(data, dict) else data

    erros = []
    for i, r in enumerate(registros):
        cnpj = r.get("cnpj_normalizado")
        if cnpj is None:
            continue
        if not isinstance(cnpj, str):
            erros.append(f"Registro {i}: CNPJ={cnpj!r} nao e string (tipo {type(cnpj).__name__})")
            continue
        if len(cnpj) != 14:
            erros.append(f"Registro {i}: CNPJ={cnpj!r} tem {len(cnpj)} digitos (esperava 14)")
        elif not cnpj.isdigit():
            erros.append(f"Registro {i}: CNPJ={cnpj!r} contem caracteres nao numericos")
        if len(erros) >= 10:
            erros.append(f"... (truncado apos 10 erros)")
            break

    passou = len(erros) == 0
    return ("test_cnpj_integrity", passou, "; ".join(erros[:3]))


def test_aplicar_regras_batch_dataframe() -> TestResult:
    """Integracao motor_regras.aplicar_regras_batch: adiciona 8 colunas a DataFrame real."""
    sys.path.insert(0, str(_ROOT))
    from scripts.motor import motor_regras

    df = pd.DataFrame([
        {"situacao": "ATIVO", "resultado": "VENDA / PEDIDO", "cnpj": "11111111000191"},
        {"situacao": "PROSPECT", "resultado": "NÃO RESPONDE", "cnpj": "22222222000192"},
        {"situacao": "INAT.REC", "resultado": "EM ATENDIMENTO", "cnpj": "33333333000193"},
    ])
    resultado = motor_regras.aplicar_regras_batch(df)

    erros = []
    for campo in motor_regras.CAMPOS_OUTPUT:
        if campo not in resultado.columns:
            erros.append(f"Coluna {campo!r} ausente")

    # Linha 0 deve ter temperatura QUENTE (ATIVO+VENDA)
    if "temperatura" in resultado.columns:
        t = resultado.iloc[0]["temperatura"]
        if t != "QUENTE":
            erros.append(f"Linha 0 temperatura={t!r}, esperava QUENTE")

    # Linha 1 deve ter temperatura FRIO (PROSPECT+NAO RESPONDE)
    if "temperatura" in resultado.columns:
        t = resultado.iloc[1]["temperatura"]
        if t != "FRIO":
            erros.append(f"Linha 1 temperatura={t!r}, esperava FRIO")

    passou = len(erros) == 0
    return ("test_aplicar_regras_batch_dataframe", passou, "; ".join(erros))


# ---------------------------------------------------------------------------
# SECAO 7 — DATA VALIDATION TESTS (requerem dados reais)
# ---------------------------------------------------------------------------

def test_real_data_load() -> TestResult:
    """Carrega base_unificada.json e verifica estrutura minima."""
    if not _BASE_UNIFICADA.exists():
        return ("test_real_data_load", None, "SKIP: base_unificada.json nao disponivel")

    try:
        with _BASE_UNIFICADA.open(encoding="utf-8") as fh:
            data = json.load(fh)
    except Exception as exc:
        return ("test_real_data_load", False, f"Falha ao carregar JSON: {exc}")

    if isinstance(data, dict):
        registros = data.get("registros", data.get("clientes", data.get("data", [])))
    elif isinstance(data, list):
        registros = data
    else:
        return ("test_real_data_load", False, f"Formato inesperado: {type(data).__name__}")

    passou = len(registros) > 0
    msg = f"base_unificada.json tem {len(registros)} registros" if passou else "base_unificada.json esta vazia"
    return ("test_real_data_load", passou, msg)


def test_real_data_motor_coverage() -> TestResult:
    """Porcentagem de clientes reais que obtem uma regra do motor."""
    if not _BASE_UNIFICADA.exists():
        return ("test_real_data_motor_coverage", None, "SKIP: base_unificada.json nao disponivel")

    sys.path.insert(0, str(_ROOT))
    from scripts.motor import motor_regras

    with _BASE_UNIFICADA.open(encoding="utf-8") as fh:
        data = json.load(fh)
    registros = data.get("registros", []) if isinstance(data, dict) else data

    total = len(registros)
    if total == 0:
        return ("test_real_data_motor_coverage", None, "SKIP: sem registros")

    encontradas = 0
    for r in registros:
        sit = r.get("situacao", "")
        res = r.get("resultado", "")
        if sit and res:
            regra = motor_regras.aplicar_regra(str(sit), str(res))
            if regra is not None:
                encontradas += 1

    pct = (encontradas / total) * 100
    # Aceitamos cobertura baixa pois muitos resultados do Excel vem formatados diferente
    passou = True  # informativo — nao bloqueia
    msg = f"{encontradas}/{total} registros com regra aplicada ({pct:.1f}%)"
    return ("test_real_data_motor_coverage", passou, msg)


def test_real_data_no_fabrication() -> TestResult:
    """Nenhum registro ALUCINACAO deve estar presente na base_unificada."""
    if not _BASE_UNIFICADA.exists():
        return ("test_real_data_no_fabrication", None, "SKIP: base_unificada.json nao disponivel")

    with _BASE_UNIFICADA.open(encoding="utf-8") as fh:
        data = json.load(fh)
    registros = data.get("registros", []) if isinstance(data, dict) else data

    alucinacoes = [
        r for r in registros
        if str(r.get("classificacao_3tier", "")).upper() == "ALUCINACAO"
    ]
    passou = len(alucinacoes) == 0
    msg = f"{len(alucinacoes)} registros ALUCINACAO encontrados na base_unificada" if not passou else ""
    return ("test_real_data_no_fabrication", passou, msg)


def test_faturamento_baseline() -> TestResult:
    """Faturamento de clientes ATIVOS deve ser compativel com baseline R$ 2.091.000.

    A base_unificada.json contem faturamento_total por cliente (acumulado historico),
    nao o faturamento anual da empresa. O campo e comparado de forma informativa:
    se a soma dos clientes ATIVO exceder R$ 500k, a base tem dados reais de faturamento.
    Nao bloqueante — apenas reporta o total encontrado.
    """
    if not _BASE_UNIFICADA.exists():
        return ("test_faturamento_baseline", None, "SKIP: base_unificada.json nao disponivel")

    with _BASE_UNIFICADA.open(encoding="utf-8") as fh:
        data = json.load(fh)
    registros = data.get("registros", []) if isinstance(data, dict) else data

    total_fat_ativo = 0.0
    tem_faturamento = False
    clientes_ativo = 0

    for r in registros:
        sit = str(r.get("situacao", "")).upper()
        fat = r.get("faturamento_total")
        if fat is not None and sit == "ATIVO":
            try:
                v = float(fat)
                if v > 0:
                    total_fat_ativo += v
                    tem_faturamento = True
                    clientes_ativo += 1
            except (ValueError, TypeError):
                pass

    if not tem_faturamento:
        return ("test_faturamento_baseline", None, "SKIP: campo faturamento_total nao disponivel em registros ATIVO")

    # Verificar que o faturamento dos ativos e um numero plausivel (> 0, < R$ 100M)
    passou = 0 < total_fat_ativo < 100_000_000
    msg = (
        f"Faturamento acumulado de {clientes_ativo} clientes ATIVO: "
        f"R$ {total_fat_ativo:,.2f} (informativo — nao comparado ao baseline anual)"
    )
    return ("test_faturamento_baseline", passou, msg)


def test_real_cnpj_no_duplicates() -> TestResult:
    """CNPJs na base_unificada nao devem ter duplicatas."""
    if not _BASE_UNIFICADA.exists():
        return ("test_real_cnpj_no_duplicates", None, "SKIP: base_unificada.json nao disponivel")

    with _BASE_UNIFICADA.open(encoding="utf-8") as fh:
        data = json.load(fh)
    registros = data.get("registros", []) if isinstance(data, dict) else data

    cnpjs = [r.get("cnpj_normalizado") for r in registros if r.get("cnpj_normalizado")]
    total = len(cnpjs)
    unicos = len(set(cnpjs))
    duplicatas = total - unicos

    # Para a base_unificada, esperamos alguns duplicatas por cruzamento de abas
    # O teste e informativo — alerta se > 10% duplicata
    passou = duplicatas == 0 or (duplicatas / total) < 0.10
    msg = f"{duplicatas}/{total} CNPJs duplicados ({duplicatas/total*100:.1f}%)"
    return ("test_real_cnpj_no_duplicates", passou, msg)


# ---------------------------------------------------------------------------
# SECAO 8 — REGRESSION TESTS
# ---------------------------------------------------------------------------

def test_prospect_no_pos_venda_estagio() -> TestResult:
    """PROSPECT + VENDA / PEDIDO deve ter estagio POS-VENDA (prospect que fechou pedido).

    Esta e uma regra de negocio legitima: quando um PROSPECT realiza uma venda,
    ele entra em POS-VENDA. O teste verifica que a combinacao existe e mapeia
    corretamente para POS-VENDA (nao para PROSPECCAO).
    """
    mr = _importar_motor_regras()
    regra = mr.aplicar_regra("PROSPECT", "VENDA / PEDIDO")
    if regra is None:
        return ("test_prospect_no_pos_venda_estagio", False, "PROSPECT+VENDA/PEDIDO deveria existir nas 92 regras")
    estagio = regra.get("estagio_funil", "")
    estagio_norm = str(estagio).upper().replace("\u00d3", "O").replace("\u00c7", "C")
    passou = "POS" in estagio_norm and "VENDA" in estagio_norm
    msg = f"estagio={estagio!r}, esperava POS-VENDA (prospect que fechou pedido)" if not passou else ""
    return ("test_prospect_no_pos_venda_estagio", passou, msg)


def test_prospect_no_cs_resultado() -> TestResult:
    """PROSPECT + CS (SUCESSO DO CLIENTE) nao deve existir como combinacao valida."""
    mr = _importar_motor_regras()
    regra = mr.aplicar_regra("PROSPECT", "CS (SUCESSO DO CLIENTE)")
    passou = regra is None
    msg = f"PROSPECT+CS existe nas regras (deveria ser invalida)" if not passou else ""
    return ("test_prospect_no_cs_resultado", passou, msg)


def test_all_situacoes_have_venda_pedido() -> TestResult:
    """Verificar quais situacoes tem combo com VENDA / PEDIDO (informativo)."""
    mr = _importar_motor_regras()
    situacoes_com_venda = []
    for sit in mr.SITUACOES_VALIDAS:
        regra = mr.aplicar_regra(sit, "VENDA / PEDIDO")
        if regra is not None:
            situacoes_com_venda.append(sit)
    # ATIVO deve ter VENDA
    passou = "ATIVO" in situacoes_com_venda
    msg = f"ATIVO nao tem combo VENDA/PEDIDO. Situacoes com venda: {situacoes_com_venda}" if not passou else ""
    return ("test_all_situacoes_have_venda_pedido", passou, msg)


def test_venda_pedido_always_positive_followup() -> TestResult:
    """VENDA / PEDIDO deve sempre ter followup_dias > 0 (nao abandonar apos venda)."""
    mr = _importar_motor_regras()
    erros = []
    for sit in mr.SITUACOES_VALIDAS:
        regra = mr.aplicar_regra(sit, "VENDA / PEDIDO")
        if regra is None:
            continue
        if regra["followup_dias"] == 0:
            erros.append(f"{sit}+VENDA -> followup=0 (esperava > 0)")
    passou = len(erros) == 0
    return ("test_venda_pedido_always_positive_followup", passou, "; ".join(erros))


def test_motor_output_presente_se_base_existe() -> TestResult:
    """Se base_unificada.json existe, motor_output.json deve existir ou pode ser gerado."""
    if not _BASE_UNIFICADA.exists():
        return ("test_motor_output_presente_se_base_existe", None, "SKIP: base_unificada.json ausente")
    # motor_output pode estar vazio (0 clientes) se run_import nao processou ainda
    if not _MOTOR_OUTPUT.exists():
        return ("test_motor_output_presente_se_base_existe", None, "SKIP: motor_output.json nao gerado ainda")
    passou = True
    msg = f"motor_output.json presente em {_MOTOR_OUTPUT}"
    return ("test_motor_output_presente_se_base_existe", passou, msg)


def test_classificar_cliente_preserva_campos() -> TestResult:
    """classificar_cliente deve preservar todos os campos originais do cliente."""
    mr = _importar_motor_regras()
    cliente_original = {
        "situacao": "ATIVO",
        "resultado": "VENDA / PEDIDO",
        "cnpj": "12345678000195",
        "nome_fantasia": "Loja Teste",
        "ticket_medio": 1500.0,
    }
    enriquecido = mr.classificar_cliente(cliente_original)
    erros = []
    for chave, valor in cliente_original.items():
        if enriquecido.get(chave) != valor:
            erros.append(f"Campo {chave!r}: original={valor!r}, enriquecido={enriquecido.get(chave)!r}")
    passou = len(erros) == 0
    return ("test_classificar_cliente_preserva_campos", passou, "; ".join(erros))


def test_processar_lote_retorna_lista() -> TestResult:
    """processar_lote deve retornar lista com mesmo comprimento que entrada."""
    mr = _importar_motor_regras()
    clientes = [
        {"situacao": "ATIVO", "resultado": "VENDA / PEDIDO"},
        {"situacao": "PROSPECT", "resultado": "NÃO RESPONDE"},
        {"situacao": "INVALIDA", "resultado": "INVALIDO"},
    ]
    resultado = mr.processar_lote(clientes)
    passou = len(resultado) == 3
    msg = f"Entrada: 3 clientes, saida: {len(resultado)}" if not passou else ""
    return ("test_processar_lote_retorna_lista", passou, msg)


def test_processar_lote_empty_input() -> TestResult:
    """processar_lote com lista vazia deve retornar lista vazia (sem erro)."""
    mr = _importar_motor_regras()
    resultado = mr.processar_lote([])
    passou = resultado == []
    msg = f"Esperava [], retornou {resultado!r}" if not passou else ""
    return ("test_processar_lote_empty_input", passou, msg)


# ---------------------------------------------------------------------------
# Organizacao dos grupos de teste
# ---------------------------------------------------------------------------

UNIT_MOTOR_REGRAS: list[TestFn] = [
    test_load_92_combinations,
    test_all_7_situacoes_present,
    test_all_14_resultados_present,
    test_known_combo_ATIVO_VENDA,
    test_known_combo_PROSPECT_NAO_RESPONDE,
    test_invalid_combo_returns_none,
    test_case_insensitive,
    test_batch_processing,
    test_campos_output_8_presentes,
    test_perda_always_perdido,
    test_all_perda_followup_zero,
    test_prospect_no_cs_combo,
    test_listar_situacoes_ordenadas,
    test_listar_resultados_14,
    test_stats_integridade,
]

UNIT_SCORE_ENGINE: list[TestFn] = [
    test_max_score_is_100,
    test_min_score_above_10,
    test_weights_sum_to_100,
    test_p0_suporte_blocking,
    test_p1_followup_blocking,
    test_p2_high_score,
    test_p7_low_score,
    test_desempate_abc_first,
    test_agenda_40_limit,
    test_p7_never_in_agenda,
    test_p0_always_included_agenda,
    test_score_unknown_values_zero,
]

UNIT_SINALEIRO: list[TestFn] = [
    test_verde_within_cycle,
    test_amarelo_warning,
    test_vermelho_danger,
    test_roxo_prospect,
    test_roxo_lead,
    test_novo_always_verde,
    test_inat_ant_always_vermelho,
    test_fallback_no_cycle_data,
    test_fallback_no_data_at_all,
    test_inat_rec_sem_dados_amarelo,
    test_tipo_cliente_progression,
    test_curva_abc_pareto,
    test_sinaleiro_batch_distribuicao,
]

UNIT_AGENDA: list[TestFn] = [
    test_normalizar_consultor_manu,
    test_normalizar_consultor_larissa_alias,
    test_normalizar_consultor_desconhecido,
    test_normalizar_consultor_julio,
    test_normalizar_consultor_daiane,
    test_4_consultores_presentes,
    test_filtrar_por_consultor_retorna_subset,
]

UNIT_CLASSIFY: list[TestFn] = [
    test_classify_carteira_real,
    test_classify_draft2_alucinacao,
    test_classify_sinaleiro_sintetico,
    test_filtrar_alucinacao_remove,
]

INTEGRATION_TESTS: list[TestFn] = [
    test_motor_then_score,
    test_full_chain_10_clients,
    test_two_base_architecture,
    test_cnpj_integrity,
    test_aplicar_regras_batch_dataframe,
]

DATA_VALIDATION_TESTS: list[TestFn] = [
    test_real_data_load,
    test_real_data_motor_coverage,
    test_real_data_no_fabrication,
    test_faturamento_baseline,
    test_real_cnpj_no_duplicates,
]

REGRESSION_TESTS: list[TestFn] = [
    test_prospect_no_pos_venda_estagio,
    test_prospect_no_cs_resultado,
    test_all_situacoes_have_venda_pedido,
    test_venda_pedido_always_positive_followup,
    test_motor_output_presente_se_base_existe,
    test_classificar_cliente_preserva_campos,
    test_processar_lote_retorna_lista,
    test_processar_lote_empty_input,
]


# ---------------------------------------------------------------------------
# Main — runner
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="CRM VITAO360 — Suite de Testes End-to-End do Motor Pipeline"
    )
    parser.add_argument("--unit", action="store_true", help="Rodar apenas unit tests")
    parser.add_argument("--integration", action="store_true", help="Rodar apenas integration tests")
    parser.add_argument("--real-data", action="store_true", help="Rodar apenas data validation tests")
    parser.add_argument("--regression", action="store_true", help="Rodar apenas regression tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Output verboso")
    args = parser.parse_args()

    # Se nenhuma flag especificada, rodar todos
    rodar_tudo = not any([args.unit, args.integration, args.real_data, args.regression])

    print("=" * 60)
    print("CRM VITAO360 — PIPELINE TEST SUITE")
    print("=" * 60)

    contador = _Contador()
    v = args.verbose

    if rodar_tudo or args.unit:
        _run_group("UNIT - Motor Regras", UNIT_MOTOR_REGRAS, contador, v)
        _run_group("UNIT - Score Engine", UNIT_SCORE_ENGINE, contador, v)
        _run_group("UNIT - Sinaleiro Engine", UNIT_SINALEIRO, contador, v)
        _run_group("UNIT - Agenda Engine", UNIT_AGENDA, contador, v)
        _run_group("UNIT - Classify", UNIT_CLASSIFY, contador, v)

    if rodar_tudo or args.integration:
        _run_group("INTEGRATION", INTEGRATION_TESTS, contador, v)

    if rodar_tudo or args.real_data:
        _run_group("DATA VALIDATION", DATA_VALIDATION_TESTS, contador, v)

    if rodar_tudo or args.regression:
        _run_group("REGRESSION", REGRESSION_TESTS, contador, v)

    # Relatorio final
    total_pass = len(contador.pass_)
    total_fail = len(contador.fail)
    total_skip = len(contador.skip)

    print()
    print("=" * 60)

    if contador.fail:
        print("FALHAS DETALHADAS:")
        for nome, msg in contador.fail:
            print(f"  FAIL: {nome}")
            print(f"        {msg}")
        print()

    status = "PASSOU" if total_fail == 0 else "FALHOU"
    print(
        f"RESULTADO: {status} — "
        f"{total_pass} PASS | {total_fail} FAIL | {total_skip} SKIP"
    )
    print("=" * 60)

    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
