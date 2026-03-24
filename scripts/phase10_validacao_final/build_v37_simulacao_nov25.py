#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V37: Simulação NOV/25 — 4 consultores, Black Friday (90% reclamações logística), churned"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from simulacao_mensal_engine import run_simulation
from datetime import date

BASE = r'c:\Users\User\OneDrive\Documentos\GitHub\CRM-VITAO360\data\output\phase10'

run_simulation({
    'version': 'V37',
    'month_name': 'NOV',
    'month_num': 11,
    'year': 2025,
    'month_start': date(2025, 11, 1),
    'month_end': date(2025, 11, 30),
    'feriados': {date(2025, 11, 20)},  # Consciência Negra (quinta)
    'col_fat': 36,
    'prev_months_max': 10,
    'seed': 52,
    'input_file': os.path.join(BASE, 'CRM_VITAO360_V36_FINAL.xlsx'),
    'output_file': os.path.join(BASE, 'CRM_VITAO360_V37_FINAL.xlsx'),
    'consultores': {
        "DAIANE STADLER":   {"max_fu": 70, "max_retry": 22, "venda_pct": 0.28, "prospects_max": 20},
        "MANU DITZEL":      {"max_fu": 65, "max_retry": 20, "venda_pct": 0.26, "prospects_max": 15},
        "LARISSA PADILHA":  {"max_fu": 60, "max_retry": 18, "venda_pct": 0.24, "prospects_max": 20},
        "JULIO GADRET":     {"max_fu": 45, "max_retry": 14, "venda_pct": 0.22, "prospects_max": 30},
    },
    # BLACK FRIDAY: 90% dos compradores tiveram problemas de logística/frete
    'black_friday_reclamacoes': 100,  # ~100 reclamações (NOV = pico)
    # Clientes inativos: equipe tentando reativar
    'churned_retries_max': 40,
})
