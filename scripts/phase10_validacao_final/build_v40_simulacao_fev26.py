#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V40: Simulação FEV/26 — 4 consultores, 49 vendas Mercos (até 16/02), Carnaval"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from simulacao_mensal_engine import run_simulation
from datetime import date

BASE = r'c:\Users\User\OneDrive\Documentos\GitHub\CRM-VITAO360\data\output\phase10'

# CNPJs compradores FEV/26 extraídos do relatorio Mercos (até 16/02/2026)
# Casados por Razão Social com CARTEIRA — 49 de 50 encontrados
BUYERS_FEV26 = [
    '00939085000178', '03207136000165', '04755895000125', '04908058013339',
    '06982791000189', '07192414001342', '08808355000113', '11322507000188',
    '13975801000114', '14147398000106', '15265760000106', '15626213000109',
    '16693613000353', '17847228000203', '18997672000189', '21450286000187',
    '21691717000105', '23014826000105', '27141630000132', '29841719000137',
    '31545180000110', '32889911000108', '33463112000138', '35830031000154',
    '36611091000149', '37370567000160', '39579910000106', '39797983000174',
    '41626544000140', '45100604000148', '47900505000176', '48097578000134',
    '48794235000129', '50342650000193', '50446226000199', '50815238000143',
    '53918909000190', '55383649000120', '57963322000153', '58010332000137',
    '60475933000167', '60670819000198', '62167819000103', '63198302000136',
    '63826539000114', '63964303000144', '64425601000129', '74552068000110',
    '76726884000128',
]

run_simulation({
    'version': 'V40',
    'month_name': 'FEV',
    'month_num': 2,
    'year': 2026,
    'month_start': date(2026, 2, 1),
    'month_end': date(2026, 2, 28),
    'feriados': {
        date(2026, 2, 16),  # Carnaval segunda
        date(2026, 2, 17),  # Carnaval terça
        date(2026, 2, 18),  # Quarta de cinzas (ponto facultativo)
    },
    'col_fat': 38,  # não usado quando buyers_override presente
    'prev_months_max': 12,
    'seed': 55,
    'input_file': os.path.join(BASE, 'CRM_VITAO360_V39_FINAL.xlsx'),
    'output_file': os.path.join(BASE, 'CRM_VITAO360_V40_FINAL.xlsx'),
    'buyers_override': BUYERS_FEV26,
    'consultores': {
        "DAIANE STADLER":   {"max_fu": 55, "max_retry": 16, "venda_pct": 0.22, "prospects_max": 8},
        "MANU DITZEL":      {"max_fu": 50, "max_retry": 14, "venda_pct": 0.28, "prospects_max": 6},
        "LARISSA PADILHA":  {"max_fu": 65, "max_retry": 20, "venda_pct": 0.40, "prospects_max": 10},
        "JULIO GADRET":     {"max_fu": 30, "max_retry": 8,  "venda_pct": 0.10, "prospects_max": 6},
    },
    # Equipe tentando reativar clientes inativos
    'churned_retries_max': 40,
})
