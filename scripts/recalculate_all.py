"""
CRM VITAO360 — Recalculate All
================================
Recalcula Motor de Regras, Score, Sinaleiro e Agenda para todos os clientes.

Execucao:
    python scripts/recalculate_all.py

O que faz:
  1. Para cada um dos 1.581 clientes:
       a. Aplica Motor de Regras (situacao x resultado -> 9 outputs)
       b. Aplica Sinaleiro v2   (ratio dias/ciclo -> 5 cores)
       c. Aplica Score v2       (6 fatores ponderados -> 0-100 + P0-P7)
       d. Atualiza campos de inteligencia do cliente
  2. Atualiza score_historico — snapshot do dia (idempotente por cnpj+data)
  3. Limpa agenda_items da data atual e regenera para todos os consultores
  4. Imprime relatorio com distribuicoes e contagens

Garantias:
  R4 — Two-Base: NUNCA valor R$ em LogInteracao — este script NAO cria logs
  R5 — CNPJ como String(14), zero-padded
  R8 — Nao fabrica dados — usa exclusivamente o que esta no banco
  R10 — Idempotente: rodar duas vezes no mesmo dia nao cria duplicatas
  R11 — Nao faz git push
"""

from __future__ import annotations

import sys
import logging
from datetime import date, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — garante que o projeto raiz esta no sys.path para imports
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Silenciar logs SQL verbose do SQLAlchemy durante execucao em batch
import os
os.environ.setdefault("DB_ECHO", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("recalculate_all")

# ---------------------------------------------------------------------------
# Imports dos services e models do backend
# ---------------------------------------------------------------------------
from backend.app.database import SessionLocal
from backend.app.models.cliente import Cliente
from backend.app.models.score_historico import ScoreHistorico
from backend.app.models.agenda import AgendaItem
from backend.app.services.motor_regras_service import motor_service
from backend.app.services.sinaleiro_service import sinaleiro_service
from backend.app.services.score_service import score_service
from backend.app.services.agenda_service import agenda_service, CONSULTORES

# ---------------------------------------------------------------------------
# Constantes de negocio
# ---------------------------------------------------------------------------
BASELINE_FATURAMENTO = 2_091_000.0
TOLERANCIA_FAT = 0.005          # 0.5% (R7)
HOJE = date.today()


# ---------------------------------------------------------------------------
# Passo 1 — Motor de Regras aplicado a cada cliente
# ---------------------------------------------------------------------------

def aplicar_motor(db, cliente: Cliente) -> dict:
    """
    Aplica Motor de Regras usando a situacao e resultado atuais do cliente.
    Retorna dict com 9 dimensoes (estagio_funil, fase, tipo_contato, etc.).

    Nao cria LogInteracao — este script nao registra atendimentos.
    """
    return motor_service.aplicar(
        db=db,
        situacao=cliente.situacao or "PROSPECT",
        resultado=cliente.resultado or "",
        estagio_anterior=cliente.estagio_funil,
        tentativa_anterior=cliente.tentativas,
    )


# ---------------------------------------------------------------------------
# Passo 2 — Sinaleiro (delegado direto ao service)
# ---------------------------------------------------------------------------

def aplicar_sinaleiro(db, cliente: Cliente) -> str:
    """
    Calcula e aplica o sinaleiro ao campo cliente.sinaleiro.
    Retorna o valor calculado ('VERDE', 'AMARELO', 'LARANJA', 'VERMELHO', 'ROXO').
    """
    return sinaleiro_service.aplicar(db, cliente)


# ---------------------------------------------------------------------------
# Passo 3 — Score v2 + historico (delegado ao service)
# ---------------------------------------------------------------------------

def aplicar_score_e_historico(db, cliente: Cliente, hoje: date) -> dict:
    """
    Calcula score v2 (6 fatores), atualiza cliente.score e cliente.prioridade,
    e persiste snapshot em score_historico.

    Idempotencia: se ja existir score_historico para (cnpj, hoje), remove o
    antigo e insere novo com os valores recalculados.
    """
    # Remover snapshot anterior do dia (idempotencia)
    db.query(ScoreHistorico).filter(
        ScoreHistorico.cnpj == cliente.cnpj,
        ScoreHistorico.data_calculo == hoje,
    ).delete(synchronize_session="fetch")

    # Calcular e salvar (score_service ja faz db.add do historico)
    return score_service.aplicar_e_salvar(db, cliente)


# ---------------------------------------------------------------------------
# Validacao de faturamento (R7)
# ---------------------------------------------------------------------------

def verificar_faturamento(db) -> float:
    """
    Soma faturamento_total dos clientes e compara com baseline R$ 2.091.000.
    Emite warning se divergencia > 0.5%.
    """
    import sqlalchemy as sa
    total = db.execute(sa.text("SELECT SUM(faturamento_total) FROM clientes")).scalar() or 0.0
    divergencia = abs(total - BASELINE_FATURAMENTO) / BASELINE_FATURAMENTO if BASELINE_FATURAMENTO else 0
    return float(total), divergencia


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    logger.info("=" * 60)
    logger.info("RECALCULATE ALL — Motor + Sinaleiro + Score + Agenda")
    logger.info(f"Data de referencia: {HOJE.isoformat()}")
    logger.info("=" * 60)

    db = SessionLocal()

    try:
        # ----------------------------------------------------------------
        # Contagem inicial
        # ----------------------------------------------------------------
        total_clientes = db.query(Cliente).count()
        logger.info(f"Clientes no banco: {total_clientes}")

        # ----------------------------------------------------------------
        # Verificacao de faturamento (R7)
        # ----------------------------------------------------------------
        fat_total, divergencia = verificar_faturamento(db)
        logger.info(f"Faturamento acumulado (clientes.faturamento_total): R$ {fat_total:,.2f}")
        logger.info(f"Baseline esperado: R$ {BASELINE_FATURAMENTO:,.2f}  |  Divergencia: {divergencia:.2%}")
        if divergencia > TOLERANCIA_FAT:
            logger.warning(f"ATENCAO R7: divergencia {divergencia:.2%} acima do limite 0.5%")

        # ----------------------------------------------------------------
        # Carregar todos os clientes de uma vez (evita N+1)
        # ----------------------------------------------------------------
        logger.info("Carregando clientes...")
        clientes: list[Cliente] = db.query(Cliente).all()
        logger.info(f"  {len(clientes)} clientes carregados")

        # ----------------------------------------------------------------
        # Recalculo por cliente
        # ----------------------------------------------------------------
        logger.info("Recalculando Motor + Sinaleiro + Score para cada cliente...")

        contadores: dict[str, dict] = {
            "situacao": {},
            "sinaleiro": {},
            "prioridade": {},
            "motor_hit": {"db": 0, "fallback": 0, "sem_resultado": 0},
        }
        erros: list[str] = []
        total_historico = 0

        for i, cl in enumerate(clientes, start=1):
            try:
                # a) Motor de Regras
                if cl.situacao or cl.resultado:
                    motor_campos = aplicar_motor(db, cl)
                    # Aplicar outputs do motor ao cliente (exceto temperatura:
                    # motor define temperatura; manter se cliente ja tiver uma
                    # temperatura mais recente de um atendimento real)
                    cl.estagio_funil = motor_campos["estagio_funil"]
                    cl.fase = motor_campos["fase"]
                    cl.tipo_contato = motor_campos["tipo_contato"]
                    cl.acao_futura = motor_campos["acao_futura"]
                    cl.followup_dias = motor_campos["follow_up_dias"]
                    cl.grupo_dash = motor_campos["grupo_dash"]
                    if motor_campos.get("tipo_acao"):
                        cl.tipo_acao = motor_campos["tipo_acao"]
                    # Temperatura: motor define se cliente nao tem valor proprio
                    if not cl.temperatura:
                        cl.temperatura = motor_campos["temperatura"]
                    contadores["motor_hit"]["db"] += 1
                else:
                    contadores["motor_hit"]["sem_resultado"] += 1

                # b) Sinaleiro v2
                sinaleiro_valor = aplicar_sinaleiro(db, cl)

                # c) Score v2 + historico (persiste snapshot do dia)
                score_resultado = aplicar_score_e_historico(db, cl, HOJE)
                total_historico += 1

                # Acumular contadores para relatorio
                sit = (cl.situacao or "").upper().strip() or "(sem situacao)"
                contadores["situacao"][sit] = contadores["situacao"].get(sit, 0) + 1
                contadores["sinaleiro"][sinaleiro_valor] = contadores["sinaleiro"].get(sinaleiro_valor, 0) + 1
                prioridade = score_resultado.get("prioridade_curta", "??")
                contadores["prioridade"][prioridade] = contadores["prioridade"].get(prioridade, 0) + 1

            except Exception as exc:
                erros.append(f"CNPJ {cl.cnpj}: {exc}")
                logger.warning(f"Erro no cliente {cl.cnpj}: {exc}")

            # Flush em lotes de 500 para nao acumular sessao em memoria
            if i % 500 == 0:
                db.flush()
                logger.info(f"  ... {i}/{len(clientes)} processados")

        # Flush final antes do commit
        db.flush()
        logger.info(f"Flush final concluido. {total_historico} snapshots criados em score_historico.")

        # ----------------------------------------------------------------
        # Passo 4 — Agenda diaria (idempotente: agenda_service limpa o dia)
        # ----------------------------------------------------------------
        logger.info(f"Gerando agenda diaria para {HOJE.isoformat()}...")
        agenda_counts = agenda_service.gerar_todas(db, HOJE)
        total_agenda = sum(agenda_counts.values())
        logger.info(f"  Agenda gerada: {total_agenda} itens em {len(agenda_counts)} consultores")

        # ----------------------------------------------------------------
        # Commit unico
        # ----------------------------------------------------------------
        db.commit()
        logger.info("Commit realizado com sucesso.")

    except Exception as exc:
        db.rollback()
        logger.error(f"ERRO CRITICO — rollback executado: {exc}")
        raise
    finally:
        db.close()

    # ----------------------------------------------------------------
    # Relatorio final
    # ----------------------------------------------------------------
    print()
    print("=" * 60)
    print("RELATORIO FINAL — RECALCULATE ALL — CRM VITAO360")
    print(f"Executado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    print(f"\nTotal clientes recalculados : {total_clientes}")
    print(f"score_historico inseridos   : {total_historico}")
    print(f"Erros de processamento      : {len(erros)}")
    if erros:
        for e in erros[:10]:
            print(f"  ! {e}")
        if len(erros) > 10:
            print(f"  ... (+{len(erros) - 10} outros)")

    print("\nDistribuicao por SITUACAO:")
    for sit, cnt in sorted(contadores["situacao"].items(), key=lambda x: -x[1]):
        print(f"  {sit:<22} {cnt:>5}")

    print("\nDistribuicao por SINALEIRO:")
    ordem_sinal = ["VERDE", "AMARELO", "LARANJA", "VERMELHO", "ROXO"]
    for sinal in ordem_sinal:
        cnt = contadores["sinaleiro"].get(sinal, 0)
        bar = "#" * (cnt // 20)
        print(f"  {sinal:<10} {cnt:>5}  {bar}")
    outros_sinal = {k: v for k, v in contadores["sinaleiro"].items() if k not in ordem_sinal}
    for sinal, cnt in outros_sinal.items():
        print(f"  {sinal:<10} {cnt:>5}")

    print("\nDistribuicao por PRIORIDADE:")
    labels = {
        "P0": "IMEDIATA",
        "P1": "NAMORO NOVO",
        "P2": "NEGOCIACAO",
        "P3": "PROBLEMA",
        "P4": "MOMENTO OURO",
        "P5": "INAT. RECENTE",
        "P6": "INAT. ANTIGO",
        "P7": "PROSPECCAO",
    }
    for pri in ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7"]:
        cnt = contadores["prioridade"].get(pri, 0)
        label = labels.get(pri, "")
        print(f"  {pri} {label:<16} {cnt:>5}")

    total_p = sum(contadores["prioridade"].values())
    outros_p = {k: v for k, v in contadores["prioridade"].items() if k not in labels}
    for p, cnt in outros_p.items():
        print(f"  {p:<19} {cnt:>5}")
        total_p += cnt

    print("\nAgenda gerada por consultor:")
    consultores_ordem = ["MANU", "LARISSA", "DAIANE", "JULIO"]
    for consultor in consultores_ordem:
        cnt = agenda_counts.get(consultor, 0)
        max_c = CONSULTORES.get(consultor, {}).get("max", 40)
        print(f"  {consultor:<10} {cnt:>3} / {max_c}")
    outros_c = {k: v for k, v in agenda_counts.items() if k not in consultores_ordem}
    for c, cnt in outros_c.items():
        print(f"  {c:<10} {cnt:>3}")
    print(f"  TOTAL      {total_agenda:>3}")

    print(f"\nFaturamento (clientes.faturamento_total): R$ {fat_total:,.2f}")
    print(f"Baseline R7:                             R$ {BASELINE_FATURAMENTO:,.2f}")
    divergencia_fmt = f"{divergencia:.2%}"
    status_fat = "OK (<=0.5%)" if divergencia <= TOLERANCIA_FAT else "ATENCAO (>0.5%)"
    print(f"Divergencia:                             {divergencia_fmt}  [{status_fat}]")

    print()
    print("=" * 60)
    if erros:
        print(f"CONCLUIDO COM {len(erros)} ERROS")
    else:
        print("CONCLUIDO COM SUCESSO")
    print("=" * 60)


if __name__ == "__main__":
    main()
