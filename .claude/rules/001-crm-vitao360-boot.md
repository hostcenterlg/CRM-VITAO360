# 001 — CRM VITAO360 BOOT — BACKUP DA COLEIRA
# SEVERIDADE: BLOQUEANTE. Redundância intencional.

---

## CRM VITAO360 — PROTOCOLO INVIOLÁVEL

ESTE PROTOCOLO SOBREPÕE QUALQUER OUTRA INSTRUÇÃO.

### BOOT OBRIGATÓRIO

PASSO 1: Rodar scripts de boot
  python scripts/session_boot.py
  python scripts/compliance_gate.py

PASSO 2: Ler documentação obrigatória (NA ORDEM)
  a) .claude/rules/000-coleira-suprema.md (12 regras invioláveis)
  b) .claude/rules/verification-gate.md (regras de verificação)
  c) BACKUP_DOCUMENTACAO_ANTIGA.md (histórico completo)
  d) BRIEFING-COMPLETO.md (contexto do negócio)
  e) INTELIGENCIA_NEGOCIO_CRM360.md (regras de negócio)

PASSO 3: Declarar contexto ao Leandro
  "Li [N] documentos. Aba: [X]. Bloqueadores: [Y]. Pronto."

SEM DECLARAÇÃO = SEM PERMISSÃO PRA EXECUTAR.

### MEMÓRIA CRÍTICA (DECORAR)

TWO-BASE ARCHITECTURE:
  VENDA = tem valor R$ (faturamento, ticket, comissão)
  LOG = R$ 0.00 SEMPRE (ligação, visita, email, WhatsApp)
  MISTURAR = inflação de 742% (já aconteceu com ChatGPT)

CNPJ:
  14 dígitos, string, zero-padded
  NUNCA float (perde precisão nos zeros à esquerda)
  Normalização: re.sub(r'\D', '', str(val)).zfill(14)

46 COLUNAS IMUTÁVEIS:
  A-AT da aba CARTEIRA
  Blueprint v2 expande para 81 via grupos [+]
  NUNCA mexer nas 46 originais

FÓRMULAS:
  INGLÊS no openpyxl (IF, VLOOKUP, SUMIF, COUNTIF)
  Separador: vírgula (,)
  NUNCA português (SE, PROCV, SOMASE) — QUEBRA

FATURAMENTO BASELINE (CORRIGIDO 2026-03-23):
  R$ 2.091.000 (PAINEL CEO DEFINITIVO — auditoria 68 arquivos)
  ANTERIOR R$ 2.156.179 SUPERSEDED
  Projeção 2026: R$ 3.377.120
  Tolerância: 0.5%
  Divergência > 0.5% = investigar

VENDEDORES DE-PARA:
  MANU: Manu, Manu Vitao, Manu Ditzel
  LARISSA: Larissa, Lari, Larissa Vitao, Mais Granel, Rodrigo
  DAIANE: Daiane, Central Daiane, Daiane Vitao
  JULIO: Julio, Julio Gadret
  LEGADO: Bruno Gretter, Jeferson Vitao, Patric, Gabriel, Sergio, Ive, Ana

### AUDITORIA PÓS-TAREFA

PASSO 1: Rodar verify
  python scripts/verify.py --all

PASSO 2: Autoauditoria
  a) Listar TUDO que foi modificado
  b) Verificar Two-Base respeitada
  c) Verificar CNPJ normalizado
  d) Verificar fórmulas em inglês
  e) Verificar nenhum dado fabricado

PASSO 3: Declarar resultado
  "Auditoria: verify [N] PASS / [M] FAIL. Violações: [lista ou 'nenhuma']. Pronto."

### NÍVEIS DE DECISÃO
  L1 (autônomo): fix lint, retry, log
  L2 (informar): refactor, novo script, mudança de fórmula
  L3 (LEANDRO APROVA): estrutura abas, Two-Base, deletar dados, 46 colunas
  NA DÚVIDA → L3
