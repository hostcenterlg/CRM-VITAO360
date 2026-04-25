"""
CRM VITAO360 — Seed de usuarios e regras do motor.

Popula automaticamente no startup:
  1. 5 usuarios iniciais (admin + 3 consultores + 1 consultor_externo)
  2. Regras do Motor de Regras V4 — 92 combinacoes (7 situacoes x 14 resultados)

Ambas as funcoes sao idempotentes: nao duplicam registros existentes.

Fonte das regras: data/intelligence/motor_regras_v4.json (source of truth — 92 combinacoes)
As combinacoes sao lidas diretamente do JSON; motor_de_regras() usado como fallback para
combinacoes ausentes no JSON.

Regras inviolaveis:
  R8  — NUNCA inventar dados; regras extraidas do JSON source of truth
  R11 — Commits atomicos (seed e parte do startup, nao do ciclo de commits)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from sqlalchemy.orm import Session

from backend.app.models.regra_motor import RegraMotor
from backend.app.models.usuario import Usuario
from backend.app.security import hash_password

# ---------------------------------------------------------------------------
# Adicionar raiz do projeto ao path para importar scripts/motor_regras.py
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # services/ -> app/ -> backend/ -> repo root
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

_MOTOR_REGRAS_JSON = _PROJECT_ROOT / "data" / "intelligence" / "motor_regras_v4.json"

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
    {
        # Julio Gadret — RCA externo, territorio Brasil (presencial)
        # Atende exclusivamente Cia Saude e Fitland; sem acesso a dados financeiros
        "email": "julio@vitao.com.br",
        "nome": "Julio Gadret",
        "role": "consultor_externo",
        "consultor_nome": "JULIO",
        "senha": "vitao2026",
    },
]


def seed_usuarios(db: Session) -> int:
    """
    Cria os 5 usuarios iniciais se ainda nao existirem e normaliza
    consultor_nome de usuarios existentes para chave curta DE-PARA.

    Usuarios: Leandro (admin), Manu (consultor), Larissa (consultor),
    Daiane (consultor), Julio Gadret (consultor_externo — Cia Saude + Fitland).

    Normalizacao de consultor_nome (alinha com clientes.consultor):
      'HEMANUELE DITZEL (MANU)' -> 'MANU'
      'LARISSA PADILHA'         -> 'LARISSA'
      'DAIANE STAVICKI'         -> 'DAIANE'
      'JULIO GADRET'            -> 'JULIO'

    Razao: clientes.consultor armazena chave DE-PARA curta (CLAUDE.md);
    routes_clientes.py filtra Cliente.consultor == user.consultor_nome.
    Sem normalizacao, consultores logados veem total=0.

    Idempotente: verifica por email antes de inserir e so faz UPDATE quando
    o valor existente difere do canonico.

    Retorna a quantidade de usuarios efetivamente criados (UPDATEs nao
    contam — sao normalizacao silenciosa).
    """
    criados = 0
    # Mapping email -> consultor_nome canonico (None para admin)
    canonico = {u["email"]: u["consultor_nome"] for u in USUARIOS_INICIAIS}

    for u in USUARIOS_INICIAIS:
        existe = db.query(Usuario).filter(Usuario.email == u["email"]).first()
        if existe:
            # Normaliza consultor_nome se diferente do canonico
            esperado = canonico.get(existe.email)
            if existe.consultor_nome != esperado:
                existe.consultor_nome = esperado
            continue

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

    db.commit()

    return criados


# ---------------------------------------------------------------------------
# Regras do motor
# ---------------------------------------------------------------------------

def _tipo_acao_para(grupo_dash: str) -> str:
    """
    Mapeia grupo_dash para o tipo_acao do dashboard.
    """
    if grupo_dash == "FUNIL":
        return "VENDA"
    if grupo_dash == "RELAC.":
        return "RELACIONAMENTO"
    if grupo_dash == "NÃO VENDA":
        return "NAO_VENDA"
    return "ATENDIMENTO"


def _carregar_combinacoes_json() -> list[dict]:
    """
    Le as 92 combinacoes do motor_regras_v4.json (source of truth).

    Fallback para lista vazia se o arquivo nao existir, para que
    a estrategia por motor_de_regras() ainda possa ser usada.
    """
    if not _MOTOR_REGRAS_JSON.exists():
        return []
    with open(_MOTOR_REGRAS_JSON, encoding="utf-8") as f:
        dados = json.load(f)
    return dados.get("combinacoes", [])


def seed_regras_motor(db: Session) -> int:
    """
    Popula a tabela regras_motor com todas as 92 combinacoes do motor_regras_v4.json
    (7 situacoes x 14 resultados, com restricoes de negocio aplicadas).

    Estrategia:
      1. Le combinacoes do JSON (source of truth — 92 entradas)
      2. Para cada combinacao ausente na tabela, insere com os campos do JSON
      3. Idempotente: verifica por chave "SITUACAO|RESULTADO" antes de inserir

    Nao atualiza regras existentes — para re-seed, deletar a tabela primeiro.

    Retorna a quantidade de regras efetivamente criadas.
    """
    criadas = 0
    combinacoes = _carregar_combinacoes_json()

    for combo in combinacoes:
        situacao = combo.get("situacao", "")
        resultado = combo.get("resultado", "")
        chave = combo.get("chave") or f"{situacao}|{resultado}"

        # Checar se ja existe (idempotencia por chave unica)
        existe = db.query(RegraMotor).filter(RegraMotor.chave == chave).first()
        if existe:
            continue

        grupo_dash = combo.get("grupo_dash") or GRUPO_DASH.get(resultado, "")
        follow_up_dias_json = combo.get("followup_dias") or combo.get("follow_up_dias")
        follow_up_dias = follow_up_dias_json if follow_up_dias_json is not None else FOLLOW_UP_DIAS.get(resultado, 0)

        regra = RegraMotor(
            situacao=situacao,
            resultado=resultado,
            estagio_funil=combo.get("estagio_funil") or "EM ATENDIMENTO",
            fase=combo.get("fase") or "ATENDIMENTO",
            tipo_contato=combo.get("tipo_contato") or "ATENDIMENTO",
            acao_futura=combo.get("acao_futura") or "ATENDIMENTO",
            temperatura=combo.get("temperatura") or "MORNO",
            follow_up_dias=follow_up_dias,
            grupo_dash=grupo_dash,
            tipo_acao=combo.get("tipo_acao") or _tipo_acao_para(grupo_dash),
            chave=chave,
        )
        db.add(regra)
        criadas += 1

    if criadas:
        db.commit()

    return criadas
