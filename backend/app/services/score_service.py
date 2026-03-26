"""
CRM VITAO360 — Score Engine v2: calcula score ponderado e prioridade P0-P7.

Score 0-100 calculado com 6 fatores ponderados (Score v2 — planilha INTELIGENTE FINAL OK):
  URGENCIA   (30%) — Dias sem compra / ciclo medio
  VALOR      (25%) — Curva ABC + Tipo Cliente
  FOLLOWUP   (20%) — Proximo follow-up vs hoje
  SINAL      (15%) — Temperatura + E-commerce
  TENTATIVA   (5%) — T1/T2/T3/T4
  SITUACAO    (5%) — Situacao Mercos

Prioridade v2 (P0-P7 com labels descritivos):
  P0 IMEDIATA      — problema_aberto=True: pula fila, nao depende de score
  P1 NAMORO NOVO   — pos-venda/CS + cliente novo/ativo + score >= 70
  P2 NEGOCIACAO    — orcamento / em atendimento / cadastro
  P3 PROBLEMA      — suporte bloqueante
  P4 MOMENTO OURO  — inat.rec score alto, ou cliente novo, ou score >= 50
  P5 INAT. RECENTE — inat.rec (score baixo) ou inat.ant score alto
  P6 INAT. ANTIGO  — inat.ant score baixo
  P7 PROSPECCAO    — prospect / lead

Mapeamento para retrocompatibilidade com model.prioridade (String(5)):
  "P0 IMEDIATA"         -> "P0"
  "P1 NAMORO NOVO"      -> "P1"
  "P2 NEGOCIACAO ATIVA" -> "P2"
  "P3 PROBLEMA"         -> "P3"
  "P4 MOMENTO OURO"     -> "P4"
  "P5 INAT. RECENTE"    -> "P5"
  "P6 INAT. ANTIGO"     -> "P6"
  "P7 PROSPECCAO"       -> "P7"

R4 — Two-Base Architecture: este servico nao toca valores monetarios de LOG.
R5 — CNPJ: String(14), zero-padded, nunca Float.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from backend.app.models.cliente import Cliente
from backend.app.models.score_historico import ScoreHistorico

# ---------------------------------------------------------------------------
# Constantes v2 (Score v2 — OFICIAL planilha INTELIGENTE FINAL OK)
# L3: nao alterar sem aprovacao
# ---------------------------------------------------------------------------

PESOS: dict[str, float] = {
    "URGENCIA": 0.30,   # Dias sem compra / ciclo medio
    "VALOR": 0.25,      # Curva ABC + Tipo Cliente
    "FOLLOWUP": 0.20,   # Proximo follow-up vs hoje
    "SINAL": 0.15,      # Temperatura + E-commerce
    "TENTATIVA": 0.05,  # T1/T2/T3/T4
    "SITUACAO": 0.05,   # Situacao Mercos
}

# Mapeamento de label longo -> label curto para persistencia no model (String(5))
_LABEL_CURTO: dict[str, str] = {
    "P0 IMEDIATA": "P0",
    "P1 NAMORO NOVO": "P1",
    "P2 NEGOCIACAO ATIVA": "P2",
    "P3 PROBLEMA": "P3",
    "P4 MOMENTO OURO": "P4",
    "P5 INAT. RECENTE": "P5",
    "P6 INAT. ANTIGO": "P6",
    "P7 PROSPECCAO": "P7",
}

# Emojis que podem aparecer prefixando o campo temperatura (motor legado)
_EMOJIS_TEMPERATURA = ["🔥", "🟡", "❄️", "💀", "🟢", "🔴", "🟣", "⚠️"]


# ---------------------------------------------------------------------------
# Normalizacao de inputs
# ---------------------------------------------------------------------------

def _normalizar(valor: object) -> str:
    """Normaliza valor para lookup: UPPER, sem espacos laterais."""
    if valor is None:
        return ""
    s = str(valor).strip().upper()
    if s in ("NAN", "NONE", "NAT", ""):
        return ""
    return s


def _limpar_temperatura(valor: object) -> str:
    """Remove emojis e espacos extras do campo temperatura antes do lookup."""
    s = _normalizar(valor)
    for emoji in _EMOJIS_TEMPERATURA:
        s = s.replace(emoji, "")
    return s.strip()


# ---------------------------------------------------------------------------
# Calculos dos 6 fatores v2 (L3: nao alterar sem aprovacao)
# ---------------------------------------------------------------------------

def _calcular_urgencia(
    situacao: str,
    dias_sem_compra: Optional[float],
    ciclo_medio: Optional[float],
) -> float:
    """Fator URGENCIA (30%) — urgencia de reativar/atender o cliente.

    - INAT.ANT = 100
    - INAT.REC = 90
    - EM RISCO  = 70
    - PROSPECT/LEAD = 10
    - Com ciclo definido: ratio = dias/ciclo -> >=1.5=100 | >=1.0=60 | >=0.7=40 | <0.7=20
    - Sem ciclo, dias > 50: 60
    - Demais: 30
    """
    sit = situacao.upper() if situacao else ""

    if sit == "INAT.ANT":
        return 100.0
    if sit == "INAT.REC":
        return 90.0
    if sit == "EM RISCO":
        return 70.0
    if sit in ("PROSPECT", "LEAD"):
        return 10.0

    if ciclo_medio and ciclo_medio > 0 and dias_sem_compra is not None:
        ratio = dias_sem_compra / ciclo_medio
        if ratio >= 1.5:
            return 100.0
        if ratio >= 1.0:
            return 60.0
        if ratio >= 0.7:
            return 40.0
        return 20.0

    if dias_sem_compra is not None and dias_sem_compra > 50:
        return 60.0

    return 30.0


def _calcular_valor(curva_abc: str, tipo_cliente: str) -> float:
    """Fator VALOR (25%) — peso financeiro e fidelidade do cliente.

    A + FIDELIZADO/MADURO=100 | A=80 | B + RECORRENTE/FIDELIZADO=60 | B=50 |
    C=20 | sem ABC: FIDELIZADO/MADURO=60 | RECORRENTE=40 | EM_DESENV=20 | default=10
    """
    abc = curva_abc.upper().strip() if curva_abc else ""
    tipo = tipo_cliente.upper().strip() if tipo_cliente else ""

    tipos_premium = {"FIDELIZADO", "MADURO"}
    tipos_recorrente = {"RECORRENTE", "FIDELIZADO"}

    if abc == "A" and tipo in tipos_premium:
        return 100.0
    if abc == "A":
        return 80.0
    if abc == "B" and tipo in tipos_recorrente:
        return 60.0
    if abc == "B":
        return 50.0
    if abc == "C":
        return 20.0

    if tipo in tipos_premium:
        return 60.0
    if tipo == "RECORRENTE":
        return 40.0
    if tipo in ("EM DESENV", "EM DESENVOLVIMENTO"):
        return 20.0
    return 10.0


def _calcular_followup(dias_atraso_followup: Optional[float]) -> float:
    """Fator FOLLOWUP (20%) — urgencia do proximo contato agendado.

    dias_atraso_followup: positivo=atrasado, negativo=futuro, None=sem FU.
    Sem FU=50 | >=7=100 | >=3=80 | >=1=70 | 0=60 | >=-3=40 | mais futuro=20
    """
    if dias_atraso_followup is None:
        return 50.0

    d = dias_atraso_followup
    if d >= 7:
        return 100.0
    if d >= 3:
        return 80.0
    if d >= 1:
        return 70.0
    if d >= 0:
        return 60.0
    if d >= -3:
        return 40.0
    return 20.0


def _calcular_sinal(temperatura: str, ecommerce_carrinho: float = 0.0) -> float:
    """Fator SINAL (15%) — temperatura de engajamento + sinais digitais.

    CRITICO=90 | QUENTE+carrinho=100 | QUENTE=80 | MORNO+carrinho=70 |
    MORNO=40 | FRIO=10 | PERDIDO=0
    """
    temp = temperatura.upper().strip() if temperatura else ""
    carrinho = float(ecommerce_carrinho) if ecommerce_carrinho else 0.0

    if temp in ("CRITICO", "CRÍTICO"):
        return 90.0
    if temp == "QUENTE":
        return 100.0 if carrinho > 0 else 80.0
    if temp == "MORNO":
        return 70.0 if carrinho > 0 else 40.0
    if temp == "FRIO":
        return 10.0
    if temp == "PERDIDO":
        return 0.0
    return 0.0


def _calcular_tentativa(tentativas: str) -> float:
    """Fator TENTATIVA (5%) — persistencia nas tentativas de contato.

    T4+=100 | T3=50 | T1/T2=10 | demais=0
    """
    tent = tentativas.upper().strip() if tentativas else ""

    if tent == "T4" or (tent.startswith("T") and len(tent) >= 2 and tent[1:].isdigit() and int(tent[1:]) >= 4):
        return 100.0
    if tent == "T3":
        return 50.0
    if tent in ("T1", "T2"):
        return 10.0
    return 0.0


def _calcular_situacao_fator(situacao: str) -> float:
    """Fator SITUACAO (5%) — situacao cadastral no Mercos.

    EM RISCO=80 | ATIVO=40 | INAT.REC/INAT.ANT=20 | PROSPECT=10 | demais=0
    """
    sit = situacao.upper().strip() if situacao else ""

    if sit == "EM RISCO":
        return 80.0
    if sit == "ATIVO":
        return 40.0
    if sit in ("INAT.REC", "INAT.ANT"):
        return 20.0
    if sit == "PROSPECT":
        return 10.0
    return 0.0


# ---------------------------------------------------------------------------
# Logica de prioridade v2
# ---------------------------------------------------------------------------

def _prioridade_v2(
    situacao: str,
    resultado: str,
    tipo_cliente: str,
    score: float,
    problema_aberto: bool = False,
) -> str:
    """Atribui prioridade P0-P7 conforme regras v2 da planilha Score v2.

    Ordem de avaliacao (L3 — nao alterar sem aprovacao):
      P0 IMEDIATA:         problema_aberto=True (pula fila, nao depende de score)
      P3 PROBLEMA:         SUPORTE
      P1 NAMORO NOVO:      POS-VENDA/CS + NOVO/ATIVO + Score >= 70
      P2 NEGOCIACAO ATIVA: ORCAMENTO / EM ATENDIMENTO / CADASTRO
      P4/P5 inat.rec:      INAT.REC + Score >= 75 -> P4, senao P5
      P5/P6 inat.ant:      INAT.ANT + Score >= 80 -> P5, senao P6
      P7 PROSPECCAO:       PROSPECT / LEAD
      P4 MOMENTO OURO:     NOVO ou Score >= 50
      P5 INAT. RECENTE:    default
    """
    sit = situacao.upper().strip() if situacao else ""
    res = resultado.upper().strip() if resultado else ""
    tipo = tipo_cliente.upper().strip() if tipo_cliente else ""

    # P0 IMEDIATA — problema aberto: pula fila, nao depende de score
    if problema_aberto:
        return "P0 IMEDIATA"

    # P3 PROBLEMA — suporte bloqueante
    if res == "SUPORTE" or sit == "SUPORTE":
        return "P3 PROBLEMA"

    # P1 NAMORO NOVO — pos-venda ou CS em cliente novo/ativo com score alto
    tipos_novos_ativos = {"NOVO", "ATIVO"}
    fases_pos_venda = {"POS-VENDA", "POS VENDA", "CS"}
    if res in fases_pos_venda and tipo in tipos_novos_ativos and score >= 70:
        return "P1 NAMORO NOVO"

    # P2 NEGOCIACAO ATIVA — em negociacao / orcamento / cadastro
    fases_negociacao = {"ORCAMENTO", "ORÇAMENTO", "EM ATENDIMENTO", "CADASTRO"}
    if res in fases_negociacao or sit in fases_negociacao:
        return "P2 NEGOCIACAO ATIVA"

    # P4/P5 — inativos recentes
    if sit == "INAT.REC":
        if score >= 75:
            return "P4 MOMENTO OURO"
        return "P5 INAT. RECENTE"

    # P5/P6 — inativos antigos
    if sit == "INAT.ANT":
        if score >= 80:
            return "P5 INAT. RECENTE"
        return "P6 INAT. ANTIGO"

    # P7 PROSPECCAO — clientes sem historico
    if sit in ("PROSPECT", "LEAD") or tipo in ("PROSPECT", "LEAD"):
        return "P7 PROSPECCAO"

    # P4 MOMENTO OURO — cliente novo com qualquer score
    if tipo == "NOVO" or sit == "NOVO":
        return "P4 MOMENTO OURO"

    # P4 MOMENTO OURO — score suficientemente alto
    if score >= 50:
        return "P4 MOMENTO OURO"

    # Default
    return "P5 INAT. RECENTE"


def _label_curto(prioridade_longa: str) -> str:
    """Converte label longo em label curto para persistencia no model (String(5))."""
    return _LABEL_CURTO.get(prioridade_longa, prioridade_longa[:2] if len(prioridade_longa) >= 2 else prioridade_longa)


# ---------------------------------------------------------------------------
# Servico principal
# ---------------------------------------------------------------------------

class ScoreService:
    """
    Calcula o score ponderado (0-100) e prioridade v2 (P1-P7) de um cliente.

    Score v2 usa 6 fatores: URGENCIA(30%), VALOR(25%), FOLLOWUP(20%),
    SINAL(15%), TENTATIVA(5%), SITUACAO(5%).

    Inputs do model Cliente mapeados:
      situacao         -> URGENCIA + SITUACAO
      curva_abc        -> VALOR
      tipo_cliente     -> VALOR
      temperatura      -> SINAL
      tentativas       -> TENTATIVA
      dias_sem_compra  -> URGENCIA
      ciclo_medio      -> URGENCIA
      followup_dias    -> FOLLOWUP (convertido: positivo = dias de atraso)
      resultado        -> Prioridade v2

    Uso tipico:
        resultado = score_service.calcular(cliente)
        score_service.aplicar_e_salvar(db, cliente)
    """

    def calcular(self, cliente: Cliente) -> dict:
        """
        Calcula score 0-100 com 6 fatores ponderados v2.

        Se cliente.problema_aberto=True, prioridade retorna "P0 IMEDIATA"
        independente do score calculado.

        Args:
            cliente: Instancia Cliente com os campos de inteligencia preenchidos.

        Returns:
            Dict com chaves: score, prioridade (label longo), prioridade_curta,
            fator_urgencia, fator_valor, fator_followup, fator_sinal,
            fator_tentativa, fator_situacao.
            Mantidos por retrocompatibilidade: fator_fase, fator_sinaleiro,
            fator_curva, fator_temperatura, fator_tipo_cliente, fator_tentativas.
        """
        temp = _limpar_temperatura(cliente.temperatura)
        situacao = _normalizar(cliente.situacao)
        curva_abc = _normalizar(cliente.curva_abc)
        tipo_cliente = _normalizar(cliente.tipo_cliente)
        tentativas = _normalizar(cliente.tentativas)
        resultado = _normalizar(cliente.resultado)

        # Extrair inputs numericos do model
        try:
            dias_sem_compra: Optional[float] = float(cliente.dias_sem_compra) if cliente.dias_sem_compra is not None else None
        except (TypeError, ValueError):
            dias_sem_compra = None

        try:
            ciclo_medio: Optional[float] = float(cliente.ciclo_medio) if cliente.ciclo_medio is not None else None
        except (TypeError, ValueError):
            ciclo_medio = None

        # followup_dias: dias ate proximo FU (positivo = atrasado se > 0, negativo = futuro)
        # O model armazena "dias de follow-up" — convertemos para "atraso"
        # Se followup_dias = 0 -> FU vencido/hoje
        # Se followup_dias > 0 -> FU no futuro (negativo no atraso)
        # Sem followup_dias -> None (sem FU agendado)
        try:
            fu_dias: Optional[float] = float(cliente.followup_dias) if cliente.followup_dias is not None else None
            # followup_dias no model = dias restantes para o proximo FU
            # dias_atraso = negativo (futuro) ou 0 (hoje)
            dias_atraso_followup: Optional[float] = -fu_dias if fu_dias is not None else None
        except (TypeError, ValueError):
            dias_atraso_followup = None

        # Calcular os 6 fatores v2
        fator_urgencia = _calcular_urgencia(situacao, dias_sem_compra, ciclo_medio)
        fator_valor = _calcular_valor(curva_abc, tipo_cliente)
        fator_followup = _calcular_followup(dias_atraso_followup)
        fator_sinal = _calcular_sinal(temp, 0.0)
        fator_tentativa = _calcular_tentativa(tentativas)
        fator_situacao = _calcular_situacao_fator(situacao)

        score = round(
            fator_urgencia * PESOS["URGENCIA"]
            + fator_valor * PESOS["VALOR"]
            + fator_followup * PESOS["FOLLOWUP"]
            + fator_sinal * PESOS["SINAL"]
            + fator_tentativa * PESOS["TENTATIVA"]
            + fator_situacao * PESOS["SITUACAO"],
            1,
        )
        score = round(min(max(score, 0.0), 100.0), 1)

        # Prioridade v2 (P0 pula fila se problema_aberto=True)
        problema_aberto: bool = bool(cliente.problema_aberto)
        prioridade_longa = _prioridade_v2(situacao, resultado, tipo_cliente, score, problema_aberto)
        prioridade_curta = _label_curto(prioridade_longa)

        return {
            "score": score,
            "prioridade": prioridade_longa,
            "prioridade_curta": prioridade_curta,
            # Fatores v2
            "fator_urgencia": float(fator_urgencia),
            "fator_valor": float(fator_valor),
            "fator_followup": float(fator_followup),
            "fator_sinal": float(fator_sinal),
            "fator_tentativa": float(fator_tentativa),
            "fator_situacao": float(fator_situacao),
            # Aliases retrocompativeis (mapeados dos fatores v2 mais proximos)
            "fator_fase": float(fator_urgencia),       # urgencia substitui fase
            "fator_sinaleiro": float(fator_sinal),     # sinal substitui sinaleiro
            "fator_curva": float(fator_valor),         # valor inclui curva ABC
            "fator_temperatura": float(fator_sinal),   # sinal inclui temperatura
            "fator_tipo_cliente": float(fator_valor),  # valor inclui tipo_cliente
            "fator_tentativas": float(fator_tentativa),
        }

    def aplicar_e_salvar(self, db: Session, cliente: Cliente) -> dict:
        """
        Calcula score, atualiza campos do cliente e persiste historico.

        Atualiza cliente.score e cliente.prioridade (label curto, ex: "P1").
        Registra ScoreHistorico com todos os fatores para rastreabilidade.

        Args:
            db: Sessao SQLAlchemy ativa.
            cliente: Instancia Cliente a ser atualizada.

        Returns:
            Dict com score, prioridade (label longo) e fatores.
        """
        resultado = self.calcular(cliente)

        # Atualizar campos do cliente
        cliente.score = resultado["score"]
        # Salvar label curto no model (String(5) nao comporta label longo)
        cliente.prioridade = resultado["prioridade_curta"]

        # Registrar snapshot no historico
        hist = ScoreHistorico(
            cnpj=cliente.cnpj,
            data_calculo=date.today(),
            score=resultado["score"],
            prioridade=resultado["prioridade_curta"],
            sinaleiro=cliente.sinaleiro,
            situacao=cliente.situacao,
            fator_urgencia=resultado["fator_urgencia"],
            fator_valor=resultado["fator_valor"],
            fator_followup=resultado["fator_followup"],
            fator_sinal=resultado["fator_sinal"],
            fator_tentativa=resultado["fator_tentativa"],
            fator_situacao=resultado["fator_situacao"],
        )
        db.add(hist)

        return resultado


# Instancia singleton — importar e usar diretamente nas rotas e services
score_service = ScoreService()
