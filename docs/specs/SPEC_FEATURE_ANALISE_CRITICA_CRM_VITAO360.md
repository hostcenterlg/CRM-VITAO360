# FEATURE: ANÁLISE CRÍTICA DO CLIENTE

Spec técnica + handoff de implementação para CRM VITAO360
Versão: 1.0 · Data: 28/04/2026 · Owner: Leandro · Status: spec

---

## 1. TESE

A Análise Crítica do Cliente é a feature que transforma o que hoje fazemos manualmente — abrir Excel ZSDFAT, cruzar com LOG | EFETIVADO, ler 4 fontes adicionais, montar DRE corrigido, gerar veredito por SKU, escrever Resumo CEO — em uma aba do CRM que abre em <2 segundos com tudo já consolidado.

**Diferença essencial:** DRE comum é P&L (números). Análise Crítica é **P&L + diagnóstico + sinaleiro + recomendação acionável + impacto R$ estimado por ação.**

Não é dashboard. É **decisão**. Cada cliente tem 1 página com:

- Margem global atual + veredito (SAUDÁVEL / RENEGOCIAR / SUBSTITUIR)
- 3 anomalias críticas detectadas automaticamente
- 5 ações priorizadas com impacto R$
- Botão "Gerar Resumo CEO" (PDF 1 página)

---

## 2. PROBLEMA QUE RESOLVE

Hoje, para cada cliente:

- 30-45 min de trabalho de analista para abrir o ZSDFAT, navegar 13 abas, identificar erros de fórmula, substituir parâmetros SAP por dados EFETIVADOS, validar gap MIX × DRE, gerar entregáveis.
- Erro humano frequente: usar parâmetro SAP onde tem dado real, fórmula em cascata errada, devolução média geral em vez de específica do cliente.
- Resultado fica num Excel local — não compartilhável, não auditável, não versionável.
- Cross-cliente é impossível: comparar Coelho × Giassi × Angeloni × Koch exige abrir 4 arquivos.

**Com a feature:** abre o cliente no CRM, vê tudo. Compara 2 clientes lado a lado em 1 clique.

---

## 3. ARQUITETURA EM 6 CAMADAS

```
┌─────────────────────────────────────────────────────────┐
│ 6. INTERFACE — Aba "Análise Crítica" no CRM             │
│    (1 página por cliente + comparativo cross-cliente)   │
├─────────────────────────────────────────────────────────┤
│ 5. APLICAÇÃO LLM — Geração de Resumo CEO + explicações  │
│    (pós-cálculo, nunca substitui regra)                  │
├─────────────────────────────────────────────────────────┤
│ 4. ENGINE DE REGRAS — DRE/MIX/Sinaleiro/Vereditos       │
│    (Python puro, deterministicamente reprodutível)       │
├─────────────────────────────────────────────────────────┤
│ 3. CAMADA DE DADOS — PostgreSQL com 9 tabelas           │
│    (modelo único da verdade, normalizado)               │
├─────────────────────────────────────────────────────────┤
│ 2. PIPELINE DE INGESTÃO — ETL programado + uploads      │
│    (mensal SAP + diário Sales Hunter + semanal pricing) │
├─────────────────────────────────────────────────────────┤
│ 1. FONTES DE DADOS — ZSDFAT, LOG, Pricing, Mercos       │
│    (8 fontes, 6 internas + 2 externas)                  │
└─────────────────────────────────────────────────────────┘
```

---

## 4. FONTES DE DADOS (8 fontes)

| # | Fonte | Onde mora hoje | Frequência | Vetor que alimenta |
|---|-------|---------------|------------|-------------------|
| F1 | ZSDFAT (Faturamento SAP) | Excel mensal extraído por CFO | Mensal | Receita, devoluções, impostos, custo produto, frete SAP, comissão, equipe |
| F2 | LOG EFETIVADO — Verbas | `Verbas 2025 x 2026 - Por Cliente.xlsx` | Mensal | DRE L31 (verba real ano) |
| F3 | LOG EFETIVADO — Frete CT-e | `Frete por Cliente 2025.xlsx` | Mensal | DRE L33 (frete real CT-e) |
| F4 | LOG EFETIVADO — Contratos | `Controle de Contratos.xlsx` | Trimestral | DRE L30 (% ZDF2/ZPMH, vigência) |
| F5 | LOG EFETIVADO — Promotores | `Despesas Clientes 2025 V2.xlsx` | Mensal | DRE L35 (custo promotor real) |
| F6 | Último Praticado por SKU | `Projeção 2026.xlsx` aba Geral | Mensal | Mix 2025 (preço, custo, devolução por SKU/cliente) |
| F7 | Pricing mercado (concorrência) | Crawler externo (CEP Curitiba 80000-000) | Semanal | Cruzamento Cliente × Mercado |
| F8 | Sales Hunter / Mercos / Deskrio | Já no CRM via pipeline diário | Diário | Sell-out, ticket médio, frequência compra |

**Crítico:** F2-F5 hoje vivem em arquivos Excel separados por cliente. CFO atualiza manualmente. Primeira tarefa de engenharia: criar interface de upload + parser por fonte.

---

## 5. MODELO DE DADOS (PostgreSQL)

### 5.1 Tabelas

```sql
-- Já existe no CRM
cliente (id, codigo_sap, nome, grupo_chave, canal, uf, ranking_top, ativo)

-- Contratos
cliente_contrato (
  id, cliente_id, bp, razao_social, loja, canal,  -- canal: VAREJO/ATACADO
  status,  -- VIGENTE/VENCIDO/SUSPENSO
  desc_total_pct,  -- 14.0, 15.8 etc.
  desc_breakdown,  -- "12+3.8" (texto livre por enquanto)
  inicio_vigencia, fim_vigencia,
  prazo_pagamento_dias,
  faixa_desconto,  -- "10,01 A 15%"
  observacao
)

-- Verbas anuais (rollup por ano)
cliente_verbas_anual (
  cliente_id, ano, valor_brl,
  fonte  -- "ZSDFAT", "LOG_EFETIVADO", "MANUAL"
  PRIMARY KEY (cliente_id, ano, fonte)
)

-- Frete mensal CT-e
cliente_frete_mensal (
  cliente_id, ano, mes,
  qtd_ctes, valor_brl,
  fonte
)

-- Promotores mensal por agência
cliente_promotor_mensal (
  cliente_id, agencia,  -- "DINAMICA MERCHANDISING", "TB PROMOÇÕES"
  ano, mes, valor_brl
)

-- Último praticado por SKU/mês
cliente_sku_praticado (
  cliente_id, sku_codigo, ano, mes,
  preco_unitario, preco_caixa,
  custo_negociado,
  unidades_por_caixa,
  preco_tabela_referencia,
  desconto_pct,  -- (tabela - praticado) / tabela
  volume_caixas,
  faturamento_brl,
  devolucao_pct
)

-- DRE consolidado por período
cliente_dre_periodo (
  cliente_id, ano,
  linha,  -- 7,8,11,14,17,18,20,23,24,30,31,32,33,34,35,40,43,...
  conta,  -- "VALOR DE TABELA", "(-) DESCONTOS DE CONTRATO"...
  valor_param_sap,  -- o que SAP reporta (cinza/amarelo no DRE)
  valor_efetivado,  -- o que LOG indica (verde no DRE)
  pct_sobre_base,
  fonte_efetivado,  -- "LOG", "ZSDFAT.CM1", "MANUAL"
  observacao
)

-- Mercado: pricing de concorrência (alimenta cruzamento)
mercado_sku_preco (
  sku_familia,  -- "GRANOLA TRAD 250G", "BRIGADEIRO ZERO 200G"...
  categoria,
  canal,  -- "Site Oficial", "ML", "Bistek SC"...
  preco_brl, preco_por_100g,
  data_coleta,
  url_pdp,
  status  -- "Disponível", "Ruptura", "Não Distribuído"
)

mercado_categoria_veredito (
  categoria,
  mediana_vitao_por_100g,
  mediana_concorr_por_100g,
  top_concorrentes,  -- array
  veredito,  -- "COMPETITIVO", "PREMIUM", "CARO_DEMAIS", "BARATO_DEMAIS"
  faixa_pdv_recomendada,
  data_referencia
)

-- Anomalias detectadas (cache de regras)
cliente_anomalia (
  cliente_id,
  tipo,  -- "VERBA_CAIU_ABRUPTO", "FRETE_SEM_CTe", "MARGEM_NEGATIVA", "DEVOLUCAO_ALTA"
  severidade,  -- "CRITICO", "ATENCAO", "REVISAR"
  descricao,
  valor_observado, valor_esperado,
  detectada_em, status  -- "ABERTA", "RESOLVIDA", "IGNORADA"
)
```

### 5.2 Por que esse modelo

- **Separação param SAP × efetivado:** mesma estrutura do DRE atual. Permite calcular gap entre o que SAP "acha" e o que realmente acontece.
- **Granularidade mensal em frete e promotor:** detecta sazonalidade e gaps (Janeiro/Novembro = R$0 = anomalia).
- **Cliente_anomalia como tabela própria:** cache de detecções, histórico, status. Permite construir "fila de revisão".
- **Mercado separado de cliente:** pricing concorrência é dado externo, atualizado por crawler, não alimentado pelo CFO.

---

## 6. PIPELINE DE INGESTÃO

### 6.1 Fluxo

```
┌────────────────┐
│  CFO sobe      │   Upload mensal de:
│  arquivos      │   - ZSDFAT_<cliente>.xlsx
│                │   - Verbas.xlsx
│                │   - Frete.xlsx
│                │   - Contratos.xlsx
│                │   - Despesas.xlsx
│                │   - Projeção_<ano>.xlsx
└────┬───────────┘
     │
     ▼
┌────────────────┐
│  Parser por    │   parser_zsdfat.py
│  fonte         │   parser_verbas.py
│                │   parser_frete.py
│                │   parser_contratos.py
│                │   parser_promotores.py
│                │   parser_ult_praticado.py
└────┬───────────┘
     │
     ▼
┌────────────────┐
│  Validação +   │   - cliente_id existe? (lookup grupo_chave)
│  normalização  │   - datas batem?
│                │   - sinais (despesa <0, receita >0)?
│                │   - duplicatas?
└────┬───────────┘
     │
     ▼
┌────────────────┐
│  PostgreSQL    │   UPSERT em batch
│  staging       │   transação atômicas por arquivo
└────┬───────────┘
     │
     ▼
┌────────────────┐
│  Engine        │   recalcula DRE, sinaleiro, anomalias
│  trigger       │
└────────────────┘
```

### 6.2 Schedules

| Job | Cron | O que faz |
|-----|------|-----------|
| `etl_zsdfat_monthly` | dia 5 do mês 03:00 | Extrai SAP, parseia, sobe staging |
| `etl_log_efetivado` | dia 7 do mês 03:00 | Verbas + Frete + Promotores + Contratos |
| `etl_pricing_mercado` | sábado 04:00 | Crawler 49 SKUs × 23 canais |
| `engine_recalc_dre` | trigger pós-ETL | Recalcula DRE, sinaleiro, anomalias |
| `engine_anomalia_alert` | diário 08:00 | Email/notificação para anomalias críticas novas |

### 6.3 Parsers

Cada parser herda de `BaseParser`:

```python
class BaseParser:
    def validate_file(self, path) -> ValidationResult: ...
    def extract(self, path) -> List[Dict]: ...
    def normalize(self, raw) -> List[Model]: ...
    def upsert(self, models, session) -> int: ...
```

**Parser ZSDFAT** (mais complexo):
- 13 abas conhecidas, mapeamento aba → conta DRE
- Validação 24 checks (do playbook v3.0): nomes abas, type mismatch, datas seriais, sinais, IFERROR mascarados, hardcodes
- Saída: `cliente_dre_periodo` com colunas valor_param_sap

**Parser LOG | EFETIVADO** (4 sub-parsers):
- **Verbas:** extração da aba consolidada `Verbas` por grupo_chave
- **Frete:** extração da aba `Frete <Cliente>` mensal
- **Contratos:** extração da aba `Desc. Financeiro | Grupo Chave` filtrada
- **Promotores:** extração da aba `RESUMO` filtrada por nome cliente

---

## 7. ENGINE DE REGRAS

Camada determinística em Python puro. Reproduz exatamente o que fazemos hoje no Excel.

### 7.1 Calculadora DRE

```python
def calcula_dre_efetivado(cliente_id, ano):
    base = carrega_dre_param_sap(cliente_id, ano)
    log = carrega_log_efetivado(cliente_id, ano)
    fat_liquido = base['linha_18']
    
    # L30 — Desc. Contrato = % ZDF2 × Fat.Líquido
    contrato = log['contrato_vigente_no_ano']
    base['linha_30_efetivado'] = -1 * contrato.desc_total_pct/100 * fat_liquido
    
    # L31 — Verbas = valor anual real
    base['linha_31_efetivado'] = -1 * log['verbas_anual']
    
    # L32 — Representante = SAP Fat.CM1 (não tem efetivado)
    base['linha_32_efetivado'] = base['linha_32_param_sap']
    
    # L33 — Frete CT-e
    base['linha_33_efetivado'] = -1 * log['frete_total_ano']
    
    # L34 — Equipe = SAP Fat.CL1
    base['linha_34_efetivado'] = base['linha_34_param_sap']
    
    # L35 — Promotores = soma todas agências mensal
    base['linha_35_efetivado'] = -1 * log['promotor_total_ano']
    
    # Recalcula linha 36 (margem contribuição) com efetivado
    base['linha_36_efetivado'] = recalcula_mc(base)
    
    return base
```

### 7.2 Sinaleiro de SKU (6 status)

```python
def sinaleiro_sku(sku_data):
    if sku_data.custo == 0 or sku_data.preco_praticado == 0:
        return 'SEM_DADOS'
    if sku_data.devolucao_pct > 0.15:
        return 'DEVOLUCAO_NAO_CAPTURADA'
    if sku_data.margem_contribuicao_pct < 0:
        return 'SUBSTITUIR'
    if sku_data.margem_contribuicao_pct < 0.05:
        return 'AJUSTAR'
    if sku_data.margem_contribuicao_pct < 0.15:
        return 'REVISAR'
    return 'OK'
```

### 7.3 Detector de Anomalias (regras)

```python
ANOMALIAS = [
    ('VERBA_CAIU_ABRUPTO', 'Verbas caíram >50% YoY', 'CRITICO',
     lambda c: abs(yoy(c.verbas_n, c.verbas_n_minus_1)) > 0.5),
    ('FRETE_MES_ZERO', 'Frete R$0 em mês com fat. >0', 'ATENCAO',
     lambda c: any(m.frete == 0 and m.fat > 0 for m in c.meses)),
    ('CONTRATO_VENCIDO', 'Contrato vencido mas verba sendo cobrada', 'CRITICO',
     lambda c: c.contrato.fim < hoje() and c.verba_ano_atual > 0),
    ('MARGEM_GLOBAL_NEGATIVA', 'Margem global < 0', 'CRITICO',
     lambda c: c.dre.margem_global_pct < 0),
    ('SKU_DEVOLUCAO_ALTA', 'SKU com >20% devolução', 'ATENCAO',
     lambda c: any(s.dev > 0.20 for s in c.skus)),
    ('CUSTOS_SAP_RESIDUAIS', 'L32/L34 ainda usam SAP (não tem efetivado)', 'REVISAR',
     lambda c: c.dre.l32_fonte == 'SAP' or c.dre.l34_fonte == 'SAP'),
    ('PROMOTOR_ALTO', 'Promotor > 6% da receita', 'ATENCAO',
     lambda c: c.promotor_total / c.receita > 0.06),
    ('VERBA_ALTA', 'Verba > 8% da receita', 'ATENCAO',
     lambda c: c.verba_anual / c.receita > 0.08),
]

def detecta_anomalias(cliente):
    return [(cod, desc, sev) for cod, desc, sev, cond in ANOMALIAS if cond(cliente)]
```

### 7.4 Veredito por SKU vs Mercado

```python
def veredito_sku_vs_mercado(sku_cliente, mercado_categoria):
    cliente_pp100 = sku_cliente.preco_pdv / sku_cliente.gramatura * 100
    mediana = mercado_categoria.mediana_concorr_por_100g
    
    if cliente_pp100 < mediana * 0.85:
        return 'BARATO_DEMAIS', 'Subir preço — espaço de margem'
    if cliente_pp100 < mediana * 1.15:
        return 'COMPETITIVO', 'Manter preço'
    if cliente_pp100 < mediana * 1.30:
        return 'PREMIUM', 'Monitorar — risco de perda de share'
    return 'CARO_DEMAIS', 'Reduzir preço PDV ou retirar SKU'
```

---

## 8. CAMADA DE IA / LLM

**Regra de ouro: LLM não calcula. LLM explica e narra.**

### 8.1 Onde LLM entra

| Função | Input | Output | Modelo |
|--------|-------|--------|--------|
| Gerar Resumo CEO | DRE + 3 anomalias top + 5 ações | Texto 1 página formatado | Sonnet 4.5 |
| Justificar anomalia | Anomalia + contexto cliente | 2-3 linhas explicando | Haiku 4.5 |
| Sugerir ação | Anomalia + histórico cliente | Recomendação com impacto R$ | Sonnet 4.5 |
| Cross-cliente comparativo | Lista de N clientes + métricas | Insights comparativos | Sonnet 4.5 |
| Chat com a aba | Pergunta usuário + dados cliente | Resposta com citação | Sonnet 4.5 |

### 8.2 Onde LLM NÃO entra

- Cálculo de DRE (regra de negócio determinística)
- Sinaleiro de SKU (regra)
- Detecção de anomalia (regra disparada por threshold)
- Cruzamento numérico cliente × mercado (cálculo)

### 8.3 Prompt do Resumo CEO

```
Você é um analista financeiro sênior gerando o Resumo CEO de 1 página
para o cliente {{nome_cliente}}.

DADOS DRE 2025 EFETIVADO (R$):
{{dre_json}}

3 ANOMALIAS DETECTADAS:
{{anomalias_lista}}

5 AÇÕES RECOMENDADAS:
{{acoes_lista}}

VEREDITO GERAL: {{veredito}}

Escreva em 6 blocos:
1. Bottom Line (3 linhas, conclusão sem hedge)
2. Indicadores principais (5 KPIs)
3. 3 Riscos críticos com fonte
4. 5 Recomendações com prazo (Imediato/Curto/Médio)
5. Conclusão (margem atual → alvo)
6. Próximos passos (3 itens)

Tom: profissional direto, zero jargão, primeira frase carrega a resposta.
Não invente números — use apenas os fornecidos.
Formato: markdown limpo, sem emojis.
```

---

## 9. INTERFACE — Aba "Análise Crítica"

### 9.1 Layout principal (1 página)

```
┌────────────────────────────────────────────────────────────────┐
│ ← Cliente: KOCH-SC · Grupo: 06-DIRETO-KOCH-SC · TOP 10        │
│                                                                │
│ Margem Global 2025: -14,91%  [VEREDITO: RENEGOCIAR]           │
├────────────────────────────────────────────────────────────────┤
│ KPI STRIP (5)                                                 │
│ Faturamento  | Margem MC% | Verbas % | Frete %  | Promotor %  │
│ R$ 8,2M     | -14,91%    | 5,2%    | 0,8%     | 1,9%         │
├────────────────────────────────────────────────────────────────┤
│ TABS: [DRE 4 anos] [Mix SKUs] [Anomalias] [Recomendações]    │
│                                                                │
│ DRE 2023 | 2024 | 2025 | 2026 (parcial)                       │
│ Linha    | R$        | %     | Δ YoY  | Fonte                 │
│ ...                                                            │
├────────────────────────────────────────────────────────────────┤
│ 3 ANOMALIAS CRÍTICAS                                          │
│ ⚠ Verbas caíram 96% (R$320K→R$13K) — investigar migração     │
│ ⚠ 2 contratos vigentes simultâneos — segregar canal          │
│ ⚠ Frete Jan/Nov = R$0 — gap de extração?                     │
├────────────────────────────────────────────────────────────────┤
│ 5 AÇÕES PRIORITÁRIAS                                          │
│ 1. Renegociar Geleia Zero (R$ 22K impacto)                    │
│ 2. ...                                                         │
│ [Botão: Gerar Resumo CEO PDF] [Exportar Excel]                │
└────────────────────────────────────────────────────────────────┘
```

### 9.2 Comparativo cross-cliente

```
┌────────────────────────────────────────────────────────────────┐
│ COMPARATIVO 8 CLIENTES                                         │
│                                                                │
│ Cliente      | Fat 2025 | Margem | Verba% | Promotor% | Sinal │
│ Coelho Diniz | R$ 5,2M  | -14,9% | 11,5%  | 8,9%      | 🔴   │
│ Giassi       | R$ 8,1M  | ...    | ...    | ...       | 🟡   │
│ Angeloni     | R$ 6,4M  | ...    | ...    | ...       | 🟢   │
│ Koch         | R$ 8,2M  | -14,9% | 0,2%*  | 1,9%      | 🔴   │
│   *anomalia: caiu de 4,0% em 2024                              │
└────────────────────────────────────────────────────────────────┘
```

### 9.3 Stack de UI

- **Framework:** mesmo do CRM (React + TypeScript)
- **Charts:** Recharts (combo bar+line para evolução, pie para sinaleiro)
- **Design:** baseline definido em `html-dashboard-design` skill (Stripe/Linear/Vercel)
- **Tabela:** virtualizada para SKUs >100

---

## 10. MVP vs ROADMAP

### MVP (Sprint 1 — 2 semanas)

**Objetivo:** substituir o trabalho manual atual para 1 cliente.

- [ ] 6 tabelas básicas no PostgreSQL
- [ ] Upload manual dos 6 arquivos Excel via interface
- [ ] Parser ZSDFAT + 4 parsers LOG | EFETIVADO
- [ ] Engine: cálculo DRE L30-L35 efetivado
- [ ] UI: 1 página com DRE + KPI strip + lista anomalias (regras hardcoded)
- [ ] Botão "Exportar Excel" (replica formato Sidecar v2 atual)

**Critério de aceite:** Coelho Diniz aberto no CRM bate 100% com Excel manual atual.

### Sprint 2 — Cruzamento Mercado (2 semanas)

- [ ] Tabela mercado_sku_preco + crawler semanal
- [ ] Engine: veredito SKU vs mercado
- [ ] UI: aba "Cruzamento Mercado" no cliente
- [ ] LLM: gerador Resumo CEO

### Sprint 3 — Cross-Cliente (2 semanas)

- [ ] Tela comparativo cross-cliente
- [ ] Anomalia inteligente (LLM justifica)
- [ ] Histórico evolução (3 anos por cliente)

### Sprint 4 — Automação (2 semanas)

- [ ] ETL programado (cron)
- [ ] Notificação anomalias (email/Slack)
- [ ] Aceite anomalia / IGNORADA / RESOLVIDA com auditoria

### Sprint 5 — Acabamento

- [ ] Chat com a aba (LLM com RAG nos dados do cliente)
- [ ] Exportação PDF Resumo CEO
- [ ] Versionamento (snapshot mensal de cada análise)

---

## 11. ANÁLISE DE FALHA

| Cenário | Sintoma | Mitigação |
|---------|---------|-----------|
| Parser ZSDFAT quebra com nova aba SAP | Erro de extração | Schema validation + fallback "ABA NÃO RECONHECIDA" |
| LOG EFETIVADO de cliente novo não tem aba dedicada | Cliente sem dados | Fallback para param SAP com flag PENDENTE |
| Crawler de pricing bloqueado por WAF | Mercado desatualizado | Cache 30 dias + alerta |
| Verba "caiu 96%" é real, não anomalia | Falso positivo | Aceite manual com justificativa |
| LLM alucina número no Resumo CEO | Texto com R$ errado | Validação pós-geração: regex de R$ deve bater com dados injetados |

**Custo de reverter:**
- **MVP:** feature flag, desligado = volta pro Excel manual (4-6h trabalho)
- **Sprint 3+:** dados ficam, UI desligada, sem perda

---

## 12. PROMPT DE HANDOFF PRO EXECUTOR

```
Contexto: estou implementando a feature "Análise Crítica do Cliente" no CRM
VITAO360. Já temos o processo manual rodando em Excel: ZSDFAT (SAP) +
LOG | EFETIVADO (Verbas, Frete, Contratos, Promotores) + Último Praticado
+ Pricing de Mercado.

Documentação completa: ler SPEC_FEATURE_ANALISE_CRITICA_CRM_VITAO360.md

Estado atual do CRM: stack Python + TypeScript + PostgreSQL + Redis. Já tem
aba DRE em construção. Pipeline diário extrai Sales Hunter + Mercos + Deskrio.

Próxima tarefa: MVP Sprint 1.
- Criar 6 tabelas (cliente_contrato, cliente_verbas_anual, cliente_frete_mensal,
  cliente_promotor_mensal, cliente_sku_praticado, cliente_dre_periodo)
- Parser ZSDFAT (referência: PLAYBOOK_MESTRE)
- 4 parsers LOG | EFETIVADO
- Engine DRE: calcular linhas 30-35 efetivadas
- UI: 1 página por cliente com DRE 4 anos + KPI strip + lista anomalias

Critério de aceite: abrir Coelho Diniz no CRM e bater 100% com o Sidecar
manual Análise Crítica - Coelho Diniz - Forense.xlsx.

Restrições:
- Zero invenção numérica. Se dado não existe, marcar PENDENTE.
- DRE separa explicitamente "param SAP" e "efetivado".
- Sinaleiro de SKU = regra determinística, não LLM.
- LLM só gera Resumo CEO no final, com prompt fechado e validação pós-geração.

Faça em ondas:
Onda 1: schema PostgreSQL + migrations
Onda 2: parsers + testes unitários
Onda 3: engine DRE + testes (Coelho Diniz como golden master)
Onda 4: API REST (GET /clientes/:id/analise-critica)
Onda 5: UI React (1 página)
```

---

## 13. CHECKLIST PRÉ-HANDOFF

- [ ] Esse spec está num lugar permanente (`/CRM-VITAO360/`)
- [ ] Anexar 1 Excel de exemplo de cada fonte na pasta `examples/`
- [ ] Ter o Coelho Diniz Forense como "golden master"
- [ ] Schema PostgreSQL revisado (índices em cliente_id, ano, mes)
- [ ] Decidir: ETL programado roda no Render/Vercel/AWS?
- [ ] Decidir: pricing crawler vai usar Claude in Chrome ou Playwright headless?
- [ ] Definir feature flag: `ANALISE_CRITICA_HABILITADA` por cliente

---

## 14. NOTAS FINAIS

**O que esse spec NÃO cobre:**
- Autenticação / autorização (assume que CRM já tem RBAC)
- Migração de clientes legados (assume que cliente_id já existe)
- Integração com Sales Hunter / Mercos (já existe, só consome)
- Histórico antes de 2023 (escopo inicial: 2023-2026)

**O que pode ser adicionado depois:**
- Forecast 2027 baseado em tendência 2023-2026
- Simulador "e se eu reduzir a verba do cliente em 2pp?"
- Alertas push para gerentes regionais
- Comparativo benchmarks setor (vs Mãe Terra, vs Jasmine)

---

**Versão:** 1.0 — 28/04/2026
**Baseada em:** Playbook Análise Crítica v3.0, Skill v3, Sidecars v2 Koch + Angeloni, Mestre v7 Pricing Diretoria, Memória CRM VITAO360.
**Próxima revisão:** após Sprint 1, com retrospectiva.

---

## RELAÇÃO COM SPECS ANTERIORES

- **SPEC_DDE_CLIENTE.md** → SUPERSEDED por esta spec. A DDE cascata (Receita → Margem → Resultado) está contida no Bloco DRE desta spec, mas aqui é mais completa: inclui param SAP vs efetivado, 8 fontes, engine de regras, e sinaleiro.
- **SPEC_ANALISE_CRITICA_VIVA.md** → SUPERSEDED. Era um dashboard de métricas, não uma análise real.
