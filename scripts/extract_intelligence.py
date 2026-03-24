import json, os, openpyxl

SOURCE = r'C:\Users\User\Downloads\VITAO360_ULTRA_FINAL (5).xlsx'
DEST_DIR = r'C:\Users\User\OneDrive\Documentos\GitHub\CRM-VITAO360\data\intelligence'

os.makedirs(DEST_DIR, exist_ok=True)
wb = openpyxl.load_workbook(SOURCE, data_only=True)
PERIODOS = ['P1','P2','P3','P4','P5','P6','P7','P8','P9','P10','P11','P12']

def save_json(filename, data):
    path = os.path.join(DEST_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path

def rows_of(sheet_name):
    ws = wb[sheet_name]
    return [r for r in ws.iter_rows(values_only=True) if any(v is not None for v in r)]

# ──────────────────────────────────────────────
# 1. PAINEL CEO
# ──────────────────────────────────────────────
def extract_painel_ceo():
    rows = rows_of('PAINEL CEO')
    kpi = rows[2]
    evolucao = []
    for row in rows[6:18]:
        if row[0] not in PERIODOS:
            continue
        evolucao.append({
            "periodo": row[0], "fat_2025": row[1], "fat_2026": row[2],
            "var_pct": round(float(row[3]), 4) if row[3] else None,
            "organica": row[4], "novos_pdv": row[5], "recompra": row[6],
            "redes": row[7], "custo": row[8], "sobra": row[9],
            "acumulado": row[10], "ativos": row[11],
        })
    ano = rows[18]
    totais_ano = {
        "fat_2025": ano[1], "fat_2026": ano[2],
        "var_pct": round(float(ano[3]), 4) if ano[3] else None,
        "organica": ano[4], "novos_pdv": ano[5], "recompra": ano[6],
        "redes": ano[7], "custo": ano[8], "sobra": ano[9],
        "acumulado": ano[10], "ativos": ano[11],
    }
    sinaleiro = []
    for row in rows[22:27]:
        if row[0]:
            sinaleiro.append({
                "nivel": row[0], "qtd": row[1], "pct_carteira": row[2],
                "ticket_medio": row[3], "acao": row[4], "perfil": row[5],
            })
    return {
        "_fonte": "VITAO360_ULTRA_FINAL (5).xlsx | PAINEL CEO",
        "_auditoria": "V_FINAL Marco/2026 - dados 100% auditados",
        "faturamento_anual_2026": kpi[0],
        "faturamento_mes12": kpi[1],
        "sobra_acumulada": kpi[2],
        "roi_operacional": round(float(kpi[3]), 4) if kpi[3] else None,
        "ativos_p12": kpi[4],
        "cac_medio": kpi[5],
        "evolucao_mensal": evolucao,
        "totais_ano": totais_ano,
        "sinaleiro_crm": sinaleiro,
    }

# ──────────────────────────────────────────────
# 2. DIAGNOSTICO 2025
# ──────────────────────────────────────────────
def extract_diagnostico_2025():
    rows = rows_of('1. DIAGNOSTICO 2025')
    kpis = []
    for r in rows[4:14]:
        if r[0]:
            kpis.append({"kpi": r[0], "valor_real": r[1], "unidade": r[2],
                         "fonte": r[3], "observacao": r[4]})
    meses = []
    for r in rows[16:29]:
        if r[0]:
            meses.append({"mes": r[0], "faturamento": r[1], "clientes_ativos": r[2],
                          "novos": r[3], "retidos": r[4], "churned": r[5],
                          "retencao": r[6], "fat_acumulado": r[7]})
    freq = []
    for r in rows[30:38]:
        if r[0]:
            freq.append({"meses_ativo": r[0], "clientes": r[1],
                         "pct_total": r[2], "interpretacao": r[3]})
    return {
        "_fonte": "VITAO360_ULTRA_FINAL (5).xlsx | 1. DIAGNOSTICO 2025",
        "_auditoria": "CRM + SAP - auditoria forense 68 arquivos",
        "kpis_reais": kpis, "mes_a_mes": meses, "frequencia_compra": freq,
    }

# ──────────────────────────────────────────────
# 3. PREMISSAS
# ──────────────────────────────────────────────
def extract_premissas():
    rows = rows_of('2. PREMISSAS')
    base = []
    for r in rows[4:13]:
        if r[0]:
            base.append({"parametro": r[0], "valor": r[1], "unidade": r[2],
                         "fonte_nota": r[3], "tipo": r[4]})
    prod = []
    for r in rows[14:24]:
        if r[0]:
            prod.append({"parametro": r[0], "valor": r[1], "unidade": r[2],
                         "justificativa": r[3], "validacao_q1": r[4]})
    fases = []
    for r in rows[25:30]:
        if r[0]:
            fases.append({"fase": r[0], "periodos": r[1], "equipe": r[2],
                          "custo_mes": r[3], "gatilho": r[4]})
    return {
        "_fonte": "VITAO360_ULTRA_FINAL (5).xlsx | 2. PREMISSAS",
        "_auditoria": "Azul=editavel | 100% fundamentadas | REAL/CALCULADO/PREMISSA",
        "base_existente": base, "producao_equipe": prod, "fases_rampup": fases,
    }

# ──────────────────────────────────────────────
# 4. MOTOR RAMP-UP
# ──────────────────────────────────────────────
def extract_motor_rampup():
    rows = rows_of('3. MOTOR RAMP-UP')

    def to_dict(row):
        d = {"metrica": row[0]}
        for i, p in enumerate(PERIODOS, 1):
            d[p] = row[i]
        d['ANO'] = row[13]
        return d

    # Section headers are rows where col A has the label AND cols B-N are all None.
    # Data rows always have numeric values in cols B+.
    # Use exact section header labels (col A only populated) to switch buckets.
    SECTION_EXACT = {
        'EQUIPE': 'eq',
        'CLIENTES/MES': 'cl',
        'FATURAMENTO R$': 'fat',
        'RESULTADO R$': 'res',
        'UNIT ECONOMICS': 'ue',
    }
    buckets = {v: [] for v in SECTION_EXACT.values()}
    cur = None

    # Also skip the period-header row (Metrica, P1, P2, ...) and the first 2 info rows
    for row in rows:
        raw = str(row[0]) if row[0] else ''
        raw_up = raw.upper().replace('\xca', 'E').replace('\u00ca', 'E')
        # A row is a section header only if all cols 1-13 are None
        is_header_row = all(v is None for v in row[1:14])
        if is_header_row:
            for lbl, bkt in SECTION_EXACT.items():
                if raw_up == lbl or raw_up.startswith(lbl):
                    cur = bkt
                    break
            continue
        # Skip the column-header row (Metrica / P1 / P2 ...)
        if row[0] == 'Métrica' or row[0] == 'Metrica':
            continue
        if cur and row[0] is not None:
            buckets[cur].append(to_dict(row))

    return {
        "_fonte": "VITAO360_ULTRA_FINAL (5).xlsx | 3. MOTOR RAMP-UP",
        "_auditoria": "Formulas referenciam aba PREMISSAS. Q1=real.",
        "equipe_mensal": buckets['eq'],
        "clientes_mensal": buckets['cl'],
        "faturamento_mensal": buckets['fat'],
        "resultado_mensal": buckets['res'],
        "unit_economics": buckets['ue'],
    }

# ──────────────────────────────────────────────
# 5. EQUIPE 2026
# ──────────────────────────────────────────────
def extract_equipe_2026():
    rows = rows_of('4. EQUIPE 2026')
    SECTION_TRIGGERS = {
        'ORGANOGRAMA': 'org',
        'ROADMAP DE CONTRATA': 'roadmap',
        'FUNIL DI': 'funil',
        'METAS POR FUN': 'metas',
    }
    SKIP_HEADERS = {'Pessoa', 'Trimestre', 'Etapa do Funil', 'Funcao', 'Funcao',
                    'Funcao', 'Função', 'Etapa do Funil'}
    org, roadmap, funil, metas = [], [], [], []
    alerta_manu = None
    cur = None

    for row in rows:
        label = str(row[0]) if row[0] else ''
        label_up = label.upper()

        # Check for section header
        switched = False
        for trigger, bucket in SECTION_TRIGGERS.items():
            if trigger in label_up:
                cur = bucket
                switched = True
                break
        if switched:
            continue

        # Manu alert
        if 'HEMANUELE' in label_up or ('MANU' in label_up and 'LICEN' in label_up):
            alerta_manu = label
            continue

        # Skip column headers
        if label in SKIP_HEADERS or (row[0] in SKIP_HEADERS):
            continue

        if cur == 'org' and row[0]:
            org.append({"pessoa": row[0], "cargo": row[1], "territorio": row[2],
                        "status": row[3], "meta": row[4],
                        "atividade_dia": row[5], "obs": row[6]})
        elif cur == 'roadmap' and row[0]:
            roadmap.append({"trimestre": row[0], "acao": row[1], "equipe": row[2],
                            "custo_mes": row[3], "gatilho": row[4],
                            "porque": row[5], "fat_estimado": row[6]})
        elif cur == 'funil' and row[0]:
            funil.append({"etapa": row[0], "meta_mensal": row[1], "por_dia": row[2],
                          "taxa": row[3], "quem": row[4],
                          "ferramenta": row[5], "obs": row[6]})
        elif cur == 'metas' and row[0]:
            metas.append({"funcao": row[0], "kpi": row[1], "meta": row[2],
                          "unidade": row[3], "periodo": row[4],
                          "acao_se_nao_atingir": row[5], "referencia": row[6]})

    return {
        "_fonte": "VITAO360_ULTRA_FINAL (5).xlsx | 4. EQUIPE 2026",
        "_auditoria": "Organograma + roadmap contratacoes + funil diario",
        "alerta_manu": alerta_manu,
        "organograma": org,
        "roadmap_contratacoes": roadmap,
        "funil_diario": funil,
        "metas_por_funcao": metas,
    }

# ──────────────────────────────────────────────
# 6. Q1 2026 REAL
# ──────────────────────────────────────────────
def extract_q1_2026_real():
    rows = rows_of('5. Q1 2026 REAL')
    fat_real = []
    for r in rows[4:8]:
        if r[0] is None:
            continue
        if isinstance(r[0], str) and r[0].startswith('*'):
            continue
        fat_real.append({
            "mes": r[0], "faturamento": r[1], "clientes": r[2],
            "pedidos": r[3], "ticket_medio": r[4],
            "novos": r[5], "recompra": r[6], "obs": r[7],
        })

    nota_marco = None
    validacao = []
    veredito = None
    in_valid = False

    for row in rows:
        label = str(row[0]) if row[0] else ''
        label_up = label.upper()
        if 'VALIDA' in label_up and ('REAL' in label_up or 'MODELO' in label_up):
            in_valid = True
            continue
        if in_valid:
            if 'VEREDITO' in label_up:
                veredito = label
                in_valid = False
                continue
            if row[0] == 'Indicador':
                continue
            if row[0]:
                validacao.append({
                    "indicador": row[0], "modelo": row[1], "real": row[2],
                    "variacao": row[3], "status": row[4], "observacao": row[5],
                })
        if row[0] and isinstance(row[0], str) and row[0].startswith('*') and 'arcial' in row[0]:
            nota_marco = row[0]

    return {
        "_fonte": "VITAO360_ULTRA_FINAL (5).xlsx | 5. Q1 2026 REAL",
        "_auditoria": "SAP Vendas Jan-Mar 2026 | 2.758 itens SAP | 178 clientes F2B",
        "nota_marco_parcial": nota_marco,
        "faturamento_real": fat_real,
        "validacao_modelo": validacao,
        "veredito": veredito,
    }

# ──────────────────────────────────────────────
# 7. CONFLITOS RESOLVIDOS
# ──────────────────────────────────────────────
def extract_conflitos_resolvidos():
    rows = rows_of('7. CONFLITOS RESOLVIDOS')
    conflitos, pendentes = [], []
    cur = None

    for row in rows:
        label = str(row[0]) if row[0] else ''
        label_up = label.upper()
        if 'CONFLITOS DE DADOS' in label_up:
            cur = 'c'
            continue
        if 'PREMISSAS PENDENTES' in label_up:
            cur = 'p'
            continue
        if row[0] in ('Tema', 'Premissa'):
            continue
        if cur == 'c' and row[0]:
            conflitos.append({
                "tema": row[0], "valor_a": row[1], "valor_b": row[2],
                "decisao": row[3], "justificativa": row[4],
            })
        elif cur == 'p' and row[0]:
            pendentes.append({
                "premissa": row[0], "valor_usado": row[1], "status": row[2],
                "se_errado": row[3], "acao": row[4],
            })

    return {
        "_fonte": "VITAO360_ULTRA_FINAL (5).xlsx | 7. CONFLITOS RESOLVIDOS",
        "_auditoria": "Auditoria forense 68 arquivos - decisao documentada",
        "conflitos": conflitos,
        "premissas_pendentes": pendentes,
    }

# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────
print("=" * 60)
print("EXTRACAO DE INTELIGENCIA — VITAO360_ULTRA_FINAL (5).xlsx")
print("=" * 60)

extractions = [
    ("painel_ceo.json",           extract_painel_ceo),
    ("diagnostico_2025.json",     extract_diagnostico_2025),
    ("premissas.json",            extract_premissas),
    ("motor_rampup.json",         extract_motor_rampup),
    ("equipe_2026.json",          extract_equipe_2026),
    ("q1_2026_real.json",         extract_q1_2026_real),
    ("conflitos_resolvidos.json", extract_conflitos_resolvidos),
]

created, errors = [], []
for filename, fn in extractions:
    try:
        data = fn()
        path = save_json(filename, data)
        size = os.path.getsize(path)
        created.append((filename, size))
        print(f"  [OK] {filename} ({size:,} bytes)")
    except Exception as e:
        import traceback
        errors.append((filename, str(e)))
        print(f"  [ERRO] {filename}: {e}")
        traceback.print_exc()

print()
print("=" * 60)
print(f"RESULTADO: {len(created)} arquivos criados | {len(errors)} erros")
print("=" * 60)

print()
print("VALIDACAO DE NUMEROS-CHAVE:")

with open(os.path.join(DEST_DIR, 'painel_ceo.json'), encoding='utf-8') as f:
    pc = json.load(f)
print(f"  Fat. Anual 2026  : R$ {pc['faturamento_anual_2026']:,.0f}")
print(f"  Sobra Acumulada  : R$ {pc['sobra_acumulada']:,.0f}")
print(f"  ROI Operacional  : {pc['roi_operacional']:.2f}x")
print(f"  Ativos P12       : {pc['ativos_p12']}")
print(f"  CAC Medio        : R$ {pc['cac_medio']}")
print(f"  Periodos evolucao: {len(pc['evolucao_mensal'])}")
print(f"  Sinaleiro niveis : {len(pc['sinaleiro_crm'])}")

with open(os.path.join(DEST_DIR, 'diagnostico_2025.json'), encoding='utf-8') as f:
    diag = json.load(f)
fat_2025 = next((k['valor_real'] for k in diag['kpis_reais'] if k['kpi'] == 'Receita anual'), None)
print(f"  Fat. 2025 base   : R$ {fat_2025:,.0f}")
print(f"  Baseline R$2.091M: {'OK' if abs(fat_2025 - 2091000) / 2091000 < 0.005 else 'DIVERGENCIA'}")
print(f"  Meses auditados  : {len(diag['mes_a_mes'])}")
print(f"  Freq. cohort     : {len(diag['frequencia_compra'])}")

with open(os.path.join(DEST_DIR, 'q1_2026_real.json'), encoding='utf-8') as f:
    q1 = json.load(f)
q1_total = next((m['faturamento'] for m in q1['faturamento_real'] if m['mes'] == 'TOTAL Q1'), None)
print(f"  Q1 2026 real     : R$ {q1_total:,.0f}")
print(f"  Validacoes Q1    : {len(q1['validacao_modelo'])}")

with open(os.path.join(DEST_DIR, 'motor_rampup.json'), encoding='utf-8') as f:
    mr = json.load(f)
print(f"  Motor equipe rows: {len(mr['equipe_mensal'])}")
print(f"  Motor fat rows   : {len(mr['faturamento_mensal'])}")
print(f"  Motor result rows: {len(mr['resultado_mensal'])}")

with open(os.path.join(DEST_DIR, 'conflitos_resolvidos.json'), encoding='utf-8') as f:
    conf = json.load(f)
print(f"  Conflitos resol. : {len(conf['conflitos'])}")
print(f"  Premissas pend.  : {len(conf['premissas_pendentes'])}")

with open(os.path.join(DEST_DIR, 'equipe_2026.json'), encoding='utf-8') as f:
    eq = json.load(f)
print(f"  Equipe organog.  : {len(eq['organograma'])} pessoas")
print(f"  Roadmap quarters : {len(eq['roadmap_contratacoes'])}")
print(f"  Funil etapas     : {len(eq['funil_diario'])}")
print(f"  Metas por funcao : {len(eq['metas_por_funcao'])}")

with open(os.path.join(DEST_DIR, 'premissas.json'), encoding='utf-8') as f:
    prem = json.load(f)
print(f"  Base existente   : {len(prem['base_existente'])} params")
print(f"  Producao equipe  : {len(prem['producao_equipe'])} params")
print(f"  Fases ramp-up    : {len(prem['fases_rampup'])} fases")

print()
print(f"Arquivos salvos em: {DEST_DIR}")
