# SPEC: Arquitetura de Navegação 3 Níveis

Versão: 1.0 · Data: 28/04/2026 · Owner: Leandro · Status: spec

---

## 1. PROBLEMA

A sidebar atual tem **20 itens** em 3 grupos. O vendedor vê 9 itens no grupo CRM, não sabe por onde começar. O gerente vê 15 itens. O admin vê 20. E ainda vão chegar: Análise Crítica, DDE, Cross-Cliente, Resumo CEO. Se continuar assim, a sidebar vira menu de restaurante chinês.

**Sidebar atual (Sidebar.tsx):**

```
CRM (todos):        Inbox, Pipeline, Agenda, Tarefas, Carteira, Sinaleiro, Pedidos, IA, Manual
Gestão (gerente+):  Dashboard, Projecao, Redes, RNC, Produtos, Relatorios
Admin (admin):      Motor, Usuarios, Import, Redistribuir, Atualizacoes
```

**Problema real:** não é só visual. O vendedor não precisa ver Projeção, Redes, RNC, Produtos. O CEO não precisa ver Tarefas, Inbox com conversas. Mostrar tudo pra todos gera ruído, cliques perdidos, e zero foco.

---

## 2. SOLUÇÃO: SIDEBAR ÚNICA, 6 ITENS, CONTEÚDO ADAPTATIVO

### Princípio: "Mesma casa, andares diferentes"

A sidebar tem as **mesmas 6 seções** pra todo mundo. O que muda é o conteúdo dentro de cada seção — controlado por widgets de permissão, não por esconder/mostrar itens do menu.

```
┌──────────────┐
│  🏠 Início   │ ← cockpit do dia (adaptativo por role)
│  👥 Clientes │ ← carteira + sinaleiro + ficha + análise crítica
│  📋 Pipeline │ ← kanban + inbox + pedidos
│  📅 Agenda   │ ← atividades + tarefas + RNC
│  📊 Análises │ ← relatórios + projeção + IA + redes + cross-cliente
│  ⚙ Config    │ ← admin only (motor, users, import, etc.)
│              │
│  V           │ ← CRM VITAO360
└──────────────┘
```

**De 20 itens → 6.** Nenhuma rota é deletada — são reagrupadas.

---

## 3. MAPEAMENTO: ROTAS ATUAIS → NOVA ESTRUTURA

### 3.1 Início (`/`)

**Substitui:** `/dashboard` (atual), `/` (home page)

| Role | Widgets que vê |
|------|---------------|
| **Vendedor** | Meta diária (%), Clientes em risco (top 5), Atividades hoje (próximos 3), Alertas pessoais |
| **Gerente** | Meta time (barra por vendedor), Ranking vendedores (tabela), Alertas time, + tudo do vendedor filtrado |
| **CEO** | DDE consolidada (KPI strip), Projeção anual (gráfico), Top 10 clientes (faturamento + sinal), Anomalias críticas abertas |

**Widgets são componentes React independentes.** Cada widget tem um `requiredRole: 'vendedor' | 'gerente' | 'admin'`. O container renderiza só os widgets que o role do usuário permite.

### 3.2 Clientes (`/clientes`)

**Substitui:** `/carteira`, `/sinaleiro`

**Sub-tabs no topo da página (não na sidebar):**

| Sub-tab | Antes era | Quem vê |
|---------|-----------|---------|
| Carteira | `/carteira` | Todos |
| Sinaleiro | `/sinaleiro` | Todos |
| Prospects | Novo | Vendedor + Gerente |

**Detalhe do cliente** (`/clientes/:id`): ao clicar num cliente, abre ficha com tabs internas:

| Tab na ficha | Conteúdo | Prioridade |
|-------------|----------|------------|
| Resumo | Dados cadastrais, KPIs, último contato, score | Existe |
| Análise Crítica | DRE + anomalias + ações + Resumo CEO | **NOVO** (SPEC_FEATURE_ANALISE_CRITICA) |
| Histórico | Timeline de interações (inbox, visitas, pedidos) | Existe parcial |
| Mix Produtos | SKUs ativos, sinaleiro por SKU | **NOVO** |
| Pedidos | Pedidos do cliente | Redirect de `/pedidos?cliente=X` |

**Visão por role:**

| Role | O que muda |
|------|-----------|
| Vendedor | Vê só SUA carteira (filtro `consultor = meu_usuario`). Pode registrar atendimento, ver análise crítica dos seus clientes. |
| Gerente | Vê TODAS as carteiras. Filtro por vendedor no topo. Vê cross-cliente (tab extra "Comparativo"). Aba Análise Crítica em modo completo (veredito + ações + Resumo CEO). |
| CEO | Vê Top 20 faturamento por padrão. Aba Análise Crítica com botão "Gerar Resumo CEO PDF". Comparativo cross-cliente como view default. |

### 3.3 Pipeline (`/pipeline`)

**Substitui:** `/pipeline`, `/inbox`, `/pedidos`

**Sub-tabs:**

| Sub-tab | Antes era | Quem vê |
|---------|-----------|---------|
| Kanban | `/pipeline` | Todos |
| Inbox | `/inbox` | Vendedor + Gerente |
| Pedidos | `/pedidos` | Todos |

**Por que agrupar Inbox aqui:** Inbox (conversas WhatsApp/Deskrio) é parte do fluxo de vendas. Uma conversa vira um atendimento, que vira um pedido, que move o card no Kanban. Estão no mesmo fluxo.

**Visão por role:**

| Role | O que muda |
|------|-----------|
| Vendedor | Kanban: meus cards. Inbox: minhas conversas. Pedidos: meus pedidos. |
| Gerente | Kanban: todos + filtro vendedor. Inbox: todas conversas + métricas (tempo resposta, volume). Pedidos: todos + gargalos. |
| CEO | Kanban: consolidado (total por estágio). Inbox: NÃO vê (irrelevante). Pedidos: volume total + ticket médio. |

### 3.4 Agenda (`/agenda`)

**Substitui:** `/agenda`, `/tarefas`, `/rnc`

**Sub-tabs:**

| Sub-tab | Antes era | Quem vê |
|---------|-----------|---------|
| Agenda | `/agenda` | Todos |
| Tarefas | `/tarefas` | Todos |
| RNC | `/rnc` | Gerente + Admin |

**Por que agrupar:** Tarefas e RNC são "coisas pra fazer". Agenda é "quando fazer". Mesmo contexto operacional.

**Visão por role:**

| Role | O que muda |
|------|-----------|
| Vendedor | Agenda: minhas visitas/calls. Tarefas: minhas pendências. Badge com contagem. |
| Gerente | Agenda: time completo + cobertura geográfica. Tarefas: time + delegação. RNC: fila de aprovação. |
| CEO | Agenda: só reuniões key accounts (se houver). Tarefas: não vê. RNC: não vê. |

### 3.5 Análises (`/analises`)

**Substitui:** `/relatorios`, `/projecao`, `/redes`, `/produtos`, `/ia`

**Sub-tabs:**

| Sub-tab | Antes era | Quem vê |
|---------|-----------|---------|
| Desempenho | `/relatorios` | Todos |
| Projeção | `/projecao` | Gerente + CEO |
| Produtos | `/produtos` | Gerente + Admin |
| Redes | `/redes` | Gerente + Admin |
| IA | `/ia` | Todos |

**Visão por role:**

| Role | O que muda |
|------|-----------|
| Vendedor | Desempenho: MEU faturamento, mix, devolução, meta. IA: chat sobre meus clientes. |
| Gerente | Desempenho: comparativo vendedores, DDE por canal, cross-cliente. Projeção: forecast time. Produtos: catálogo + curva ABC. Redes: gestão de franquias/redes. |
| CEO | Desempenho: Painel CEO (DDE consolidada, P&L, tendência 12m). Projeção: forecast anual + cenários. Cross-cliente como view principal. |

### 3.6 Config (`/admin`)

**Substitui:** `/admin/motor`, `/admin/usuarios`, `/admin/import`, `/admin/redistribuir`, `/atualizacoes`, `/docs`, `/manual`

**Sub-tabs:**

| Sub-tab | Antes era | Quem vê |
|---------|-----------|---------|
| Motor | `/admin/motor` | Admin |
| Usuários | `/admin/usuarios` | Admin |
| Import | `/admin/import` | Admin |
| Redistribuir | `/admin/redistribuir` | Admin |
| Manual | `/docs` ou `/manual` | Todos |
| Atualizações | `/atualizacoes` | Todos |

**Nota:** Manual e Atualizações ficam visíveis pra todos, mas dentro de Config. Alternativa: mover Manual pro header como "?" e Atualizações como toast/notification — decisão de UX a validar.

---

## 4. MODELO DE PERMISSÕES

### 4.1 Roles

```typescript
type UserRole = 'vendedor' | 'gerente' | 'admin';

// Mapeamento atual do AuthContext:
// isAdmin → role === 'admin'
// isGerenteOuAdmin → role === 'gerente' || role === 'admin'
// Vendedor → default (nem gerente, nem admin)
```

### 4.2 Visibilidade de Sub-tabs

```typescript
interface SubTab {
  id: string;
  label: string;
  href: string;
  minRole: UserRole;  // 'vendedor' = todos, 'gerente' = gerente+admin, 'admin' = admin only
}

const CLIENTES_TABS: SubTab[] = [
  { id: 'carteira',  label: 'Carteira',  href: '/clientes',          minRole: 'vendedor' },
  { id: 'sinaleiro', label: 'Sinaleiro', href: '/clientes/sinaleiro', minRole: 'vendedor' },
  { id: 'prospects', label: 'Prospects', href: '/clientes/prospects', minRole: 'vendedor' },
];
```

### 4.3 Filtro automático por vendedor

```typescript
// No Sidebar ou AppShell, injeta o filtro automaticamente:
function getDefaultFilter(user: User, section: string): Record<string, string> {
  if (user.role === 'vendedor') {
    return { consultor: user.nome_consultor };
  }
  return {}; // gerente/admin vê tudo
}
```

**Regra:** Vendedor NUNCA vê dados de outro vendedor na view padrão. Pode buscar clientes de outros consultores na busca global (se permitido), mas a listagem default é sempre filtrada.

---

## 5. ONDE ENTRA CADA FEATURE NOVA

| Feature | Onde na navegação | Como acessa |
|---------|-------------------|-------------|
| **Análise Crítica** | Clientes → ficha do cliente → tab "Análise Crítica" | Click no cliente → tab |
| **DDE** | Dentro da Análise Crítica (é a seção DRE da AC) | Dentro da tab Análise Crítica |
| **Cross-Cliente** | Análises → Desempenho (gerente/CEO view) | Sub-tab ou widget |
| **Resumo CEO** | Clientes → ficha → AC → botão "Gerar" | Botão na Análise Crítica |
| **Painel CEO** | Início (CEO view) | É o cockpit do CEO |
| **Comparativo** | Clientes (gerente view) → tab "Comparativo" | Tab extra na Carteira |

---

## 6. IMPACTO NO CÓDIGO ATUAL

### 6.1 Sidebar.tsx — Rewrite

```typescript
// DE:
const navGroups: NavGroup[] = [
  { label: 'CRM', items: [/* 9 items */] },
  { label: 'Gestao', items: [/* 6 items */], gerenteOuAdmin: true },
  { label: 'Admin', items: [/* 5 items */], adminOnly: true },
];

// PARA:
const navItems: NavItem[] = [
  { href: '/',         label: 'Início',   icon: HomeIcon },
  { href: '/clientes', label: 'Clientes', icon: UsersIcon },
  { href: '/pipeline', label: 'Pipeline', icon: KanbanIcon },
  { href: '/agenda',   label: 'Agenda',   icon: CalendarIcon },
  { href: '/analises', label: 'Análises', icon: ChartIcon, minRole: 'vendedor' },
  { href: '/admin',    label: 'Config',   icon: GearIcon,  minRole: 'admin' },
];
```

### 6.2 Rotas — Redirect Compatibility

As rotas antigas continuam funcionando via redirect:

```typescript
// next.config.js ou middleware.ts
const REDIRECTS = [
  { source: '/carteira',   destination: '/clientes' },
  { source: '/sinaleiro',  destination: '/clientes/sinaleiro' },
  { source: '/inbox',      destination: '/pipeline/inbox' },
  { source: '/pedidos',    destination: '/pipeline/pedidos' },
  { source: '/tarefas',    destination: '/agenda/tarefas' },
  { source: '/rnc',        destination: '/agenda/rnc' },
  { source: '/relatorios', destination: '/analises' },
  { source: '/projecao',   destination: '/analises/projecao' },
  { source: '/redes',      destination: '/analises/redes' },
  { source: '/produtos',   destination: '/analises/produtos' },
  { source: '/ia',         destination: '/analises/ia' },
  { source: '/dashboard',  destination: '/' },
  { source: '/docs',       destination: '/admin/manual' },
  { source: '/manual',     destination: '/admin/manual' },
  { source: '/atualizacoes', destination: '/admin/atualizacoes' },
];
```

**Nenhuma rota é deletada.** Todas redirecionam. Bookmarks e links salvos continuam funcionando.

### 6.3 Sub-tab Component (novo)

```typescript
// components/SubTabs.tsx
interface SubTabsProps {
  tabs: SubTab[];
  activeTab: string;
}

function SubTabs({ tabs, activeTab }: SubTabsProps) {
  const { user } = useAuth();
  const visibleTabs = tabs.filter(t => hasMinRole(user.role, t.minRole));
  
  return (
    <div className="border-b border-gray-200 mb-4">
      <nav className="flex gap-6 px-4">
        {visibleTabs.map(tab => (
          <Link
            key={tab.id}
            href={tab.href}
            className={activeTab === tab.id ? 'border-b-2 border-green-600 text-green-700' : 'text-gray-500'}
          >
            {tab.label}
          </Link>
        ))}
      </nav>
    </div>
  );
}
```

### 6.4 Widget System (novo)

```typescript
// components/Widget.tsx
interface WidgetConfig {
  id: string;
  component: React.ComponentType;
  minRole: UserRole;
  section: string;  // 'inicio', 'clientes', etc.
  order: number;
}

const WIDGETS: WidgetConfig[] = [
  // Início — Vendedor
  { id: 'meta-diaria',      component: MetaDiaria,      minRole: 'vendedor', section: 'inicio', order: 1 },
  { id: 'clientes-risco',   component: ClientesRisco,   minRole: 'vendedor', section: 'inicio', order: 2 },
  { id: 'atividades-hoje',  component: AtividadesHoje,   minRole: 'vendedor', section: 'inicio', order: 3 },
  
  // Início — Gerente (vê tudo acima + estes)
  { id: 'meta-time',        component: MetaTime,         minRole: 'gerente',  section: 'inicio', order: 0 },
  { id: 'ranking-vendedores', component: RankingVendedores, minRole: 'gerente', section: 'inicio', order: 1 },
  { id: 'alertas-time',     component: AlertasTime,      minRole: 'gerente',  section: 'inicio', order: 2 },
  
  // Início — CEO (vê tudo acima + estes)
  { id: 'dde-consolidada',  component: DDEConsolidada,   minRole: 'admin',    section: 'inicio', order: 0 },
  { id: 'projecao-anual',   component: ProjecaoAnual,    minRole: 'admin',    section: 'inicio', order: 1 },
];

function WidgetGrid({ section }: { section: string }) {
  const { user } = useAuth();
  const widgets = WIDGETS
    .filter(w => w.section === section && hasMinRole(user.role, w.minRole))
    .sort((a, b) => a.order - b.order);
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {widgets.map(w => <w.component key={w.id} />)}
    </div>
  );
}
```

---

## 7. CASO ESPECIAL: DAIANE

Daiane é **gerente E vendedora de key accounts**. Na navegação antiga, ela precisaria alternar entre "modo vendedor" e "modo gerente". Na nova:

- Ela tem role `gerente`
- No Início, vê Meta Time (gerente) + Meta Diária dela (vendedor) — ambos os widgets
- Em Clientes, vê todas as carteiras MAS pode filtrar "Minhas" pra focar nos key accounts
- Em Pipeline, vê todos os deals + os dela destacados
- Toggle "Minha Visão / Visão Time" no header resolve sem mudar de role

```
┌─ Header ──────────────────────────────────────┐
│  Clientes                                      │
│  [Minha Carteira ▾]  ou  [Time Completo ▾]     │
│  Carteira | Sinaleiro | Prospects | Comparativo│
└────────────────────────────────────────────────┘
```

---

## 8. MOBILE (BottomNav)

O `BottomNav.tsx` já existe. Na nova arquitetura:

```
┌──────┬──────┬──────┬──────┬──────┐
│Início│Client│Pipel.│Agenda│ Mais │
└──────┴──────┴──────┴──────┴──────┘
```

"Mais" abre drawer com: Análises, Config, Manual, Perfil.

5 itens no bottom nav (padrão iOS/Android — nunca mais que 5).

---

## 9. IMPLEMENTAÇÃO — ONDAS

### Onda 1 — Sidebar Rewrite (1 dia)
- [ ] Reescrever `Sidebar.tsx` de 20 itens → 6 itens
- [ ] Criar componente `SubTabs.tsx`
- [ ] Configurar redirects em `next.config.js`
- [ ] Testar: todas as rotas antigas funcionam via redirect

### Onda 2 — Reagrupar Páginas (2-3 dias)
- [ ] Mover `/carteira` → `/clientes` (com sub-tab Carteira)
- [ ] Mover `/sinaleiro` → `/clientes/sinaleiro`
- [ ] Mover `/inbox` → `/pipeline/inbox`
- [ ] Mover `/pedidos` → `/pipeline/pedidos`
- [ ] Mover `/tarefas` → `/agenda/tarefas`
- [ ] Mover `/rnc` → `/agenda/rnc`
- [ ] Mover `/relatorios`, `/projecao`, `/redes`, `/produtos`, `/ia` → `/analises/*`

### Onda 3 — Widget System + Início Adaptativo (2 dias)
- [ ] Criar `WidgetGrid` component
- [ ] Criar widgets iniciais (MetaDiaria, ClientesRisco, AtividadesHoje)
- [ ] Implementar Início com widgets por role
- [ ] Toggle "Minha Visão / Visão Time" pra gerentes

### Onda 4 — Filtro Automático por Vendedor (1 dia)
- [ ] Implementar `getDefaultFilter()` no AppShell
- [ ] Aplicar filtro automático em Carteira, Pipeline, Agenda
- [ ] Validar: vendedor só vê seus dados na view padrão

### Onda 5 — Mobile BottomNav Update (0.5 dia)
- [ ] Atualizar `BottomNav.tsx` pra 5 itens
- [ ] "Mais" drawer com seções restantes

---

## 10. DECISÕES L3 NECESSÁRIAS

| # | Decisão | Impacto |
|---|---------|---------|
| 1 | Aprovar reestruturação de 20 → 6 itens | Toda navegação muda |
| 2 | Inbox vai pra dentro de Pipeline ou fica separado? | UX de conversas |
| 3 | Manual/Atualizações ficam em Config ou viram ícone no header? | Acessibilidade |
| 4 | Toggle "Minha Visão / Visão Time" — implementar na Onda 3 ou depois? | Scope |
| 5 | Config fica visível pra todos (com itens filtrados) ou some completamente pra vendedor? | Sidebar vendedor: 5 ou 6 itens |

---

## 11. RELAÇÃO COM OUTRAS SPECS

| Spec | Como se conecta |
|------|----------------|
| SPEC_FEATURE_ANALISE_CRITICA | Análise Crítica = tab dentro de `/clientes/:id` |
| SPEC_DDE_CLIENTE (superseded) | DDE vive dentro da Análise Crítica |
| Painel CEO | É o "Início" do role admin/CEO |
| Briefing VSCode 28/Abr | Fix Inbox primeiro, depois nav rewrite |

---

## 12. PRÉ-REQUISITOS

1. **Bug 2 (Inbox) fixado** — não faz sentido mover Inbox pra Pipeline se ela não funciona
2. **Pipeline populado** — não faz sentido agrupar se tudo está vazio
3. **AuthContext com roles claros** — já existe (`isAdmin`, `isGerenteOuAdmin`), mas precisa de `user.role` explícito

**Sequência recomendada:** Fix Inbox → Popular Pipeline → Nav Rewrite (Onda 1-5)

---

*Versão 1.0 — 28/04/2026*
*Baseada em: Sidebar.tsx atual (20 itens), AppShell.tsx, discussão sobre 3 níveis, personas VITAO360.*
