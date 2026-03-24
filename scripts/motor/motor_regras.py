"""
Motor de Regras v4 — CRM VITAO360.

Carrega as 92 combinacoes (7 SITUACAO x 14 RESULTADO) do JSON source-of-truth
e expoe funcoes para classificar clientes individualmente ou em lote.

Outputs por combinacao:
    estagio_funil, fase, tipo_contato, acao_futura,
    temperatura, followup_dias, grupo_dash, tipo_acao

Regras inviolaveis aplicadas aqui:
    - CNPJ sempre string 14 digitos (R5) — nao aplicavel neste modulo
    - Two-Base: valores R$ APENAS em registros tipo VENDA (R4) — nao aplicavel
    - NUNCA fabricar dados (R8) — carregamento 100% do JSON
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_ROOT = Path(__file__).resolve().parents[2]  # CRM-VITAO360/
_INTELLIGENCE_DIR = _ROOT / "data" / "intelligence"
_OUTPUT_DIR = _ROOT / "data" / "output" / "motor"
_BASE_UNIFICADA = _OUTPUT_DIR / "base_unificada.json"

MOTOR_REGRAS_JSON = _INTELLIGENCE_DIR / "motor_regras_v4.json"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("motor.regras")

# ---------------------------------------------------------------------------
# Constantes de validacao (carregadas em runtime a partir do JSON)
# ---------------------------------------------------------------------------
SITUACOES_VALIDAS: set[str] = set()
RESULTADOS_VALIDOS: set[str] = set()
COMBINACOES_VALIDAS: int = 92  # valor fixo do source-of-truth

# Campos de saida publicos (os 8 campos obrigatorios de cada regra)
CAMPOS_OUTPUT: tuple[str, ...] = (
    "estagio_funil",
    "fase",
    "tipo_contato",
    "acao_futura",
    "temperatura",
    "followup_dias",
    "grupo_dash",
    "tipo_acao",
)

# Situacoes conhecidas do dominio CRM VITAO360 (7 situacoes x 14 resultados = 92 combinacoes)
# LEAD   = prospect no funil, nunca comprou; objetivo: qualificar e converter em 1a venda
# NOVO   = cliente com 1a compra recente; objetivo: onboarding e gerar 2a compra
# ATIVO  = cliente com compras recentes (<=50 dias)
# EM RISCO = cliente proximo do limite de inatividade (51-60 dias)
# INAT.REC = cliente inativo recente (61-90 dias); cadencia de salvamento
# INAT.ANT = cliente inativo antigo (>90 dias); cadencia de reativacao
# PROSPECT = contato sem nenhuma compra nem funil ativo
SITUACOES_CONHECIDAS: tuple[str, ...] = (
    "ATIVO",
    "EM RISCO",
    "INAT.ANT",
    "INAT.REC",
    "LEAD",
    "NOVO",
    "PROSPECT",
)

# ---------------------------------------------------------------------------
# Tabela de regras: (SITUACAO, RESULTADO) -> dict com 8 dimensoes de output
# Populada em _carregar_regras() ao importar o modulo.
# ---------------------------------------------------------------------------
_REGRAS: dict[tuple[str, str], dict] = {}

# Indice secundario: situacao -> list de combos (para listar_combinacoes_por_situacao)
_REGRAS_POR_SITUACAO: dict[str, list[dict]] = {}

# Metadados preservados do JSON (para stats())
_META: dict = {}


# ---------------------------------------------------------------------------
# Carregamento do JSON na importacao do modulo
# ---------------------------------------------------------------------------

def _carregar_regras() -> None:
    """Carrega motor_regras_v4.json e popula _REGRAS, SITUACOES_VALIDAS, RESULTADOS_VALIDOS.

    Executada automaticamente ao importar o modulo. Gera FileNotFoundError
    se o JSON nao existir, pois o motor e inutilizavel sem ele.
    """
    global SITUACOES_VALIDAS, RESULTADOS_VALIDOS, _META

    if not MOTOR_REGRAS_JSON.exists():
        raise FileNotFoundError(
            f"JSON de regras nao encontrado: {MOTOR_REGRAS_JSON}\n"
            "Verifique o path em data/intelligence/motor_regras_v4.json"
        )

    with MOTOR_REGRAS_JSON.open(encoding="utf-8") as fh:
        dados = json.load(fh)

    _META = dados.get("meta", {})
    SITUACOES_VALIDAS = set(_META.get("situacoes_unicas", []))
    RESULTADOS_VALIDOS = set(_META.get("resultados_unicos", []))

    combinacoes = dados.get("combinacoes", [])
    for combo in combinacoes:
        situacao = combo["situacao"].strip().upper()
        resultado = combo["resultado"].strip().upper()
        chave = (situacao, resultado)

        entrada: dict = {
            "estagio_funil": combo.get("estagio_funil", "INDEFINIDO"),
            "fase": combo.get("fase", "INDEFINIDO"),
            "tipo_contato": combo.get("tipo_contato", "INDEFINIDO"),
            "acao_futura": combo.get("acao_futura", "VERIFICAR MANUALMENTE"),
            "temperatura": combo.get("temperatura", "FRIO"),
            "followup_dias": combo.get("followup_dias", 0),
            "grupo_dash": combo.get("grupo_dash", "NAO VENDA"),
            "tipo_acao": combo.get("tipo_acao", "ADMIN"),
            # campos internos (prefixo _ para distinguir dos 8 campos publicos)
            "_regra_aplicada": True,
            "_numero_regra": combo.get("numero"),
            "_chave": combo.get("chave", f"{situacao}|{resultado}"),
            # dados originais preservados para rastreabilidade
            "_situacao_original": combo["situacao"],
            "_resultado_original": combo["resultado"],
        }
        _REGRAS[chave] = entrada

        # Indice por situacao
        if situacao not in _REGRAS_POR_SITUACAO:
            _REGRAS_POR_SITUACAO[situacao] = []
        _REGRAS_POR_SITUACAO[situacao].append(entrada)

    total_carregadas = len(_REGRAS)
    if total_carregadas != COMBINACOES_VALIDAS:
        logger.warning(
            "Esperava %d combinacoes, carregou %d. Verifique motor_regras_v4.json.",
            COMBINACOES_VALIDAS,
            total_carregadas,
        )
    else:
        logger.info(
            "Motor de Regras v4 carregado: %d combinacoes (%d situacoes x ~%d resultados)",
            total_carregadas,
            len(SITUACOES_VALIDAS),
            len(RESULTADOS_VALIDOS),
        )


# Executa imediatamente ao importar o modulo
_carregar_regras()


# ---------------------------------------------------------------------------
# API Publica -- funcoes principais
# ---------------------------------------------------------------------------

def aplicar_regra(situacao: str, resultado: str) -> dict | None:
    """Consulta a tabela de 92 regras e retorna as 8 dimensoes de output.

    Normaliza situacao e resultado (strip + upper) antes do lookup.
    Retorna None se a combinacao nao existir -- nunca inventa valores.

    Args:
        situacao: Situacao do cliente (ex: "ATIVO", "INAT.REC", "PROSPECT").
        resultado: Resultado do ultimo contato (ex: "VENDA / PEDIDO", "NAO ATENDE").

    Returns:
        Dict com chaves: estagio_funil, fase, tipo_contato, acao_futura,
        temperatura, followup_dias, grupo_dash, tipo_acao, _regra_aplicada,
        _numero_regra; ou None se a combinacao nao estiver nas 92 regras.
    """
    situacao_norm = (situacao or "").strip().upper()
    resultado_norm = (resultado or "").strip().upper()

    if not situacao_norm or not resultado_norm:
        logger.warning(
            "aplicar_regra: entrada vazia -- situacao=%r resultado=%r",
            situacao,
            resultado,
        )
        return None

    chave = (situacao_norm, resultado_norm)
    regra = _REGRAS.get(chave)

    if regra is None:
        logger.warning(
            "Combinacao nao encontrada: SITUACAO='%s' / RESULTADO='%s'",
            situacao_norm,
            resultado_norm,
        )
        return None

    return regra


def validar_combinacao(situacao: str, resultado: str) -> bool:
    """Verifica se a combinacao (SITUACAO, RESULTADO) existe nas 92 regras.

    Normalizacao identica a aplicar_regra: strip + upper.

    Args:
        situacao: Situacao do cliente.
        resultado: Resultado do ultimo contato.

    Returns:
        True se a combinacao esta nas 92 regras, False caso contrario.
    """
    situacao_norm = (situacao or "").strip().upper()
    resultado_norm = (resultado or "").strip().upper()
    return (situacao_norm, resultado_norm) in _REGRAS


def aplicar_regras_batch(
    df: pd.DataFrame,
    col_situacao: str = "situacao",
    col_resultado: str = "resultado",
) -> pd.DataFrame:
    """Aplica o motor de regras em lote a um DataFrame.

    Adiciona 8 novas colunas ao DataFrame original com os outputs do motor.
    Linhas sem combinacao valida recebem None/NaN nas colunas de output.
    Usa operacoes vetorizadas (map via Serie) onde possivel.

    Args:
        df: DataFrame com colunas de situacao e resultado.
        col_situacao: Nome da coluna de situacao (padrao: "situacao").
        col_resultado: Nome da coluna de resultado (padrao: "resultado").

    Returns:
        Copia do DataFrame com 8 colunas adicionadas:
        estagio_funil, fase, tipo_contato, acao_futura,
        temperatura, followup_dias, grupo_dash, tipo_acao.

    Raises:
        KeyError: Se col_situacao ou col_resultado nao existirem no DataFrame.
    """
    if col_situacao not in df.columns:
        raise KeyError(
            f"Coluna de situacao '{col_situacao}' nao encontrada no DataFrame. "
            f"Colunas disponiveis: {list(df.columns)}"
        )
    if col_resultado not in df.columns:
        raise KeyError(
            f"Coluna de resultado '{col_resultado}' nao encontrada no DataFrame. "
            f"Colunas disponiveis: {list(df.columns)}"
        )

    resultado_df = df.copy()

    # Normalizar as colunas de entrada para lookup
    situacoes_norm = (
        resultado_df[col_situacao]
        .astype(str)
        .str.strip()
        .str.upper()
    )
    resultados_norm = (
        resultado_df[col_resultado]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Construir chaves de lookup como lista de tuples
    chaves = list(zip(situacoes_norm, resultados_norm))

    # Buscar regras para cada linha (O(1) por lookup)
    regras_encontradas = [_REGRAS.get(chave) for chave in chaves]

    # Extrair cada campo de output em uma lista e atribuir como coluna
    for campo in CAMPOS_OUTPUT:
        resultado_df[campo] = [
            regra[campo] if regra is not None else None
            for regra in regras_encontradas
        ]

    # Log de cobertura
    total = len(df)
    encontradas = sum(1 for r in regras_encontradas if r is not None)
    nao_encontradas = total - encontradas
    if nao_encontradas > 0:
        logger.warning(
            "aplicar_regras_batch: %d/%d linhas sem regra correspondente",
            nao_encontradas,
            total,
        )
    else:
        logger.info(
            "aplicar_regras_batch: %d/%d linhas com regra aplicada",
            encontradas,
            total,
        )

    return resultado_df


# ---------------------------------------------------------------------------
# Helpers de consulta
# ---------------------------------------------------------------------------

def listar_situacoes() -> list[str]:
    """Retorna todos os valores unicos de SITUACAO presentes nas 92 regras.

    Returns:
        Lista de strings ordenada (ex: ["ATIVO", "EM RISCO", "INAT.ANT", ...]).
    """
    return sorted(SITUACOES_VALIDAS)


def listar_resultados() -> list[str]:
    """Retorna todos os valores unicos de RESULTADO presentes nas 92 regras.

    Returns:
        Lista de strings ordenada (ex: ["CADASTRO", "CS (SUCESSO DO CLIENTE)", ...]).
    """
    return sorted(RESULTADOS_VALIDOS)


def listar_combinacoes_por_situacao(situacao: str) -> list[dict]:
    """Retorna todas as combinacoes validas para uma dada SITUACAO.

    Args:
        situacao: Situacao a filtrar (case-insensitive, strip aplicado).

    Returns:
        Lista de dicts com os 8 campos de output para cada combinacao.
        Lista vazia se a situacao nao existir nas 92 regras.
    """
    situacao_norm = (situacao or "").strip().upper()
    combos = _REGRAS_POR_SITUACAO.get(situacao_norm, [])
    return [
        {campo: combo[campo] for campo in CAMPOS_OUTPUT}
        | {"_numero_regra": combo.get("_numero_regra")}
        for combo in combos
    ]


def stats() -> dict:
    """Retorna estatisticas resumidas do motor de regras.

    Returns:
        Dict com:
        - total_combinacoes: int -- total de regras carregadas
        - total_esperado: int -- 92 (valor fixo do source-of-truth)
        - integridade_ok: bool -- True se total_combinacoes == total_esperado
        - combinacoes_por_situacao: dict[str, int] -- contagem por situacao
        - combinacoes_por_temperatura: dict[str, int] -- contagem por temperatura
        - combinacoes_por_grupo_dash: dict[str, int] -- contagem por grupo_dash
        - combinacoes_por_tipo_acao: dict[str, int] -- contagem por tipo_acao
        - situacoes: list[str] -- todas as situacoes unicas ordenadas
        - resultados: list[str] -- todos os resultados unicos ordenados
        - fonte_json: str -- path do JSON de origem
        - versao: str -- titulo do motor (do campo meta.titulo)
        - gerado_em: str -- data de geracao do JSON
    """
    combinacoes_por_situacao: dict[str, int] = {}
    combinacoes_por_temperatura: dict[str, int] = {}
    combinacoes_por_grupo_dash: dict[str, int] = {}
    combinacoes_por_tipo_acao: dict[str, int] = {}

    for (situacao, _resultado), regra in _REGRAS.items():
        combinacoes_por_situacao[situacao] = combinacoes_por_situacao.get(situacao, 0) + 1

        temp = regra.get("temperatura", "INDEFINIDO")
        combinacoes_por_temperatura[temp] = combinacoes_por_temperatura.get(temp, 0) + 1

        grupo = regra.get("grupo_dash", "INDEFINIDO")
        combinacoes_por_grupo_dash[grupo] = combinacoes_por_grupo_dash.get(grupo, 0) + 1

        tipo = regra.get("tipo_acao", "INDEFINIDO")
        combinacoes_por_tipo_acao[tipo] = combinacoes_por_tipo_acao.get(tipo, 0) + 1

    return {
        "total_combinacoes": len(_REGRAS),
        "total_esperado": COMBINACOES_VALIDAS,
        "integridade_ok": len(_REGRAS) == COMBINACOES_VALIDAS,
        "combinacoes_por_situacao": dict(sorted(combinacoes_por_situacao.items())),
        "combinacoes_por_temperatura": dict(sorted(combinacoes_por_temperatura.items())),
        "combinacoes_por_grupo_dash": dict(sorted(combinacoes_por_grupo_dash.items())),
        "combinacoes_por_tipo_acao": dict(sorted(combinacoes_por_tipo_acao.items())),
        "situacoes": listar_situacoes(),
        "resultados": listar_resultados(),
        "fonte_json": str(MOTOR_REGRAS_JSON),
        "versao": _META.get("titulo", "Motor de Regras v4"),
        "gerado_em": _META.get("gerado_em", ""),
    }


# ---------------------------------------------------------------------------
# Compatibilidade com codigo legado -- funcoes existentes preservadas
# ---------------------------------------------------------------------------

def classificar_cliente(cliente: dict) -> dict:
    """Aplica o motor de regras a um unico cliente e retorna o dict enriquecido.

    O dict de entrada deve conter pelo menos: situacao, resultado.
    Todos os campos originais sao preservados; os outputs do motor sao adicionados
    com prefixo 'motor_'. Se a combinacao nao for encontrada, campos motor_* ficam None.

    Args:
        cliente: Dict com dados do cliente vindo do pipeline de importacao.

    Returns:
        Dict original + campos motor_* com as 8 dimensoes de output.
    """
    if not isinstance(cliente, dict):
        raise TypeError(f"classificar_cliente espera dict, recebeu {type(cliente)}")

    situacao = cliente.get("situacao", "")
    resultado = cliente.get("resultado", "")

    regra = aplicar_regra(situacao, resultado)

    enriquecido = dict(cliente)
    if regra is not None:
        enriquecido["motor_estagio_funil"] = regra["estagio_funil"]
        enriquecido["motor_fase"] = regra["fase"]
        enriquecido["motor_tipo_contato"] = regra["tipo_contato"]
        enriquecido["motor_acao_futura"] = regra["acao_futura"]
        enriquecido["motor_temperatura"] = regra["temperatura"]
        enriquecido["motor_followup_dias"] = regra["followup_dias"]
        enriquecido["motor_grupo_dash"] = regra["grupo_dash"]
        enriquecido["motor_tipo_acao"] = regra["tipo_acao"]
        enriquecido["motor_regra_aplicada"] = True
        enriquecido["motor_numero_regra"] = regra.get("_numero_regra")
    else:
        for campo in CAMPOS_OUTPUT:
            enriquecido[f"motor_{campo}"] = None
        enriquecido["motor_regra_aplicada"] = False
        enriquecido["motor_aviso"] = (
            f"Combinacao nao encontrada: ({situacao!r}, {resultado!r})"
        )

    return enriquecido


def processar_lote(clientes: list[dict]) -> list[dict]:
    """Processa uma lista de clientes em lote aplicando o motor de regras a cada um.

    Loga um sumario ao final: total processados, regras aplicadas, nao encontradas.

    Args:
        clientes: Lista de dicts de clientes do pipeline de importacao.

    Returns:
        Lista de dicts enriquecidos com campos motor_*.
    """
    if not clientes:
        logger.warning("processar_lote: lista de clientes vazia recebida")
        return []

    resultados: list[dict] = []
    total = len(clientes)
    aplicadas = 0
    nao_encontradas = 0

    for cliente in clientes:
        enriquecido = classificar_cliente(cliente)
        resultados.append(enriquecido)
        if enriquecido.get("motor_regra_aplicada"):
            aplicadas += 1
        else:
            nao_encontradas += 1

    logger.info(
        "processar_lote CONCLUIDO: %d clientes processados | %d regras aplicadas | %d combinacoes nao encontradas",
        total,
        aplicadas,
        nao_encontradas,
    )

    return resultados


# ---------------------------------------------------------------------------
# CLI -- execucao direta
# ---------------------------------------------------------------------------

def _imprimir_sumario() -> None:
    """Imprime sumario do estado atual do motor de regras."""
    s = stats()
    print()
    print("=" * 60)
    print(f"  {s['versao']}")
    print("=" * 60)
    print(f"  Combinacoes carregadas : {s['total_combinacoes']}/{s['total_esperado']}")
    print(f"  Integridade            : {'OK' if s['integridade_ok'] else 'FALHA'}")
    print(f"  Situacoes validas ({len(s['situacoes'])})  :")
    for sit in s["situacoes"]:
        n = s["combinacoes_por_situacao"].get(sit, 0)
        print(f"    - {sit:<15} ({n} combinacoes)")
    print(f"  Resultados validos ({len(s['resultados'])}) :")
    for res in s["resultados"]:
        print(f"    - {res}")
    print("  Por temperatura:")
    for temp, cnt in s["combinacoes_por_temperatura"].items():
        print(f"    {temp:<12}: {cnt}")
    print("  Por grupo_dash:")
    for grupo, cnt in s["combinacoes_por_grupo_dash"].items():
        print(f"    {grupo:<14}: {cnt}")
    print("=" * 60)


def _smoke_test() -> None:
    """Testa 5 combinacoes conhecidas para validar o carregamento."""
    casos = [
        ("ATIVO", "VENDA / PEDIDO"),
        ("PROSPECT", "NÃO RESPONDE"),
        ("INAT.REC", "EM ATENDIMENTO"),
        # LEAD: prospect no funil, foco em qualificacao e 1a venda
        ("LEAD", "EM ATENDIMENTO"),
        # NOVO: cliente recente, foco em onboarding e 2a compra
        ("NOVO", "PÓS-VENDA"),
    ]
    print("\n  SMOKE TEST -- 3 combinacoes conhecidas:")
    for situacao, resultado in casos:
        r = aplicar_regra(situacao, resultado)
        if r is not None:
            print(
                f"  [OK ] {situacao} + {resultado}"
                f" => estagio={r['estagio_funil']}"
                f" | temp={r['temperatura']}"
                f" | dias={r['followup_dias']}"
            )
        else:
            print(f"  [MISS] {situacao} + {resultado} => combinacao nao encontrada")
    print()


def _executar_self_test() -> int:
    """Auto-teste completo do motor de regras.

    Testa aplicar_regra, validar_combinacao, aplicar_regras_batch,
    listar_situacoes, listar_resultados, listar_combinacoes_por_situacao e stats().

    Returns:
        0 se todos os testes passaram, 1 caso contrario.
    """
    falhas: list[str] = []

    print()
    print("=" * 60)
    print("  SELF TEST -- Motor de Regras v4")
    print("=" * 60)

    # --- 1. Integridade do carregamento ---
    total = len(_REGRAS)
    if total == COMBINACOES_VALIDAS:
        print(f"  [PASS] Carregamento: {total} combinacoes (esperado {COMBINACOES_VALIDAS})")
    else:
        msg = f"Carregamento: {total} combinacoes (esperado {COMBINACOES_VALIDAS})"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- 2. aplicar_regra -- combinacao conhecida com 8 campos presentes ---
    r = aplicar_regra("ATIVO", "VENDA / PEDIDO")
    if r is not None:
        print(f"  [PASS] aplicar_regra('ATIVO', 'VENDA / PEDIDO') => estagio_funil={r['estagio_funil']}")
        campos_ausentes = [c for c in CAMPOS_OUTPUT if c not in r]
        if not campos_ausentes:
            print("  [PASS] Todos os 8 campos de output presentes")
        else:
            msg = f"Campos ausentes no output: {campos_ausentes}"
            print(f"  [FAIL] {msg}")
            falhas.append(msg)
    else:
        msg = "aplicar_regra('ATIVO', 'VENDA / PEDIDO') retornou None inesperadamente"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- 3. aplicar_regra -- segunda combinacao conhecida ---
    r2 = aplicar_regra("INAT.REC", "EM ATENDIMENTO")
    if r2 is not None:
        print(f"  [PASS] aplicar_regra('INAT.REC', 'EM ATENDIMENTO') => temperatura={r2['temperatura']}")
    else:
        msg = "aplicar_regra('INAT.REC', 'EM ATENDIMENTO') retornou None inesperadamente"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- 4. aplicar_regra -- combinacao invalida deve retornar None ---
    r_invalida = aplicar_regra("SITUACAO_INEXISTENTE", "RESULTADO_INEXISTENTE")
    if r_invalida is None:
        print("  [PASS] aplicar_regra(invalido) => None (correto)")
    else:
        msg = "aplicar_regra(invalido) deveria retornar None"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- 5. aplicar_regra -- inputs vazios devem retornar None ---
    r_vazio = aplicar_regra("", "")
    if r_vazio is None:
        print("  [PASS] aplicar_regra('', '') => None (correto)")
    else:
        msg = "aplicar_regra('', '') deveria retornar None"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- 6. aplicar_regra -- None como input deve retornar None ---
    r_none = aplicar_regra(None, None)  # type: ignore[arg-type]
    if r_none is None:
        print("  [PASS] aplicar_regra(None, None) => None (correto)")
    else:
        msg = "aplicar_regra(None, None) deveria retornar None"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- 7. validar_combinacao -- positivo ---
    if validar_combinacao("ATIVO", "VENDA / PEDIDO") is True:
        print("  [PASS] validar_combinacao('ATIVO', 'VENDA / PEDIDO') => True")
    else:
        msg = "validar_combinacao('ATIVO', 'VENDA / PEDIDO') deveria ser True"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- 8. validar_combinacao -- negativo ---
    if validar_combinacao("INVALIDO", "INVALIDO") is False:
        print("  [PASS] validar_combinacao('INVALIDO', 'INVALIDO') => False")
    else:
        msg = "validar_combinacao('INVALIDO', 'INVALIDO') deveria ser False"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- 9. aplicar_regras_batch -- estrutura e cobertura ---
    df_teste = pd.DataFrame([
        {"situacao": "ATIVO", "resultado": "VENDA / PEDIDO"},
        {"situacao": "INAT.REC", "resultado": "EM ATENDIMENTO"},
        {"situacao": "INVALIDA", "resultado": "INVALIDO"},
        {"situacao": "", "resultado": ""},
    ])
    df_resultado = aplicar_regras_batch(df_teste)

    if all(c in df_resultado.columns for c in CAMPOS_OUTPUT):
        print(f"  [PASS] aplicar_regras_batch: 8 colunas de output adicionadas")
    else:
        ausentes = [c for c in CAMPOS_OUTPUT if c not in df_resultado.columns]
        msg = f"aplicar_regras_batch: colunas ausentes = {ausentes}"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    if df_resultado.iloc[0]["temperatura"] is not None:
        print(f"  [PASS] aplicar_regras_batch: linha 0 preenchida (temperatura={df_resultado.iloc[0]['temperatura']})")
    else:
        msg = "aplicar_regras_batch: linha 0 (ATIVO+VENDA) deveria ter temperatura preenchida"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # Pandas converte None para NaN em colunas mistas, aceitar ambos
    temp_invalida = df_resultado.iloc[2]["temperatura"]
    if temp_invalida is None or pd.isna(temp_invalida):
        print("  [PASS] aplicar_regras_batch: linha invalida => None/NaN (correto)")
    else:
        msg = f"aplicar_regras_batch: linha invalida deveria ter temperatura=None/NaN, got {temp_invalida!r}"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- 10. listar_situacoes ---
    situacoes = listar_situacoes()
    if len(situacoes) == 7:
        print(f"  [PASS] listar_situacoes: {len(situacoes)} situacoes")
    else:
        msg = f"listar_situacoes: esperava 7, retornou {len(situacoes)}"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- 11. listar_resultados ---
    resultados_lista = listar_resultados()
    if len(resultados_lista) == 14:
        print(f"  [PASS] listar_resultados: {len(resultados_lista)} resultados")
    else:
        msg = f"listar_resultados: esperava 14, retornou {len(resultados_lista)}"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- 12. listar_combinacoes_por_situacao -- situacao valida ---
    combos_ativo = listar_combinacoes_por_situacao("ATIVO")
    if len(combos_ativo) > 0:
        print(f"  [PASS] listar_combinacoes_por_situacao('ATIVO'): {len(combos_ativo)} combinacoes")
    else:
        msg = "listar_combinacoes_por_situacao('ATIVO') retornou lista vazia"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- 13. listar_combinacoes_por_situacao -- situacao invalida ---
    combos_invalida = listar_combinacoes_por_situacao("SITUACAO_INVALIDA")
    if combos_invalida == []:
        print("  [PASS] listar_combinacoes_por_situacao(invalida) => [] (correto)")
    else:
        msg = "listar_combinacoes_por_situacao(invalida) deveria retornar []"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- 14. stats ---
    s = stats()
    if s["total_combinacoes"] == COMBINACOES_VALIDAS and s["integridade_ok"]:
        print(f"  [PASS] stats(): {s['total_combinacoes']} combinacoes, integridade OK")
    else:
        msg = f"stats(): integridade={s['integridade_ok']}, total={s['total_combinacoes']}"
        print(f"  [FAIL] {msg}")
        falhas.append(msg)

    # --- Resultado final ---
    print()
    print("=" * 60)
    if not falhas:
        print(f"  RESULTADO: PASSOU -- 0 falhas")
        print("=" * 60)
        return 0
    else:
        print(f"  RESULTADO: FALHOU -- {len(falhas)} falha(s)")
        for i, f in enumerate(falhas, 1):
            print(f"    {i}. {f}")
        print("=" * 60)
        return 1


def _processar_base_unificada() -> Optional[Path]:
    """Carrega base_unificada.json, processa lote, salva motor_output.json."""
    if not _BASE_UNIFICADA.exists():
        logger.info(
            "base_unificada.json nao encontrada em %s -- pulando processamento em lote",
            _BASE_UNIFICADA,
        )
        return None

    logger.info("Carregando base_unificada.json: %s", _BASE_UNIFICADA)
    with _BASE_UNIFICADA.open(encoding="utf-8") as fh:
        base = json.load(fh)

    # Aceita lista diretamente ou {"clientes": [...]}
    if isinstance(base, list):
        clientes = base
    elif isinstance(base, dict):
        clientes = base.get("clientes", base.get("data", []))
    else:
        logger.error("Formato inesperado em base_unificada.json: %s", type(base))
        return None

    logger.info("Processando %d clientes em lote...", len(clientes))
    resultado = processar_lote(clientes)

    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = _OUTPUT_DIR / "motor_output.json"
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(resultado, fh, ensure_ascii=False, indent=2)

    logger.info("motor_output.json salvo em: %s", output_path)

    # Estatisticas por temperatura
    freq_temp: dict[str, int] = {}
    freq_grupo: dict[str, int] = {}
    for c in resultado:
        t = c.get("motor_temperatura") or "INDEFINIDO"
        g = c.get("motor_grupo_dash") or "INDEFINIDO"
        freq_temp[t] = freq_temp.get(t, 0) + 1
        freq_grupo[g] = freq_grupo.get(g, 0) + 1

    print("\n  RESULTADO DO PROCESSAMENTO EM LOTE:")
    print(f"  Total processados: {len(resultado)}")
    print("  Por temperatura:")
    for temp, cnt in sorted(freq_temp.items()):
        print(f"    {temp:<12}: {cnt}")
    print("  Por grupo dashboard:")
    for grupo, cnt in sorted(freq_grupo.items()):
        print(f"    {grupo:<14}: {cnt}")
    print()

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Motor de Regras v4 -- CRM VITAO360")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Executa self-test completo e sai com exit code 0 (OK) ou 1 (FALHA)",
    )
    args = parser.parse_args()

    if args.test:
        exit_code = _executar_self_test()
        sys.exit(exit_code)

    # Modo normal: sumario + smoke test + processamento de lote (se disponivel)
    _imprimir_sumario()
    _smoke_test()

    output = _processar_base_unificada()
    if output:
        print(f"  Output salvo em: {output}")
    else:
        print("  [INFO] Nenhum processamento em lote -- base_unificada.json ausente.")
        print("  Para processar, gere o arquivo com: python scripts/motor/run_import.py")

    # Retorna exit code 0 apenas se todas as 92 combinacoes foram carregadas
    if len(_REGRAS) != COMBINACOES_VALIDAS:
        logger.error(
            "FALHA DE INTEGRIDADE: %d/%d combinacoes carregadas",
            len(_REGRAS),
            COMBINACOES_VALIDAS,
        )
        sys.exit(1)

    sys.exit(0)
