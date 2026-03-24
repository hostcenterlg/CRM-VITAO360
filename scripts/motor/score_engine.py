"""
Score Engine — Motor de Prioridade CRM VITAO360 v1.0.

Calcula score ponderado (0-100) a partir de 6 dimensoes e atribui
prioridade P0-P7 para cada cliente. Alimenta a agenda diaria de
40 atendimentos por consultor.

Regras de negocio extraidas de:
  data/intelligence/arquitetura_9_dimensoes.json
  data/intelligence/fases_estrategicas.json

Regras inviolaveis:
  - P0/P1 sao bloqueios: entram ANTES do score ponderado
  - P7 nunca entra na agenda diaria (campanha mensal)
  - Desempate dentro de mesma prioridade: ABC > ticket > maturidade > FU vencido
  - Meta balance: se P2-P5 nao cobrem 80% da meta mensal,
    clientes PROSPECCAO recebem +20 no score (forcado)
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger("motor.score_engine")

# ---------------------------------------------------------------------------
# Constantes de negocio (regras estaveis — alterar apenas com aprovacao L3)
# ---------------------------------------------------------------------------

PESOS: dict[str, float] = {
    "FASE": 0.25,
    "SINALEIRO": 0.20,
    "CURVA_ABC": 0.20,
    "TEMPERATURA": 0.15,
    "TIPO_CLIENTE": 0.10,
    "TENTATIVAS": 0.10,
}

# Fases estrategicas principais + sub-fases operacionais que se mapeiam a elas
SCORE_FASE: dict[str, float] = {
    # Fases estrategicas canonicas
    "RECOMPRA": 100,
    "NEGOCIACAO": 80,
    "NEGOCIAÇÃO": 80,  # alias com acento
    "SALVAMENTO": 60,
    "RECUPERACAO": 40,
    "RECUPERAÇÃO": 40,  # alias com acento
    "PROSPECCAO": 30,
    "PROSPECÇÃO": 30,   # alias com acento
    "NUTRICAO": 10,
    "NUTRIÇÃO": 10,     # alias com acento
    # Sub-fases operacionais mapeadas para fase estrategica equivalente
    "POS-VENDA": 100,          # -> RECOMPRA
    "POS VENDA": 100,          # variante sem hifen
    "CS": 100,                 # Customer Success -> RECOMPRA
    "ORCAMENTO": 80,           # -> NEGOCIACAO
    "ORÇAMENTO": 80,           # alias com acento
    "EM ATENDIMENTO": 80,      # -> NEGOCIACAO
}

SCORE_SINALEIRO: dict[str, float] = {
    "VERMELHO": 100,
    "AMARELO": 60,
    "VERDE": 30,
    "ROXO": 0,
}

SCORE_CURVA_ABC: dict[str, float] = {
    "A": 100,
    "B": 60,
    "C": 30,
}

SCORE_TEMPERATURA: dict[str, float] = {
    "QUENTE": 100,
    "MORNO": 60,
    "FRIO": 30,
    "CRITICO": 20,
    "CRÍTICO": 20,  # alias com acento
    "PERDIDO": 0,
}

SCORE_TIPO_CLIENTE: dict[str, float] = {
    "MADURO": 100,
    "FIDELIZADO": 85,
    "RECORRENTE": 70,
    "EM DESENV": 50,
    "EM DESENVOLVIMENTO": 50,
    "NOVO": 30,
    "LEAD": 15,
    "PROSPECT": 10,
}

SCORE_TENTATIVAS: dict[str, float] = {
    "T1": 100,
    "T2": 70,
    "T3": 40,
    "T4": 10,
    "NUTRICAO": 5,
    "NUTRIÇÃO": 5,  # alias com acento
}

# (label, score_min, score_max) — P0 e P1 sao bloqueios, nao entram aqui
FAIXAS_PRIORIDADE: list[tuple[str, float, float]] = [
    ("P2", 80.0, 100.0),
    ("P3", 60.0, 79.9),
    ("P4", 45.0, 59.9),
    ("P5", 30.0, 44.9),
    ("P6", 15.0, 29.9),
    ("P7",  0.0, 14.9),
]

# Ordem de maturidade para desempate (mais maduro = menor indice)
_ORDEM_MATURIDADE: list[str] = [
    "MADURO", "FIDELIZADO", "RECORRENTE", "EM DESENV",
    "EM DESENVOLVIMENTO", "NOVO", "LEAD", "PROSPECT",
]

# Meta mensal padrao: R$ 3.156.614 / 12 meses
META_MENSAL_DEFAULT: float = 3_156_614.0 / 12  # ~263.051

# Limite da agenda diaria por consultor
MAX_ATENDIMENTOS_DEFAULT: int = 40

# Teto de P1 na agenda diaria
MAX_P1_AGENDA: int = 15

# Boost de score para PROSPECCAO quando meta balance ativa
BOOST_PROSPECCAO: float = 20.0


# ---------------------------------------------------------------------------
# Funcoes auxiliares internas
# ---------------------------------------------------------------------------

def _normalizar(val: object) -> str:
    """Normaliza um valor de input para string UPPER sem espacos laterais.

    Valores None, NaN ou vazios retornam string vazia ''.
    """
    if val is None:
        return ""
    s = str(val).strip().upper()
    if s in ("NAN", "NONE", "NAT", ""):
        return ""
    return s


def _lookup(tabela: dict[str, float], chave: str) -> float:
    """Busca chave na tabela de scores; retorna 0.0 se nao encontrada.

    Registra warning para valores desconhecidos que nao sao vazios,
    para facilitar diagnostico de dados sujos.
    """
    if not chave:
        return 0.0
    valor = tabela.get(chave)
    if valor is None:
        logger.debug("Valor desconhecido na lookup: '%s' — score 0.0 aplicado", chave)
        return 0.0
    return valor


def _prioridade_por_score(score: float) -> str:
    """Converte score ponderado em label de prioridade P2-P7."""
    for label, score_min, score_max in FAIXAS_PRIORIDADE:
        if score_min <= score <= score_max:
            return label
    # score exatamente 100 ja cobre P2 (80-100); guard extra
    if score >= 80.0:
        return "P2"
    return "P7"


def _indice_maturidade(tipo_cliente: str) -> int:
    """Retorna indice de maturidade para ordenacao no desempate.

    Menor indice = mais maduro = aparece primeiro na agenda.
    Valor desconhecido retorna indice alto (vai para o fim).
    """
    norm = _normalizar(tipo_cliente)
    for i, nivel in enumerate(_ORDEM_MATURIDADE):
        if nivel == norm:
            return i
    return len(_ORDEM_MATURIDADE)


def _indice_prioridade(prioridade: str) -> int:
    """Converte label de prioridade em inteiro para ordenacao (P0=0, P7=7)."""
    mapa = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4, "P5": 5, "P6": 6, "P7": 7}
    return mapa.get(prioridade, 99)


# ---------------------------------------------------------------------------
# API publica
# ---------------------------------------------------------------------------

def calcular_score(
    fase: object,
    sinaleiro: object,
    curva_abc: object,
    temperatura: object,
    tipo_cliente: object,
    tentativas: object,
) -> float:
    """Calcula o score ponderado (0-100) a partir das 6 dimensoes de input.

    Todos os inputs sao aceitos como qualquer tipo e normalizados
    internamente para UPPER string. Valores desconhecidos valem 0 na
    dimensao correspondente (sem erro).

    Args:
        fase: Fase estrategica do cliente (ex: 'RECOMPRA', 'SALVAMENTO').
        sinaleiro: Sinaleiro de saude (ex: 'VERMELHO', 'VERDE').
        curva_abc: Curva ABC de faturamento (ex: 'A', 'B', 'C').
        temperatura: Temperatura de engajamento (ex: 'QUENTE', 'FRIO').
        tipo_cliente: Maturidade na carteira (ex: 'MADURO', 'NOVO').
        tentativas: Sequencia de contato (ex: 'T1', 'T3', 'NUTRICAO').

    Returns:
        Score ponderado arredondado a 1 decimal, entre 0.0 e 100.0.
    """
    n_fase = _normalizar(fase)
    n_sinaleiro = _normalizar(sinaleiro)
    n_abc = _normalizar(curva_abc)
    n_temperatura = _normalizar(temperatura)
    n_tipo = _normalizar(tipo_cliente)
    n_tent = _normalizar(tentativas)

    score_bruto = (
        _lookup(SCORE_FASE, n_fase) * PESOS["FASE"]
        + _lookup(SCORE_SINALEIRO, n_sinaleiro) * PESOS["SINALEIRO"]
        + _lookup(SCORE_CURVA_ABC, n_abc) * PESOS["CURVA_ABC"]
        + _lookup(SCORE_TEMPERATURA, n_temperatura) * PESOS["TEMPERATURA"]
        + _lookup(SCORE_TIPO_CLIENTE, n_tipo) * PESOS["TIPO_CLIENTE"]
        + _lookup(SCORE_TENTATIVAS, n_tent) * PESOS["TENTATIVAS"]
    )

    return round(min(max(score_bruto, 0.0), 100.0), 1)


def atribuir_prioridade(
    resultado: object,
    estagio_funil: object,
    fase: object,
    sinaleiro: object,
    curva_abc: object,
    temperatura: object,
    tipo_cliente: object,
    tentativas: object,
    problema_aberto: bool = False,
    followup_vencido: bool = False,
    cs_no_prazo: bool = False,
) -> tuple[str, float]:
    """Atribui prioridade P0-P7 com base nos bloqueios e no score ponderado.

    Ordem de avaliacao:
      P0 (IMEDIATA): SUPORTE com problema aberto — pula toda a fila.
      P1 (URGENTE):  EM ATENDIMENTO com follow-up vencido, OU CS no prazo.
      P2-P7:         Score ponderado das 6 dimensoes.

    Args:
        resultado: Ultimo resultado registrado (ex: 'SUPORTE', 'EM ATENDIMENTO').
        estagio_funil: Estagio no kanban (usado para enriquecer contexto de P1).
        fase: Fase estrategica para calculo de score.
        sinaleiro: Sinaleiro de saude.
        curva_abc: Curva ABC.
        temperatura: Temperatura de engajamento.
        tipo_cliente: Maturidade na carteira.
        tentativas: Sequencia de contato.
        problema_aberto: True se ha RNC/chamado de suporte em aberto.
        followup_vencido: True se follow-up esta vencido.
        cs_no_prazo: True se CS esta dentro do prazo prometido.

    Returns:
        Tupla (prioridade, score) onde prioridade eh 'P0'..'P7'
        e score eh o score ponderado (0-100). P0 e P1 retornam
        score calculado normalmente (para fins de relatorio).
    """
    n_resultado = _normalizar(resultado)

    score = calcular_score(fase, sinaleiro, curva_abc, temperatura, tipo_cliente, tentativas)

    # Bloqueio P0: problema de suporte em aberto — risco de perda imediata
    if n_resultado == "SUPORTE" and problema_aberto:
        return ("P0", score)

    # Bloqueio P1: namoro novo nao pode esfriar / promessa precisa ser cumprida
    if (n_resultado == "EM ATENDIMENTO" and followup_vencido) or cs_no_prazo:
        return ("P1", score)

    return (_prioridade_por_score(score), score)


def calcular_score_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula score e prioridade para um DataFrame de clientes.

    Colunas de input esperadas (case-insensitive via rename interno):
      Obrigatorias: fase, sinaleiro, curva_abc, temperatura, tipo_cliente, tentativas
      Para P0/P1:   resultado (default ''), problema_aberto (default False),
                    followup_vencido (default False), cs_no_prazo (default False)

    Colunas adicionadas ao DataFrame retornado:
      score      float — score ponderado 0-100
      prioridade str   — label P0..P7

    Nao modifica o DataFrame original (retorna copia).

    Args:
        df: DataFrame com ao menos as 6 colunas de dimensoes de score.

    Returns:
        DataFrame com colunas 'score' e 'prioridade' adicionadas.

    Raises:
        KeyError: Se colunas obrigatorias de score estiverem ausentes.
    """
    resultado = df.copy()

    # Colunas obrigatorias para o score
    colunas_score = ["fase", "sinaleiro", "curva_abc", "temperatura", "tipo_cliente", "tentativas"]
    ausentes = [c for c in colunas_score if c not in resultado.columns]
    if ausentes:
        raise KeyError(
            f"Colunas obrigatorias ausentes no DataFrame: {ausentes}. "
            f"Colunas disponiveis: {list(resultado.columns)}"
        )

    # Colunas opcionais de bloqueio P0/P1 — preenchidas com default se ausentes
    if "resultado" not in resultado.columns:
        resultado["resultado"] = ""
    if "problema_aberto" not in resultado.columns:
        resultado["problema_aberto"] = False
    if "followup_vencido" not in resultado.columns:
        resultado["followup_vencido"] = False
    if "cs_no_prazo" not in resultado.columns:
        resultado["cs_no_prazo"] = False

    scores: list[float] = []
    prioridades: list[str] = []

    for _, row in resultado.iterrows():
        prio, sc = atribuir_prioridade(
            resultado=row["resultado"],
            estagio_funil=row.get("estagio_funil", ""),
            fase=row["fase"],
            sinaleiro=row["sinaleiro"],
            curva_abc=row["curva_abc"],
            temperatura=row["temperatura"],
            tipo_cliente=row["tipo_cliente"],
            tentativas=row["tentativas"],
            problema_aberto=bool(row["problema_aberto"]),
            followup_vencido=bool(row["followup_vencido"]),
            cs_no_prazo=bool(row["cs_no_prazo"]),
        )
        scores.append(sc)
        prioridades.append(prio)

    resultado["score"] = scores
    resultado["prioridade"] = prioridades

    return resultado


def ordenar_por_prioridade(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena o DataFrame por prioridade e criterios de desempate.

    Ordem de ordenacao:
      1. Prioridade (P0 primeiro, P7 por ultimo)
      2. Desempate dentro da mesma prioridade:
         a. curva_abc (A > B > C)
         b. ticket_medio (maior primeiro) — se coluna existir
         c. tipo_cliente (mais maduro primeiro)
         d. followup_vencido_dias (mais vencido primeiro) — se coluna existir

    P7 vai para o fundo (nunca entra na agenda diaria).

    Args:
        df: DataFrame com colunas 'prioridade', 'curva_abc', 'tipo_cliente'
            e opcionalmente 'ticket_medio', 'followup_vencido_dias'.

    Returns:
        DataFrame ordenado (indice resetado).
    """
    resultado = df.copy()

    # Coluna auxiliar para ordenacao numerica de prioridade
    resultado["_prio_num"] = resultado["prioridade"].apply(_indice_prioridade)

    # Coluna auxiliar para ordenacao de ABC (A=0, B=1, C=2, desconhecido=9)
    _abc_ordem: dict[str, int] = {"A": 0, "B": 1, "C": 2}
    resultado["_abc_num"] = resultado["curva_abc"].apply(
        lambda v: _abc_ordem.get(_normalizar(v), 9)
    )

    # Coluna auxiliar para maturidade do tipo cliente
    resultado["_maturidade_num"] = resultado["tipo_cliente"].apply(_indice_maturidade)

    # Construir lista de colunas e ascendings para sort_values
    colunas_sort: list[str] = ["_prio_num", "_abc_num"]
    ascendings: list[bool] = [True, True]

    if "ticket_medio" in resultado.columns:
        colunas_sort.append("ticket_medio")
        ascendings.append(False)  # maior ticket primeiro

    colunas_sort.append("_maturidade_num")
    ascendings.append(True)  # menor indice = mais maduro

    if "followup_vencido_dias" in resultado.columns:
        colunas_sort.append("followup_vencido_dias")
        ascendings.append(False)  # mais dias vencido primeiro

    resultado = resultado.sort_values(colunas_sort, ascending=ascendings)

    # Remover colunas auxiliares
    resultado = resultado.drop(columns=["_prio_num", "_abc_num", "_maturidade_num"])

    return resultado.reset_index(drop=True)


def gerar_agenda_diaria(
    df: pd.DataFrame,
    max_atendimentos: int = MAX_ATENDIMENTOS_DEFAULT,
) -> pd.DataFrame:
    """Seleciona clientes para a agenda diaria do consultor.

    Regras de inclusao:
      P0: SEMPRE incluido — pula fila, nao conta no limite de 40.
      P1: Ate MAX_P1_AGENDA (15) por dia.
      P2-P6: Preenchem vagas restantes ate max_atendimentos.
      P7: NUNCA incluido na agenda diaria (campanha mensal).

    O DataFrame de entrada deve estar ordenado por prioridade
    (usar ordenar_por_prioridade() antes desta funcao).

    Args:
        df: DataFrame ja ordenado com coluna 'prioridade'.
        max_atendimentos: Limite de atendimentos por dia (padrao 40).
            P0 nao conta; P1 tem sublimite proprio (15).

    Returns:
        DataFrame com coluna adicional 'na_agenda' (bool).
        True = cliente entra na agenda do dia.
    """
    resultado = df.copy()
    resultado["na_agenda"] = False

    vagas_disponiveis = max_atendimentos
    p1_incluidos = 0

    for idx in resultado.index:
        prio = resultado.at[idx, "prioridade"]

        if prio == "P0":
            resultado.at[idx, "na_agenda"] = True
            # P0 nao consome vagas do limite de 40

        elif prio == "P1":
            if p1_incluidos < MAX_P1_AGENDA and vagas_disponiveis > 0:
                resultado.at[idx, "na_agenda"] = True
                p1_incluidos += 1
                vagas_disponiveis -= 1

        elif prio == "P7":
            # Nunca entra na agenda diaria
            resultado.at[idx, "na_agenda"] = False

        else:
            # P2-P6: preenche vagas restantes
            if vagas_disponiveis > 0:
                resultado.at[idx, "na_agenda"] = True
                vagas_disponiveis -= 1

    return resultado


def aplicar_meta_balance(
    df: pd.DataFrame,
    meta_mensal: float = META_MENSAL_DEFAULT,
) -> pd.DataFrame:
    """Aplica regra de Meta Balance: forcca PROSPECCAO se P2-P5 nao cobrem 80% da meta.

    Logica:
      1. Soma potencial_venda de clientes P2-P5 (se coluna existir).
      2. Se soma < 80% da meta mensal: adiciona BOOST_PROSPECCAO (+20)
         ao score de clientes com fase == PROSPECCAO/PROSPECÇÃO.
      3. Recalcula prioridade com novo score.

    Se a coluna 'potencial_venda' nao existir no DataFrame,
    a regra nao e aplicada e o DataFrame e retornado sem alteracoes.

    Args:
        df: DataFrame com colunas 'prioridade', 'fase', 'score'
            e opcionalmente 'potencial_venda'.
        meta_mensal: Meta mensal em reais (padrao ~R$ 263.051).

    Returns:
        DataFrame com scores e prioridades possivelmente ajustados.
        Adiciona coluna 'meta_balance_ativo' (bool) indicando se
        o boost foi aplicado.
    """
    resultado = df.copy()
    resultado["meta_balance_ativo"] = False

    if "potencial_venda" not in resultado.columns:
        logger.info(
            "Meta Balance: coluna 'potencial_venda' ausente — regra nao aplicada."
        )
        return resultado

    mascara_p2_p5 = resultado["prioridade"].isin(["P2", "P3", "P4", "P5"])
    soma_potencial = resultado.loc[mascara_p2_p5, "potencial_venda"].sum()
    limite_80pct = meta_mensal * 0.80

    if soma_potencial >= limite_80pct:
        logger.info(
            "Meta Balance: potencial P2-P5 R$ %.0f >= 80%% da meta R$ %.0f — sem ajuste.",
            soma_potencial,
            limite_80pct,
        )
        return resultado

    logger.warning(
        "Meta Balance ATIVO: potencial P2-P5 R$ %.0f < 80%% meta R$ %.0f. "
        "Aplicando boost +%.0f em PROSPECCAO.",
        soma_potencial,
        limite_80pct,
        BOOST_PROSPECCAO,
    )

    fases_prospeccao = {"PROSPECÇÃO", "PROSPECCAO"}
    mascara_prospeccao = resultado["fase"].apply(
        lambda v: _normalizar(v) in fases_prospeccao
    )

    resultado.loc[mascara_prospeccao, "score"] = (
        resultado.loc[mascara_prospeccao, "score"] + BOOST_PROSPECCAO
    ).clip(upper=100.0).round(1)

    resultado.loc[mascara_prospeccao, "prioridade"] = resultado.loc[
        mascara_prospeccao, "score"
    ].apply(_prioridade_por_score)

    resultado.loc[mascara_prospeccao, "meta_balance_ativo"] = True

    n_ajustados = mascara_prospeccao.sum()
    logger.info("Meta Balance: %d clientes PROSPECCAO tiveram score ajustado.", n_ajustados)

    return resultado


def stats(df: Optional[pd.DataFrame] = None) -> dict:
    """Retorna resumo estatistico da distribuicao de scores e prioridades.

    Se df for None, retorna apenas os metadados das constantes do engine.

    Args:
        df: DataFrame com colunas 'score' e 'prioridade' (opcional).

    Returns:
        Dicionario com:
          - pesos: pesos das 6 dimensoes
          - faixas: faixas de prioridade P2-P7
          - distribuicao_prioridade: contagem por label (se df fornecido)
          - score_stats: media, mediana, min, max (se df fornecido)
          - total_clientes: contagem total (se df fornecido)
          - na_agenda: contagem de True/False na coluna 'na_agenda' (se existir)
    """
    resultado: dict = {
        "pesos": PESOS,
        "faixas": {label: (smin, smax) for label, smin, smax in FAIXAS_PRIORIDADE},
        "boost_prospeccao": BOOST_PROSPECCAO,
        "meta_mensal_default": META_MENSAL_DEFAULT,
        "max_atendimentos_padrao": MAX_ATENDIMENTOS_DEFAULT,
        "max_p1_agenda": MAX_P1_AGENDA,
    }

    if df is None:
        return resultado

    if "score" in df.columns:
        resultado["score_stats"] = {
            "media": round(float(df["score"].mean()), 1),
            "mediana": round(float(df["score"].median()), 1),
            "minimo": round(float(df["score"].min()), 1),
            "maximo": round(float(df["score"].max()), 1),
        }

    if "prioridade" in df.columns:
        contagem = df["prioridade"].value_counts().to_dict()
        # Garantir que todos os labels aparecem (mesmo com zero)
        todos_labels = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]
        resultado["distribuicao_prioridade"] = {
            label: int(contagem.get(label, 0)) for label in todos_labels
        }
        resultado["total_clientes"] = len(df)

    if "na_agenda" in df.columns:
        resultado["na_agenda"] = {
            "incluidos": int(df["na_agenda"].sum()),
            "excluidos": int((~df["na_agenda"]).sum()),
        }

    return resultado


# ---------------------------------------------------------------------------
# CLI de teste
# ---------------------------------------------------------------------------

def _run_tests() -> None:
    """Executa suite de testes rapidos para validacao do engine."""
    import json

    separador = "-" * 60

    print(separador)
    print("SCORE ENGINE — TESTE RAPIDO")
    print(separador)

    # ------------------------------------------------------------------
    # Teste 1: Score de 3 perfis representativos
    # ------------------------------------------------------------------
    print("\n[1] CALCULO DE SCORE — 3 PERFIS")

    perfis = [
        {
            "nome": "Cliente Recompra A — Vermelho (urgente reativacao)",
            "args": ("RECOMPRA", "VERMELHO", "A", "QUENTE", "MADURO", "T1"),
            "esperado_min": 85.0,
        },
        {
            "nome": "Prospect Frio C — T3 (baixa prioridade)",
            "args": ("PROSPECCAO", "ROXO", "C", "FRIO", "PROSPECT", "T3"),
            "esperado_max": 25.0,
        },
        {
            "nome": "Salvamento B — Amarelo (risco medio)",
            "args": ("SALVAMENTO", "AMARELO", "B", "MORNO", "RECORRENTE", "T2"),
            "esperado_range": (35.0, 70.0),
        },
    ]

    for p in perfis:
        sc = calcular_score(*p["args"])
        status = "OK"
        if "esperado_min" in p and sc < p["esperado_min"]:
            status = f"FAIL (esperado >= {p['esperado_min']})"
        elif "esperado_max" in p and sc > p["esperado_max"]:
            status = f"FAIL (esperado <= {p['esperado_max']})"
        elif "esperado_range" in p:
            lo, hi = p["esperado_range"]
            if not (lo <= sc <= hi):
                status = f"FAIL (esperado {lo}-{hi})"
        print(f"  {p['nome']}")
        print(f"    score={sc}  [{status}]")

    # ------------------------------------------------------------------
    # Teste 2: Bloqueios P0 e P1
    # ------------------------------------------------------------------
    print(f"\n[2] BLOQUEIOS P0 e P1")

    casos_bloqueio = [
        {
            "desc": "SUPORTE + problema_aberto=True -> P0",
            "kwargs": {
                "resultado": "SUPORTE", "estagio_funil": "SUPORTE",
                "fase": "RECOMPRA", "sinaleiro": "VERDE", "curva_abc": "B",
                "temperatura": "MORNO", "tipo_cliente": "RECORRENTE",
                "tentativas": "T1", "problema_aberto": True,
            },
            "esperado": "P0",
        },
        {
            "desc": "SUPORTE + problema_aberto=False -> NAO e P0",
            "kwargs": {
                "resultado": "SUPORTE", "estagio_funil": "SUPORTE",
                "fase": "RECOMPRA", "sinaleiro": "VERDE", "curva_abc": "B",
                "temperatura": "MORNO", "tipo_cliente": "RECORRENTE",
                "tentativas": "T1", "problema_aberto": False,
            },
            "esperado_not": "P0",
        },
        {
            "desc": "EM ATENDIMENTO + followup_vencido=True -> P1",
            "kwargs": {
                "resultado": "EM ATENDIMENTO", "estagio_funil": "ATENDIMENTO",
                "fase": "NEGOCIACAO", "sinaleiro": "AMARELO", "curva_abc": "A",
                "temperatura": "QUENTE", "tipo_cliente": "FIDELIZADO",
                "tentativas": "T1", "followup_vencido": True,
            },
            "esperado": "P1",
        },
        {
            "desc": "cs_no_prazo=True -> P1",
            "kwargs": {
                "resultado": "CS", "estagio_funil": "CS",
                "fase": "RECOMPRA", "sinaleiro": "VERDE", "curva_abc": "A",
                "temperatura": "QUENTE", "tipo_cliente": "MADURO",
                "tentativas": "T1", "cs_no_prazo": True,
            },
            "esperado": "P1",
        },
    ]

    for caso in casos_bloqueio:
        prio, sc = atribuir_prioridade(**caso["kwargs"])
        ok = True
        if "esperado" in caso and prio != caso["esperado"]:
            ok = False
        if "esperado_not" in caso and prio == caso["esperado_not"]:
            ok = False
        status = "OK" if ok else f"FAIL (obtido={prio})"
        print(f"  {caso['desc']}")
        print(f"    prioridade={prio}  score={sc}  [{status}]")

    # ------------------------------------------------------------------
    # Teste 3: Atribuicao de prioridade por faixa de score
    # ------------------------------------------------------------------
    print(f"\n[3] FAIXAS DE PRIORIDADE")

    casos_faixa = [
        ("RECOMPRA", "VERMELHO", "A", "QUENTE", "MADURO", "T1", "P2"),
        ("NEGOCIACAO", "AMARELO", "B", "MORNO", "RECORRENTE", "T2", "P3"),
        ("SALVAMENTO", "AMARELO", "B", "FRIO", "EM DESENV", "T2", "P4"),
        ("PROSPECCAO", "VERDE", "C", "FRIO", "LEAD", "T3", "P6"),
        ("NUTRICAO", "ROXO", "C", "PERDIDO", "PROSPECT", "T4", "P7"),
    ]

    for *dims, esperada in casos_faixa:
        sc = calcular_score(*dims)
        prio, _ = atribuir_prioridade("VENDA", "", *dims)
        status = "OK" if prio == esperada else f"FAIL (esperado={esperada}, score={sc})"
        print(f"  fase={dims[0]:12s} abc={dims[2]} score={sc:5.1f} -> {prio}  [{status}]")

    # ------------------------------------------------------------------
    # Teste 4: Ordenacao com desempate
    # ------------------------------------------------------------------
    print(f"\n[4] DESEMPATE — ORDENACAO")

    dados_desempate = pd.DataFrame([
        {"fase": "RECOMPRA",  "sinaleiro": "VERMELHO", "curva_abc": "A",
         "temperatura": "QUENTE", "tipo_cliente": "MADURO",    "tentativas": "T1",
         "ticket_medio": 5000.0, "nome": "Cliente-A-Maduro"},
        {"fase": "RECOMPRA",  "sinaleiro": "VERMELHO", "curva_abc": "B",
         "temperatura": "QUENTE", "tipo_cliente": "FIDELIZADO", "tentativas": "T1",
         "ticket_medio": 8000.0, "nome": "Cliente-B-Fidelizado"},
        {"fase": "RECOMPRA",  "sinaleiro": "VERMELHO", "curva_abc": "A",
         "temperatura": "QUENTE", "tipo_cliente": "RECORRENTE", "tentativas": "T1",
         "ticket_medio": 3000.0, "nome": "Cliente-A-Recorrente"},
    ])

    df_desempate = calcular_score_batch(dados_desempate)
    df_desempate = ordenar_por_prioridade(df_desempate)
    print("  Ordem resultante (ABC prioriza sobre ticket dentro de P2):")
    for i, row in df_desempate.iterrows():
        print(f"    {i+1}. {row['nome']:30s} abc={row['curva_abc']} "
              f"ticket={row['ticket_medio']:.0f} score={row['score']}")

    # ------------------------------------------------------------------
    # Teste 5: Agenda diaria
    # ------------------------------------------------------------------
    print(f"\n[5] AGENDA DIARIA — 40 SLOTS")

    n_clientes = 80
    import random
    random.seed(42)

    fases_pool = list(SCORE_FASE.keys())[:6]
    sin_pool = list(SCORE_SINALEIRO.keys())
    abc_pool = list(SCORE_CURVA_ABC.keys())
    temp_pool = list(SCORE_TEMPERATURA.keys())
    tipo_pool = list(SCORE_TIPO_CLIENTE.keys())
    tent_pool = list(SCORE_TENTATIVAS.keys())

    dados_agenda = pd.DataFrame([
        {
            "fase": random.choice(fases_pool),
            "sinaleiro": random.choice(sin_pool),
            "curva_abc": random.choice(abc_pool),
            "temperatura": random.choice(temp_pool),
            "tipo_cliente": random.choice(tipo_pool),
            "tentativas": random.choice(tent_pool),
            "resultado": "",
        }
        for _ in range(n_clientes)
    ])

    # Injetar 2 P0 e 3 P1 manualmente
    dados_agenda.at[0, "resultado"] = "SUPORTE"
    dados_agenda.at[0, "problema_aberto"] = True
    dados_agenda.at[1, "resultado"] = "SUPORTE"
    dados_agenda.at[1, "problema_aberto"] = True
    dados_agenda.at[2, "resultado"] = "EM ATENDIMENTO"
    dados_agenda.at[2, "followup_vencido"] = True
    dados_agenda.at[3, "resultado"] = "EM ATENDIMENTO"
    dados_agenda.at[3, "followup_vencido"] = True
    dados_agenda.at[4, "cs_no_prazo"] = True

    df_agenda = calcular_score_batch(dados_agenda)
    df_agenda = ordenar_por_prioridade(df_agenda)
    df_agenda = gerar_agenda_diaria(df_agenda, max_atendimentos=40)

    resumo = stats(df_agenda)
    print(f"  Total clientes: {resumo['total_clientes']}")
    print(f"  Distribuicao: {resumo['distribuicao_prioridade']}")
    print(f"  Score media={resumo['score_stats']['media']}  "
          f"mediana={resumo['score_stats']['mediana']}")
    print(f"  Na agenda: {resumo['na_agenda']['incluidos']} / excluidos: {resumo['na_agenda']['excluidos']}")

    agenda_incluidos = df_agenda[df_agenda["na_agenda"]]["prioridade"].value_counts().to_dict()
    print(f"  Composicao da agenda: {agenda_incluidos}")

    p7_na_agenda = df_agenda[df_agenda["na_agenda"] & (df_agenda["prioridade"] == "P7")]
    if len(p7_na_agenda) == 0:
        print("  P7 na agenda: 0  [OK — P7 nunca entra na agenda]")
    else:
        print(f"  P7 na agenda: {len(p7_na_agenda)}  [FAIL — P7 nao deveria entrar!]")

    # ------------------------------------------------------------------
    # Resumo final
    # ------------------------------------------------------------------
    print(f"\n{separador}")
    print("SCORE ENGINE — TESTE CONCLUIDO")
    print(separador)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s [%(name)s] %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Score Engine — Motor de Prioridade CRM VITAO360"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Executa suite de testes rapidos de validacao",
    )
    args = parser.parse_args()

    if args.test:
        _run_tests()
    else:
        parser.print_help()
        sys.exit(0)
