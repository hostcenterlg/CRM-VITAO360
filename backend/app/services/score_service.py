"""
CRM VITAO360 — Score Engine: calcula score ponderado e prioridade P0-P7.

Score 0-100 calculado com 6 fatores ponderados:
  FASE         (25%) — Fase do funil comercial
  SINALEIRO    (20%) — Saude do ciclo de compra
  CURVA_ABC    (20%) — Valor do cliente (ABC)
  TEMPERATURA  (15%) — Temperatura comercial
  TIPO_CLIENTE (10%) — Maturidade do cliente
  TENTATIVAS   (10%) — Historico de contatos

Prioridade:
  P0 — SUPORTE com problema_aberto (pula fila)
  P1 — EM ATENDIMENTO + followup_vencido + cs_no_prazo
  P2 — Score 80-100
  P3 — Score 60-79.9
  P4 — Score 45-59.9
  P5 — Score 30-44.9
  P6 — Score 15-29.9
  P7 — Score 0-14.9

R4 — Two-Base Architecture: este servico nao toca valores monetarios.
R5 — CNPJ: String(14), zero-padded, nunca Float.
"""

from __future__ import annotations

import unicodedata
from datetime import date

from sqlalchemy.orm import Session

from backend.app.models.cliente import Cliente
from backend.app.models.score_historico import ScoreHistorico

# ---------------------------------------------------------------------------
# Tabelas de lookup (extraidas de scripts/motor/score_engine.py)
# ---------------------------------------------------------------------------

PESOS: dict[str, float] = {
    "FASE": 0.25,
    "SINALEIRO": 0.20,
    "CURVA_ABC": 0.20,
    "TEMPERATURA": 0.15,
    "TIPO_CLIENTE": 0.10,
    "TENTATIVAS": 0.10,
}

SCORE_FASE: dict[str, int] = {
    "RECOMPRA": 100,
    "NEGOCIACAO": 80,
    "NEGOCIAÇÃO": 80,
    "POS-VENDA": 100,
    "PÓS-VENDA": 100,
    "CS": 100,
    "CS / RECOMPRA": 100,
    "ORCAMENTO": 80,
    "ORÇAMENTO": 80,
    "EM ATENDIMENTO": 80,
    "SALVAMENTO": 60,
    "RECUPERACAO": 40,
    "RECUPERAÇÃO": 40,
    "PROSPECCAO": 30,
    "PROSPECÇÃO": 30,
    "NUTRICAO": 10,
    "NUTRIÇÃO": 10,
}

SCORE_SINALEIRO: dict[str, int] = {
    "VERMELHO": 100,
    "AMARELO": 60,
    "VERDE": 30,
    "ROXO": 0,
}

SCORE_CURVA_ABC: dict[str, int] = {
    "A": 100,
    "B": 60,
    "C": 30,
}

SCORE_TEMPERATURA: dict[str, int] = {
    "QUENTE": 100,
    "MORNO": 60,
    "FRIO": 30,
    "CRITICO": 20,
    "CRÍTICO": 20,
    "PERDIDO": 0,
}

SCORE_TIPO_CLIENTE: dict[str, int] = {
    "MADURO": 100,
    "FIDELIZADO": 85,
    "RECORRENTE": 70,
    "EM DESENVOLVIMENTO": 50,
    "EM DESENV": 50,
    "NOVO": 30,
    "LEAD": 15,
    "PROSPECT": 10,
}

SCORE_TENTATIVAS: dict[str, int] = {
    "T1": 100,
    "T2": 70,
    "T3": 40,
    "T4": 10,
    "NUTRICAO": 5,
    "NUTRIÇÃO": 5,
}

# Faixas de prioridade por score (label, score_min, score_max)
FAIXAS_PRIORIDADE: list[tuple[str, float, float]] = [
    ("P2", 80.0, 100.0),
    ("P3", 60.0, 79.9),
    ("P4", 45.0, 59.9),
    ("P5", 30.0, 44.9),
    ("P6", 15.0, 29.9),
    ("P7",  0.0, 14.9),
]

# Emojis que podem aparecer prefixando o campo temperatura
_EMOJIS_TEMPERATURA = ["🔥", "🟡", "❄️", "💀", "🟢", "🔴", "🟣", "⚠️"]


def _normalizar(valor: object) -> str:
    """
    Normaliza um valor para lookup nas tabelas de score.

    Remove espacos, converte para maiusculas.
    Nao remove acentos — as tabelas de lookup aceitam formas acentuadas e
    nao-acentuadas para cobrir variantes do motor legado.
    """
    if valor is None:
        return ""
    return str(valor).strip().upper()


def _limpar_temperatura(valor: object) -> str:
    """
    Remove emojis e espacos extras do campo temperatura antes do lookup.

    O motor de regras pode prefixar temperatura com emojis:
      '🔥 QUENTE' -> 'QUENTE'
      '❄️ FRIO'   -> 'FRIO'
    """
    s = _normalizar(valor)
    for emoji in _EMOJIS_TEMPERATURA:
        s = s.replace(emoji, "")
    return s.strip()


class ScoreService:
    """
    Calcula o score ponderado (0-100) e prioridade (P0-P7) de um cliente.

    Uso tipico:
        resultado = score_service.calcular(cliente)
        score_service.aplicar_e_salvar(db, cliente)
    """

    def calcular(self, cliente: Cliente) -> dict:
        """
        Calcula score 0-100 com 6 fatores ponderados.

        Args:
            cliente: Instancia Cliente com os campos de inteligencia preenchidos.

        Returns:
            Dict com chaves: score, prioridade, fator_fase, fator_sinaleiro,
            fator_curva, fator_temperatura, fator_tipo_cliente, fator_tentativas.
        """
        temp = _limpar_temperatura(cliente.temperatura)

        fator_fase = SCORE_FASE.get(_normalizar(cliente.fase), 0)
        fator_sinaleiro = SCORE_SINALEIRO.get(_normalizar(cliente.sinaleiro), 0)
        fator_curva = SCORE_CURVA_ABC.get(_normalizar(cliente.curva_abc), 0)
        fator_temperatura = SCORE_TEMPERATURA.get(temp, 0)
        fator_tipo = SCORE_TIPO_CLIENTE.get(_normalizar(cliente.tipo_cliente), 0)
        fator_tentativas = SCORE_TENTATIVAS.get(_normalizar(cliente.tentativas), 0)

        score = round(
            fator_fase * PESOS["FASE"]
            + fator_sinaleiro * PESOS["SINALEIRO"]
            + fator_curva * PESOS["CURVA_ABC"]
            + fator_temperatura * PESOS["TEMPERATURA"]
            + fator_tipo * PESOS["TIPO_CLIENTE"]
            + fator_tentativas * PESOS["TENTATIVAS"],
            1,
        )

        prioridade = self._calcular_prioridade(cliente, score)

        return {
            "score": score,
            "prioridade": prioridade,
            "fator_fase": float(fator_fase),
            "fator_sinaleiro": float(fator_sinaleiro),
            "fator_curva": float(fator_curva),
            "fator_temperatura": float(fator_temperatura),
            "fator_tipo_cliente": float(fator_tipo),
            "fator_tentativas": float(fator_tentativas),
        }

    def _calcular_prioridade(self, cliente: Cliente, score: float) -> str:
        """
        Determina a prioridade P0-P7 do cliente.

        Logica:
          P0 — problema_aberto=True (pula fila — suporte critico)
          P1 — followup_vencido=True E cs_no_prazo=True (atendimento urgente)
          P2-P7 — por faixa de score

        Args:
            cliente: Instancia com flags problema_aberto, followup_vencido, cs_no_prazo.
            score: Score ja calculado (0-100).

        Returns:
            String de prioridade (P0, P1, ..., P7).
        """
        if cliente.problema_aberto:
            return "P0"

        if cliente.followup_vencido and cliente.cs_no_prazo:
            return "P1"

        for label, score_min, score_max in FAIXAS_PRIORIDADE:
            if score_min <= score <= score_max:
                return label

        return "P7"

    def aplicar_e_salvar(self, db: Session, cliente: Cliente) -> dict:
        """
        Calcula score, atualiza campos do cliente e persiste historico.

        Atualiza cliente.score e cliente.prioridade (sem commit — responsabilidade
        do caller para permitir operacoes em batch).

        Registra um ScoreHistorico com todos os fatores para rastreabilidade.

        Args:
            db: Sessao SQLAlchemy ativa.
            cliente: Instancia Cliente a ser atualizada.

        Returns:
            Dict com score, prioridade e fatores (mesmo retorno de calcular()).
        """
        resultado = self.calcular(cliente)

        # Atualizar campos do cliente
        cliente.score = resultado["score"]
        cliente.prioridade = resultado["prioridade"]

        # Registrar snapshot no historico
        hist = ScoreHistorico(
            cnpj=cliente.cnpj,
            data_calculo=date.today(),
            score=resultado["score"],
            prioridade=resultado["prioridade"],
            sinaleiro=cliente.sinaleiro,
            situacao=cliente.situacao,
            fator_fase=resultado["fator_fase"],
            fator_sinaleiro=resultado["fator_sinaleiro"],
            fator_curva=resultado["fator_curva"],
            fator_temperatura=resultado["fator_temperatura"],
            fator_tipo_cliente=resultado["fator_tipo_cliente"],
            fator_tentativas=resultado["fator_tentativas"],
        )
        db.add(hist)

        return resultado


# Instancia singleton — importar e usar diretamente nas rotas e services
score_service = ScoreService()
