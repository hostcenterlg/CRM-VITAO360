# UX SPEC SAAS — CRM VITAO360
# Especificacao de Interface e Design System
# Versao: 1.0 — 2026-03-25
# Status: DEFINITIVO

---

## PRINCIPIOS FUNDAMENTAIS

- Tema: LIGHT EXCLUSIVAMENTE — nunca dark mode, nunca modo noturno
- Fonte: Arial em todo o sistema (dados: 9pt, headers: 10pt, titulos: 12pt)
- Densidade: alta — maximo de informacao por tela sem poluicao visual
- Hierarquia: Leandro (admin total) > Manu/Larissa/Daiane (consultoras) > Julio (sem acesso)
- Viewport primario: desktop 1920px (gestoras usam notebook); secundario: tablet 768px; terciario: mobile 375px

---

## 1. MAPA DE TELAS

### 10 Paginas do Sistema

| # | Rota | Nome | Acesso | Descricao |
|---|------|------|--------|-----------|
| 1 | `/` | Dashboard | Todos | KPIs globais, distribuicoes, top 10 |
| 2 | `/carteira` | Carteira | Todos | Lista completa de clientes com filtros |
| 3 | `/agenda` | Agenda | Todos | Agenda comercial — montar, distribuir, executar |
| 4 | `/log` | LOG | Todos | Registro de atendimentos (Two-Base: R$ 0,00) |
| 5 | `/projecao` | Projecao | Leandro | Cenarios financeiros e metas |
| 6 | `/sinaleiro` | Sinaleiro Redes | Leandro | Painel de redes (923 lojas, 8 redes) |
| 7 | `/clientes/:cnpj` | Cliente Detalhe | Todos | Ficha completa + historico + agenda |
| 8 | `/import` | Importacao | Leandro | Upload de xlsx Mercos/SAP |
| 9 | `/config` | Configuracoes | Leandro | Parametros do sistema |
| 10 | `/login` | Login | Publico | Autenticacao de usuario |

### Hierarquia de Navegacao

```
/login
  |
  +-- / (Dashboard)
  |
  +-- /carteira
  |     +-- /clientes/:cnpj (Cliente Detalhe)
  |
  +-- /agenda
  |     +-- /agenda/:id (Detalhe da Agenda)
  |
  +-- /log
  |
  +-- /projecao [Leandro]
  |
  +-- /sinaleiro [Leandro]
  |
  +-- /import [Leandro]
  |
  +-- /config [Leandro]
```

---

## 2. WIREFRAMES ASCII

### 2.1 DASHBOARD

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [V] CRM VITAO360          Dashboard                    [Leandro ▾]  [Sair]  │
├──────────┬─────────────────────────────────────────────────────────────────┤
│          │  DASHBOARD — Visao Geral da Carteira                            │
│ [V]      ├─────────────────────────────────────────────────────────────────┤
│ VITAO360 │                                                                  │
│          │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────┐ │
│ -- Nav --│  │ CLIENTES     │ │ ATIVOS       │ │ FATURAMENTO  │ │ SCORE  │ │
│          │  │     489      │ │     312      │ │ R$ 2.091.000 │ │  6,2   │ │
│ Dashboard│  │ 0 prospects  │ │ 177 inativos │ │ Baseline 25  │ │ 8 crit │ │
│ [ativo]  │  └──────────────┘ └──────────────┘ └──────────────┘ └────────┘ │
│          │                                                                  │
│ Carteira │  ┌──────────────────────────────┐ ┌──────────────────────────┐  │
│          │  │ Distribuicao por Situacao    │ │ Distribuicao por Sinalei │  │
│ Agenda   │  │                              │ │                          │  │
│          │  │ ATIVO     ████████████  64%  │ │ VERDE  ██████████   41%  │  │
│ LOG      │  │ INAT.REC  ████          18%  │ │ AMAREL ████         22%  │  │
│          │  │ INAT.ANT  ██             8%  │ │ VERM   ███          19%  │  │
│ Projecao │  │ PROSPECT  ████          10%  │ │ ROXO   ██           18%  │  │
│          │  └──────────────────────────────┘ └──────────────────────────┘  │
│ Sinaleiro│                                                                  │
│          │  ┌──────────────────────────────┐ ┌──────────────────────────┐  │
│ Import   │  │ Distribuicao por Consultor   │ │ Distribuicao por Prio    │  │
│          │  │                              │ │                          │  │
│ Config   │  │ LARISSA   ████████████  45%  │ │ P0  ██                6% │  │
│          │  │ MANU      ████████      32%  │ │ P1  ████             14% │  │
│          │  │ DAIANE    ████          15%  │ │ P2  ██████           21% │  │
│          │  │ LEGADO    ███            8%  │ │ P3  ████████         28% │  │
│          │  └──────────────────────────────┘ └──────────────────────────┘  │
│          │                                                                  │
│ v1.0     │  TOP 10 CLIENTES POR FATURAMENTO                                │
│ 2026     │  ┌────┬──────────────────┬──────────┬───────────┬─────┬──┬────┐ │
│          │  │ # │ Cliente          │ Consultor│ Faturamento│Scor│ABC│Sinal│ │
│          │  ├────┼──────────────────┼──────────┼───────────┼─────┼──┼────┤ │
│          │  │  1 │ Supermercado X  │ LARISSA  │ R$180.000 │ 8.2 │[A]│[V]│ │
│          │  │  2 │ Rede Sul Ltda   │ MANU     │ R$145.000 │ 7.5 │[A]│[V]│ │
│          │  │  3 │ Natural Shop    │ LARISSA  │ R$98.000  │ 6.8 │[A]│[Am]│ │
│          │  │ ...│ ...             │ ...      │ ...       │ ... │...│...│ │
│          │  └────┴──────────────────┴──────────┴───────────┴─────┴──┴────┘ │
└──────────┴─────────────────────────────────────────────────────────────────┘
```

Elementos de estado:
- Loading: skeleton bars animados (pulse cinza)
- Erro: faixa vermelha com mensagem descritiva
- Vazio: mensagem "Sem dados disponíveis" centralizada

---

### 2.2 CARTEIRA

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [V] CRM VITAO360          Carteira                     [Leandro ▾]  [Sair]  │
├──────────┬─────────────────────────────────────────────────────────────────┤
│          │  CARTEIRA — 489 Clientes                    [+ Novo] [Exportar]  │
│ SIDEBAR  ├─────────────────────────────────────────────────────────────────┤
│          │                                                                  │
│ Dashboard│  FILTROS                                                         │
│          │  ┌──────────────────────────────────────────────────────────┐   │
│ Carteira │  │ [Busca: Nome, CNPJ, Cidade...]  [Consultor ▾] [ABC ▾]   │   │
│ [ativo]  │  │ [Situacao ▾] [Sinaleiro ▾]  [Prioridade ▾]  [Limpar]   │   │
│          │  └──────────────────────────────────────────────────────────┘   │
│ Agenda   │                                                                  │
│          │  ┌──────────────────────────────────────────────────────────┐   │
│ LOG      │  │ CNPJ         │Nome Fantasia    │Cid │Consul│Fat    │Sc│ABC│Sin│ │
│          │  ├──────────────┼─────────────────┼────┼──────┼───────┼──┼───┼──┤ │
│ ...      │  │ 00.000.000/  │ Supermercado X  │POA │LARISSAR$180K │8.2│[A]│[V]│ │
│          │  │ 00.001.000/  │ Rede Sul Ltda   │FLN │MANU  │R$145K│7.5│[A]│[V]│ │
│          │  │ 00.002.000/  │ Natural Shop    │CWB │LARISSAR$98K  │6.8│[A]│[Y]│ │
│          │  │ 00.003.000/  │ Grao Natural    │POA │DAIANE│R$72K │5.2│[B]│[R]│ │
│          │  │ 00.004.000/  │ Verde Vida      │GRU │MANU  │R$45K │4.1│[C]│[P]│ │
│          │  │              │ ...             │    │      │       │  │   │  │ │
│          │  ├──────────────┴─────────────────┴────┴──────┴───────┴──┴───┴──┤ │
│          │  │  Mostrando 1-50 de 489    [< Ant]  Pag 1/10  [Prox >]       │ │
│          │  └──────────────────────────────────────────────────────────────┘ │
│          │                                                                  │
│          │  Clique em qualquer linha para abrir ficha completa do cliente   │
└──────────┴─────────────────────────────────────────────────────────────────┘
```

Comportamentos:
- Clique na linha: abre `/clientes/:cnpj` (ficha completa)
- Hover na linha: highlight cinza claro `#F9FAFB`
- Ordenacao por cabecalho de coluna (icone seta)
- Filtros persistem no URL (permite compartilhar link filtrado)
- Exportar: gera xlsx com a selecao atual

---

### 2.3 AGENDA

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [V] CRM VITAO360          Agenda                       [Leandro ▾]  [Sair]  │
├──────────┬─────────────────────────────────────────────────────────────────┤
│          │  AGENDA COMERCIAL          [Nova Agenda]  [Distribuir] [Exportar]│
│ SIDEBAR  ├─────────────────────────────────────────────────────────────────┤
│          │                                                                  │
│ ...      │  ABAS: [Pendentes (12)] [Em Execucao (3)] [Concluidas (87)]     │
│          │                                                                  │
│ Agenda   │  Semana: [< Mar 18] Mar 25 2026 [Mar 31 >]  [Consultor: Todos ▾]│
│ [ativo]  │                                                                  │
│          │  ┌────────────────────────────────────────────────────────────┐  │
│ ...      │  │ LARISSA PADILHA                         42 clientes — R$0  │  │
│          │  │ ┌────────────────────────────────────────────────────────┐ │  │
│          │  │ │[P0] Supermercado X    POA   R$180K  A  [ROXO]  [Lig]  │ │  │
│          │  │ │[P1] Rede Sul SC       FLN   R$145K  A  [VERD]  [Wpp]  │ │  │
│          │  │ │[P2] Natural Shop      CWB   R$98K   A  [AMAR]  [Vis]  │ │  │
│          │  │ └────────────────────────────────────────────────────────┘ │  │
│          │  └────────────────────────────────────────────────────────────┘  │
│          │                                                                  │
│          │  ┌────────────────────────────────────────────────────────────┐  │
│          │  │ MANU DITZEL                             38 clientes — R$0  │  │
│          │  │ ┌────────────────────────────────────────────────────────┐ │  │
│          │  │ │[P0] Atacado Central   FLN   R$120K  A  [ROXO]  [Lig]  │ │  │
│          │  │ │[P2] BioBom Ltda       POA   R$85K   B  [VERM]  [Vis]  │ │  │
│          │  │ └────────────────────────────────────────────────────────┘ │  │
│          │  └────────────────────────────────────────────────────────────┘  │
│          │                                                                  │
│          │  ┌────────────────────────────────────────────────────────────┐  │
│          │  │ DAIANE STAVICKI                         18 clientes — R$0  │  │
│          │  │ [Redes e Key Accounts — ver /sinaleiro]                    │  │
│          │  └────────────────────────────────────────────────────────────┘  │
└──────────┴─────────────────────────────────────────────────────────────────┘
```

Fluxo Leandro (gestor):
1. Cria agenda via "Nova Agenda" — seleciona clientes por filtro (prio, sinaleiro, consultor)
2. Clica "Distribuir" — sistema aloca automaticamente por consultor
3. Consultoras recebem notificacao (badge no nav) com lista de clientes

Fluxo consultora:
1. Ve sua fila em "Pendentes"
2. Abre card do cliente → registra atendimento
3. Card move para "Em Execucao" → "Concluidas"

---

### 2.4 ATENDIMENTO (Registro de LOG)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [V] CRM VITAO360     Registrar Atendimento          [Larissa ▾]  [Sair]    │
├──────────┬─────────────────────────────────────────────────────────────────┤
│          │  ATENDIMENTO — Supermercado X                                    │
│ SIDEBAR  │  CNPJ: 00.000.000/0001-00   ATIVO   [A]   [VERDE]   Score: 8.2  │
│          ├─────────────────────────────────────────────────────────────────┤
│          │                                                                  │
│ ...      │  ┌────────────────────────────────────────────────────────────┐  │
│          │  │ TIPO DE CONTATO                                            │  │
│          │  │  ( ) Ligacao   ( ) WhatsApp   ( ) Visita   ( ) Email      │  │
│          │  └────────────────────────────────────────────────────────────┘  │
│          │                                                                  │
│          │  ┌────────────────────────────────────────────────────────────┐  │
│          │  │ DATA/HORA         DURACAO          RESPONSAVEL             │  │
│          │  │ [25/03/2026 ...]  [00:15 ...]      [LARISSA     ]          │  │
│          │  └────────────────────────────────────────────────────────────┘  │
│          │                                                                  │
│          │  ┌────────────────────────────────────────────────────────────┐  │
│          │  │ RESULTADO DO CONTATO                                       │  │
│          │  │  ( ) Pedido realizado   ( ) Retornar   ( ) Sem sucesso     │  │
│          │  │  ( ) Reagendar          ( ) Cancelado                      │  │
│          │  └────────────────────────────────────────────────────────────┘  │
│          │                                                                  │
│          │  ┌────────────────────────────────────────────────────────────┐  │
│          │  │ OBSERVACOES (opcional)                                     │  │
│          │  │ ┌──────────────────────────────────────────────────────┐  │  │
│          │  │ │ Comentarios sobre o atendimento...                   │  │  │
│          │  │ │                                                      │  │  │
│          │  │ └──────────────────────────────────────────────────────┘  │  │
│          │  └────────────────────────────────────────────────────────────┘  │
│          │                                                                  │
│          │  AVISO: Valor R$ = R$ 0,00 automaticamente (Two-Base LOG)        │
│          │                                                                  │
│          │  [Cancelar]                            [Salvar Atendimento]      │
└──────────┴─────────────────────────────────────────────────────────────────┘
```

Regras de negocio no form:
- Campo valor NUNCA aparece no formulario de LOG (Two-Base Architecture)
- Data/hora pre-preenchida com horario atual
- Responsavel pre-preenchido com usuario logado
- Validacao obrigatoria: tipo de contato + resultado

---

### 2.5 SINALEIRO REDES

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [V] CRM VITAO360     Sinaleiro de Redes             [Leandro ▾]  [Sair]    │
├──────────┬─────────────────────────────────────────────────────────────────┤
│          │  SINALEIRO REDES — 8 Redes / 923 Lojas              [Exportar]  │
│ SIDEBAR  ├─────────────────────────────────────────────────────────────────┤
│          │                                                                  │
│ ...      │  RESUMO                                                          │
│          │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│ Sinaleiro│  │ ROXO     │ │ VERM     │ │ AMAR     │ │ VERDE    │           │
│ [ativo]  │  │ 3 redes  │ │ 2 redes  │ │ 1 rede   │ │ 2 redes  │           │
│          │  │ 280 lojas│ │ 180 lojas│ │ 110 lojas│ │ 353 lojas│           │
│ ...      │  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
│          │                                                                  │
│          │  ┌────────────────────────────────────────────────────────────┐  │
│          │  │ REDE              │ LOJAS │ SINALEIRO │ FAT/LOJA │ ACAO    │  │
│          │  ├───────────────────┼───────┼───────────┼──────────┼─────────┤  │
│          │  │ [>] Rede Alfa     │  245  │ [ROXO]    │ R$2.800  │[Abrir]  │  │
│          │  │ [>] Rede Beta     │  180  │ [VERMELHO]│ R$1.950  │[Abrir]  │  │
│          │  │ [>] Rede Gama     │  135  │ [ROXO]    │ R$3.100  │[Abrir]  │  │
│          │  │ [>] Rede Delta    │  110  │ [AMARELO] │ R$2.200  │[Abrir]  │  │
│          │  │ [>] Rede Epsilon  │   95  │ [VERDE]   │ R$4.500  │[Abrir]  │  │
│          │  │ [>] Rede Zeta     │   80  │ [VERMELHO]│ R$1.200  │[Abrir]  │  │
│          │  │ [>] Rede Eta      │   45  │ [VERDE]   │ R$5.800  │[Abrir]  │  │
│          │  │ [>] Rede Theta    │   33  │ [ROXO]    │ R$2.100  │[Abrir]  │  │
│          │  └────────────────────────────────────────────────────────────┘  │
│          │                                                                  │
│          │  [>] expande linha para ver lojas individuais da rede            │
└──────────┴─────────────────────────────────────────────────────────────────┘
```

Interacoes:
- Clique em [>]: expande accordion com lojas da rede
- Clique em [Abrir]: abre detalhe da rede com todas as lojas e historico
- Cores dos cards de resumo: background com a cor do sinaleiro (opacity 15%)
- Linha da tabela: cor de fundo sutil conforme sinaleiro

---

### 2.6 CLIENTE DETALHE

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ [V] CRM VITAO360     < Voltar à Carteira                [Leandro ▾] [Sair]  │
├──────────┬─────────────────────────────────────────────────────────────────┤
│          │  SUPERMERCADO X LTDA                      [Agendar] [Novo LOG]   │
│ SIDEBAR  │  CNPJ: 00.000.000/0001-00                                        │
│          ├────────────────────────┬────────────────────────────────────────┤
│          │ STATUS                 │ FINANCEIRO                              │
│          │ Situacao: [ATIVO]      │ Faturamento:   R$ 180.000               │
│          │ Sinaleiro: [VERDE]     │ Ticket Medio:  R$ 12.000                │
│          │ ABC: [A]               │ Ultima Compra: 15/03/2026               │
│          │ Score: 8.2 / 10        │ Pedidos 12m:   15                       │
│          │ Prioridade: [P0]       │ LTV estimado:  R$ 540.000               │
│          ├────────────────────────┴────────────────────────────────────────┤
│          │ DADOS CADASTRAIS                                                 │
│          │ Razao Social: Supermercado X Comercio e Distribuicao Ltda       │
│          │ Cidade/UF:    Porto Alegre / RS    Consultor: LARISSA            │
│          │ Segmento:     Supermercado         Rede:      N/A                │
│          │ Tel:          (51) 3000-0000       Email:     contato@supx.com   │
│          ├─────────────────────────────────────────────────────────────────┤
│          │ SCORE BREAKDOWN                                                  │
│          │ Frequencia:   ████████████████████ 9.5                          │
│          │ Ticket:       ████████████████░░░░ 8.0                          │
│          │ Recencia:     ████████████████████ 9.0                          │
│          │ Mix Produtos: ██████████████░░░░░░ 7.2                          │
│          │ Estab. Parc.: ████████████████████ 9.5                          │
│          ├─────────────────────────────────────────────────────────────────┤
│          │ HISTORICO DE ATENDIMENTOS                                       │
│          │                                                                 │
│          │  25/03 [Lig] LARISSA — Pedido realizado — "Confirmou 50cx..."   │
│          │  18/03 [Wpp] LARISSA — Retornar — "Aguardando aprovacao..."     │
│          │  10/03 [Vis] LARISSA — Pedido realizado — "Visita presencial..." │
│          │  01/03 [Lig] LARISSA — Sem sucesso — "Nao atendeu"              │
│          │  [Carregar mais...]                                              │
│          ├─────────────────────────────────────────────────────────────────┤
│          │ AGENDA ATIVA                                                    │
│          │ Proxima acao: 28/03/2026 — Visita programada — LARISSA          │
└──────────┴─────────────────────────────────────────────────────────────────┘
```

---

## 3. COMPONENTES — DESIGN SYSTEM

### 3.1 DataTable

Componente de tabela padrao do sistema.

| Propriedade | Valor |
|-------------|-------|
| Fonte celulas | Arial 9pt, `#374151` |
| Fonte cabecalho | Arial 10pt bold, `#6B7280`, uppercase |
| Altura linha | 36px (desktop), 44px (tablet/touch) |
| Hover linha | background `#F9FAFB` |
| Borda | `1px solid #E5E7EB` entre linhas |
| Header bg | `#F9FAFB` |
| Sombra container | `0 1px 3px rgba(0,0,0,0.08)` |
| Border radius | 8px |
| Padding celula | `12px 16px` |
| Ordenacao | Seta up/down no cabecalho, ativo em azul `#2563EB` |

Variantes:
- `default` — exibicao normal com hover
- `compact` — altura 28px, fonte 8pt (para telas densas)
- `striped` — linhas alternadas `#FFFFFF` / `#F9FAFB`
- `selectable` — checkbox na primeira coluna para acoes em lote
- `loading` — skeleton rows animados (pulse)
- `empty` — estado vazio com icone e mensagem centrada

Estados especiais de linha:
- Critico (sinaleiro ROXO): borda esquerda `3px solid #800080`
- Alerta (sinaleiro VERMELHO): borda esquerda `3px solid #FF0000`

---

### 3.2 KpiCard

Card de metrica principal.

| Propriedade | Valor |
|-------------|-------|
| Tamanho | 200px x 100px min (responsivo) |
| Background | `#FFFFFF` |
| Borda | `1px solid #E5E7EB` |
| Border radius | 8px |
| Sombra | `0 1px 3px rgba(0,0,0,0.08)` |
| Accent bar | `4px solid {accentColor}` no topo |
| Titulo | Arial 10pt, `#6B7280` |
| Valor | Arial 24pt bold, `#111827` |
| Subtitulo | Arial 9pt, `#9CA3AF` |
| Padding | `16px` |

Variantes de accentColor:
- Total Clientes: `#2563EB` (azul)
- Ativos: `#00B050` (verde VITAO)
- Faturamento: `#7C3AED` (roxo premium)
- Score/Criticos: `#DC2626` (vermelho alerta)
- Inativos: `#F59E0B` (amber)

Estado loading:
- Titulo: skeleton `80px x 10px`
- Valor: skeleton `140px x 24px`
- Subtitulo: skeleton `100px x 8px`
- Animacao: `pulse 1.5s ease-in-out infinite`

---

### 3.3 StatusBadge

Badge colorido para status, sinaleiro, prioridade e ABC.

| Variante | Valores | Cores BG/Text |
|----------|---------|---------------|
| `situacao` | ATIVO | `#00B050` / `#FFFFFF` |
| `situacao` | INAT.REC | `#FFC000` / `#1A1A1A` |
| `situacao` | INAT.ANT | `#FF0000` / `#FFFFFF` |
| `situacao` | PROSPECT | `#808080` / `#FFFFFF` |
| `sinaleiro` | VERDE | `#00B050` / `#FFFFFF` |
| `sinaleiro` | AMARELO | `#FFC000` / `#1A1A1A` |
| `sinaleiro` | VERMELHO | `#FF0000` / `#FFFFFF` |
| `sinaleiro` | ROXO | `#800080` / `#FFFFFF` |
| `prioridade` | P0 | `#FF0000` / `#FFFFFF` |
| `prioridade` | P1 | `#FF6600` / `#FFFFFF` |
| `prioridade` | P2 | `#FFC000` / `#1A1A1A` |
| `prioridade` | P3 | `#FFFF00` / `#1A1A1A` |
| `prioridade` | P4 | `#9CA3AF` / `#FFFFFF` |
| `prioridade` | P5 | `#D1D5DB` / `#374151` |
| `prioridade` | P6 | `#E5E7EB` / `#6B7280` |
| `prioridade` | P7 | `#F3F4F6` / `#9CA3AF` |
| `abc` | A | `#00B050` / `#FFFFFF` |
| `abc` | B | `#FFFF00` / `#1A1A1A` |
| `abc` | C | `#FFC000` / `#1A1A1A` |
| `abc` | D | `#9CA3AF` / `#FFFFFF` |

Tamanhos:
- `default`: `px-2 py-0.5 text-xs` (12pt)
- `small`: `px-1.5 py-0 text-[10px]`
- `large`: `px-3 py-1 text-sm` (tabelas de destaque)

Typography: Arial bold, uppercase, letter-spacing 0.05em
Border-radius: 4px (badge quadrado)

---

### 3.4 AbcBadge

Extensao do StatusBadge com icone opcional.

Igual ao StatusBadge variante `abc`, com adicional:
- Pode exibir icone de estrela em badges "A"
- Tooltip ao hover: "Curva ABC: {descricao do tier}"

---

### 3.5 SinaleiroBadge

Extensao do StatusBadge com icone de circulo colorido.

| Sinaleiro | Icone | Significado |
|-----------|-------|-------------|
| ROXO | Circulo roxo preenchido | Critico — acao imediata |
| VERMELHO | Circulo vermelho preenchido | Em risco — intervencao urgente |
| AMARELO | Circulo amarelo preenchido | Atencao — monitorar |
| VERDE | Circulo verde preenchido | Saudavel — manutencao |

Variacao de exibicao:
- `badge` (padrao): texto + background colorido (igual StatusBadge)
- `dot`: apenas circulo 8px sem texto (para colunas compactas)
- `dot-label`: circulo 8px + texto ao lado, sem background

---

### 3.6 ScoreBar

Barra de progresso para visualizacao de score (0-10).

```
Frequencia:  ████████████████░░░░  8.2 / 10
```

| Propriedade | Valor |
|-------------|-------|
| Altura | 8px |
| Border radius | 4px |
| Background vazio | `#E5E7EB` |
| Cor da barra por range | |
| 8.0 - 10.0 | `#00B050` (verde) |
| 6.0 - 7.9 | `#FFC000` (amarelo) |
| 4.0 - 5.9 | `#FF6600` (laranja) |
| 0.0 - 3.9 | `#FF0000` (vermelho) |
| Label esquerda | Arial 9pt, `#6B7280`, 100px fixo |
| Valor direita | Arial 9pt bold, `#374151` |
| Transicao | `width 500ms ease-out` |

Uso principal: tela de detalhe do cliente (score breakdown por dimensao)

---

### 3.7 AgendaCard

Card de item na lista de agenda.

```
┌────────────────────────────────────────────────────────┐
│ [P0]  Supermercado X Ltda              [ROXO]          │
│       Porto Alegre / RS                R$ 180.000      │
│       Curva [A] — Score 8.2            [Lig] [Wpp] [V]│
└────────────────────────────────────────────────────────┘
```

| Propriedade | Valor |
|-------------|-------|
| Background | `#FFFFFF` |
| Borda | `1px solid #E5E7EB` |
| Borda esquerda | `4px solid {cor da prioridade}` |
| Border radius | 6px |
| Padding | `12px 16px` |
| Sombra hover | `0 2px 8px rgba(0,0,0,0.12)` |
| Cursor | `pointer` |
| Transicao hover | `box-shadow 150ms ease, transform 150ms ease` |
| Transform hover | `translateY(-1px)` |

Estados:
- `pending`: borda esquerda prioridade, badge [PENDENTE] cinza
- `in-progress`: borda esquerda prioridade, badge [EM EXECUCAO] azul
- `done`: background `#F9FAFB`, opacidade 70%, badge [CONCLUIDO] verde
- `overdue`: borda `1px solid #FF0000`, badge [ATRASADO] vermelho

Botoes de acao rapida (aparecem no hover):
- [Lig]: telefone — abre telefonia VoIP ou discador
- [Wpp]: WhatsApp — abre chat Deskrio
- [Vis]: visita — abre formulario de agendamento

---

### 3.8 TimelineEntry

Entrada no historico de atendimentos.

```
25/03 |  [Lig]  LARISSA   Pedido realizado
      |         "Confirmou pedido de 50cx caldo natural..."
      |
18/03 |  [Wpp]  LARISSA   Retornar
      |         "Aguardando aprovacao do gerente para pedido"
```

| Propriedade | Valor |
|-------------|-------|
| Linha vertical | `2px solid #E5E7EB` |
| Data | Arial 9pt bold, `#9CA3AF`, 40px fixo |
| Icone tipo | 20px x 20px, cores por tipo (ver abaixo) |
| Nome responsavel | Arial 9pt bold, `#374151` |
| Resultado | Arial 9pt, badge colorido |
| Observacao | Arial 9pt italic, `#6B7280`, truncada em 2 linhas |

Cores por tipo de contato:
- Ligacao: `#2563EB` (azul)
- WhatsApp: `#00A651` (verde WA)
- Visita: `#7C3AED` (roxo)
- Email: `#F59E0B` (amber)

---

### 3.9 FilterBar

Barra de filtros combinados.

| Elemento | Spec |
|----------|------|
| Container | `bg-white border border-gray-200 rounded-lg p-3` |
| Input de busca | `width: 280px`, placeholder cinza, icone lupa |
| Dropdowns | `height: 32px`, Arial 9pt, borda `#D1D5DB` |
| Botao Limpar | Link texto `#6B7280`, sem borda |
| Botao Aplicar | Background `#00B050`, texto branco, border-radius 4px |
| Gap entre elementos | `8px` |

Dropdowns disponiveis:
- Consultor: [Todos, MANU, LARISSA, DAIANE]
- Situacao: [Todos, ATIVO, INAT.REC, INAT.ANT, PROSPECT]
- Sinaleiro: [Todos, VERDE, AMARELO, VERMELHO, ROXO]
- ABC: [Todos, A, B, C, D]
- Prioridade: [Todos, P0, P1, P2, P3, P4+]
- UF: multiselect com estados brasileiros

Comportamento:
- Filtros ativos exibem badge com contador no dropdown
- "Limpar" reseta TODOS os filtros simultaneamente
- Filtros persistem no URL (query string)
- Aplicar em tempo real (debounce 300ms) — sem botao submit

---

### 3.10 AtendimentoForm

Formulario de registro de atendimento (LOG).

| Campo | Tipo | Obrigatorio | Validacao |
|-------|------|-------------|-----------|
| Tipo de Contato | Radio (4 opcoes) | Sim | Um deve estar selecionado |
| Data/Hora | DateTime | Sim | Nao pode ser futura |
| Duracao | Time input (MM:SS) | Nao | Maximo 4h |
| Responsavel | Readonly (usuario logado) | Auto | N/A |
| Resultado | Radio (5 opcoes) | Sim | Um deve estar selecionado |
| Observacoes | Textarea | Nao | Max 500 caracteres |
| Valor R$ | AUSENTE — nunca exibir | N/A | Two-Base Architecture |

Resultados disponiveis:
- Pedido realizado (verde)
- Retornar (azul)
- Sem sucesso (cinza)
- Reagendar (amarelo)
- Cancelado (vermelho)

Submit: `POST /api/log` com `valor_rs: 0.00` hardcoded no backend.

---

## 4. FLUXOS DE USUARIO

### 4.1 LEANDRO — Montar e Distribuir Agenda

```
Leandro acessa /agenda
       |
       v
[Nova Agenda] → Modal de configuracao
       |
       +-- Define periodo (semana/quinzena/mes)
       +-- Define criterios de selecao:
       |     - Prioridade: [P0] [P1] [P2] (multipla selecao)
       |     - Sinaleiro: [ROXO] [VERMELHO] (multipla selecao)
       |     - Consultor: [Todos] ou especifico
       |     - Limite de clientes por consultora: [40-60]
       |
       v
Sistema mostra preview: "Serao agendados 128 clientes"
Breakdown por consultora:
  LARISSA: 52 clientes
  MANU:    41 clientes
  DAIANE:  35 clientes
       |
       v
[Confirmar e Distribuir]
       |
       v
Sistema cria registros de agenda (status: PENDENTE)
Notificacao exibida: "Agenda distribuida com sucesso"
Badge nas contas das consultoras: numero de pendentes
       |
       v
Leandro pode ver /agenda com aba "Pendentes (128)"
Pode filtrar por consultora, reordenar prioridade
Pode remover cliente da agenda (acao L2 — informar)
Pode exportar agenda como xlsx
```

---

### 4.2 CONSULTORA — Receber Agenda, Executar, Registrar Resultado

```
Consultora (Manu/Larissa/Daiane) acessa /agenda
       |
       v
Ve aba "Pendentes (41)" com seus clientes
Cards ordenados por prioridade: P0 > P1 > P2 > ...
       |
       v
Clica no AgendaCard do cliente
       |
       v
Abre /clientes/:cnpj (Cliente Detalhe)
Ve: historico de atendimentos anteriores
Ve: score breakdown, sinaleiro, ABC, faturamento
Ve: ultima compra, pedidos 12 meses
       |
       v
[Novo LOG] — abre AtendimentoForm
       |
       +-- Seleciona tipo: Ligacao / WhatsApp / Visita / Email
       +-- Informa resultado: Pedido realizado / Retornar / etc
       +-- Observacoes opcionais
       |
       v
[Salvar Atendimento]
       |
       v
Sistema salva com valor R$ = 0,00 (Two-Base)
Cliente move para aba "Em Execucao" -> "Concluidas"
Timeline do cliente atualizada em tempo real
Score pode ser recalculado se resultado = Pedido realizado
       |
       v
Consultora volta para /agenda e pega proximo cliente
```

---

### 4.3 IMPORT — Upload de xlsx Mercos/SAP

```
Leandro acessa /import
       |
       v
┌─────────────────────────────────────────────┐
│ IMPORTACAO DE DADOS                         │
│                                             │
│ Tipo: [Mercos ▾] [SAP] [Deskrio]           │
│                                             │
│ ┌─────────────────────────────────────────┐ │
│ │                                         │ │
│ │    Arraste o arquivo xlsx aqui          │ │
│ │    ou [Selecionar Arquivo]              │ │
│ │                                         │ │
│ └─────────────────────────────────────────┘ │
│                                             │
│ AVISO: Verificar Data Inicial/Final         │
│ (Relatorios Mercos podem mentir nas datas)  │
│                                             │
│ [Importar]                                  │
└─────────────────────────────────────────────┘
       |
       v
Sistema valida arquivo (progress bar)
       |
       +-- Erro de formato → mensagem clara com correcao sugerida
       +-- Datas suspeitas → aviso "Confirme o periodo do relatorio"
       |
       v
Preview dos dados antes de confirmar:
  - N registros encontrados
  - N CNPJs novos / N atualizacoes / N conflitos
  - Alerta se faturamento divergir >0.5% do baseline
       |
       v
[Confirmar Importacao]
       |
       v
Importacao executada — log detalhado linha a linha
Resultado: "N registros importados com sucesso. M erros."
Link para ver erros em detalhes (exportavel)
       |
       v
Dashboard atualizado automaticamente (revalidacao)
```

---

### 4.4 DETALHE CLIENTE — Abrir, Ver Historico, Agendar

```
Entrada pode ser:
  a) Clique em linha da /carteira
  b) Clique em AgendaCard na /agenda
  c) Link direto /clientes/00000000000100
       |
       v
Carrega /clientes/:cnpj
       |
       v
Secao superior: STATUS + FINANCEIRO (2 colunas)
  Situacao [badge], Sinaleiro [badge], ABC [badge]
  Score visual com barra colorida
  Faturamento, ticket medio, ultima compra
       |
       v
Secao DADOS CADASTRAIS: razao social, cidade, telefone
       |
       v
Secao SCORE BREAKDOWN: 5 barras ScoreBar
  Frequencia | Ticket | Recencia | Mix | Estabilidade
       |
       v
Secao HISTORICO (timeline infinita, paginada em 10)
  Cada entrada: data, tipo, responsavel, resultado, obs
  [Carregar mais] → busca proxima pagina
       |
       v
Secao AGENDA ATIVA: proxima acao programada
       |
       v
Acoes disponiveis:
  [Novo LOG] → AtendimentoForm (sem campo valor R$)
  [Agendar] → Abre modal de agendamento futuro
  [Editar] → Leandro apenas — editar dados cadastrais
```

---

## 5. PALETA COMPLETA

### 5.1 Cores de Status (Inviolaveis — Regra R9)

| Nome | Hex | RGB | Uso |
|------|-----|-----|-----|
| Status Verde | `#00B050` | 0, 176, 80 | ATIVO, ABC-A, Sinaleiro VERDE |
| Status Amarelo | `#FFC000` | 255, 192, 0 | INAT.REC, ABC-C, Sinaleiro AMARELO, P2 |
| Status Vermelho | `#FF0000` | 255, 0, 0 | INAT.ANT, Sinaleiro VERMELHO, P0 |
| Status Roxo | `#800080` | 128, 0, 128 | Sinaleiro ROXO (Critico) |
| ABC Amarelo | `#FFFF00` | 255, 255, 0 | ABC-B |
| Prioridade Laranja | `#FF6600` | 255, 102, 0 | P1 |

### 5.2 Cores de Interface (UI Base)

| Nome | Hex | Uso |
|------|-----|-----|
| Branco | `#FFFFFF` | Background paginas, cards, tabelas |
| Cinza 50 | `#F9FAFB` | Background alternado, hover linhas |
| Cinza 100 | `#F3F4F6` | Background secoes secundarias |
| Cinza 200 | `#E5E7EB` | Bordas gerais, separadores |
| Cinza 300 | `#D1D5DB` | Bordas inputs, dropdowns |
| Cinza 400 | `#9CA3AF` | Texto placeholder, labels secundarios |
| Cinza 500 | `#6B7280` | Texto auxiliar, subtitulos |
| Cinza 700 | `#374151` | Texto dados, celulas tabela |
| Cinza 900 | `#111827` | Texto principal, titulos |

### 5.3 Cores de Acao e Marca

| Nome | Hex | Uso |
|------|-----|-----|
| Marca VITAO | `#00B050` | Logo, botoes primarios, links ativos |
| Azul Info | `#2563EB` | Botoes secundarios, links, ordenacao ativa |
| Azul 50 | `#EFF6FF` | Background info leve |
| Verde 50 | `#F0FDF4` | Background item ativo sidebar |
| Roxo Premium | `#7C3AED` | KpiCard faturamento |
| Vermelho Erro | `#DC2626` | Erros, alertas criticos |
| Amber | `#F59E0B` | Avisos, atencao |

### 5.4 Gradientes e Opacidades (uso controlado)

| Elemento | Spec |
|----------|------|
| Sinaleiro ROXO em cards | `rgba(128, 0, 128, 0.12)` background |
| Sinaleiro VERMELHO em cards | `rgba(255, 0, 0, 0.08)` background |
| Sinaleiro AMARELO em cards | `rgba(255, 192, 0, 0.10)` background |
| Sinaleiro VERDE em cards | `rgba(0, 176, 80, 0.08)` background |
| Overlay mobile sidebar | `rgba(0, 0, 0, 0.30)` |
| Skeleton loading | `rgba(0, 0, 0, 0.06)` pulsante |

### 5.5 Sombras

| Nome | CSS | Uso |
|------|-----|-----|
| Sombra card | `0 1px 3px rgba(0,0,0,0.08)` | KpiCard, DataTable container |
| Sombra hover | `0 2px 8px rgba(0,0,0,0.12)` | AgendaCard hover |
| Sombra modal | `0 20px 60px rgba(0,0,0,0.20)` | Modais |
| Sombra dropdown | `0 4px 16px rgba(0,0,0,0.12)` | Dropdowns abertos |

---

## 6. RESPONSIVIDADE

### 6.1 Breakpoints

| Breakpoint | Largura | Contexto |
|------------|---------|---------|
| Mobile | 375px | iPhone SE, uso emergencial em campo |
| Tablet | 768px | iPad, reunioes, uso consultora em deslocamento |
| Desktop MD | 1280px | Notebook padrao das consultoras |
| Desktop LG | 1920px | Desktop Leandro, gestao completa |

### 6.2 Desktop 1920px — Layout Completo

```
┌──────────────────────────────────────────────────────────┐
│ Sidebar 224px fixa | Conteudo flex: 1 (max 1696px)       │
│                    |                                      │
│ Nav sempre visivel | KPIs: 4 colunas grid                │
│ sem collapse       | Graficos: 2 colunas                  │
│                    | Tabelas: largura total               │
└──────────────────────────────────────────────────────────┘
```

- Sidebar: `width: 224px`, `position: fixed`, sem collapse
- Conteudo: `margin-left: 224px`, padding `24px`
- KpiCards: `grid-cols-4 gap-4`
- Graficos distribuicao: `grid-cols-2 gap-4`
- DataTable: colunas completas, todas visiveis
- AgendaCards: lista vertical com detalhes completos

### 6.3 Tablet 768px — Layout Adaptado

```
┌───────────────────────────────────────────┐
│ [Menu] CRM VITAO360        [User] [Sair] │
├───────────────────────────────────────────┤
│ Conteudo principal (largura total)         │
│                                            │
│ KPIs: 2 colunas (2x2)                     │
│ Graficos: 1 coluna (empilhados)            │
│ Tabela: scroll horizontal, colunas chave  │
└───────────────────────────────────────────┘
```

- Sidebar: `position: fixed`, desliza da esquerda, overlay escuro
- Hamburger no header topo
- KpiCards: `grid-cols-2 gap-3`
- Graficos: `grid-cols-1` (empilhados verticalmente)
- DataTable: scroll horizontal, colunas prioritarias visiveis (Nome, Status, Faturamento)
- AgendaCards: layout condensado, acoes de hover visiveis por tap

### 6.4 Mobile 375px — Layout Minimo

```
┌──────────────────────────────┐
│ [Menu] VITAO360  [User]      │
├──────────────────────────────┤
│ KPIs: 1 coluna (empilhados)  │
│ ou 2 colunas com fonte menor │
│                              │
│ Graficos: ocultados          │
│ (link "Ver distribuicao")    │
│                              │
│ Top 10: cards verticais      │
│ (sem tabela)                 │
└──────────────────────────────┘
```

- Sidebar: drawer completo sobre o conteudo
- KpiCards: `grid-cols-2` com valores menores (Arial 18pt)
- Graficos de distribuicao: ocultos no dashboard, acesso via link
- DataTable: substituida por cards verticais (lista)
- AtendimentoForm: campos em coluna unica, botoes full-width
- AgendaCards: simplificados — nome + prioridade + botao registrar

### 6.5 Regras de Responsividade

| Elemento | Desktop | Tablet | Mobile |
|----------|---------|--------|--------|
| Sidebar | Fixa visivel | Drawer overlay | Drawer overlay |
| KpiCards | 4 colunas | 2 colunas | 2 colunas |
| Graficos | 2 colunas | 1 coluna | Ocultos |
| DataTable | Todas colunas | Scroll horiz. | Cards verticais |
| AgendaCard | Completo | Compacto | Minimo |
| AtendimentoForm | 2 colunas | 1 coluna | 1 coluna |
| Botoes | inline | inline | full-width |
| Fonte dados | Arial 9pt | Arial 9pt | Arial 9pt |
| Fonte headers | Arial 10pt | Arial 10pt | Arial 10pt |

---

## 7. TIPOGRAFIA COMPLETA

| Nivel | Fonte | Tamanho | Peso | Cor | Uso |
|-------|-------|---------|------|-----|-----|
| Titulo pagina | Arial | 20pt (1.25rem) | 700 | `#111827` | H1 de cada pagina |
| Titulo secao | Arial | 14pt (0.875rem) | 600 | `#374151` | Subtitulos de cards |
| Label cabecalho | Arial | 11pt (0.6875rem) | 600 | `#6B7280` | Cabecalhos de tabela |
| Dado primario | Arial | 9pt (0.5625rem) | 400 | `#374151` | Celulas de tabela |
| Dado destaque | Arial | 9pt (0.5625rem) | 500 | `#111827` | Nome do cliente |
| Dado financeiro | Arial | 9pt (0.5625rem) | 500 | `#111827` | Valores monetarios (monospace) |
| Label secundario | Arial | 9pt (0.5625rem) | 400 | `#6B7280` | Subtextos |
| Micro texto | Arial | 10px | 400 | `#9CA3AF` | CNPJ, versao, rodape |
| KPI valor | Arial | 24pt (1.5rem) | 700 | `#111827` | Numeros principais |
| KPI subtitulo | Arial | 9pt | 400 | `#9CA3AF` | Contexto do KPI |

Valores monetarios: usar fonte `font-mono` (Courier/monospace) para alinhamento de colunas.
CNPJ: sempre `font-mono` para leitura facil.

---

## 8. ESPACAMENTO E GRID

Sistema de espacamento baseado em multiplos de 4px:

| Token | Valor | Uso |
|-------|-------|-----|
| space-1 | 4px | Gap minimo, padding micro |
| space-2 | 8px | Gap entre elementos inline |
| space-3 | 12px | Padding interno de badges/botoes |
| space-4 | 16px | Padding interno de cards |
| space-5 | 20px | Gap entre cards |
| space-6 | 24px | Padding de pagina |
| space-8 | 32px | Separacao entre secoes |

Grid de pagina:
- Colunas: 12 colunas
- Gutter: 16px (tablet) / 24px (desktop)
- Margin lateral: 24px (desktop) / 16px (tablet) / 12px (mobile)

---

## 9. ESTADOS DE INTERFACE

### Estados de Loading

| Componente | Comportamento |
|------------|---------------|
| KpiCard | Skeleton retangular pulsante |
| DataTable | 6 linhas skeleton com colunas proporcionals |
| BarChart | 4 barras skeleton de larguras variadas |
| ClienteDetalhe | Skeleton por secao |
| AgendaCard | Skeleton com 3 linhas |

Skeleton: background `#F3F4F6`, animacao `pulse 1.5s ease-in-out infinite`

### Estados de Erro

| Nivel | Componente | Cor |
|-------|------------|-----|
| Erro de pagina | Faixa topo | Fundo `#FEF2F2`, borda `#FECACA`, texto `#DC2626` |
| Erro de campo | Label abaixo | Texto `#DC2626`, icone triangulo |
| Aviso | Faixa info | Fundo `#FFFBEB`, borda `#FDE68A`, texto `#92400E` |
| Sucesso | Toast | Fundo `#F0FDF4`, borda `#BBF7D0`, texto `#166534` |

Toast notifications:
- Posicao: canto inferior direito, `z-index: 50`
- Duracao: 4 segundos
- Animacao: slide-up na entrada, fade-out na saida
- Empilhamento: maximo 3 simultaneos

### Estados Vazios

| Pagina | Mensagem | CTA |
|--------|----------|-----|
| Carteira sem filtro | "Nenhum cliente encontrado" | — |
| Agenda sem pendentes | "Agenda limpa — sem pendencias" | [Nova Agenda] |
| LOG sem registros | "Sem atendimentos registrados" | [Novo LOG] |
| Timeline vazia | "Sem historico de atendimentos" | [Registrar primeiro] |

---

## 10. ACESSIBILIDADE

### Requisitos Minimos (WCAG 2.1 AA)

| Requisito | Implementacao |
|-----------|---------------|
| Contraste texto | Min 4.5:1 para texto normal, 3:1 para texto grande |
| Focus visivel | `outline: 2px solid #2563EB` em todos os elementos focaveis |
| Alt text | Todos os icones SVG com `aria-label` ou `aria-hidden="true"` |
| Campos de formulario | `label` associado a cada `input` via `htmlFor` / `id` |
| Tabela | `<thead>`, `<th scope="col">` para cabecalhos |
| Loading | `aria-live="polite"` para skeleton states |
| Modais | Foco aprisionado dentro, `Escape` para fechar |
| Erros | `aria-invalid="true"` + `aria-describedby` para mensagem de erro |

### Verificacao de Contraste — Cores Criticas

| Combinacao | Ratio | Status |
|------------|-------|--------|
| #FFFFFF sobre #00B050 | 3.1:1 | PASS (texto grande/bold) |
| #1A1A1A sobre #FFC000 | 11.2:1 | PASS |
| #FFFFFF sobre #FF0000 | 4.0:1 | PASS (bold) |
| #FFFFFF sobre #800080 | 5.0:1 | PASS |
| #374151 sobre #FFFFFF | 8.5:1 | PASS |
| #6B7280 sobre #FFFFFF | 4.6:1 | PASS |
| #1A1A1A sobre #FFFF00 | 19.6:1 | PASS |

---

## 11. ANIMACOES E TRANSICOES

Principios: rapido, sutil, funcional. Nunca decorativo puro.

| Elemento | Animacao | Duracao | Easing |
|----------|----------|---------|--------|
| Hover linha tabela | background-color | 100ms | ease |
| Hover AgendaCard | box-shadow + translateY(-1px) | 150ms | ease |
| Sidebar mobile | translateX | 200ms | ease-out |
| BarChart preenchimento | width | 500ms | ease-out |
| ScoreBar preenchimento | width | 500ms | ease-out |
| Toast entrada | translateY(-8px) + opacity | 200ms | ease-out |
| Toast saida | opacity | 300ms | ease-in |
| Modal entrada | scale(0.95→1) + opacity | 150ms | ease-out |
| Dropdown abertura | opacity + translateY(-4px→0) | 120ms | ease-out |
| Skeleton pulse | opacity (1→0.5→1) | 1.5s | ease-in-out, infinite |
| Tab switch | opacity | 100ms | ease |
| Accordion expand | height | 200ms | ease |

Preferencia do usuario: respeitar `prefers-reduced-motion` — desativar animacoes nao essenciais.

---

## 12. COMPONENTES EXISTENTES — MAPEAMENTO

Estado atual do frontend Next.js (confirmado via leitura de codigo):

| Componente | Arquivo | Status | Proximos Passos |
|------------|---------|--------|-----------------|
| AppShell | `layout.tsx` | Implementado | Adicionar badge de notificacao no nav |
| Sidebar | `Sidebar.tsx` | Implementado | Adicionar rotas /log, /sinaleiro, /import, /config |
| KpiCard | `KpiCard.tsx` | Implementado | Adicionar variante de trending (seta up/down) |
| StatusBadge | `StatusBadge.tsx` | Implementado | Adicionar variante `dot` e `dot-label` |
| ClienteTable | `ClienteTable.tsx` | Implementado | Adicionar colunas ABC, ordenacao |
| ClienteModal | `ClienteModal.tsx` | Implementado | Evoluir para pagina /clientes/:cnpj |
| Dashboard | `page.tsx` | Implementado | Adicionar trend indicators nos KPIs |
| Carteira | `/carteira/page.tsx` | Implementado | Adicionar FilterBar completa |
| Agenda | `/agenda/page.tsx` | Implementado | Adicionar AgendaCard, fluxo distribuicao |
| Projecao | `/projecao/page.tsx` | Implementado | Verificar estado |

Componentes a criar (por prioridade):

| # | Componente | Prioridade | Pagina |
|---|------------|------------|--------|
| 1 | AgendaCard | ALTA | /agenda |
| 2 | AtendimentoForm | ALTA | /log, /clientes/:cnpj |
| 3 | TimelineEntry | ALTA | /clientes/:cnpj |
| 4 | ScoreBar | MEDIA | /clientes/:cnpj |
| 5 | SinaleiroBadge dot variant | MEDIA | Multiplas |
| 6 | FilterBar | MEDIA | /carteira, /agenda |
| 7 | ClienteDetalhePage | MEDIA | /clientes/:cnpj |
| 8 | SinaleiroPanel | BAIXA | /sinaleiro |
| 9 | ImportWizard | BAIXA | /import |
| 10 | Toast system | BAIXA | Global |

---

## 13. NAVEGACAO — SPEC SIDEBAR

### Itens de Navegacao Completos

```typescript
const navItems = [
  { href: '/',          label: 'Dashboard',    icon: 'home',       roles: ['all']     },
  { href: '/carteira',  label: 'Carteira',     icon: 'users',      roles: ['all']     },
  { href: '/agenda',    label: 'Agenda',       icon: 'calendar',   roles: ['all']     },
  { href: '/log',       label: 'LOG',          icon: 'clipboard',  roles: ['all']     },
  { href: '/projecao',  label: 'Projecao',     icon: 'trending-up',roles: ['leandro'] },
  { href: '/sinaleiro', label: 'Sinaleiro',    icon: 'traffic',    roles: ['leandro'] },
  { href: '/import',    label: 'Importacao',   icon: 'upload',     roles: ['leandro'] },
  { href: '/config',    label: 'Configuracoes',icon: 'settings',   roles: ['leandro'] },
]
```

### Badge de Notificacao

- Aparece ao lado do label "Agenda" quando ha pendencias
- Cor: `#DC2626` (vermelho)
- Texto: numero de itens pendentes (max "99+")
- Tamanho: 18px x 18px, border-radius 9px
- Fonte: Arial 10px bold branco

### Header de Usuario

```
[V] CRM VITAO360   |   [Leandro Simao ▾]    [Sair]
```

Dropdown de usuario:
- Meu Perfil
- Alterar Senha
- Sair

### Footer da Sidebar

```
VITAO Alimentos B2B
v1.0 — 2026
```

---

## 14. PAGINAS ADICIONAIS — SPEC RAPIDA

### 14.1 Login (/login)

```
┌──────────────────────────────────────┐
│                                      │
│     [V] CRM VITAO360                │
│     Inteligencia Comercial           │
│                                      │
│     ┌────────────────────────────┐   │
│     │ E-mail                     │   │
│     │ [________________________] │   │
│     │ Senha                      │   │
│     │ [________________________] │   │
│     │                            │   │
│     │ [   Entrar   ]             │   │
│     └────────────────────────────┘   │
│                                      │
│     Esqueceu a senha? Contate o      │
│     administrador.                   │
│                                      │
└──────────────────────────────────────┘
```

- Background: `#F9FAFB`
- Card centralizado: `max-width: 380px`, sombra media
- Botao Entrar: background `#00B050`, texto branco, full-width
- Sem registro publico — acesso por convite de Leandro

### 14.2 Configuracoes (/config) — Leandro apenas

Secoes:
- Parametros do Score (pesos das 5 dimensoes)
- Definicao de ranges do Sinaleiro
- Gestao de usuarios (Manu, Larissa, Daiane — sem Julio)
- Integracao Mercos (webhook ou upload)
- Integracao SAP (upload xlsx)
- Backup e exportacao de dados

### 14.3 Projecao (/projecao) — Leandro apenas

Secoes:
- Cenario Atual vs Baseline R$ 2.091.000
- Projecao 2026: R$ 3.377.120 (+69%)
- Grafico linha: historico mensal + projecao
- Q1 2026 real: R$ 459.465
- Breakdown por consultora e segmento
- Simulador de cenarios (slider de crescimento)

---

## NOTAS DE IMPLEMENTACAO

### Dependencias Recomendadas (ja alinhadas com Next.js existente)

| Dependencia | Uso |
|-------------|-----|
| `@tanstack/react-table` | DataTable avancada com ordenacao/paginacao |
| `recharts` | Graficos de linha para projecao |
| `react-dropzone` | Upload de xlsx na importacao |
| `date-fns` | Formatacao de datas pt-BR |
| `react-hot-toast` | Sistema de toasts |

Ja existente no codebase: Tailwind CSS, Next.js App Router, TypeScript.

### Convencoes de Codigo

- Componentes: PascalCase, `export default`
- Props: interface nomeada `{Component}Props`
- Cores: NUNCA hardcoded inline, usar tokens CSS ou constante importada de `lib/colors.ts`
- Formatacao BRL: SEMPRE via `formatBRL()` de `lib/api.ts`
- CNPJ: SEMPRE via `formatCnpj()` — nunca formatar manualmente
- Datas: `date-fns/locale/pt-BR` para formatacao em portugues

### Tokens de Cor Sugeridos (lib/colors.ts)

```typescript
export const colors = {
  // Status (R9 — inviolaveis)
  ativo: '#00B050',
  inatRec: '#FFC000',
  inatAnt: '#FF0000',
  prospect: '#808080',

  // Sinaleiro (R9 — inviolaveis)
  sinaleiroVerde: '#00B050',
  sinaleiroAmarelo: '#FFC000',
  sinaleiroVermelho: '#FF0000',
  sinaleiroRoxo: '#800080',

  // ABC (R9 — inviolaveis)
  abcA: '#00B050',
  abcB: '#FFFF00',
  abcC: '#FFC000',

  // Prioridade
  p0: '#FF0000',
  p1: '#FF6600',
  p2: '#FFC000',
  p3: '#FFFF00',
  p4: '#9CA3AF',
  p5: '#D1D5DB',
  p6: '#E5E7EB',
  p7: '#F3F4F6',

  // UI base
  brand: '#00B050',
  primary: '#2563EB',
  error: '#DC2626',
  warning: '#F59E0B',
  surface: '#FFFFFF',
  surfaceSecondary: '#F9FAFB',
  border: '#E5E7EB',
  textPrimary: '#111827',
  textSecondary: '#374151',
  textMuted: '#6B7280',
  textSubtle: '#9CA3AF',
} as const;
```

---

*UX_SPEC_SAAS.md — CRM VITAO360 — 2026-03-25*
*Autor: @ux VITAO360 | Regra R9 aplicada integralmente*
*LIGHT THEME EXCLUSIVAMENTE — nunca dark mode*
