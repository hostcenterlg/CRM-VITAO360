#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V35: Simulação SET/25 — 4 consultores, 93 vendas, 7 Set = domingo"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from simulacao_mensal_engine import run_simulation
from datetime import date

BASE = r'c:\Users\User\OneDrive\Documentos\GitHub\CRM-VITAO360\data\output\phase10'

run_simulation({
    'version': 'V35',
    'month_name': 'SET',
    'month_num': 9,
    'year': 2025,
    'month_start': date(2025, 9, 1),
    'month_end': date(2025, 9, 30),
    'feriados': set(),  # 7 Set = domingo, sem impacto
    'col_fat': 34,
    'prev_months_max': 8,
    'seed': 50,
    'input_file': os.path.join(BASE, 'CRM_VITAO360_V34_FINAL.xlsx'),
    'output_file': os.path.join(BASE, 'CRM_VITAO360_V35_FINAL.xlsx'),
    'consultores': {
        "DAIANE STADLER":   {"max_fu": 85, "max_retry": 28, "venda_pct": 0.36, "prospects_max": 30},
        "MANU DITZEL":      {"max_fu": 75, "max_retry": 22, "venda_pct": 0.34, "prospects_max": 25},
        "LARISSA PADILHA":  {"max_fu": 55, "max_retry": 18, "venda_pct": 0.30, "prospects_max": 40},
    },
})
