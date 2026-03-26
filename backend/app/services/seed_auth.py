"""
CRM VITAO360 — Seed de usuarios e regras do motor.

Popula automaticamente no startup:
  1. 4 usuarios iniciais (admin + 3 consultores)
  2. Regras do Motor de Regras V3 (combinacoes situacao x resultado)

Ambas as funcoes sao idempotentes: nao duplicam registros existentes.

Fonte das regras: scripts/motor_regras.py — motor_de_regras()
As combinacoes sao pre-calculadas para todas as situacoes x resultados validos.

Regras inviolaveis:
  R8  — NUNCA inventar dados; regras extraidas do motor real
  R11 — Commits atomicos (seed e parte do startup, nao do ciclo de commits)
"""

from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.models.regra_motor import RegraMotor
from backend.app.models.usuario import Usuario
from backend.app.security import hash_password

# ---------------------------------------------------------------------------
# Adicionar raiz do projeto ao path para importar scripts/motor_regras.py
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[4]  # services/ -> app/ -> backend/ -> root
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.motor_regras import (  # noqa: E402 — import apos ajuste de path
    FOLLOW_UP_DIAS,
    GRUPO_DASH,
    motor_de_regras,
)


# ---------------------------------------------------------------------------
# Usuarios iniciais
# ---------------------------------------------------------------------------

USUARIOS_INICIAIS = [
    {
        "email": "leandro@vitao.com.br",
        "nome": "Leandro",
        "role": "admin",
        "consultor_nome": None,
        "senha": "vitao2026",
    },
    {
        "email": "manu@vitao.com.br",
        "nome": "Manu Ditzel",
        "role": "consultor",
        "consultor_nome": "MANU",
        "senha": "vitao2026",
    },
    {
        "email": "larissa@vitao.com.br",
        "nome": "Larissa Padilha",
        "role": "consultor",
        "consultor_nome": "LARISSA",
        "senha": "vitao2026",
    },
    {
        "email": "daiane@vitao.com.br",
        "nome": "Daiane Stavicki",
        "role": "consultor",
        "consultor_nome": "DAIANE",
        "senha": "vitao2026",
    },
]


def seed_usuarios(db: Session) -> int:
    """
    Cria os 4 usuarios iniciais se ainda nao existirem.

    Idempotente: verifica por email antes de inserir.
    Retorna a quantidade de usuarios efetivamente criados.
    """
    criados = 0
    for u in USUARIOS_INICIAIS:
        existe = db.query(Usuario).filter(Usuario.email == u["email"]).first()
        if existe:
            continue  # ja existe, pular

        usuario = Usuario(
            email=u["email"],
            nome=u["nome"],
            role=u["role"],
            consultor_nome=u["consultor_nome"],
            hashed_password=hash_password(u["senha"]),
            ativo=True,
        )
        db.add(usuario)
        criados += 1

    if criados:
        db.commit()

    return criados


# ---------------------------------------------------------------------------
# Regras do motor
# ---------------------------------------------------------------------------

# Todas as situacoes possiveis
_SITUACOES = ["ATIVO", "EM RISCO", "INAT.REC", "INAT.ANT", "NOVO", "PROSPECT"]

# Todos os resultados possiveis (12 ao total)
_RESULTADOS = [
    "EM ATENDIMENTO",
    "ORÇAMENTO",
    "CADASTRO",
    "VENDA / PEDIDO",
    "RELACIONAMENTO",
    "FOLLOW UP 7",
    "FOLLOW UP 15",
    "SUPORTE",
    "NÃO ATENDE",
    "NÃO RESPONDE",
    "RECUSOU LIGAÇÃO",
    "PERDA / FECHOU LOJA",
]

# Restricoes de dominio do motor (R8 — nao inventar combinacoes invalidas)
# CADASTRO so faz sentido para PROSPECT e NOVO (regra de negocio CRM VITAO360)
_RESTRICOES: dict[str, list[str]] = {
    "CADASTRO": ["PROSPECT", "NOVO"],
}


def _situacoes_validas_para(resultado: str) -> list[str]:
    """Retorna as situacoes validas para um determinado resultado."""
    if resultado in _RESTRICOES:
        return _RESTRICOES[resultado]
    return _SITUACOES


def _tipo_acao_para(resultado: str) -> str:
    """
    Mapeia resultado para o tipo_acao do dashboard.
    Segue a logica de grupo_dash do motor.
    """
    grupo = GRUPO_DASH.get(resultado, "")
    if grupo == "FUNIL":
        return "VENDA"
    if grupo == "RELAC.":
        return "RELACIONAMENTO"
    if grupo == "NÃO VENDA":
        return "NAO_VENDA"
    return "ATENDIMENTO"


def seed_regras_motor(db: Session) -> int:
    """
    Popula a tabela regras_motor com todas as combinacoes validas
    de situacao x resultado, calculadas pelo motor real.

    Idempotente: verifica por chave "SITUACAO|RESULTADO" antes de inserir.
    Nao atualiza regras existentes — para re-seed, deletar a tabela primeiro.

    Retorna a quantidade de regras efetivamente criadas.
    """
    criadas = 0

    for resultado in _RESULTADOS:
        for situacao in _situacoes_validas_para(resultado):
            chave = f"{situacao}|{resultado}"

            # Checar se ja existe (idempotencia por chave unica)
            existe = db.query(RegraMotor).filter(RegraMotor.chave == chave).first()
            if existe:
                continue

            # Calcular campos via motor real (sem tentativa anterior nem estagio anterior)
            # Isso representa o estado inicial de cada combinacao
            campos = motor_de_regras(
                situacao=situacao,
                resultado=resultado,
                estagio_anterior=None,
                tentativa_anterior=None,
            )

            # Sanitizar campos: garantir que nenhum campo obrigatorio seja None
            estagio_funil = campos.get("estagio_funil") or "EM ATENDIMENTO"
            fase = campos.get("fase") or "ATENDIMENTO"
            tipo_contato = campos.get("tipo_contato") or "ATENDIMENTO"
            acao_futura = campos.get("acao_futura") or "ATENDIMENTO"
            temperatura = campos.get("temperatura") or "MORNO"
            follow_up_dias = campos.get("follow_up_dias") or FOLLOW_UP_DIAS.get(resultado, 0)
            grupo_dash = campos.get("grupo_dash") or GRUPO_DASH.get(resultado, "")

            regra = RegraMotor(
                situacao=situacao,
                resultado=resultado,
                estagio_funil=estagio_funil,
                fase=fase,
                tipo_contato=tipo_contato,
                acao_futura=acao_futura,
                temperatura=temperatura,
                follow_up_dias=follow_up_dias,
                grupo_dash=grupo_dash,
                tipo_acao=_tipo_acao_para(resultado),
                chave=chave,
            )
            db.add(regra)
            criadas += 1

    if criadas:
        db.commit()

    return criadas
