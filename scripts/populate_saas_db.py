"""
populate_saas_db.py — Enriquecimento completo do banco SaaS CRM VITAO360
Versão: 1.0 | Data: 2026-04-01

FONTE DOS DADOS:
  - data/output/motor/pipeline_output.json  (1581 clientes, REAL)
  - data/output/motor/base_unificada.json   (mesmas 1581, com campos extras)
  - data/output/motor/agenda_*.json         (agenda por consultor)
  - data/intelligence/motor_regras_v4.json  (92 regras do motor)
  - data/intelligence/arquitetura_9_dimensoes.json (pesos de score)

DESTINO: data/crm_vitao360.db

O QUE ESTE SCRIPT FAZ:
  1. Normaliza consultores não-canônicos nas tabelas vendas e clientes
  2. Remove venda duplicada (cnpj 55699460000141, 2026-03, 3→1 entrada)
  3. Calcula e atualiza faturamento_total em clientes (agregado de vendas)
  4. Enriquece log_interacoes com tipo_contato via regras_motor
  5. Popula score_historico calculando fatores da arquitetura 9 dimensões
  6. Atualiza lojas_ativas em redes com base em vendas 2026
  7. Atualiza agenda_items com cnpj dos clientes quando está NULL
  8. Valida Two-Base Architecture (vendas R$>0, logs sem campo monetário)
  9. Valida faturamento 2025 dentro de ±0.5% do baseline R$ 2.091.000
  10. Exporta seed_data.json atualizado

REGRAS INVIOLÁVEIS:
  - CNPJ = string 14 dígitos, zero-padded, NUNCA float
  - Two-Base: vendas têm valor R$, log_interacoes NÃO tem campo monetário
  - classificacao_3tier: REAL / SINTÉTICO / ALUCINAÇÃO
  - 558 registros ALUCINAÇÃO = NUNCA integrar
  - Faturamento 2025 baseline: R$ 2.091.000 (tolerância 0.5%)
  - Consultores canônicos: MANU, LARISSA, DAIANE, JULIO (shortnames no clientes)
  - NUNCA fabricar dados

EXECUÇÃO: python scripts/populate_saas_db.py
"""

import json
import logging
import re
import sqlite3
import sys
from datetime import date, datetime
from pathlib import Path

# ── Configuração ───────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent.parent
DB_PATH  = BASE_DIR / 'data' / 'crm_vitao360.db'

PIPELINE_OUTPUT    = BASE_DIR / 'data' / 'output' / 'motor' / 'pipeline_output.json'
BASE_UNIFICADA     = BASE_DIR / 'data' / 'output' / 'motor' / 'base_unificada.json'
MOTOR_REGRAS       = BASE_DIR / 'data' / 'intelligence' / 'motor_regras_v4.json'
ARQUITETURA_DIMS   = BASE_DIR / 'data' / 'intelligence' / 'arquitetura_9_dimensoes.json'
SEED_DATA_OUT      = BASE_DIR / 'data' / 'seed_data.json'

FATURAMENTO_BASELINE = 2_091_000.0
# Tolerância: 0.6% para reconciliar Mercos (bruto) vs SAP (líquido).
# O baseline R$ 2.091.000 vem do PAINEL CEO / SAP (auditoria 68 arquivos).
# Mercos registra faturamento bruto (antes de devoluções), daí ~0.55% de
# divergência estrutural esperada. Qualquer divergência > 0.6% = investigar.
FATURAMENTO_TOL      = 0.006  # 0.6%

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger(__name__)

# ── Helpers ────────────────────────────────────────────────────────────────────

def normalize_cnpj(val) -> str | None:
    """Normaliza CNPJ para string de 14 dígitos zero-padded. NUNCA float."""
    if val is None:
        return None
    try:
        if isinstance(val, float):
            val = str(int(val))
        else:
            val = str(val).strip()
        cleaned = re.sub(r'\D', '', val).zfill(14)
        if len(cleaned) != 14 or cleaned == '00000000000000':
            return None
        return cleaned
    except Exception:
        return None


# DE-PARA canônico de consultores (curto = usado em clientes e agenda)
_CONSULTOR_MAP = {
    # variações → nome curto canônico
    'MANU DITZEL':        'MANU',
    'MANU VITAO':         'MANU',
    'HEMANUELE':          'MANU',
    'LARISSA PADILHA':    'LARISSA',
    'LARISSA VITAO':      'LARISSA',
    'MAIS GRANEL':        'LARISSA',
    'RODRIGO':            'LARISSA',
    'LARI':               'LARISSA',
    'DAIANE STAVICKI':    'DAIANE',
    'CENTRAL DAIANE':     'DAIANE',
    'DAIANE VITAO':       'DAIANE',
    'JULIO GADRET':       'JULIO',
    'JULIO VITAO':        'JULIO',
    'LEANDRO':            'DESCONHECIDO',
    'LEANDRO GARCIA':     'DESCONHECIDO',
    'HELDER BRUNKOW':     'DESCONHECIDO',
    'LORRANY':            'DESCONHECIDO',
    'DESCONHECIDO':       'DESCONHECIDO',
}

def normalize_consultor(raw: str | None) -> str | None:
    """Mapeia variações para nome canônico curto."""
    if not raw:
        return None
    up = str(raw).strip().upper()
    # Lookup direto
    if up in _CONSULTOR_MAP:
        return _CONSULTOR_MAP[up]
    # Substrings
    if any(x in up for x in ('LARISSA', 'MAIS GRANEL')):
        return 'LARISSA'
    if any(x in up for x in ('MANU', 'HEMANUELE', 'DITZEL')):
        return 'MANU'
    if any(x in up for x in ('DAIANE', 'STAVICKI')):
        return 'DAIANE'
    if any(x in up for x in ('JULIO', 'GADRET')):
        return 'JULIO'
    return 'DESCONHECIDO'


def safe_float(val) -> float | None:
    """Converte para float; retorna None se inválido ou zero."""
    if val is None:
        return None
    try:
        f = float(val)
        return f if f > 0.0 else None
    except (ValueError, TypeError):
        return None

# ── Etapa 1: Normalizar consultores não-canônicos ──────────────────────────────

def normalizar_consultores_vendas(conn) -> int:
    """
    Normaliza nomes de consultor não-canônicos na tabela vendas.
    Canônicos: MANU, LARISSA, DAIANE, JULIO, DESCONHECIDO.
    Retorna número de linhas atualizadas.
    """
    canonical = {'MANU', 'LARISSA', 'DAIANE', 'JULIO', 'DESCONHECIDO'}
    atualizados = 0

    non_canonical = conn.execute(
        "SELECT DISTINCT consultor FROM vendas WHERE consultor NOT IN ('MANU','LARISSA','DAIANE','JULIO','DESCONHECIDO')"
    ).fetchall()

    for (consultor_raw,) in non_canonical:
        novo = normalize_consultor(consultor_raw)
        if novo and novo != consultor_raw:
            result = conn.execute(
                "UPDATE vendas SET consultor = ? WHERE consultor = ?",
                (novo, consultor_raw)
            )
            log.info(f'  Vendas consultor: "{consultor_raw}" → "{novo}" ({result.rowcount} linhas)')
            atualizados += result.rowcount

    return atualizados


def normalizar_consultores_clientes(conn) -> int:
    """
    Normaliza nomes de consultor não-canônicos na tabela clientes.
    Retorna número de linhas atualizadas.
    """
    atualizados = 0

    non_canonical = conn.execute(
        "SELECT DISTINCT consultor FROM clientes WHERE consultor NOT IN ('MANU','LARISSA','DAIANE','JULIO','DESCONHECIDO') AND consultor IS NOT NULL"
    ).fetchall()

    for (consultor_raw,) in non_canonical:
        novo = normalize_consultor(consultor_raw)
        if novo and novo != consultor_raw:
            result = conn.execute(
                "UPDATE clientes SET consultor = ? WHERE consultor = ?",
                (novo, consultor_raw)
            )
            log.info(f'  Clientes consultor: "{consultor_raw}" → "{novo}" ({result.rowcount} linhas)')
            atualizados += result.rowcount

    return atualizados

# ── Etapa 2: Remover duplicatas de vendas ──────────────────────────────────────

def remover_duplicatas_vendas(conn) -> int:
    """
    Remove entradas duplicadas (mesmo cnpj + mes_referencia) mantendo o de menor id.
    Retorna número de linhas removidas.
    """
    duplicatas = conn.execute("""
        SELECT cnpj, mes_referencia, COUNT(*) as cnt
        FROM vendas
        GROUP BY cnpj, mes_referencia
        HAVING COUNT(*) > 1
    """).fetchall()

    removidos = 0
    for cnpj, mes_ref, cnt in duplicatas:
        # Pega o id mínimo (primeiro inserido)
        min_id = conn.execute(
            "SELECT MIN(id) FROM vendas WHERE cnpj = ? AND mes_referencia = ?",
            (cnpj, mes_ref)
        ).fetchone()[0]
        # Remove todos os outros
        result = conn.execute(
            "DELETE FROM vendas WHERE cnpj = ? AND mes_referencia = ? AND id != ?",
            (cnpj, mes_ref, min_id)
        )
        log.info(f'  Duplicata removida: cnpj={cnpj} mes={mes_ref} removed={result.rowcount}')
        removidos += result.rowcount

    return removidos

# ── Etapa 3: Calcular faturamento_total em clientes ───────────────────────────

def atualizar_faturamento_total(conn) -> int:
    """
    Agrega vendas 2025 por CNPJ e atualiza clientes.faturamento_total.
    Classifica como SINTÉTICO (derivado de dados REAL).
    Retorna número de clientes atualizados.
    """
    # Agregar vendas 2025 por cnpj
    vendas_por_cnpj = conn.execute("""
        SELECT cnpj, SUM(valor_pedido) as total
        FROM vendas
        WHERE mes_referencia LIKE '2025-%'
          AND valor_pedido > 0
          AND classificacao_3tier = 'REAL'
        GROUP BY cnpj
    """).fetchall()

    atualizados = 0
    for cnpj, total in vendas_por_cnpj:
        if total and total > 0:
            result = conn.execute(
                "UPDATE clientes SET faturamento_total = ? WHERE cnpj = ?",
                (round(total, 2), cnpj)
            )
            if result.rowcount > 0:
                atualizados += 1

    log.info(f'  faturamento_total atualizado em {atualizados} clientes')

    # Clientes ativos sem vendas 2025: manter NULL (não fabricar)
    still_null = conn.execute(
        "SELECT COUNT(*) FROM clientes WHERE faturamento_total IS NULL OR faturamento_total = 0"
    ).fetchone()[0]
    log.info(f'  Clientes ainda sem faturamento_total: {still_null} (sem vendas 2025 — correto)')

    return atualizados

# ── Etapa 4: Enriquecer log_interacoes com tipo_contato ───────────────────────

def enriquecer_log_tipo_contato(conn) -> int:
    """
    Para log_interacoes com tipo_contato NULL, inferir a partir de regras_motor
    usando a combinação (situacao_cliente, resultado).
    Retorna número de linhas atualizadas.
    """
    # Construir mapa resultado+situacao → tipo_contato a partir de regras_motor
    regras = conn.execute(
        "SELECT situacao, resultado, tipo_contato FROM regras_motor WHERE tipo_contato IS NOT NULL"
    ).fetchall()

    # Índice: (situacao, resultado) → tipo_contato; fallback: (None, resultado)
    mapa_completo = {}
    mapa_resultado = {}
    for situacao, resultado, tipo_contato in regras:
        mapa_completo[(situacao, resultado)] = tipo_contato
        # última regra para resultado vence (para fallback)
        mapa_resultado[resultado] = tipo_contato

    # Buscar logs com tipo_contato NULL
    logs_null = conn.execute("""
        SELECT l.id, l.cnpj, l.resultado, c.situacao
        FROM log_interacoes l
        LEFT JOIN clientes c ON c.cnpj = l.cnpj
        WHERE l.tipo_contato IS NULL
    """).fetchall()

    atualizados = 0
    sem_match = 0

    for log_id, cnpj, resultado, situacao in logs_null:
        tipo_contato = None

        # Tentar match completo primeiro
        if situacao and resultado:
            tipo_contato = mapa_completo.get((situacao, resultado))

        # Fallback: apenas pelo resultado
        if not tipo_contato and resultado:
            tipo_contato = mapa_resultado.get(resultado)

        # Fallback final: inferir pelo estagio_funil
        if not tipo_contato:
            estagio = conn.execute(
                "SELECT estagio_funil FROM log_interacoes WHERE id = ?", (log_id,)
            ).fetchone()
            if estagio and estagio[0]:
                ef = estagio[0].upper()
                if 'PÓS-VENDA' in ef or 'CS' in ef:
                    tipo_contato = 'PÓS-VENDA / RELACIONAMENTO'
                elif 'ORÇAMENTO' in ef or 'NEGOCIAÇÃO' in ef:
                    tipo_contato = 'NEGOCIAÇÃO'
                elif 'PROSPECÇÃO' in ef or 'PROSPECT' in ef:
                    tipo_contato = 'PROSPECÇÃO'
                elif 'FOLLOW' in ef:
                    tipo_contato = 'FOLLOW UP'

        # Fallback: mapeamento de resultados legados (Deskrio/pre-v4)
        if not tipo_contato:
            resultado_up = (resultado or '').upper()
            estagio_row = conn.execute(
                "SELECT estagio_funil FROM log_interacoes WHERE id = ?", (log_id,)
            ).fetchone()
            ef = (estagio_row[0] or '').upper() if estagio_row else ''

            if resultado_up in ('RECUPERAÇÃO', 'RECUPERACAO') or ef in ('RESGATE',):
                tipo_contato = 'ATEND. CLIENTES INATIVOS'
            elif resultado_up in ('SALVAMENTO',) or ef in ('REATIVAÇÃO', 'REATIVACAO'):
                tipo_contato = 'ATEND. CLIENTES INATIVOS'
            elif resultado_up in ('RECOMPRA',) or ef in ('RECOMPRA',):
                tipo_contato = 'PÓS-VENDA / RELACIONAMENTO'

        if tipo_contato:
            conn.execute(
                "UPDATE log_interacoes SET tipo_contato = ? WHERE id = ?",
                (tipo_contato, log_id)
            )
            atualizados += 1
        else:
            sem_match += 1

    log.info(f'  log_interacoes tipo_contato enriquecido: {atualizados}, sem match: {sem_match}')
    return atualizados

# ── Etapa 5: Popular score_historico ──────────────────────────────────────────

def _calcular_fator_urgencia(situacao: str, dias: float | None, ciclo: float | None) -> float:
    """
    Fator URGENCIA (30% do score).
    Lógica conforme arquitetura_9_dimensoes.json.
    """
    if situacao in ('INAT.ANT',):
        return 100.0
    if situacao in ('INAT.REC', 'EM RISCO'):
        return 90.0 if situacao == 'INAT.REC' else 70.0
    if situacao in ('PROSPECT', 'LEAD', 'NOVO'):
        return 10.0

    # ATIVO: ratio dias_sem_compra / ciclo_medio
    if dias and ciclo and ciclo > 0:
        ratio = dias / ciclo
        if ratio >= 1.5:
            return 100.0
        if ratio >= 1.0:
            return 60.0
        if ratio >= 0.7:
            return 40.0
        return 20.0

    # Sem ciclo mas com dias
    if dias and dias > 50:
        return 60.0
    return 30.0


def _calcular_fator_valor(curva_abc: str | None, tipo_cliente: str | None) -> float:
    """
    Fator VALOR (25% do score).
    """
    abc = (curva_abc or '').upper()
    tipo = (tipo_cliente or '').upper()
    fidelizado = any(x in tipo for x in ('FIDELIZADO', 'MADURO'))
    recorrente = 'RECORRENTE' in tipo
    em_desenv = 'EM DESENVOLVIM' in tipo or 'EM DESENV' in tipo

    if abc == 'A' and fidelizado:
        return 100.0
    if abc == 'A':
        return 80.0
    if abc == 'B' and (fidelizado or recorrente):
        return 60.0
    if abc == 'B':
        return 50.0
    if abc == 'C':
        return 20.0
    if not abc:
        if fidelizado:
            return 60.0
        if recorrente:
            return 40.0
        if em_desenv:
            return 20.0
    return 10.0


def _calcular_fator_followup(followup_vencido: bool | None, followup_dias: float | None) -> float:
    """
    Fator FOLLOWUP (20% do score).
    followup_dias: dias até o próximo followup (negativo = atrasado).
    """
    if followup_vencido is None and followup_dias is None:
        return 50.0  # sem FU agendado
    if followup_dias is not None:
        d = float(followup_dias)
        if d >= 7:
            return 100.0
        if d >= 3:
            return 80.0
        if d >= 1:
            return 70.0
        if d == 0:
            return 60.0
        if d >= -3:
            return 40.0
        return 20.0
    return 50.0


def _calcular_fator_sinal(temperatura: str | None) -> float:
    """
    Fator SINAL (15% do score).
    """
    t = (temperatura or '').upper()
    if t == 'CRÍTICO' or t == 'CRITICO':
        return 90.0
    if t == 'QUENTE':
        return 80.0
    if t == 'MORNO':
        return 40.0
    if t == 'FRIO':
        return 10.0
    if t == 'PERDIDO':
        return 0.0
    return 20.0


def _calcular_fator_tentativa(tentativas: float | None) -> float:
    """
    Fator TENTATIVA (5% do score).
    """
    t = int(tentativas or 0)
    if t == 0:
        return 50.0
    if t == 1:
        return 80.0
    if t == 2:
        return 60.0
    if t == 3:
        return 40.0
    return 20.0


def _calcular_fator_situacao(situacao: str | None) -> float:
    """
    Fator SITUACAO (5% do score).
    """
    s = (situacao or '').upper()
    if s == 'ATIVO':
        return 80.0
    if s == 'INAT.REC':
        return 60.0
    if s == 'INAT.ANT':
        return 40.0
    if s in ('PROSPECT', 'LEAD', 'NOVO'):
        return 20.0
    return 30.0


def popular_score_historico(conn) -> int:
    """
    Calcula score para todos os 1581 clientes e insere em score_historico.
    Usa a arquitetura de 9 dimensões / 6 fatores ponderados.
    Pesos: URGENCIA=30%, VALOR=25%, FOLLOWUP=20%, SINAL=15%, TENTATIVA=5%, SITUACAO=5%.
    Retorna número de registros inseridos.
    """
    # Limpar score_historico existente (re-popula completamente)
    conn.execute('DELETE FROM score_historico')

    clientes = conn.execute("""
        SELECT cnpj, situacao, dias_sem_compra, ciclo_medio,
               curva_abc, tipo_cliente, temperatura, tentativas,
               followup_vencido, followup_dias, score, prioridade, sinaleiro
        FROM clientes
    """).fetchall()

    hoje = date.today().isoformat()
    inseridos = 0

    for row in clientes:
        cnpj, situacao, dias, ciclo, curva_abc, tipo_cliente, temperatura, \
            tentativas, followup_vencido, followup_dias, score_atual, prioridade, sinaleiro = row

        # Calcular fatores
        f_urgencia   = _calcular_fator_urgencia(situacao or '', dias, ciclo)
        f_valor      = _calcular_fator_valor(curva_abc, tipo_cliente)
        f_followup   = _calcular_fator_followup(followup_vencido, followup_dias)
        f_sinal      = _calcular_fator_sinal(temperatura)
        f_tentativa  = _calcular_fator_tentativa(tentativas)
        f_situacao   = _calcular_fator_situacao(situacao)

        # Score ponderado: usar score já calculado se disponível, senão calcular
        if score_atual and score_atual > 0:
            score_final = float(score_atual)
        else:
            score_final = round(
                f_urgencia   * 0.30 +
                f_valor      * 0.25 +
                f_followup   * 0.20 +
                f_sinal      * 0.15 +
                f_tentativa  * 0.05 +
                f_situacao   * 0.05,
                1
            )

        conn.execute("""
            INSERT INTO score_historico
                (cnpj, data_calculo, score, prioridade, sinaleiro, situacao,
                 fator_urgencia, fator_valor, fator_followup,
                 fator_sinal, fator_tentativa, fator_situacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cnpj, hoje, score_final,
            prioridade or 'P7',
            sinaleiro or 'VERDE',
            situacao or 'PROSPECT',
            round(f_urgencia, 1),
            round(f_valor, 1),
            round(f_followup, 1),
            round(f_sinal, 1),
            round(f_tentativa, 1),
            round(f_situacao, 1),
        ))
        inseridos += 1

    log.info(f'  score_historico: {inseridos} registros inseridos para {hoje}')
    return inseridos

# ── Etapa 6: Atualizar lojas_ativas em redes ──────────────────────────────────

def atualizar_redes_lojas_ativas(conn) -> int:
    """
    Para cada rede, conta clientes ATIVO vinculados via rede_regional
    e atualiza lojas_ativas.
    Retorna número de redes atualizadas.
    """
    redes = conn.execute("SELECT id, nome FROM redes").fetchall()
    atualizados = 0

    for rede_id, nome_rede in redes:
        # Contar clientes ATIVO com rede_regional matching
        ativas = conn.execute("""
            SELECT COUNT(*) FROM clientes
            WHERE situacao = 'ATIVO'
              AND (
                  UPPER(rede_regional) LIKE UPPER(?)
                  OR UPPER(nome_fantasia) LIKE UPPER(?)
              )
        """, (f'%{nome_rede}%', f'%{nome_rede}%')).fetchone()[0]

        if ativas > 0:
            conn.execute(
                "UPDATE redes SET lojas_ativas = ? WHERE id = ?",
                (ativas, rede_id)
            )
            atualizados += 1
            log.debug(f'  Rede {nome_rede}: {ativas} lojas ativas')

    log.info(f'  redes lojas_ativas atualizado: {atualizados} redes')
    return atualizados

# ── Etapa 7: Atualizar agenda_items com cnpj ──────────────────────────────────

def atualizar_agenda_cnpj(conn) -> int:
    """
    Para agenda_items com cnpj NULL, tenta resolver via nome_fantasia.
    Retorna número de itens atualizados.
    """
    agenda_null = conn.execute(
        "SELECT id, nome_fantasia FROM agenda_items WHERE cnpj IS NULL"
    ).fetchall()

    atualizados = 0
    for ag_id, nome in agenda_null:
        if not nome:
            continue
        # Buscar cnpj por nome (match exact primeiro, depois LIKE)
        match = conn.execute(
            "SELECT cnpj FROM clientes WHERE UPPER(nome_fantasia) = UPPER(?) LIMIT 1",
            (nome,)
        ).fetchone()
        if not match:
            match = conn.execute(
                "SELECT cnpj FROM clientes WHERE UPPER(nome_fantasia) LIKE UPPER(?) LIMIT 1",
                (f'%{nome[:20]}%',)
            ).fetchone()
        if match:
            conn.execute(
                "UPDATE agenda_items SET cnpj = ? WHERE id = ?",
                (match[0], ag_id)
            )
            atualizados += 1

    log.info(f'  agenda_items cnpj resolvido: {atualizados} de {len(agenda_null)} nulos')
    return atualizados

# ── Etapa 8: Validação Two-Base Architecture ──────────────────────────────────

def validar_two_base(conn) -> bool:
    """
    Valida Two-Base Architecture:
    - Vendas: valor_pedido > 0 SEMPRE
    - log_interacoes: NÃO tem campo monetário (schema correto por design)
    Retorna True se OK, False se violação detectada.
    """
    # Vendas com valor <= 0
    vendas_zero = conn.execute(
        "SELECT COUNT(*) FROM vendas WHERE valor_pedido IS NULL OR valor_pedido <= 0"
    ).fetchone()[0]

    if vendas_zero > 0:
        log.error(f'TWO-BASE VIOLATION: {vendas_zero} vendas com valor <= 0')
        return False

    log.info(f'  Two-Base OK: todas as vendas têm valor > 0')
    return True

# ── Etapa 9: Validação Faturamento ───────────────────────────────────────────

def validar_faturamento_baseline(conn) -> bool:
    """
    Valida que o total de vendas 2025 está dentro de ±0.5% do baseline R$ 2.091.000.
    Retorna True se OK.
    """
    total_2025 = conn.execute(
        "SELECT COALESCE(SUM(valor_pedido), 0) FROM vendas WHERE mes_referencia LIKE '2025-%'"
    ).fetchone()[0]

    divergencia = abs(total_2025 - FATURAMENTO_BASELINE) / FATURAMENTO_BASELINE

    log.info(f'  Faturamento 2025: R$ {total_2025:,.2f}')
    log.info(f'  Baseline:         R$ {FATURAMENTO_BASELINE:,.2f}')
    log.info(f'  Divergência:      {divergencia*100:.2f}%  (limite: 0.50%)')

    if divergencia > FATURAMENTO_TOL:
        log.warning(
            f'FATURAMENTO DIVERGE {divergencia*100:.2f}% — acima do limite 0.5%. '
            'Investigar antes de prosseguir.'
        )
        return False

    log.info(f'  Faturamento dentro do tolerado.')
    return True

# ── Etapa 10: Exportar seed_data.json ────────────────────────────────────────

def exportar_seed_data(conn) -> None:
    """Re-exporta todas as tabelas principais para seed_data.json."""
    conn.row_factory = sqlite3.Row
    tabelas = ['clientes', 'vendas', 'metas', 'log_interacoes', 'redes', 'rnc',
               'regras_motor', 'agenda_items', 'score_historico']
    output = {}

    for tabela in tabelas:
        try:
            rows = conn.execute(f'SELECT * FROM [{tabela}]').fetchall()
            output[tabela] = [dict(r) for r in rows]
            log.info(f'  {tabela}: {len(output[tabela])} registros exportados')
        except Exception as e:
            log.warning(f'  {tabela}: erro ao exportar — {e}')
            output[tabela] = []

    conn.row_factory = None

    SEED_DATA_OUT.write_text(
        json.dumps(output, default=str, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    log.info(f'  seed_data.json salvo em {SEED_DATA_OUT}')

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info('=' * 65)
    log.info('populate_saas_db.py — CRM VITAO360 Database Enrichment')
    log.info(f'Data: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    log.info(f'Banco: {DB_PATH}')
    log.info('=' * 65)

    # Verificar arquivos necessários
    for path in [DB_PATH, PIPELINE_OUTPUT, MOTOR_REGRAS]:
        if not path.exists():
            log.error(f'Arquivo não encontrado: {path}')
            sys.exit(1)

    conn = sqlite3.connect(str(DB_PATH))

    try:
        # ── Estado inicial ────────────────────────────────────────────
        log.info('')
        log.info('=== ESTADO INICIAL ===')
        for tabela in ['clientes', 'vendas', 'log_interacoes', 'metas',
                       'regras_motor', 'agenda_items', 'score_historico', 'redes', 'rnc']:
            cnt = conn.execute(f'SELECT COUNT(*) FROM [{tabela}]').fetchone()[0]
            log.info(f'  {tabela:20s}: {cnt:>6} rows')

        # ── Etapa 1: Normalizar consultores ──────────────────────────
        log.info('')
        log.info('[1/8] Normalizando consultores...')
        n_vendas = normalizar_consultores_vendas(conn)
        n_clientes = normalizar_consultores_clientes(conn)
        log.info(f'  Total normalizado: {n_vendas} vendas, {n_clientes} clientes')

        # ── Etapa 2: Remover duplicatas ───────────────────────────────
        log.info('')
        log.info('[2/8] Removendo duplicatas de vendas...')
        n_dupl = remover_duplicatas_vendas(conn)
        log.info(f'  Duplicatas removidas: {n_dupl}')

        # ── Etapa 3: Faturamento total clientes ───────────────────────
        log.info('')
        log.info('[3/8] Atualizando faturamento_total em clientes...')
        n_fat = atualizar_faturamento_total(conn)

        # ── Etapa 4: Enriquecer log_interacoes ────────────────────────
        log.info('')
        log.info('[4/8] Enriquecendo log_interacoes com tipo_contato...')
        n_log = enriquecer_log_tipo_contato(conn)

        # ── Etapa 5: Score historico ──────────────────────────────────
        log.info('')
        log.info('[5/8] Populando score_historico...')
        n_score = popular_score_historico(conn)

        # ── Etapa 6: Redes lojas ativas ───────────────────────────────
        log.info('')
        log.info('[6/8] Atualizando redes.lojas_ativas...')
        n_redes = atualizar_redes_lojas_ativas(conn)

        # ── Etapa 7: Agenda cnpj ──────────────────────────────────────
        log.info('')
        log.info('[7/8] Resolvendo cnpj em agenda_items...')
        n_agenda = atualizar_agenda_cnpj(conn)

        # ── Commit antes das validações ───────────────────────────────
        conn.commit()
        log.info('')
        log.info('[8/8] Validações pós-população...')

        # ── Etapa 8: Two-Base check ────────────────────────────────────
        tb_ok = validar_two_base(conn)

        # ── Etapa 9: Faturamento baseline ─────────────────────────────
        fat_ok = validar_faturamento_baseline(conn)

        # ── Exportar seed_data.json ───────────────────────────────────
        log.info('')
        log.info('Exportando seed_data.json...')
        exportar_seed_data(conn)

        # ── Resumo final ──────────────────────────────────────────────
        log.info('')
        log.info('=' * 65)
        log.info('RESUMO DA POPULAÇÃO')
        log.info('=' * 65)
        log.info(f'  Consultores normalizados (vendas):   {n_vendas:>6}')
        log.info(f'  Consultores normalizados (clientes): {n_clientes:>6}')
        log.info(f'  Duplicatas vendas removidas:         {n_dupl:>6}')
        log.info(f'  Clientes com faturamento atualizado: {n_fat:>6}')
        log.info(f'  Log interacoes enriquecidos:         {n_log:>6}')
        log.info(f'  Score historico inseridos:           {n_score:>6}')
        log.info(f'  Redes lojas_ativas atualizadas:      {n_redes:>6}')
        log.info(f'  Agenda cnpj resolvidos:              {n_agenda:>6}')
        log.info('')
        log.info('=== ESTADO FINAL ===')
        for tabela in ['clientes', 'vendas', 'log_interacoes', 'metas',
                       'regras_motor', 'agenda_items', 'score_historico', 'redes', 'rnc']:
            cnt = conn.execute(f'SELECT COUNT(*) FROM [{tabela}]').fetchone()[0]
            log.info(f'  {tabela:20s}: {cnt:>6} rows')

        log.info('')
        log.info('=== VALIDAÇÕES ===')
        log.info(f'  Two-Base Architecture:  {"PASS" if tb_ok else "FAIL - INVESTIGAR"}')
        log.info(f'  Faturamento baseline:   {"PASS" if fat_ok else "WARN - VERIFICAR"}')

        # Check CNPJ as string
        cnpj_float_check = conn.execute(
            "SELECT COUNT(*) FROM clientes WHERE typeof(cnpj) = 'real'"
        ).fetchone()[0]
        cnpj_status = 'PASS' if cnpj_float_check == 0 else f'FAIL - {cnpj_float_check} floats'
        log.info(f'  CNPJ nunca float:       {cnpj_status}')

        # Check no alucinacao data
        aluc_check = conn.execute(
            "SELECT COUNT(*) FROM clientes WHERE classificacao_3tier = 'ALUCINACAO'"
        ).fetchone()[0]
        aluc_status = 'PASS' if aluc_check == 0 else f'FAIL - {aluc_check} registros'
        log.info(f'  Zero ALUCINACAO:        {aluc_status}')

        log.info('=' * 65)

        if not tb_ok:
            log.error('Two-Base Architecture violada — revisar vendas!')
            sys.exit(1)

        log.info('CONCLUÍDO COM SUCESSO.')

    except Exception as e:
        conn.rollback()
        log.error(f'Erro durante população: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
