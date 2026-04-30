"""
CRM VITAO360 — PDF Generator (Onda 6 — ROMEO)

Gera PDF A4 1 página com Resumo CEO via reportlab.

Estrutura do PDF:
  - Cabeçalho: VITAO360 | RESUMO CEO | Razão Social
  - Linha de metadados: CNPJ | Ano | Veredito
  - Corpo: texto do resumo (fonte LLM ou template)
  - Rodapé: timestamp | fonte (LLM/TEMPLATE) | validação R$

DEPENDÊNCIA: reportlab >= 4.0
"""

from __future__ import annotations

from io import BytesIO
from typing import Optional

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


# ---------------------------------------------------------------------------
# Cores VITAO360 (tema LIGHT — R9)
# ---------------------------------------------------------------------------

# Nunca dark mode. Cores status da regra R9.
_COR_HEADER = colors.HexColor("#1A3A5C")   # azul escuro corporativo
_COR_ACCENT = colors.HexColor("#00B050")   # verde ATIVO (R9)
_COR_ALERTA = colors.HexColor("#FFC000")   # amarelo INAT.REC (R9)
_COR_CRITICO = colors.HexColor("#FF0000")  # vermelho INAT.ANT (R9)
_COR_CINZA = colors.HexColor("#666666")
_COR_BORDA = colors.HexColor("#CCCCCC")
_COR_FUNDO_HEADER = colors.HexColor("#F0F4F8")

# Mapeamento veredito → cor
_VEREDITO_CORES = {
    "SAUDAVEL": _COR_ACCENT,
    "REVISAR": _COR_ALERTA,
    "RENEGOCIAR": _COR_ALERTA,
    "SUBSTITUIR": _COR_CRITICO,
    "ALERTA_CREDITO": _COR_CRITICO,
    "SEM_DADOS": _COR_CINZA,
}


def _cor_veredito(veredito: str) -> object:
    return _VEREDITO_CORES.get(veredito, _COR_CINZA)


def _pdf_fallback(metadata: dict) -> bytes:
    """
    PDF mínimo em texto puro (fallback se reportlab não instalado).
    Retorna bytes UTF-8 como 'PDF' (na prática é texto — não ideal,
    mas nunca quebra o endpoint).
    """
    cnpj = metadata.get("cnpj", "")
    ano = metadata.get("ano", "")
    razao_social = metadata.get("razao_social", "")
    texto = metadata.get("texto", "")
    veredito = metadata.get("veredito", "")
    fonte = metadata.get("fonte", "TEMPLATE")
    validacao = metadata.get("validacao", "OK")
    gerado_em = metadata.get("gerado_em", "")

    content = (
        f"RESUMO CEO — {razao_social}\n"
        f"CNPJ: {cnpj} | Ano: {ano} | Veredito: {veredito}\n"
        f"{'='*60}\n\n"
        f"{texto}\n\n"
        f"{'='*60}\n"
        f"Gerado em {gerado_em} | Fonte: {fonte} | Validação R$: {validacao}\n"
        f"[AVISO: reportlab não instalado — PDF em formato texto]\n"
    )
    return content.encode("utf-8")


def gerar_pdf_resumo_ceo(texto: str, metadata: dict) -> bytes:
    """
    Gera PDF A4 1 página com cabeçalho VITAO360 + texto + rodapé.

    Args:
        texto: texto do resumo (multi-linha, vindo de gerar_resumo_ceo)
        metadata: dict com cnpj, ano, razao_social, veredito, fonte,
                  validacao, gerado_em

    Returns:
        bytes do PDF gerado

    Raises:
        RuntimeError se reportlab indisponível e texto não é bytes
    """
    if not REPORTLAB_AVAILABLE:
        return _pdf_fallback({**metadata, "texto": texto})

    cnpj = metadata.get("cnpj", "")
    ano = metadata.get("ano", "")
    razao_social = metadata.get("razao_social", "") or cnpj
    veredito = metadata.get("veredito", "SEM_DADOS")
    fonte = metadata.get("fonte", "TEMPLATE")
    validacao = metadata.get("validacao", "OK")
    gerado_em = metadata.get("gerado_em", "")

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title=f"Resumo CEO — {razao_social}",
        author="CRM VITAO360",
    )

    styles = getSampleStyleSheet()

    # Estilos customizados (Arial 9pt dados, 10pt headers — R9)
    estilo_titulo = ParagraphStyle(
        "TituloVitao",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=_COR_HEADER,
        spaceAfter=4,
        leading=16,
    )
    estilo_subtitulo = ParagraphStyle(
        "SubtituloVitao",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=_COR_CINZA,
        spaceAfter=2,
        leading=11,
    )
    estilo_veredito = ParagraphStyle(
        "VeredrditoVitao",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=_cor_veredito(veredito),
        spaceAfter=0,
        leading=12,
    )
    estilo_corpo = ParagraphStyle(
        "CorpoVitao",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.black,
        spaceAfter=4,
        leading=13,
        wordWrap="LTR",
    )
    estilo_secao = ParagraphStyle(
        "SecaoVitao",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        textColor=_COR_HEADER,
        spaceAfter=2,
        leading=11,
    )
    estilo_rodape = ParagraphStyle(
        "RodapeVitao",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7,
        textColor=_COR_CINZA,
        spaceAfter=0,
        leading=9,
        alignment=TA_CENTER,
    )

    story = []

    # ------------------------------------------------------------------
    # CABEÇALHO
    # ------------------------------------------------------------------
    story.append(Paragraph("CRM VITAO360 — RESUMO CEO", estilo_titulo))
    story.append(Paragraph(f"{razao_social}", estilo_subtitulo))
    story.append(
        Paragraph(
            f"CNPJ: {cnpj}&nbsp;&nbsp;|&nbsp;&nbsp;"
            f"Ano de referência: {ano}&nbsp;&nbsp;|&nbsp;&nbsp;"
            f"Veredito: <b>{veredito}</b>",
            estilo_subtitulo,
        )
    )
    story.append(HRFlowable(width="100%", thickness=1, color=_COR_BORDA, spaceAfter=8))

    # ------------------------------------------------------------------
    # CORPO — texto do resumo
    # Processa linha por linha, detectando seções (em maiúsculas + ':')
    # ------------------------------------------------------------------
    linhas_texto = texto.split("\n")

    for linha in linhas_texto:
        linha_strip = linha.strip()
        if not linha_strip:
            story.append(Spacer(1, 0.15 * cm))
            continue

        # Detecta cabeçalho do resumo (primeira linha: "RESUMO CEO — ...")
        if linha_strip.startswith("RESUMO CEO —"):
            continue  # já exibido no cabeçalho do PDF

        # Detecta seções (ex: "DIAGNÓSTICO:", "ANOMALIAS:", "AÇÕES PRIORITÁRIAS:", etc.)
        eh_secao = (
            linha_strip.endswith(":") and linha_strip == linha_strip.upper()
        ) or linha_strip.rstrip(":").upper() in (
            "DIAGNÓSTICO", "ANOMALIAS", "AÇÕES PRIORITÁRIAS",
            "AÇÕES PRIORITÁRIAS:", "RECOMENDAÇÃO FINAL", "RECOMENDAÇÃO FINAL:",
            "DIAGNOSTICO", "ACOES PRIORITARIAS", "RECOMENDACAO FINAL",
        )

        if eh_secao:
            story.append(Paragraph(linha_strip, estilo_secao))
        else:
            story.append(Paragraph(linha_strip, estilo_corpo))

    # ------------------------------------------------------------------
    # RODAPÉ
    # ------------------------------------------------------------------
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_COR_BORDA, spaceAfter=4))

    validacao_cor = "#00B050" if validacao == "OK" else "#FF0000"
    story.append(
        Paragraph(
            f"Gerado em {gerado_em} &nbsp;|&nbsp; "
            f"Fonte: {fonte} &nbsp;|&nbsp; "
            f"Validação R$: <font color='{validacao_cor}'><b>{validacao}</b></font> &nbsp;|&nbsp; "
            "CRM VITAO360 — Confidencial",
            estilo_rodape,
        )
    )

    doc.build(story)
    return buffer.getvalue()
