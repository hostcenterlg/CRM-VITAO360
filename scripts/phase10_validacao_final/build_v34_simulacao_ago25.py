#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V34: Simulação AGO/25 — LARISSA entra! HELDER saiu! 3 consultores, 117 vendas"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from simulacao_mensal_engine import run_simulation
from datetime import date

BASE = r'c:\Users\User\OneDrive\Documentos\GitHub\CRM-VITAO360\data\output\phase10'

run_simulation({
    'version': 'V34',
    'month_name': 'AGO',
    'month_num': 8,
    'year': 2025,
    'month_start': date(2025, 8, 1),
    'month_end': date(2025, 8, 31),
    'feriados': set(),
    'col_fat': 33,
    'prev_months_max': 7,
    'seed': 49,
    'input_file': os.path.join(BASE, 'CRM_VITAO360_V33_FINAL.xlsx'),
    'output_file': os.path.join(BASE, 'CRM_VITAO360_V34_FINAL.xlsx'),
    'consultores': {
        "DAIANE STADLER":   {"max_fu": 90, "max_retry": 30, "venda_pct": 0.38, "prospects_max": 50},
        "MANU DITZEL":      {"max_fu": 80, "max_retry": 25, "venda_pct": 0.32, "prospects_max": 40},
        "LARISSA PADILHA":  {"max_fu": 25, "max_retry": 10, "venda_pct": 0.30, "prospects_max": 60},
    },
})
