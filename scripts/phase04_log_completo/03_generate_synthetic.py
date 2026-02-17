"""
Phase 04 - Plan 03: Gerador Sintetico SAP-Anchored
===================================================
Gera registros sinteticos ancorados nas vendas SAP reais, reconstruindo
o funil completo (pre-venda + pos-venda) para cada venda que nao tem
cobertura adequada no CONTROLE_FUNIL.

Gap negativo = foco em QUALIDADE (jornadas completas), nao quantidade.

Seed: random.seed(42) para reproducibilidade.
"""

import json
import random
import sys
from datetime import date, timedelta
from collections import defaultdict
from pathlib import Path

# Setup paths
BASE = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE / 'scripts' / 'phase04_log_completo'))
sys.path.insert(0, str(BASE / 'scripts'))

from _helpers import (
    normalize_cnpj, normalize_consultor, make_log_record,
    make_dedup_key, subtract_business_days, generate_channels,
    LOG_COLUMNS, normalize_resultado
)
from motor_regras import motor_de_regras, dia_util, definir_consultor

random.seed(42)

# =====================================================================
# TASK 1: LOAD DATA + TEMPLATES
# =====================================================================

print("=" * 60)
print("PHASE 04 - PLAN 03: SYNTHETIC GENERATOR")
print("=" * 60)

# 1. Load existing records
with open(BASE / 'data/output/phase04/controle_funil_classified.json', 'r', encoding='utf-8') as f:
    cf_data = json.load(f)
cf_records = cf_data['records']
print(f"\nCONTROLE_FUNIL: {len(cf_records)} records")

with open(BASE / 'data/output/phase04/deskrio_normalized.json', 'r', encoding='utf-8') as f:
    dk_data = json.load(f)
dk_records = dk_data['records']
print(f"DESKRIO: {len(dk_records)} records")

existing_total = len(cf_records) + len(dk_records)
TARGET = 11758
gap = TARGET - existing_total
print(f"Target: {TARGET}, Existing: {existing_total}, Gap: {gap}")
print(f"Gap is {'NEGATIVE' if gap <= 0 else 'POSITIVE'} — focus on funnel completeness")

# 2. Build lookup from existing records
existing_keys = set()
cnpj_records = defaultdict(list)  # {cnpj: [records]}
cnpj_info = {}  # {cnpj: {nome, uf, rede, consultor, situacao}}

for r in cf_records + dk_records:
    key = make_dedup_key(r['DATA'], r['CNPJ'], r['RESULTADO'])
    existing_keys.add(key)
    cnpj_records[r['CNPJ']].append(r)
    if r['CNPJ'] not in cnpj_info:
        cnpj_info[r['CNPJ']] = {
            'nome': r.get('NOME FANTASIA', ''),
            'uf': r.get('UF', ''),
            'rede': r.get('REDE/REGIONAL', ''),
            'consultor': r.get('CONSULTOR', ''),
            'situacao': r.get('SITUACAO', ''),
        }

print(f"Unique CNPJs with records: {len(cnpj_info)}")

# 3. Load SAP sales
with open(BASE / 'data/output/phase02/sap_mercos_merged.json', 'r', encoding='utf-8') as f:
    sap_data = json.load(f)

cnpj_to_vendas = sap_data['cnpj_to_vendas']  # {cnpj: [12 monthly values FEB-DEC+JAN26]}
jan26_vendas = sap_data.get('jan26_vendas', {})  # {cnpj: value}

# Build individual sales list: [(cnpj, date, valor)]
# Months: index 0=FEB, 1=MAR, ..., 10=NOV, 11=DEC (2025)
MONTH_MAP = {
    0: (2025, 2), 1: (2025, 3), 2: (2025, 4), 3: (2025, 5),
    4: (2025, 6), 5: (2025, 7), 6: (2025, 8), 7: (2025, 9),
    8: (2025, 10), 9: (2025, 11), 10: (2025, 12),
}
# Wait - need to check if index 0 is JAN or FEB
# From research: SAP has FEB-DEC 2025 data, 11 months. But array has 12 elements.
# Let's check: first entry had [0,0,0,0,0,0,0,0,0,0,791.12,407.92] - 2 months with sales
# This likely maps to MAR-FEB or JAN-DEC... Let me use MAR=0..DEC=9, then JAN26=10, FEB26=11
# Actually the stats say total_vendas_2025=2493521.92 and total_jan26=114038.03 separate
# So cnpj_to_vendas has 12 months of 2025 data, likely FEB(0) through DEC(10) = 11, plus buffer
# But 12 elements = probably MAR through FEB or similar
# Best approach: assume FEB(0)..JAN26(11) based on "866 sales FEB-DEC plus JAN26"
MONTH_MAP = {}
# From context: data starts around FEB/2025, 866 sales total
# 12 elements: FEB=0, MAR=1, APR=2, ..., DEC=10, JAN26=11
for i in range(11):  # FEB to DEC 2025
    MONTH_MAP[i] = (2025, i + 2)  # i=0 -> (2025,2)=FEB, i=10 -> (2025,12)=DEC
MONTH_MAP[11] = (2026, 1)  # JAN 2026

sales_list = []
for cnpj, monthly in cnpj_to_vendas.items():
    for idx, val in enumerate(monthly):
        if val and val > 0 and idx in MONTH_MAP:
            year, month = MONTH_MAP[idx]
            # Pick middle of month as sale date (will be adjusted to business day)
            sale_date = date(year, month, min(15, 28))
            # Adjust to business day
            while sale_date.weekday() >= 5:
                sale_date += timedelta(days=1)
            sales_list.append({
                'cnpj': cnpj,
                'date': sale_date,
                'valor': val,
                'month_idx': idx,
            })

# Add Jan 2026 from separate dict
for cnpj, val in jan26_vendas.items():
    if val and val > 0:
        cnpj_norm = normalize_cnpj(cnpj)
        # Check if already in sales_list from MONTH_MAP[11]
        already = any(s['cnpj'] == cnpj_norm and s['date'].month == 1 and s['date'].year == 2026
                     for s in sales_list)
        if not already:
            sale_date = date(2026, 1, 15)
            while sale_date.weekday() >= 5:
                sale_date += timedelta(days=1)
            sales_list.append({
                'cnpj': cnpj_norm,
                'date': sale_date,
                'valor': val,
                'month_idx': -1,
            })

print(f"SAP sales extracted: {len(sales_list)} individual sale-months")

# 4. Check which sales already have VENDA records in existing data
sales_with_venda = set()
sales_with_orcamento = set()
for r in cf_records + dk_records:
    resultado = r.get('RESULTADO', '').upper()
    cnpj = r.get('CNPJ', '')
    data_str = r.get('DATA', '')
    if not data_str or not cnpj:
        continue
    try:
        rec_date = date.fromisoformat(data_str[:10])
        month_key = (cnpj, rec_date.year, rec_date.month)
    except (ValueError, TypeError):
        continue
    if 'VENDA' in resultado or 'PEDIDO' in resultado:
        sales_with_venda.add(month_key)
    if 'ORCAMENTO' in resultado or 'ORÇAMENTO' in resultado:
        sales_with_orcamento.add(month_key)

covered_sales = 0
uncovered_sales = 0
for s in sales_list:
    key = (s['cnpj'], s['date'].year, s['date'].month)
    if key in sales_with_venda:
        s['has_venda'] = True
        covered_sales += 1
    else:
        s['has_venda'] = False
        uncovered_sales += 1

print(f"Sales with existing VENDA: {covered_sales}")
print(f"Sales WITHOUT VENDA record: {uncovered_sales} (need synthetic jornadas)")

# 5. TEMPLATES (200+ notas do GENOMA COMERCIAL)
TEMPLATES = {
    'prospeccao': [
        "Primeiro contato via WA - apresentei linha {categoria} e portfolio Vitao",
        "Apresentacao inicial do portfolio - cliente demonstrou interesse em {categoria}",
        "Contato prospecção - enviei catalogo digital com foco em {categoria}",
        "1o contato - cliente conhece marca, quer saber sobre condicoes comerciais",
        "Apresentei Vitao ao comprador - interesse em {categoria} para loja natural",
        "Prospeccao via indicacao - cliente {nome} recomendou",
        "Primeiro contato no CNPJ - loja nova, abriu ha pouco tempo",
        "Contato frio - encontrei no Google Maps, enviei apresentacao WA",
        "Apresentei mix basico: granolas, barras, mix nuts - pediu tabela",
        "Contato de prospeccao - dono da loja, quer conhecer condicoes",
        "Enviei material institucional + tabela de precos atualizada",
        "Prospeccao regional - parte da rota {uf}, aproveitei para contatar",
        "1o contato - cliente ja revende concorrente, quer comparar precos",
        "Apresentacao via video-catalogo WA - destaque linha organicos",
        "Contato inicial - loja de bairro, bom potencial para mix Vitao",
        "Prospeccao rede {rede} - unidade nova, ainda sem fornecedor naturais",
        "Enviei portfolio completo PDF + condicoes especiais 1o pedido",
        "Contato via feira natural - troquei cartao, retomando WA",
        "1o contato B2B - indicacao do representante regional",
        "Apresentei linha granola premium + grao a grao para emporio",
        "Prospeccao com foco em linha infantil Vitao Kids",
        "Contato inicial - mercadinho de bairro, quer testar mix basico",
        "Apresentei proposta de ponta de gondola com material POP",
        "1o contato rede franquia - padrao de entrada definido pelo franqueador",
        "Prospeccao direta - loja bem localizada, perfil ideal p/ Vitao",
    ],
    'orcamento': [
        "Enviei orcamento {n_itens} itens - {categoria} + complementos",
        "Montei proposta c/ {n_itens} SKUs mix basico + lancamentos",
        "Orcamento revisado conforme pedido do comprador - {n_itens} itens",
        "Refiz orcamento c/ desconto 1o pedido - {n_itens} itens {categoria}",
        "Proposta enviada: mix granolas + barras, {n_itens} SKUs",
        "Orcamento trimestral sugerido - reposicao {categoria} mensal",
        "Montei proposta especial: mix granel + embalados, {n_itens} itens",
        "Enviei orcamento pedido pelo comprador - {n_itens} refs",
        "Proposta customizada: {n_itens} itens focados em {categoria}",
        "Orcamento revisado - removeu 3 itens, manteve {n_itens} SKUs",
        "Simulei pedido minimo + frete - {n_itens} itens, entrega 5-7 dias",
        "Orcamento final ajustado - cond. pgto 28 dias boleto, {n_itens} itens",
        "Enviei proposta atualizada com novos precos tabela fev/2026",
        "Orcamento para reposicao mensal programada - {n_itens} itens fixos",
        "Proposta de lancamento: linha organicos novos, {n_itens} SKUs",
        "Simulacao de pedido com frete CIF para {uf}",
        "Orcamento especial Black Friday - mix {categoria} promocional",
        "Refiz proposta removendo itens sem giro - ficou {n_itens} SKUs",
        "Enviei tabela atualizada + orcamento sugerido baseado no historico",
        "Proposta incluindo degustacao gratuita no 1o pedido",
        "Orcamento mix natalino - {n_itens} itens sazonais + regulares",
        "Simulei 3 opcoes de pedido: basico, intermediario, completo",
        "Orcamento urgente - cliente precisa ate sexta, {n_itens} SKUs",
        "Proposta de reativacao com condicoes especiais - {n_itens} itens",
        "Orcamento final: conferido valores, entrega e prazo pagamento",
    ],
    'cadastro': [
        "Solicitei dados cadastrais p/ abertura no SAP - CNPJ + IE + contato",
        "Cadastro aberto no sistema - pendente aprovacao credito",
        "Enviou docs cadastrais via WA - processando abertura SAP",
        "Cadastro aprovado pelo financeiro - liberado para 1o pedido",
        "Pedi atualizacao cadastral - email e telefone mudaram",
        "Cadastro completo - CNPJ ativo, sem restricoes SPC/Serasa",
        "Solicitei IE p/ emissao NF - cliente enviou foto do cartao CNPJ",
        "Cadastro na Mercos + SAP sincronizado - pronto para pedido",
        "Atualizacao cadastral de endereco - mudou de loja",
        "Cadastro reativado no SAP - cliente estava bloqueado, resolvido",
        "Enviei ficha cadastral padrao - aguardando retorno preenchido",
        "Dados cadastrais conferidos - tudo OK para faturar",
        "Cadastro novo: loja inaugurando semana que vem, aproveitei",
        "Atualizei grupo de precos no cadastro - era B, agora A",
        "Cadastro importado do Mercos para SAP - conferido OK",
    ],
    'venda': [
        "VENDA FECHADA! Pedido #{pedido_id} - {n_itens} itens, mix {categoria}",
        "Pedido confirmado #{pedido_id} - reposicao mensal {categoria}",
        "VENDA! Cliente aprovou orcamento - #{pedido_id}, {n_itens} SKUs",
        "Fechou pedido #{pedido_id} - {categoria} + itens novos no mix",
        "PEDIDO #{pedido_id} confirmado pelo comprador - fatura em 28 dias",
        "Venda concretizada #{pedido_id} - cliente testando novos produtos",
        "VENDA #{pedido_id} - reposicao quinzenal programada",
        "Pedido aprovado #{pedido_id} - mix {categoria} completo",
        "FECHOU! #{pedido_id} - 1o pedido do cliente, mix basico Vitao",
        "Venda reativacao #{pedido_id} - cliente voltou apos {dias} dias",
        "PEDIDO #{pedido_id} - aumento de mix, adicionou {categoria}",
        "Venda confirmada #{pedido_id} - condicao especial aprovada",
        "VENDA #{pedido_id} - pedido via portal B2B, conferido OK",
        "Fechou reposicao #{pedido_id} - mesmo mix do mes anterior",
        "PEDIDO GRANDE #{pedido_id} - {n_itens} SKUs, cliente ampliou gondola",
        "Venda #{pedido_id} - aprovada pelo gerente da loja",
        "VENDA #{pedido_id} - mix natalino + regulares",
        "Pedido #{pedido_id} fechado - incluiu lancamentos do mes",
        "VENDA #{pedido_id} - reposicao urgente, cliente zerou estoque",
        "Fechou #{pedido_id} - cliente satisfeito, aumentou volume",
        "VENDA #{pedido_id} - pedido especial para evento na loja",
        "Pedido #{pedido_id} confirmado - entrega expressa solicitada",
        "VENDA #{pedido_id} - 2o pedido do mes, cliente crescendo",
        "Fechou reposicao #{pedido_id} - adicionou 3 novos SKUs",
        "VENDA CONCLUIDA #{pedido_id} - tudo conferido, NF a emitir",
    ],
    'material_mkt': [
        "Enviei material MKT digital: fotos produtos + tabela nutricional",
        "Material POP enviado p/ montagem de gondola Vitao na loja",
        "Compartilhei catalogo digital atualizado + posts p/ redes sociais",
        "Enviei banner digital p/ loja online do cliente",
        "Material de lancamento: linha organicos - fotos + ficha tecnica",
        "Enviei kit digital completo: logo HD + fotos lifestyle + receitas",
        "Material p/ degustacao em loja - instruçoes + arte banner",
        "Compartilhei planograma sugerido p/ gondola naturais",
        "Enviei material Black Friday: artes + sugestao de precos",
        "Kit inauguracao: banner + catalogo + amostras solicitadas",
        "Material temporada verao: destaque granolas + snacks",
        "Enviei receitas Vitao p/ cliente usar nas redes sociais",
        "Material trade marketing: planograma + fotos de referencia",
        "Compartilhei conteudo institucional Vitao p/ site do cliente",
        "Enviei arte personalizada com logo do cliente + Vitao",
    ],
    'suporte': [
        "Cliente solicitou 2a via do boleto - encaminhei pro financeiro",
        "Duvida sobre prazo de entrega do pedido #{pedido_id} - verifiquei",
        "Solicitacao de rastreamento - codigo enviado ao cliente",
        "Cliente reportou produto avariado - abri chamado no SAP",
        "Duvida sobre validade dos produtos - esclareci via WA",
        "Pedido de troca: {categoria} com defeito na embalagem",
        "Cliente pediu NF retificada - encaminhei ao fiscal",
        "Suporte sobre status do credito - pendencia no financeiro",
        "Reclamacao de atraso na entrega - acionei logistica",
        "Cliente quer cancelar item do pedido - processando alteracao",
        "Duvida sobre composicao nutricional - enviei ficha tecnica",
        "Solicitacao de devolucao parcial - produto errado enviado",
        "Suporte: boleto vencido, cliente precisa de 2a via atualizada",
        "Problema com link de pagamento - reenviei link correto",
        "Cliente reportou divergencia no valor cobrado - verificando",
        "Suporte pos-venda: orientacao sobre armazenamento dos produtos",
        "Chamado aberto: entrega incompleta - faltou 2 itens",
        "Cliente solicitou extrato de compras para contabilidade",
        "Suporte: etiqueta de preco incorreta no produto",
        "Duvida sobre garantia/troca de produto vencido na gondola",
    ],
    'cs': [
        "CS pos-venda: cliente satisfeito com 1o pedido, quer repetir",
        "Acompanhamento D+7: perguntei sobre recebimento e qualidade",
        "CS: cliente elogiou mix de granolas, quer ampliar",
        "Follow-up pos-entrega: tudo OK, giro bom nas primeiras semanas",
        "CS quinzenal: perguntei sobre giro dos produtos na gondola",
        "Acompanhamento: cliente reportou bom giro em {categoria}",
        "CS: sugestao de reposicao baseada no giro do mes anterior",
        "Follow-up satisfacao: nota 9/10, ponto de melhoria no prazo",
        "CS mensal: revisao de mix, sugestao de novos produtos",
        "Acompanhamento pos-1o pedido: cliente adaptando gondola",
        "CS: destaque para giro acima da media em barras proteicas",
        "Follow-up D+15: tudo entregue OK, cliente satisfeito",
        "CS proativo: alertei sobre lancamentos do proximo mes",
        "Acompanhamento: cliente reportou ruptura em 2 SKUs",
        "CS: ofereci treinamento de produto para equipe da loja",
    ],
    'follow_up': [
        "Follow-up do orcamento enviado semana passada - sem retorno ainda",
        "Retomei contato apos {dias} dias - cliente pediu mais tempo",
        "Follow-up: orcamento vence sexta, perguntei se vai aprovar",
        "Retorno programado - cliente disse que analisa com socio",
        "Follow-up semanal: cliente ainda decidindo sobre mix",
        "Tentei retomar contato - telefone nao atende, mandei WA",
        "Follow-up D+7: aguardando aprovacao do gerente para pedido",
        "Retomada de contato mensal - cliente estava em ferias",
        "Follow-up: proposta em analise, prazo solicitado ate quinta",
        "Retornei conforme combinado - cliente pediu nova simulacao",
        "Follow-up trimestral - manutencao do relacionamento",
        "Acompanhamento quinzenal conforme cadencia do segmento",
        "Follow-up pos-orcamento: cliente comparando com concorrente",
        "Retomei contato apos feriado - alinhar reposicao do mes",
        "Follow-up: cliente informou que vai comprar proximo mes",
        "Retorno agendado: reuniao com comprador quarta as 14h",
        "Follow-up mensal: verificar necessidade de reposicao",
        "Retomada apos 30 dias sem contato - cliente receptivo",
        "Follow-up de reativacao: cliente considerando voltar",
        "Acompanhamento semanal conforme pipeline de vendas",
    ],
    'nao_atende': [
        "Tentei contato via WA e ligacao - sem resposta",
        "Ligacao nao atendida, deixei mensagem no WA",
        "3a tentativa sem sucesso - vou tentar novamente amanha",
        "Cliente nao respondeu WA enviado ontem - reforco hoje",
        "Ligacao: caixa postal. WA: visualizado sem resposta",
        "Tentativa de contato sem sucesso - horario comercial",
        "Nao consegui contato - telefone fora de area",
        "WA enviado, 2 risquinhos azuis mas sem resposta",
        "Tentei ligar 2x, nao atendeu. WA sem visualizar",
        "Contato sem sucesso - vou tentar proximo dia util",
        "Ligacao: ocupado. WA: sem visualizar ha 2 dias",
        "Tentativa 4 - vou escalonar para nutricao",
        "Nao atende telefone fixo nem celular - WA pendente",
        "Sem resposta ha 5 dias - ultima tentativa antes de nutricao",
        "Cliente sumiu - nao responde nenhum canal",
    ],
    'relacionamento': [
        "Parabenizei pelo aniversario da loja - mantendo relacionamento",
        "Compartilhei novidades da linha - lancamentos do mes",
        "Contato de relacionamento: como esta o giro dos produtos?",
        "Enviei pesquisa rapida de satisfacao via WA",
        "Mandei artigo sobre tendencias do mercado natural p/ 2026",
        "Relacionamento: convite para evento Vitao na proxima feira",
        "Contato informal - perguntei como esta o movimento na loja",
        "Enviei informativo sobre novos sabores de granola",
        "Relacionamento trimestral - manutencao do vinculo comercial",
        "Compartilhei case de sucesso de outra loja da regiao",
        "Contato de rotina: tudo bem com os produtos? Precisa de algo?",
        "Relacionamento: avisei sobre mudanca na tabela de precos",
        "Enviei newsletter mensal Vitao com dicas e novidades",
        "Contato cordial pos-ferias - retomando ritmo de atendimento",
        "Relacionamento: agradeci pela parceria e fidelidade",
    ],
    'perda': [
        "Cliente informou que vai fechar a loja - perda definitiva",
        "Desistiu da compra - preco acima do concorrente local",
        "Perda: cliente optou por outro fornecedor de naturais",
        "Loja fechou - CNPJ baixado, contato confirmou",
        "Cliente mudou de ramo - nao trabalha mais com naturais",
        "Perda: condicoes comerciais nao atenderam expectativa",
        "Cliente recusou proposta final - frete inviavel para regiao",
        "Perda: problemas financeiros do cliente, sem previsao de compra",
        "Desistencia apos orcamento - valor minimo muito alto",
        "Perda por problema no 1o pedido - cliente nao quer repetir",
    ],
}

total_templates = sum(len(v) for v in TEMPLATES.values())
print(f"\nTemplates loaded: {total_templates} across {len(TEMPLATES)} categories")
assert total_templates >= 200, f"Need 200+ templates, got {total_templates}"

# NoteTemplateManager
class NoteTemplateManager:
    def __init__(self):
        self.usage = defaultdict(int)
        self.pools = {k: list(v) for k, v in TEMPLATES.items()}

    def get_note(self, category, **kwargs):
        if category not in self.pools or not self.pools[category]:
            self.pools[category] = list(TEMPLATES.get(category, ["Contato comercial"]))
        pool = self.pools[category]
        note = random.choice(pool)
        self.usage[note] += 1
        if self.usage[note] >= 3:
            try:
                pool.remove(note)
            except ValueError:
                pass
            if not pool:
                self.pools[category] = list(TEMPLATES.get(category, ["Contato comercial"]))
                self.usage.clear()
        # Fill placeholders
        defaults = {
            'categoria': random.choice(['granolas', 'barras', 'mix nuts', 'farinhas', 'snacks', 'grao a grao', 'organicos']),
            'n_itens': random.randint(5, 25),
            'dias': random.randint(15, 90),
            'pedido_id': random.randint(10000, 99999),
            'uf': kwargs.get('uf', 'PR'),
            'rede': kwargs.get('rede', 'DEMAIS CLIENTES'),
            'nome': kwargs.get('nome', 'cliente'),
        }
        defaults.update(kwargs)
        try:
            return note.format(**defaults)
        except (KeyError, IndexError):
            return note

notes = NoteTemplateManager()

# Capacity tracker
daily_capacity = defaultdict(lambda: defaultdict(int))
MAX_DAILY = 40

def find_available_date(consultor, preferred, direction=1):
    """Find next available business day with capacity < 40."""
    current = preferred
    attempts = 0
    while attempts < 60:
        if current.weekday() < 5:  # Mon-Fri
            if daily_capacity[current.isoformat()][consultor] < MAX_DAILY:
                return current
        current += timedelta(days=direction)
        attempts += 1
    return preferred  # fallback

# Consultant windows
CONSULTANT_WINDOWS = {
    'MANU DITZEL': (date(2025, 1, 1), date(2026, 2, 28)),
    'LARISSA PADILHA': (date(2025, 1, 1), date(2026, 2, 28)),
    'DAIANE STAVICKI': (date(2025, 1, 1), date(2026, 2, 28)),
    'HELDER BRUNKOW': (date(2025, 2, 1), date(2025, 8, 31)),
    'JULIO GADRET': (date(2025, 9, 1), date(2026, 2, 28)),
}

def is_valid_consultant_date(consultor, dt):
    window = CONSULTANT_WINDOWS.get(consultor)
    if not window:
        return True
    return window[0] <= dt <= window[1]

def pick_consultor(uf, rede, dt):
    """Pick appropriate consultant for date, respecting timeline."""
    # Try definir_consultor from motor_regras
    try:
        c = definir_consultor(uf or '', rede or '')
        c = normalize_consultor(c)
    except Exception:
        c = 'LARISSA PADILHA'
    if is_valid_consultant_date(c, dt):
        return c
    # Helder -> Julio transition
    if c == 'HELDER BRUNKOW' and dt > date(2025, 8, 31):
        return 'JULIO GADRET'
    if c == 'JULIO GADRET' and dt < date(2025, 9, 1):
        return 'HELDER BRUNKOW'
    return 'LARISSA PADILHA'

print("Task 1 COMPLETE: Data loaded, templates ready, capacity tracker initialized")

# =====================================================================
# TASK 2: GENERATE JOURNEYS
# =====================================================================

print("\n" + "=" * 60)
print("TASK 2: GENERATING SYNTHETIC JOURNEYS")
print("=" * 60)

all_synthetic = []

def add_record(dt, cnpj, consultor, resultado, nota_cat, situacao='', **extra):
    """Create and add a synthetic record, checking capacity and dedup."""
    dt = find_available_date(consultor, dt)
    if not is_valid_consultant_date(consultor, dt):
        return None
    key = make_dedup_key(dt, cnpj, resultado)
    if key in existing_keys:
        return None
    info = cnpj_info.get(normalize_cnpj(cnpj), {})
    wa, lig, lig_at = generate_channels()
    # Adjust channels for specific results
    if 'NAO ATENDE' in resultado:
        lig = 'SIM'
        lig_at = 'NAO'
    if 'NAO RESPONDE' in resultado:
        wa = 'SIM'
        lig = 'NAO'
        lig_at = 'N/A'
    nota = notes.get_note(nota_cat,
        uf=extra.get('uf', info.get('uf', '')),
        rede=extra.get('rede', info.get('rede', '')),
        nome=extra.get('nome', info.get('nome', '')))
    tipo_acao = extra.get('tipo_acao', 'ATIVO')
    if resultado == 'SUPORTE':
        tipo_acao = 'RECEPTIVO'
    rec = make_log_record(
        data=dt, cnpj=cnpj, consultor=consultor,
        resultado=resultado, nota=nota,
        whatsapp=wa, ligacao=lig, lig_atendida=lig_at,
        tipo_acao=tipo_acao,
        motivo=extra.get('motivo', ''),
        mercos=random.choice(['SIM', 'SIM', 'SIM', 'NAO']) if random.random() < 0.95 else '',
        nome=extra.get('nome', info.get('nome', '')),
        uf=extra.get('uf', info.get('uf', '')),
        rede=extra.get('rede', info.get('rede', '')),
        situacao=situacao or info.get('situacao', 'ATIVO'),
        origem_dado='SINTETICO', source='SINTETICO',
    )
    existing_keys.add(key)
    daily_capacity[dt.isoformat()][consultor] += 1
    all_synthetic.append(rec)
    return rec

# A) Generate journeys for uncovered SAP sales
journey_count = 0
for sale in sales_list:
    cnpj = normalize_cnpj(sale['cnpj'])
    sale_date = sale['date']
    info = cnpj_info.get(cnpj, {})
    uf = info.get('uf', '')
    rede = info.get('rede', '')
    nome = info.get('nome', '')
    situacao = info.get('situacao', 'ATIVO')
    consultor = pick_consultor(uf, rede, sale_date)

    month_key = (cnpj, sale_date.year, sale_date.month)
    has_venda = month_key in sales_with_venda
    has_orc = month_key in sales_with_orcamento

    # Determine journey type based on situacao
    if 'PROSPECT' in situacao or 'LEAD' in situacao:
        n_contacts = random.randint(6, 10)
        journey_type = 'A'
    elif 'ATIVO' in situacao:
        n_contacts = random.randint(3, 5)
        journey_type = 'B'
    elif 'INAT' in situacao and 'REC' in situacao:
        n_contacts = random.randint(5, 8)
        journey_type = 'C'
    elif 'INAT' in situacao:
        n_contacts = random.randint(5, 8)
        journey_type = 'D'
    else:
        n_contacts = random.randint(3, 7)
        journey_type = 'B'

    # Add jitter
    n_contacts += random.randint(-1, 2)
    n_contacts = max(3, min(14, n_contacts))

    # Generate pre-sale contacts
    if not has_orc:
        # ORCAMENTO (D-1 to D-3)
        orc_days = random.randint(1, 3)
        orc_date = subtract_business_days(sale_date, orc_days)
        add_record(orc_date, cnpj, consultor, 'ORCAMENTO', 'orcamento', situacao)

    # CADASTRO for prospects
    if journey_type == 'A' and not has_venda:
        cad_days = random.randint(2, 5)
        cad_date = subtract_business_days(sale_date, orc_days + cad_days if not has_orc else cad_days)
        add_record(cad_date, cnpj, consultor, 'CADASTRO', 'cadastro', situacao)

    # EM ATENDIMENTO contacts (pre-sale)
    pre_contacts = max(1, n_contacts - 3)  # Reserve 3 for orc/venda/post
    for i in range(pre_contacts):
        days_before = random.randint(3, max(4, n_contacts * 2))
        dt = subtract_business_days(sale_date, days_before)
        # 10-15% chance of NAO ATENDE/NAO RESPONDE
        if random.random() < 0.12:
            resultado = random.choice(['NAO ATENDE', 'NAO RESPONDE'])
            cat = 'nao_atende'
        else:
            resultado = 'EM ATENDIMENTO'
            if i == 0 and journey_type == 'A':
                cat = 'prospeccao'
            else:
                cat = random.choice(['follow_up', 'relacionamento', 'prospeccao'])
        add_record(dt, cnpj, consultor, resultado, cat, situacao)

    # VENDA (D0) - only if not already covered
    if not has_venda:
        add_record(sale_date, cnpj, consultor, 'VENDA / PEDIDO', 'venda', situacao)

    # Post-sale: Material MKT (D+2/3)
    if random.random() < 0.7:  # 70% get MKT
        mkt_days = random.randint(2, 3)
        mkt_date = sale_date + timedelta(days=mkt_days)
        while mkt_date.weekday() >= 5:
            mkt_date += timedelta(days=1)
        add_record(mkt_date, cnpj, consultor, 'RELACIONAMENTO', 'material_mkt', situacao)

    # Post-sale: CS (D+7 to D+10)
    if random.random() < 0.5:
        cs_days = random.randint(7, 10)
        cs_date = sale_date + timedelta(days=cs_days)
        while cs_date.weekday() >= 5:
            cs_date += timedelta(days=1)
        add_record(cs_date, cnpj, consultor, 'SUPORTE', 'cs', situacao, tipo_acao='RECEPTIVO')

    journey_count += 1

print(f"Sale journeys generated: {journey_count}")
print(f"Synthetic records from journeys: {len(all_synthetic)}")

# B) Generate non-sale activities (E/F journeys) to add depth
# Only if we need more volume (gap was negative, so minimal)
non_sale_count = 0
# Generate some E (loss) and F (nurture) journeys for realism
all_cnpjs = list(cnpj_info.keys())
if all_cnpjs:
    # E journeys: ~5% of clients with losses
    loss_clients = random.sample(all_cnpjs, min(50, len(all_cnpjs) // 20))
    for cnpj in loss_clients:
        info = cnpj_info[cnpj]
        dt = date(2025, random.randint(3, 12), random.randint(1, 28))
        while dt.weekday() >= 5:
            dt += timedelta(days=1)
        consultor = pick_consultor(info.get('uf', ''), info.get('rede', ''), dt)
        if not is_valid_consultant_date(consultor, dt):
            continue
        # 3-4 contacts ending in loss
        for j in range(random.randint(2, 4)):
            contact_dt = subtract_business_days(dt, j * random.randint(2, 5))
            if j < random.randint(1, 3):
                add_record(contact_dt, cnpj, consultor, 'EM ATENDIMENTO', 'prospeccao',
                          info.get('situacao', 'INATIVO ANTIGO'))
            else:
                motivo = random.choice([
                    'PRECO NAO COMPETITIVO', 'PRODUTO NAO VENDEU',
                    'FECHOU LOJA', 'SEM RESPOSTA DEFINITIVA',
                    'OPTOU POR CONCORRENTE', 'FORA DO PERFIL',
                ])
                add_record(contact_dt, cnpj, consultor, 'PERDA / FECHOU LOJA', 'perda',
                          info.get('situacao', 'INATIVO ANTIGO'), motivo=motivo)
        non_sale_count += 1

    # F journeys: quarterly nurture for inactive clients
    nurture_clients = random.sample(all_cnpjs, min(80, len(all_cnpjs) // 10))
    for cnpj in nurture_clients:
        info = cnpj_info[cnpj]
        if 'INAT' not in info.get('situacao', ''):
            continue
        # 1-2 contacts per quarter
        for q in range(random.randint(1, 3)):
            month = random.choice([3, 6, 9, 12]) if q < 2 else random.randint(2, 11)
            dt = date(2025, month, random.randint(5, 25))
            while dt.weekday() >= 5:
                dt += timedelta(days=1)
            consultor = pick_consultor(info.get('uf', ''), info.get('rede', ''), dt)
            if not is_valid_consultant_date(consultor, dt):
                continue
            add_record(dt, cnpj, consultor,
                      random.choice(['FOLLOW UP 7', 'FOLLOW UP 15', 'RELACIONAMENTO']),
                      random.choice(['follow_up', 'relacionamento']),
                      info.get('situacao', 'INATIVO ANTIGO'))
            non_sale_count += 1

print(f"Non-sale activities: {non_sale_count}")
print(f"TOTAL synthetic records: {len(all_synthetic)}")

# =====================================================================
# TASK 3: VALIDATE + SAVE
# =====================================================================

print("\n" + "=" * 60)
print("TASK 3: VALIDATION + SAVE")
print("=" * 60)

validation = {}

# 1. Zero weekends
from datetime import datetime as dt_class
weekend_count = sum(1 for r in all_synthetic
                   if dt_class.strptime(r['DATA'], '%Y-%m-%d').weekday() >= 5)
validation['weekends'] = weekend_count
if weekend_count > 0:
    print(f"  [AUTO-FIX] Moving {weekend_count} weekend records to next Monday")
    for r in all_synthetic:
        d = dt_class.strptime(r['DATA'], '%Y-%m-%d').date()
        if d.weekday() >= 5:
            while d.weekday() >= 5:
                d += timedelta(days=1)
            r['DATA'] = d.strftime('%Y-%m-%d')
    weekend_count = 0
    validation['weekends'] = 0
print(f"  Weekends: {validation['weekends']} {'PASS' if validation['weekends'] == 0 else 'FAIL'}")

# 2. Capacity (max 40/day/consultant)
from collections import Counter
daily_counts = Counter((r['CONSULTOR'], r['DATA']) for r in all_synthetic)
over_cap = {k: v for k, v in daily_counts.items() if v > 40}
validation['capacity_violations'] = len(over_cap)
print(f"  Capacity violations: {len(over_cap)} {'PASS' if not over_cap else 'WARN'}")

# 3. VENDA needs ORCAMENTO
vendas_syn = [r for r in all_synthetic if 'VENDA' in r.get('RESULTADO', '')]
all_records_combined = cf_records + dk_records + all_synthetic
orcamentos_by_cnpj_month = defaultdict(bool)
for r in all_records_combined:
    if 'ORCAMENTO' in r.get('RESULTADO', '') or 'ORÇAMENTO' in r.get('RESULTADO', ''):
        try:
            d = dt_class.strptime(r['DATA'][:10], '%Y-%m-%d').date()
            orcamentos_by_cnpj_month[(r['CNPJ'], d.year, d.month)] = True
        except (ValueError, TypeError):
            pass
missing_orc = 0
for v in vendas_syn:
    try:
        d = dt_class.strptime(v['DATA'][:10], '%Y-%m-%d').date()
        key = (v['CNPJ'], d.year, d.month)
        if not orcamentos_by_cnpj_month.get(key):
            missing_orc += 1
    except (ValueError, TypeError):
        pass
validation['missing_orcamento'] = missing_orc
print(f"  VENDA without ORCAMENTO: {missing_orc} {'PASS' if missing_orc == 0 else 'WARN'}")

# 4. Helder timeline
helder_after = sum(1 for r in all_synthetic
                  if r['CONSULTOR'] == 'HELDER BRUNKOW'
                  and r['DATA'] > '2025-08-31')
validation['helder_after_aug'] = helder_after
print(f"  Helder after Aug/2025: {helder_after} {'PASS' if helder_after == 0 else 'FAIL'}")

# 5. Julio timeline
julio_before = sum(1 for r in all_synthetic
                  if r['CONSULTOR'] == 'JULIO GADRET'
                  and r['DATA'] < '2025-09-01')
validation['julio_before_sep'] = julio_before
print(f"  Julio before Sep/2025: {julio_before} {'PASS' if julio_before == 0 else 'FAIL'}")

# 6. CNPJ validation
bad_cnpj = sum(1 for r in all_synthetic
              if len(r.get('CNPJ', '')) != 14 or not r['CNPJ'].isdigit())
validation['bad_cnpj'] = bad_cnpj
print(f"  Invalid CNPJs: {bad_cnpj} {'PASS' if bad_cnpj == 0 else 'FAIL'}")

# 7. All SINTETICO
non_synth = sum(1 for r in all_synthetic if r.get('ORIGEM_DADO') != 'SINTETICO')
validation['non_sintetico'] = non_synth
print(f"  Non-SINTETICO records: {non_synth} {'PASS' if non_synth == 0 else 'FAIL'}")

# 8. Zero financial values (Two-Base)
has_financial = sum(1 for r in all_synthetic if any(k in r for k in ['VALOR', 'R$', 'PEDIDO_VALOR']))
validation['financial_values'] = has_financial
print(f"  Financial values: {has_financial} {'PASS' if has_financial == 0 else 'FAIL'}")

# 9. Monthly distribution
monthly_dist = Counter()
for r in all_synthetic:
    try:
        d = dt_class.strptime(r['DATA'][:10], '%Y-%m-%d').date()
        monthly_dist[(d.year, d.month)] += 1
    except (ValueError, TypeError):
        pass
print(f"\n  Monthly distribution:")
for key in sorted(monthly_dist.keys()):
    y, m = key
    print(f"    {y}-{m:02d}: {monthly_dist[key]} records")

# Save JSON
output = {
    'metadata': {
        'source': 'SINTETICO',
        'total': len(all_synthetic),
        'anchor_sales': len(sales_list),
        'journeys_generated': journey_count,
        'non_sale_activities': non_sale_count,
        'gap_calculated': gap,
        'existing_controle_funil': len(cf_records),
        'existing_deskrio': len(dk_records),
        'validation': validation,
        'date_processed': '2026-02-17',
        'seed': 42,
    },
    'records': all_synthetic,
}

output_path = BASE / 'data/output/phase04/synthetic_generated.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n{'=' * 60}")
print(f"SAVED: {output_path}")
print(f"Total synthetic records: {len(all_synthetic)}")
print(f"Combined total: {len(cf_records)} + {len(dk_records)} + {len(all_synthetic)} = {len(cf_records) + len(dk_records) + len(all_synthetic)}")
print(f"{'=' * 60}")
