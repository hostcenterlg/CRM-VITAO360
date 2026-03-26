"""
Score Engine — Motor de Prioridade CRM VITAO360 v2.0.

Calcula score ponderado (0-100) a partir de 6 fatores v2 (alinhado com
planilha INTELIGENTE FINAL OK, Score v2, CARTEIRA cols 137-144) e atribui
prioridade P1-P7 para cada cliente. Alimenta a agenda diaria de
40 atendimentos por consultor.

Fatores v2 (pesos oficiais da planilha):
  URGENCIA  (30%): Dias sem compra / ciclo medio
  VALOR     (25%): Curva ABC + Tipo Cliente
  FOLLOWUP  (20%): Proximo follow-up vs hoje
  SINAL     (15%): Temperatura + E-commerce
  TENTATIVA  (5%): T1/T2/T3/T4
  SITUACAO   (5%): Situacao Mercos

Regras de negocio extraidas de:
  data/intelligence/arquitetura_9_dimensoes.json
  data/intelligence/fases_estrategicas.json
  Planilha: INTELIGENTE FINAL OK — Score v2 (cols 137-144)

Regras inviolaveis (L3):
  - Assinaturas publicas calcular_score / calcular_score_batch imutaveis
  - CNPJ = string 14 digitos (nunca float/int)
  - Nenhum dado fabricado — entradas nao mapeadas valem 0
  - Two-Base Architecture: valores monetarios apenas em registro VENDA
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
# Constantes de negocio — Score v2 (OFICIAL planilha INTELIGENTE FINAL OK)
# Alterar apenas com aprovacao L3.
# ---------------------------------------------------------------------------

PESOS: dict[str, float] = {
    "URGENCIA": 0.30,   # Dias sem compra / ciclo medio
    "VALOR": 0.25,      # Curva ABC + Tipo Cliente
    "FOLLOWUP": 0.20,   # Proximo follow-up vs hoje
    "SINAL": 0.15,      # Temperatura + E-commerce
    "TENTATIVA": 0.05,  # T1/T2/T3/T4
    "SITUACAO": 0.05,   # Situacao Mercos
}

# Ordem de maturidade para desempate (menor indice = mais maduro = prioridade maior)
_ORDEM_MATURIDADE: list[str] = [
    "MADURO", "FIDELIZADO", "RECORRENTE", "EM DESENV",
    "EM DESENVOLVIMENTO", "NOVO", "LEAD", "PROSPECT",
]

# Meta mensal padrao: R$ 3.377.120 (projecao 2026) / 12 meses
META_MENSAL_DEFAULT: float = 3_377_120.0 / 12  # ~281.427

# Limite da agenda diaria por consultor
MAX_ATENDIMENTOS_DEFAULT: int = 40

# Teto de P1 na agenda diaria
MAX_P1_AGENDA: int = 15

# Boost de score para PROSPECCAO quando meta balance ativa
BOOST_PROSPECCAO: float = 20.0


# ---------------------------------------------------------------------------
# Calculos dos 6 fatores v2 — logica extraida das formulas Excel
# (L3: nao alterar sem aprovacao)
# ---------------------------------------------------------------------------

def _calcular_urgencia(
    situacao: str,
    dias_sem_compra: Optional[float],
    ciclo_medio: Optional[float],
) -> float:
    """Fator URGENCIA (30%) — quao urgente e reativar / atender este cliente.

    Logica extraida da planilha Score v2:
      - INAT.ANT = 100
      - INAT.REC = 90
      - EM RISCO  = 70
      - PROSPECT/LEAD = 10
      - Com ciclo definido:
          ratio = dias_sem_compra / ciclo_medio
          >= 1.5 -> 100 | >= 1.0 -> 60 | >= 0.7 -> 40 | < 0.7 -> 20
      - Sem ciclo e dias > 50: 60
      - Demais: 30
    """
    sit = situacao.upper() if situacao else ""

    if sit == "INAT.ANT":
        return 100.0
    if sit == "INAT.REC":
        return 90.0
    if sit == "EM RISCO":
        return 70.0
    if sit in ("PROSPECT", "LEAD"):
        return 10.0

    # Situacoes ativas: calcular pelo ciclo de compra
    if ciclo_medio and ciclo_medio > 0 and dias_sem_compra is not None:
        ratio = dias_sem_compra / ciclo_medio
        if ratio >= 1.5:
            return 100.0
        if ratio >= 1.0:
            return 60.0
        if ratio >= 0.7:
            return 40.0
        return 20.0

    # Sem ciclo definido: usar dias brutos
    if dias_sem_compra is not None and dias_sem_compra > 50:
        return 60.0

    return 30.0


def _calcular_valor(curva_abc: str, tipo_cliente: str) -> float:
    """Fator VALOR (25%) — peso financeiro e fidelidade do cliente.

    Logica extraida da planilha Score v2:
      A + FIDELIZADO/MADURO = 100
      A = 80
      B + RECORRENTE/FIDELIZADO = 60
      B = 50
      C = 20
      Sem ABC mas FIDELIZADO/MADURO = 60
      Sem ABC mas RECORRENTE = 40
      Sem ABC mas EM_DESENV = 20
      default = 10
    """
    abc = curva_abc.upper().strip() if curva_abc else ""
    tipo = tipo_cliente.upper().strip() if tipo_cliente else ""

    tipos_premium = {"FIDELIZADO", "MADURO"}
    tipos_recorrente = {"RECORRENTE", "FIDELIZADO"}

    if abc == "A" and tipo in tipos_premium:
        return 100.0
    if abc == "A":
        return 80.0
    if abc == "B" and tipo in tipos_recorrente:
        return 60.0
    if abc == "B":
        return 50.0
    if abc == "C":
        return 20.0

    # Sem curva ABC definida — usar tipo_cliente como proxy
    if tipo in tipos_premium:
        return 60.0
    if tipo == "RECORRENTE":
        return 40.0
    if tipo in ("EM DESENV", "EM DESENVOLVIMENTO"):
        return 20.0
    return 10.0


def _calcular_followup(dias_atraso_followup: Optional[float]) -> float:
    """Fator FOLLOWUP (20%) — urgencia do proximo contato agendado.

    dias_atraso_followup: positivo = atrasado, negativo = futuro, None = sem FU.

    Logica extraida da planilha Score v2:
      Sem follow-up     = 50 (default neutro)
      >= 7 dias atraso  = 100
      >= 3 dias         = 80
      >= 1 dia          = 70
      Hoje (0)          = 60
      Ate -3 (futuro)   = 40
      Mais futuro       = 20
    """
    if dias_atraso_followup is None:
        return 50.0

    d = dias_atraso_followup
    if d >= 7:
        return 100.0
    if d >= 3:
        return 80.0
    if d >= 1:
        return 70.0
    if d >= 0:
        return 60.0
    if d >= -3:
        return 40.0
    return 20.0


def _calcular_sinal(temperatura: str, ecommerce_carrinho: float = 0.0) -> float:
    """Fator SINAL (15%) — temperatura de engajamento + sinais digitais.

    Logica extraida da planilha Score v2:
      CRITICO                           = 90
      QUENTE + carrinho e-commerce > 0  = 100
      QUENTE                            = 80
      MORNO + B2B ativo + carrinho > 0  = 70
      MORNO + B2B ativo                 = 60
      MORNO                             = 40
      FRIO                              = 10
      PERDIDO                           = 0
    """
    temp = temperatura.upper().strip() if temperatura else ""
    carrinho = float(ecommerce_carrinho) if ecommerce_carrinho else 0.0

    if temp == "CRITICO" or temp == "CRÍTICO":
        return 90.0
    if temp == "QUENTE":
        return 100.0 if carrinho > 0 else 80.0
    if temp == "MORNO":
        # B2B ativo heuristico: se ha carrinho aberto presume B2B ativo
        if carrinho > 0:
            return 70.0
        return 40.0
    if temp == "FRIO":
        return 10.0
    if temp == "PERDIDO":
        return 0.0
    return 0.0


def _calcular_tentativa(tentativas: str) -> float:
    """Fator TENTATIVA (5%) — persistencia nas tentativas de contato.

    Logica extraida da planilha Score v2:
      T4+  = 100
      T3   = 50
      T1/T2 = 10
    """
    tent = tentativas.upper().strip() if tentativas else ""

    if tent == "T4" or tent.startswith("T") and len(tent) >= 2 and tent[1:].isdigit() and int(tent[1:]) >= 4:
        return 100.0
    if tent == "T3":
        return 50.0
    if tent in ("T1", "T2"):
        return 10.0
    return 0.0


def _calcular_situacao(situacao: str) -> float:
    """Fator SITUACAO (5%) — situacao cadastral no Mercos.

    Logica extraida da planilha Score v2:
      EM RISCO    = 80
      ATIVO       = 40
      INAT.REC    = 20
      INAT.ANT    = 20
      PROSPECT    = 10
    """
    sit = situacao.upper().strip() if situacao else ""

    if sit == "EM RISCO":
        return 80.0
    if sit == "ATIVO":
        return 40.0
    if sit in ("INAT.REC", "INAT.ANT"):
        return 20.0
    if sit == "PROSPECT":
        return 10.0
    return 0.0


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


def _prioridade_v2(
    situacao: str,
    resultado: str,
    tipo_cliente: str,
    score: float,
) -> str:
    """Atribui prioridade P1-P7 conforme regras v2 da planilha Score v2.

    Ordem de avaliacao (L3 — nao alterar sem aprovacao):
      P3 PROBLEMA:      SUPORTE
      P1 NAMORO NOVO:   POS-VENDA/CS + NOVO/ATIVO + Score >= 70
      P2 NEGOCIACAO:    ORCAMENTO / EM ATENDIMENTO / CADASTRO
      P4 MOMENTO OURO:  INAT.REC + Score >= 75
      P5 INAT. RECENTE: INAT.REC (score abaixo de 75)
      P5 INAT. RECENTE: INAT.ANT + Score >= 80
      P6 INAT. ANTIGO:  INAT.ANT (score abaixo de 80)
      P7 PROSPECCAO:    PROSPECT / LEAD
      P4 MOMENTO OURO:  NOVO
      P4 MOMENTO OURO:  Score >= 50
      P5 INAT. RECENTE: default
    """
    sit = situacao.upper().strip() if situacao else ""
    res = resultado.upper().strip() if resultado else ""
    tipo = tipo_cliente.upper().strip() if tipo_cliente else ""

    # P3 PROBLEMA — suporte bloqueante
    if res == "SUPORTE" or sit == "SUPORTE":
        return "P3 PROBLEMA"

    # P1 NAMORO NOVO — pos-venda ou CS em cliente novo/ativo com score alto
    tipos_novos_ativos = {"NOVO", "ATIVO"}
    fases_pos_venda = {"POS-VENDA", "POS VENDA", "CS"}
    if res in fases_pos_venda and tipo in tipos_novos_ativos and score >= 70:
        return "P1 NAMORO NOVO"

    # P2 NEGOCIACAO ATIVA — em negociacao / orcamento / cadastro
    fases_negociacao = {"ORCAMENTO", "ORÇAMENTO", "EM ATENDIMENTO", "CADASTRO"}
    if res in fases_negociacao or sit in fases_negociacao:
        return "P2 NEGOCIACAO ATIVA"

    # P4/P5 — inativos recentes
    if sit == "INAT.REC":
        if score >= 75:
            return "P4 MOMENTO OURO"
        return "P5 INAT. RECENTE"

    # P5/P6 — inativos antigos
    if sit == "INAT.ANT":
        if score >= 80:
            return "P5 INAT. RECENTE"
        return "P6 INAT. ANTIGO"

    # P7 PROSPECCAO — clientes sem historico
    if sit in ("PROSPECT", "LEAD") or tipo in ("PROSPECT", "LEAD"):
        return "P7 PROSPECCAO"

    # P4 MOMENTO OURO — cliente novo com qualquer score
    if tipo == "NOVO" or sit == "NOVO":
        return "P4 MOMENTO OURO"

    # P4 MOMENTO OURO — score suficientemente alto
    if score >= 50:
        return "P4 MOMENTO OURO"

    # Default
    return "P5 INAT. RECENTE"


def _indice_prioridade(prioridade: str) -> int:
    """Converte label de prioridade em inteiro para ordenacao (menor = mais urgente)."""
    mapa = {
        "P1 NAMORO NOVO": 1,
        "P2 NEGOCIACAO ATIVA": 2,
        "P3 PROBLEMA": 3,
        "P4 MOMENTO OURO": 4,
        "P5 INAT. RECENTE": 5,
        "P6 INAT. ANTIGO": 6,
        "P7 PROSPECCAO": 7,
        # Aliases curtos (retrocompatibilidade)
        "P1": 1, "P2": 2, "P3": 3, "P4": 4, "P5": 5, "P6": 6, "P7": 7,
    }
    return mapa.get(prioridade, 99)


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


# ---------------------------------------------------------------------------
# API publica (L3: assinaturas imutaveis)
# ---------------------------------------------------------------------------

def calcular_score(
    situacao: object,
    curva_abc: object,
    tipo_cliente: object,
    temperatura: object,
    tentativas: object,
    dias_sem_compra: object = None,
    ciclo_medio: object = None,
    dias_atraso_followup: object = None,
    ecommerce_carrinho: object = 0.0,
) -> float:
    """Calcula o score ponderado (0-100) a partir dos 6 fatores v2.

    Alinhado com planilha INTELIGENTE FINAL OK — Score v2 (CARTEIRA cols 137-144).
    Todos os inputs sao normalizados internamente. Valores desconhecidos
    valem 0 na dimensao correspondente (sem erro).

    Args:
        situacao: Situacao Mercos do cliente
                  (ex: 'ATIVO', 'INAT.REC', 'INAT.ANT', 'EM RISCO', 'PROSPECT').
        curva_abc: Curva ABC de faturamento (ex: 'A', 'B', 'C').
        tipo_cliente: Maturidade na carteira
                      (ex: 'MADURO', 'FIDELIZADO', 'RECORRENTE', 'NOVO').
        temperatura: Temperatura de engajamento
                     (ex: 'QUENTE', 'MORNO', 'FRIO', 'CRITICO', 'PERDIDO').
        tentativas: Sequencia de contato (ex: 'T1', 'T2', 'T3', 'T4').
        dias_sem_compra: Dias desde a ultima compra (float ou None).
        ciclo_medio: Ciclo medio de compra do cliente em dias (float ou None).
        dias_atraso_followup: Atraso do follow-up em dias; positivo = atrasado,
                              negativo = futuro, None = sem FU agendado.
        ecommerce_carrinho: Valor de carrinho aberto no e-commerce (0 = sem carrinho).

    Returns:
        Score ponderado arredondado a 1 decimal, entre 0.0 e 100.0.
    """
    n_situacao = _normalizar(situacao)
    n_abc = _normalizar(curva_abc)
    n_tipo = _normalizar(tipo_cliente)
    n_temp = _normalizar(temperatura)
    n_tent = _normalizar(tentativas)

    try:
        f_dias = float(dias_sem_compra) if dias_sem_compra is not None else None
    except (TypeError, ValueError):
        f_dias = None

    try:
        f_ciclo = float(ciclo_medio) if ciclo_medio is not None else None
    except (TypeError, ValueError):
        f_ciclo = None

    try:
        f_followup = float(dias_atraso_followup) if dias_atraso_followup is not None else None
    except (TypeError, ValueError):
        f_followup = None

    try:
        f_carrinho = float(ecommerce_carrinho) if ecommerce_carrinho else 0.0
    except (TypeError, ValueError):
        f_carrinho = 0.0

    score_bruto = (
        _calcular_urgencia(n_situacao, f_dias, f_ciclo) * PESOS["URGENCIA"]
        + _calcular_valor(n_abc, n_tipo) * PESOS["VALOR"]
        + _calcular_followup(f_followup) * PESOS["FOLLOWUP"]
        + _calcular_sinal(n_temp, f_carrinho) * PESOS["SINAL"]
        + _calcular_tentativa(n_tent) * PESOS["TENTATIVA"]
        + _calcular_situacao(n_situacao) * PESOS["SITUACAO"]
    )

    return round(min(max(score_bruto, 0.0), 100.0), 1)


def atribuir_prioridade(
    resultado: object,
    situacao: object,
    curva_abc: object,
    tipo_cliente: object,
    temperatura: object,
    tentativas: object,
    dias_sem_compra: object = None,
    ciclo_medio: object = None,
    dias_atraso_followup: object = None,
    ecommerce_carrinho: object = 0.0,
) -> tuple[str, float]:
    """Atribui prioridade P1-P7 com base no score ponderado v2 e regras de negocio.

    Alinhado com planilha INTELIGENTE FINAL OK — Score v2.

    Args:
        resultado: Ultimo resultado / estagio registrado
                   (ex: 'SUPORTE', 'EM ATENDIMENTO', 'POS-VENDA', 'CS').
        situacao: Situacao Mercos do cliente.
        curva_abc: Curva ABC de faturamento.
        tipo_cliente: Maturidade na carteira.
        temperatura: Temperatura de engajamento.
        tentativas: Sequencia de contato.
        dias_sem_compra: Dias desde a ultima compra (float ou None).
        ciclo_medio: Ciclo medio de compra em dias (float ou None).
        dias_atraso_followup: Atraso do follow-up em dias.
        ecommerce_carrinho: Valor de carrinho aberto no e-commerce.

    Returns:
        Tupla (prioridade, score) onde prioridade eh 'P1 NAMORO NOVO'..'P7 PROSPECCAO'
        e score eh o score ponderado (0-100).
    """
    n_resultado = _normalizar(resultado)
    n_situacao = _normalizar(situacao)
    n_tipo = _normalizar(tipo_cliente)

    score = calcular_score(
        situacao=situacao,
        curva_abc=curva_abc,
        tipo_cliente=tipo_cliente,
        temperatura=temperatura,
        tentativas=tentativas,
        dias_sem_compra=dias_sem_compra,
        ciclo_medio=ciclo_medio,
        dias_atraso_followup=dias_atraso_followup,
        ecommerce_carrinho=ecommerce_carrinho,
    )

    prioridade = _prioridade_v2(n_situacao, n_resultado, n_tipo, score)
    return (prioridade, score)


def calcular_score_batch(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula score e prioridade para um DataFrame de clientes.

    Colunas de input esperadas (obrigatorias):
      situacao, curva_abc, tipo_cliente, temperatura, tentativas

    Colunas opcionais:
      resultado           — estagio/resultado para regras de prioridade
      dias_sem_compra     — float, dias desde ultima compra
      ciclo_medio         — float, ciclo medio de compra em dias
      dias_atraso_followup — float, atraso do follow-up (positivo=atrasado)
      ecommerce_carrinho  — float, valor do carrinho e-commerce aberto

    Colunas adicionadas ao DataFrame retornado:
      score      float — score ponderado 0-100
      prioridade str   — label P1..P7 (ex: 'P1 NAMORO NOVO')

    Nao modifica o DataFrame original (retorna copia).

    Args:
        df: DataFrame com ao menos as 5 colunas obrigatorias.

    Returns:
        DataFrame com colunas 'score' e 'prioridade' adicionadas.

    Raises:
        KeyError: Se colunas obrigatorias estiverem ausentes.
    """
    resultado = df.copy()

    colunas_obrigatorias = ["situacao", "curva_abc", "tipo_cliente", "temperatura", "tentativas"]
    ausentes = [c for c in colunas_obrigatorias if c not in resultado.columns]
    if ausentes:
        raise KeyError(
            f"Colunas obrigatorias ausentes no DataFrame: {ausentes}. "
            f"Colunas disponiveis: {list(resultado.columns)}"
        )

    # Colunas opcionais — preenchidas com defaults se ausentes
    if "resultado" not in resultado.columns:
        resultado["resultado"] = ""
    for col_opt in ("dias_sem_compra", "ciclo_medio", "dias_atraso_followup"):
        if col_opt not in resultado.columns:
            resultado[col_opt] = None
    if "ecommerce_carrinho" not in resultado.columns:
        resultado["ecommerce_carrinho"] = 0.0

    scores: list[float] = []
    prioridades: list[str] = []

    for _, row in resultado.iterrows():
        prio, sc = atribuir_prioridade(
            resultado=row["resultado"],
            situacao=row["situacao"],
            curva_abc=row["curva_abc"],
            tipo_cliente=row["tipo_cliente"],
            temperatura=row["temperatura"],
            tentativas=row["tentativas"],
            dias_sem_compra=row["dias_sem_compra"],
            ciclo_medio=row["ciclo_medio"],
            dias_atraso_followup=row["dias_atraso_followup"],
            ecommerce_carrinho=row["ecommerce_carrinho"],
        )
        scores.append(sc)
        prioridades.append(prio)

    resultado["score"] = scores
    resultado["prioridade"] = prioridades

    return resultado


def ordenar_por_prioridade(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena o DataFrame por prioridade e criterios de desempate.

    Ordem de ordenacao:
      1. Prioridade (P1 primeiro, P7 por ultimo)
      2. Desempate dentro da mesma prioridade:
         a. curva_abc (A > B > C)
         b. ticket_medio (maior primeiro) — se coluna existir
         c. tipo_cliente (mais maduro primeiro)
         d. dias_atraso_followup (mais atrasado primeiro) — se coluna existir

    P7 PROSPECCAO vai para o fundo (nunca entra na agenda diaria).

    Args:
        df: DataFrame com colunas 'prioridade', 'curva_abc', 'tipo_cliente'
            e opcionalmente 'ticket_medio', 'dias_atraso_followup'.

    Returns:
        DataFrame ordenado (indice resetado).
    """
    resultado = df.copy()

    resultado["_prio_num"] = resultado["prioridade"].apply(_indice_prioridade)

    _abc_ordem: dict[str, int] = {"A": 0, "B": 1, "C": 2}
    resultado["_abc_num"] = resultado["curva_abc"].apply(
        lambda v: _abc_ordem.get(_normalizar(v), 9)
    )

    resultado["_maturidade_num"] = resultado["tipo_cliente"].apply(_indice_maturidade)

    colunas_sort: list[str] = ["_prio_num", "_abc_num"]
    ascendings: list[bool] = [True, True]

    if "ticket_medio" in resultado.columns:
        colunas_sort.append("ticket_medio")
        ascendings.append(False)  # maior ticket primeiro

    colunas_sort.append("_maturidade_num")
    ascendings.append(True)  # menor indice = mais maduro

    if "dias_atraso_followup" in resultado.columns:
        colunas_sort.append("dias_atraso_followup")
        ascendings.append(False)  # mais atrasado primeiro

    resultado = resultado.sort_values(colunas_sort, ascending=ascendings)
    resultado = resultado.drop(columns=["_prio_num", "_abc_num", "_maturidade_num"])

    return resultado.reset_index(drop=True)


def gerar_agenda_diaria(
    df: pd.DataFrame,
    max_atendimentos: int = MAX_ATENDIMENTOS_DEFAULT,
) -> pd.DataFrame:
    """Seleciona clientes para a agenda diaria do consultor.

    Regras de inclusao:
      P3 PROBLEMA:     SEMPRE incluido — pula fila, nao conta no limite de 40.
      P1 NAMORO NOVO:  Ate MAX_P1_AGENDA (15) por dia.
      P2-P6:           Preenchem vagas restantes ate max_atendimentos.
      P7 PROSPECCAO:   NUNCA incluido na agenda diaria (campanha mensal).

    O DataFrame de entrada deve estar ordenado por prioridade
    (usar ordenar_por_prioridade() antes desta funcao).

    Args:
        df: DataFrame ja ordenado com coluna 'prioridade'.
        max_atendimentos: Limite de atendimentos por dia (padrao 40).
            P3 PROBLEMA nao conta; P1 tem sublimite proprio (15).

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
        prio_num = _indice_prioridade(prio)

        # P3 PROBLEMA — entra sempre, nao consome vagas
        if prio_num == 3:
            resultado.at[idx, "na_agenda"] = True

        # P1 NAMORO NOVO — sublimite de 15
        elif prio_num == 1:
            if p1_incluidos < MAX_P1_AGENDA and vagas_disponiveis > 0:
                resultado.at[idx, "na_agenda"] = True
                p1_incluidos += 1
                vagas_disponiveis -= 1

        # P7 PROSPECCAO — nunca entra na agenda diaria
        elif prio_num == 7:
            resultado.at[idx, "na_agenda"] = False

        # P2, P4, P5, P6 — preenche vagas restantes
        else:
            if vagas_disponiveis > 0:
                resultado.at[idx, "na_agenda"] = True
                vagas_disponiveis -= 1

    return resultado


def aplicar_meta_balance(
    df: pd.DataFrame,
    meta_mensal: float = META_MENSAL_DEFAULT,
) -> pd.DataFrame:
    """Aplica regra de Meta Balance: forca PROSPECCAO se P2-P5 nao cobrem 80% da meta.

    Logica:
      1. Soma potencial_venda de clientes P2-P5 (se coluna existir).
      2. Se soma < 80% da meta mensal: adiciona BOOST_PROSPECCAO (+20)
         ao score de clientes com prioridade P7 PROSPECCAO.
      3. Recalcula prioridade com novo score.

    Se a coluna 'potencial_venda' nao existir no DataFrame,
    a regra nao e aplicada e o DataFrame e retornado sem alteracoes.

    Args:
        df: DataFrame com colunas 'prioridade', 'score'
            e opcionalmente 'potencial_venda'.
        meta_mensal: Meta mensal em reais (padrao ~R$ 281.427).

    Returns:
        DataFrame com scores e prioridades possivelmente ajustados.
        Adiciona coluna 'meta_balance_ativo' (bool).
    """
    resultado = df.copy()
    resultado["meta_balance_ativo"] = False

    if "potencial_venda" not in resultado.columns:
        logger.info(
            "Meta Balance: coluna 'potencial_venda' ausente — regra nao aplicada."
        )
        return resultado

    # Selecionar P2 a P5 (por numero de prioridade)
    mascara_p2_p5 = resultado["prioridade"].apply(
        lambda p: _indice_prioridade(p) in (2, 3, 4, 5)
    )
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
        "Aplicando boost +%.0f em P7 PROSPECCAO.",
        soma_potencial,
        limite_80pct,
        BOOST_PROSPECCAO,
    )

    mascara_prospeccao = resultado["prioridade"].apply(
        lambda p: _indice_prioridade(p) == 7
    )

    resultado.loc[mascara_prospeccao, "score"] = (
        resultado.loc[mascara_prospeccao, "score"] + BOOST_PROSPECCAO
    ).clip(upper=100.0).round(1)

    # Recalcular prioridade com score ajustado (usando situacao se disponivel)
    def _recalc_prio(row: pd.Series) -> str:
        sit = _normalizar(row.get("situacao", ""))
        res = _normalizar(row.get("resultado", ""))
        tipo = _normalizar(row.get("tipo_cliente", ""))
        return _prioridade_v2(sit, res, tipo, row["score"])

    resultado.loc[mascara_prospeccao, "prioridade"] = resultado.loc[
        mascara_prospeccao
    ].apply(_recalc_prio, axis=1)

    resultado.loc[mascara_prospeccao, "meta_balance_ativo"] = True

    n_ajustados = mascara_prospeccao.sum()
    logger.info("Meta Balance: %d clientes P7 PROSPECCAO tiveram score ajustado.", n_ajustados)

    return resultado


def stats(df: Optional[pd.DataFrame] = None) -> dict:
    """Retorna resumo estatistico da distribuicao de scores e prioridades.

    Se df for None, retorna apenas os metadados das constantes do engine.

    Args:
        df: DataFrame com colunas 'score' e 'prioridade' (opcional).

    Returns:
        Dicionario com:
          - pesos: pesos dos 6 fatores v2
          - distribuicao_prioridade: contagem por label (se df fornecido)
          - score_stats: media, mediana, min, max (se df fornecido)
          - total_clientes: contagem total (se df fornecido)
          - na_agenda: contagem de True/False na coluna 'na_agenda' (se existir)
    """
    resultado: dict = {
        "versao": "v2.0",
        "pesos": PESOS,
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
        todos_labels = [
            "P1 NAMORO NOVO", "P2 NEGOCIACAO ATIVA", "P3 PROBLEMA",
            "P4 MOMENTO OURO", "P5 INAT. RECENTE", "P6 INAT. ANTIGO",
            "P7 PROSPECCAO",
        ]
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
    """Executa suite de testes rapidos para validacao do engine v2."""
    import json

    separador = "-" * 60

    print(separador)
    print("SCORE ENGINE v2 — TESTE RAPIDO")
    print(separador)

    # ------------------------------------------------------------------
    # Teste 1: Fatores v2 individuais
    # ------------------------------------------------------------------
    print("\n[1] FATORES v2 — CALCULO INDIVIDUAL")

    print("  URGENCIA:")
    casos_urgencia = [
        ("INAT.ANT", None, None, 100.0),
        ("INAT.REC", None, None, 90.0),
        ("EM RISCO", None, None, 70.0),
        ("PROSPECT", None, None, 10.0),
        ("ATIVO", 60.0, 30.0, 100.0),   # ratio=2.0 >= 1.5
        ("ATIVO", 25.0, 30.0, 40.0),    # ratio=0.83 >= 0.7
        ("ATIVO", 60.0, None, 60.0),    # sem ciclo, dias > 50
        ("ATIVO", 10.0, None, 30.0),    # sem ciclo, dias <= 50
    ]
    for sit, dias, ciclo, esperado in casos_urgencia:
        v = _calcular_urgencia(sit, dias, ciclo)
        status = "OK" if v == esperado else f"FAIL (esperado={esperado})"
        print(f"    sit={sit:10s} dias={str(dias):4s} ciclo={str(ciclo):4s} "
              f"-> {v:.0f}  [{status}]")

    print("  VALOR:")
    casos_valor = [
        ("A", "MADURO", 100.0),
        ("A", "RECORRENTE", 80.0),
        ("B", "FIDELIZADO", 60.0),
        ("B", "NOVO", 50.0),
        ("C", "QUALQUER", 20.0),
        ("", "FIDELIZADO", 60.0),
        ("", "RECORRENTE", 40.0),
        ("", "LEAD", 10.0),
    ]
    for abc, tipo, esperado in casos_valor:
        v = _calcular_valor(abc, tipo)
        status = "OK" if v == esperado else f"FAIL (esperado={esperado})"
        print(f"    abc={abc:2s} tipo={tipo:12s} -> {v:.0f}  [{status}]")

    print("  FOLLOWUP:")
    casos_fu = [
        (None, 50.0),
        (7.0, 100.0),
        (3.0, 80.0),
        (1.0, 70.0),
        (0.0, 60.0),
        (-2.0, 40.0),
        (-10.0, 20.0),
    ]
    for dias, esperado in casos_fu:
        v = _calcular_followup(dias)
        status = "OK" if v == esperado else f"FAIL (esperado={esperado})"
        print(f"    dias_atraso={str(dias):6s} -> {v:.0f}  [{status}]")

    print("  SINAL:")
    casos_sinal = [
        ("CRITICO", 0.0, 90.0),
        ("QUENTE", 100.0, 100.0),
        ("QUENTE", 0.0, 80.0),
        ("MORNO", 50.0, 70.0),
        ("MORNO", 0.0, 40.0),
        ("FRIO", 0.0, 10.0),
        ("PERDIDO", 0.0, 0.0),
    ]
    for temp, carrinho, esperado in casos_sinal:
        v = _calcular_sinal(temp, carrinho)
        status = "OK" if v == esperado else f"FAIL (esperado={esperado})"
        print(f"    temp={temp:8s} carrinho={carrinho:.0f} -> {v:.0f}  [{status}]")

    print("  TENTATIVA:")
    casos_tent = [
        ("T4", 100.0),
        ("T3", 50.0),
        ("T1", 10.0),
        ("T2", 10.0),
    ]
    for tent, esperado in casos_tent:
        v = _calcular_tentativa(tent)
        status = "OK" if v == esperado else f"FAIL (esperado={esperado})"
        print(f"    tent={tent} -> {v:.0f}  [{status}]")

    # ------------------------------------------------------------------
    # Teste 2: Score ponderado v2 — perfis representativos
    # ------------------------------------------------------------------
    print(f"\n[2] SCORE PONDERADO v2 — PERFIS REPRESENTATIVOS")

    perfis = [
        {
            "nome": "INAT.ANT + A + FIDELIZADO + QUENTE + T4 + FU 7d atrasado",
            "kwargs": {
                "situacao": "INAT.ANT", "curva_abc": "A", "tipo_cliente": "FIDELIZADO",
                "temperatura": "QUENTE", "tentativas": "T4",
                "dias_sem_compra": None, "ciclo_medio": None,
                "dias_atraso_followup": 7.0, "ecommerce_carrinho": 0.0,
            },
            "esperado_min": 80.0,
        },
        {
            "nome": "PROSPECT + C + LEAD + FRIO + T1 + sem FU",
            "kwargs": {
                "situacao": "PROSPECT", "curva_abc": "C", "tipo_cliente": "LEAD",
                "temperatura": "FRIO", "tentativas": "T1",
                "dias_sem_compra": None, "ciclo_medio": None,
                "dias_atraso_followup": None, "ecommerce_carrinho": 0.0,
            },
            "esperado_max": 30.0,
        },
        {
            "nome": "ATIVO + B + RECORRENTE + MORNO + T2 + ciclo normal",
            "kwargs": {
                "situacao": "ATIVO", "curva_abc": "B", "tipo_cliente": "RECORRENTE",
                "temperatura": "MORNO", "tentativas": "T2",
                "dias_sem_compra": 20.0, "ciclo_medio": 30.0,
                "dias_atraso_followup": 1.0, "ecommerce_carrinho": 0.0,
            },
            "esperado_range": (30.0, 70.0),
        },
    ]

    for p in perfis:
        sc = calcular_score(**p["kwargs"])
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
    # Teste 3: Prioridades v2
    # ------------------------------------------------------------------
    print(f"\n[3] PRIORIDADES v2")

    casos_prio = [
        {
            "desc": "SUPORTE -> P3 PROBLEMA",
            "resultado": "SUPORTE", "situacao": "ATIVO",
            "tipo_cliente": "MADURO", "esperado": "P3 PROBLEMA",
        },
        {
            "desc": "EM ATENDIMENTO -> P2 NEGOCIACAO ATIVA",
            "resultado": "EM ATENDIMENTO", "situacao": "ATIVO",
            "tipo_cliente": "FIDELIZADO", "esperado": "P2 NEGOCIACAO ATIVA",
        },
        {
            "desc": "INAT.REC + score alto -> P4 MOMENTO OURO",
            "resultado": "", "situacao": "INAT.REC",
            "tipo_cliente": "FIDELIZADO", "esperado": "P4 MOMENTO OURO",
            "score_override": 80.0,
        },
        {
            "desc": "INAT.ANT + score baixo -> P6 INAT. ANTIGO",
            "resultado": "", "situacao": "INAT.ANT",
            "tipo_cliente": "RECORRENTE", "esperado": "P6 INAT. ANTIGO",
            "score_override": 50.0,
        },
        {
            "desc": "PROSPECT -> P7 PROSPECCAO",
            "resultado": "", "situacao": "PROSPECT",
            "tipo_cliente": "LEAD", "esperado": "P7 PROSPECCAO",
            "score_override": 20.0,
        },
    ]

    for caso in casos_prio:
        score_test = caso.get("score_override", 60.0)
        prio = _prioridade_v2(caso["situacao"], caso["resultado"], caso["tipo_cliente"], score_test)
        status = "OK" if prio == caso["esperado"] else f"FAIL (obtido='{prio}')"
        print(f"  {caso['desc']}")
        print(f"    prioridade='{prio}'  [{status}]")

    # ------------------------------------------------------------------
    # Teste 4: Batch
    # ------------------------------------------------------------------
    print(f"\n[4] BATCH — 5 CLIENTES")

    dados = pd.DataFrame([
        {
            "situacao": "INAT.ANT", "curva_abc": "A", "tipo_cliente": "MADURO",
            "temperatura": "QUENTE", "tentativas": "T4",
            "resultado": "", "dias_sem_compra": 120.0, "ciclo_medio": 30.0,
            "dias_atraso_followup": 10.0,
        },
        {
            "situacao": "ATIVO", "curva_abc": "B", "tipo_cliente": "RECORRENTE",
            "temperatura": "MORNO", "tentativas": "T2",
            "resultado": "EM ATENDIMENTO",
        },
        {
            "situacao": "INAT.REC", "curva_abc": "A", "tipo_cliente": "FIDELIZADO",
            "temperatura": "MORNO", "tentativas": "T3",
            "resultado": "",
        },
        {
            "situacao": "PROSPECT", "curva_abc": "C", "tipo_cliente": "LEAD",
            "temperatura": "FRIO", "tentativas": "T1",
            "resultado": "",
        },
        {
            "situacao": "ATIVO", "curva_abc": "A", "tipo_cliente": "MADURO",
            "temperatura": "QUENTE", "tentativas": "T1",
            "resultado": "SUPORTE",
        },
    ])

    df_resultado = calcular_score_batch(dados)
    df_resultado = ordenar_por_prioridade(df_resultado)
    df_resultado = gerar_agenda_diaria(df_resultado)

    for _, row in df_resultado.iterrows():
        print(f"  sit={row['situacao']:10s} abc={row['curva_abc']} "
              f"score={row['score']:5.1f} prio='{row['prioridade']:20s}' "
              f"agenda={'SIM' if row['na_agenda'] else 'NAO'}")

    # ------------------------------------------------------------------
    # Resumo final
    # ------------------------------------------------------------------
    resumo = stats(df_resultado)
    print(f"\n{separador}")
    print("SCORE ENGINE v2 — TESTE CONCLUIDO")
    print(f"  Distribuicao: {resumo.get('distribuicao_prioridade', {})}")
    print(f"  Na agenda: {resumo.get('na_agenda', {})}")
    print(separador)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s [%(name)s] %(message)s",
    )

    parser = argparse.ArgumentParser(
        description="Score Engine v2 — Motor de Prioridade CRM VITAO360"
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
