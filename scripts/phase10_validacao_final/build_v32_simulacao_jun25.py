#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V32: Simulação JUN/25 — 3 consultores, 101 vendas, 21 dias úteis"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from simulacao_mensal_engine import run_simulation
from datetime import date

BASE = r'c:\Users\User\OneDrive\Documentos\GitHub\CRM-VITAO360\data\output\phase10'

run_simulation({
    'version': 'V32',
    'month_name': 'JUN',
    'month_num': 6,
    'year': 2025,
    'month_start': date(2025, 6, 1),
    'month_end': date(2025, 6, 30),
    'feriados': set(),  # Sem feriados nacionais em JUN
    'col_fat': 31,
    'prev_months_max': 5,
    'seed': 47,
    'input_file': os.path.join(BASE, 'CRM_VITAO360_V31_FINAL.xlsx'),
    'output_file': os.path.join(BASE, 'CRM_VITAO360_V32_FINAL.xlsx'),
    'consultores': {
        "DAIANE STADLER":  {"max_fu": 90, "max_retry": 30, "venda_pct": 0.36, "prospects_max": 60},
        "HELDER BRUNKOW":  {"max_fu": 65, "max_retry": 20, "venda_pct": 0.32, "prospects_max": 50},
        "MANU DITZEL":     {"max_fu": 65, "max_retry": 20, "venda_pct": 0.32, "prospects_max": 50},
    },
})
