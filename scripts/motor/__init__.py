"""
Motor Operacional CRM VITAO360 v2.0

Modulo principal do motor Python que extrai inteligencia da planilha FINAL
(40 abas, 210K+ formulas) e processa: import, motor de regras, score,
sinaleiro, agenda inteligente e projecao.

Pipeline completo:
    import xlsx -> normalizar CNPJ -> DE-PARA vendedores
        -> calcular SITUACAO -> aplicar MOTOR (92 regras)
        -> calcular SCORE (6 fatores) -> gerar P1-P7
        -> calcular SINALEIRO -> gerar CADENCIA
        -> gerar AGENDA (40-60/consultor, Score desc)
        -> exportar xlsx
"""

from scripts.motor.helpers import normalizar_cnpj, normalizar_vendedor, safe_read_sheet

__all__ = [
    "normalizar_cnpj",
    "normalizar_vendedor",
    "safe_read_sheet",
    "importar_planilha",
]


def __getattr__(name):
    """Lazy import para modulos que podem nao existir ainda durante build."""
    if name == "importar_planilha":
        from scripts.motor.import_pipeline import importar_planilha
        return importar_planilha
    raise AttributeError(f"module 'scripts.motor' has no attribute {name!r}")

__version__ = "2.0.0"
