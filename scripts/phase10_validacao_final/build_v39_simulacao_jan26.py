#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V39: Simulação JAN/26 — 4 consultores, 71 vendas SAP, 1 Jan = feriado"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from simulacao_mensal_engine import run_simulation
from datetime import date

BASE = r'c:\Users\User\OneDrive\Documentos\GitHub\CRM-VITAO360\data\output\phase10'

run_simulation({
    'version': 'V39',
    'month_name': 'JAN',
    'month_num': 1,
    'year': 2026,
    'month_start': date(2026, 1, 1),
    'month_end': date(2026, 1, 31),
    'feriados': {date(2026, 1, 1)},  # Confraternização Universal (quinta)
    'col_fat': 38,
    'prev_months_max': 12,  # não usado mais (engine usa month_start)
    'seed': 54,
    'input_file': os.path.join(BASE, 'CRM_VITAO360_V38_FINAL.xlsx'),
    'output_file': os.path.join(BASE, 'CRM_VITAO360_V39_FINAL.xlsx'),
    'consultores': {
        "DAIANE STADLER":   {"max_fu": 60, "max_retry": 18, "venda_pct": 0.21, "prospects_max": 10},
        "MANU DITZEL":      {"max_fu": 55, "max_retry": 16, "venda_pct": 0.30, "prospects_max": 8},
        "LARISSA PADILHA":  {"max_fu": 70, "max_retry": 22, "venda_pct": 0.39, "prospects_max": 12},
        "JULIO GADRET":     {"max_fu": 35, "max_retry": 10, "venda_pct": 0.10, "prospects_max": 8},
    },
    # Equipe tentando reativar clientes inativos (pós festas)
    'churned_retries_max': 45,
})
