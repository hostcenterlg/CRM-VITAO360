"""
Funcoes utilitarias do Motor Operacional CRM VITAO360 v2.0.

Fornece: normalizar_cnpj, normalizar_vendedor, safe_read_sheet.
"""

import logging
import re
from typing import Optional

from scripts.motor.config import DE_PARA_VENDEDORES

logger = logging.getLogger("motor.helpers")


def normalizar_cnpj(val) -> Optional[str]:
    """Normaliza CNPJ para string de 14 digitos zero-padded.

    - None ou vazio -> None
    - Remove tudo que nao eh digito
    - Zero-pad ate 14 digitos
    - Se mais de 14 digitos: log warning, retorna os ultimos 14
    - NUNCA retorna float ou int

    Args:
        val: Qualquer valor (str, int, float, None)

    Returns:
        String de 14 digitos ou None
    """
    if val is None:
        return None

    val_str = str(val).strip()
    if val_str == "" or val_str.lower() == "nan" or val_str.lower() == "none":
        return None

    # Remove tudo que nao eh digito
    digits = re.sub(r"\D", "", val_str)

    if len(digits) == 0:
        return None

    # Zero-pad ate 14 digitos
    cnpj = digits.zfill(14)

    # Se mais de 14 digitos (ex: float com decimais espurios)
    if len(cnpj) > 14:
        logger.warning(
            "CNPJ com mais de 14 digitos: %r -> %s (usando ultimos 14)",
            val,
            cnpj,
        )
        cnpj = cnpj[-14:]

    return cnpj


def normalizar_vendedor(nome) -> Optional[str]:
    """Mapeia alias de vendedor para nome canonico (MANU, LARISSA, etc.).

    Logica de match:
    - Normaliza para UPPER
    - Para cada (canonical, aliases): verifica se alias.upper() esta contido
      no nome ou nome esta contido no alias.upper()
    - Se nenhum match: retorna "DESCONHECIDO"
      (LEGADO sao vendedores CONHECIDOS que sairam, nao eh fallback)

    Args:
        nome: Nome do vendedor como aparece na planilha

    Returns:
        Nome canonico (MANU, LARISSA, DAIANE, JULIO, LEGADO)
        ou "DESCONHECIDO" se nao encontrar match.
        None se nome eh None/vazio.
    """
    if nome is None:
        return None

    nome_str = str(nome).strip()
    if nome_str == "" or nome_str.lower() == "nan" or nome_str.lower() == "none":
        return None

    nome_upper = nome_str.upper()

    for canonical, aliases in DE_PARA_VENDEDORES.items():
        for alias in aliases:
            alias_upper = alias.upper()
            if alias_upper in nome_upper or nome_upper in alias_upper:
                return canonical

    return "DESCONHECIDO"


def safe_read_sheet(wb, sheet_name: str):
    """Tenta ler uma aba do workbook, retorna None se nao encontrada.

    Args:
        wb: Workbook openpyxl
        sheet_name: Nome exato da aba

    Returns:
        Worksheet ou None
    """
    try:
        ws = wb[sheet_name]
        logger.info("Aba lida com sucesso: '%s'", sheet_name)
        return ws
    except KeyError:
        logger.warning("Aba NAO encontrada: '%s'", sheet_name)
        return None
