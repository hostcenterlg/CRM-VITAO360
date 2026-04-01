# Pipeline de Extração Diária — CRM VITAO360

> Spec técnica para alimentar o SaaS com dados de 3 fontes.
> Gerado: 2026-04-01 | Autor: Cowork

---

## Visão Geral

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  DESKRIO     │    │SALES HUNTER │    │   MERCOS    │
│  (API REST)  │    │ (Browser)   │    │  (Browser)  │
└──────┬───────┘    └──────┬──────┘    └──────┬──────┘
       │                   │                  │
       │  curl + JWT       │  Chrome ext.     │  Chrome ext.
       │                   │                  │
       └───────────┬───────┴──────────────────┘
                   │
          ┌────────▼────────┐
          │  CRM-VITAO360   │
          │  /data/          │
          │  (JSON + CSV)    │
          └────────┬────────┘
                   │
          ┌────────▼────────┐
          │  VSCode Claude  │
          │  ingest →       │
          │  PostgreSQL     │
          └─────────────────┘
```

**Agendamento**: Todo dia às 07:00 (horário de Brasília)
**Task ID**: `crm-extracao-diaria`

---

## FONTE 1: DESKRIO (Prioridade Máxima — 100% automatizável)

### Acesso
- **Tipo**: API REST pública (Swagger OAS 3.0)
- **Base URL**: `https://appapi.deskrio.com.br`
- **Docs**: `https://appapi.deskrio.com.br/docs/public/`
- **Auth**: Bearer JWT (expira Set/2026)
- **Login web**: app.deskrio.com.br (leandro.garcia@vitao.com.br)

### Endpoints Disponíveis (7 seções, 22 endpoints)

#### Mensagens (2)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/api/messages/{ticketId}` | Mensagens de um ticket |
| POST | `/v1/api/messages/send` | Enviar mensagem |

#### Kanban (5)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/api/kanban-boards` | Lista quadros Kanban |
| GET | `/v1/api/kanban-columns/{boardId}` | Colunas de um quadro |
| GET | `/v1/api/kanban-card/{boardId}` | Cards de um quadro |
| PUT | `/v1/api/kanban-cards/{cardId}` | Atualizar card |
| POST | `/v1/api/kanban-cards` | Criar card |

#### Chat Interno (4)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/api/internal-chat/users` | Usuários do chat |
| GET | `/v1/api/internal-chat/groups` | Grupos do chat |
| POST | `/v1/api/internal-chat/{chatId}/message` | Msg no chat |
| POST | `/v1/api/internal-chat/group/{groupId}/message` | Msg no grupo |

#### Extrainfo (3)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/api/extrainfo/field` | Campos extras (CNPJ, Código SAP, Estado) |
| PUT | `/v1/api/extrainfo/{contactId}` | Atualizar extras do contato |
| PUT | `/v1/api/extrainfo/kanban-boards/{cardId}` | Atualizar extras do card |

#### Tickets (5)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/api/ticket/{ticketId}` | Detalhes de um ticket |
| GET | `/v1/api/ticket-status/{ticketId}` | Status de um ticket |
| GET | `/v1/api/tickets?startDate=DD/MM/YYYY&endDate=DD/MM/YYYY` | Tickets por período |
| PUT | `/v1/api/ticket/update/{ticketId}` | Atualizar ticket |
| POST | `/v1/api/tickets/bulk-open` | Abrir tickets em lote |

#### WhatsApp API (2)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| POST | `/v1/api/whatsapp-api/template/send/{apiId}` | Enviar template |
| POST | `/v1/api/whatsapp-api/trigger/{apiId}` | Disparar template (API oficial) |

#### Conexões (1)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/api/connections` | Conexões disponíveis |

#### Contatos (5)
| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/v1/api/contacts` | Todos os contatos (15.539 em 01/Abr) |
| GET | `/v1/api/contact/id/{contactId}` | Contato por ID |
| GET | `/v1/api/contact/{number}` | Contato por número |
| GET | `/v1/api/custom-field/{number}` | Campos customizados |
| PUT | `/v1/api/tag/{contactId}` | Adicionar tag |

### Dados Validados (01/Abr/2026)
- **Contatos**: 15.539 registros
- **Tickets** (última semana): 154 registros
- **Kanban "Vendas Vitao"**: 95 cards (board id: 20)
- **Campos extras**: CNPJ, CNPJ 2, CNPJ 3, Código SAP, Estado
- **Usuários Kanban**: Daiane Stavicki, Larissa, Administrador

### Extração Diária (P1)
| Endpoint | Output | Frequência |
|----------|--------|------------|
| GET /contacts | `deskrio/YYYY-MM-DD/contacts.json` | Diário |
| GET /tickets (D-1) | `deskrio/YYYY-MM-DD/tickets.json` | Diário |
| GET /kanban-boards + cards | `deskrio/YYYY-MM-DD/kanban_*.json` | Diário |
| GET /extrainfo/field | `deskrio/YYYY-MM-DD/extrainfo_fields.json` | Semanal |
| GET /messages/{id} | `deskrio/YYYY-MM-DD/messages_*.json` | Diário (top 50) |
| GET /connections | `deskrio/YYYY-MM-DD/connections.json` | Semanal |

### IMPORTANTE: Deskrio → CRM Bridge
Os contatos Deskrio têm campos extras com CNPJ e Código SAP.
Isso permite cruzar Deskrio ↔ SAP/Mercos via CNPJ normalizado.
Este é o LINK entre atendimento (Deskrio) e vendas (Sales Hunter/Mercos).

---

## FONTE 2: SALES HUNTER (SAP Web Portal)

### Acesso
- **Tipo**: Portal web (browser automation)
- **URL**: `saleshunter.vitao.com.br/relatorios#`
- **Login**: leandro@maisgranel.com.br
- **Empresas**: VITAO Curitiba (cwb), VITAO Vila Velha (vv)
- **Export**: CSV/XLSX

### Relatórios Disponíveis (30+)

#### P1 — Diário (8 tipos × 2 empresas = 16 extrações)
| Relatório | Código | Conteúdo |
|-----------|--------|----------|
| Faturamento por Cliente | fat_cliente | Vendas por CNPJ |
| Faturamento NF Detalhe | fat_nf_det | Notas fiscais detalhadas |
| Faturamento por Produto | fat_produto | Vendas por SKU |
| Carteira de Clientes | carteira | Base ativa |
| Débitos | debitos | Inadimplência |
| Devolução por Cliente | devolucao_cliente | Devoluções |
| Faturamento por Empresa | fat_empresa | Consolidado |
| Pedidos por Produto | pedidos_produto | Pipeline pedidos |

#### P2 — Semanal (segundas-feiras)
fat_uf, fat_grupo_mat, mix_ativo, mix_fat, margem_produto, devolucao_produto

#### P3 — Mensal (dia 1)
hierarquia, lista_preco, desconto_fin, grupo_clientes, tempo_recebimento, produto_kg, grupo_mat_kg, produtos

### Naming Convention
```
data/sales_hunter/YYYY-MM-DD/morning/
  {tipo}_{empresa}_{vendedor}_{data}_{hora}.csv
```
Exemplo: `fat_cliente_cwb_all_2026-04-01_0700.csv`

### Dependência
Requer Chrome aberto e logado. Se indisponível → SKIP + log.

---

## FONTE 3: MERCOS

### Acesso
- **Tipo**: Portal web (browser automation) + API interna
- **URL**: `app.mercos.com/399424/`
- **Dados**: 6.429 clientes, 29 indicadores, 19 relatórios

### Extração Diária
- Clientes (via API interna do Mercos)
- Pedidos do dia
- Indicadores atualizados

### Dependência
Requer Chrome aberto e logado. Se indisponível → SKIP + log.

### Spec Completa
Ver: `MERCOS_SPEC_COMPLETA_SAAS.md` (mapeamento completo de todas as features)

---

## Estrutura de Output

```
CRM-VITAO360/data/
├── deskrio/
│   └── YYYY-MM-DD/
│       ├── contacts.json          (15K+ registros)
│       ├── tickets.json           (~20-30/dia)
│       ├── kanban_boards.json
│       ├── kanban_cards_20.json   (board Vendas Vitao)
│       ├── extrainfo_fields.json
│       ├── connections.json
│       └── messages_*.json        (top 50 tickets)
│
├── sales_hunter/
│   └── YYYY-MM-DD/
│       └── morning/
│           ├── fat_cliente_cwb_all_*.csv
│           ├── fat_cliente_vv_all_*.csv
│           └── ... (16 CSVs P1)
│
├── mercos/
│   └── YYYY-MM-DD/
│       ├── clientes.json
│       ├── pedidos.json
│       └── indicadores.json
│
├── extraction_report_YYYY-MM-DD.json  (relatório da extração)
└── latest_extraction.json             (ponteiro para mais recente)
```

---

## Relatório de Extração

Cada execução gera `extraction_report_YYYY-MM-DD.json`:

```json
{
  "timestamp": "2026-04-01T07:00:00-03:00",
  "sources": {
    "deskrio": {
      "status": "SUCCESS",
      "contacts": 15539,
      "tickets": 28,
      "kanban_cards": 95,
      "messages": 50,
      "duration_seconds": 45
    },
    "sales_hunter": {
      "status": "SKIPPED",
      "reason": "Chrome not available",
      "reports_extracted": 0
    },
    "mercos": {
      "status": "SUCCESS",
      "clients": 6429,
      "orders": 12,
      "duration_seconds": 120
    }
  },
  "total_records": 22141,
  "errors": []
}
```

---

## Handoff para VSCode

O VSCode Claude consome os dados extraídos via scripts de ingestão:

1. `backend/scripts/ingest_deskrio.py` — JSON → PostgreSQL
2. `backend/scripts/ingest_sales_hunter.py` — CSV → PostgreSQL
3. `backend/scripts/ingest_mercos.py` — JSON → PostgreSQL

Os scripts devem:
- Normalizar CNPJ (14 dígitos, string, zero-padded)
- Respeitar Two-Base Architecture (VENDA ≠ LOG)
- Classificar dados como Tier REAL
- Criar reconciliação entre fontes via CNPJ

---

## Cronograma

| Horário | Ação |
|---------|------|
| 07:00 | Task automática dispara |
| 07:01 | Deskrio API (curl, sempre funciona) |
| 07:05 | Sales Hunter browser (se Chrome aberto) |
| 07:15 | Mercos browser (se Chrome aberto) |
| 07:20 | Gera extraction_report |
| 07:25 | Notifica conclusão |

---

## Token Deskrio

- **Tipo**: JWT (HS256)
- **Emissão**: ~12/Mar/2026
- **Expiração**: ~Set/2026
- **Perfil**: admin
- **CompanyId**: 38
- **AÇÃO NECESSÁRIA**: Renovar token antes de Set/2026
