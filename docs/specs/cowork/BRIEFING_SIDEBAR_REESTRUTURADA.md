# BRIEFING: Reestruturar Sidebar — Nova Ordem de Navegação

> **Data:** 29/Abr/2026 · **Prioridade:** ALTA (fazer JUNTO com Inbox)
> **De:** Leandro (via Cowork)
> **Para:** VSCode Claude Code
> **Contexto:** Leandro definiu a nova sidebar após ver o estado atual. Sidebar é shell global (layout.tsx).

---

## DECISÃO DO LEANDRO — NOVA SIDEBAR

### ANTES (sidebar atual — 9 itens):
```
1. Inbox
2. Pipeline
3. Agenda
4. Tarefas
5. Carteira
6. RNC
7. Pedidos
8. Inteligência IA
9. Manual
```

### DEPOIS (nova sidebar — 7 itens):
```
1. Inbox              ← mantém (posição 1)
2. Inteligência IA    ← sobe de #8 para #2
3. Agenda + Tarefas   ← UNIFICAR em 1 item (era #3 e #4 separados)
4. Pedidos            ← mantém
5. Clientes           ← RENOMEAR "Carteira" → "Clientes"
6. Produtos           ← NOVO (não existe hoje)
7. Manual             ← mantém (último)
```

### REMOVIDOS DA SIDEBAR:
- ❌ **Pipeline** — sai da sidebar
- ❌ **RNC** — sai da sidebar

> **Nota:** Pipeline e RNC não são deletados do código. Apenas saem da sidebar.
> Pipeline pode virar sub-aba dentro de outra tela no futuro.

---

## ESPECIFICAÇÕES POR ITEM

### 1. Inbox (sem mudança de posição)
- Ícone: `MessageSquare` (Lucide) ou equivalente WhatsApp
- Badge: contador de mensagens não lidas (número)
- Rota: `/inbox`
- **Execução completa está no briefing:** `BRIEFING_INBOX_CONVERSAS_COMO_DEMO.md`

### 2. Inteligência IA (mover para #2)
- Ícone: `Brain` ou `Sparkles` (Lucide)
- Label: "Inteligência IA"
- Rota: `/inteligencia` (ou como está hoje)
- Sem badge por enquanto

### 3. Agenda + Tarefas (UNIFICAR)
- Ícone: `CalendarCheck` (Lucide) — combina calendário + check
- Label: "Agenda"
- Rota: `/agenda` (rota única)
- **UX da unificação:**

```
┌─────────────────────────────────────────────────┐
│  Agenda                                          │
│                                                  │
│  [📅 Compromissos]  [✅ Tarefas]    ← tabs     │
│  ─────────────────────────────────               │
│                                                  │
│  Tab Compromissos:                               │
│  - Calendário visual (dia/semana)                │
│  - Reuniões, visitas, follow-ups agendados       │
│  - Sinaleiros de atraso (vermelho se vencido)    │
│                                                  │
│  Tab Tarefas:                                    │
│  - Lista de tarefas do vendedor                  │
│  - Checkboxes para concluir                      │
│  - Filtro: Pendentes / Concluídas / Atrasadas    │
│  - Criar nova tarefa inline                      │
│                                                  │
│  AMBAS as tabs mostram itens de HOJE em destaque │
│  com contagem no topo: "3 compromissos · 5 tasks"│
└─────────────────────────────────────────────────┘
```

- **Regra UX:** ao clicar "Agenda" na sidebar, abre na tab que tiver mais itens pendentes para hoje
- Badge na sidebar: total de itens para hoje (compromissos + tarefas pendentes)
- A página de Agenda que já existe (com 40 items da Larissa) é a base — só adicionar a tab Tarefas

### 4. Pedidos (sem mudança)
- Ícone: `ShoppingCart` ou `Package` (Lucide)
- Label: "Pedidos"
- Rota: `/pedidos`
- Badge: pedidos pendentes (se houver lógica)

### 5. Clientes (renomear de "Carteira")
- Ícone: `Users` (Lucide)
- Label: "Clientes" (NÃO "Carteira")
- Rota: `/clientes` (pode manter `/carteira` internamente e fazer redirect, ou renomear)
- Funcionalidade: exatamente igual ao que "Carteira" faz hoje (11.764 clientes, filtros, score, ABC, sinaleiro)
- Badge: nenhum

### 6. Produtos (NOVO)
- Ícone: `Box` ou `Package` (Lucide)
- Label: "Produtos"
- Rota: `/produtos`
- **Conteúdo mínimo para existir (placeholder funcional):**

```
┌─────────────────────────────────────────────────┐
│  Produtos                                        │
│                                                  │
│  [🔍 Buscar produto...]                         │
│                                                  │
│  Lista de produtos com:                          │
│  - Código SKU (codigo_produto)                   │
│  - Descrição                                     │
│  - Preço tabela                                  │
│  - Custo comercial (se disponível, tabela        │
│    produto_custo_comercial)                      │
│  - Margem % calculada                            │
│                                                  │
│  Fonte: tabela produto_custo_comercial           │
│  (criada pela DDE_MIGRATION_002_CMV.sql)         │
│                                                  │
│  Se tabela vazia: mostrar mensagem               │
│  "Dados de produtos serão importados em breve"   │
│  com ícone de Box vazio                          │
└─────────────────────────────────────────────────┘
```

- **Backend:** endpoint `GET /api/produtos` que faz `SELECT * FROM produto_custo_comercial ORDER BY descricao`
- Se a tabela não tiver dados ainda, retorna `[]` e o frontend mostra empty state
- **Futuro:** esta tela será enriquecida com mix por cliente, ranking de produtos, etc.

### 7. Manual (sem mudança)
- Ícone: `BookOpen` (Lucide)
- Label: "Manual"
- Rota: `/manual`
- Último item, separador visual antes dele (divider line)

---

## IMPLEMENTAÇÃO TÉCNICA

### Arquivo principal da sidebar
Procurar em: `components/Sidebar.tsx`, `components/Layout.tsx`, ou `app/layout.tsx`
O array de navegação provavelmente é algo como:

```tsx
const navItems = [
  { label: 'Inbox',           icon: MessageSquare, href: '/inbox',         badge: unreadCount },
  { label: 'Inteligência IA', icon: Brain,         href: '/inteligencia'  },
  { label: 'Agenda',          icon: CalendarCheck,  href: '/agenda',        badge: todayCount },
  { label: 'Pedidos',         icon: ShoppingCart,   href: '/pedidos'       },
  { label: 'Clientes',        icon: Users,          href: '/clientes'      },
  { label: 'Produtos',        icon: Box,            href: '/produtos'      },
  // --- divider ---
  { label: 'Manual',          icon: BookOpen,       href: '/manual'        },
]
```

### Checklist de execução

1. [ ] Alterar array de navegação na sidebar (nova ordem, 7 itens)
2. [ ] Remover Pipeline e RNC do array
3. [ ] Renomear "Carteira" → "Clientes" (label + ícone)
4. [ ] Unificar Agenda + Tarefas → página única com tabs
5. [ ] Criar página `/produtos` (placeholder com empty state)
6. [ ] Criar endpoint `GET /api/produtos`
7. [ ] Adicionar badges dinâmicos (Inbox = não lidas, Agenda = hoje)
8. [ ] Testar que todas as 7 rotas funcionam
9. [ ] Mobile: sidebar vira bottom nav ou hamburger (5 itens visíveis + "Mais")

---

## ORDEM DE EXECUÇÃO (sugerida)

**Sprint Sidebar (2-3h):**
1. Alterar o array + ícones + labels (30min)
2. Renomear Carteira → Clientes (15min)
3. Unificar Agenda + Tarefas em tabs (1h)
4. Criar /produtos placeholder + endpoint (45min)
5. Badges dinâmicos (30min)
6. Testar mobile (15min)

**PODE ser feito em paralelo com o Inbox** — sidebar é shell global, Inbox é conteúdo da rota.

---

## NÃO FAZER

- ❌ Não deletar código de Pipeline/RNC — só tirar da sidebar nav
- ❌ Não implementar funcionalidade complexa em Produtos — é placeholder
- ❌ Não mudar o layout da sidebar (largura, cores, posição) — só o conteúdo dos itens
- ❌ Não inventar itens que Leandro não pediu

---

**Versão:** 1.0 — 29/Abr/2026
**Autor:** Cowork (revisor) + Leandro
**Próximo passo após sidebar:** Inbox demo-quality → DDE + Análise Crítica
