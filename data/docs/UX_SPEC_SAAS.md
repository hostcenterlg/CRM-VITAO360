# UX SPEC SAAS — CRM VITAO360
# Especificacao Completa de Interface, Design System e Fluxos
# Versao: 2.0 — 2026-03-25 | Autor: @ux
# Status: DEFINITIVO — fonte de verdade para frontend

---

## PRINCIPIOS FUNDAMENTAIS

### A Lei do CRM Autonomo

> O CRM manda. O consultor executa. Complexidade ZERO na interface. Inteligencia TOTAL no backend.

Cada decisao de design passa por um teste:
**"Isso ajuda o consultor a EXECUTAR mais rapido?"**
Se nao — a tela esta errada.

### Anti-Patterns Proibidos

| Anti-Pattern | Por que e errado | Alternativa |
|-------------|-----------------|-------------|
| Formulario com 10+ campos | Consultor faz 40-60 atendimentos/dia | Dropdown + textarea, nada mais |
| Score com explicacao detalhada | Consultor nao precisa saber POR QUE | So mostrar o numero e a posicao |
| Dashboard de graficos sem acao | Informacao sem prescricao = paralisia | Sempre info + acao prescrita |
| Consultor escolhendo ordem | Perde 80% da inteligencia | Motor ordena, consultor executa |
| Dark mode | Regra R9 — sempre LIGHT | Background branco, texto escuro |

---

## DESIGN SYSTEM

### DS-01. Paleta de Cores

```css
/* === CORES DE STATUS (imutaveis — R9) === */
--color-ativo:     #00B050;   /* ATIVO, VERDE sinaleiro, ABC-A */
--color-inativo:   #FFC000;   /* INAT.REC, AMARELO sinaleiro, ABC-C */
--color-critico:   #FF0000;   /* INAT.ANT, VERMELHO sinaleiro */
--color-roxo:      #7030A0;   /* Sinaleiro ROXO (sem historico) */
--color-abc-b:     #FFFF00;   /* ABC-B */
--color-prospect:  #808080;   /* PROSPECT */

/* === CORES DE PRIORIDADE === */
--color-p0:        #FF0000;   /* P0 IMEDIATA */
--color-p1:        #FF6600;   /* P1 NAMORO NOVO / URGENTE */
--color-p2:        #FFC000;   /* P2 NEGOCIACAO ATIVA */
--color-p3:        #FFFF00;   /* P3 MOMENTO OURO */
--color-p4:        #9CA3AF;   /* P4 MEDIA */
--color-p5:        #D1D5DB;   /* P5 MEDIA-BAIXA */
--color-p6:        #E5E7EB;   /* P6 BAIXA */
--color-p7:        #F3F4F6;   /* P7 NUTRICAO */

/* === CORES BASE === */
--color-brand:     #00B050;   /* Cor primaria VITAO */
--color-brand-dk:  #007A38;   /* Hover / estados ativos */
--color-bg:        #FFFFFF;   /* Fundo principal */
--color-surface:   #F9FAFB;   /* Fundo secundario (tabelas, cards) */
--color-border:    #E5E7EB;   /* Bordas gerais */
--color-border-dk: #D1D5DB;   /* Bordas de inputs */

/* === TEXTO === */
--color-text-primary:   #111827;   /* Titulos, valores principais */
--color-text-secondary: #374151;   /* Corpo, labels */
--color-text-muted:     #6B7280;   /* Subtitulos, placeholder */
--color-text-faint:     #9CA3AF;   /* Metadados, timestamps */

/* === FEEDBACK === */
--color-success:   #00B050;
--color-warning:   #FFC000;
--color-error:     #DC2626;
--color-info:      #2563EB;

/* === TIPO DE CONTATO === */
--color-ligacao:   #2563EB;   /* Ligacao telefonica */
--color-whatsapp:  #00A651;   /* WhatsApp */
--color-visita:    #7C3AED;   /* Visita presencial */
--color-email:     #F59E0B;   /* Email */
```

### DS-02. Tipografia

```
Fonte principal: Arial (obrigatoria — R9)
Fallbacks: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif

Escala tipografica:
  --text-xs:    9px   / line-height 1.4  — dados de tabela, metadados
  --text-sm:   10px   / line-height 1.5  — headers de coluna, labels
  --text-base: 12px   / line-height 1.5  — corpo geral, sidebar
  --text-md:   14px   / line-height 1.6  — titulos de secao
  --text-lg:   18px   / line-height 1.4  — titulos de pagina
  --text-xl:   24px   / line-height 1.2  — valores KPI principais
  --text-2xl:  32px   / line-height 1.1  — valores de destaque (CEO)

Pesos:
  normal: 400   — corpo, descricoes
  medium: 500   — labels, metadados importantes
  semibold: 600 — cabecalhos, badges
  bold: 700     — titulos, valores KPI

Casos de uso:
  Dados em tabela:    Arial 9px / 400  / #374151
  Cabecalho tabela:   Arial 10px / 600 / #6B7280 / UPPERCASE / letter-spacing 0.05em
  Titulo pagina:      Arial 18px / 700 / #111827
  Titulo secao:       Arial 14px / 600 / #111827
  KPI valor:          Arial 24px / 700 / #111827
  KPI label:          Arial 10px / 500 / #6B7280
  Sidebar item:       Arial 12px / 500 / #374151
  Badge:              Arial 10px / 700 / uppercase
  Acao prescrita:     Arial 12px / 600 / #111827 (campo mais importante da agenda)
  Placeholder:        Arial 12px / 400 / #9CA3AF italic
  Timestamp:          Arial 9px  / 400 / #9CA3AF
  CNPJ:               Arial 9px  / 400 / #6B7280 / font-family: monospace
```

### DS-03. Espacamento e Grid

```
Grid: 12 colunas, gutter 16px, margem lateral 24px (desktop)
Container max-width: 1440px (centrado acima de 1440px)

Spacing scale (multiplos de 4px):
  --space-1:  4px
  --space-2:  8px
  --space-3: 12px
  --space-4: 16px
  --space-5: 20px
  --space-6: 24px
  --space-8: 32px

Padding padrao:
  Card/Panel:     16px
  Table cell:     12px 16px
  Input:          8px 12px
  Button:         8px 16px (pequeno), 10px 20px (normal)
  Modal:          24px
  Section gap:    24px
  Page padding:   16px (mobile), 24px (tablet), 32px (desktop)

Alturas de linha de tabela:
  Padrao:  36px (desktop)
  Compacto: 28px (telas densas)
  Touch:   44px (mobile/tablet)
```

### DS-04. Componentes Reutilizaveis

#### DS-04-A. StatusBadge

Badge colorido para SITUACAO, SINALEIRO, PRIORIDADE, ABC, TEMPERATURA.

```
Anatomia:
  [████████ TEXTO ████████]
   bg: cor da variante
   text: branco ou #1A1A1A (para fundos claros)
   font: Arial 10px bold uppercase
   padding: 2px 8px
   border-radius: 3px

Tamanhos:
  .badge-sm:  padding 1px 6px, font 9px   — colunas compactas
  .badge:     padding 2px 8px, font 10px  — padrao
  .badge-lg:  padding 4px 10px, font 11px — destaque

Mapa completo de cores:
  situacao/ATIVO:    bg #00B050 text #FFF
  situacao/EM RISCO: bg #FF6600 text #FFF
  situacao/INAT.REC: bg #FFC000 text #1A1A1A
  situacao/INAT.ANT: bg #FF0000 text #FFF
  situacao/PROSPECT: bg #808080 text #FFF
  situacao/LEAD:     bg #6366F1 text #FFF
  situacao/NOVO:     bg #0EA5E9 text #FFF
  sinaleiro/VERDE:   bg #00B050 text #FFF
  sinaleiro/AMARELO: bg #FFC000 text #1A1A1A
  sinaleiro/VERMELHO:bg #FF0000 text #FFF
  sinaleiro/ROXO:    bg #7030A0 text #FFF
  prioridade/P0:     bg #FF0000 text #FFF
  prioridade/P1:     bg #FF6600 text #FFF
  prioridade/P2:     bg #FFC000 text #1A1A1A
  prioridade/P3:     bg #FFFF00 text #1A1A1A
  prioridade/P4:     bg #9CA3AF text #FFF
  prioridade/P5:     bg #D1D5DB text #374151
  prioridade/P6:     bg #E5E7EB text #6B7280
  prioridade/P7:     bg #F3F4F6 text #9CA3AF
  abc/A:             bg #00B050 text #FFF
  abc/B:             bg #FFFF00 text #1A1A1A
  abc/C:             bg #FFC000 text #1A1A1A
  temperatura/QUENTE:  bg #EF4444 text #FFF
  temperatura/MORNO:   bg #F97316 text #FFF
  temperatura/FRIO:    bg #60A5FA text #FFF
  temperatura/CRITICO: bg #7030A0 text #FFF
  temperatura/PERDIDO: bg #6B7280 text #FFF
```

#### DS-04-B. SinaleiroDot

Indicador circular para uso em colunas compactas.

```
.sinaleiro-dot {
  width: 10px; height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.sinaleiro-dot.verde    { background: #00B050; }
.sinaleiro-dot.amarelo  { background: #FFC000; }
.sinaleiro-dot.vermelho { background: #FF0000; }
.sinaleiro-dot.roxo     { background: #7030A0; }

Variante com label:
  [●] VERDE — dot 10px + texto ao lado, sem fundo colorido
```

#### DS-04-C. KpiCard

Card de metrica com destaque numerico.

```
┌─────────────────────────────────┐
│ ████ (accent bar 4px no topo)   │
│                                 │
│ LABEL METRICA              ICON │
│ 2.456                           │
│ subtitulo / variacao            │
└─────────────────────────────────┘

Props:
  label:      string (uppercase, 10px semibold #6B7280)
  value:      string | number (24px bold #111827)
  subtitle:   string (9px #9CA3AF)
  accentColor: hex string
  icon:       SVG 20x20px (cor #9CA3AF)
  trend:      { value: number, direction: 'up'|'down' } — opcional

Accent colors por uso:
  Total Clientes:    #2563EB
  Ativos:            #00B050
  Faturamento:       #7C3AED
  Follow-ups:        #F59E0B
  Criticos:          #DC2626
  Score medio:       #0EA5E9
  Meta atingida:     #00B050
  Gap meta:          #FF0000

Dimensoes:
  min-width: 180px
  height: 90px (compacto) / 110px (padrao)
  border-radius: 8px
  border: 1px solid #E5E7EB
  box-shadow: 0 1px 3px rgba(0,0,0,0.08)
  padding: 16px

Estado loading:
  accent bar: skeleton animado
  label: skeleton 80px x 10px
  value: skeleton 120px x 24px
  animacao: pulse 1.5s ease-in-out infinite
```

#### DS-04-D. ScoreBar (Barra de Score)

```
Uso: exibir score 0-100 com cor contextual.

Visual:
  [██████████████░░░░░░] 87

Largura da barra: 80px fixo (em tabela), 120px (detalhe cliente)
Altura: 6px
Border-radius: 3px
Background vazio: #E5E7EB
Valor texto: Arial 9px bold #374151, alinhado a direita

Cor da barra por range:
  >= 70: #00B050 (verde)
  >= 40: #FFC000 (amarelo)
  <  40: #FF0000 (vermelho)

Animacao: width transicao 400ms ease-out ao montar
```

#### DS-04-E. AgendaCard (Card de Agenda)

```
┌──────────────────────────────────────────────────────────┐
│ [P1] ██████  │ #3 — DISTRIBUIDORA LIGEIRO        [VERM] │
│              │ RJ — 45 dias sem compra                   │
│              │ ┌────────────────────────────────────────┐│
│              │ │ ACAO: Confirmar orcamento, fechar venda││
│              │ └────────────────────────────────────────┘│
│              │ TENTATIVA T2 — Sinaleiro Vermelho          │
│              │ Follow-up: HOJE (vencido ha 2 dias)        │
│              │                  [Registrar Atendimento]   │
└──────────────────────────────────────────────────────────┘

Anatomia:
  Borda esquerda: 4px solid {cor da prioridade}
  Background: #FFFFFF (padrao) / #FFFBEB (P1 urgente)
  Border: 1px solid #E5E7EB
  Border-radius: 6px
  Padding: 12px 16px
  Gap entre cards: 8px

Hover:
  box-shadow: 0 4px 12px rgba(0,0,0,0.10)
  transform: translateY(-1px)
  transition: 150ms ease

Layout interno (grid 2 colunas):
  Coluna esquerda (72px): badge prioridade + score bar vertical
  Coluna direita (flex-1): nome + dados + ACAO PRESCRITA + botao

Acao prescrita (bloco de destaque):
  background: #F0FDF4 (quando positivo) / #FEF2F2 (quando urgente)
  border-left: 3px solid {cor do sinaleiro}
  font: Arial 12px 600 #111827
  padding: 6px 10px
  border-radius: 0 4px 4px 0

Borda P1/P3 especial (pula fila):
  border: 2px solid #FF6600
  Marcador de canto superior direito: "PRIORITARIO" tag pequena

Estados:
  pending:     borda prioridade normal
  concluido:   opacity 0.6, background #F9FAFB, badge [OK] verde
  com-rnc:     badge [RNC] vermelho no canto superior
```

#### DS-04-F. Modal

```
Backdrop: rgba(0,0,0,0.5) — blur: 2px
Container: bg #FFFFFF, border-radius 12px, max-width 560px (padrao) / 800px (grande)
Header: padding 24px 24px 16px, border-bottom 1px solid #E5E7EB
Body: padding 24px, overflow-y auto, max-height calc(100vh - 200px)
Footer: padding 16px 24px, border-top 1px solid #E5E7EB, flex, justify-between
Animacao abertura: opacity 0->1 + scale 0.96->1, 200ms ease-out
Fechamento: ESC, backdrop click (exceto modais criticos)
```

#### DS-04-G. DataTable

```
Container:
  background: #FFFFFF
  border: 1px solid #E5E7EB
  border-radius: 8px
  box-shadow: 0 1px 3px rgba(0,0,0,0.08)
  overflow: hidden

Header:
  background: #F9FAFB
  font: Arial 10px 600 #6B7280 UPPERCASE letter-spacing 0.05em
  padding: 8px 16px
  border-bottom: 1px solid #E5E7EB
  height: 36px
  sticky ao scroll vertical

Linhas:
  height: 36px (desktop), 28px (compacto), 44px (mobile)
  border-bottom: 1px solid #F3F4F6
  hover: background #F9FAFB
  cursor: pointer (linhas clicaveis)

Indicadores de linha:
  Sinaleiro ROXO:     border-left 3px solid #7030A0
  Sinaleiro VERMELHO: border-left 3px solid #FF0000
  P0/P1:             border-left 3px solid #FF0000/#FF6600

Pagination:
  Container: padding 12px 16px, border-top 1px solid #E5E7EB
  Texto: "Mostrando X-Y de Z"
  Botoes: Previous / Next, desabilitados quando nao aplicavel
  Tamanho de pagina: [25, 50, 100] dropdown

Ordenacao:
  Icone: seta up/down, neutro cinza quando inativo, verde #00B050 ativo
  Click no cabecalho: asc -> desc -> sem ordenacao

Estados:
  loading: skeleton rows com pulse animation, 6 linhas
  empty:   icone centralizado + mensagem descritiva
  error:   faixa vermelha no topo com mensagem de erro
```

#### DS-04-H. FilterBar

```
Container:
  background: #FFFFFF
  border: 1px solid #E5E7EB
  border-radius: 8px
  padding: 12px 16px
  display: flex, align-items: center, gap: 8px, flex-wrap: wrap

Elementos:
  Search input: width 280px, height 32px, border-radius 6px
    - icone lupa a esquerda (16px, #9CA3AF)
    - placeholder "Buscar por nome ou CNPJ..."
    - clear button "x" quando preenchido

  Dropdown filter: height 32px, min-width 120px
    - border: 1px solid #D1D5DB, border-radius 6px
    - font: Arial 12px #374151
    - ativo (filtro aplicado): border-color #00B050, background #F0FDF4
    - badge contador quando filtro ativo: pequeno circulo verde com numero

  Botao Limpar filtros:
    - apenas texto "Limpar" #6B7280
    - visivel somente quando ha filtros ativos
    - hover: #374151

Filtros disponiveis (por tela):
  Carteira:  Consultor, Situacao, Sinaleiro, ABC, Temperatura, Prioridade, UF
  Sinaleiro: Consultor, Cor, Rede
  Agenda:    Consultor, Prioridade, Sinaleiro
  RNC:       Consultor, Tipo, Status, Area Responsavel
```

#### DS-04-I. TimelineEntry

```
Layout vertical com linha conectora:

  25/03 ─●─ [Lig] LARISSA                Pedido realizado
             "Confirmou 50cx de caldo natural. Pedido #12.456"

  18/03 ─●─ [Wpp] LARISSA                Retornar
             "Aguardando aprovacao do gerente para pedido maior"

Especificacoes:
  Linha vertical: 2px solid #E5E7EB, margem esquerda 52px
  Dot: 8px circulo, border 2px solid {cor tipo contato}, bg #FFF

  Data: Arial 9px 500 #9CA3AF, width 40px, alinhada a direita
  Gap linha-conteudo: 8px

  Conteudo:
    Linha 1: [tipo badge] + consultor (bold) + resultado (badge colorido)
    Linha 2: descricao italic #6B7280, max 2 linhas, text-overflow ellipsis

  Cor do dot e tipo badge por tipo contato:
    Ligacao:   #2563EB
    WhatsApp:  #00A651
    Visita:    #7C3AED
    Email:     #F59E0B

  Resultado badge: StatusBadge variante personalizada
    VENDA:         bg #00B050 text #FFF
    ORCAMENTO:     bg #0EA5E9 text #FFF
    EM ATENDIMENTO:bg #2563EB text #FFF
    FU7/FU15:      bg #9CA3AF text #FFF
    NAO ATENDE:    bg #FFC000 text #1A1A1A
    NAO RESPONDE:  bg #FFC000 text #1A1A1A
    RECUSOU:       bg #FF0000 text #FFF
    PERDA:         bg #FF0000 text #FFF
    CS/POS-VENDA:  bg #7C3AED text #FFF
```

#### DS-04-J. ProgressMeta (Barra de Meta)

```
Label: Arial 9px #6B7280
Barra: height 8px, border-radius 4px
Bg: #E5E7EB
Preenchimento:
  >= 100%: #00B050 (verde — atingiu)
  >= 80%:  #FFC000 (amarelo — perto)
  >= 50%:  #FF6600 (laranja — atencao)
  <  50%:  #FF0000 (vermelho — critico)

Uso: coluna "% Meta" em tabelas de projecao e sinaleiro
```

#### DS-04-K. DonutChart (Grafico Rosca)

```
Uso: distribuicao de sinaleiro no Dashboard CEO

Tamanho: 120px x 120px
Espessura anel: 20px
Centro: percentual total ou valor (Arial 12px bold)

Segmentos por ordem (maior para menor):
  VERDE:    #00B050
  AMARELO:  #FFC000
  VERMELHO: #FF0000
  ROXO:     #7030A0

Legenda (ao lado direito):
  Cada linha: [cor dot 8px] + label + (qtd) + "R$ valor"
  Arial 9px #374151

Hover em segmento: tooltip com detalhes
Animacao: stroke-dasharray de 0 ate valor final, 800ms ease-out
```

### DS-05. Layout e Navegacao

```
Layout geral (desktop):
┌─────────────────────────────────────────────────────────────────┐
│                         HEADER (48px)                           │
├──────────┬──────────────────────────────────────────────────────┤
│          │                                                       │
│ SIDEBAR  │              CONTEUDO DA PAGINA                      │
│ (224px)  │              (flex-1, overflow-y auto)               │
│          │                                                       │
└──────────┴──────────────────────────────────────────────────────┘

Header:
  height: 48px
  background: #FFFFFF
  border-bottom: 1px solid #E5E7EB
  padding: 0 16px
  Conteudo: [hamburger mobile] [titulo pagina] [spacer] [user info] [logout]

Sidebar:
  width: 224px (desktop fixo), drawer (mobile)
  background: #FFFFFF
  border-right: 1px solid #E5E7EB
  overflow-y: auto

  Topo: Logo VITAO360 (28px icone verde + texto)
  Corpo: links de navegacao (5px gap)
  Rodape: secao admin + versao

  Item de nav:
    padding: 8px 12px
    border-radius: 6px
    font: Arial 12px 500
    gap icone-texto: 10px
    ativo: bg #F0FDF4, text #00B050, border 1px solid #DCFCE7
    hover: bg #F9FAFB, text #374151

Mobile (< 1024px):
  Sidebar: drawer com overlay (translateX -100% -> 0)
  Header: hamburger button visivel
  Main: padding 12px (menor que desktop)
```

### DS-06. Animacoes e Transicoes

```
Principio: animacoes so em momentos de alto impacto.
Duracao padrao: 150-200ms (rapido = sensacao de responsividade)

Transicoes permitidas:
  Hover button/link:     background-color 150ms ease
  Hover card/linha:      box-shadow + transform 150ms ease
  Modal abertura:        opacity + scale 200ms ease-out
  Sidebar mobile:        translateX 200ms ease
  Skeleton pulse:        opacity 0.4->1->0.4, 1.5s infinite
  Progress bar:          width 400ms ease-out (ao montar)
  Score bar:             width 400ms ease-out (ao montar)

Transicoes proibidas:
  Sem animacoes de rotacao desnecessarias
  Sem bounce ou spring exagerado
  Sem delays superiores a 300ms
```

### DS-07. Acessibilidade

```
ARIA obrigatorios:
  Sidebar: role="navigation" aria-label="Menu principal"
  Tabelas: role="table" com cabecalhos <th scope="col">
  Botoes de acao: aria-label descritivo ("Registrar atendimento de {nome}")
  Modais: role="dialog" aria-modal="true" aria-labelledby="{id do titulo}"
  Status badges: aria-label="{tipo}: {valor}" (ex: "Sinaleiro: VERMELHO")
  Filtros: aria-label por dropdown ("Filtrar por situacao")
  Loading: aria-busy="true" + aria-label="Carregando..."

Foco:
  Focus ring: 2px solid #00B050, offset 2px
  Ordem de tabulacao: logica e sequencial
  Esc: fecha modais e drawers
  Enter/Space: ativa botoes e links
  Sem armadilhas de foco (exceto modais abertas)

Contraste minimo:
  Texto sobre fundo: minimo 4.5:1 (WCAG AA)
  Excecao badges P3/ABC-B (FFFF00): verificado — #1A1A1A sobre #FFFF00 = 17:1 OK
  Excecao badges P6/P7 cinza claro: verificado — #6B7280 sobre #E5E7EB = 4.6:1 OK

Elementos interativos:
  Area minima de clique: 44x44px (WCAG 2.5.5)
  Botoes de linha em tabela: minimo 32px altura
```

---

## TELAS — ESPECIFICACOES DETALHADAS

### TELA 1: LOGIN (`/login`)

**Proposito:** Autenticacao simples, redirect por role.
**Personas:** Todas (publico).

#### Layout

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                                                                               │
│                              (fundo #F9FAFB)                                  │
│                                                                               │
│                    ┌──────────────────────────────────┐                       │
│                    │                                  │                       │
│                    │    [V]  CRM VITAO360             │                       │
│                    │    Inteligencia Comercial        │                       │
│                    │                                  │                       │
│                    │  ──────────────────────────────  │                       │
│                    │                                  │                       │
│                    │  Email profissional               │                       │
│                    │  ┌──────────────────────────┐   │                       │
│                    │  │ usuario@vitao.com.br      │   │                       │
│                    │  └──────────────────────────┘   │                       │
│                    │                                  │                       │
│                    │  Senha                           │                       │
│                    │  ┌──────────────────────────┐   │                       │
│                    │  │ ••••••••••••         [👁] │   │                       │
│                    │  └──────────────────────────┘   │                       │
│                    │                                  │                       │
│                    │  [       Entrar       ]          │                       │
│                    │                                  │                       │
│                    │  Esqueceu a senha? Fale com      │                       │
│                    │  o administrador.                │                       │
│                    │                                  │                       │
│                    └──────────────────────────────────┘                       │
│                                                                               │
│                    VITAO Alimentos — Uso interno exclusivo                    │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### Especificacoes

**Card login:**
- max-width: 400px, centralizado (horizontal + vertical)
- background: #FFFFFF
- border: 1px solid #E5E7EB
- border-radius: 12px
- padding: 40px
- box-shadow: 0 4px 16px rgba(0,0,0,0.08)

**Logo VITAO:**
- Quadrado 40px, background #00B050, border-radius 8px
- Letra "V" branca, bold, 22px
- Titulo "CRM VITAO360" Arial 18px bold #111827
- Subtitulo "Inteligencia Comercial" Arial 11px #9CA3AF

**Inputs:**
- height: 40px, border-radius: 6px
- border: 1px solid #D1D5DB
- font: Arial 12px #374151
- focus: border-color #00B050, ring 2px #00B050 opacity-20
- padding: 8px 12px

**Botao Entrar:**
- width: 100%
- height: 40px
- background: #00B050
- text: #FFFFFF, Arial 13px 600
- border-radius: 6px
- hover: background #007A38
- loading state: spinner branco + "Entrando..."
- disabled: opacity 0.6

**Redirect apos login (por role):**
- admin: `/dashboard`
- consultor LARISSA/MANU: `/agenda` (agenda propria pre-selecionada)
- consultor DAIANE: `/dashboard`
- consultor JULIO: `/agenda`
- viewer: `/carteira`

**Tratamento de erros:**
- Credenciais invalidas: faixa vermelha no topo do card "Credenciais invalidas. Tente novamente."
- Server error: faixa vermelha "Erro de servidor. Tente em alguns instantes."
- Token expirado (redirecionado): faixa amarela "Sessao expirada. Faca login novamente."

**Segurança:**
- JWT armazenado em httpOnly cookie (nao em localStorage)
- Campo senha: type="password" por padrao, toggle visibilidade
- Sem "Lembrar acesso" (seguranca corporativa)

---

### TELA 2: DASHBOARD CEO (`/dashboard`)

**Proposito:** Visao executiva total — KPIs, distribuicoes, saude da carteira.
**Personas:** P1 (Leandro), P4 (Daiane).
**Tela mais densa do sistema — informacao maxima, acao rapida.**

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER: [V] CRM VITAO360    Dashboard              [Leandro] [Sair]         │
├──────────┬──────────────────────────────────────────────────────────────────┤
│          │ DASHBOARD — Visao Geral          [Atualizado: 25/03 05:02]       │
│ SIDEBAR  ├──────────────────────────────────────────────────────────────────┤
│          │                                                                   │
│ Dash [*] │ BLOCO 1: KPI CARDS (6 cards, grid 6 colunas)                    │
│ Carteira │ ┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌──────┐│
│ Agenda   │ │CLIENTES ││ ATIVOS  ││FATURAMENTO│SCORE MED││FU VENCID││CRIT. ││
│ Sinaleiro│ │  661    ││  312    ││R$2.091.000│  58,3   ││   47    ││  28  ││
│ Projecao │ │ 1.581   ││ 47%    ││ baseline  ││ /100    ││ hoje    ││urgent││
│ RNC      │ └─────────┘└─────────┘└─────────┘└─────────┘└─────────┘└──────┘│
│          │                                                                   │
│ Admin    │ BLOCO 2: SINALEIRO + PERFORMANCE                                  │
│ Usuarios │ ┌────────────────────────────────┐ ┌────────────────────────────┐│
│ Motor    │ │  DONUT SINALEIRO               │ │  PERFORMANCE POR CONSULTOR ││
│          │ │                                │ │                            ││
│          │ │     [donut 120px]              │ │  Nome     Cli  Fat  Meta% St││
│          │ │                                │ │  MANU     165  777K  84% BOM││
│ v1.0     │ │ [●] VERDE    134  20.3%        │ │  LARISSA  222  964K  77% BOM││
│          │ │     R$...                      │ │  DAIANE   164  210K  15% !! ││
│          │ │ [●] AMARELO   63   9.5%        │ │  JULIO    110  149K  13% !! ││
│          │ │     R$...                      │ │  TOTAL    661 2.1M  44%     ││
│          │ │ [●] VERMELHO 299  45.2%        │ └────────────────────────────┘│
│          │ │     R$...                      │                               │
│          │ │ [●] ROXO     165  25.0%        │                               │
│          │ │     R$...                      │                               │
│          │ └────────────────────────────────┘                               │
│          │                                                                   │
│          │ BLOCO 3: DISTRIBUICOES (4 barras horizontais clicaveis)          │
│          │ ┌───────────────────────────────────────────────────────────────┐│
│          │ │ POR SITUACAO          POR PRIORIDADE                          ││
│          │ │ ATIVO     ████████ 47%│ P0+P1 ██ 8%                          ││
│          │ │ INAT.REC  ████    18% │ P2    ████ 20%                       ││
│          │ │ INAT.ANT  ██      9%  │ P3    ████████ 28%                   ││
│          │ │ PROSPECT  ████    16% │ P4+   ████████████ 44%               ││
│          │ │                       │                                       ││
│          │ │ POR TEMPERATURA       POR ABC                                 ││
│          │ │ QUENTE  ██ 12%        │ A (top 20%)  ████ 20%                ││
│          │ │ MORNO   ████████ 38%  │ B (prox 30%) ██████ 30%              ││
│          │ │ FRIO    ████████ 35%  │ C (resto)    ████████████ 50%        ││
│          │ │ CRITICO ██ 10%        │                                       ││
│          │ └───────────────────────────────────────────────────────────────┘│
│          │                                                                   │
│          │ BLOCO 4: TOP 10 CLIENTES POR FATURAMENTO                        │
│          │ ┌────┬─────────────────────┬──────────┬───────────┬───┬───┬────┐│
│          │ │ #  │ Cliente             │ Consultor│ Fat 2025  │ Sc│ABC│Sin ││
│          │ ├────┼─────────────────────┼──────────┼───────────┼───┼───┼────┤│
│          │ │  1 │ Distribuidora A     │ LARISSA  │ R$180.000 │87 │[A]│[V] ││
│          │ │  2 │ Rede Sul Ltda       │ MANU     │ R$145.000 │75 │[A]│[V] ││
│          │ │  3 │ Natural Shop        │ LARISSA  │ R$ 98.000 │62 │[A]│[Am]││
│          │ │ ...│ ...                 │          │           │   │   │    ││
│          │ └────┴─────────────────────┴──────────┴───────────┴───┴───┴────┘│
└──────────┴──────────────────────────────────────────────────────────────────┘
```

#### Bloco 1 — KPI Cards (6 cards)

| Card | Valor | Subtitulo | Accent |
|------|-------|-----------|--------|
| Total Clientes | 661 | "1.581 na carteira total" | #2563EB |
| Ativos | 312 | "47% da carteira ativa" | #00B050 |
| Faturamento | R$ 2.091.000 | "Baseline 2025" | #7C3AED |
| Score Medio | 58,3 | "De 0 a 100" | #0EA5E9 |
| Follow-ups Vencidos | 47 | "Acao necessaria hoje" | #F59E0B |
| Clientes Criticos | 28 | "P0/P1 sem contato" | #DC2626 |

Cards de FU Vencidos e Criticos sao clicaveis: redirect para `/agenda?prioridade=P0,P1`.

#### Bloco 2 — Sinaleiro + Performance

**Donut Sinaleiro:**
- Hover em segmento: tooltip "VERMELHO: 299 clientes | R$ XXX"
- Click em segmento: filtra `/clientes?sinaleiro=VERMELHO`
- Centro: percentual do segmento ao hover, "661 clientes" em repouso

**Tabela Performance:**
- Status BOM: badge verde
- Status CRITICO: badge vermelho + linha com fundo #FEF2F2
- Click na linha: filtra carteira por consultor

#### Bloco 3 — Distribuicoes

- 4 mini-graficos de barra horizontal em grid 2x2
- Barras clicaveis: click filtra a carteira com aquele critério
- Cores: conforme paleta de status correspondente

#### Bloco 4 — Top 10

- Tabela compacta, 10 linhas fixas
- Click na linha: abre detalhe do cliente

---

### TELA 3: AGENDA (`/agenda`) — TELA MAIS IMPORTANTE

**Proposito:** Lista diaria priorizada. O CRM manda, o consultor executa.
**Personas:** P2 (Manu), P3 (Larissa), P4 (Daiane), P5 (Julio).
**Principio central:** O consultor abre e ve EXATAMENTE quem ligar, em que ordem, e o que fazer.

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER: [V] CRM VITAO360   Agenda           [Larissa Padilha] [Sair]        │
├──────────┬──────────────────────────────────────────────────────────────────┤
│          │ AGENDA COMERCIAL — LARISSA PADILHA        25/03/2026 (Segunda)   │
│ SIDEBAR  │ ┌───────────────────────────────────────────────────────────┐    │
│ (Leandro │ │  23 de 47 atendimentos concluidos hoje   ███████░░░░ 49%  │    │
│ ve todas)│ └───────────────────────────────────────────────────────────┘    │
│          │                                                                   │
│ Agenda[*]│ ABAS CONSULTOR (Leandro ve todas; consultor ve so a sua):         │
│          │ [LARISSA (47)] [MANU (38)] [JULIO (22)] [DAIANE (18)]            │
│          │                                                                   │
│          │ FILTROS:  [Prioridade ▾] [Sinaleiro ▾] [Busca nome/CNPJ...]     │
│          │                                                                   │
│          │ AVISOS ESPECIAIS:                                                 │
│          │ ⚠ 3 clientes P0/P1 aguardam. Prioridade maxima.                 │
│          │                                                                   │
│          │ ─────── PRIORITARIOS (pula fila) ─────────────────────────────  │
│          │                                                                   │
│          │ ┌──────────────────────────────────────────────────────────────┐ │
│          │ │[P1] #1  ──DISTRIBUIDORA LIGEIRO LTDA ─────────────── [VERM] │ │
│          │ │         RJ — ATIVO — 45 dias sem compra                     │ │
│          │ │         ┌───────────────────────────────────────────────┐   │ │
│          │ │         │ ACAO: Confirmar orcamento enviado, fechar venda│   │ │
│          │ │         └───────────────────────────────────────────────┘   │ │
│          │ │         Tentativa T2 | Follow-up: HOJE (vencido 2d)        │ │
│          │ │                              [Registrar Atendimento]        │ │
│          │ └──────────────────────────────────────────────────────────────┘ │
│          │                                                                   │
│          │ ┌──────────────────────────────────────────────────────────────┐ │
│          │ │[P3] #2  MERCADINHO DO PEDRO ─────────────────────── [VERM]  │ │
│          │ │         SP — SUPORTE ABERTO — problema entrega               │ │
│          │ │         ┌───────────────────────────────────────────────┐   │ │
│          │ │         │ ACAO: Verificar status do chamado de suporte   │   │ │
│          │ │         └───────────────────────────────────────────────┘   │ │
│          │ │         Tentativa T1 | Follow-up: ONTEM (vencido 1d)       │ │
│          │ │                              [Registrar Atendimento]        │ │
│          │ └──────────────────────────────────────────────────────────────┘ │
│          │                                                                   │
│          │ ─────── REGULAR ─────────────────────────────────────────────   │
│          │                                                                   │
│          │ ┌──────────────────────────────────────────────────────────────┐ │
│          │ │[P2] #3  NATURAL SHOP ────────────────────────────── [AMAR]  │ │
│          │ │         PR — ATIVO — 22 dias sem compra                     │ │
│          │ │         ┌───────────────────────────────────────────────┐   │ │
│          │ │         │ ACAO: Tentativa de recompra — oferecer novidade│   │ │
│          │ │         └───────────────────────────────────────────────┘   │ │
│          │ │         Tentativa T1 | Follow-up: 28/03 (3 dias)           │ │
│          │ │                              [Registrar Atendimento]        │ │
│          │ └──────────────────────────────────────────────────────────────┘ │
│          │ [+ 44 clientes restantes...]                                      │
└──────────┴──────────────────────────────────────────────────────────────────┘
```

#### Especificacoes Detalhadas

**Barra de progresso do dia:**
- height: 8px, border-radius 4px
- text: "X de Y atendimentos concluidos hoje"
- cor: #00B050 (preenchimento), #E5E7EB (vazio)
- atualiza em tempo real apos cada registro

**Tabs de consultor:**
- Leandro: ve todas as 4 abas com badges de contagem
- Consultor: ve SUA aba selecionada por padrao (determinado pelo JWT)
- Cor ativa: borda inferior 2px #00B050, texto #00B050, bg #F0FDF4
- Badge contagem: circulo cinza com numero de itens pendentes

**Separador PRIORITARIOS vs REGULAR:**
- Linha divisoria com label "PRIORITARIOS (pula fila)"
- P0/P3 (suporte) aparecem sempre no topo, mesmo que score baixo
- P1 (namoro novo, urgente) vem logo apos

**Card AgendaCard — detalhamento:**
- Borda esquerda: 4px solid {cor prioridade}
- Header card: [badge prioridade] + [#posicao] + Nome + [badge sinaleiro]
- Linha 2: UF — Situacao — "X dias sem compra"
- BLOCO ACAO (destaque principal):
  - background: #F0FDF4 (sinaleiro verde) / #FEF2F2 (vermelho) / #FFFBEB (amarelo)
  - border-left: 3px solid {cor sinaleiro}
  - font: Arial 12px semibold #111827
  - texto: exatamente o campo ACAO_FUTURA do Motor
- Linha tentativa: "Tentativa T{n} | Follow-up: {data} ({status}"
  - status "HOJE": badge amarelo pulsante
  - status "vencido Nd": badge vermelho
  - status "em X dias": texto cinza
- Botao "Registrar Atendimento": verde, alinhado a direita
  - hover: sombra, translateY(-1px)
  - click: abre Modal de Atendimento

**Marcacao de concluido:**
- Card concluido: opacity 0.55, bg #F9FAFB, icone [✓] no lugar do botao
- Nao desaparece (consultor confirma que fez)

**Contadores:**
- Subtitulo: "Bom dia, Larissa. 47 clientes aguardam hoje."
- Progresso: texto + barra dinamica

---

### TELA 4: MODAL DE ATENDIMENTO (modal na Agenda)

**Proposito:** Registro rapido de atendimento. Maximo 30 segundos para preencher.
**Regra critica:** Complexidade ZERO. Motor faz o resto.

#### Layout

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ BACKDROP (rgba(0,0,0,0.5))                                                   │
│                                                                              │
│     ┌──────────────────────────────────────────────────────────────────┐    │
│     │  REGISTRAR ATENDIMENTO                                    [X]    │    │
│     │  DISTRIBUIDORA LIGEIRO LTDA                                      │    │
│     │  04.067.573/0001-93  — ATIVO — [VERMELHO] — Score 87 — P1       │    │
│     ├──────────────────────────────────────────────────────────────────┤    │
│     │                                                                  │    │
│     │  RESULTADO DO CONTATO (obrigatorio)                              │    │
│     │  ┌──────────────────────────────────────────────────────────┐   │    │
│     │  │ Selecione o resultado...                               ▾  │   │    │
│     │  └──────────────────────────────────────────────────────────┘   │    │
│     │  Opcoes: VENDA | ORCAMENTO | EM ATENDIMENTO | POS-VENDA | CS    │    │
│     │          RELACIONAMENTO | FU7 | FU15 | SUPORTE | NAO ATENDE     │    │
│     │          NAO RESPONDE | RECUSOU | CADASTRO | PERDA              │    │
│     │                                                                  │    │
│     │  DESCRICAO (obrigatorio)                                         │    │
│     │  ┌──────────────────────────────────────────────────────────┐   │    │
│     │  │ O que aconteceu neste contato?                           │   │    │
│     │  │                                                          │   │    │
│     │  │                                                          │   │    │
│     │  └──────────────────────────────────────────────────────────┘   │    │
│     │  (minimo 10 caracteres)                                          │    │
│     │                                                                  │    │
│     │  TIPO DE CONTATO                                                 │    │
│     │  [◉] Ligacao  [○] WhatsApp  [○] Visita  [○] Email              │    │
│     │                                                                  │    │
│     │  ─────────────────────────────────────────────────────────────  │    │
│     │                                                                  │    │
│     │  CAMPOS AUTO (lidos apos salvar — Motor processa):               │    │
│     │  Estagio Funil: [ .............. ]  Temperatura: [ ........... ] │    │
│     │  Fase:          [ .............. ]  Follow-up:   [ ........... ] │    │
│     │  Acao Futura:   [ ........................................... ]   │    │
│     │                                                                  │    │
│     │  ─────────────────────────────────────────────────────────────  │    │
│     │                                                                  │    │
│     │  [Cancelar]                          [Salvar Atendimento]        │    │
│     └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────┘

ESTADO APOS SALVAR (2 segundos):

     ┌──────────────────────────────────────────────────────────────────┐
     │  ✓ MOTOR PROCESSOU                                               │
     │                                                                  │
     │  Estagio:     EM ATENDIMENTO                                     │
     │  Temperatura: QUENTE                                             │
     │  Fase:        NEGOCIACAO                                         │
     │  Acao Futura: Confirmar orcamento — cliente pronto para fechar   │
     │  Follow-up:   AMANHA (26/03/2026)                                │
     │                                                                  │
     │  [Fechar e continuar agenda]                                     │
     └──────────────────────────────────────────────────────────────────┘
```

#### Especificacoes

**Campos obrigatorios:**
1. RESULTADO: dropdown com 14 opcoes (mapa Motor)
2. DESCRICAO: textarea, minimo 10 caracteres

**Campos auto (read-only, preenchidos pelo Motor):**
- CNPJ: auto-preenchido pelo contexto do card
- CONSULTOR: auto-preenchido pelo JWT
- DATA/HORA: automatica
- ESTAGIO FUNIL, FASE, TEMPERATURA, ACAO FUTURA, FOLLOW-UP: calculados pelo Motor apos salvar

**Campos NAO existentes (proibido por Two-Base):**
- Nenhum campo de valor R$ no formulario de LOG
- Nota no rodape: "Valor: R$ 0,00 (log de atendimento — Two-Base Architecture)"

**Fluxo de submit:**
1. Consultor escolhe RESULTADO + escreve DESCRICAO
2. Click "Salvar Atendimento"
3. Loading spinner no botao
4. Backend: Motor roda, calcula 9 outputs
5. Modal atualiza para "Estado Apos Salvar" (exibe outputs do Motor)
6. Card da agenda atualiza para "concluido" (sem reload de pagina)
7. Click "Fechar e continuar" fecha modal

**Validacoes:**
- RESULTADO vazio: borda vermelha + "Selecione o resultado"
- DESCRICAO curta: "Minimo 10 caracteres"
- Submit sem validar: botao nao dispara

---

### TELA 5: CARTEIRA (`/clientes`)

**Proposito:** Tabela completa de todos os clientes. Visao analitica e rapida.
**Personas:** Todos.

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                      │
├──────────┬──────────────────────────────────────────────────────────────────┤
│          │ CARTEIRA DE CLIENTES                     661 clientes ativos     │
│ SIDEBAR  ├──────────────────────────────────────────────────────────────────┤
│          │ FILTROS                                                           │
│ Carteira │ ┌──────────────────────────────────────────────────────────────┐ │
│ [ativo]  │ │ [Busca: Nome ou CNPJ...]  [Consultor ▾] [Situacao ▾] [Sinal▾]│ │
│          │ │ [ABC ▾] [Temp. ▾] [Prioridade ▾] [UF ▾]        [Limpar]     │ │
│          │ └──────────────────────────────────────────────────────────────┘ │
│          │ Filtros ativos: [Consultor: LARISSA x] [Sinaleiro: VERMELHO x]   │
│          │                                                                   │
│          │ ┌──────────────────────────────────────────────────────────────┐ │
│          │ │CNPJ         │Nome Fantasia    │UF │Cons.│Sit.   │Temp│Sc│ABC│Sin│
│          │ ├─────────────┼─────────────────┼───┼─────┼───────┼────┼──┼───┼──┤
│          │ │00.000.000/01│Distribuidora A  │RJ │LAR  │[ATIVO]│QUE │87│[A]│[V]│
│          │ │00.001.000/01│Natural Shop     │PR │LAR  │[ATIVO]│MOR │62│[A]│[A]│
│          │ │00.002.000/01│BioBom Ltda      │SP │LAR  │[IN.REC│FRI │45│[B]│[R]│
│          │ │00.003.000/01│Verde Vida       │MG │LAR  │[ATIVO]│MOR │38│[C]│[A]│
│          │ │ ...         │ ...             │   │     │       │    │  │   │  │
│          │ ├─────────────┴─────────────────┴───┴─────┴───────┴────┴──┴───┴──┤
│          │ │ Mostrando 1-50 de 222     [< Anterior]  Pagina 1 / 5  [Proxima>]│
│          │ └──────────────────────────────────────────────────────────────┘  │
└──────────┴──────────────────────────────────────────────────────────────────┘
```

#### Colunas da tabela

| Coluna | Tipo | Largura | Ordenavel |
|--------|------|---------|-----------|
| CNPJ | texto mono | 140px | Sim |
| Nome Fantasia | texto | flex | Sim |
| UF | texto | 40px | Sim |
| Consultor | texto | 80px | Sim |
| Situacao | StatusBadge | 100px | Sim |
| Temperatura | StatusBadge | 80px | Sim |
| Score | numero + barra | 80px | Sim (desc) |
| ABC | StatusBadge | 40px | Sim |
| Sinaleiro | SinaleiroDot | 50px | Sim |
| Faturamento | monetario | 90px | Sim (desc) |

**Colunas ocultas por padrao (toggle "+" para expandir):**
- Prioridade, Fase, Estagio Funil, Dias Sem Compra, Ultimo Pedido, Rede, Cidade

**Comportamentos:**
- Click linha: abre `/clientes/{cnpj}` (pagina de detalhe)
- Hover linha: bg #F9FAFB
- Borda esquerda: conforme sinaleiro (VERMELHO/ROXO = borda colorida)
- Filtros: persistem em URL `?consultor=LARISSA&sinaleiro=VERMELHO`
- Paginacao: 50 por pagina (padrao), opcoes 25/50/100

**Permissoes:**
- P5 (Julio): ve somente seus clientes (filtro automatico)
- Coluna Faturamento: oculta para P5

---

### TELA 6: DETALHE CLIENTE (`/clientes/{cnpj}`)

**Proposito:** Ficha completa do cliente com historico, financeiro e status.
**Personas:** Todos (financeiro oculto para P5).

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER: < Voltar a Carteira                [Leandro] [Sair]                 │
├──────────┬──────────────────────────────────────────────────────────────────┤
│          │ DISTRIBUIDORA LIGEIRO LTDA                    [Registrar Atend.] │
│ SIDEBAR  │ CNPJ: 04.067.573/0001-93  — [ATIVO] — LARISSA                   │
│          ├──────────────────────────────────────────────────────────────────┤
│          │                                                                   │
│          │ BLOCO 1: IDENTIDADE [v]                                           │
│          │ ┌──────────────────────────────────────────────────────────────┐ │
│          │ │ Razao Social: DISTRIBUIDORA LIGEIRO LTDA                     │ │
│          │ │ CNPJ: 04.067.573/0001-93    UF: RJ   Cidade: Rio de Janeiro  │ │
│          │ │ Email: compras@ligeiro.com.br           Tel: (21) 3000-0000   │ │
│          │ │ Rede: Independente   Consultor: LARISSA   SAP: 00012345       │ │
│          │ └──────────────────────────────────────────────────────────────┘ │
│          │                                                                   │
│          │ BLOCO 2: STATUS E MOTOR [v]                                       │
│          │ ┌────────────────────────────┬───────────────────────────────┐   │
│          │ │ Situacao:    [ATIVO]       │ Score: 87/100                 │   │
│          │ │ Temperatura: [QUENTE]      │ [██████████████░░] 87         │   │
│          │ │ Sinaleiro:   [VERMELHO]    │                               │   │
│          │ │ Prioridade:  [P1]          │ Breakdown do Score:           │   │
│          │ │ ABC:         [A]           │ Urgencia (30%): 100 — 30pt    │   │
│          │ │ Fase:        NEGOCIACAO    │ Valor (25%):     80 — 20pt    │   │
│          │ │ Estagio:     EM ATENDIMENTO│ Follow-up (20%): 100 — 20pt   │   │
│          │ │ Tipo Cliente:RECORRENTE    │ Sinal (15%):      60 —  9pt   │   │
│          │ │ Tentativa:   T2            │ Tentativa (5%):   70 —  3,5pt │   │
│          │ │ Dias s/compra: 45          │ Situacao (5%):    40 —  2pt   │   │
│          │ │ Ciclo medio: 23 dias       │                               │   │
│          │ │                            │ SCORE TOTAL: 87,5             │   │
│          │ └────────────────────────────┴───────────────────────────────┘   │
│          │                                                                   │
│          │ BLOCO 3: FINANCEIRO [v] (oculto para P5)                         │
│          │ ┌──────────────────────────────────────────────────────────────┐ │
│          │ │ Faturamento 2025:  R$ 180.000  │ Ticket Medio: R$ 12.000    │ │
│          │ │ Faturamento 2026:  R$  22.500  │ N Compras 12m: 15           │ │
│          │ │ Meta 2026:         R$ 240.000  │ Meses positivados: 8/12     │ │
│          │ │ % Atingido:        9.4%        │ Ultima compra: 01/02/2026   │ │
│          │ │                                │                             │ │
│          │ │ Vendas mes a mes 2026:                                       │ │
│          │ │ Jan: R$12.500 | Fev: R$10.000 | Mar: — | ...               │ │
│          │ └──────────────────────────────────────────────────────────────┘ │
│          │                                                                   │
│          │ BLOCO 4: HISTORICO DE ATENDIMENTOS [v]                           │
│          │ ┌──────────────────────────────────────────────────────────────┐ │
│          │ │  25/03 ─●─ [Lig] LARISSA      [EM ATENDIMENTO]              │ │
│          │ │             "Confirmou orcamento enviado, aguarda aprovacao"  │ │
│          │ │                                                               │ │
│          │ │  18/03 ─●─ [Wpp] LARISSA      [FU7]                         │ │
│          │ │             "Enviou mensagem de acompanhamento do pedido"     │ │
│          │ │                                                               │ │
│          │ │  10/03 ─●─ [Lig] LARISSA      [ORCAMENTO]                   │ │
│          │ │             "Enviou proposta por email. Aguardando retorno."  │ │
│          │ │                                                               │ │
│          │ │  [Carregar mais 17 atendimentos]                              │ │
│          │ └──────────────────────────────────────────────────────────────┘ │
└──────────┴──────────────────────────────────────────────────────────────────┘
```

#### Especificacoes

**Blocos colapsaveis:**
- Header de bloco: titulo + seta (▼/▲) + click expande/colapsa
- Estado salvo em sessionStorage (persiste entre navegacoes)
- Por padrao: todos abertos

**Bloco Status — Score Breakdown:**
- Cada linha: label (peso%) + valor numerico + pontos calculados
- Total destacado com separador e fonte maior
- Sem explicar POR QUE o score e alto/baixo — so os numeros
- Nota: "Score calculado automaticamente pelo Motor"

**Bloco Financeiro:**
- Vendas mes a mes: chips compactos com o valor de cada mes
- Mes sem dado: "—"
- % Atingido: badge colorido (ProgressMeta)

**Bloco Historico:**
- 20 primeiros atendimentos visiveis
- Paginacao: "Carregar mais X" (append, nao substitui)
- Ordenacao: mais recente primeiro
- Click em entrada: expande descricao completa (se truncada)

**Botao "Registrar Atendimento":**
- Fixo no header da pagina
- Abre o mesmo Modal de Atendimento da Agenda

---

### TELA 7: SINALEIRO (`/sinaleiro`)

**Proposito:** Saude de toda a carteira por status de sinaleiro.
**Personas:** P1 (Leandro), P4 (Daiane).

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                      │
├──────────┬──────────────────────────────────────────────────────────────────┤
│          │ SINALEIRO DE CARTEIRA                   661 clientes analisados  │
│ SIDEBAR  ├──────────────────────────────────────────────────────────────────┤
│          │ RESUMO (4 cards clicaveis)                                        │
│ Sinaleiro│ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐     │
│ [ativo]  │ │  VERDE     │ │  AMARELO   │ │  VERMELHO  │ │   ROXO     │     │
│          │ │  134       │ │   63       │ │   299      │ │   165      │     │
│          │ │  20.3%     │ │   9.5%     │ │  45.2%     │ │  25.0%     │     │
│          │ │ R$ ...     │ │ R$ ...     │ │ R$ ...     │ │ R$ ...     │     │
│          │ └────────────┘ └────────────┘ └────────────┘ └────────────┘     │
│          │                                                                   │
│          │ FILTROS: [Cor ▾] [Consultor ▾] [Rede ▾] [ABC ▾]  [Limpar]      │
│          │                                                                   │
│          │ ┌──────────────────────────────────────────────────────────────┐ │
│          │ │CNPJ    │Nome Fantasia  │Cons.│Rede│Meta    │Real  │%  │Gap  │Cor│
│          │ ├────────┼───────────────┼─────┼────┼────────┼──────┼───┼─────┼──┤
│          │ │04.067..│Distrib. Ligei.│LAR  │ —  │R$24.0K │R$22K │92%│-2K │[V]│
│          │ │00.001..│Natural Shop   │LAR  │ —  │R$12.0K │R$8K  │67%│-4K │[A]│
│          │ │00.002..│BioBom Ltda    │LAR  │ —  │R$18.0K │R$2K  │11%│-16K│[R]│
│          │ │00.003..│Verde Vida     │LAR  │ —  │R$6.0K  │R$0   │0% │-6K │[Rx]│
│          │ │ ...    │ ...           │     │    │        │      │   │    │  │
│          │ ├────────┴───────────────┴─────┴────┴────────┴──────┴───┴─────┴──┤
│          │ │ Mostrando 1-50 de 299 (filtrado: VERMELHO)                     │
│          │ └──────────────────────────────────────────────────────────────┘  │
│          │                                                                   │
│          │ NOTA: Sinaleiro = saude do ciclo de compra (dias / ciclo medio)  │
│          │ VERDE: saudavel | AMARELO: atencao | VERMELHO: em risco | ROXO: s/ hist.
└──────────┴──────────────────────────────────────────────────────────────────┘
```

#### Cards de Resumo

- Click em card filtra a tabela para aquela cor
- Card selecionado: borda 2px solid {cor}, bg opacity 10%
- Faturamento de cada grupo: soma de todos os clientes daquela cor

#### Colunas

| Coluna | Descricao |
|--------|-----------|
| CNPJ | monospace |
| Nome | click abre detalhe |
| Consultor | filtro rapido |
| Rede | franquia/rede |
| Meta | meta mensal/anual |
| Realizado | R$ real |
| % Atingimento | ProgressMeta badge |
| Gap | diferenca, vermelho se negativo |
| Cor | SinaleiroBadge grande |
| Maturidade | VERDE>=100%, AMARELO>=50%, VERMELHO>=1%, ROXO=0% |
| Acao | texto do Motor ("Cobrar recompra", "Salvar urgente") |

---

### TELA 8: PROJECAO (`/projecao`)

**Proposito:** Metas vs realizado por consultor e mes.
**Personas:** P1 (Leandro) exclusivamente.

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                      │
├──────────┬──────────────────────────────────────────────────────────────────┤
│          │ PROJECAO COMERCIAL 2026              [Periodo ▾] [Consultor ▾]  │
│ SIDEBAR  ├──────────────────────────────────────────────────────────────────┤
│          │                                                                   │
│ Projecao │ DESTAQUE:                                                         │
│ [ativo]  │ ┌─────────────────────┐ ┌─────────────────────┐                  │
│          │ │ BASELINE 2025       │ │ META 2026            │                  │
│          │ │ R$ 2.091.000        │ │ R$ 4.747.200         │                  │
│          │ │ (auditoria forense) │ │ +127% vs 2025        │                  │
│          │ └─────────────────────┘ └─────────────────────┘                  │
│          │ ┌─────────────────────┐ ┌─────────────────────┐                  │
│          │ │ REALIZADO 2026 YTD  │ │ PROJECAO 2026        │                  │
│          │ │ R$ 415.904          │ │ R$ 3.377.120         │                  │
│          │ │ 8.8% da meta anual  │ │ +69% vs 2025         │                  │
│          │ └─────────────────────┘ └─────────────────────┘                  │
│          │                                                                   │
│          │ REALIZADO vs META POR CONSULTOR (barras agrupadas)               │
│          │ ┌──────────────────────────────────────────────────────────────┐ │
│          │ │  MANU    Meta: R$926K  Real: R$777K  ████████████████░ 84%   │ │
│          │ │  LARISSA Meta:R$1.24M  Real: R$964K  █████████████░░░░ 77%   │ │
│          │ │  DAIANE  Meta:R$1.4M   Real: R$210K  ████░░░░░░░░░░░░░ 15%   │ │
│          │ │  JULIO   Meta:R$1.19M  Real: R$150K  ███░░░░░░░░░░░░░░ 13%   │ │
│          │ └──────────────────────────────────────────────────────────────┘ │
│          │                                                                   │
│          │ TABELA: META vs REALIZADO POR CLIENTE                            │
│          │ ┌──────────────────────────────────────────────────────────────┐ │
│          │ │ Cliente    │Consult│Meta Anual │Realizado│% Ating│   Gap     │ │
│          │ ├────────────┼───────┼───────────┼─────────┼───────┼───────────┤ │
│          │ │ Distrib. A │LARISSA│R$ 240.000 │R$ 22.500│  9.4% │-R$217.500│ │
│          │ │ Nat. Shop  │LARISSA│R$ 144.000 │R$ 18.000│ 12.5% │-R$126.000│ │
│          │ │ Rede Sul   │MANU   │R$ 180.000 │R$145.000│ 80.6% │ -R$35.000│ │
│          │ │ ...        │       │           │         │       │           │ │
│          │ └──────────────────────────────────────────────────────────────┘ │
└──────────┴──────────────────────────────────────────────────────────────────┘
```

#### Especificacoes

**Grafico de barras:**
- Barra Meta: cinza #E5E7EB (fundo)
- Barra Realizado: sobreposta, cor por % atingimento (ProgressMeta)
- Label: % atingimento ao final da barra

**Tabela:**
- Gap negativo: texto #DC2626 + parenteses `(R$ 217.500)`
- Gap positivo: texto #00B050
- % Atingimento: ProgressMeta badge

**Filtros:**
- Periodo: Q1/Q2/Q3/Q4/Anual
- Consultor: multiselect

---

### TELA 9: RNC (`/rnc`)

**Proposito:** Registro e acompanhamento de nao-conformidades.
**Personas:** P1 (Leandro), P2 (Manu), P3 (Larissa), P4 (Daiane).

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                      │
├──────────┬──────────────────────────────────────────────────────────────────┤
│          │ REGISTRO DE NAO-CONFORMIDADE (RNC)        [+ Nova RNC]           │
│ SIDEBAR  ├──────────────────────────────────────────────────────────────────┤
│          │ PAINEL RESUMO                                                     │
│ RNC      │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │
│ [ativo]  │ │  RESOLVIDO   │ │ EM ANDAMENTO │ │   PENDENTE   │              │
│          │ │  84  (62%)   │ │  31  (23%)   │ │  20  (15%)   │              │
│          │ └──────────────┘ └──────────────┘ └──────────────┘              │
│          │                                                                   │
│          │ FILTROS: [Consultor ▾] [Tipo ▾] [Status ▾] [Area ▾]  [Limpar]  │
│          │                                                                   │
│          │ ┌──────────────────────────────────────────────────────────────┐ │
│          │ │ # │Data  │Cliente        │Tipo Problema │Area   │Status│Dias │ │
│          │ ├───┼──────┼───────────────┼──────────────┼───────┼──────┼─────┤ │
│          │ │ 1 │25/03 │Distrib. A     │Atraso Entrega│Expedi │[PEND]│  0 │ │
│          │ │ 2 │20/03 │Natural Shop   │Erro NF       │Fiscal │[AND] │  5 │ │
│          │ │ 3 │15/03 │BioBom Ltda    │Produto Avar. │Qualid │[RES] │  8 │ │
│          │ │ 4 │10/03 │Verde Vida     │Cobranca Indev│Financ │[PEND]│ 15 │ │
│          │ │ ...│ ...  │ ...           │ ...          │       │      │    │ │
│          │ ├───┴──────┴───────────────┴──────────────┴───────┴──────┴─────┤ │
│          │ │ Mostrando 1-50 de 135 RNCs                                    │ │
│          │ └──────────────────────────────────────────────────────────────┘ │
│          │                                                                   │
│          │ SLA: Pendentes > 5 dias aparecem em vermelho                     │
└──────────┴──────────────────────────────────────────────────────────────────┘
```

#### 8 Tipos de Problema

1. Atraso na Entrega — Area: Expedicao
2. Produto Avariado — Area: Qualidade
3. Erro na Nota Fiscal — Area: Fiscal/TI
4. Cobranca Indevida — Area: Financeiro
5. Problema de Cadastro — Area: Comercial/TI
6. Falta de Produto — Area: Estoque
7. Reclamacao de Qualidade — Area: Qualidade
8. Outro — Area: Comercial

#### Status Badges

| Status | Cor |
|--------|-----|
| PENDENTE | #FF0000 texto branco |
| EM ANDAMENTO | #FFC000 texto escuro |
| RESOLVIDO | #00B050 texto branco |

**SLA:**
- PENDENTE > 5 dias: linha bg #FEF2F2, badge "ATRASADO"
- PENDENTE > 10 dias: badge pulsante

**Modal "Nova RNC":**
- Campos: Cliente (CNPJ autocomplete), Tipo Problema (dropdown 8 opcoes), Descricao, Area Responsavel (auto pelo tipo)
- Sem campos de valor monetario

---

### TELA 10: ADMIN MOTOR (`/admin/motor`)

**Proposito:** Visualizar as 92 regras do Motor. Read-only (L3 para alterar).
**Personas:** P1 (Leandro) exclusivamente.

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                      │
├──────────┬──────────────────────────────────────────────────────────────────┤
│          │ MOTOR DE REGRAS v4                    92 combinacoes — READ ONLY │
│ SIDEBAR  ├──────────────────────────────────────────────────────────────────┤
│          │ AVISO: Alteracoes no Motor = decisao L3 (aprovacao Leandro).     │
│ Admin    │ Esta tela e somente leitura. Para alterar: abrir chamado.        │
│ Motor[*] │                                                                   │
│          │ FILTROS: [Situacao ▾]  [Resultado ▾]  [Fase ▾]                  │
│          │                                                                   │
│          │ ┌──────────────────────────────────────────────────────────────┐ │
│          │ │ Situacao  │Resultado      │Estagio Funil   │Fase    │Temp│FU │ │
│          │ ├───────────┼───────────────┼────────────────┼────────┼────┼───┤ │
│          │ │[ATIVO]    │VENDA          │ACOMP POS-VENDA │POS-VND │QUE │ 4 │ │
│          │ │[ATIVO]    │ORCAMENTO      │ORCAMENTO       │NEGOC.  │QUE │ 7 │ │
│          │ │[ATIVO]    │EM ATENDIMENTO │EM ATENDIMENTO  │NEGOC.  │QUE │ 3 │ │
│          │ │[ATIVO]    │POS-VENDA      │POS-VENDA       │POS-VND │MOR │15 │ │
│          │ │[ATIVO]    │CS             │CS              │RECOMPRA│MOR │30 │ │
│          │ │[ATIVO]    │NAO ATENDE     │TENTATIVA       │NEGOC.  │FRI │ 1 │ │
│          │ │[ATIVO]    │NAO RESPONDE   │TENTATIVA       │NEGOC.  │FRI │ 1 │ │
│          │ │[ATIVO]    │RECUSOU        │FOLLOW-UP       │NEGOC.  │FRI │15 │ │
│          │ │[ATIVO]    │RELACIONAMENTO │RELACIONAMENTO  │POS-VND │MOR │30 │ │
│          │ │[ATIVO]    │FU7            │FOLLOW-UP       │NEGOC.  │MOR │ 7 │ │
│          │ │[ATIVO]    │FU15           │FOLLOW-UP       │NEGOC.  │MOR │15 │ │
│          │ │[ATIVO]    │SUPORTE        │SUPORTE         │POS-VND │CRI │ 1 │ │
│          │ │[ATIVO]    │CADASTRO       │CADASTRO        │NEGOC.  │QUE │ 3 │ │
│          │ │[ATIVO]    │PERDA          │NUTRICAO        │NUTRICAO│PER │ — │ │
│          │ │ ...       │ ...           │ ...            │ ...    │... │...│ │
│          │ └──────────────────────────────────────────────────────────────┘ │
│          │                                                                   │
│          │ COLUNAS COMPLETAS: Situacao | Resultado | Estagio Funil | Fase   │
│          │   | Tipo Contato | Acao Futura | Temperatura | FU (dias) | Grupo │
└──────────┴──────────────────────────────────────────────────────────────────┘
```

#### Colunas completas

| Coluna | Descricao |
|--------|-----------|
| Situacao | Badge situacao (7 valores) |
| Resultado | Resultado do consultor (14 valores) |
| Estagio Funil | Output Motor |
| Fase | Output Motor |
| Tipo Contato | Output Motor |
| Acao Futura | Texto prescritivo (pode ser longo) |
| Temperatura | Output Motor |
| Follow-up (dias) | Numero |
| Grupo Dashboard | Agrupamento |
| Tipo Acao | Classificacao |

**Navegacao de 92 linhas:**
- Sem paginacao (tabela curta — 92 linhas cabem com scroll)
- Filtro por situacao: mostra subset (ex: apenas ATIVO = 14 linhas)

---

### TELA 11: ADMIN USUARIOS (`/admin/usuarios`)

**Proposito:** CRUD de usuarios do sistema.
**Personas:** P1 (Leandro) exclusivamente.

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                      │
├──────────┬──────────────────────────────────────────────────────────────────┤
│          │ GERENCIAMENTO DE USUARIOS               [+ Novo Usuario]         │
│ SIDEBAR  ├──────────────────────────────────────────────────────────────────┤
│          │                                                                   │
│ Admin    │ ┌──────────────────────────────────────────────────────────────┐ │
│ Usuarios │ │ Nome            │Email                   │Role     │Cons.│Ativo│
│ [ativo]  │ ├─────────────────┼────────────────────────┼─────────┼─────┼─────┤
│          │ │ Leandro Vitao   │leandro@vitao.com.br    │[Admin]  │  —  │[SIM]│
│          │ │ Manu Ditzel     │manu@vitao.com.br       │[Consul.]│MANU │[SIM]│
│          │ │ Larissa Padilha │larissa@vitao.com.br    │[Consul.]│LAR. │[SIM]│
│          │ │ Daiane Stavicki │daiane@vitao.com.br     │[Consul.]│DAIA.│[SIM]│
│          │ │ Julio Gadret    │julio@vitao.com.br      │[Consul.]│JULIO│[SIM]│
│          │ ├─────────────────┴────────────────────────┴─────────┴─────┴─────┤
│          │ │ 5 usuarios cadastrados                   [Editar] [Ativar/Des] │
│          │ └──────────────────────────────────────────────────────────────┘  │
└──────────┴──────────────────────────────────────────────────────────────────┘
```

#### Modal de Usuario (criar/editar)

```
┌──────────────────────────────────────────────────────────────┐
│ NOVO USUARIO / EDITAR USUARIO                          [X]   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Nome completo *                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Manu Ditzel                                          │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Email *                                                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ manu@vitao.com.br                                    │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Role *                                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ [◉] Consultor  [○] Admin  [○] Viewer                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Consultor vinculado (se Role = Consultor)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ MANU                                               ▾ │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Senha temporaria (deixar vazio para manter)                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ ••••••••                                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  Status: [◉] Ativo  [○] Inativo                             │
│                                                              │
│ [Cancelar]                            [Salvar]              │
└──────────────────────────────────────────────────────────────┘
```

**Roles disponiveis:**
| Role | Acesso |
|------|--------|
| admin | Tudo |
| consultor | Agenda propria, Carteira, LOG, RNC, sem Admin |
| viewer | Carteira e Dashboard (sem LOG, sem Admin) |

---

### TELA 12: REDES (`/redes`)

**Proposito:** Sinaleiro especifico por rede/franquia com drill-down de lojas.
**Personas:** P1 (Leandro), P4 (Daiane).

#### Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER                                                                      │
├──────────┬──────────────────────────────────────────────────────────────────┤
│          │ REDES E FRANQUIAS                 2 redes | 130 lojas            │
│ SIDEBAR  ├──────────────────────────────────────────────────────────────────┤
│          │                                                                   │
│ Redes[*] │ ┌───────────────────────────────────────────────────────────────┐│
│          │ │ Rede        │Cons.│Lojas│Fat Real │Meta   │% Ating│Gap  │Cor  ││
│          │ ├─────────────┼─────┼─────┼─────────┼───────┼───────┼─────┼─────┤│
│          │ │ [>] FITLAND │JULIO│  58 │R$129.989│R$621K │ 20.9% │-491K│[VRM]││
│          │ │              ← expande accordion de lojas →                   ││
│          │ │ [>] CIA SAUDE│JULIO│ 72 │R$ 36.465│R$783K │  4.7% │-746K│[VRM]││
│          │ │              ← expande accordion de lojas →                   ││
│          │ └───────────────────────────────────────────────────────────────┘│
│          │                                                                   │
│          │ ACCORDION ABERTO — FITLAND (58 lojas):                           │
│          │ ┌───────────────────────────────────────────────────────────────┐│
│          │ │  CNPJ       │Nome Loja     │Cidade│Fat Real│Meta  │%  │Cor   ││
│          │ │  ──────────────────────────────────────────────────────────── ││
│          │ │  12.345.678/│Fitland SP 01 │SP    │R$8.500 │R$12K │71%│[AM]  ││
│          │ │  12.345.679/│Fitland SP 02 │SP    │R$2.100 │R$12K │18%│[VM]  ││
│          │ │  12.345.680/│Fitland RJ 01 │RJ    │R$9.800 │R$10K │98%│[VE]  ││
│          │ │  12.345.681/│Fitland PR 01 │CWB   │R$0     │R$12K │ 0%│[RX]  ││
│          │ │  ...        │              │      │        │      │   │      ││
│          │ │  Distribuicao: 5[V] 4[A] 35[Vm] 14[Rx]                       ││
│          │ └───────────────────────────────────────────────────────────────┘│
└──────────┴──────────────────────────────────────────────────────────────────┘
```

#### Especificacoes

**Accordion de redes:**
- Click em [>]: expande lista de lojas daquela rede
- Apenas uma rede expandida por vez (fechar ao abrir outra)
- Icone [>] rotaciona 90 ao expandir

**Distribuicao de cores no rodape:**
- "5[V] 4[A] 35[Vm] 14[Rx]" — contadores por cor
- Dots coloridos + numero + sigla

**Click em loja:** redireciona para `/clientes/{cnpj}`

---

## FLUXOS DE NAVEGACAO

### Fluxo Principal — Consultor (Manu/Larissa)

```
LOGIN → /agenda (propria)
  |
  +→ Click "Registrar Atendimento" → Modal Atendimento → Fecha → continua na agenda
  |
  +→ Click no nome do cliente → /clientes/{cnpj}
  |     |
  |     +→ Click "Registrar Atendimento" → Modal Atendimento
  |     +→ Botao Voltar → /agenda (com scroll na posicao anterior)
  |
  +→ Sidebar: /clientes → tabela da carteira propria
  +→ Sidebar: /rnc → criar/ver RNCs
```

### Fluxo Principal — Admin (Leandro)

```
LOGIN → /dashboard
  |
  +→ Click card KPI "47 Follow-ups" → /agenda?prioridade=P0,P1
  +→ Click segmento Donut VERMELHO → /clientes?sinaleiro=VERMELHO
  +→ Click linha tabela Top 10 → /clientes/{cnpj}
  +→ Click performance DAIANE → /clientes?consultor=DAIANE
  |
  +→ Sidebar: /agenda → ver todas as abas (Larissa/Manu/Julio/Daiane)
  +→ Sidebar: /sinaleiro → saude carteira
  +→ Sidebar: /projecao → metas vs realizado
  +→ Sidebar: /redes → fitland/cia saude
  +→ Sidebar: /rnc → todos os problemas
  +→ Sidebar: /admin/motor → ver 92 regras
  +→ Sidebar: /admin/usuarios → CRUD usuarios
```

### Fluxo de Atendimento (40-60x por dia)

```
Agenda (lista) → Card #N → Click "Registrar Atendimento"
  → Modal abre (< 1s)
  → Seleciona RESULTADO (dropdown, 14 opcoes)
  → Escreve DESCRICAO (textarea)
  → Seleciona TIPO CONTATO (radio)
  → Click "Salvar Atendimento"
  → Spinner 1-2s (Motor processa)
  → Exibe outputs do Motor (feedback)
  → Click "Fechar e continuar"
  → Card marcado como [CONCLUIDO]
  → Proximo card esta pronto para acao
Total tempo: 30-60 segundos por atendimento
```

---

## ESTADOS DE UI

### Estado Loading

```
Skeleton:
  width: variavel (80-240px dependendo do elemento)
  height: correspondente ao conteudo
  background: linear-gradient(90deg, #F3F4F6, #E5E7EB, #F3F4F6)
  animation: pulse 1.5s ease-in-out infinite
  border-radius: 4px (texto), 50% (avatares), 8px (cards)

Spinner (botoes, operacoes curtas):
  16px circulo borda, cor branca ou #00B050
  animation: spin 1s linear infinite
  posicionado no centro do botao
```

### Estado Vazio

```
Container: centralizado, padding 48px
Icone: SVG 48px, cor #D1D5DB
Titulo: Arial 14px 600 #374151 — ex: "Nenhum cliente encontrado"
Subtitulo: Arial 12px #9CA3AF — ex: "Tente remover os filtros aplicados"
Botao (opcional): "Limpar filtros" ou "Adicionar primeiro"
```

### Estado de Erro

```
Faixa de erro (no topo da secao):
  background: #FEF2F2
  border: 1px solid #FECACA
  border-radius: 6px
  padding: 12px 16px
  icone: alerta vermelho 16px
  texto: Arial 12px #B91C1C
  botao: "Tentar novamente" (link)

Erro de formulario (por campo):
  border: 1px solid #DC2626
  texto de erro: Arial 9px #DC2626 abaixo do campo
```

### Estado de Sucesso

```
Toast (canto superior direito):
  background: #F0FDF4
  border: 1px solid #BBF7D0
  border-radius: 6px
  padding: 12px 16px
  icone: check verde 16px
  texto: Arial 12px #14532D
  duracao: 3 segundos, depois desaparece (slide-up)
  posicao: fixed top-4 right-4 z-50
```

---

## RESPONSIVIDADE

### Breakpoints

```
sm: 640px   — mobile largo
md: 768px   — tablet
lg: 1024px  — tablet/desktop pequeno (sidebar ativa)
xl: 1280px  — desktop padrao
2xl: 1536px — desktop grande
```

### Desktop (>= 1024px) — Viewport primario

- Sidebar fixa (224px)
- Grid 12 colunas para layout de cards
- Tabelas com todas as colunas visiveis
- KPI Cards: 6 colunas em uma linha
- Modal: max-width 560px centralizado

### Tablet (768px - 1023px)

- Sidebar: drawer mobile (hamburger)
- KPI Cards: grid 3 colunas (2 linhas de 3)
- Tabelas: scroll horizontal para colunas extras
- Modal: max-width 95vw

### Mobile (< 768px)

- Sidebar: drawer mobile com overlay
- KPI Cards: grid 2 colunas (3 linhas de 2)
- Tabelas: colunas reduzidas (esconder Fat., Fase, ABC)
- Agenda: cards empilhados, botao Registrar em full-width
- Modal: 100vw, border-radius no topo apenas (bottom-sheet style)
- Botoes: min-height 44px (touch target)

---

## NAVEGACAO GLOBAL (SIDEBAR)

```
Items para todos os roles:
  [ico] Dashboard       /
  [ico] Agenda          /agenda
  [ico] Carteira        /clientes
  [ico] RNC             /rnc

Items para admin e gestor (Leandro, Daiane):
  [ico] Sinaleiro       /sinaleiro
  [ico] Projecao        /projecao
  [ico] Redes           /redes

Items exclusivos admin (Leandro):
  ─ ADMINISTRACAO ─────
  [ico] Motor de Regras /admin/motor
  [ico] Usuarios        /admin/usuarios
```

Restricoes por role (aplicadas no RouteGuard):

| Rota | admin | consultor | viewer |
|------|-------|-----------|--------|
| /dashboard | SIM | NÃO (redir /agenda) | SIM |
| /agenda | SIM (todas abas) | SIM (so a propria) | NÃO |
| /clientes | SIM | SIM | SIM |
| /clientes/{cnpj} | SIM | SIM (financeiro oculto P5) | SIM |
| /sinaleiro | SIM | DAIANE only | NÃO |
| /projecao | SIM | NÃO | NÃO |
| /redes | SIM | DAIANE only | NÃO |
| /rnc | SIM | SIM | NÃO |
| /admin/* | SIM | NÃO | NÃO |

---

## REGRAS DE NEGOCIO NA UI

### Two-Base Architecture na Interface

```
PROIBIDO em qualquer formulario de LOG (atendimento):
  - Campo "Valor" ou "R$"
  - Qualquer input numerico monetario
  - A nota "R$ 0,00" deve aparecer no footer do modal

PERMITIDO apenas na Carteira/Projecao/Sinaleiro:
  - Faturamento R$
  - Meta R$
  - Gap R$
  - Ticket Medio R$
```

### Permissao de Visualizacao Financeira

```
P5 (Julio) — ocultar:
  - Coluna "Faturamento" na Carteira
  - Bloco "FINANCEIRO" no Detalhe do Cliente
  - Aba "Projecao"
  - Dados de meta na Carteira

Implementacao: CSS display:none (nao basta nao renderizar — dados nao chegam da API)
```

### CNPJ

```
Exibicao SEMPRE formatada: XX.XXX.XXX/XXXX-XX
Font: monospace para alinhar colunas
Funcao formatCnpj(cnpj: string): string
  const d = cnpj.replace(/\D/g,'').padStart(14,'0')
  return `${d.slice(0,2)}.${d.slice(2,5)}.${d.slice(5,8)}/${d.slice(8,12)}-${d.slice(12)}`
```

### Score

```
Exibicao: numero inteiro de 0 a 100 (arredondar: Math.round)
Nunca explicar os 6 fatores ponderados na tela do consultor
Apenas no Detalhe do Cliente (bloco STATUS): breakdown por fator
ScoreBar: cor por range (>=70 verde, >=40 amarelo, <40 vermelho)
```

---

## GUIA DE IMPLEMENTACAO — NEXT.JS + TAILWIND

### Estrutura de Componentes

```
src/
  components/
    ui/
      StatusBadge.tsx        ← DS-04-A (ja existe, manter)
      SinaleiroDot.tsx       ← DS-04-B (novo)
      KpiCard.tsx            ← DS-04-C (ja existe parcial)
      ScoreBar.tsx           ← DS-04-D (ja existe na agenda)
      AgendaCard.tsx         ← DS-04-E (novo — componentizar)
      Modal.tsx              ← DS-04-F (novo — base modal)
      DataTable.tsx          ← DS-04-G (novo — tabela generica)
      FilterBar.tsx          ← DS-04-H (novo)
      TimelineEntry.tsx      ← DS-04-I (novo)
      ProgressMeta.tsx       ← DS-04-J (novo)
      DonutChart.tsx         ← DS-04-K (novo — SVG puro ou recharts)
    layout/
      AppShell.tsx           ← (ja existe)
      Sidebar.tsx            ← (ja existe)
    forms/
      AtendimentoModal.tsx   ← modal de registro
      RncModal.tsx           ← modal de RNC
      UsuarioModal.tsx       ← modal de usuario
  app/
    (auth)/
      login/
        page.tsx
    (protected)/
      layout.tsx             ← RouteGuard + AppShell
      page.tsx               ← Dashboard
      agenda/
        page.tsx
      clientes/
        page.tsx
        [cnpj]/
          page.tsx
      sinaleiro/
        page.tsx
      projecao/
        page.tsx
      redes/
        page.tsx
      rnc/
        page.tsx
      admin/
        motor/
          page.tsx
        usuarios/
          page.tsx
```

### CSS Variables (globals.css)

```css
:root {
  /* Status */
  --c-ativo:     #00B050;
  --c-inatrec:   #FFC000;
  --c-inatant:   #FF0000;
  --c-roxo:      #7030A0;
  --c-prospect:  #808080;

  /* Brand */
  --c-brand:     #00B050;
  --c-brand-dk:  #007A38;

  /* Base */
  --c-bg:        #FFFFFF;
  --c-surface:   #F9FAFB;
  --c-border:    #E5E7EB;
  --c-border-dk: #D1D5DB;

  /* Text */
  --c-text-1:    #111827;
  --c-text-2:    #374151;
  --c-text-3:    #6B7280;
  --c-text-4:    #9CA3AF;
}
```

### Tailwind Extensions (tailwind.config.ts)

```ts
extend: {
  colors: {
    brand: '#00B050',
    'brand-dk': '#007A38',
    ativo: '#00B050',
    'inat-rec': '#FFC000',
    'inat-ant': '#FF0000',
    sinaleiro: {
      verde: '#00B050',
      amarelo: '#FFC000',
      vermelho: '#FF0000',
      roxo: '#7030A0',
    },
  },
  fontFamily: {
    sans: ['Arial', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
  },
}
```

---

## CHECKLIST DE QUALIDADE

Antes de marcar qualquer tela como "done", verificar:

### Visual
- [ ] Fundo sempre branco (#FFFFFF) ou cinza claro (#F9FAFB) — nunca escuro
- [ ] Todas as cores de status batem com a paleta DS-01
- [ ] Fonte Arial em todos os elementos
- [ ] Badges: uppercase, bold, border-radius 3px
- [ ] KPI Cards: accent bar no topo, valor 24px bold
- [ ] ScoreBar com cor dinamica por range

### Funcional
- [ ] Modal de atendimento: SEM campo de valor R$
- [ ] CNPJ sempre formatado XX.XXX.XXX/XXXX-XX
- [ ] Score exibido como inteiro (0-100)
- [ ] Filtros da carteira persistem na URL
- [ ] RouteGuard bloqueando rotas por role
- [ ] P5 (Julio) sem colunas/blocos financeiros

### Estados
- [ ] Loading: skeleton animado (nao spinner em tabelas grandes)
- [ ] Empty: icone + mensagem descritiva
- [ ] Error: faixa vermelha com mensagem + botao retry

### Acessibilidade
- [ ] Todos os badges com aria-label descritivo
- [ ] Tabelas com <th scope="col">
- [ ] Modais com role="dialog" aria-modal="true"
- [ ] Focus ring visivel (2px solid #00B050)
- [ ] Botoes com minimo 44x44px (touch)

### Responsividade
- [ ] Desktop (1280px): layout completo
- [ ] Tablet (768px): sidebar drawer, grid adaptado
- [ ] Mobile (375px): cards empilhados, colunas reduzidas

---

*Documento criado pelo @ux em 25/03/2026.*
*Fonte de verdade para o frontend — Next.js 14 + Tailwind CSS.*
*Versao 2.0 — substitui versao 1.0 anterior.*
