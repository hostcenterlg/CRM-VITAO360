#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V33: Simulação JUL/25 — 3 consultores, 77 vendas, 23 dias úteis"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from simulacao_mensal_engine import run_simulation
from datetime import date

BASE = r'c:\Users\User\OneDrive\Documentos\GitHub\CRM-VITAO360\data\output\phase10'

run_simulation({
    'version': 'V33',
    'month_name': 'JUL',
    'month_num': 7,
    'year': 2025,
    'month_start': date(2025, 7, 1),
    'month_end': date(2025, 7, 31),
    'feriados': set(),  # Sem feriados nacionais em JUL
    'col_fat': 32,
    'prev_months_max': 6,
    'seed': 48,
    'input_file': os.path.join(BASE, 'CRM_VITAO360_V32_FINAL.xlsx'),
    'output_file': os.path.join(BASE, 'CRM_VITAO360_V33_FINAL.xlsx'),
    'consultores': {
        "DAIANE STADLER":  {"max_fu": 90, "max_retry": 30, "venda_pct": 0.35, "prospects_max": 50},
        "HELDER BRUNKOW":  {"max_fu": 70, "max_retry": 25, "venda_pct": 0.33, "prospects_max": 40},
        "MANU DITZEL":     {"max_fu": 70, "max_retry": 25, "venda_pct": 0.32, "prospects_max": 40},
    },
})
