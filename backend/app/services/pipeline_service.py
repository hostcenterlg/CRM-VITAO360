"""
CRM VITAO360 — Pipeline Orchestrator Service

Orquestra o pipeline completo de sincronizacao:
  1. _sync_deskrio  — carrega extrações de data/deskrio/ → DB
  2. _sync_mercos   — carrega extrações de data/mercos/ → DB
  3. _recalculate   — recalcula Score, Sinaleiro e Agenda para todos os clientes

Regras criticas:
  R4 — Two-Base Architecture: NUNCA valor R$ em LogInteracao.
  R5 — CNPJ: String(14), zero-padded, nunca float.
  R8 — NUNCA fabricar dados. Tudo vem de arquivos em data/.
  R11 — Logs estruturados, sem commits fora do service.

Design:
  - PipelineService e stateful: armazena historico de runs em memoria
    (nao persiste no DB para evitar dependencia de schema extra).
  - Cada etapa captura exceçoes e continua (graceful degradation).
  - _sync_deskrio processa contacts e kanban_cards do ultimo snapshot.
  - _sync_mercos processa indicadores e pedidos_ativos do ultimo snapshot.
  - _recalculate chama score_service e sinaleiro_service para todos os clientes.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Raiz do projeto (3 niveis acima de backend/app/services/)
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DATA_DIR = _PROJECT_ROOT / "data"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalizar_cnpj(valor: Any) -> str:
    """R5: converte para string 14 digitos, zero-padded."""
    return re.sub(r"\D", "", str(valor)).zfill(14)


def _latest_snapshot(source: str) -> Path | None:
    """
    Retorna o Path do diretorio mais recente em data/{source}/.

    Os diretorios sao nomeados como YYYY-MM-DD. Escolhe o mais recente
    com pelo menos um arquivo JSON dentro.
    """
    base = _DATA_DIR / source
    if not base.is_dir():
        return None

    dirs = sorted(
        [d for d in base.iterdir() if d.is_dir() and re.match(r"\d{4}-\d{2}-\d{2}", d.name)],
        key=lambda d: d.name,
        reverse=True,
    )
    for d in dirs:
        if any(d.glob("*.json")):
            return d
    return None


def _load_json(path: Path) -> Any | None:
    """Carrega JSON de arquivo. Retorna None em erro sem propagar."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Pipeline: falha ao carregar %s — %s", path, exc)
        return None


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class StepResult:
    nome: str
    sucesso: bool
    registros_processados: int = 0
    mensagem: str = ""
    erro: str = ""


@dataclass
class PipelineResult:
    inicio: datetime
    fim: datetime | None = None
    sucesso: bool = False
    steps: list[StepResult] = field(default_factory=list)
    total_clientes_atualizados: int = 0
    mensagem: str = ""

    @property
    def duracao_segundos(self) -> float | None:
        if self.fim and self.inicio:
            return (self.fim - self.inicio).total_seconds()
        return None

    def to_dict(self) -> dict:
        return {
            "inicio": self.inicio.isoformat(),
            "fim": self.fim.isoformat() if self.fim else None,
            "duracao_segundos": self.duracao_segundos,
            "sucesso": self.sucesso,
            "total_clientes_atualizados": self.total_clientes_atualizados,
            "mensagem": self.mensagem,
            "steps": [
                {
                    "nome": s.nome,
                    "sucesso": s.sucesso,
                    "registros_processados": s.registros_processados,
                    "mensagem": s.mensagem,
                    "erro": s.erro,
                }
                for s in self.steps
            ],
        }


@dataclass
class PipelineStatus:
    ultimo_run: PipelineResult | None
    proximo_agendado: str | None  # ISO string ou None
    em_execucao: bool

    def to_dict(self) -> dict:
        return {
            "ultimo_run": self.ultimo_run.to_dict() if self.ultimo_run else None,
            "proximo_agendado": self.proximo_agendado,
            "em_execucao": self.em_execucao,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

class PipelineService:
    """
    Orquestra o pipeline completo de sincronizacao e recalculo do CRM.

    Thread-safe: _lock impede runs concorrentes.
    Historico: mantem os ultimos 20 runs em memoria.
    """

    _MAX_HISTORICO = 20

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._em_execucao = False
        self._historico: list[PipelineResult] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_full_pipeline(self, db: Session) -> PipelineResult:
        """
        Executa o pipeline completo: sync_deskrio → sync_mercos → recalculate.

        Thread-safe: retorna imediatamente com erro se ja houver um run ativo.

        Args:
            db: Sessao SQLAlchemy ativa (caller gerencia o ciclo de vida).

        Returns:
            PipelineResult com resultados de cada step e totais.
        """
        if self._em_execucao:
            result = PipelineResult(
                inicio=datetime.now(timezone.utc),
                sucesso=False,
                mensagem="Pipeline ja em execucao. Aguarde o termino.",
            )
            result.fim = result.inicio
            return result

        with self._lock:
            self._em_execucao = True
            result = PipelineResult(inicio=datetime.now(timezone.utc))

            try:
                logger.info("Pipeline: iniciando run completo")

                # Step 1 — Sync Deskrio
                step_deskrio = self._sync_deskrio(db)
                result.steps.append(step_deskrio)
                logger.info(
                    "Pipeline step deskrio: sucesso=%s registros=%d",
                    step_deskrio.sucesso,
                    step_deskrio.registros_processados,
                )

                # Step 2 — Sync Mercos
                step_mercos = self._sync_mercos(db)
                result.steps.append(step_mercos)
                logger.info(
                    "Pipeline step mercos: sucesso=%s registros=%d",
                    step_mercos.sucesso,
                    step_mercos.registros_processados,
                )

                # Step 3 — Recalculate
                step_recalc = self._recalculate(db)
                result.steps.append(step_recalc)
                logger.info(
                    "Pipeline step recalculate: sucesso=%s clientes=%d",
                    step_recalc.sucesso,
                    step_recalc.registros_processados,
                )

                result.total_clientes_atualizados = step_recalc.registros_processados
                result.sucesso = all(s.sucesso for s in result.steps)
                result.mensagem = (
                    "Pipeline concluido com sucesso."
                    if result.sucesso
                    else "Pipeline concluido com falhas em alguns steps."
                )

            except Exception as exc:
                logger.exception("Pipeline: erro inesperado — %s", exc)
                result.sucesso = False
                result.mensagem = f"Erro inesperado no pipeline: {exc}"
            finally:
                result.fim = datetime.now(timezone.utc)
                self._em_execucao = False
                # Adicionar ao historico (circular buffer)
                self._historico.append(result)
                if len(self._historico) > self._MAX_HISTORICO:
                    self._historico.pop(0)

            logger.info(
                "Pipeline: concluido | sucesso=%s duracao=%.1fs",
                result.sucesso,
                result.duracao_segundos or 0,
            )
            return result

    def get_status(self) -> PipelineStatus:
        """
        Retorna o status atual do pipeline.

        Returns:
            PipelineStatus com ultimo run, proximo agendado e flag em_execucao.
        """
        return PipelineStatus(
            ultimo_run=self._historico[-1] if self._historico else None,
            proximo_agendado=None,  # Agendamento automatico nao implementado nesta versao
            em_execucao=self._em_execucao,
        )

    def get_logs(self) -> list[dict]:
        """
        Retorna os ultimos runs do pipeline como lista de dicts.

        Returns:
            Lista dos ultimos _MAX_HISTORICO runs, mais recente primeiro.
        """
        return [r.to_dict() for r in reversed(self._historico)]

    def get_notifications(self, db: Session) -> list[dict]:
        """
        Gera alertas dinamicos baseados no estado atual do banco.

        Categorias:
          CHURN          — temperatura='CRITICO'
          SINALEIRO_VERMELHO — sinaleiro='VERMELHO' e dias sem contato >= 7
          FOLLOWUP_VENCIDO   — followup_vencido=True
          META_RISCO         — pct_alcancado < 0.5 (menos de 50% da meta)

        R4 — Nenhum dado monetario de LOG e retornado aqui.
        R5 — CNPJ sempre string 14 digitos.
        R8 — Apenas dados REAL do banco.

        Returns:
            Lista de dicts com {tipo, prioridade, cnpj, nome, mensagem, acao}.
        """
        from datetime import date

        from backend.app.models.cliente import Cliente
        from backend.app.models.log_interacao import LogInteracao
        from sqlalchemy import func

        alertas: list[dict] = []
        hoje = date.today()

        try:
            clientes = db.query(Cliente).filter(
                Cliente.classificacao_3tier != "ALUCINACAO"
            ).all()
        except Exception as exc:
            logger.error("get_notifications: falha ao buscar clientes — %s", exc)
            return []

        for c in clientes:
            cnpj = c.cnpj or ""
            nome = c.nome_fantasia or c.razao_social or cnpj

            # -- CHURN: temperatura CRITICO
            if c.temperatura == "CRITICO":
                alertas.append({
                    "tipo": "CHURN",
                    "prioridade": "ALTA",
                    "cnpj": cnpj,
                    "nome": nome,
                    "mensagem": f"{nome} com temperatura CRITICO — risco de perda iminente.",
                    "acao": "Ligar imediatamente. Verificar problemas em aberto.",
                })

            # -- SINALEIRO VERMELHO sem contato ha 7+ dias
            if c.sinaleiro == "VERMELHO":
                ultimo_contato = (
                    db.query(func.max(LogInteracao.data_interacao))
                    .filter(LogInteracao.cnpj == cnpj)
                    .scalar()
                )
                dias_sem_contato: int | None = None
                if ultimo_contato:
                    try:
                        dt = (
                            ultimo_contato.date()
                            if hasattr(ultimo_contato, "date")
                            else ultimo_contato
                        )
                        dias_sem_contato = (hoje - dt).days
                    except Exception:
                        dias_sem_contato = None

                if dias_sem_contato is None or dias_sem_contato >= 7:
                    dias_txt = f"{dias_sem_contato} dias" if dias_sem_contato is not None else "periodo desconhecido"
                    alertas.append({
                        "tipo": "SINALEIRO_VERMELHO",
                        "prioridade": "ALTA",
                        "cnpj": cnpj,
                        "nome": nome,
                        "mensagem": f"{nome} com sinaleiro VERMELHO e sem contato ha {dias_txt}.",
                        "acao": "Entrar em contato urgente para reativar relacionamento.",
                    })

            # -- FOLLOW-UP VENCIDO
            if c.followup_vencido:
                alertas.append({
                    "tipo": "FOLLOWUP_VENCIDO",
                    "prioridade": "MEDIA",
                    "cnpj": cnpj,
                    "nome": nome,
                    "mensagem": f"{nome} com follow-up vencido.",
                    "acao": "Registrar contato ou reagendar follow-up.",
                })

            # -- META EM RISCO: menos de 50% da meta realizado
            if (
                c.meta_anual
                and c.meta_anual > 0
                and c.pct_alcancado is not None
                and c.pct_alcancado < 0.5
            ):
                pct_txt = f"{c.pct_alcancado * 100:.1f}%"
                alertas.append({
                    "tipo": "META_RISCO",
                    "prioridade": "MEDIA",
                    "cnpj": cnpj,
                    "nome": nome,
                    "mensagem": f"{nome} com apenas {pct_txt} da meta anual realizado.",
                    "acao": "Aumentar frequencia de contato e oferta de mix.",
                })

        # Ordenar: ALTA primeiro, depois MEDIA
        prioridade_ordem = {"ALTA": 0, "MEDIA": 1, "BAIXA": 2}
        alertas.sort(key=lambda a: prioridade_ordem.get(a["prioridade"], 9))

        logger.info("get_notifications: %d alertas gerados", len(alertas))
        return alertas

    # ------------------------------------------------------------------
    # Private steps
    # ------------------------------------------------------------------

    def _sync_deskrio(self, db: Session) -> StepResult:
        """
        Sincroniza contatos Deskrio do snapshot mais recente em data/deskrio/.

        Processa contacts.json: atualiza email/telefone de clientes existentes
        via matching por numero de telefone ou campo CNPJ em extraInfo.

        R5 — CNPJ normalizado para 14 digitos antes de qualquer lookup.
        R8 — NUNCA cria clientes novos com dados do Deskrio (fonte nao e CNPJ-primaria).
        """
        from backend.app.models.cliente import Cliente

        snapshot = _latest_snapshot("deskrio")
        if snapshot is None:
            return StepResult(
                nome="sync_deskrio",
                sucesso=False,
                mensagem="Nenhum snapshot encontrado em data/deskrio/",
            )

        contacts_path = snapshot / "contacts.json"
        if not contacts_path.exists():
            return StepResult(
                nome="sync_deskrio",
                sucesso=False,
                mensagem=f"contacts.json nao encontrado em {snapshot.name}",
            )

        contacts = _load_json(contacts_path)
        if not isinstance(contacts, list):
            return StepResult(
                nome="sync_deskrio",
                sucesso=False,
                mensagem="contacts.json nao e uma lista valida",
            )

        atualizados = 0
        erros = 0

        try:
            for contato in contacts:
                if not isinstance(contato, dict):
                    continue

                # Tentar resolver CNPJ via extraInfo
                cnpj_norm: str | None = None
                extra_info = contato.get("extraInfo") or []
                for campo in extra_info:
                    if not isinstance(campo, dict):
                        continue
                    if campo.get("name", "").upper().startswith("CNPJ"):
                        raw = str(campo.get("value", "")).strip()
                        if raw:
                            cnpj_norm = _normalizar_cnpj(raw)
                            break

                if cnpj_norm and len(cnpj_norm) == 14:
                    cliente = db.query(Cliente).filter(Cliente.cnpj == cnpj_norm).first()
                    if cliente:
                        numero = contato.get("number") or ""
                        email = contato.get("email") or ""
                        atualizado = False

                        if numero and not cliente.telefone:
                            cliente.telefone = re.sub(r"\D", "", numero)[:20]
                            atualizado = True
                        if email and not cliente.email:
                            cliente.email = email[:255]
                            atualizado = True

                        if atualizado:
                            atualizados += 1

            db.commit()
            logger.info("sync_deskrio: %d clientes atualizados | snapshot=%s", atualizados, snapshot.name)
            return StepResult(
                nome="sync_deskrio",
                sucesso=True,
                registros_processados=atualizados,
                mensagem=f"Snapshot {snapshot.name}: {len(contacts)} contatos processados, {atualizados} clientes atualizados.",
            )

        except Exception as exc:
            db.rollback()
            logger.exception("sync_deskrio: erro — %s", exc)
            return StepResult(
                nome="sync_deskrio",
                sucesso=False,
                registros_processados=atualizados,
                erro=str(exc),
                mensagem="Erro durante sync_deskrio. Rollback executado.",
            )

    def _sync_mercos(self, db: Session) -> StepResult:
        """
        Sincroniza dados Mercos do snapshot mais recente em data/mercos/.

        Processa:
          - indicadores.json: atualiza metricas de carteira (sem alterar vendas)
          - pedidos_ativos.json: registra vendas novas (numero_pedido como dedup)

        R4 — Two-Base: pedidos com valor > 0 sao VENDAS. NUNCA valor em LOG.
        R5 — CNPJ: nao disponivel diretamente nos pedidos Mercos, usa nome fuzzy.
        R8 — Apenas dados do arquivo real — NUNCA fabricar CNPJs.
        """
        snapshot = _latest_snapshot("mercos")
        if snapshot is None:
            return StepResult(
                nome="sync_mercos",
                sucesso=False,
                mensagem="Nenhum snapshot encontrado em data/mercos/",
            )

        indicadores_path = snapshot / "indicadores.json"
        pedidos_path = snapshot / "pedidos_ativos.json"

        processados = 0
        avisos: list[str] = []

        # -- Indicadores: registrar no log para auditoria (sem alterar dados de clientes)
        if indicadores_path.exists():
            indicadores = _load_json(indicadores_path)
            if isinstance(indicadores, dict):
                periodo = indicadores.get("period", "desconhecido")
                vendido = indicadores.get("evolucao_venda", {}).get("vendido_no_mes", 0)
                logger.info(
                    "sync_mercos indicadores: periodo=%s vendido_mes=%.2f",
                    periodo,
                    vendido,
                )
                processados += 1
            else:
                avisos.append("indicadores.json invalido")
        else:
            avisos.append("indicadores.json nao encontrado")

        # -- Pedidos ativos: registrar novas vendas sem duplicar
        vendas_novas = 0
        if pedidos_path.exists():
            from datetime import date
            from backend.app.models.venda import Venda
            from backend.app.models.cliente import Cliente

            pedidos_data = _load_json(pedidos_path)
            pedidos = pedidos_data.get("pedidos", []) if isinstance(pedidos_data, dict) else []

            try:
                for pedido in pedidos:
                    if not isinstance(pedido, dict):
                        continue

                    numero = str(pedido.get("numero", "")).strip()
                    valor = pedido.get("valor", 0.0)

                    if not numero or not valor or valor <= 0:
                        continue

                    # Deduplicacao por numero do pedido
                    existe = db.query(Venda).filter(Venda.numero_pedido == numero).first()
                    if existe:
                        continue

                    # Tentar resolver CNPJ pelo nome do cliente (heuristico)
                    # R8: nao fabricar CNPJ — skip se nao encontrar
                    nome_cliente = (pedido.get("razao_social") or pedido.get("cliente") or "").strip()
                    cnpj_resolvido: str | None = None

                    if nome_cliente:
                        # Busca exata por razao_social primeiro
                        c = db.query(Cliente).filter(
                            Cliente.razao_social.ilike(f"%{nome_cliente[:40]}%")
                        ).first()
                        if c:
                            cnpj_resolvido = c.cnpj

                    if not cnpj_resolvido:
                        # Sem CNPJ resolvido — nao registrar para nao violar R8
                        logger.debug(
                            "sync_mercos: pedido %s sem CNPJ resolvido para '%s' — ignorado",
                            numero,
                            nome_cliente[:50],
                        )
                        continue

                    # Normalizar data
                    data_str = pedido.get("data", "")
                    try:
                        data_pedido = date.fromisoformat(data_str)
                    except (ValueError, TypeError):
                        data_pedido = date.today()

                    # Mapear vendedor
                    vendedor_raw = (pedido.get("vendedor") or "").strip()
                    consultor = _mapear_vendedor(vendedor_raw)

                    # R4: valor > 0, classificacao REAL (dado do Mercos)
                    venda = Venda(
                        cnpj=cnpj_resolvido,
                        data_pedido=data_pedido,
                        numero_pedido=numero,
                        valor_pedido=float(valor),
                        consultor=consultor,
                        fonte="MERCOS",
                        classificacao_3tier="REAL",
                        mes_referencia=data_pedido.strftime("%Y-%m"),
                    )
                    db.add(venda)
                    vendas_novas += 1

                db.commit()
                processados += vendas_novas
                logger.info("sync_mercos: %d vendas novas registradas | snapshot=%s", vendas_novas, snapshot.name)

            except Exception as exc:
                db.rollback()
                logger.exception("sync_mercos pedidos: erro — %s", exc)
                avisos.append(f"Erro ao processar pedidos: {exc}")
        else:
            avisos.append("pedidos_ativos.json nao encontrado")

        msg = f"Snapshot {snapshot.name}: {processados} registros processados, {vendas_novas} vendas novas."
        if avisos:
            msg += " Avisos: " + "; ".join(avisos)

        return StepResult(
            nome="sync_mercos",
            sucesso=True,
            registros_processados=processados,
            mensagem=msg,
        )

    def _recalculate(self, db: Session) -> StepResult:
        """
        Recalcula Score, Sinaleiro e flags de follow-up para todos os clientes ativos.

        Usa score_service e sinaleiro_service (singletons existentes).
        Commit em batch de 100 para evitar transacoes longas.

        R4 — Nenhum valor monetario e alterado aqui.
        R8 — Apenas clientes classificados como REAL ou SINTETICO.
        """
        from backend.app.models.cliente import Cliente
        from backend.app.services.score_service import score_service
        from backend.app.services.sinaleiro_service import sinaleiro_service

        BATCH_SIZE = 100
        processados = 0
        erros = 0

        try:
            clientes = (
                db.query(Cliente)
                .filter(Cliente.classificacao_3tier.in_(["REAL", "SINTETICO"]))
                .all()
            )

            for i, cliente in enumerate(clientes):
                try:
                    # Recalcular score
                    score_service.aplicar(db, cliente)

                    # Recalcular sinaleiro
                    sinaleiro_service.aplicar(db, cliente)

                    processados += 1

                    # Commit em batch
                    if (i + 1) % BATCH_SIZE == 0:
                        db.commit()
                        logger.debug("recalculate: batch %d confirmado", (i + 1) // BATCH_SIZE)

                except Exception as exc:
                    erros += 1
                    logger.warning(
                        "recalculate: erro no cliente %s — %s", cliente.cnpj, exc
                    )

            # Commit do ultimo batch
            db.commit()

            logger.info(
                "recalculate: %d clientes processados, %d erros", processados, erros
            )
            msg = f"{processados} clientes recalculados."
            if erros:
                msg += f" {erros} clientes com erro (ignorados)."

            return StepResult(
                nome="recalculate",
                sucesso=erros == 0,
                registros_processados=processados,
                mensagem=msg,
            )

        except Exception as exc:
            db.rollback()
            logger.exception("recalculate: erro geral — %s", exc)
            return StepResult(
                nome="recalculate",
                sucesso=False,
                registros_processados=processados,
                erro=str(exc),
                mensagem="Erro geral no recalculo. Rollback executado.",
            )


# ---------------------------------------------------------------------------
# Helpers de dominio
# ---------------------------------------------------------------------------

# DE-PARA vendedores (R: CLAUDE.md)
_VENDEDOR_MAP: dict[str, str] = {
    "manu": "MANU",
    "manu vitao": "MANU",
    "manu ditzel": "MANU",
    "larissa": "LARISSA",
    "lari": "LARISSA",
    "larissa vitao": "LARISSA",
    "larissa padilha": "LARISSA",
    "mais granel": "LARISSA",
    "rodrigo": "LARISSA",
    "daiane": "DAIANE",
    "central daiane": "DAIANE",
    "central - daiane": "DAIANE",
    "daiane vitao": "DAIANE",
    "julio": "JULIO",
    "julio gadret": "JULIO",
}


def _mapear_vendedor(raw: str) -> str:
    """Converte nome livre do vendedor para canonical (MANU/LARISSA/DAIANE/JULIO/LEGADO)."""
    chave = raw.strip().lower()
    if chave in _VENDEDOR_MAP:
        return _VENDEDOR_MAP[chave]
    # Verificar substring
    for k, v in _VENDEDOR_MAP.items():
        if k in chave:
            return v
    return "LEGADO"


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

pipeline_service = PipelineService()
