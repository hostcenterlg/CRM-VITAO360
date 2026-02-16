# 🎯 JARVIS CRM CENTRAL — ÍNDICE MESTRE
## Documentação Fase a Fase para Construção Excel

---

## QUEM SOMOS

**Empresa:** VITAO Alimentos — distribuidora B2B de alimentos naturais (Curitiba-PR)
**Canal:** Lojistas de produtos naturais (pequeno varejo)
**Operador:** Leandro (único usuário da planilha; consultores recebem agendas via WhatsApp)
**CEO:** Autista, altamente inteligente, prefere formatos resumidos, scroll vertical

---

## EQUIPE COMERCIAL

| CONSULTOR | TERRITÓRIO | REDES EXCLUSIVAS |
|-----------|-----------|-----------------|
| MANU DITZEL | SC, PR, RS | — |
| LARISSA PADILHA | Resto do Brasil | — |
| JULIO GADRET | — | CIA DA SAUDE, FITLAND |
| DAIANE STAVICKI | — | DIVINA TERRA, BIOMUNDO, MUNDO VERDE, VIDA LEVE, TUDO EM GRAOS |

---

## UNIVERSO DE DADOS

- 489 clientes carteira (105 ativos, 80 inat.rec, 304 inat.ant)
- 5.540 prospects cadastrados
- 923 lojas em 8 redes de franquia
- Taxa retenção atual: ~20.3% (crítica)

---

## ARQUIVO FINAL

**Nome:** `JARVIS_CRM_CENTRAL_FEV2026.xlsx`

| ABA | NOME | COLUNAS | FUNÇÃO | FASE |
|-----|------|---------|--------|------|
| 1 | CARTEIRA | 81 | Fonte única da verdade — 1 linha por CNPJ | FASE 1 |
| 2 | LOG | 20 | Histórico oficial de interações | FASE 2 |
| 3 | DRAFT 2 | 27 | Quarentena — valida antes de ir pro LOG | FASE 3 |
| 4 | DASH | ~16 | 7 dashboards atendimentos (vertical) | FASE 4 |
| 5 | DASH CLIENTES | ~6 | Saúde carteira, funil, positivação | FASE 5 |
| 6 | REGRAS | — | Tabelas validação, dropdowns, cálculos | FASE 0 |

**Arquivo separado:** `AGENDA_[CONSULTOR]_[DATA].xlsx` — FASE 6

---

## ORDEM DE CONSTRUÇÃO

```
FASE 0: REGRAS ────── fundação (Named Ranges, tabelas validação)
    ↓
FASE 1: CARTEIRA ──── 81 cols, 8 grupos [+], fórmulas
    ↓
FASE 2: LOG ────────── 20 cols, PROCV da CARTEIRA
    ↓
FASE 3: DRAFT 2 ───── 27 cols, validação automática
    ↓
FASE 4: DASH ──────── 7 blocos, CONT.SES do LOG
    ↓
FASE 5: DASH CLIENTES  4 blocos, CONT.SES da CARTEIRA
    ↓
FASE 6: AGENDA ────── Arquivo separado, script gerador
```

**CADA FASE = 1 CONVERSA NOVA** com Claude. Entregar o documento da fase + o arquivo .xlsx gerado na fase anterior.

---

## REGRAS INVIOLÁVEIS

1. **CNPJ = chave primária** em todas as abas. Formato TEXTO: 00.000.000/0000-00
2. **Two-Base Architecture:** Valores financeiros SEPARADOS de interações. Nunca misturar.
3. **Fórmulas em PORTUGUÊS:** SE, PROCV, ÍNDICE, CORRESP, CONT.SES, SOMASES, HOJE
4. **Fórmulas Excel reais** — NUNCA calcular em Python e hardcodar valores
5. **Cores imutáveis:** ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000
6. **Font:** Arial 10 sempre. Tema LIGHT (nunca dark mode)
7. **Zero fabricação de dados.** Se não tem, fica vazio.
8. **Rodar `python scripts/recalc.py`** após cada fase e corrigir TODOS os erros

---

## MAPA DE REFERÊNCIAS CRUZADAS

### CARTEIRA referencia:
- REGRAS → Named Ranges para dropdowns (TAB_CONSULTOR, TAB_SITUACAO, etc.)
- REGRAS → PROCV para dias follow-up

### LOG referencia:
- CARTEIRA → ÍNDICE+CORRESP por CNPJ (puxa nome, UF, rede, situação, fase, tentativa)
- REGRAS → TAB_RESULTADO_FOLLOWUP para calcular datas follow-up

### DRAFT 2 referencia:
- CARTEIRA → CORRESP por CNPJ (validação se existe)
- REGRAS → Named Ranges para dropdowns inline

### DASH referencia:
- LOG → CONT.SES para todas as matrizes (por DATA, CONSULTOR, TIPO, RESULTADO, MOTIVO)

### DASH CLIENTES referencia:
- CARTEIRA → CONT.SES (SITUAÇÃO, SINALEIRO, FASE, POSITIVAÇÃO)

### AGENDA (separado):
- CARTEIRA → dados read-only (filtrados por consultor + prioridade)
- Dropdowns inline (sem referência Named Ranges)

---

## CHECKLIST GLOBAL (executar ao final de todas as fases)

- [ ] REGRAS: 10 Named Ranges criados
- [ ] CARTEIRA: 81 colunas, 8 grupos, freeze K2
- [ ] LOG: 20 colunas, fórmulas ÍNDICE+CORRESP, freeze E2
- [ ] DRAFT 2: 27 colunas, validação Y/Z/AA
- [ ] DASH: 7 blocos verticais, filtros, CONT.SES
- [ ] DASH CLIENTES: 4 blocos, CONT.SES/SOMASES
- [ ] AGENDA: template funcional, script gerador
- [ ] Zero erros em TODAS as abas (recalc.py)
- [ ] Dropdowns funcionam em todas as abas
- [ ] Formatação condicional aplicada (cores situação, sinaleiro, etc.)
- [ ] Cross-references testadas (alterar dado na CARTEIRA → reflete no LOG/DASH)

---

## DOCUMENTOS POR FASE

| ARQUIVO | FASE | PÁGINAS |
|---------|------|---------|
| `FASE_0_REGRAS.md` | Foundation | ~3 |
| `FASE_1_CARTEIRA.md` | Core | ~6 |
| `FASE_2_LOG.md` | Core | ~4 |
| `FASE_3_DRAFT2.md` | Validation | ~3 |
| `FASE_4_DASH.md` | Dashboards | ~5 |
| `FASE_5_DASH_CLIENTES.md` | Dashboards | ~3 |
| `FASE_6_AGENDA.md` | Operations | ~3 |

**Total: 7 documentos, ~27 páginas de especificação**

---

## COMO USAR

1. Abrir conversa nova com Claude
2. Colar o documento da FASE correspondente
3. Anexar o .xlsx da fase anterior (se houver)
4. Pedir para construir
5. Validar resultado
6. Seguir para próxima fase

**Dica:** Testar simultaneamente no Claude Chat e Claude Code para comparar resultados.
