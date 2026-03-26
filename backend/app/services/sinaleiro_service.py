"""
CRM VITAO360 — Sinaleiro Engine: calcula saude do cliente e penetracao de redes.

Logica de sinaleiro por cliente:
  PROSPECT / LEAD  -> ROXO   (ainda nao e cliente)
  NOVO             -> VERDE  (cliente recente, sem ciclo)
  INAT.ANT         -> VERMELHO (inativo ha mais de 1 ciclo prolongado)
  Com ciclo_medio:
    dias <= ciclo          -> VERDE
    dias <= ciclo + 30     -> AMARELO
    dias > ciclo + 30      -> VERMELHO
  Fallback sem ciclo:
    dias <= 50  -> VERDE
    dias <= 90  -> AMARELO
    dias > 90   -> VERMELHO

Penetracao de redes:
  potencial = total_lojas * R$525 (ticket ref/mes) * 11 meses
  pct = faturamento_real / potencial * 100
  0%           -> ROXO    (sem penetracao) — cadencia: 1x/sem WA+Lig
  < 40%        -> VERMELHO (penetracao critica) — cadencia: 2x/sem
  40-60%       -> AMARELO (penetracao media)  — cadencia: 1x/sem
  >= 60%       -> VERDE   (boa penetracao)   — cadencia: Mensal

R4 — Two-Base Architecture: este servico nao toca valores monetarios de LOG.
R5 — CNPJ: String(14), zero-padded, nunca Float.
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from backend.app.models.cliente import Cliente
from backend.app.models.rede import Rede

# ---------------------------------------------------------------------------
# Constantes de referencia (extraidas de scripts/motor/sinaleiro_engine.py)
# ---------------------------------------------------------------------------

TICKET_REF_MENSAL: float = 525.0   # R$/mes por loja (ticket medio referencia)
MESES_REF: int = 11                 # Meses ativos por ano (excluindo ferias)

_DIAS_FALLBACK_AMARELO = 50
_DIAS_FALLBACK_VERMELHO = 90
_DIAS_MARGEM_CICLO = 30  # dias alem do ciclo antes de virar VERMELHO


class SinaleiroService:
    """
    Calcula o sinaleiro de clientes e penetracao de redes.

    Uso tipico:
        sinaleiro = sinaleiro_service.calcular(cliente)
        sinaleiro_service.aplicar(db, cliente)
        dados_rede = sinaleiro_service.calcular_penetracao_rede(rede)
    """

    def calcular(self, cliente: Cliente) -> str:
        """
        Calcula o sinaleiro de um cliente individualmente.

        Considera: situacao, dias_sem_compra e ciclo_medio para determinar
        se o cliente esta dentro ou fora do ciclo esperado de compra.

        Args:
            cliente: Instancia Cliente com campos situacao, dias_sem_compra,
                     ciclo_medio preenchidos.

        Returns:
            String com o sinaleiro: 'VERDE', 'AMARELO', 'VERMELHO' ou 'ROXO'.
        """
        situacao = (cliente.situacao or "").strip().upper()

        # Clientes nao ativos: sinaleiro especial
        if situacao in ("PROSPECT", "LEAD"):
            return "ROXO"

        if situacao == "NOVO":
            return "VERDE"

        if situacao == "INAT.ANT":
            return "VERMELHO"

        # Clientes com situacao indefinida e sem dados de compra
        dias = cliente.dias_sem_compra
        if dias is None:
            if situacao in ("INAT.REC", "EM RISCO"):
                return "AMARELO"
            return "VERDE"

        # Com ciclo medio calculado: usar como referencia precisa
        ciclo = cliente.ciclo_medio
        if ciclo and ciclo > 0:
            if dias <= ciclo:
                return "VERDE"
            if dias <= ciclo + _DIAS_MARGEM_CICLO:
                return "AMARELO"
            return "VERMELHO"

        # Fallback para clientes sem ciclo historico
        if dias <= _DIAS_FALLBACK_AMARELO:
            return "VERDE"
        if dias <= _DIAS_FALLBACK_VERMELHO:
            return "AMARELO"
        return "VERMELHO"

    def aplicar(self, db: Session, cliente: Cliente) -> str:
        """
        Calcula o sinaleiro e atualiza o campo cliente.sinaleiro.

        Nao faz commit — responsabilidade do caller para permitir batch.

        Args:
            db: Sessao SQLAlchemy ativa (usado para extensibilidade futura).
            cliente: Instancia Cliente a ser atualizada.

        Returns:
            String com o novo sinaleiro calculado.
        """
        sinaleiro = self.calcular(cliente)
        cliente.sinaleiro = sinaleiro
        return sinaleiro

    def calcular_penetracao_rede(self, rede: Rede) -> dict:
        """
        Calcula o percentual de penetracao e sinaleiro de uma rede.

        Formula:
          potencial_maximo = total_lojas * TICKET_REF_MENSAL * MESES_REF
          pct_penetracao   = faturamento_real / potencial_maximo * 100

        Sinaleiro por faixa de penetracao:
          0%     -> ROXO    (sem faturamento na rede)
          < 40%  -> VERMELHO (baixo aproveitamento)
          < 60%  -> AMARELO  (aproveitamento medio)
          >= 60% -> VERDE    (boa penetracao)

        Args:
            rede: Instancia Rede com total_lojas e faturamento_real preenchidos.

        Returns:
            Dict com: pct_penetracao, sinaleiro, cadencia, potencial_maximo.
        """
        potencial = rede.total_lojas * TICKET_REF_MENSAL * MESES_REF
        pct = (rede.faturamento_real / potencial * 100) if potencial > 0 else 0.0

        if pct == 0:
            sinaleiro = "ROXO"
            cadencia = "1x/sem WA+Lig"
        elif pct < 40:
            sinaleiro = "VERMELHO"
            cadencia = "2x/sem"
        elif pct < 60:
            sinaleiro = "AMARELO"
            cadencia = "1x/sem"
        else:
            sinaleiro = "VERDE"
            cadencia = "Mensal"

        return {
            "pct_penetracao": round(pct, 1),
            "sinaleiro": sinaleiro,
            "cadencia": cadencia,
            "potencial_maximo": round(potencial, 2),
        }


# Instancia singleton — importar e usar diretamente nas rotas e services
sinaleiro_service = SinaleiroService()
