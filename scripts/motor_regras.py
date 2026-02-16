"""
Motor de Regras V3 — CRM VITAO360
Implementa spec Part 15: RESULTADO → campos automaticos
Standalone module, importavel por build_v3.py
"""
from datetime import date, timedelta


# ═══════════════════════════════════════════════════════════════
# FUNCOES AUXILIARES
# ═══════════════════════════════════════════════════════════════

def dia_util(data_base, dias):
    """Calcula data futura em dias uteis (seg-sex)."""
    if dias == 0:
        return data_base
    atual = data_base
    contados = 0
    while contados < dias:
        atual += timedelta(days=1)
        if atual.weekday() < 5:
            contados += 1
    return atual


def calcular_situacao(dias_sem_compra, tem_compra, nunca_comprou):
    if nunca_comprou:
        return "PROSPECT"
    if not tem_compra:
        return "PROSPECT"
    if dias_sem_compra <= 50:
        return "ATIVO"
    if dias_sem_compra <= 60:
        return "EM RISCO"
    if dias_sem_compra <= 90:
        return "INAT.REC"
    return "INAT.ANT"


def calcular_sinaleiro_ciclo(dias_sem_compra, ciclo_medio):
    if ciclo_medio is None or ciclo_medio == 0:
        return "\U0001f7e3"  # 🟣
    if dias_sem_compra <= ciclo_medio:
        return "\U0001f7e2"  # 🟢
    if dias_sem_compra <= ciclo_medio + 30:
        return "\U0001f7e1"  # 🟡
    return "\U0001f534"  # 🔴


def calcular_sinaleiro_meta(realizado, meta):
    if meta is None or meta == 0:
        return "\u26AB"  # ⚫
    pct = realizado / meta
    if pct >= 1.0:
        return "\U0001f7e2"  # 🟢
    if pct >= 0.5:
        return "\U0001f7e1"  # 🟡
    if realizado == 0:
        return "\u26AB"  # ⚫
    return "\U0001f534"  # 🔴


def calcular_tipo_cliente(meses_positivado):
    if meses_positivado == 0:
        return "PROSPECT"
    if meses_positivado == 1:
        return "NOVO"
    if meses_positivado <= 3:
        return "EM DESENVOLVIMENTO"
    if meses_positivado <= 6:
        return "RECORRENTE"
    return "FIDELIZADO"


def calcular_curva(valor_total):
    if valor_total is None or valor_total == 0:
        return "C"
    if valor_total >= 2000:
        return "A"
    if valor_total >= 500:
        return "B"
    return "C"


def definir_consultor(uf, rede, vendedor_ultimo=""):
    rede_upper = (rede or "").upper()
    if "CIA DA SAUDE" in rede_upper or "CIA DA SAÚDE" in rede_upper or "FITLAND" in rede_upper:
        return "JULIO GADRET"
    redes_daiane = [
        "DIVINA TERRA", "BIOMUNDO", "BIO MUNDO", "MUNDO VERDE",
        "TUDO EM GRAOS", "TUDO EM GRÃOS", "VGA", "VIDA LEVE",
        "ARMAZEM", "ARMAZÉM", "NATURVIDA", "LIGEIRINHO",
        "TRIP", "ESMERALDA", "MERCOCENTRO",
    ]
    if any(r in rede_upper for r in redes_daiane):
        return "DAIANE STAVICKI"
    if uf in ["SC", "PR", "RS"]:
        return "MANU DITZEL"
    return "LARISSA PADILHA"


def calcular_oportunidade(itens_carrinho, acesso_b2b, comprou_mes):
    if itens_carrinho and itens_carrinho > 0 and not comprou_mes:
        return "\U0001f525 QUENTE"  # 🔥
    if acesso_b2b and acesso_b2b > 0:
        return "\U0001f7e1 MORNO"  # 🟡
    return "\u2744\ufe0f FRIO"  # ❄️


# ═══════════════════════════════════════════════════════════════
# CONSTANTES DO MOTOR
# ═══════════════════════════════════════════════════════════════

FOLLOW_UP_DIAS = {
    "EM ATENDIMENTO": 2,
    "ORÇAMENTO": 1,
    "CADASTRO": 2,
    "VENDA / PEDIDO": 45,
    "RELACIONAMENTO": 7,
    "FOLLOW UP 7": 7,
    "FOLLOW UP 15": 15,
    "SUPORTE": 0,
    "NÃO ATENDE": 1,
    "NÃO RESPONDE": 1,
    "RECUSOU LIGAÇÃO": 2,
    "PERDA / FECHOU LOJA": 0,
}

GRUPO_DASH = {
    "EM ATENDIMENTO": "FUNIL",
    "ORÇAMENTO": "FUNIL",
    "CADASTRO": "FUNIL",
    "VENDA / PEDIDO": "FUNIL",
    "RELACIONAMENTO": "RELAC.",
    "FOLLOW UP 7": "RELAC.",
    "FOLLOW UP 15": "RELAC.",
    "SUPORTE": "RELAC.",
    "NÃO ATENDE": "NÃO VENDA",
    "NÃO RESPONDE": "NÃO VENDA",
    "RECUSOU LIGAÇÃO": "NÃO VENDA",
    "PERDA / FECHOU LOJA": "NÃO VENDA",
}

RESULTADOS_NAO_ATENDE = ["NÃO ATENDE", "NÃO RESPONDE", "RECUSOU LIGAÇÃO"]


# ═══════════════════════════════════════════════════════════════
# MOTOR DE REGRAS PRINCIPAL
# ═══════════════════════════════════════════════════════════════

def motor_de_regras(situacao, resultado, estagio_anterior=None, tentativa_anterior=None):
    """
    Recebe SITUACAO + RESULTADO, retorna dict com TODOS os campos calculados.
    """
    r = {}
    r['follow_up_dias'] = FOLLOW_UP_DIAS.get(resultado, 0)
    r['grupo_dash'] = GRUPO_DASH.get(resultado, "")

    # ── REGRAS UNIVERSAIS (independe de situacao) ──

    if resultado == "VENDA / PEDIDO":
        r['estagio_funil'] = "PÓS-VENDA"
        r['fase'] = "PÓS-VENDA"
        r['tipo_contato'] = "PÓS-VENDA / RELACIONAMENTO"
        r['acao_futura'] = "PÓS-VENDA"
        r['acao_detalhada'] = "Acompanhamento pós-venda, garantir satisfação"
        r['temperatura'] = "\U0001f525 QUENTE"
        r['tentativa'] = None
        return r

    if resultado == "ORÇAMENTO":
        r['estagio_funil'] = "ORÇAMENTO"
        r['fase'] = "ORÇAMENTO"
        r['tipo_contato'] = "NEGOCIAÇÃO"
        r['temperatura'] = "\U0001f525 QUENTE"
        r['tentativa'] = None
        r['acao_futura'] = _acao_futura_por_situacao(situacao)
        r['acao_detalhada'] = "Proposta enviada, aguardando retorno"
        return r

    if resultado == "PERDA / FECHOU LOJA":
        r['estagio_funil'] = "PERDA / NUTRIÇÃO"
        r['fase'] = "NUTRIÇÃO"
        r['tipo_contato'] = "PERDA / NUTRIÇÃO"
        r['acao_futura'] = "NUTRIÇÃO"
        r['acao_detalhada'] = "Cliente perdido, manter nutrição longo prazo"
        r['temperatura'] = "\U0001f480 PERDIDO"
        r['tentativa'] = None
        return r

    # ── NÃO ATENDE / NÃO RESPONDE / RECUSOU → manter estágio, avançar tentativa ──

    if resultado in RESULTADOS_NAO_ATENDE:
        r['estagio_funil'] = estagio_anterior or _estagio_padrao(situacao)
        r['fase'] = _fase_padrao(situacao)
        r['tipo_contato'] = _tipo_contato_por_situacao(situacao)
        r['acao_futura'] = _acao_futura_por_situacao(situacao)
        r['temperatura'] = "\u2744\ufe0f FRIO"

        seq = {"T1": "T2", "T2": "T3", "T3": "T4"}
        if tentativa_anterior is None:
            r['tentativa'] = "T1"
            r['acao_detalhada'] = "1a tentativa sem resposta, tentar novamente"
        elif tentativa_anterior == "T4":
            r['estagio_funil'] = "PERDA / NUTRIÇÃO"
            r['fase'] = "NUTRIÇÃO"
            r['acao_futura'] = "NUTRIÇÃO"
            r['temperatura'] = "\U0001f480 PERDIDO"
            r['tentativa'] = "NUTRIÇÃO"
            r['acao_detalhada'] = "4 tentativas sem resposta, mover para nutrição"
        else:
            r['tentativa'] = seq.get(tentativa_anterior, "T1")
            r['acao_detalhada'] = f"Tentativa {r['tentativa']} sem resposta"
        return r

    # ── DEMAIS RESULTADOS por situacao ──

    r['tentativa'] = None  # reset quando responde
    r['temperatura'] = "\U0001f7e1 MORNO"

    if resultado == "EM ATENDIMENTO":
        r['estagio_funil'] = "EM ATENDIMENTO"
        if situacao == "PROSPECT":
            r['fase'] = "PROSPECÇÃO"
            r['tipo_contato'] = "PROSPECÇÃO"
            r['acao_detalhada'] = "Prospect respondeu, iniciar negociação"
        elif situacao in ["INAT.REC", "EM RISCO"]:
            r['fase'] = "SALVAMENTO"
            r['tipo_contato'] = "ATEND. CLIENTES INATIVOS"
            r['acao_detalhada'] = "Cliente inativo recente em atendimento, salvar"
        elif situacao == "INAT.ANT":
            r['fase'] = "RECUPERAÇÃO"
            r['tipo_contato'] = "ATEND. CLIENTES INATIVOS"
            r['acao_detalhada'] = "Cliente inativo antigo reativado, recuperar"
        else:  # ATIVO, NOVO
            r['fase'] = "EM ATENDIMENTO"
            r['tipo_contato'] = "ATEND. CLIENTES ATIVOS"
            r['acao_detalhada'] = "Cliente ativo em atendimento"

    elif resultado == "CADASTRO":
        r['estagio_funil'] = "EM ATENDIMENTO"
        r['fase'] = "PROSPECÇÃO"
        r['tipo_contato'] = "PROSPECÇÃO"
        r['acao_detalhada'] = "Novo cadastro em andamento"

    elif resultado == "RELACIONAMENTO":
        if situacao in ["ATIVO", "EM RISCO"]:
            r['estagio_funil'] = "CS / RECOMPRA"
            r['fase'] = "CS"
            r['acao_detalhada'] = "Manutenção de relacionamento, CS"
        elif situacao == "INAT.REC":
            r['estagio_funil'] = "CS / RECOMPRA"
            r['fase'] = "SALVAMENTO"
            r['acao_detalhada'] = "Salvando cliente inativo recente"
        else:  # INAT.ANT, PROSPECT
            r['estagio_funil'] = "RELACIONAMENTO"
            r['fase'] = "RECUPERAÇÃO"
            r['acao_detalhada'] = "Recuperando relacionamento"
        r['tipo_contato'] = "PÓS-VENDA / RELACIONAMENTO"

    elif resultado in ["FOLLOW UP 7", "FOLLOW UP 15"]:
        if situacao in ["ATIVO", "EM RISCO"]:
            r['estagio_funil'] = "CS / RECOMPRA"
            r['fase'] = "CS / RECOMPRA"
        else:
            r['estagio_funil'] = estagio_anterior or _estagio_padrao(situacao)
            r['fase'] = _fase_padrao(situacao)
        r['tipo_contato'] = "FOLLOW UP"
        dias = "7" if resultado == "FOLLOW UP 7" else "15"
        r['acao_detalhada'] = f"Follow-up {dias} dias agendado"

    elif resultado == "SUPORTE":
        r['estagio_funil'] = "RELACIONAMENTO"
        r['fase'] = "RELACIONAMENTO"
        r['tipo_contato'] = "PÓS-VENDA / RELACIONAMENTO"
        r['acao_detalhada'] = "Suporte prestado, problema resolvido"

    r['acao_futura'] = _acao_futura_por_situacao(situacao)
    return r


# ═══════════════════════════════════════════════════════════════
# HELPERS INTERNOS
# ═══════════════════════════════════════════════════════════════

def _estagio_padrao(situacao):
    return {
        "ATIVO": "CS / RECOMPRA",
        "EM RISCO": "CS / RECOMPRA",
        "INAT.REC": "EM ATENDIMENTO",
        "INAT.ANT": "EM ATENDIMENTO",
        "NOVO": "PÓS-VENDA",
        "PROSPECT": "PROSPECÇÃO",
    }.get(situacao, "EM ATENDIMENTO")


def _fase_padrao(situacao):
    return {
        "ATIVO": "RECOMPRA",
        "EM RISCO": "SALVAMENTO",
        "INAT.REC": "SALVAMENTO",
        "INAT.ANT": "RECUPERAÇÃO",
        "NOVO": "PÓS-VENDA",
        "PROSPECT": "PROSPECÇÃO",
    }.get(situacao, "EM ATENDIMENTO")


def _acao_futura_por_situacao(situacao):
    return {
        "ATIVO": "RECOMPRA",
        "EM RISCO": "SALVAMENTO",
        "INAT.REC": "SALVAMENTO",
        "INAT.ANT": "REATIVAÇÃO",
        "NOVO": "PÓS-VENDA",
        "PROSPECT": "PROSPECÇÃO",
    }.get(situacao, "ATENDIMENTO")


def _tipo_contato_por_situacao(situacao):
    return {
        "ATIVO": "ATEND. CLIENTES ATIVOS",
        "EM RISCO": "ATEND. CLIENTES ATIVOS",
        "INAT.REC": "ATEND. CLIENTES INATIVOS",
        "INAT.ANT": "ATEND. CLIENTES INATIVOS",
        "NOVO": "ATEND. CLIENTES ATIVOS",
        "PROSPECT": "PROSPECÇÃO",
    }.get(situacao, "ATEND. CLIENTES ATIVOS")


# ═══════════════════════════════════════════════════════════════
# SCORE PARA RANKING DA AGENDA (6 fatores)
# ═══════════════════════════════════════════════════════════════

def calcular_score(dias_sem_compra, ciclo_medio, curva, tipo_cliente,
                   follow_up_date, hoje, oportunidade, temperatura,
                   tentativa, situacao):
    # Fator 1: Urgencia temporal (30%)
    if ciclo_medio and ciclo_medio > 0:
        ratio = dias_sem_compra / ciclo_medio
        if ratio < 0.7:
            f1 = 0
        elif ratio <= 1.0:
            f1 = 30
        elif ratio <= 1.5:
            f1 = 60
        else:
            f1 = 90
    else:
        f1 = 50

    # Fator 2: Valor do cliente (25%)
    valor_map = {
        ("A", "FIDELIZADO"): 100,
        ("A", "RECORRENTE"): 80,
        ("B", "FIDELIZADO"): 70,
        ("B", "RECORRENTE"): 50,
    }
    f2 = valor_map.get((curva, tipo_cliente))
    if f2 is None:
        if curva == "A":
            f2 = 60
        elif curva == "B":
            f2 = 40
        elif situacao == "PROSPECT":
            f2 = 30
        else:
            f2 = 20

    # Fator 3: Follow-up vencido (20%)
    if follow_up_date and hoje:
        delta = (hoje - follow_up_date).days
        if delta == 0:
            f3 = 100
        elif 1 <= delta <= 3:
            f3 = 80
        elif 4 <= delta <= 7:
            f3 = 60
        elif delta > 7:
            f3 = 40
        else:
            f3 = 0
    else:
        f3 = 0

    # Fator 4: Sinal de compra (15%)
    opp = (oportunidade or "").upper()
    temp = (temperatura or "").upper()
    if "QUENTE" in opp:
        f4 = 100
    elif "QUENTE" in temp:
        f4 = 80
    elif "MORNO" in opp:
        f4 = 40
    else:
        f4 = 0

    # Fator 5: Tentativa (5%)
    tent_map = {"T4": 100, "T3": 50, "T2": 10, "T1": 10}
    f5 = tent_map.get(tentativa, 0)

    # Fator 6: Situacao (5%)
    sit_map = {"EM RISCO": 80, "INAT.REC": 60, "ATIVO": 40, "INAT.ANT": 20, "PROSPECT": 10}
    f6 = sit_map.get(situacao, 20)

    score = (f1 * 0.30) + (f2 * 0.25) + (f3 * 0.20) + (f4 * 0.15) + (f5 * 0.05) + (f6 * 0.05)
    return round(score, 1)


# ═══════════════════════════════════════════════════════════════
# VALIDACAO
# ═══════════════════════════════════════════════════════════════

def validar_registro(situacao, estagio, fase, tipo_contato, acao, resultado):
    """Checa combinacoes proibidas. Retorna lista de erros (vazia = OK)."""
    erros = []

    if situacao == "PROSPECT":
        if fase in ["RECOMPRA", "CS", "PÓS-VENDA", "SALVAMENTO"]:
            erros.append(f"PROSPECT nao pode ter FASE={fase}")
        if tipo_contato in ["ATEND. CLIENTES ATIVOS", "ATEND. CLIENTES INATIVOS"]:
            erros.append(f"PROSPECT nao pode ter TIPO={tipo_contato}")

    if situacao == "ATIVO":
        if fase in ["SALVAMENTO", "RECUPERAÇÃO"]:
            erros.append(f"ATIVO nao pode ter FASE={fase}")
        if acao in ["REATIVAÇÃO", "SALVAMENTO"]:
            erros.append(f"ATIVO nao pode ter ACAO={acao}")

    if situacao == "INAT.ANT":
        if fase in ["CS", "RECOMPRA", "CS / RECOMPRA"]:
            erros.append(f"INAT.ANT nao pode ter FASE={fase}")

    if situacao == "NOVO":
        if fase in ["SALVAMENTO", "RECUPERAÇÃO"]:
            erros.append(f"NOVO nao pode ter FASE={fase}")

    if resultado == "VENDA / PEDIDO" and fase != "PÓS-VENDA":
        erros.append(f"VENDA deve ter FASE=PÓS-VENDA, nao {fase}")

    if resultado == "ORÇAMENTO" and estagio != "ORÇAMENTO":
        erros.append(f"ORÇAMENTO deve ter ESTAGIO=ORÇAMENTO, nao {estagio}")

    if resultado == "CADASTRO" and situacao not in ["PROSPECT", "NOVO"]:
        erros.append(f"CADASTRO so para PROSPECT/NOVO, nao {situacao}")

    return erros


# ═══════════════════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=== Motor de Regras V3 — Self Test ===\n")

    tests = [
        ("ATIVO", "VENDA / PEDIDO", None, None),
        ("PROSPECT", "ORÇAMENTO", None, None),
        ("INAT.REC", "NÃO ATENDE", "EM ATENDIMENTO", None),
        ("ATIVO", "FOLLOW UP 7", "CS / RECOMPRA", None),
        ("INAT.ANT", "PERDA / FECHOU LOJA", None, None),
        ("ATIVO", "EM ATENDIMENTO", None, None),
        ("PROSPECT", "CADASTRO", "PROSPECÇÃO", None),
        ("INAT.REC", "RELACIONAMENTO", None, None),
        ("ATIVO", "NÃO ATENDE", "CS / RECOMPRA", "T1"),
        ("ATIVO", "NÃO ATENDE", "CS / RECOMPRA", "T4"),
    ]

    all_ok = True
    for sit, res, est_ant, tent_ant in tests:
        r = motor_de_regras(sit, res, est_ant, tent_ant)
        erros = validar_registro(sit, r['estagio_funil'], r['fase'],
                                 r['tipo_contato'], r.get('acao_futura', ''), res)
        status = "OK" if not erros else f"ERRO: {erros}"
        if erros:
            all_ok = False
        print(f"  {sit:12} + {res:22} -> EST={r['estagio_funil']:20} "
              f"FASE={r.get('fase',''):15} TIPO={r.get('tipo_contato',''):30} "
              f"TEMP={r.get('temperatura',''):12} TENT={str(r.get('tentativa','')):8} "
              f"[{status}]")

    print(f"\n{'ALL TESTS PASSED' if all_ok else 'SOME TESTS FAILED'}")
