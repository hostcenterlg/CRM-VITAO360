#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V36: Simulação OUT/25 — JULIO entra! 5 consultores, 113 vendas"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from simulacao_mensal_engine import run_simulation
from datetime import date

BASE = r'c:\Users\User\OneDrive\Documentos\GitHub\CRM-VITAO360\data\output\phase10'

run_simulation({
    'version': 'V36',
    'month_name': 'OUT',
    'month_num': 10,
    'year': 2025,
    'month_start': date(2025, 10, 1),
    'month_end': date(2025, 10, 31),
    'feriados': set(),  # 12 Out = domingo, sem impacto
    'col_fat': 35,
    'prev_months_max': 9,
    'seed': 51,
    'input_file': os.path.join(BASE, 'CRM_VITAO360_V35_FINAL.xlsx'),
    'output_file': os.path.join(BASE, 'CRM_VITAO360_V36_FINAL.xlsx'),
    'consultores': {
        "DAIANE STADLER":   {"max_fu": 75, "max_retry": 22, "venda_pct": 0.28, "prospects_max": 25},
        "MANU DITZEL":      {"max_fu": 70, "max_retry": 20, "venda_pct": 0.26, "prospects_max": 20},
        "LARISSA PADILHA":  {"max_fu": 60, "max_retry": 18, "venda_pct": 0.26, "prospects_max": 25},
        "JULIO GADRET":     {"max_fu": 15, "max_retry": 8,  "venda_pct": 0.20, "prospects_max": 50},
    },
})
