"""
CRM VITAO360 — Reclassificacao de PROSPECTs da DAIANE
======================================================

Missao:
  DAIANE tem 1.054 PROSPECTs, a grande maioria sem faturamento real.
  Este script reclassifica cada um de acordo com as seguintes regras:

  1. Tem rede real (BIO MUNDO, MUNDO VERDE, NOVA GERACAO, VIDA LEVE,
     DIVINA TERRA, CIA DA SAUDE, ARMAZEM FIT STORE):
       -> Manter DAIANE  (ela gerencia redes/franquias)
       -> tipo_cliente = 'PROSPECT_REDE'

  2. SEM GRUPO ou NULL rede com faturamento_total > 0:
       -> Manter DAIANE  (ja tem historico de compra)
       -> tipo_cliente = 'PROSPECT_REDE_FAT'

  3. SEM GRUPO ou NULL rede, sem faturamento, UF in (SC, PR, RS):
       -> Reassignar para MANU  (territorio Sul)
       -> tipo_cliente inalterado

  4. SEM GRUPO ou NULL rede, sem faturamento, UF fora de Sul:
       -> Reassignar para LARISSA  (resto do Brasil)
       -> tipo_cliente inalterado

  5. SEM GRUPO ou NULL rede, sem faturamento, UF=NULL:
       -> consultor = 'NAO_ATRIBUIDO'  (revisao manual posterior)
       -> tipo_cliente inalterado

REGRAS INVIOLAVEIS:
  - R4  Two-Base: este script NAO toca valores monetarios
  - R5  CNPJ: string 14 digitos, nunca alterado
  - R8  Nenhum cliente e deletado — apenas consultor/tipo_cliente sao alterados
  - R11 Log de cada mudanca em audit_logs
  - Idempotente: re-executar produz o mesmo resultado

Uso:
  python scripts/reclassify_daiane_prospects.py [--dry-run]

  --dry-run: mostra o que seria feito, sem gravar no banco
"""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Configuracao de paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "crm_vitao360.db"

# Adicionar raiz ao sys.path para importar modelos SQLAlchemy
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
logger = logging.getLogger("reclassify_daiane")

# ---------------------------------------------------------------------------
# Constantes de negocio
# ---------------------------------------------------------------------------
USUARIO_SISTEMA = "SISTEMA_RECLASSIFICACAO"

# UFs do territorio da MANU (Sul do Brasil)
UFS_MANU = {"SC", "PR", "RS"}

# Redes gerenciadas pela DAIANE — strings exatas que aparecem no campo
# rede_regional do banco (verificado 2026-04-01)
REDES_DAIANE = {
    "06 - INTERNA - BIO MUNDO",
    "06 - INTERNA - MUNDO VERDE",
    "06 - INTERNA - NOVA GERACAO",
    "06 - INTERNA - CIA DA SAUDE",
    "06 - INTERNA - ARMAZEM FIT STORE",
    "DIVINA TERRA",
    "VIDA LEVE",
}

# Valor sentinel para rede sem grupo real
REDE_SEM_GRUPO = "06 - SEM GRUPO"


# ---------------------------------------------------------------------------
# Helpers de classificacao
# ---------------------------------------------------------------------------

def _tem_rede_real(rede_regional: Optional[str]) -> bool:
    """Retorna True se o campo rede_regional e uma rede gerenciada pela DAIANE."""
    return rede_regional in REDES_DAIANE


def _tem_faturamento(faturamento_total: Optional[float]) -> bool:
    """Retorna True se o cliente tem algum faturamento registrado."""
    return faturamento_total is not None and faturamento_total > 0.0


def _destino_sem_rede(uf: Optional[str]) -> str:
    """Decide o destino de um PROSPECT sem rede real e sem faturamento.

    Returns:
        'MANU'           — UF no Sul (SC, PR, RS)
        'LARISSA'        — UF fora do Sul
        'NAO_ATRIBUIDO'  — UF desconhecida
    """
    if not uf:
        return "NAO_ATRIBUIDO"
    if uf.upper() in UFS_MANU:
        return "MANU"
    return "LARISSA"


# ---------------------------------------------------------------------------
# Sessao SQLAlchemy
# ---------------------------------------------------------------------------

def _criar_session() -> tuple[Session, object]:
    """Cria engine SQLite e retorna (session, engine)."""
    db_url = f"sqlite:///{DB_PATH}"
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    return SessionLocal(), engine


# ---------------------------------------------------------------------------
# Registro de auditoria
# ---------------------------------------------------------------------------

def _registrar_audit(
    session: Session,
    cnpj: str,
    campo: str,
    valor_anterior: Optional[str],
    valor_novo: Optional[str],
    dry_run: bool,
) -> None:
    """Insere um registro em audit_logs para rastreabilidade total.

    Em dry_run, apenas loga a intencao sem gravar.
    """
    msg = (
        f"  AUDIT {cnpj} | {campo}: "
        f"{valor_anterior!r} -> {valor_novo!r}"
    )
    if dry_run:
        logger.info(f"[DRY-RUN]{msg}")
        return

    session.execute(
        text("""
            INSERT INTO audit_logs
                (cnpj, campo, valor_anterior, valor_novo, usuario_nome, created_at)
            VALUES
                (:cnpj, :campo, :valor_anterior, :valor_novo, :usuario_nome, :created_at)
        """),
        {
            "cnpj": cnpj,
            "campo": campo,
            "valor_anterior": str(valor_anterior) if valor_anterior is not None else None,
            "valor_novo": str(valor_novo) if valor_novo is not None else None,
            "usuario_nome": USUARIO_SISTEMA,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )


# ---------------------------------------------------------------------------
# Logica principal de reclassificacao
# ---------------------------------------------------------------------------

def _classificar_prospect(row: dict) -> tuple[Optional[str], Optional[str]]:
    """Decide (novo_consultor, novo_tipo_cliente) para um PROSPECT da DAIANE.

    Retorna (None, None) se nenhuma alteracao for necessaria.

    Regras em ordem de prioridade:
      1. Rede real -> DAIANE / PROSPECT_REDE
      2. Sem rede real + faturamento -> DAIANE / PROSPECT_REDE_FAT
      3. Sem rede real + sem faturamento -> destino por UF / tipo_cliente inalterado
    """
    rede = row["rede_regional"]
    fat = row["faturamento_total"]
    uf = row["uf"]

    if _tem_rede_real(rede):
        # Regra 1: e uma rede/franquia gerenciada por DAIANE
        novo_tipo = "PROSPECT_REDE"
        # consultor nao muda
        if row["tipo_cliente"] != novo_tipo:
            return ("DAIANE", novo_tipo)
        return (None, None)

    if _tem_faturamento(fat):
        # Regra 2: sem rede oficial, mas tem historico de compra — manter DAIANE
        novo_tipo = "PROSPECT_REDE_FAT"
        if row["tipo_cliente"] != novo_tipo:
            return ("DAIANE", novo_tipo)
        return (None, None)

    # Regra 3: sem rede, sem faturamento — redistribuir por UF
    novo_consultor = _destino_sem_rede(uf)
    # tipo_cliente nao e alterado neste caso
    if row["consultor"] != novo_consultor:
        return (novo_consultor, row["tipo_cliente"])
    return (None, None)


def reclassificar(dry_run: bool = False) -> None:
    """Executa a reclassificacao completa. Idempotente."""

    logger.info("=" * 60)
    logger.info("RECLASSIFICACAO DE PROSPECTs — DAIANE")
    logger.info(f"DB: {DB_PATH}")
    logger.info(f"Modo: {'DRY-RUN (sem gravacao)' if dry_run else 'PRODUCAO (gravando)'}")
    logger.info("=" * 60)

    if not DB_PATH.exists():
        logger.error(f"Banco nao encontrado: {DB_PATH}")
        sys.exit(1)

    session, engine = _criar_session()

    try:
        # ------------------------------------------------------------------
        # 1. Carregar todos os PROSPECTs da DAIANE
        # ------------------------------------------------------------------
        result = session.execute(
            text("""
                SELECT id, cnpj, nome_fantasia, uf, rede_regional,
                       consultor, situacao, tipo_cliente, faturamento_total
                FROM clientes
                WHERE consultor = 'DAIANE'
                  AND situacao = 'PROSPECT'
                ORDER BY id
            """)
        )
        prospects = [dict(row._mapping) for row in result]
        total_input = len(prospects)
        logger.info(f"PROSPECTs DAIANE carregados: {total_input}")

        # ------------------------------------------------------------------
        # 2. Classificar cada prospect
        # ------------------------------------------------------------------
        contadores = {
            "DAIANE_rede":       0,   # mantidos com tipo PROSPECT_REDE
            "DAIANE_fat":        0,   # mantidos com tipo PROSPECT_REDE_FAT
            "MANU":              0,   # reassignados para MANU
            "LARISSA":           0,   # reassignados para LARISSA
            "NAO_ATRIBUIDO":     0,   # UF desconhecida
            "sem_mudanca":       0,   # ja estavam corretos (idempotencia)
        }

        updates_consultor: list[dict] = []    # clientes com mudanca de consultor
        updates_tipo: list[dict] = []         # clientes com mudanca de tipo_cliente
        audit_entries: list[dict] = []        # para logging DRY-RUN

        for row in prospects:
            cnpj = row["cnpj"]
            novo_consultor, novo_tipo = _classificar_prospect(row)

            if novo_consultor is None and novo_tipo is None:
                # Nenhuma alteracao necessaria
                contadores["sem_mudanca"] += 1
                continue

            # Determinar qual contador incrementar
            if novo_consultor in ("DAIANE", None):
                # tipo_cliente mudou mas consultor e DAIANE
                if novo_tipo == "PROSPECT_REDE":
                    contadores["DAIANE_rede"] += 1
                elif novo_tipo == "PROSPECT_REDE_FAT":
                    contadores["DAIANE_fat"] += 1
                else:
                    contadores["DAIANE_rede"] += 1
            else:
                contadores[novo_consultor] += 1

            # Preparar updates — separar mudanca de consultor de mudanca de tipo
            consultor_atual = row["consultor"]
            tipo_atual = row["tipo_cliente"]

            consultor_efetivo = novo_consultor if novo_consultor != consultor_atual else None
            tipo_efetivo = novo_tipo if novo_tipo != tipo_atual else None

            if consultor_efetivo is not None:
                updates_consultor.append({
                    "cnpj": cnpj,
                    "novo_consultor": consultor_efetivo,
                    "consultor_anterior": consultor_atual,
                })

            if tipo_efetivo is not None:
                updates_tipo.append({
                    "cnpj": cnpj,
                    "novo_tipo": tipo_efetivo,
                    "tipo_anterior": tipo_atual,
                })

            # Registrar auditoria
            if consultor_efetivo is not None:
                _registrar_audit(
                    session, cnpj,
                    "consultor",
                    consultor_atual,
                    consultor_efetivo,
                    dry_run,
                )
            if tipo_efetivo is not None:
                _registrar_audit(
                    session, cnpj,
                    "tipo_cliente",
                    tipo_atual,
                    tipo_efetivo,
                    dry_run,
                )

        # ------------------------------------------------------------------
        # 3. Aplicar updates em lote
        # ------------------------------------------------------------------
        now_iso = datetime.now(timezone.utc).isoformat()

        if not dry_run:
            # Update consultor em lote
            if updates_consultor:
                session.execute(
                    text("""
                        UPDATE clientes
                        SET consultor  = :novo_consultor,
                            updated_at = :updated_at
                        WHERE cnpj = :cnpj
                    """),
                    [
                        {
                            "cnpj": u["cnpj"],
                            "novo_consultor": u["novo_consultor"],
                            "updated_at": now_iso,
                        }
                        for u in updates_consultor
                    ],
                )

            # Update tipo_cliente em lote
            if updates_tipo:
                session.execute(
                    text("""
                        UPDATE clientes
                        SET tipo_cliente = :novo_tipo,
                            updated_at   = :updated_at
                        WHERE cnpj = :cnpj
                    """),
                    [
                        {
                            "cnpj": u["cnpj"],
                            "novo_tipo": u["novo_tipo"],
                            "updated_at": now_iso,
                        }
                        for u in updates_tipo
                    ],
                )

            session.commit()
            logger.info(
                f"Commit: {len(updates_consultor)} mudancas de consultor, "
                f"{len(updates_tipo)} mudancas de tipo_cliente."
            )
        else:
            logger.info(
                f"[DRY-RUN] Seriam gravados: "
                f"{len(updates_consultor)} mudancas de consultor, "
                f"{len(updates_tipo)} mudancas de tipo_cliente."
            )

        # ------------------------------------------------------------------
        # 4. Verificacao pos-update (apenas em producao)
        # ------------------------------------------------------------------
        if not dry_run:
            result_verify = session.execute(
                text("""
                    SELECT consultor, COUNT(*)
                    FROM clientes
                    WHERE situacao = 'PROSPECT'
                      AND cnpj IN (
                          SELECT cnpj FROM audit_logs
                          WHERE usuario_nome = :usuario
                      )
                    GROUP BY consultor
                """),
                {"usuario": USUARIO_SISTEMA},
            )
            logger.info("Verificacao pos-update (por consultor, so PROSPECTs alterados):")
            for consultor, cnt in result_verify:
                logger.info(f"  {consultor or 'NULL':<20} {cnt:>5}")

        # ------------------------------------------------------------------
        # 5. Sumario final
        # ------------------------------------------------------------------
        total_alterados = (
            contadores["DAIANE_rede"]
            + contadores["DAIANE_fat"]
            + contadores["MANU"]
            + contadores["LARISSA"]
            + contadores["NAO_ATRIBUIDO"]
        )

        print()
        print("=" * 60)
        print("SUMARIO RECLASSIFICACAO DAIANE PROSPECTS")
        print("=" * 60)
        print(f"Total PROSPECTs analisados:       {total_input:>6}")
        print(f"Sem mudanca (ja corretos):         {contadores['sem_mudanca']:>6}")
        print()
        print("Alteracoes realizadas:")
        print(f"  Mantidos DAIANE (rede real):     {contadores['DAIANE_rede']:>6}  tipo_cliente -> PROSPECT_REDE")
        print(f"  Mantidos DAIANE (com fat.):      {contadores['DAIANE_fat']:>6}  tipo_cliente -> PROSPECT_REDE_FAT")
        print(f"  Reassignados para MANU (Sul):    {contadores['MANU']:>6}  (SC/PR/RS)")
        print(f"  Reassignados para LARISSA:       {contadores['LARISSA']:>6}  (resto do Brasil)")
        print(f"  Marcados NAO_ATRIBUIDO:          {contadores['NAO_ATRIBUIDO']:>6}  (UF desconhecida)")
        print(f"  Total alterados:                 {total_alterados:>6}")
        print()
        print(f"Registros audit_log inseridos:    {len(updates_consultor) + len(updates_tipo):>6}")
        print()

        if dry_run:
            print("MODO DRY-RUN — nenhuma alteracao gravada.")
        else:
            print("STATUS: CONCLUIDO — alteracoes gravadas com sucesso.")

        print("=" * 60)

        # Validacao de consistencia: total deve bater
        assert total_input == total_alterados + contadores["sem_mudanca"], (
            f"INCONSISTENCIA: {total_input} != "
            f"{total_alterados} + {contadores['sem_mudanca']}"
        )

    except Exception:
        session.rollback()
        logger.exception("Erro durante reclassificacao — rollback executado.")
        sys.exit(1)
    finally:
        session.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reclassifica PROSPECTs da DAIANE sem dados reais."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Mostra o que seria feito sem gravar no banco.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    reclassificar(dry_run=args.dry_run)
