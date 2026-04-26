# B1.1 — Reconciliação Faturamento R$ 5.0M de Diferença
**Data:** 2026-04-26  
**Executor:** @data-engineer  
**Banco:** data/crm_vitao360.db (SQLite 21MB)  
**Classificação:** REAL (somente queries SELECT em dados existentes)

---

## 1. Schemas Inspecionados

### clientes (8.164 rows)
Colunas relevantes:
- `cnpj` VARCHAR(14) — string 14d, zero-padded — R5 OK
- `faturamento_total` FLOAT — ver diagnóstico abaixo
- `canal_id` INTEGER FK → canais (7 canais: INTERNO, FOOD_SERVICE, DIRETO, INDIRETO, FARMA, BODY, DIGITAL)
- `consultor` VARCHAR(50) — MANU/LARISSA/DAIANE/JULIO/LEGADO
- `created_at` DATETIME
- CNPJ como float: 0 casos — OK
- CNPJ com length != 14: 0 casos — OK
- CNPJs duplicados: 0 — OK

### vendas (6.944 rows)
Colunas relevantes:
- `cnpj` VARCHAR(14) — chave de join
- `data_pedido` DATE — usada para corte temporal
- `valor_pedido` FLOAT — valor da venda
- `fonte` VARCHAR(20) — 'MERCOS' (2025) ou 'SAP' (2026-04)
- `consultor` VARCHAR(50)
- `classificacao_3tier` VARCHAR(15) — todos 'REAL'
- `status_pedido` VARCHAR(20)
- `mes_referencia` VARCHAR(7)

### import_jobs (4 rows)
Todos do tipo SALES_HUNTER, data 2026-04-25. Job 1 inseriu 59.827 registros (populou vendas + clientes via ingest_sales_hunter.py). Jobs 2-4 = 0 inseridos (idempotência OK).

### venda_itens (45.833 rows)
Detalhe de NF. Não usada na reconciliação de faturamento (granularidade não necessária).

---

## 2. Faturamento por Ano e Canal

### MERCOS 2025 (fonte principal, dados reais)

| Canal       | Clientes | Pedidos | Faturamento 2025    |
|-------------|----------|---------|---------------------|
| DIRETO      | 384      | 726     | R$ 1.397.090,73     |
| INTERNO     | 33       | 102     | R$ 467.904,10       |
| sem canal   | 70       | 101     | R$ 237.424,89       |
| **TOTAL**   | **487**  | **929** | **R$ 2.102.419,72** |

**Baseline PAINEL CEO 2025: R$ 2.091.000 → Diferença: +R$ 11.419 (+0,5%) — dentro da tolerância.**

### MERCOS 2026 Q1 (Jan-Mar)

| Canal       | Clientes | Pedidos | Faturamento Q1 2026 |
|-------------|----------|---------|---------------------|
| DIRETO      | 93       | 181     | R$ 272.976,96       |
| INTERNO     | 28       | 53      | R$ 244.276,69       |
| sem canal   | 31       | 68      | R$ 103.914,36       |
| **TOTAL**   | **152**  | **302** | **R$ 621.168,01**   |

> Nota: Q1 esperado R$ 459.465 é divergente (+35,2%). Investigar: a referência CLAUDE.md pode ser apenas canal DIRETO + sem canal (R$ 376.891) ou pode incluir somente consultores ativos sem canal INTERNO. O INTELIGENCIA_NEGOCIO_CRM360 cita R$ 415.904. Requerer esclarecimento L3 antes de usar Q1 em produção.

### SAP abril/2026 (DUPLICADO — ver flag)

| Status   | Pedidos (banco) | Valor (banco) | Pedidos reais | Valor real  |
|----------|-----------------|---------------|---------------|-------------|
| FATURADO | 5.711           | R$ 11.744.185 | ~2.855        | R$ 5.872.092|

---

## 3. O que clientes.faturamento_total Realmente Significa

**Conclusão: faturamento_total = faturamento SAP de ABRIL/2026 (período do relatório), NÃO histórico lifetime.**

Evidência direta:
- fat_cliente.xlsx coluna 16 = "Faturado abril/2026" e coluna 22 = "Total faturado"
- SUM(col16) = SUM(col22) = R$ 5.689.261 (razão = 1,00x exato)
- O relatório SAP Sales Hunter foi gerado exclusivamente para o período 01/04/2026–24/04/2026
- Para fat_empresa: "Venda abril/2026" == "Total venda" (mesmos valores confirmados)
- fat_nf_det: range de datas 01/04/2026 a 24/04/2026 APENAS (17 dias úteis)

**Por que o banco mostra R$ 7,1M em vez de R$ 5,7M do fat_cliente?**  
O banco tem 8.164 clientes vs 5.514 no fat_cliente. Os 2.650 extras (Deskrio/Mercos sem SAP em abril) acumulam faturamento_total de fontes anteriores não sobrescritas.

---

## 4. Flag R4/R5/R8 — Violações Detectadas

### FLAG BLOQUEANTE — Two-Base violada em `vendas`
**fat_nf_det_cwb e fat_nf_det_vv são arquivos IDÊNTICOS** (mesmo tamanho 2.472.660 bytes, mesmo conteúdo linha a linha). O script ingest_sales_hunter.py importa AMBOS sem deduplicação por numero_pedido no INSERT.

Resultado:
- 4.950 de 5.519 clientes (89,7%) têm `SUM(vendas.valor_pedido)` = exatamente 2× seu `faturamento_total`
- vendas SAP banco: R$ 11.744.185 = exatamente 2× fat_empresa.venda (R$ 5.872.092)
- Pedidos duplicados confirmados (ex.: 0001236861 aparece 3×)

**Impacto: qualquer endpoint que use `SUM(vendas.valor_pedido WHERE fonte='SAP')` retorna o dobro do real.**

### FLAG INFORMATIVO — clientes.faturamento_total semântica incorreta
O nome `faturamento_total` induz a crer que é histórico acumulado. É, na verdade, o faturamento do mês de extração (abril/2026). Usando essa coluna como "faturamento anual" ou "histórico" produz erro conceitual grave.

### R5 — CNPJ: OK
- 0 CNPJs como float
- 0 CNPJs com length != 14
- 0 CNPJs duplicados em clientes

### R8 — Dados fabricados: Não detectados
Todos os registros de vendas têm `classificacao_3tier = 'REAL'`. Nenhum ALUCINAÇÃO encontrado nas tabelas auditadas.

---

## 5. Top 10 Clientes DIRETO 2025

| # | CNPJ           | Nome                          | UF | Consultor | Pedidos | Faturamento 2025 |
|---|----------------|-------------------------------|----|-----------|---------|--------------------|
| 1 | 41418074000120 | SIMPLES E SAUDAVEL COMERCIO   | SP | LARISSA   | 9       | R$ 42.023,18       |
| 2 | 00939085000178 | VIVA PORTO DE GALINHAS RESORT | PE | LARISSA   | 6       | R$ 39.087,21       |
| 3 | 15265760000106 | A CEREALISSIMA                | GO | LARISSA   | 7       | R$ 34.694,16       |
| 4 | 08895369000111 | SOLAR PORTO DE GALINHAS       | PE | LARISSA   | 5       | R$ 30.261,47       |
| 5 | 55615538000283 | CASA HIRATA - SUPERMERCADO    | SP | MANU      | 7       | R$ 26.475,77       |
| 6 | 34901637000170 | SALES SUPERMERCADO            | PA | LARISSA   | 7       | R$ 26.402,91       |
| 7 | 34924371000181 | SOARES DISTRIBUIDORA          | PR | MANU      | 1       | R$ 25.920,00       |
| 8 | 41887017000190 | CHOKOLATEN                    | SC | MANU      | 3       | R$ 25.239,48       |
| 9 | 31545180000110 | NATURALIS PRODUTOS NATURAIS   | SC | MANU      | 7       | R$ 22.540,65       |
|10 | 14133092000192 | BESCO                         | SC | MANU      | 3       | R$ 22.144,89       |

---

## 6. Diagnóstico: O Que Cada Coluna/Tabela Realmente Significa

| Fonte                          | O que é                              | Período     | Tier   |
|--------------------------------|--------------------------------------|-------------|--------|
| `clientes.faturamento_total`   | Faturamento SAP do mês de extração   | Abril/2026  | REAL   |
| `vendas WHERE fonte='MERCOS'`  | Pedidos reais por data               | 2025–2026   | REAL   |
| `vendas WHERE fonte='SAP'`     | NFs abril/2026 **duplicadas 2×**     | Abril/2026  | REAL*  |
| `SUM(clientes.faturamento_total)` | R$ 7,1M — NÃO é faturamento 2025 | Abr/2026   | Enganoso|
| `SUM(vendas.valor_pedido WHERE year=2025)` | R$ 2,1M — faturamento anual real | 2025 | REAL |

*SAP REAL individualmente mas DUPLICADO no banco — não usar SUM direto.

---

## 7. Recomendação Técnica

**Para "faturamento 2025" no CRM ativo, usar:**
```sql
SELECT SUM(valor_pedido)
FROM vendas
WHERE strftime('%Y', data_pedido) = '2025'
  AND fonte = 'MERCOS'
  AND classificacao_3tier = 'REAL'
```
Resultado: R$ 2.102.419 — dentro do baseline (±0,5%).

**NÃO usar `clientes.faturamento_total` para representar faturamento anual ou histórico.**

**Ações necessárias (requerem aprovação L3):**

1. **DEDUPLICAR vendas SAP**: remover duplicatas de fat_nf_det_vv (manter apenas CWB ou dedupliar por numero_pedido + cnpj + data + valor). Impacto: remove ~2.855 pedidos e ~R$ 5,87M do banco.

2. **RENOMEAR clientes.faturamento_total** para `faturamento_mes_extracao` e adicionar coluna `faturamento_2025` calculada via `SUM(vendas WHERE year=2025)`. Isto requer migração de schema (L3).

3. **Alternativa sem migração (L1/L2)**: nos endpoints de API, usar `SUM(vendas.valor_pedido WHERE year=2025 AND fonte='MERCOS')` on-the-fly em vez de `clientes.faturamento_total`. Zero risco de dados, zero migração.

**Recomendação preferida: Opção 3 (on-the-fly via vendas) para faturamento anual nos endpoints.** Mantém faturamento_total como cache do último período SAP. Correção da duplicação SAP fica pendente de L3.

---

## 7. Investigação L3#5 — Causa Raiz Duplicação SAP

**Data:** 2026-04-26  
**Executor:** @data-engineer  
**Status:** SOMENTE LEITURA — banco não modificado  

---

### 7.1 Hipótese Confirmada: A

**CWB e VV retornam dataset 100% idêntico (mesmos pedidos, mesmos itens, mesmo valor).**

Evidências diretas:

- `fat_cliente_cwb` vs `fat_cliente_vv`: 5.503 CNPJs × 100% overlap, todos os valores numéricos iguais. Diferenças apenas em col26-col29 (campos de representante regional — IDs de rotas de entrega distintos por filial, dados não usados no ingest). Conteúdo financeiro: idêntico.
- `fat_nf_det_cwb` vs `fat_nf_det_vv`: 6.397 pedidos únicos × 100% overlap. 24.769 pares (pedido, item) × 100% idênticos. col5 (valor_unit) SUM = R$ 5.266.898,61 em ambos. Diferenças apenas em col22-col25 (campos de representante/rota).
- `fat_empresa_cwb` vs `fat_empresa_vv`: ambos retornam **"VITAO - Curitiba", Centro 7000**, venda = R$ 5.872.092,97. O endpoint VV não retorna "VITAO - Varginha" — retorna a mesma filial CWB.

**Conclusão: os endpoints `/cwb` e `/vv` do Sales Hunter entregam o consolidado nacional da empresa VITAO (Centro 7000 — Curitiba). Não existe filtro por filial no servidor. A distinção CWB/VV é cosmética no nome do arquivo; o dataset é um.**

---

### 7.2 Mecanismo Exato do Bug (Phase 4 — linhas 873-891)

```python
# Bug: pedidos_buffer agrupa por chave (cnpj, pedido, data) — correto
# PORÉM: para CWB E VV (mesmos itens), executa:
pedidos_buffer[chave]["valor_total"] += valor_item   # acumula 2x
pedidos_buffer[chave]["itens"].append(...)            # duplica lista
```

- CWB processa: chave criada, valor_total = R$X, itens = [N itens]  
- VV processa: chave já existe, valor_total += R$X → R$2X, itens += [mesmos N itens]  
- Resultado: 1 venda inserida com valor 2× real, e venda_itens com 2× os itens

O buffer em memória **deduplicou os registros de venda** (5.711 rows, não 11.422), mas **acumulou o valor e os itens duas vezes** antes da inserção.

---

### 7.3 Números Confirmados

| Métrica | Banco atual | Real (1×) | Excesso |
|---------|-------------|-----------|---------|
| Vendas SAP (rows) | 5.711 | 5.711 | 0 (count OK) |
| Vendas SAP (valor) | R$ 11.744.185,94 | R$ 5.872.092,97 | R$ 5.872.092,97 |
| venda_itens SAP (rows) | 42.212 | ~21.106 | ~21.106 |
| venda_itens SAP (valor) | R$ 11.744.185,94 | R$ 5.872.092,97 | R$ 5.872.092,97 |
| Ratio banco/real | **2,0000×** | 1,0000× | — |

fat_empresa oficial (fonte primária): R$ 5.872.092,97 → banco tem exatamente o dobro.

---

### 7.4 Plano de Remediação (requer aprovação L3 para execução)

**Pré-condição obrigatória: backup antes de qualquer operação destrutiva.**

```bash
# Backup pré-remediação
cp data/crm_vitao360.db data/backups/crm_vitao360_pre_remediation_$(date +%Y%m%d_%H%M%S).db
```

**Passo 1 — Corrigir ingest_sales_hunter.py (fix no buffer, L2)**

Adicionar deduplicação de itens por `(cod_material, quantidade, valor_item)` dentro de cada chave de pedido. O script já deduplica a chave do pedido; falta ignorar itens duplicados de VV quando CWB já os inseriu:

```python
# Em phase_4_vendas, após: chave_venda = (cnpj, cod_pedido, data_pedido)
# Adicionar controle de itens já vistos por chave:
if chave_venda not in pedidos_buffer:
    pedidos_buffer[chave_venda] = {
        "valor_total": 0.0,
        "itens": [],
        "itens_vistos": set(),  # NOVO: dedup de itens
    }

# Chave do item: (cod_material, seq_item, quantidade)
chave_item = (cod_material, to_str(row[3], max_len=10), qty)
if chave_item in pedidos_buffer[chave_venda]["itens_vistos"]:
    continue  # NOVO: pula item duplicado de VV
pedidos_buffer[chave_venda]["itens_vistos"].add(chave_item)
pedidos_buffer[chave_venda]["valor_total"] += valor_item
pedidos_buffer[chave_venda]["itens"].append(...)
```

Alternativa mais simples (L1/L2): processar apenas `fat_nf_det_cwb`, ignorar `fat_nf_det_vv` enquanto os dois forem idênticos. Adicionar log de aviso explícito se tamanhos diferirem (sinal de que VV virou dataset independente).

**Passo 2 — Limpar banco (L3 — DELETE destrutivo)**

```sql
-- Remover venda_itens SAP (FK cascade ou delete direto)
DELETE FROM venda_itens 
WHERE venda_id IN (SELECT id FROM vendas WHERE fonte = 'SAP');

-- Remover vendas SAP
DELETE FROM vendas WHERE fonte = 'SAP';

-- Reset faturamento_total em clientes (será repovoado pelo re-ingest)
UPDATE clientes SET faturamento_total = 0 WHERE faturamento_total > 0;
```

**Passo 3 — Re-ingest com script corrigido**

```bash
python scripts/ingest_sales_hunter.py --date 2026-04-25
```

**Passo 4 — Validação pós-remediação**

```sql
-- Deve retornar ~R$ 5.872.093 (±0,5%)
SELECT SUM(valor_pedido) FROM vendas WHERE fonte = 'SAP';

-- Deve retornar ~5.711 pedidos, ~21.000 itens
SELECT COUNT(*) FROM vendas WHERE fonte = 'SAP';
SELECT COUNT(*) FROM venda_itens vi 
JOIN vendas v ON vi.venda_id = v.id WHERE v.fonte = 'SAP';
```

**Rollback:** restaurar backup com `cp data/backups/crm_vitao360_pre_remediation_*.db data/crm_vitao360.db`

---

### 7.5 venda_itens — Duplicação Confirmada

- venda_itens SAP banco: **42.212 rows** (R$ 11.744.185,94)  
- venda_itens SAP real esperado: **~21.106 rows** (R$ 5.872.092,97)  
- Ratio: **2,0000×** — mesma duplicação que vendas  
- venda_itens Mercos (não afetado): 3.621 rows — correto  

---

### 7.6 Estimativa de Tempo de Execução

| Passo | Estimativa | Risco |
|-------|-----------|-------|
| Backup | 30 seg | Baixo |
| Corrigir ingest_sales_hunter.py | 30 min | Médio (testar com --dry-run) |
| DELETE vendas+itens SAP | < 5 seg | Alto (irreversível sem backup) |
| Re-ingest --date 2026-04-25 | 3-5 min | Baixo |
| Validação | 10 min | Baixo |
| **Total** | **~45-50 min** | — |

---

### 7.7 Riscos

- **Risco alto**: DELETE sem backup → perda permanente de dados. Mitigação: backup obrigatório antes.
- **Risco médio**: script corrigido pode ter edge case não testado. Mitigação: rodar `--dry-run` primeiro, validar contagem vs fat_empresa.
- **Risco baixo**: endpoints de API que usam `SUM(vendas.valor_pedido WHERE fonte='SAP')` já retornam 2× o real — após remediação passarão a retornar o valor correto. Verificar se algum frontend usa esse valor absoluto e espera o valor dobrado.
- **Sem risco**: vendas MERCOS não afetadas (confirmado — fonte separada, import independente).

---

### 7.8 FLAG — Achado Adicional

**Importante para fix futuro:** os campos col22-col25 de fat_nf_det (código/nome do representante regional de nível 1 e 2) diferem em **35.192 células** entre CWB e VV após ordenação por pedido+item. Isso indica que o Sales Hunter atribui diferentes representantes regionais dependendo do endpoint consultado, mesmo retornando os mesmos pedidos. Este campo não é usado atualmente pelo ingest — mas se algum dia for utilizado, a lógica de qual arquivo usar (CWB ou VV) precisará ser definida.

---

*Seção adicionada por @data-engineer em 2026-04-26 — Investigação L3#5. Somente queries SELECT — banco não modificado.*
