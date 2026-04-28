# BRIEFING VSCode — 28/Abr/2026

## STATUS DE PRODUÇÃO + PRÓXIMOS PASSOS

Verificado por: Cowork (inspeção ao vivo em produção)
URL: https://frontend-one-liart-94.vercel.app
Data/hora: 28/Abr/2026, verificação ao vivo via Chrome

---

## STATUS DOS 3 BUGS CRÍTICOS

### ✅ BUG 1: CARTEIRA — RESOLVIDO

- `/carteira` carrega normalmente
- Mostrando 11.764 clientes com CNPJ, nome, UF, consultor, situação, temperatura, score, curva ABC, sinaleiro, faturamento
- Filtros funcionando: Consultor, Sinaleiro, Prioridade, UF, Situação (ATIVO/INAT.REC/INAT.ANT/PROSPECT/EM RISCO/LEAD/NOVO), Curva ABC, Temperatura
- Exportar CSV visível
- Nenhum crash observado

### ❌ BUG 2: INBOX — AINDA QUEBRADO

- `/inbox` mostra: "WhatsApp desconectado — mostrando últimos dados disponíveis"
- "Nenhuma conversa encontrada"
- "Nenhum ticket nos últimos 7 dias"
- **Diagnóstico técnico:**
  - `GET /api/whatsapp/inbox?dias=7` retorna HTTP 200 mas body = `{"detail": "Not authenticated"}`
  - `GET /api/whatsapp/status` retorna HTTP 200 mas body = `{"detail": "Not authenticated"}`
  - `GET /api/auth/me` retorna `{"detail": "Not authenticated"}`
  - As chamadas client-side não passam token de autenticação
  - As páginas que funcionam (Carteira, Agenda) usam SSR (server-side rendering) onde o auth funciona
  - **Causa raiz DUPLA:**
    1. Backend não tem dados Deskrio no PostgreSQL (JSONs extraídos mas nunca ingeridos)
    2. Chamadas client-side da Inbox não enviam token JWT — precisam usar SSR como as outras páginas
- **Fix necessário:**
  1. Migrar a Inbox para SSR (server component) como a Carteira e Agenda já fazem
  2. OU: implementar passagem de token nas chamadas client-side
  3. E: ingerir os dados Deskrio no PostgreSQL (11.534 contatos + 448 tickets dos JSONs)

### ✅ BUG 3: AGENDA — RESOLVIDO

- `/agenda` mostra "Agenda Comercial" com data correta (28/Abr/2026)
- 40 itens na agenda da LARISSA
- Tabs: MANU, LARISSA (40), DAIANE, JULIO, OUTROS
- "Resumo Semanal IA" visível
- Clientes com prioridade (P5), sinaleiro (LARANJA/VERDE), situação (INAT.REC/MORNO), score (64.5)
- Botão "Registrar Atendimento" e "Gerar Agenda" funcionando
- Busca por nome/CNPJ, filtro por Prioridade e Sinaleiro

---

## OUTRAS PÁGINAS VERIFICADAS

### Pipeline Kanban

- `/pipeline` carrega: "200 clientes no pipeline"
- FAT. ACUMULADO: R$ 1.228.212,71
- MAS: Colunas EM ATENDIMENTO (0), PEDIDO (0), POS-VENDA (0), FOLLOW-UP (0) — todas vazias
- Provável causa: mesma que a Inbox — dados de interação (Deskrio/WhatsApp) não ingeridos, logo ninguém está em nenhum estágio
- Não é crash, é falta de dados

---

## PRIORIDADES ATUALIZADAS

```
┌─────────────────────────────────────────────────────────────────┐
│  1º  FIX INBOX (Bug 2 remanescente)                            │
│      → Migrar para SSR OU passar token client-side              │
│      → Ingerir dados Deskrio no PostgreSQL                      │
│      → Testar: /inbox mostra conversas reais                    │
├─────────────────────────────────────────────────────────────────┤
│  2º  POPULAR PIPELINE                                           │
│      → Pipeline depende de dados de interação (mesmo do inbox)  │
│      → Após ingestão Deskrio, pipeline deve popular             │
│      → Verificar se engine de regras move cards automaticamente │
├─────────────────────────────────────────────────────────────────┤
│  3º  NOVA FEATURE: ANÁLISE CRÍTICA DO CLIENTE                   │
│      → Spec completa em SPEC_FEATURE_ANALISE_CRITICA_CRM.md    │
│      → MVP Sprint 1: schema + parsers + engine DRE + UI        │
│      → Golden master: Coelho Diniz                              │
│      → 5 ondas de implementação                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## SOBRE A FEATURE ANÁLISE CRÍTICA

Spec completa salva em: `SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md`

**Resumo para o VSCode:**
- 9 tabelas novas no PostgreSQL (6 de dados cliente + 2 mercado + 1 anomalias)
- 6 parsers de Excel (ZSDFAT + 4 LOG EFETIVADO + Último Praticado)
- Engine de regras Python puro (DRE L30-L35, sinaleiro SKU, detector anomalias)
- 1 aba nova no CRM: "Análise Crítica" por cliente
- LLM só no final (Resumo CEO) — nunca calcula
- Feature flag: `ANALISE_CRITICA_HABILITADA`

**Implementar em 5 ondas:**
1. Schema PostgreSQL + migrations
2. Parsers + testes unitários
3. Engine DRE + testes (Coelho Diniz golden master)
4. API REST (`GET /clientes/:id/analise-critica`)
5. UI React (1 página)

**PRÉ-REQUISITO:** Fix do Inbox (Bug 2) primeiro. A Análise Crítica é feature nova — não começa até o CRM base estar estável.

---

## DADOS PARA INGESTÃO (já extraídos, prontos)

| Arquivo | Registros | Tabela destino |
|---------|-----------|---------------|
| `data/INSERT_CONTATOS_WHATSAPP.json` | 11.534 | contatos_whatsapp |
| `data/deskrio/2026-04-15-v2/contacts.json` | 15.603 | contatos_whatsapp (bruto) |
| `data/deskrio/2026-04-15-v2/tickets_merged.json` | 448 | tickets/log_interacoes |
| `data/deskrio/2026-04-15-v2/kanban_cards_20.json` | 95 | kanban_cards |
| `data/deskrio/2026-04-15-v2/kanban_columns_20.json` | 10 | kanban_columns |

---

## TOKEN DESKRIO (VÁLIDO)

```
API: https://appapi.deskrio.com.br/v1/api/
Auth: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Company ID: 38
Expira: Dez/2026
```

---

## NAVEGAÇÃO 3 NÍVEIS (NOVA DECISÃO ARQUITETURAL)

Sidebar única com 6 itens fixos, conteúdo adaptativo por papel:
- **Vendedor:** Minha meta, meus clientes, meu pipeline, minha agenda
- **Gerente:** Meta time, ranking, todas carteiras, cross-cliente
- **CEO:** DDE consolidada, projeção, Painel CEO, Resumo CEO

Spec de navegação será formalizada após estabilizar Bug 2 + Pipeline.
