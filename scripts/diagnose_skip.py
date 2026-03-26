"""Analisa por que rows sao puladas na carga de LOGs."""
import re
import openpyxl
from datetime import datetime, date

XLSX_PATH = r"C:\Users\User\OneDrive\Área de Trabalho\CRM_VITAO360  INTELIGENTE   FINAL OK .xlsx"

IDX_DATA = 0
IDX_CONSULTOR = 1
IDX_CNPJ = 3
IDX_ESTAGIO = 8
IDX_FASE = 10
IDX_RESULTADO = 20

def normalizar_cnpj(val):
    if val is None:
        return None
    if isinstance(val, float):
        val = str(int(val))
    else:
        val = str(val)
    digits = re.sub(r"\D", "", val).zfill(14)
    digits = digits[-14:]
    if len(digits) != 14 or digits == "00000000000000":
        return None
    return digits

def coerce_date(val):
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day)
    return None

wb = openpyxl.load_workbook(XLSX_PATH, data_only=True, read_only=True)

for aba in ['LARISSA']:
    ws = wb[aba]
    motivos = {
        "vazia": 0,
        "sem_data": 0,
        "sem_cnpj": 0,
        "sem_consultor": 0,
        "sem_resultado_todos": 0,
        "ok": 0
    }
    total = 0

    for row_vals in ws.iter_rows(min_row=2, values_only=True):
        total += 1

        if all(v is None for v in row_vals):
            motivos["vazia"] += 1
            continue

        data = coerce_date(row_vals[IDX_DATA])
        if data is None:
            motivos["sem_data"] += 1
            continue

        cnpj = normalizar_cnpj(row_vals[IDX_CNPJ]) if len(row_vals) > IDX_CNPJ else None
        if cnpj is None:
            motivos["sem_cnpj"] += 1
            continue

        consultor = str(row_vals[IDX_CONSULTOR]).strip() if row_vals[IDX_CONSULTOR] else None
        if not consultor:
            motivos["sem_consultor"] += 1
            continue

        resultado = row_vals[IDX_RESULTADO] if len(row_vals) > IDX_RESULTADO else None
        fase = row_vals[IDX_FASE] if len(row_vals) > IDX_FASE else None
        estagio = row_vals[IDX_ESTAGIO] if len(row_vals) > IDX_ESTAGIO else None

        if resultado is None and fase is None and estagio is None:
            motivos["sem_resultado_todos"] += 1
            continue

        motivos["ok"] += 1

    print(f"\n=== {aba} - {total} rows total ===")
    for k, v in motivos.items():
        pct = 100.0 * v / total if total > 0 else 0
        print(f"  {k:<25}: {v:5d} ({pct:.1f}%)")

wb.close()
