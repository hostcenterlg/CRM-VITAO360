"""
Phase 04 - Shared Helpers
Funcoes compartilhadas para todo o pipeline LOG Completo.

Funcoes:
  normalize_cnpj       - CNPJ para 14 digitos zero-padded
  normalize_consultor   - Nomes de consultores para forma canonica
  classify_record       - Classificacao 3-tier: REAL / SINTETICO / ALUCINACAO
  make_dedup_key        - Chave composta DATA+CNPJ+RESULTADO
  make_log_record       - Dict com as 20 colunas LOG + metadados
  subtract_business_days - Calcular datas anteriores (seg-sex)
  generate_channels     - Combinacao WhatsApp/Ligacao/Lig.Atendida
  LOG_COLUMNS           - Lista ordenada das 20 colunas
"""

import re
import sys
import random
from datetime import date, timedelta
from pathlib import Path

# Garantir importacao de motor_regras.py do diretorio scripts/
_scripts_dir = str(Path(__file__).resolve().parent.parent)
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)

from motor_regras import motor_de_regras, dia_util, definir_consultor


# =====================================================================
# CONSTANTES
# =====================================================================

LOG_COLUMNS = [
    'DATA',              # A
    'CONSULTOR',         # B
    'NOME FANTASIA',     # C
    'CNPJ',              # D
    'UF',                # E
    'REDE/REGIONAL',     # F
    'SITUACAO',          # G
    'WHATSAPP',          # H
    'LIGACAO',           # I
    'LIGACAO ATENDIDA',  # J
    'TIPO ACAO',         # K
    'TIPO DO CONTATO',   # L
    'RESULTADO',         # M
    'MOTIVO',            # N
    'FOLLOW-UP',         # O
    'ACAO',              # P
    'MERCOS ATUALIZADO', # Q
    'FASE',              # R
    'TENTATIVA',         # S
    'NOTA DO DIA',       # T
]

# Vendedores ficticios (indicam alucinacao)
VENDEDORES_FICTICIOS = [
    "JOAO SILVA", "PEDRO OLIVEIRA", "MARIA SANTOS",
    "ANA COSTA", "CARLOS FERREIRA", "LUCAS ALMEIDA",
]

# Padroes de notas sinteticas (12 padroes genericos)
NOTAS_SINTETICAS_PADROES = [
    "primeiro contato com prospect",
    "follow-up apos primeiro contato",
    "material de marketing enviado",
    "apresentacao de catalogo",
    "envio de proposta comercial",
    "acompanhamento da proposta",
    "negociacao em andamento",
    "suporte pos-venda",
    "cliente solicitou 2a via",
    "cliente pediu rastreamento",
    "follow-up cs",
    "verificar reposicao",
]

# Mapeamento de RESULTADO sem acento <-> com acento (P8 VITAO SEM ACENTO no LOG)
# motor_regras.py usa acentos internamente
RESULTADO_SEM_ACENTO = {
    "EM ATENDIMENTO": "EM ATENDIMENTO",
    "ORCAMENTO": "ORÇAMENTO",
    "CADASTRO": "CADASTRO",
    "VENDA / PEDIDO": "VENDA / PEDIDO",
    "RELACIONAMENTO": "RELACIONAMENTO",
    "FOLLOW UP 7": "FOLLOW UP 7",
    "FOLLOW UP 15": "FOLLOW UP 15",
    "SUPORTE": "SUPORTE",
    "NAO ATENDE": "NÃO ATENDE",
    "NAO RESPONDE": "NÃO RESPONDE",
    "RECUSOU LIGACAO": "RECUSOU LIGAÇÃO",
    "PERDA / FECHOU LOJA": "PERDA / FECHOU LOJA",
}

# Reverso: com acento -> sem acento
RESULTADO_COM_ACENTO = {v: k for k, v in RESULTADO_SEM_ACENTO.items()}

# Mapeamento de consultores: variantes -> forma canonica
_CONSULTOR_MAP = {
    "CENTRAL - DAIANE": "DAIANE STAVICKI",
    "CENTRAL DAIANE": "DAIANE STAVICKI",
    "DAIANE": "DAIANE STAVICKI",
    "DAIANE STAVICKI": "DAIANE STAVICKI",
    "HEMANUELE DITZEL (MANU)": "MANU DITZEL",
    "HEMANUELE DITZEL": "MANU DITZEL",
    "MANU": "MANU DITZEL",
    "MANU DITZEL": "MANU DITZEL",
    "LARISSA PADILHA": "LARISSA PADILHA",
    "LARISSA": "LARISSA PADILHA",
    "JULIO GADRET": "JULIO GADRET",
    "JULIO  GADRET": "JULIO GADRET",
    "HELDER BRUNKOW": "HELDER BRUNKOW",
    "HELDER": "HELDER BRUNKOW",
    "LORRANY": "LORRANY",
    "LEANDRO GARCIA": "LEANDRO GARCIA",
    "LEANDRO": "LEANDRO GARCIA",
    "TIME": "TIME",
}


# =====================================================================
# FUNCOES
# =====================================================================

def normalize_cnpj(raw):
    """
    Remove tudo exceto digitos, zfill(14).
    Ex: '32.387.943/0001-05' -> '32387943000105'
    """
    if raw is None:
        return ""
    return re.sub(r'[^0-9]', '', str(raw)).zfill(14)


def normalize_consultor(nome):
    """
    Normaliza nomes de consultores para forma canonica.
    - 'CENTRAL - DAIANE' -> 'DAIANE STAVICKI'
    - 'Julio  Gadret' (espaco duplo) -> 'JULIO GADRET'
    - 'HEMANUELE DITZEL (MANU)' -> 'MANU DITZEL'
    - Todos uppercase, strip, replace multi-spaces
    """
    if nome is None:
        return ""
    # Uppercase, strip, collapse multi-spaces
    cleaned = re.sub(r'\s+', ' ', str(nome).upper().strip())
    # Lookup em mapeamento
    if cleaned in _CONSULTOR_MAP:
        return _CONSULTOR_MAP[cleaned]
    # Tentar match parcial para variantes com parenteses etc.
    for variant, canonical in _CONSULTOR_MAP.items():
        if variant in cleaned or cleaned in variant:
            return canonical
    # Se nao encontrou, retornar limpo
    return cleaned


def normalize_resultado(resultado):
    """
    Normaliza RESULTADO para formato SEM ACENTO (P8 VITAO SEM ACENTO).
    Retorna tupla (sem_acento, com_acento_para_motor).
    """
    if not resultado:
        return "", ""
    r = re.sub(r'\s+', ' ', str(resultado).upper().strip())

    # Remover acentos para lookup
    r_sem = r
    for com, sem in [
        ("ORÇAMENTO", "ORCAMENTO"),
        ("NÃO ATENDE", "NAO ATENDE"),
        ("NÃO RESPONDE", "NAO RESPONDE"),
        ("RECUSOU LIGAÇÃO", "RECUSOU LIGACAO"),
        ("LIGAÇÃO", "LIGACAO"),
    ]:
        r_sem = r_sem.replace(com, sem)

    # Se ja esta sem acento, mapear para com acento para o motor
    if r_sem in RESULTADO_SEM_ACENTO:
        return r_sem, RESULTADO_SEM_ACENTO[r_sem]

    # Se ja esta com acento, mapear para sem acento
    if r in RESULTADO_COM_ACENTO:
        return RESULTADO_COM_ACENTO[r], r

    # Fallback: retornar como esta
    return r_sem, r


def classify_record(cnpj, nome, vendedor, nota):
    """
    Classificacao 3-tier conforme criterios documentados na AUDITORIA.

    Retorna tupla (classificacao, razao):
      - 'ALUCINACAO': CNPJ invalido, nome padrao, vendedor ficticio
      - 'SINTETICO': Notas genericas, notas curtas
      - 'REAL': Passa todos os checks

    Args:
        cnpj: CNPJ bruto (antes de normalize)
        nome: Nome fantasia do cliente
        vendedor: Nome do vendedor/consultor
        nota: Nota do dia / observacao
    """
    # --- ALUCINACAO checks ---
    cnpj_clean = re.sub(r'[^0-9]', '', str(cnpj)) if cnpj else ""
    if len(cnpj_clean) < 14:
        return 'ALUCINACAO', 'CNPJ invalido (<14 digitos)'

    nome_upper = str(nome or "").upper().strip()
    if re.match(r'^CLIENTE\s*\d+', nome_upper):
        return 'ALUCINACAO', 'Nome padrao CLIENTE+numero'

    vendedor_upper = str(vendedor or "").upper().strip()
    vendedor_normalized = re.sub(r'\s+', ' ', vendedor_upper)
    if vendedor_normalized in [v.upper() for v in VENDEDORES_FICTICIOS]:
        return 'ALUCINACAO', f'Vendedor ficticio: {vendedor_normalized}'

    # --- SINTETICO checks ---
    nota_str = str(nota or "").strip()
    nota_lower = nota_str.lower()

    for padrao in NOTAS_SINTETICAS_PADROES:
        if padrao in nota_lower:
            return 'SINTETICO', f'Nota generica: {padrao}'

    if 0 < len(nota_str) < 15:
        return 'SINTETICO', 'Nota curta (<15 chars)'

    # --- REAL: passa todos os checks ---
    return 'REAL', 'Nota contextual com detalhes especificos'


def make_dedup_key(data, cnpj, resultado):
    """
    Chave composta DATA(YYYY-MM-DD) + CNPJ(14-dig) + RESULTADO(upper,trimmed).
    Separados por '|'.

    Args:
        data: date object ou string YYYY-MM-DD
        cnpj: CNPJ ja normalizado (14 digitos) ou bruto
        resultado: RESULTADO do atendimento
    """
    if isinstance(data, date):
        data_str = data.strftime('%Y-%m-%d')
    else:
        data_str = str(data).strip()[:10]

    cnpj_str = normalize_cnpj(cnpj)
    resultado_str = str(resultado or "").strip().upper()

    return f"{data_str}|{cnpj_str}|{resultado_str}"


def subtract_business_days(data_base, dias):
    """
    Calcula data anterior em dias uteis (seg-sex).
    Espelho de dia_util() para calcular datas no passado.

    Args:
        data_base: date object
        dias: numero de dias uteis para subtrair
    """
    if dias == 0:
        return data_base
    atual = data_base
    contados = 0
    while contados < dias:
        atual -= timedelta(days=1)
        if atual.weekday() < 5:
            contados += 1
    return atual


def generate_channels():
    """
    Gerar combinacao WhatsApp/Ligacao/Lig.Atendida com probabilidades reais.
    - WhatsApp: 98.3% SIM
    - Ligacao: 49.7% SIM
    - Ligacao Atendida: 20% das ligacoes (80% nao atendidas)

    Returns:
        tuple (whatsapp, ligacao, lig_atendida) com valores 'SIM'/'NAO'/'N/A'
    """
    whatsapp = 'SIM' if random.random() < 0.983 else 'NAO'
    ligacao = 'SIM' if random.random() < 0.497 else 'NAO'

    if ligacao == 'SIM':
        lig_atendida = 'SIM' if random.random() < 0.20 else 'NAO'
    else:
        lig_atendida = 'N/A'

    return whatsapp, ligacao, lig_atendida


def make_log_record(data, cnpj, consultor, resultado, nota,
                    whatsapp='SIM', ligacao='NAO', lig_atendida='N/A',
                    tipo_acao='ATIVO', motivo='', mercos='',
                    nome='', uf='', rede='', situacao='',
                    origem_dado='REAL', source='CONTROLE_FUNIL'):
    """
    Cria dict com as 20 colunas LOG + campos extras ORIGEM_DADO e SOURCE.

    Usa motor_de_regras() para campos derivados (follow-up, fase, estagio, tipo_contato).
    NUNCA inclui campos financeiros (Two-Base Architecture).

    Args:
        data: date ou datetime
        cnpj: CNPJ (sera normalizado)
        consultor: Nome do consultor (sera normalizado)
        resultado: RESULTADO do atendimento
        nota: NOTA DO DIA
        whatsapp/ligacao/lig_atendida: Canais de contato
        tipo_acao: ATIVO ou RECEPTIVO
        motivo: Motivo (quando nao houve venda)
        mercos: MERCOS ATUALIZADO (SIM/NAO)
        nome: NOME FANTASIA
        uf: Estado
        rede: REDE/REGIONAL
        situacao: SITUACAO do cliente
        origem_dado: REAL ou SINTETICO
        source: CONTROLE_FUNIL, DESKRIO, SINTETICO
    """
    # Normalizar CNPJ
    cnpj_norm = normalize_cnpj(cnpj)

    # Normalizar consultor
    consultor_norm = normalize_consultor(consultor)

    # Normalizar resultado (sem acento para LOG, com acento para motor)
    resultado_sem, resultado_motor = normalize_resultado(resultado)

    # Rodar motor de regras para campos derivados
    try:
        regras = motor_de_regras(situacao or "", resultado_motor)
    except Exception:
        regras = {}

    # Calcular follow-up
    follow_up_dias = regras.get('follow_up_dias', 0)
    if follow_up_dias > 0 and isinstance(data, date):
        follow_up = dia_util(data, follow_up_dias)
        follow_up_str = follow_up.strftime('%Y-%m-%d')
    else:
        follow_up_str = ""

    # Fase (sem acento — P8)
    fase_raw = regras.get('fase', '')
    fase = _remover_acentos(fase_raw)

    # Tipo do contato (sem acento)
    tipo_contato_raw = regras.get('tipo_contato', '')
    tipo_contato = _remover_acentos(tipo_contato_raw)

    # Acao futura (sem acento)
    acao_raw = regras.get('acao_futura', '')
    acao = _remover_acentos(acao_raw)

    # Tentativa
    tentativa = regras.get('tentativa', '') or ''

    # Ligacao atendida logica
    if ligacao != 'SIM':
        lig_atendida = 'N/A'

    # Converter data para string
    if isinstance(data, date):
        data_str = data.strftime('%Y-%m-%d')
    else:
        data_str = str(data).strip()[:10] if data else ""

    record = {
        'DATA': data_str,
        'CONSULTOR': consultor_norm,
        'NOME FANTASIA': str(nome or "").strip(),
        'CNPJ': cnpj_norm,
        'UF': str(uf or "").strip().upper(),
        'REDE/REGIONAL': str(rede or "").strip().upper() if rede else "DEMAIS CLIENTES",
        'SITUACAO': str(situacao or "").strip().upper(),
        'WHATSAPP': whatsapp,
        'LIGACAO': ligacao,
        'LIGACAO ATENDIDA': lig_atendida,
        'TIPO ACAO': tipo_acao,
        'TIPO DO CONTATO': tipo_contato,
        'RESULTADO': resultado_sem,
        'MOTIVO': str(motivo or "").strip().upper(),
        'FOLLOW-UP': follow_up_str,
        'ACAO': acao,
        'MERCOS ATUALIZADO': str(mercos or "").strip().upper(),
        'FASE': fase,
        'TENTATIVA': str(tentativa),
        'NOTA DO DIA': str(nota or "").strip(),
        # Metadados (nao fazem parte das 20 colunas LOG, mas necessarios para pipeline)
        'ORIGEM_DADO': origem_dado,
        'SOURCE': source,
    }

    return record


def _remover_acentos(texto):
    """Remove acentos comuns do portugues (P8 VITAO SEM ACENTO)."""
    if not texto:
        return ""
    mapa = {
        'Á': 'A', 'À': 'A', 'Ã': 'A', 'Â': 'A',
        'É': 'E', 'Ê': 'E',
        'Í': 'I',
        'Ó': 'O', 'Ô': 'O', 'Õ': 'O',
        'Ú': 'U', 'Ü': 'U',
        'Ç': 'C',
        'á': 'a', 'à': 'a', 'ã': 'a', 'â': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ü': 'u',
        'ç': 'c',
    }
    result = []
    for ch in str(texto):
        result.append(mapa.get(ch, ch))
    return ''.join(result)


# =====================================================================
# SELF-TEST
# =====================================================================

if __name__ == "__main__":
    print("=== Phase 04 _helpers.py — Self Test ===\n")

    # normalize_cnpj
    assert normalize_cnpj('32.387.943/0001-05') == '32387943000105'
    assert normalize_cnpj('123') == '00000000000123'
    assert normalize_cnpj(None) == ''
    print("  normalize_cnpj: PASS")

    # normalize_consultor
    assert normalize_consultor('CENTRAL - DAIANE') == 'DAIANE STAVICKI'
    assert normalize_consultor('Julio  Gadret') == 'JULIO GADRET'
    assert normalize_consultor('HEMANUELE DITZEL (MANU)') == 'MANU DITZEL'
    assert normalize_consultor('Manu Ditzel') == 'MANU DITZEL'
    assert normalize_consultor('Larissa Padilha') == 'LARISSA PADILHA'
    print("  normalize_consultor: PASS")

    # classify_record
    assert classify_record('123', 'CLIENTE 001', 'JOAO SILVA', 'nota')[0] == 'ALUCINACAO'
    assert classify_record('32387943000105', 'Loja', 'MANU', 'primeiro contato com prospect')[0] == 'SINTETICO'
    assert classify_record('32387943000105', 'Loja', 'MANU', 'Cliente pediu orcamento de 500kg de granola')[0] == 'REAL'
    print("  classify_record: PASS")

    # make_dedup_key
    assert make_dedup_key('2025-06-15', '32387943000105', 'VENDA / PEDIDO') == '2025-06-15|32387943000105|VENDA / PEDIDO'
    assert make_dedup_key(date(2025, 6, 15), '32387943000105', 'VENDA / PEDIDO') == '2025-06-15|32387943000105|VENDA / PEDIDO'
    print("  make_dedup_key: PASS")

    # LOG_COLUMNS
    assert len(LOG_COLUMNS) == 20
    assert LOG_COLUMNS[0] == 'DATA'
    assert LOG_COLUMNS[-1] == 'NOTA DO DIA'
    print("  LOG_COLUMNS: PASS (20 cols)")

    # subtract_business_days
    d = date(2025, 6, 16)  # Monday
    assert subtract_business_days(d, 1) == date(2025, 6, 13)  # Friday
    assert subtract_business_days(d, 5) == date(2025, 6, 9)   # Previous Monday
    print("  subtract_business_days: PASS")

    # generate_channels
    random.seed(42)
    w, l, la = generate_channels()
    assert w in ('SIM', 'NAO')
    assert l in ('SIM', 'NAO')
    assert la in ('SIM', 'NAO', 'N/A')
    print("  generate_channels: PASS")

    # make_log_record
    rec = make_log_record(
        data=date(2025, 6, 15),
        cnpj='32387943000105',
        consultor='Manu Ditzel',
        resultado='VENDA / PEDIDO',
        nota='Fechou pedido 500kg granola',
        nome='Loja Teste',
        uf='PR',
        situacao='ATIVO',
    )
    assert rec['CNPJ'] == '32387943000105'
    assert rec['CONSULTOR'] == 'MANU DITZEL'
    assert rec['RESULTADO'] == 'VENDA / PEDIDO'
    assert 'VALOR' not in rec
    assert 'PEDIDO' not in rec or rec.get('PEDIDO') is None
    assert len([k for k in rec if k in LOG_COLUMNS]) == 20
    print("  make_log_record: PASS")

    # normalize_resultado
    sem, com = normalize_resultado('ORÇAMENTO')
    assert sem == 'ORCAMENTO'
    assert com == 'ORÇAMENTO'
    sem2, com2 = normalize_resultado('NAO ATENDE')
    assert sem2 == 'NAO ATENDE'
    assert com2 == 'NÃO ATENDE'
    print("  normalize_resultado: PASS")

    print("\nALL HELPER TESTS PASSED")
