#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V38: Simulação DEZ/25 — 4 consultores, pós-Black Friday reclamações, Natal, churned"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from simulacao_mensal_engine import run_simulation
from datetime import date

BASE = r'c:\Users\User\OneDrive\Documentos\GitHub\CRM-VITAO360\data\output\phase10'

run_simulation({
    'version': 'V38',
    'month_name': 'DEZ',
    'month_num': 12,
    'year': 2025,
    'month_start': date(2025, 12, 1),
    'month_end': date(2025, 12, 31),
    'feriados': {date(2025, 12, 25)},  # Natal (quinta)
    'col_fat': 37,
    'prev_months_max': 11,
    'seed': 53,
    'input_file': os.path.join(BASE, 'CRM_VITAO360_V37_FINAL.xlsx'),
    'output_file': os.path.join(BASE, 'CRM_VITAO360_V38_FINAL.xlsx'),
    'consultores': {
        "DAIANE STADLER":   {"max_fu": 65, "max_retry": 20, "venda_pct": 0.28, "prospects_max": 15},
        "MANU DITZEL":      {"max_fu": 60, "max_retry": 18, "venda_pct": 0.26, "prospects_max": 10},
        "LARISSA PADILHA":  {"max_fu": 55, "max_retry": 16, "venda_pct": 0.24, "prospects_max": 15},
        "JULIO GADRET":     {"max_fu": 50, "max_retry": 14, "venda_pct": 0.22, "prospects_max": 20},
    },
    # Pós-Black Friday: ainda reclamações, mas diminuindo
    'black_friday_reclamacoes': 50,  # DEZ = metade do pico de NOV
    # Clientes inativos: equipe continua tentando
    'churned_retries_max': 35,
})
