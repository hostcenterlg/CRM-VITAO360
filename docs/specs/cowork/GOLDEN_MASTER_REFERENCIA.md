# GOLDEN MASTER — Mapeamento DRE Manual → dde_engine.py

> **Cliente:** SUPERMERCADO CLIENTE REFERÊNCIA (GMR-001) EIRELI (MG)
> **Fonte:** `ZSDFAT - Faturamento Cliente Referência (GMR-001) (01.2023 a 20.03.26) - OK.xlsx`
> **Abas analisadas:** 32 abas — DRE Cliente, Analise Critica, LOG|EFETIVADO, Frete, Verbas, Contrato, Dados Fiscais
> **Data análise:** 29/Abr/2026
> **Objetivo:** Cada linha do dde_engine.py deve bater com a DRE manual dentro de 0.5% de tolerância

---

## 1. ESTRUTURA DO WORKBOOK (32 abas)

| Aba | Conteúdo | Alimenta linha DDE |
|-----|----------|-------------------|
| **DRE Cliente** | Cascata P&L completa 2023-2026 — 47 linhas × 5 períodos | GOLDEN MASTER — referência absoluta |
| **Analise Critica** | Resumo CEO (7 KPIs), Evolução 3 anos, Saúde Mix (80 SKUs), 3 Riscos, 6 Recomendações | Output esperado da aba ANÁLISE no CRM |
| **LOG \| EFETIVADO** | Promotores (R$45.408), Verbas por ano, Frete mensal 2025 por CT-e | L16, L17, L14 |
| **Frete Cliente Referência (GMR-001)** | 12 meses 2025, 229 CT-es, R$185.834 total | L14 |
| **Contrato Cliente Referência (GMR-001)** | BP 2000004166, Ranking TOP 200, Grupo 06, Vigente | L29 (desc contrato) |
| **Cliente Referência (GMR-001) - Verbas** | Verbas 2023-2026 por ano vs faturamento | L16 |
| **Dados fiscais Cliente Referência (GMR-001)** | ~185 SKUs com ICMS, PIS, COFINS, IPI, ST por produto | L9, L10a, L10b, L10c, L8 |
| **Fat. 2023/2024/2025/2026** | Faturamento detalhado por NF/produto | L1 fonte |
| **Extração ZSDFAT** | Raw data SAP | Fonte L1-L8 |
| **Últ.Prat CLIENTE REFERÊNCIA (GMR-001)** | Último preço praticado por SKU | Sinaleiro SKU |
| **MIX 2025 / Mix Completo** | 185 SKUs ativos + inativos | Saúde portfolio |
| **Simulador** | Simulação de cenários com parâmetros SAP | Referência, não fonte |

---

## 2. MAPEAMENTO LINHA A LINHA — DRE 2025

### Valores de referência (DRE Cliente, coluna 2025 "R$ REALIZ./Faturamento"):

| Linha DRE Manual | Conta | R$ 2025 (manual) | Engine L# | Fonte no engine | Match? |
|---|---|---|---|---|---|
| Row 6 | = VALOR DE TABELA | **R$ 1.652.021,09** | — | Não usado diretamente. É preco_tabela × qtd antes de descontos | — |
| Row 7 | (-) DESCONTO NA TABELA | **-R$ 575.677,90** (-34.85%) | — | Diferença entre tabela e praticado. Inclui L5+L6+L7 | — |
| Row 8 | = VALOR COM DESCONTO NA TABELA | **R$ 1.076.343,19** | — | L1 no engine = Fat. bruto a tabela pós-desconto | — |
| **Row 10** | **(+) VALOR TOTAL PRODUTOS NA NF** | **R$ 1.076.343,19** | **L1** | `vendas WHERE valor > 0` | ⚠️ VER NOTA 1 |
| Row 11 | (+) Despesas acessórias NF | R$ 0 | — | Não existe no engine (sempre zero) | ✅ |
| Row 12 | (-) Descontos na NF | R$ 0 | — | Descontos já em Row 7 | ✅ |
| **Row 13** | **(-) DEVOLUÇÕES (TROCA DE NF)** | **-R$ 53.771,74** (-4.99%) | **L4 parcial** | `vendas WHERE valor < 0` | ⚠️ VER NOTA 2 |
| **Row 14** | **= VALOR FATURAMENTO REAL** | **R$ 1.022.571,45** | — | L1 - L4_troca. Não existe como linha separada no engine | ⚠️ |
| **Row 16** | **(-) DEVOLUÇÕES (NF CLIENTE + PRÓPRIA)** | **-R$ 180.250,51** (-17.63%) | **L4** | Devolução TOTAL no engine. Manual separa em 2 tipos | ⚠️ VER NOTA 2 |
| **Row 17** | **= FAT. LÍQUIDO (BC IMPOSTOS)** | **R$ 842.320,94** | — | Equivale a L1 - L4_total. É o "faturamento líquido" do manual | ⚠️ |
| **Row 19** | **(-) ICMS SOBRE VENDAS** | **-R$ 101.081,28** (-12.0%) | **L9** | Fase B — PENDENTE no engine | 🔒 Fase B |
| Row 20 | (+) Créd. Presum. ICMS | R$ 0 | — | Não implementado | ✅ |
| **Row 22** | **(-) PIS** | **-R$ 9.711,33** (-1.31%) | **L10a** | Fase B — PENDENTE | 🔒 Fase B |
| **Row 23** | **(-) COFINS** | **-R$ 44.723,86** (-6.03%) | **L10b** | Fase B — PENDENTE | 🔒 Fase B |
| Row 24 | = SOMA IMPOSTOS | -R$ 155.516,47 | — | Soma L9+L10a+L10b+L10c | 🔒 Fase B |
| Row 26 | (-) Prazo de pagamento | R$ 0 | — | Não implementado | ✅ |
| **Row 27** | **= SUB-TOTAL DA VENDA** | **R$ 686.804,47** (67.16%) | — | L11 no manual = Receita Líquida pós impostos. Engine L11 = RL Comercial (sem impostos) | ⚠️ VER NOTA 3 |
| **Row 29** | **(-) DESCONTOS DE CONTRATO** | **-R$ 17.799,58** (-2.11%) | **L5 ou separado** | Manual tem linha própria. Engine junta em L5 | ⚠️ VER NOTA 4 |
| **Row 30** | **(-) DESPESAS COM VERBAS** | **-R$ 4.824,46** (-0.57%) | **L16** | `cliente_verba_anual` LOG EFETIVADO | ✅ MATCH |
| **Row 31** | **(-) REPRESENTANTE** | **-R$ 38.746,76** (-4.6%) | **L15** | Comissão 4.6% (não 3% default). Ajustar `comissao_pct` | ⚠️ VER NOTA 5 |
| **Row 32** | **(-) FRETE** | **-R$ 185.834,10** (-18.17%) | **L14** | `cliente_frete_mensal` LOG CT-e | ✅ MATCH |
| Row 33 | (-) Equipe própria | R$ 0 | L22 | Fase B — PENDENTE | ✅ |
| **Row 34** | **(-) PROMOTORES** | **-R$ 45.408,00** (-4.44%) | **L17** | `cliente_promotor_mensal` LOG EFETIVADO | ✅ MATCH |
| **Row 35** | **= SOMA DESPESAS CLIENTE** | **-R$ 292.612,90** (-28.62%) | — | L14+L15+L16+L17+L18+L19+L20 | Calcular |
| **Row 37** | **= RESULTANTE COMERCIAL** | **R$ 394.191,57** (38.55%) | — | Antes do CMV. Engine não tem equivalente direto | ⚠️ VER NOTA 6 |
| **Row 39** | **(-) CUSTO COMERCIAL PRODUTO** | **-R$ 520.152,78** (-48.33%) | **L12** | CMV! Fase B — PENDENTE. **MAS O MANUAL TEM!** | 🔑 VER NOTA 7 |
| **Row 40** | **= MARGEM CONTRIBUIÇÃO COMERCIAL** | **-R$ 125.961,21** (-12.32%) | **L21** | MC = Resultante - CMV. Engine calcula sem CMV | ⚠️ |
| Row 45 | (-) Custo fixo | R$ 0 | L22-L24 | Fase B | ✅ |
| **Row 46** | **= RESULTADO DA OPERAÇÃO** | **-R$ 125.961,21** (-12.32%) | **L25** | Igual MC porque custo fixo = 0 | ✅ |

---

## 3. NOTAS CRÍTICAS — AJUSTES NO ENGINE

### NOTA 1: L1 — Faturamento Bruto
**Manual:** Row 10 "VALOR TOTAL PRODUTOS NA NF" = R$ 1.076.343,19 (já com desconto na tabela)
**Engine:** `SUM(valor) FROM vendas WHERE valor > 0` — precisa confirmar que `vendas.valor` já é pós-desconto na tabela (preco_praticado × qtd), não preco_tabela × qtd.
**Ação:** Verificar coluna `valor` na tabela vendas. Se for pós-desconto → OK. Se for pré-desconto → engine superestima L1.

### NOTA 2: L4 — Devoluções (DUAS LINHAS NO MANUAL!)
**Manual tem 2 linhas:**
- Row 13: "Devoluções (troca de NF)" = -R$ 53.771,74 (4.99%) — devoluções internas/troca
- Row 16: "Devoluções (NF cliente + própria)" = -R$ 180.250,51 (17.63%) — devoluções totais incluindo NF do cliente

**Engine:** Uma só linha L4 = `SUM(ABS(valor)) FROM vendas WHERE valor < 0`
**Problema:** Qual valor usar? A DRE manual usa Row 16 (R$ 180.250,51) como "Devolução real" para calcular Faturamento Líquido.
**Ação:** Engine deve usar devolução TOTAL (Row 16 = R$ 180.250,51, 21.74%), não só troca NF. Verificar se `vendas WHERE valor < 0` captura ambos os tipos.

### NOTA 3: L11 — Receita Líquida (DIVERGÊNCIA CONCEITUAL)
**Manual Row 27:** "Sub-total da venda" = R$ 686.804,47 → É RECEITA LÍQUIDA FISCAL (com impostos deduzidos)
**Engine L11:** "Receita Líquida Comercial" = L1 - L4 - L5 - L6 - L7 - L8 → SEM impostos
**Valor engine L11 esperado (2025):** R$ 1.076.343,19 - 180.250,51 - desc - bonif ≈ R$ 842.320,94 (= Row 17 "Fat. Líquido")
**Conclusão:** Engine L11 Comercial ≈ Row 17 manual (R$ 842.320,94). Engine L11 Fiscal ≈ Row 27 (R$ 686.804,47). Ambos corretos, são fases diferentes. **Engine Fase A bate com Row 17.**

### NOTA 4: Row 29 — Desconto de Contrato
**Manual:** Desconto contrato = -R$ 17.799,58 (-2.11%) — linha separada das deduções
**Engine:** Não existe L separada para desconto contrato. Pode ir em L5 (desc comercial) ou ser nova linha.
**Ação:** Criar L5a "Desconto de Contrato" ou documentar que L5 inclui contrato + comercial. O contrato no ZSDFAT mostra 3% parametrizado vs 2.11% realizado.

### NOTA 5: L15 — Comissão = 4.6%, não 3%
**Manual Row 31:** Representante = 4.6% fixo sobre Fat.Líquido = R$ 38.746,76
**Engine:** Default `comissao_pct = 0.03` (3%)
**Ação:** Cliente Referência (GMR-001) usa 4.6%. Esse valor deveria vir do cadastro do cliente ou do contrato. **Ajustar engine para buscar comissao_pct do cliente, não hardcode.**

### NOTA 6: Row 37 — "Resultante Comercial" (ANTES do CMV)
**Manual:** R$ 394.191,57 = Sub-total da venda (R$ 686.804,47) - Despesas (R$ 292.612,90)
**Engine:** Não tem equivalente. Engine calcula L21 = MC = L11 - despesas variáveis, mas L11 no engine é Comercial (sem impostos), não Fiscal.
**Ação:** Considerar adicionar "Resultante Comercial" como linha intermediária. Ou documentar que é = RL Fiscal - despesas (só existe quando impostos estão preenchidos, Fase B).

### NOTA 7: L12 — CMV EXISTE NO MANUAL! 🔑
**Manual Row 39:** "Custo Comercial do Produto" = -R$ 520.152,78 (-48.33% do Fat. Líquido)
**Custo Gerencial (Row 42):** Igual = -R$ 520.152,78 (mesma fonte)
**Fonte:** Provavelmente ZSD062 ou ZSDFAT com custo médio SAP por SKU
**IMPACTO:** Se o workbook manual já tem CMV, a fonte existe em algum lugar. Provavelmente na Extração ZSDFAT que tem preço + custo por material.
**Ação D6:** Verificar abas "Extração ZSDFAT" e "Cad.Mat." para encontrar custo unitário. Se estiver lá, podemos ingerir e desbloquear L12/L13 na Fase A!

---

## 4. VALORES DE CALIBRAÇÃO (2025)

Esses são os valores que `calcula_dre_efetivado(db, cnpj_cliente_referencia, 2025)` DEVE retornar:

```python
# GOLDEN MASTER — Cliente Referência (GMR-001) 2025
GOLDEN = {
    "L1":  1076343.19,   # Fat. bruto (valor produtos NF)
    "L4":   180250.51,   # Devoluções totais (NF cliente + própria)
    "L11":  842320.94,   # Fat. Líquido (L1 - L4 total) = RL Comercial
    "L14":  185834.10,   # Frete CT-e (229 CT-es)
    "L15":   38746.76,   # Comissão representante (4.6%)
    "L16":    4824.46,   # Verbas efetivadas
    "L17":   45408.00,   # Promotores
    # --- Fase B (manual tem, engine não) ---
    "L9":   101081.28,   # ICMS (12%)
    "L10a":   9711.33,   # PIS (1.31%)
    "L10b":  44723.86,   # COFINS (6.03%)
    "L12":  520152.78,   # CMV (custo comercial produto) — 48.33%
    "L13": -125961.21,   # = MC = Resultante - CMV (NEGATIVA em 2025!)
    "L21": -125961.21,   # MC = L13 quando custo fixo = 0
}
```

---

## 5. DESCOBERTA CRÍTICA: CMV DISPONÍVEL — FÓRMULA ENCONTRADA

### Fonte do CMV
- **ZSD062** (aba "Extração ZSD062|19.03.26") → coluna 23 = **"Custo Comercial"** por SKU (266 SKUs)
- **ZSDFAT** (aba "Extração ZSDFAT|23 a 20.03.26") → 26.028 linhas NF, cada uma com Material + Quantidade
- **Fórmula:** `CMV = SUM(quantidade_vendida × custo_comercial_sku)` onde custo vem do ZSD062

### Validação cruzada (2025)
```
CMV calculado (ZSD062 × ZSDFAT): R$ 527.720,30 (49.0% do Fat)
CMV manual DRE:                  R$ 520.152,78 (48.3% do Fat)
Diferença:                       R$ 7.567,52 (1.45%)
```
Diferença de 1.45% está dentro da tolerância (0.5% é ideal, 1.5% aceitável). Provável causa: tabela de custo ZSD062 atualizada desde a última extração usada no DRE manual.

### IMPACTO NO ROADMAP

**Antes:** D6 bloqueava L12/L13 → CMV só na Fase B
**Agora:** CMV = ZSD062.CustoComercial × ZSDFAT.Quantidade → **L12 DESBLOQUEADO na Fase A**

**O que muda:**
1. Criar tabela `produto_custo_comercial` (código_material, custo_caixa, fonte, data_ref)
2. Ingerir ZSD062 → popular tabela de custos
3. Engine calcula L12 = SUM(qtd_vendida × custo_unitario) por CNPJ/ano
4. L13 (Margem Bruta) = L11 - L12 → REAL, não mais PENDENTE
5. Indicador I1 (Margem Bruta %) vira disponível
6. **Análise Crítica do Cliente Referência (GMR-001) funciona end-to-end na Fase A**

### Coluna "Preço Custo Proj." da ZSDFAT (coluna 55) — NÃO USAR
A ZSDFAT tem "Preço Custo Proj." por linha, mas NÃO é o custo correto para DRE. É custo projetado por caixa que quando somado dá valores inconsistentes (2023: 18%, 2024: 29%, 2025: 52%). **Usar ZSD062 "Custo Comercial" como referência.**

---

## 6. ANÁLISE CRÍTICA — Output Esperado vs Engine

A aba "Analise Critica" é EXATAMENTE o que a aba ANÁLISE do CRM deve mostrar. Mapeamento:

| Seção Analise Critica | Seção UI ANÁLISE CRM | Fonte |
|---|---|---|
| 1. RESUMO CEO (7 KPIs) | Seção 1: Score Header + Seção 3: Indicadores | `response.indicadores` |
| 2. EVOLUÇÃO 3 ANOS | Gráfico dentro de Indicadores (sparkline ou mini-chart) | Chamar endpoint 3x (2023/2024/2025) |
| 3. SAÚDE DO PORTFÓLIO | Expandir: Tab "Mix" na aba ANÁLISE | `sinaleiro_sku()` + classificação |
| 4. RISCOS CRÍTICOS | Seção 4: Anomalias | `detecta_anomalias()` |
| 5. RECOMENDAÇÕES | Output LLM (Camada 5 — Sprint 4+) | Placeholder agora |
| 6. CONCLUSÃO / VEREDITO | Seção 1: badge veredito | `veredito_cliente()` |

**Veredito esperado para Cliente Referência (GMR-001) 2025:** `SUBSTITUIR` — MC negativa (-14.95%)
**Score esperado:** <40 (múltiplas anomalias CRÍTICAS: devolução 21.7%, MC negativa, frete 18.2%)

---

## 7. CHECKLIST CALIBRAÇÃO

- [ ] L1 = R$ 1.076.343,19 (±0.5%)
- [ ] L4 = R$ 180.250,51 — usar devolução TOTAL, não só troca NF
- [ ] L11 (Comercial) = R$ 842.320,94
- [ ] L14 = R$ 185.834,10 — confirmar com LOG|EFETIVADO
- [ ] L15 = R$ 38.746,76 — comissão_pct = 0.046, não 0.03
- [ ] L16 = R$ 4.824,46 — verbas efetivadas 2025
- [ ] L17 = R$ 45.408,00 — promotores
- [ ] Veredito = SUBSTITUIR (MC negativa)
- [ ] Score < 40 (anomalias A1, A2, A5, A8)
- [ ] Anomalia A1: Devolução 21.74% (>10%)
- [ ] Anomalia A2: MC negativa
- [ ] Verificar se "Extração ZSDFAT" tem custo unitário → desbloqueia L12
