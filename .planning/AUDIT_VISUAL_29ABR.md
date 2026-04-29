# Auditoria Visual UX — 29/Abr/2026

> **Auditor:** SQUAD ALPHA (gsd-ui-auditor)
> **Escopo:** 10 páginas + componentes principais
> **Severidade:** P0 (bloqueante) / P1 (alta) / P2 (média) / P3 (baixa)
> **Screenshots:** não capturados (sem dev server ativo — auditoria por código)
> **Baseline:** abstract 6-pillar standards + regras R9 do projeto

---

## SUMÁRIO EXECUTIVO

- **Total de issues:** 47
- **P0:** 6 | **P1:** 16 | **P2:** 17 | **P3:** 8
- **Top 3 problemas estruturais:**
  1. **Epidemia de texto sub-10px:** 527 ocorrências de `text-[9px]`, `text-[8px]`, `text-[10px]`, `text-[11px]` em 46 arquivos. O sistema literalmente reproduce o problema do Excel (9-10pt) no browser. Ilegível sem zoom.
  2. **Baixo contraste sistêmico:** 681 ocorrências de `text-gray-300`, `text-gray-400`, `text-gray-500` em fundos brancos. Gray-400 (#9CA3AF sobre #FFFFFF = contraste 2.85:1 — abaixo do mínimo WCAG AA de 4.5:1 para texto normal).
  3. **Filtro "Food" invisível:** o filtro de canal não existe na UI da Carteira. O backend filtra por `canal_id` (integer), mas a página `carteira/page.tsx` não expõe seletor de canal. Todos os clientes FOOD_SERVICE ficam atrás de um filtro que o usuário não consegue acionar.

---

## PROBLEMAS GLOBAIS (afetam toda a app)

### [P0] **Epidemia de texto sub-12px**
527 ocorrências de tamanhos sub-mínimos (`text-[8px]`, `text-[9px]`, `text-[10px]`, `text-[11px]`) em 46 arquivos TSX. No browser moderno com DPI alto, 10px corresponde a ~7.5pt — inelegível. Esse padrão replica o Excel 9pt que causou a reclamação original do Leandro.

Arquivos mais afetados:
- `app/inbox/page.tsx`: 90+ ocorrências (badges, timestamps, labels em quase todo o componente)
- `app/page.tsx` (dashboard): 40+ ocorrências (`text-[10px]` em cabeçalhos de tabela, labels de gráfico)
- `components/Sidebar.tsx`: `text-[10px]` nos group labels e no footer; `text-[9px]` em badge contadores
- `components/AppShell.tsx`: `text-[10px]` no badge de role, no InboxBadge
- `components/ui/Badge.tsx` linha 31: `xs: 'text-[10px] px-1.5 py-0 leading-4'` — o tamanho `xs` da badge é definido como 10px, fazendo todo badge xs ser ilegível

### [P0] **Contraste WCAG insuficiente — texto cinza-claro sobre branco**
`text-gray-300` (#D1D5DB sobre #FFFFFF) = contraste 1.61:1 — falha catastrófica.
`text-gray-400` (#9CA3AF sobre #FFFFFF) = contraste 2.85:1 — falha WCAG AA (mínimo 4.5:1 para texto body, 3:1 para texto grande).
681 ocorrências totais de gray-300/400/500 usados como cor de texto em conteúdo semântico.

Casos críticos:
- `app/page.tsx:1010-1011`: `text-gray-400` + `text-gray-300` em mensagem de estado vazio ("Dados indisponíveis")
- `app/page.tsx:1298`: `text-gray-300` em linha de instrução
- `components/Sidebar.tsx:619`: `text-[10px] text-gray-300` no footer "v1.0 — 2026" (combinação mortal: 10px + gray-300)
- `components/AppShell.tsx`: `text-gray-400` no breadcrumb (gray-400 = baixo contraste em texto de navegação)
- `app/inbox/page.tsx:384`: `text-gray-400` para texto de instrução de estado vazio

### [P0] **Filtro "Food" (canal FOOD_SERVICE) ausente na UI da Carteira** [CROSS-SQUAD]
Ver seção dedicada abaixo.

### [P1] **Inconsistência de tokens de cor — dois sistemas de verde em paralelo**
O `tailwind.config.ts` define `vitao.verde = '#00B050'` (nome PT) e `vitao.green = '#00A859'` (nome EN). São tons diferentes de verde usados ao mesmo tempo:
- `bg-vitao-green` (EN, #00A859) no Sidebar brand header, Avatar, StatusDot
- `text-vitao-green` (EN) nos links ativos da Sidebar
- `bg-[#00B050]` hardcoded no Sidebar collapsed active state
- `style={{ color: '#00B050' }}` em múltiplos lugares do Dashboard

Isso produz duas tonalidades de verde visíveis simultaneamente sem razão semântica.

### [P1] **Header hardcoded com dados fictícios em produção**
`components/AppShell.tsx:443`: `"R$ 187k / R$ 250k"` e `"(75%)"` são valores hardcoded (`// TODO Wave 3`). Mostra meta falsa em todas as telas para todos os usuários. **Dado fabricado em produção.**

### [P1] **Sidebar MetaWidget com dados hardcoded**
`components/Sidebar.tsx:582-586`: `meta={250000}` e `realizado={187000}` e `mes="Abril 2026"` fixos no código. O widget mostra sempre "75% — Abril 2026" independente do mês ou usuário. [CROSS-SQUAD]

### [P1] **Tokens de cor duplicados e hardcoded espalhados**
Há 3 formas de referenciar a mesma cor verde no mesmo projeto:
1. Classe Tailwind `bg-vitao-green` (token EN config)
2. Classe Tailwind `bg-vitao-verde` (token PT config)
3. `style={{ backgroundColor: '#00B050' }}` ou `style={{ color: '#00B050' }}` hardcoded inline

Causa mismatch visual (dois verdes diferentes aparecem lado a lado) e impossibilita troca global via token.

### [P2] **Spacing inconsistente no main container**
`components/AppShell.tsx:493`: `p-3 md:p-4 lg:p-6` — o padding do conteúdo principal salta de 12px para 16px para 24px. Mas muitas páginas usam `-m-3 lg:-m-6` para "romper" esse padding (ex: Inbox, linha 1176). Isso cria buracos de alinhamento: em alguns viewports o conteúdo flutua sem margem; em outros "sangra" para fora.

### [P2] **Dashboard abas de navegação: labels truncados em mobile**
`app/page.tsx:71-82`: TABS com labels como `'SAUDE DA BASE'`, `'REDES + SINALEIRO'`, `'MOTIVOS + RNC'` — em mobile é usado `labelMobile: 'SAD'`, `'RED'`, `'MOT'`. Essas abreviações de 3 letras são opacas para usuário novo. A própria aba "INDICADORES" → "IND" é ambígua (indicadores de quê?).

### [P2] **Ausência de design system para estados de loading/empty no Dashboard**
Dashboard usa spinner inline em alguns locais e `animate-pulse` skeleton em outros, sem padrão. As páginas Carteira, Pedidos e Produtos têm skeletons bem implementados; o Dashboard usa padrão diferente. Inconsistência visual marcada.

### [P3] **Dark mode declarado mas nunca aplicado (configuração confusa)**
`tailwind.config.ts:3`: `darkMode: 'class'` — comentário diz "never applied" mas a config existe. Se alguma lib externa injetar `.dark` no `<html>`, cores irão quebrar. Recomendação: mudar para `darkMode: false` para eliminar o risco.

---

## PROBLEMAS POR PÁGINA

### `/inbox` — `app/inbox/page.tsx`
**Estado:** funcional com fallback demo

**Issues:**
- [P0] `linha 166`: Avatar size `sm` usa `text-[10px]` — avatar de 32px com texto de 10px para iniciais
- [P0] `linha 299`: badge contador de conversas abertas: `text-[10px] font-bold` — badge numérico ilegível
- [P0] `linha 355-368`: abas de filtro (Todos / Aguard. / Em Atend. / Finaliz.) usam `text-[10px] font-semibold`. Elementos clicáveis de navegação primária com fonte de 10px. Touch target insuficiente: `py-1` = ~24px total.
- [P0] `linha 361`: badge counter aninhado na aba: `text-[8px] font-bold` — 8px é ilegível em qualquer contexto.
- [P1] `linha 462`: preview da última mensagem usa `text-[11px]` — texto de conteúdo a 11px.
- [P1] `linha 467`: badge de temperatura (Quente/Morno): `text-[9px] font-semibold` — 9px é sub-mínimo.
- [P1] `linha 509`: mini-avatar no chat (enviado por): `text-[9px] font-bold` — ilegível para iniciais.
- [P1] `linha 515`: remetente da bolha: `text-[9px] text-gray-400` — combinação 9px + gray-400 = ilegível.
- [P1] `linha 528-531`: timestamps das bolhas: `text-[9px] text-gray-400` — timestamps críticos ilegíveis.
- [P1] `linha 836`: consultor no painel lateral: `text-[10px] text-vitao-darkgreen` — verde escuro em 10px legível, mas consistência com resto da UI requer upgrade.
- [P1] `linha 901`: badge "Recompra proxima": `text-[9px] font-semibold` — 9px em badge informativo crítico.
- [P2] `linha 270-271`: abas "Aguard." e "Em Atend." — labels truncados artificialmente. "Aguardando" e "Em Atendimento" cabem se `text-[11px]` for usado com flex-shrink ajustado.
- [P2] `linha 165-169`: Avatar tamanho `sm` (w-8 h-8 = 32px) com `text-[10px]`. Avatar tamanho `lg` (w-12 h-12 = 48px) com `text-sm`. Proporção ok no lg, ruim no sm.
- [P2] `linha 841-848`: placeholder IA usa `bg-gray-100` com texto `text-gray-500` e `text-gray-400` — seção funcional com contraste deliberadamente atenuado pode parecer "quebrada" ao usuário.
- [P3] `linha 589`: `quickPills` usam strings sem acento ("Catalogo", "Prazo Entrega") — inconsistência com o resto da UI que usa acentuação.

### `/carteira` — `app/carteira/page.tsx`
**Estado:** funcional

**Issues:**
- [P0] Ausência do filtro por canal na UI (ver seção Filtro Food)
- [P1] `linha 404`: cards Curva ABC e Top 5 com `h2` usando `text-sm font-bold` — hierarquia de título inconsistente com o `h1` da página logo abaixo (`text-lg sm:text-xl`).
- [P1] `linha 440`: subtítulo do cabeçalho usa `text-xs text-gray-500` — texto de informação útil (contagem de clientes) com contraste abaixo do WCAG.
- [P1] `linha 529`: badge de aviso de filtro local usa `text-orange-600 font-medium` inline em parágrafo — funcional mas sem componente formal.
- [P2] `linha 402-411`: bloco "Curva ABC + Top 5" no topo da Carteira ocupa espaço visual considerável antes do filtro e da tabela. Usuário que vem buscar um cliente específico tem que rolar para chegar ao filtro. Hierarquia de ação invertida.
- [P2] `components/ClienteTable.tsx:262`: célula CLIENTE usa `font-medium text-gray-900 break-words` sem tamanho de fonte explícito — herda `text-sm` (14px) do body via globals.css, mas colunas menores usam `text-xs` explicitamente. Inconsistência de tamanho entre células.
- [P2] `components/ClienteTable.tsx:271-272`: razão social e CNPJ na sub-linha usam `text-[11px] text-gray-400` e `text-[10px] text-gray-400` — conteúdo informativo de identificação do cliente em 10px com baixo contraste.
- [P3] `components/ClienteTable.tsx:55-58`: ícones de temperatura são emoji (`🔥`, `⚠️`, `❄️`, `🚨`) dentro de um Badge formal. Emojis quebram consistência visual e podem renderizar diferente por OS.

### `/agenda` — `app/agenda/page.tsx`
**Estado:** funcional

**Issues:**
- [P1] `linha 76-93` (FollowUpBadge): badge "HOJE" usa `style={{ animation: 'pulse 1.5s ease-in-out infinite' }}` inline — `pulse` não existe como keyframe definido em globals.css (apenas `animate-pulse-dot` existe). Este badge não pulsa, e o código tem um bug silencioso.
- [P1] `linha 429-430` (tag PRIORITARIO): a tag usa `style={}` inline com cor calculada — `prio === 'P3'` usa cor `'#FFFF00'` (amarelo puro) com `color: '#1a1a1a'`. Amarelo puro (#FFFF00) sobre branco é problemático; o contraste texto-branco preto sobre amarelo é ok, mas o amarelo puro causa fadiga visual.
- [P1] `linha 439`: número do item (`#idx + 1`) usa `text-xs text-gray-500` — informação de sequência em cinza médio, pouco visível.
- [P2] `linha 462`: linha de sinaleiro usa `text-sm text-gray-600` + descrição `text-gray-500 italic text-xs` — mistura de tamanhos (sm + xs) na mesma linha de informação sem hierarquia semântica clara.
- [P2] `linha 469-477`: bloco "Acao Prescrita" usa `border-l-4 border-gray-300` (borda cinza clara) para destaque da ação mais importante do card. A borda de destaque não tem peso visual suficiente — deveria ser `border-vitao-green` ou `border-orange-400` para indicar urgência.
- [P2] `linha 510`: botão "📱 WhatsApp" usa emoji inline — inconsistente com o padrão de SVG icons do resto da app.
- [P2] `linha 512`: botão "✅ Registrar Atendimento" usa emoji — idem.
- [P3] Botão de geração de agenda ("Gerar Agenda") não tem estado disabled visual claro durante loading — spinner existe mas o botão mantém aparência interativa.

### `/pedidos` — `app/pedidos/page.tsx`
**Estado:** funcional

**Issues:**
- [P1] `linha 499-500`: label "Busca" usa `hidden sm:block` — em mobile não há nenhuma label visível antes do input. O input não tem placeholder suficientemente descritivo para compensar (tem "Cliente, CNPJ ou numero..." — ok, mas a inconsistência com desktop é confusa).
- [P1] `linha 547`: filtros "expandidos" usam `grid grid-cols-2 gap-2` em mobile — os selects de Status e Consultor ficam muito comprimidos em telas pequenas.
- [P1] `linha 95-100` (StatusBadge local): usa `text-[10px] font-semibold` — badge de status de pedido em 10px ilegível.
- [P2] `linha 28-34` (STATUS_CONFIG): as cores são hardcoded (`bg: '#6B7280'`, `bg: '#3B82F6'`, etc.) sem usar os tokens do design system (vitao-green, vitao-blue, etc.). Pedidos têm seu próprio sistema de cores desconectado do DS.
- [P2] `linha 91-100` (StatusBadge local): este componente duplica a funcionalidade de `StatusPill` do design system mas com lógica diferente. Dois sistemas de badge para status em paralelo.
- [P3] Não há paginação explícita na lista de pedidos — se backend retornar 1000 pedidos, todos renderizam no DOM.

### `/` — `app/page.tsx` (Dashboard CEO)
**Estado:** funcional

**Issues:**
- [P1] `linha 386`: label "Insight do Dia" usa `text-[10px] font-bold text-white/70` — sobre gradiente azul/roxo. `white/70` = rgba(255,255,255,0.70) = contraste ~3:1 — abaixo do WCAG AA em texto de 10px.
- [P1] `linha 397-424`: mini badges do IA widget usam `text-[11px] font-semibold text-white` sobre `bg-white/15` — contraste insuficiente (branco sobre branco translúcido = ~1.5:1).
- [P1] Aba de navegação com 10 tabs (`RESUMO` até `PROJECAO`) em linha horizontal — em telas médias (768-1024px) as abas transbordam ou ficam com scroll horizontal sem indicador visual de overflow. Labels maiúsculos como `'SAUDE DA BASE'`, `'REDES + SINALEIRO'` têm tracking inadequado para buttons.
- [P1] `linha 882`: labels de gráfico de sinaleiro usam `text-[10px]` — labels de gráfico Recharts a 10px são ilegíveis.
- [P1] `linha 1017-1019`: cabeçalhos de tabela `<th>` usam `text-[10px] font-semibold text-gray-500` — headers de tabela a 10px + gray-500 = baixo contraste.
- [P2] `linha 363-366`: h1 "Dashboard VITAO360" usa `text-xl sm:text-2xl` — adequado, mas o subtítulo usa `text-sm text-gray-500` sem label semântico (deveria ser `<p>` com `aria-describedby` ou `subtitle` role).
- [P2] `linha 1360` e `linha 1365-1377`: grelha de dados de performance por consultor usa `text-[10px] text-gray-400` para labels — dados de performance críticos com contraste insuficiente.
- [P3] `linha 97-103`: constantes de cor `VERDE`, `AMARELO`, etc. são redefinidas localmente no arquivo em vez de importar do design system. Inconsistência: `VERMELHO = '#FF0000'` aqui vs `vitao.vermelho = '#FF0000'` no config (coincidentemente iguais, mas frágil).

### `/produtos` — `app/produtos/page.tsx`
**Estado:** funcional

**Issues:**
- [P1] `linha 45-56` (BadgeAtivo): usa `style={}` inline com `backgroundColor: '#00B050'` e `backgroundColor: '#FF0000'` — bypassa o design system tokens.
- [P1] `linha 66-73` (SkeletonRow): skeleton usa `bg-gray-100 animate-pulse` sem variar a largura de forma realista. Todos os skeletons são retângulos planos sem hierarquia visual.
- [P2] As colunas da tabela de produtos têm `px-4 py-3` enquanto a tabela de carteira usa `px-3 py-2.5` — espaçamento inconsistente entre tabelas do sistema.
- [P3] Não há estado vazio ilustrado para "nenhum produto encontrado com estes filtros".

### `/gestao/dde` — `app/gestao/dde/page.tsx`
**Estado:** placeholder demo-quality (mockup declarado no código)

**Issues:**
- [P1] Página inteira é mockup com dados sintéticos não sinalizados ao usuário final com destaque suficiente. O aviso "valores são ilustrativos" está apenas no comentário de código, não na UI. Usuário leigo pode confundir com dados reais.
- [P2] A cascata DRE usa `text-[10px]`, `text-[11px]`, `text-xs` sem hierarquia tipográfica clara entre código de linha, descrição e valor.
- [P3] Badge "EM CONST." na Sidebar (linha 555 do Sidebar.tsx) usa `animate-pulse` piscando — distrai na navegação.

### `/gestao/analise-critica` — `app/gestao/analise-critica/page.tsx`
**Estado:** bloqueado/placeholder (não auditado em detalhe — marcado como BLOQUEADO na sidebar)

### `/manual` — `app/manual/page.tsx`
**Estado:** funcional

**Issues:**
- [P2] Conteúdo é texto estático sem tamanho de fonte explícito nos parágrafos — herda 14px do body, adequado, mas seções internas não têm hierarquia tipográfica consistente.
- [P3] Página sem breadcrumb funcional — o AppShell injeta breadcrumb automaticamente, mas a página "Manual" não tem sub-seções de navegação interna.

### `/pipeline` — `app/pipeline/page.tsx`
**Estado:** funcional (Kanban)

**Issues:**
- [P1] Kanban horizontal com 14 colunas não tem scroll indicator em mobile — em tela de 375px, o usuário não tem pista visual de que há mais colunas à direita.
- [P2] Swimlane labels (`PRE-VENDA`, `VENDA`, etc.) usam text-xs uppercase sem espaçamento visual suficiente entre swimlanes — as fronteiras de grupo ficam implícitas.
- [P3] Cards do Kanban têm `cursor-grab` apenas quando drag está ativo, sem cursor indicando draggable no hover.

---

## PROBLEMAS POR COMPONENTE

### `Sidebar.tsx`

- [P1] `linha 502`: group label usa `text-[10px] font-semibold text-gray-400 uppercase tracking-wider` — 10px + gray-400 = falha de contraste WCAG para texto de navegação.
- [P1] `linha 619`: footer usa `text-[10px] text-gray-300` — 10px + gray-300 = combinação de contraste mais baixa do sistema inteiro (1.61:1).
- [P1] `linha 620`: versão `text-[10px] text-gray-300` — idem. Informação quase invisível.
- [P2] `linha 484`: brand header usa `gradient-vitao` (verde escuro) com `text-white/70` para o subtítulo "Inteligencia Comercial" — `white/70` sobre verde escuro pode ter contraste insuficiente dependendo do monitor.
- [P2] Badge "EM CONST." (linha 555) usa `animate-pulse` permanentemente — elemento de UI em pulsação constante é distrator visual crônico.
- [P3] Sidebar expandida tem largura `w-56` (224px) que compete com o conteúdo em telas de 768-900px.

### `ClienteDetalhe.tsx`

- [P1] `linha 96`: cabeçalho de bloco colapsável usa `text-[11px] font-semibold text-gray-600 uppercase tracking-wider` — label de seção em 11px com gray-600 (contraste ~4.6:1 — passa WCAG mas é borderline).
- [P2] O componente usa `LineChart` (Recharts) sem `aria-label` no `ResponsiveContainer` — inacessível para screen readers.
- [P3] Blocos colapsáveis usam `bg-gray-50 hover:bg-gray-100` — diferença visual mínima entre estado normal e hover.

### `ClienteTable.tsx`

- [P1] `linha 270-272`: sub-linha da célula CLIENTE (razão social + CNPJ) usa `text-[11px] text-gray-400` e `text-[10px] text-gray-400` — dados de identificação em fonte sub-mínima com baixo contraste.
- [P2] `linha 33-42`: coluna `mobileHidden` para "Temperatura", "Curva", "Faturamento" e "Sinaleiro" — em mobile a tabela mostra apenas Cliente, Consultor, Situação e Score. Falta contexto para tomada de decisão em campo.
- [P3] Sem `caption` ou `aria-label` no elemento `<table>` — inacessível para screen readers.

### `components/ui/Badge.tsx`

- [P0] `linha 31`: tamanho `xs` definido como `text-[10px] px-1.5 py-0 leading-4` — este é o tamanho padrão usado em tags de status, contadores de nav, temperatura no Inbox. Todos os badges `xs` são ilegíveis. **Correção sistêmica:** `text-[10px]` → `text-xs` (12px).
- [P1] `linha 22-29` (VARIANT_CLASSES): `neutral: 'bg-gray-100 text-gray-700'` — `text-gray-700` sobre `bg-gray-100` = contraste ~4.7:1 — passa barely. `danger: 'bg-red-100 text-red-800'` = ~5.9:1 OK. `warning: 'bg-orange-100 text-orange-800'` = ~5.3:1 OK.
- [P2] `INAT.ANT` mapeia para `variant: 'neutral'` (cinza) em StatusPill — mas R9 diz `INAT.ANT=#FF0000`. O badge fica cinza no lugar de vermelho, violando a paleta de status oficial do projeto.

### `components/ui/StatusPill.tsx`

- [P1] `linha 42-43`: `INAT.ANT` → `{ variant: 'neutral', label: 'Inat. Antigo' }` usa cinza. A regra R9 especifica `INAT.ANT = #FF0000` (vermelho). O badge deveria ser `variant: 'danger'` para obedecer a paleta oficial. **Violação da regra R9.**

### `components/AppShell.tsx`

- [P1] `linha 443`: `"R$ 187k / R$ 250k"` hardcoded na barra de header — dado falso exposto em produção. [CROSS-SQUAD]
- [P2] `linha 389-390`: breadcrumb da página atual usa `text-sm font-semibold text-gray-900` e o item anterior usa `text-xs text-gray-400 hover:text-gray-700` — a diferença de tamanho (text-sm vs text-xs) é excessiva e cria desequilíbrio visual no breadcrumb.
- [P2] `linha 363`: header usa `py-2.5` resultando em ~48px de altura total — adequado para touch, mas o padding assimétrico `px-3 md:px-4` cria espaçamento diferente de desktop vs mobile.

### `components/ui/MetaWidget.tsx`

- [P2] `linha 59`: porcentagem usa `text-xs font-bold` — adequado. Mas `linha 61`: valor realizado usa `text-sm font-bold` e `linha 62`: meta usa `text-[10px] opacity-75` — hierarquia tipográfica errada: o "de R$250K" (meta = contexto) é menor e mais apagado que o valor realizado, mas ambos são igualmente importantes para entendimento. A meta deveria ter ao menos `text-xs`.

---

## RECOMENDAÇÕES PARA SQUAD DELTA (Design Tokens)

### Token de tipografia mínimo necessário

```
Scale:
  text-label:   12px / text-xs     (mínimo para labels, badges, timestamps)
  text-body-sm: 13px / text-[13px] (body compacto, tabelas densas)
  text-body:    14px / text-sm     (body padrão — já definido em globals.css)
  text-subtitle: 15px / text-[15px] (sub-cabeçalhos, nomes de seção)
  text-heading-sm: 17px / text-[17px] ou text-lg
  text-heading:  20px / text-xl
  text-display:  24px / text-2xl

PROIBIR:
  text-[8px]  — nunca usar
  text-[9px]  — nunca usar
  text-[10px] — somente para informação verdadeiramente decorativa (ex: indicador de versão em footer)
  text-[11px] — usar text-xs (12px) no lugar
```

### Token de cor de texto — hierarquia de contraste

```
text-primary:    gray-900 (#111827) — títulos, valores principais
text-secondary:  gray-700 (#374151) — texto de corpo, labels
text-tertiary:   gray-600 (#4B5563) — texto auxiliar (MÍNIMO aceitável para contraste)
text-muted:      gray-500 (#6B7280) — apenas para informação de baixa prioridade (datas, prefixos)
text-disabled:   gray-400 (#9CA3AF) — SOMENTE para elementos disabled/inativos, NUNCA para conteúdo semântico
text-ghost:      gray-300 (#D1D5DB) — ELIMINAR de conteúdo semântico completamente

REGRA: Nunca usar text-gray-400 ou text-gray-300 para texto informativo. Use somente para placeholders de input e elementos desabilitados.
```

### Token de cor de status — corrigir violação R9

```
ATIVO:     bg-green-100   text-green-800   (current: OK)
INAT.REC:  bg-orange-100  text-orange-800  (current: OK via 'warning')
INAT.ANT:  bg-red-100     text-red-800     (CORRIGIR: 'neutral' → 'danger')
PROSPECT:  bg-blue-100    text-blue-800    (current: OK via 'info')
EM RISCO:  bg-red-100     text-red-800     (current: OK via 'danger')
```

### Token de spacing

```
Escala rem-based existente via Tailwind (2, 3, 4, 6, 8, 12, 16, 24) já é adequada.
Problema: uso de arbitrary values [16px], [20px], [32px] em alguns componentes.
Eliminar todos os px-[n] e py-[n] — usar a escala padrão Tailwind.
```

### Unificar tokens de cor verde

```
Problema atual: dois tokens de verde convivem:
  vitao.verde  = '#00B050' (PT)
  vitao.green  = '#00A859' (EN)

Decisão necessária (L3): escolher UM. Recomendação: manter '#00B050' como canônico
(alinhado com R9 — "ATIVO=#00B050") e deprecar '#00A859'.
```

---

## RECOMENDAÇÕES PARA WAVE 2 (Aplicação — prioridade P0 → P3)

### P0 — Bloqueantes imediatos

1. **`components/ui/Badge.tsx:31` — `text-[10px]` → `text-xs` (12px)**
   Antes: `xs: 'text-[10px] px-1.5 py-0 leading-4'`
   Depois: `xs: 'text-xs px-1.5 py-0.5 leading-4'`
   Impacto: corrige ~150 badges em todo o sistema de uma vez.

2. **`components/ui/StatusPill.tsx:42-43` — INAT.ANT → `danger`**
   Antes: `'INAT.ANT': { variant: 'neutral', label: 'Inat. Antigo' }`
   Depois: `'INAT.ANT': { variant: 'danger',  label: 'Inat. Antigo' }`
   Impacto: alinha com regra R9 (#FF0000 para INAT.ANT). Tabela de Carteira + todos os badges de status ficam corretos.

3. **`app/inbox/page.tsx:355-365` — touch target das abas de filtro**
   Antes: `py-1 text-[10px]` nas filter tabs
   Depois: `py-2 text-xs` (mínimo 36px de altura, texto 12px)
   Impacto: tabs clicáveis em mobile sem precisar de precisão de pixel.

4. **`components/Sidebar.tsx:619-620` — footer ilegível**
   Antes: `text-[10px] text-gray-300` / `text-[10px] text-gray-300`
   Depois: `text-xs text-gray-400` (ou remover completamente o footer)
   Impacto: elimina a pior combinação de contraste do sistema.

5. **`components/AppShell.tsx:439-443` — remover meta hardcoded do header**
   Antes: `<span className="font-semibold text-vitao-green">R$ 187k / R$ 250k</span>`
   Depois: ocultar completamente até Wave 3 conectar com `/api/metas/atual`
   Impacto: remove dado falso exposto em produção para todos os usuários.

6. **`components/Sidebar.tsx:582-586` — MetaWidget com dados hardcoded**
   Antes: `<MetaWidget meta={250000} realizado={187000} mes="Abril 2026" />`
   Depois: ocultar widget (ou substituir por skeleton) até dados reais estarem disponíveis
   Impacto: remove dado falso persistente no footer da sidebar.

### P1 — Alta prioridade

7. **Global — substituir `text-gray-300` semântico por `text-gray-500` mínimo**
   Grep: `text-gray-300` usado como cor de texto (não como `bg-gray-300` ou `border-gray-300`)
   Ação: substituir por `text-gray-500` (mínimo aceitável para contraste 4.5:1)
   Arquivos: `app/page.tsx:1011, 1298`, `components/Sidebar.tsx:619-620`

8. **Global — `text-[9px]` e `text-[8px]` → `text-xs` (12px)**
   Grep: `text-\[9px\]`, `text-\[8px\]`
   Ação: substituir todos por `text-xs`
   Arquivos principais: `app/inbox/page.tsx` (6 ocorrências), `components/Sidebar.tsx` (InboxBadge, AgendaBadge)

9. **`app/agenda/page.tsx:76` — FollowUpBadge animation bug**
   Antes: `style={{ animation: 'pulse 1.5s ease-in-out infinite' }}`
   Depois: `className="animate-pulse"` (usa keyframe Tailwind existente)
   Impacto: badge "HOJE" passa a pulsar como intencionado.

10. **`app/page.tsx:397-424` — badges sobre `bg-white/15` — contraste insuficiente**
    Antes: `bg-white/15 text-[11px] font-semibold text-white`
    Depois: `bg-white/25 text-xs font-semibold text-white`
    Impacto: contraste dos mini badges do widget IA sobe de ~1.5:1 para ~2.5:1 (ainda baixo para AA mas muito melhor).

11. **`app/carteira/page.tsx` — reorganizar hierarquia: filtro ANTES dos gráficos**
    Mover o bloco "Curva ABC + Top 5" (linhas 401-411) para abaixo do FilterGroup.
    Impacto: usuário que quer filtrar clientes acessa o filtro imediatamente sem rolar.

12. **`app/pedidos/page.tsx:95-100` — StatusBadge local com `text-[10px]`**
    Antes: `text-[10px] font-semibold rounded uppercase`
    Depois: usar `StatusPill` do design system ou `text-xs`
    Impacto: unifica os badges de status de pedido com o DS.

### P2 — Média prioridade

13. **`app/inbox/page.tsx:270` — labels de tab — "Aguard." → "Aguardando"**
    Aumentar para `text-xs` e usar labels completas — elas cabem em `flex-1` com fonte 12px.

14. **`app/agenda/page.tsx:468` — borda de "Acao Prescrita"**
    Antes: `border-l-4 border-gray-300`
    Depois: `border-l-4 border-vitao-green` (ação prescrita deve ter destaque Vitao)

15. **`app/agenda/page.tsx:510, 512` — substituir emojis por SVG icons**
    Antes: `<span>📱</span> WhatsApp` / `<span>✅</span> Registrar`
    Depois: usar SVG inline consistente com o padrão do resto da app

16. **`app/pedidos/page.tsx:28-34` — unificar STATUS_CONFIG de pedidos com design system**
    Mapear `DIGITADO` → `neutral`, `LIBERADO` → `info`, `FATURADO` → `success`, `ENTREGUE` → `brand`, `CANCELADO` → `danger` usando `Badge` variant do DS.

17. **`tailwind.config.ts` — resolver conflito de dois tokens verde**
    Decisão: manter `vitao.verde = '#00B050'` como canônico; `vitao.green = '#00A859'` → deprecar ou alinhar ao mesmo valor.

18. **`components/ClienteTable.tsx:271-272` — melhorar contraste das sub-linhas**
    Antes: `text-[11px] text-gray-400` e `text-[10px] text-gray-400`
    Depois: `text-xs text-gray-500` (mínimo aceitável)

19. **`components/Sidebar.tsx:502` — group label contraste**
    Antes: `text-[10px] font-semibold text-gray-400`
    Depois: `text-[11px] font-semibold text-gray-500`

---

## COMPLIANCE COM REGRAS CRM

### R9 — Visual LIGHT exclusivamente
Status: **PASS**. Nenhuma classe `.dark` ou modo escuro foi inadvertidamente ativado. `tailwind.config.ts` define `darkMode: 'class'` mas nunca injeta `.dark` no DOM. Recomendação: mudar para `darkMode: false` para eliminar o risco.

### Cores oficiais — verificação
| Código | R9 especifica | Implementação atual | Status |
|--------|--------------|---------------------|--------|
| ATIVO | `#00B050` | `bg-green-100 text-green-800` via Badge `success` | **DIVERGE** — R9 diz #00B050 sólido, mas UI usa verde claro semântico. Aceitável como escolha de legibilidade. |
| INAT.REC | `#FFC000` | `bg-orange-100 text-orange-800` via Badge `warning` | **DIVERGE** — laranja vs amarelo. Semanticamente coerente mas difere da paleta Excel. |
| INAT.ANT | `#FF0000` | `bg-gray-100 text-gray-700` via Badge `neutral` | **VIOLAÇÃO R9** — cinza no lugar de vermelho. |
| A | `#00B050` | `CurvaPill` usa verde | **PASS** |
| B | `#FFFF00` | `CurvaPill` usa amarelo | **PASS** |
| C | `#FFC000` | `CurvaPill` usa laranja-amarelo | **PASS** |

### Fonte Web
R9 especifica "Arial 9pt dados, 10pt headers" para Excel. No web, `globals.css:30-34` define corretamente `font-family: Inter` e `font-size: 14px`. O problema é que muitos componentes usam `text-[10px]` e `text-[9px]` replicando os tamanhos do Excel — o que faz sentido no Excel com DPI de impressão, mas é ilegível em tela.

---

## PROBLEMA REPORTADO ESPECÍFICO — Filtro "Food" sem clientes

### Diagnóstico completo

**Sintoma:** Leandro seleciona filtro "Food" na Carteira e não aparecem clientes.

**Investigação no código:**

**1. Estrutura do canal no banco:**
`backend/alembic/versions/f557927e169e_multi_channel_architecture_canais_.py:41`:
```python
("FOOD_SERVICE", "ATIVO", "Food service (industria, distribuidor, varejo)")
```
O canal existe no banco com nome `"FOOD_SERVICE"` e status `ATIVO`. Clientes têm `canal_id` FK para essa tabela.

**2. API do backend:**
`backend/app/api/routes_clientes.py:293-352`: O endpoint aceita `canal_id: Optional[int]` como query parameter. O filtro funciona por ID numérico, não por nome.

**3. UI da Carteira:**
`frontend/src/app/carteira/page.tsx`: Os `FILTER_FIELDS` (linhas 43-113) definem filtros de:
- busca, consultor, situacoes, abcs, temperaturas, sinaleiro, prioridade, uf

**Não existe campo de filtro por canal.** A página de Carteira nunca envia `canal_id` para o backend.

**4. CanalSelector no Header:**
`components/CanalSelector.tsx`: O CanalSelector existe no header global e persiste via `CanalContext`. Ele armazena o `canalId` selecionado no localStorage. **Mas a página de Carteira não consome o `canalId` do CanalContext na sua chamada `fetchClientes`.**

`frontend/src/app/carteira/page.tsx:266-282` (função `load`):
```typescript
fetchClientes({
  busca: ...,
  consultor: ...,
  sinaleiro: ...,
  prioridade: ...,
  uf: ...,
  sort_by: ...,
  sort_dir: ...,
  limit: PAGE_SIZE,
  offset,
})
```
**`canal_id` está ausente da chamada.** O `CanalContext` é importado em `CanalSelector` mas não em `carteira/page.tsx`.

**5. Raiz do bug:**
A desconexão tem dois aspectos:
- **Aspecto A (UX):** O CanalSelector no header filtra o canal globalmente para o usuário, mas a Carteira ignora o canal selecionado quando faz fetch. O usuário seleciona "FOOD_SERVICE" no CanalSelector e vê clientes do canal que o scoping do backend já filtrou (`stmt = stmt.where(Cliente.canal_id.in_(user_canal_ids))`) — mas não com filtro explícito do canal selecionado.
- **Aspecto B (Funcional):** Se o usuário quer filtrar a Carteira especificamente por "Food" usando o filtro LOCAL da página, não existe essa opção nos filtros da Carteira.

**O que acontece hoje quando Leandro seleciona "Food" no header:**
O CanalSelector grava `canalId = <id do FOOD_SERVICE>` no CanalContext/localStorage, mas `carteira/page.tsx` nunca lê esse contexto. A Carteira sempre mostra todos os clientes do usuário independente do canal selecionado no header.

**Fix necessário (SQUAD CHARLIE):**
```typescript
// carteira/page.tsx — importar useCanal e passar canal_id para fetchClientes
import { useCanal } from '@/contexts/CanalContext';
const { canalId } = useCanal();

// Na função load():
fetchClientes({
  // ... demais filtros ...
  canal_id: canalId ?? undefined,  // <-- adicionar esta linha
});
```
E re-executar load quando `canalId` mudar no useEffect.

---

## FILES AUDITED

```
frontend/src/app/globals.css
frontend/src/app/layout.tsx
frontend/src/app/page.tsx (Dashboard)
frontend/src/app/inbox/page.tsx
frontend/src/app/carteira/page.tsx
frontend/src/app/agenda/page.tsx
frontend/src/app/pedidos/page.tsx
frontend/src/app/produtos/page.tsx
frontend/src/app/pipeline/page.tsx
frontend/src/app/gestao/dde/page.tsx
frontend/src/app/manual/page.tsx
frontend/src/components/Sidebar.tsx
frontend/src/components/AppShell.tsx
frontend/src/components/CanalSelector.tsx
frontend/src/components/ClienteDetalhe.tsx
frontend/src/components/ClienteTable.tsx
frontend/src/components/ui/Badge.tsx
frontend/src/components/ui/StatusPill.tsx
frontend/src/components/ui/FilterGroup.tsx
frontend/src/components/ui/MetaWidget.tsx
frontend/src/components/ui/ScoreBar.tsx
frontend/tailwind.config.ts
backend/app/api/routes_clientes.py
backend/app/api/routes_canais.py
backend/alembic/versions/f557927e169e_multi_channel_architecture_canais_.py
```

---

*Auditoria concluída em modo código-only (sem dev server). Nenhum arquivo de código foi modificado.*
