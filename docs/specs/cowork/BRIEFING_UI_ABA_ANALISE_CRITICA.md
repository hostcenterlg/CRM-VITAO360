# BRIEFING UI: Aba "Análise" no Cliente — DDE + Análise Crítica

> **Data:** 29/Abr/2026
> **Para:** VSCode executor (Next.js frontend)
> **Depende de:** `routes_dde.py` (5 endpoints), `dde_engine.py` (engine Python)
> **Página:** `/clientes/[cnpj]` → nova aba "ANÁLISE"

---

## VISÃO GERAL

Quando o gestor abre um cliente, hoje vê: DADOS, VENDAS, CONTATO, HISTÓRICO.
A nova aba **ANÁLISE** mostra a cascata P&L daquele cliente em tempo real.

```
┌────────────────────────────────────────────────────────────────────┐
│  CLIENTE REFERÊNCIA (GMR-001) LTDA · CNPJ 12.345.678/0001-90                      │
│  [DADOS]  [VENDAS]  [CONTATO]  [HISTÓRICO]  [✦ ANÁLISE]           │
│  ─────────────────────────────────────────── ════════════           │
└────────────────────────────────────────────────────────────────────┘
```

A aba ANÁLISE tem 4 seções verticais, scrolláveis:

---

## SEÇÃO 1: HEADER — Score + Veredito

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                     │
│  ┌─────────┐                                                        │
│  │  78/100  │  REVISAR                                              │
│  │  ████░░░ │  "Margem 5-15% — atenção em verba/devolução"         │
│  └─────────┘                                                        │
│                                                                     │
│  Fase A · Dados comerciais · Atualizado 29/Abr 14:32               │
│                                                                     │
│  [↻ Recalcular]                              Ano: [2025 ▼]         │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

**Regras:**
- Score (I9): círculo radial. Verde ≥80, Amarelo 60-79, Laranja 40-59, Vermelho <40
- Veredito: badge grande com cor correspondente
  - SAUDAVEL → verde `#4CAF50`
  - REVISAR → amarelo `#FFC107` texto escuro
  - RENEGOCIAR → laranja `#FF9800`
  - SUBSTITUIR → vermelho `#F44336`
  - ALERTA_CREDITO → roxo `#9C27B0`
  - SEM_DADOS → cinza `#9E9E9E`
- "Fase A" tag pequena → indica que é cascata comercial (sem SAP fiscal)
- Botão "Recalcular" faz `GET /api/dde/cliente/{cnpj}?ano=X&persist=true`
- Dropdown "Ano" filtra o período

---

## SEÇÃO 2: CASCATA P&L — A tabela principal

```
┌────────────────────────────────────────────────────────────────────┐
│  DEMONSTRAÇÃO DE RESULTADO — CASCATA P&L                           │
│                                                                     │
│  LINHA │ CONTA                        │ VALOR (R$)   │ % RL  │ ▮  │
│  ──────┼─────────────────────────────┼──────────────┼───────┼───  │
│  L1    │ Faturamento bruto a tabela   │  1.234.567   │       │ ██ │
│  L2    │ IPI sobre vendas             │          —   │       │    │
│  L3    │ = Receita Bruta com IPI      │  1.234.567   │       │ ██ │
│  ──────┼─────────────────────────────┼──────────────┼───────┼───  │
│  L4    │ (-) Devoluções               │    -45.230   │  3.7% │ █  │
│  L5    │ (-) Desconto comercial       │          —*  │       │    │
│  L6    │ (-) Desconto financeiro      │          —*  │       │    │
│  L7    │ (-) Bonificações             │          —*  │       │    │
│  L8    │ (-) IPI faturado             │          —   │       │    │
│  L9    │ (-) ICMS                     │  ░░░░░░░░░   │       │    │
│  L10a  │ (-) PIS                      │  ░░░░░░░░░   │       │    │
│  L10b  │ (-) COFINS                   │  ░░░░░░░░░   │       │    │
│  L10c  │ (-) ICMS-ST                  │  ░░░░░░░░░   │       │    │
│  L11   │ = Receita Líquida (Comerc.)  │  1.189.337   │ 100%  │ ██ │
│  ──────┼─────────────────────────────┼──────────────┼───────┼───  │
│  L12   │ (-) CMV                      │  ░░░░░░░░░   │       │    │
│  L13   │ = Margem Bruta               │  ░░░░░░░░░   │       │    │
│  ──────┼─────────────────────────────┼──────────────┼───────┼───  │
│  L14   │ (-) Frete                    │    -98.400   │  8.3% │ █  │
│  ...   │ ...                          │              │       │    │
│  L21   │ = Margem Contribuição        │   890.120    │ 74.8% │ ██ │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

**Regras visuais da tabela:**

1. **Linhas totalizadoras** (L3, L11, L13, L21, L25): fundo `#F5F5F5`, font-weight 600, borda superior
2. **Linhas PENDENTE** (valor=null): mostrar `░░░░░` em cinza claro com tooltip "Aguardando [fonte]"
3. **Linhas SINTETICO**: asterisco `*` ao lado do valor, tooltip "Estimativa — [observacao]"
4. **Linhas REAL**: sem marcação especial
5. **Coluna % RL**: percentual sobre L11 (Receita Líquida). Só para linhas de L4 em diante.
6. **Barra visual** (última coluna): barra horizontal proporcional ao valor absoluto. Verde para linhas =, vermelho para linhas (−)
7. **Separadores de bloco**: linha cinza grossa entre blocos (Receita → Deduções → CMV → Despesas → Fixas → Resultado)
8. **Legenda no rodapé**:
   ```
   ██ REAL   ██* SINTÉTICO (estimativa)   ░░░ PENDENTE (Fase B)
   ```

**API call:**
```
GET /api/dde/cliente/{cnpj}?ano=2025
→ response.dre[] → mapear diretamente para linhas da tabela
```

---

## SEÇÃO 3: INDICADORES — Cards de KPI

```
┌────────────────────────────────────────────────────────────────────┐
│  INDICADORES                                                        │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ MC %     │  │ Custo    │  │ Devolução│  │ DSO      │           │
│  │  74.8%   │  │ Servir   │  │   3.7%   │  │  42 dias │           │
│  │  ▲ 2.1pp │  │  12.3%   │  │  ▼ 0.5pp │  │  ▼ 8d   │           │
│  │  verde   │  │  verde   │  │  verde   │  │  verde   │           │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘           │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                         │
│  │ Verba %  │  │ Inadimp  │  │ Margem   │                         │
│  │   4.2%   │  │   1.8%   │  │ Bruta    │                         │
│  │  verde   │  │  verde   │  │ ░░░ Fase B│                         │
│  └──────────┘  └──────────┘  └──────────┘                         │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

**Regras:**
- 7 cards em grid (4 colunas desktop, 2 mobile)
- Cada card usa a cor do semáforo: verde (bom), amarelo (atenção), vermelho (crítico)
- Cards Fase B: fundo cinza claro, badge "Fase B"
- Variação vs período anterior (se disponível): seta ▲/▼ com pp ou dias
- Card I1 (Margem Bruta %): desabilitado até CMV existir
- Cards mapeiam direto de `response.indicadores`

**Thresholds para cor:**

| Indicador | Verde | Amarelo | Vermelho |
|-----------|-------|---------|----------|
| MC % (I2) | ≥15% | 5-15% | <5% |
| Custo Servir (I4) | <15% | 15-25% | >25% |
| Devolução (I7) | <5% | 5-10% | >10% |
| DSO/Aging (I8) | <45d | 45-90d | >90d |
| Verba % (I5) | <5% | 5-8% | >8% |
| Inadimpl (I6) | <3% | 3-5% | >5% |

---

## SEÇÃO 4: ANOMALIAS — Alertas do motor de regras

```
┌────────────────────────────────────────────────────────────────────┐
│  ALERTAS                                    3 anomalias detectadas  │
│                                                                     │
│  🔴 CRÍTICA · A2 Margem de contribuição negativa                   │
│     MC = -R$ 12.340 · Limite: R$ 0                                  │
│                                                                     │
│  🟡 MÉDIA · A4 Verba alta                                          │
│     Verba 9.2% da receita · Limite: 8%                              │
│                                                                     │
│  🟡 MÉDIA · A8 Frete alto                                          │
│     Frete 13.1% da receita · Limite: 12%                            │
│                                                                     │
└────────────────────────────────────────────────────────────────────┘
```

**Regras:**
- Lista vertical, ordenada por severidade (CRITICA → ALTA → MEDIA)
- Ícone: 🔴 CRITICA, 🟠 ALTA, 🟡 MEDIA
- Cada alerta mostra: regra, descrição, valor encontrado, limite
- Se zero anomalias: mostrar "✅ Nenhuma anomalia detectada" com fundo verde claro
- API: `GET /api/dde/score/{cnpj}?ano=2025` → `response.anomalias[]`

---

## COMPONENTES REACT (sugestão de estrutura)

```
components/
  cliente/
    analise/
      TabAnalise.tsx           ← orquestrador (fetch + state)
      ScoreHeader.tsx          ← seção 1 (score radial + veredito)
      CascataTable.tsx         ← seção 2 (tabela DRE)
      IndicadoresGrid.tsx      ← seção 3 (cards KPI)
      AnomaliasPanel.tsx       ← seção 4 (lista de alertas)
      CascataRow.tsx           ← linha individual da tabela
      StatusBadge.tsx          ← badge REAL/SINTETICO/PENDENTE
```

**State:**
```typescript
const [dre, setDre] = useState<DREResponse | null>(null)
const [score, setScore] = useState<ScoreResponse | null>(null)
const [ano, setAno] = useState(2025)
const [loading, setLoading] = useState(true)

useEffect(() => {
  Promise.all([
    fetch(`/api/dde/cliente/${cnpj}?ano=${ano}`).then(r => r.json()),
    fetch(`/api/dde/score/${cnpj}?ano=${ano}`).then(r => r.json()),
  ]).then(([dreData, scoreData]) => {
    setDre(dreData)
    setScore(scoreData)
    setLoading(false)
  })
}, [cnpj, ano])
```

---

## RESPONSIVIDADE

| Breakpoint | Layout |
|------------|--------|
| ≥1280px | Cascata full width, indicadores 4 colunas |
| 768-1279px | Cascata com scroll horizontal, indicadores 3 colunas |
| <768px | Cascata em cards empilhados (não tabela), indicadores 2 colunas |

**Mobile (cascata como cards):**
```
┌──────────────────────────┐
│ L1 · Faturamento bruto   │
│ R$ 1.234.567             │
│ ██████████████████ REAL   │
├──────────────────────────┤
│ L4 · (-) Devoluções      │
│ -R$ 45.230 · 3.7% RL    │
│ ████████ REAL             │
└──────────────────────────┘
```

---

## CORES VITÃO

Usar as cores do CRM, não inventar novas:
- Verde primário: `#00A859`
- Azul: `#0066CC`
- Roxo: `#7C3AED`
- Laranja: `#F59E0B`
- Vermelho: `#EF4444`
- Cinza texto: `#374151`
- Cinza fundo: `#F9FAFB`
- Cinza borda: `#E5E7EB`

---

## CHECKLIST

- [ ] Aba "ANÁLISE" aparece na página do cliente
- [ ] Score radial com cor correta
- [ ] Veredito badge com cor semântica
- [ ] Cascata P&L: 25 linhas renderizadas
- [ ] Linhas PENDENTE: fundo cinza + ░░░
- [ ] Linhas SINTETICO: asterisco + tooltip
- [ ] Linhas totalizadoras: fundo destacado
- [ ] 7 cards de indicadores com semáforo
- [ ] Anomalias listadas por severidade
- [ ] Dropdown ano funciona
- [ ] Botão recalcular funciona
- [ ] Responsivo: desktop + tablet + mobile
- [ ] **TESTAR:** Cliente Referência (GMR-001) renderiza cascata completa
- [ ] **TESTAR:** Cliente sem dados mostra "SEM_DADOS" e não crash
