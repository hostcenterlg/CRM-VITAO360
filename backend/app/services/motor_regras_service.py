"""
CRM VITAO360 — Servico do Motor de Regras.

Port da logica de scripts/motor_regras.py para uso no backend FastAPI.
Duas estrategias de resolucao:
  - PRIMARIA : Buscar na tabela regras_motor por chave "SITUACAO|RESULTADO"
  - FALLBACK  : Importar e chamar motor_de_regras() de scripts/motor_regras.py

R4 — Two-Base Architecture:
  Este servico cria registros de LOG (LogInteracao). NUNCA inserir
  campo de valor monetario em LogInteracao. Qualquer R$ aqui = violacao.

R5 — CNPJ: String(14), zero-padded, NUNCA Float.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.models.regra_motor import RegraMotor
from backend.app.models.log_interacao import LogInteracao
from backend.app.models.cliente import Cliente

# Adicionar raiz do projeto ao sys.path para importar scripts/ como fallback
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

try:
    from scripts.motor_regras import motor_de_regras as _motor_original
    _FALLBACK_DISPONIVEL = True
except ImportError:
    _FALLBACK_DISPONIVEL = False


class MotorRegrasService:
    """
    Encapsula a logica do Motor de Regras CRM.

    Hierarquia de resolucao:
      1. Tabela regras_motor (seed de 68 regras pre-calculadas)
      2. scripts/motor_regras.py (fallback direto para cobertura total)

    Resultado: dict com 9 dimensoes calculadas automaticamente.
    """

    # Sequencia padrao de tentativas de contato
    _SEQ_TENTATIVA: dict[str | None, str] = {
        None: "T1",
        "T1": "T2",
        "T2": "T3",
        "T3": "T4",
        "T4": "NUTRIÇÃO",
    }

    # Resultados que avancam tentativa (sem resposta do cliente)
    _RESULTADOS_SEM_RESPOSTA = {"NÃO ATENDE", "NÃO RESPONDE", "RECUSOU LIGAÇÃO"}

    def aplicar(
        self,
        db: Session,
        situacao: str,
        resultado: str,
        estagio_anterior: str | None = None,
        tentativa_anterior: str | None = None,
    ) -> dict:
        """
        Aplica o motor de regras para a combinacao situacao + resultado.

        Tenta a tabela regras_motor primeiro. Se nao encontrar, usa o
        motor original de scripts/motor_regras.py como fallback.

        Args:
            db: Sessao SQLAlchemy ativa.
            situacao: Situacao atual do cliente (ATIVO, PROSPECT, INAT.REC, ...).
            resultado: Resultado da interacao (VENDA / PEDIDO, ORÇAMENTO, ...).
            estagio_anterior: Estagio de funil anterior (usado para NÃO ATENDE).
            tentativa_anterior: Ultima tentativa registrada (T1, T2, T3, T4).

        Returns:
            Dict com 9 dimensoes: estagio_funil, fase, tipo_contato, acao_futura,
            temperatura, follow_up_dias, grupo_dash, tipo_acao, tentativa.
        """
        # Estrategia PRIMARIA: tabela regras_motor
        chave = f"{situacao}|{resultado}"
        regra = db.query(RegraMotor).filter(RegraMotor.chave == chave).first()

        if regra:
            # Calcular tentativa separadamente pois depende do historico
            tentativa = None
            if resultado in self._RESULTADOS_SEM_RESPOSTA:
                tentativa = self._avancar_tentativa(tentativa_anterior)

            return {
                "estagio_funil": regra.estagio_funil,
                "fase": regra.fase,
                "tipo_contato": regra.tipo_contato,
                "acao_futura": regra.acao_futura,
                "temperatura": regra.temperatura,
                "follow_up_dias": regra.follow_up_dias,
                "grupo_dash": regra.grupo_dash or "",
                "tipo_acao": regra.tipo_acao,
                "tentativa": tentativa,
            }

        # Estrategia FALLBACK: motor original em scripts/
        if _FALLBACK_DISPONIVEL:
            r = _motor_original(situacao, resultado, estagio_anterior, tentativa_anterior)
            return {
                "estagio_funil": r.get("estagio_funil", ""),
                "fase": r.get("fase", ""),
                "tipo_contato": r.get("tipo_contato", ""),
                "acao_futura": r.get("acao_futura", ""),
                "temperatura": r.get("temperatura", ""),
                "follow_up_dias": r.get("follow_up_dias", 0),
                "grupo_dash": r.get("grupo_dash", ""),
                "tipo_acao": r.get("tipo_acao"),
                "tentativa": r.get("tentativa"),
            }

        # Sem fallback: retornar campos basicos calculados localmente
        return self._resolver_sem_fallback(situacao, resultado, estagio_anterior, tentativa_anterior)

    def registrar_atendimento(
        self,
        db: Session,
        cnpj: str,
        resultado: str,
        descricao: str,
        consultor: str,
        user_id: int | None = None,
    ) -> LogInteracao:
        """
        Fluxo completo de registro de atendimento:
          1. Busca cliente por CNPJ
          2. Aplica motor de regras com contexto do cliente
          3. Cria LogInteracao (R4: NUNCA campo de valor monetario)
          4. Atualiza campos de inteligencia do cliente
          5. Retorna o log criado (sem commit — responsabilidade do caller)

        Args:
            db: Sessao SQLAlchemy ativa.
            cnpj: CNPJ do cliente (14 digitos, string).
            resultado: Resultado da interacao.
            descricao: Observacoes livres do consultor.
            consultor: Nome do consultor (MANU, LARISSA, DAIANE, ...).
            user_id: ID do usuario autenticado para auditoria.

        Returns:
            LogInteracao recém criado (ainda nao commitado).

        Raises:
            ValueError: Se o cliente com o CNPJ informado nao existir.
        """
        # Passo 1: Buscar cliente para obter contexto atual
        cliente = db.query(Cliente).filter(Cliente.cnpj == cnpj).first()
        if not cliente:
            raise ValueError(f"Cliente com CNPJ {cnpj} nao encontrado")

        # Passo 2: Aplicar motor com contexto real do cliente
        campos = self.aplicar(
            db=db,
            situacao=cliente.situacao or "PROSPECT",
            resultado=resultado,
            estagio_anterior=cliente.estagio_funil,
            tentativa_anterior=cliente.tentativas,
        )

        # Passo 3: Criar LogInteracao
        # R4 — Two-Base: NUNCA valor monetario aqui.
        # Esta tabela e a metade LOG da arquitetura.
        log = LogInteracao(
            cnpj=cnpj,
            data_interacao=datetime.now(timezone.utc),
            consultor=consultor,
            resultado=resultado,
            descricao=descricao or "",
            estagio_funil=campos["estagio_funil"],
            fase=campos["fase"],
            tipo_contato=campos["tipo_contato"],
            acao_futura=campos["acao_futura"],
            temperatura=campos["temperatura"],
            follow_up_dias=campos["follow_up_dias"],
            grupo_dash=campos["grupo_dash"],
            tentativa=campos["tentativa"],
            created_by=user_id,
        )
        db.add(log)

        # Passo 4: Atualizar campos de inteligencia do cliente
        cliente.temperatura = campos["temperatura"]
        cliente.fase = campos["fase"]
        cliente.estagio_funil = campos["estagio_funil"]
        cliente.acao_futura = campos["acao_futura"]
        cliente.followup_dias = campos["follow_up_dias"]
        cliente.tentativas = campos["tentativa"]
        cliente.resultado = resultado
        cliente.tipo_contato = campos["tipo_contato"]
        if campos.get("tipo_acao"):
            cliente.tipo_acao = campos["tipo_acao"]

        # Passo 5: Recalcular sinaleiro e score apos cada atendimento
        # Import local para evitar import circular entre services
        from backend.app.services.sinaleiro_service import sinaleiro_service  # noqa: PLC0415
        from backend.app.services.score_service import score_service  # noqa: PLC0415

        sinaleiro_service.aplicar(db, cliente)
        score_service.aplicar_e_salvar(db, cliente)

        # flush para gerar log.id sem commit
        db.flush()
        return log

    def _avancar_tentativa(self, anterior: str | None) -> str:
        """
        Avanca a sequencia de tentativas: None → T1 → T2 → T3 → T4 → NUTRIÇÃO.

        Args:
            anterior: Ultima tentativa registrada ou None para primeira.

        Returns:
            Proxima tentativa na sequencia.
        """
        return self._SEQ_TENTATIVA.get(anterior, "T1")

    # Constantes locais para o fallback de emergencia (sem imports circulares)
    _FOLLOW_UP_DIAS_FALLBACK: dict[str, int] = {
        "EM ATENDIMENTO": 2, "ORÇAMENTO": 1, "CADASTRO": 2,
        "VENDA / PEDIDO": 45, "RELACIONAMENTO": 7,
        "FOLLOW UP 7": 7, "FOLLOW UP 15": 15, "SUPORTE": 0,
        "NÃO ATENDE": 1, "NÃO RESPONDE": 1,
        "RECUSOU LIGAÇÃO": 2, "PERDA / FECHOU LOJA": 0,
    }
    _GRUPO_DASH_FALLBACK: dict[str, str] = {
        "EM ATENDIMENTO": "FUNIL", "ORÇAMENTO": "FUNIL",
        "CADASTRO": "FUNIL", "VENDA / PEDIDO": "FUNIL",
        "RELACIONAMENTO": "RELAC.", "FOLLOW UP 7": "RELAC.",
        "FOLLOW UP 15": "RELAC.", "SUPORTE": "RELAC.",
        "NÃO ATENDE": "NÃO VENDA", "NÃO RESPONDE": "NÃO VENDA",
        "RECUSOU LIGAÇÃO": "NÃO VENDA", "PERDA / FECHOU LOJA": "NÃO VENDA",
    }

    def _resolver_sem_fallback(
        self,
        situacao: str,
        resultado: str,
        estagio_anterior: str | None,
        tentativa_anterior: str | None,
    ) -> dict:
        """
        Resolucao basica quando nao ha regra na tabela e o modulo
        scripts/motor_regras.py nao esta disponivel.

        Cobre os resultados mais criticos para garantir operacao minima.
        Usa constantes locais para evitar importacao circular.
        """
        tentativa = None
        if resultado in self._RESULTADOS_SEM_RESPOSTA:
            tentativa = self._avancar_tentativa(tentativa_anterior)

        return {
            "estagio_funil": estagio_anterior or "EM ATENDIMENTO",
            "fase": "EM ATENDIMENTO",
            "tipo_contato": "LIGAÇÃO",
            "acao_futura": situacao,
            "temperatura": "\U0001f7e1 MORNO",  # 🟡 MORNO
            "follow_up_dias": self._FOLLOW_UP_DIAS_FALLBACK.get(resultado, 7),
            "grupo_dash": self._GRUPO_DASH_FALLBACK.get(resultado, ""),
            "tipo_acao": None,
            "tentativa": tentativa,
        }


# Instancia singleton — importar e usar diretamente nas rotas
motor_service = MotorRegrasService()
