# CARTEIRA BLUEPRINT -- CRM VITAO360

> Fonte: CRM_VITAO360 INTELIGENTE FINAL OK .xlsx | Aba CARTEIRA
> Extraido por: @data-engineer -- CRM VITAO360
> Versao: 1.0

---

## 1. VISAO GERAL

A aba **CARTEIRA** e o motor central do CRM VITAO360. Funciona como painel unificado que consolida dados de tres fontes primarias (Mercos, SAP, CRM/DRAFT 2) em uma unica visao por cliente.

| Metrica | Valor |
|---------|-------|
| Total de colunas | 144 |
| Total de formulas | 180.477 |
| Total de linhas de dados | 1.590 |
| Grupos de colunas | 14 |
| Colunas com formula (dados) | 114 |
| Colunas de cabecalho com formula | 36 |
| Linha maxima | 1.593 |

---

## 2. MAPA DE GRUPOS

| # | Grupo | Range | Qtd Colunas | Subgrupos |
|---|-------|-------|-------------|-----------|
| 1 | MERCOS | A-AA | 27 | ANCORA, IDENTIDADE, REDE, EQUIPE, STATUS, COMPRA, ECOMMERCE, ATENDIMENTO MERCOS |
| 2 | VENDAS 2025 | AB-AN | 13 | TOTAL 2025, 2025-01 a 2025-12 |
| 3 | VENDAS 2026 | AO-BA | 13 | TOTAL 2026, 2026-01 a 2026-12 |
| 4 | VENDAS | BB-BI | 8 | RECORRENCIA, TIPO CLIENTE |
| 5 | FUNIL | BJ-CB | 19 | ANCORA, PIPELINE, PERFIL, MATURIDADE, CONVERSAO, ACAO, SINAL |
| 6 | SAP | CC-CE | 3 | CODIGO DO CLIENTE, CNPJ, RAZAO SOCIAL |
| 7 | STATUS SAP | CF-CH | 3 | CADASTRO, ATENDIMENTO, BLOQUEIO |
| 8 | DADOS CADASTRAIS SAP | CI-CQ | 9 | DESC GRUPO CLIENTE, ZP GERENTE NAC., ZR REPRESENTANTE, ZV VEND INTERNO, CANAL, TIPO CLIENTE, MACROREGIAO, MICROREGIAO, GRUPO CHAVE |
| 9 | ANUAL | CR-CT | 3 | META, REALIZADO, % ALCANCADO |
| 10 | Q1 | CU-CW | 3 | META SAP TRI, META IGUALIT. TRI, % ALCANCADO TRI |
| 11 | JANEIRO | CX-DH | 11 | META SAP, META IGUALIT., DATA PEDIDO, JUSTIFICATIVA (SEM 1-5), REALIZADO, % SAP |
| 12 | FEVEREIRO | DI-DS | 11 | META SAP, META IGUALIT., % IGUALIT., DATA PEDIDO, JUSTIFICATIVA (SEM 1-5), REALIZADO, % SAP |
| 13 | MARCO | DT-ED | 11 | META SAP, META IGUALIT., % IGUALIT., DATA PEDIDO, JUSTIFICATIVA (SEM 1-5), REALIZADO, % SAP |
| 14 | Q1 (ANCORA) | EE-EN | 10 | REALIZADO TRI, % TRI SAP, SCORE & PRIORIDADE v2 (URGENCIA 30%, VALOR 25%, FOLLOW-UP 20%, SINAL 15%, TENTATIVA 5%, SITUACAO 5%, SCORE, PRIORIDADE v2) |

---

## 3. MAPA DE COLUNAS DETALHADO

### Grupo 1: MERCOS (A-AA, 27 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| A | NOME FANTASIA | ANCORA |
| B | CNPJ | IDENTIDADE |
| C | RAZAO SOCIAL | IDENTIDADE |
| D | UF | IDENTIDADE |
| E | CIDADE | IDENTIDADE |
| F | EMAIL | IDENTIDADE |
| G | TELEFONE | IDENTIDADE |
| H | DATA CADASTRO | IDENTIDADE |
| I | REDE REGIONAL | REDE |
| J | ULT REGISTRO MERCOS | REDE |
| K | CONSULTOR | EQUIPE |
| L | VENDEDOR ULTIMO PEDIDO | EQUIPE |
| M | SITUACAO | STATUS |
| N | PRIORIDADE | STATUS |
| O | DIAS SEM COMPRA | COMPRA |
| P | DATA ULTIMO PEDIDO | COMPRA |
| Q | VALOR ULTIMO PEDIDO | COMPRA |
| R | CICLO MEDIO | COMPRA |
| S | ACESSO B2B | ECOMMERCE |
| T | ACESSOS PORTAL | ECOMMERCE |
| U | ITENS CARRINHO | ECOMMERCE |
| V | VALOR B2B | ECOMMERCE |
| W | OPORTUNIDADE | ECOMMERCE |
| X | TIPO CONTATO | ATENDIMENTO MERCOS |
| Y | RESULTADO | ATENDIMENTO MERCOS |
| Z | MOTIVO | ATENDIMENTO MERCOS |
| AA | DESCRICAO | ATENDIMENTO MERCOS |

### Grupo 2: VENDAS 2025 (AB-AN, 13 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| AB | TOTAL 2025 (formula: SUM) | TOTAL 2025 |
| AC | Jan/25 | 2025-01 |
| AD | Fev/25 | 2025-02 |
| AE | Mar/25 | 2025-03 |
| AF | Abr/25 | 2025-04 |
| AG | Mai/25 | 2025-05 |
| AH | Jun/25 | 2025-06 |
| AI | Jul/25 | 2025-07 |
| AJ | Ago/25 | 2025-08 |
| AK | Set/25 | 2025-09 |
| AL | Out/25 | 2025-10 |
| AM | Nov/25 | 2025-11 |
| AN | Dez/25 | 2025-12 |

### Grupo 3: VENDAS 2026 (AO-BA, 13 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| AO | TOTAL 2026 (formula: SUM) | TOTAL 2026 |
| AP | Jan/26 | 2026-01 |
| AQ | Fev/26 | 2026-02 |
| AR | Mar/26 | 2026-03 |
| AS | Abr/26 | 2026-04 |
| AT | Mai/26 | 2026-05 |
| AU | Jun/26 | 2026-06 |
| AV | Jul/26 | 2026-07 |
| AW | Ago/26 | 2026-08 |
| AX | Set/26 | 2026-09 |
| AY | Out/26 | 2026-10 |
| AZ | Nov/26 | 2026-11 |
| BA | Dez/26 | 2026-12 |

### Grupo 4: VENDAS (BB-BI, 8 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| BB | TICKET MEDIO | RECORRENCIA |
| BC | (tipo cliente) | TIPO CLIENTE |
| BD | No COMPRAS | RECORRENCIA |
| BE | CURVA ABC | RECORRENCIA |
| BF | MESES POSITIVADO | RECORRENCIA |
| BG | MEDIA MENSAL | RECORRENCIA |
| BH | TICKET MEDIO | RECORRENCIA |
| BI | MESES LISTA | RECORRENCIA |

### Grupo 5: FUNIL (BJ-CB, 19 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| BJ | ESTAGIO FUNIL | ANCORA |
| BK | PROX FOLLOWUP | PIPELINE |
| BL | DATA ULT ATENDIMENTO | PIPELINE |
| BM | ACAO FUTURA | (sem subgrupo) |
| BN | ULTIMO RESULTADO | PIPELINE |
| BO | MOTIVO | PIPELINE |
| BP | TIPO CLIENTE | PERFIL |
| BQ | TENTATIVA | PERFIL |
| BR | FASE | MATURIDADE |
| BS | ULTIMA RECOMPRA | MATURIDADE |
| BT | TEMPERATURA | CONVERSAO |
| BU | DIAS ATE CONVERSAO | CONVERSAO |
| BV | DATA 1o CONTATO | CONVERSAO |
| BW | DATA 1o ORCAMENTO | CONVERSAO |
| BX | DATA 1a VENDA | CONVERSAO |
| BY | TOTAL TENTATIVAS | CONVERSAO |
| BZ | PROX ACAO | ACAO |
| CA | ACAO DETALHADA | ACAO |
| CB | SINALEIRO | SINAL |

### Grupo 6: SAP (CC-CE, 3 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| CC | CODIGO DO CLIENTE | CODIGO DO CLIENTE |
| CD | CNPJ | CNPJ |
| CE | RAZAO SOCIAL | RAZAO SOCIAL |

### Grupo 7: STATUS SAP (CF-CH, 3 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| CF | CADASTRO | CADASTRO |
| CG | ATENDIMENTO | ATENDIMENTO |
| CH | BLOQUEIO | BLOQUEIO |

### Grupo 8: DADOS CADASTRAIS SAP (CI-CQ, 9 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| CI | DESCRICAO GRUPO CLIENTE | DESC GRUPO CLIENTE |
| CJ | ZP NOME GERENTE NACIONAL | GERENTE NACIONAL |
| CK | ZR NOME REPRESENTANTE | REPRESENTANTE |
| CL | ZV NOME VEND INTERNO | VEND INTERNO |
| CM | 01 NOME DO CANAL | CANAL |
| CN | 02 NOME TIPO CLIENTE | TIPO CLIENTE |
| CO | 03 NOME MACROREGIAO | MACROREGIAO |
| CP | 04 NOME MICROREGIAO | MICROREGIAO |
| CQ | 06 NOME GRUPO CHAVE | GRUPO CHAVE |

### Grupo 9: ANUAL (CR-CT, 3 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| CR | META (XLOOKUP PROJECAO) | META |
| CS | REALIZADO (SUM AP:BA) | REALIZADO |
| CT | % ALCANCADO (CS/CR) | % ALCANCADO |

### Grupo 10: Q1 (CU-CW, 3 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| CU | META SAP TRI (XLOOKUP PROJECAO M+N+O) | META SAP TRI |
| CV | META IGUALIT. TRI (XLOOKUP PROJECAO BC+BD+BE) | META IGUALIT. TRI |
| CW | % ALCANCADO TRI (EE/CU) | % ALCANCADO TRI |

### Grupo 11: JANEIRO (CX-DH, 11 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| CX | META SAP (XLOOKUP PROJECAO M) | META SAP |
| CY | META IGUALIT. (XLOOKUP PROJECAO BC) | META IGUALIT. |
| CZ | % IGUALIT. (DG/CY) | (calculado) |
| DA | DATA PEDIDO | DATA PEDIDO |
| DB | JUSTIFICATIVA SEM 1 | JUSTIFICATIVA |
| DC | JUSTIFICATIVA SEM 2 | JUSTIFICATIVA |
| DD | JUSTIFICATIVA SEM 3 | JUSTIFICATIVA |
| DE | JUSTIFICATIVA SEM 4 | JUSTIFICATIVA |
| DF | JUSTIFICATIVA SEM 5 | JUSTIFICATIVA |
| DG | REALIZADO (=AP) | REALIZADO |
| DH | % SAP (DG/CX) | % SAP |

### Grupo 12: FEVEREIRO (DI-DS, 11 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| DI | META SAP | META SAP |
| DJ | META IGUALIT. | META IGUALIT. |
| DK | % IGUALIT. (DR/DJ) | % IGUALIT. |
| DL | DATA PEDIDO | DATA PEDIDO |
| DM | JUSTIFICATIVA SEM 1 | JUSTIFICATIVA |
| DN | JUSTIFICATIVA SEM 2 | JUSTIFICATIVA |
| DO | JUSTIFICATIVA SEM 3 | JUSTIFICATIVA |
| DP | JUSTIFICATIVA SEM 4 | JUSTIFICATIVA |
| DQ | JUSTIFICATIVA SEM 5 | JUSTIFICATIVA |
| DR | REALIZADO | REALIZADO |
| DS | % SAP (DR/DI) | % SAP |

### Grupo 13: MARCO (DT-ED, 11 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| DT | META SAP | META SAP |
| DU | META IGUALIT. | META IGUALIT. |
| DV | % IGUALIT. (EC/DU) | % IGUALIT. |
| DW | DATA PEDIDO | DATA PEDIDO |
| DX | JUSTIFICATIVA SEM 1 | JUSTIFICATIVA |
| DY | JUSTIFICATIVA SEM 2 | JUSTIFICATIVA |
| DZ | JUSTIFICATIVA SEM 3 | JUSTIFICATIVA |
| EA | JUSTIFICATIVA SEM 4 | JUSTIFICATIVA |
| EB | JUSTIFICATIVA SEM 5 | JUSTIFICATIVA |
| EC | REALIZADO | REALIZADO |
| ED | % SAP (EC/DT) | % SAP |

### Grupo 14: Q1 ANCORA (EE-EN, 10 colunas)

| Col | Nome | Subgrupo |
|-----|------|----------|
| EE | REALIZADO TRI (DG+DR+EC) | REALIZADO TRI |
| EF | % TRI SAP (EE/CU) | % TRI SAP |
| EG | URGENCIA (30%) | SCORE & PRIORIDADE v2 |
| EH | VALOR (25%) | SCORE & PRIORIDADE v2 |
| EI | FOLLOW-UP (20%) | SCORE & PRIORIDADE v2 |
| EJ | SINAL (15%) | SCORE & PRIORIDADE v2 |
| EK | TENTATIVA (5%) | SCORE & PRIORIDADE v2 |
| EL | SITUACAO (5%) | SCORE & PRIORIDADE v2 |
| EM | SCORE | SCORE & PRIORIDADE v2 |
| EN | PRIORIDADE v2 | SCORE & PRIORIDADE v2 |

---

## 4. PADROES DE FORMULAS

A CARTEIRA utiliza 5 padroes principais de formulas para consolidar dados de multiplas fontes.

### 4.1 INDEX/MATCH de DRAFT 1 (Dados Mercos)

Padrao predominante nas colunas A-AA e AB-BA. Busca dados no DRAFT 1 usando CNPJ (coluna B) como chave, cruzando com a coluna BH do DRAFT 1.

**Exemplo -- Coluna A (NOME FANTASIA):**
```
=IFERROR(
  INDEX('DRAFT 1'!$A$4:$A$566, MATCH($B4,'DRAFT 1'!$BH$4:$BH$566,0)),
  IFERROR(
    INDEX('DRAFT 3 '!$C$4:$C$1528, MATCH($B4,'DRAFT 3 '!$R$4:$R$1528,0)),
    IFERROR(
      INDEX(OPERACIONAL!$B$3:$B$663, MATCH($B4,OPERACIONAL!$W$3:$W$663,0)),
      \"\"
    )
  )
)
```

Nota: usa cascata de fallback -- busca primeiro no DRAFT 1 (Mercos), depois DRAFT 3 (SAP), depois OPERACIONAL. Padrao comum para dados de identidade (nome, razao social, UF, cidade, email, telefone).

### 4.2 INDEX/MATCH de DRAFT 3 (Dados SAP)

Padrao usado nas colunas CC-CQ. Busca dados cadastrais SAP usando CNPJ (coluna B) cruzando com coluna R do DRAFT 3.

**Exemplo -- Coluna CC (CODIGO DO CLIENTE SAP):**
```
=IFERROR(
  INDEX('DRAFT 3 '!$A$4:$A$1528, MATCH($B4,'DRAFT 3 '!$R$4:$R$1528,0)),
  \"\"
)
```

Colunas CI a CQ seguem o mesmo padrao, buscando nas colunas G a O do DRAFT 3 (grupo cliente, gerente, representante, vendedor interno, canal, tipo, macro/microregiao, grupo chave).

### 4.3 XLOOKUP de PROJECAO

Padrao usado nas colunas CR-ED para metas e projecao. Busca na aba PROJECAO usando o CNPJ convertido a VALUE (numerico).

**Exemplo -- Coluna CR (META ANUAL):**
```
=IFERROR(
  _xlfn.XLOOKUP(VALUE($B4),'PROJECAO '!$A$4:$A$662,'PROJECAO '!$L$4:$L$662),
  0
)
```

**Exemplo -- Coluna CU (META SAP TRIMESTRAL Q1):**
```
=IFERROR(
  _xlfn.XLOOKUP(VALUE($B4),'PROJECAO '!$A$4:$A$662,'PROJECAO '!$M$4:$M$662)
  + _xlfn.XLOOKUP(VALUE($B4),'PROJECAO '!$A$4:$A$662,'PROJECAO '!$N$4:$N$662)
  + _xlfn.XLOOKUP(VALUE($B4),'PROJECAO '!$A$4:$A$662,'PROJECAO '!$O$4:$O$662),
  0
)
```

### 4.4 IF Chains para Classificacao

Usadas nas colunas de status (M, N, CB) para classificar clientes automaticamente.

**Exemplo -- Coluna M (SITUACAO):**
```
=IF(B4=\"\",\"\",
  IF(OR(BD4=\"\",BD4=0),\"PROSPECT\",
    IF(OR(O4=\"\",O4=0),\"ATIVO\",
      IF(O4<=50,\"ATIVO\",
        IF(O4<=60,\"EM RISCO\",
          IF(O4<=90,\"INAT.REC\",\"INAT.ANT\")
        )
      )
    )
  )
)
```

**Exemplo -- Coluna CB (SINALEIRO) -- usa LET para legibilidade:**
```
=IF(B4=\"\",\"\",
  IF(OR(M4=\"PROSPECT\",M4=\"LEAD\"),\"ROXO\",
    IF(M4=\"NOVO\",\"VERDE\",
      IF(OR(O4=\"\",O4=0),
        IF(M4=\"ATIVO\",\"VERDE\",
          IF(M4=\"EM RISCO\",\"AMARELO\",
            IF(M4=\"INAT.REC\",\"AMARELO\",\"VERMELHO\")
          )
        ),
        _xlfn.LET(_xlpm.ciclo,R4, _xlpm.dias,O4,
          IF(_xlpm.ciclo=0,
            IF(_xlpm.dias<=50,\"VERDE\",IF(_xlpm.dias<=90,\"AMARELO\",\"VERMELHO\")),
            IF(_xlpm.dias<=_xlpm.ciclo,\"VERDE\",
              IF(_xlpm.dias<=_xlpm.ciclo+30,\"AMARELO\",\"VERMELHO\")
            )
          )
        )
      )
    )
  )
)
```

### 4.5 XLOOKUP de DRAFT 2 (Dados CRM/Funil)

Padrao usado nas colunas do FUNIL (BK-BQ, CA). Busca no DRAFT 2 usando CNPJ, com flag `-1` (busca do ultimo para o primeiro = registro mais recente).

**Exemplo -- Coluna BK (PROX FOLLOWUP):**
```
=IFERROR(
  _xlfn.XLOOKUP($B4,'DRAFT 2'!$AN$2:$AN$4403,'DRAFT 2'!$V$2:$V$4403,\"\",0,-1),
  \"\"
)
```

O parametro `-1` no XLOOKUP busca a ultima ocorrencia, garantindo que o registro mais recente do funil seja retornado.

---

## 5. FLUXO DE DADOS

```
DRAFT 1 (Mercos)
  |
  +--> CARTEIRA cols A-AA (identidade, status, compra, ecommerce, atendimento)
  +--> CARTEIRA cols AB-BA (vendas 2025 e 2026 mes a mes)
  +--> CARTEIRA cols BB-BI (recorrencia, tipo cliente, curva ABC)

DRAFT 2 (CRM / Funil de Atendimentos)
  |
  +--> CARTEIRA cols BJ-CB (funil: pipeline, perfil, maturidade, conversao, acao, sinaleiro)

DRAFT 3 (SAP)
  |
  +--> CARTEIRA cols CC-CQ (codigo SAP, CNPJ, razao social, status, dados cadastrais)
  +--> Fallback para cols A-AA quando DRAFT 1 nao encontra

PROJECAO
  |
  +--> CARTEIRA cols CR-CT (meta anual, realizado, % alcancado)
  +--> CARTEIRA cols CU-CW (meta Q1 trimestral)
  +--> CARTEIRA cols CX-ED (metas mensais Jan/Fev/Mar, realizado, % SAP)

OPERACIONAL (fallback)
  |
  +--> CARTEIRA cols A, C, D, I, K (quando nem DRAFT 1 nem DRAFT 3 encontram)

CALCULOS INTERNOS
  |
  +--> Col M: SITUACAO (IF chain sobre BD e O)
  +--> Col N: PRIORIDADE (IF chain sobre EN)
  +--> Col BU: DIAS ATE CONVERSAO (BX - BV)
  +--> Col CB: SINALEIRO (LET + IF chains sobre M, O, R)
  +--> Col CT: % ALCANCADO (CS/CR)
  +--> Col EE: REALIZADO TRI (DG+DR+EC)
  +--> Cols EG-EN: SCORE & PRIORIDADE v2 (ponderado 6 dimensoes)
```

### Resumo das Fontes

| Fonte | Abas Referenciadas | Colunas CARTEIRA | Tipo de Dados |
|-------|-------------------|------------------|---------------|
| DRAFT 1 | Mercos (566 linhas) | A-BA, BB-BI | Clientes, vendas, recorrencia |
| DRAFT 2 | CRM/Funil (4.403 linhas) | BJ-CB | Atendimentos, pipeline, conversao |
| DRAFT 3 | SAP (1.528 linhas) | CC-CQ + fallback A-AA | Cadastro, status, hierarquia |
| PROJECAO | Metas (662 linhas) | CR-ED | Metas, realizado, % |
| OPERACIONAL | Base interna (663 linhas) | Fallback A, C, D, I, K | Identidade (ultimo recurso) |
| RESUMO META | Consolidado | AB-AN (cabecalhos) | Totais mensais |

---

## 6. REGRAS DE INTEGRIDADE

### 6.1 Two-Base Architecture

A CARTEIRA respeita a separacao fundamental do CRM VITAO360:

- **VENDA** (registros com valor R$): colunas AB-BA (vendas 2025/2026), BB (ticket medio), BG (media mensal), BH (ticket medio), CR-ED (metas e realizado)
- **LOG** (registros de interacao, SEMPRE R$0,00): colunas BJ-CA (funil, pipeline, atendimentos, acoes)

NUNCA somar valores de colunas de VENDA com dados do FUNIL. A violacao desta regra causa inflacao de 742% (ja ocorrida historicamente).

### 6.2 CNPJ como Chave Primaria

- Coluna B (CNPJ): chave primaria de toda a CARTEIRA
- Coluna CD (CNPJ SAP): chave de cruzamento com DRAFT 3
- Formato: string de 14 digitos, zero-padded
- Formula de normalizacao (col B):
  ```
  =IF(CD4=\"\",\"\",SUBSTITUTE(SUBSTITUTE(SUBSTITUTE(CD4&\"\",\".\",\"\"),\"/\",\"\"),\"-\",\"\"))
  ```
- NUNCA armazenar como float (perde zeros a esquerda)
- Todo cruzamento entre DRAFT 1, DRAFT 2, DRAFT 3 e PROJECAO usa CNPJ como chave

### 6.3 Colunas Originais vs Expandidas

**46 colunas originais (IMUTAVEIS):**

As 46 colunas originais correspondem as colunas A-AT da versao inicial da CARTEIRA. Estas colunas NAO podem ser adicionadas, removidas ou reordenadas. Compreendem:

- Colunas A-AA (27): Grupo MERCOS completo (identidade, status, compra, ecommerce, atendimento)
- Colunas AB-AN (13): Grupo VENDAS 2025 (total + 12 meses)
- Colunas AO-AT (6): Grupo VENDAS 2026 parcial (total + Jan a Mai)

**98 colunas expandidas (Blueprint v2):**

A expansao de 46 para 144 colunas foi feita via grupos [+] (colunas agrupaveis no Excel), mantendo as 46 originais intactas:

- Colunas AU-BA (7): Restante de VENDAS 2026 (Jun a Dez)
- Colunas BB-BI (8): Grupo VENDAS (recorrencia e tipo cliente)
- Colunas BJ-CB (19): Grupo FUNIL completo
- Colunas CC-CQ (15): Grupos SAP + STATUS SAP + DADOS CADASTRAIS SAP
- Colunas CR-CT (3): Grupo ANUAL
- Colunas CU-CW (3): Grupo Q1
- Colunas CX-DH (11): Grupo JANEIRO
- Colunas DI-DS (11): Grupo FEVEREIRO
- Colunas DT-ED (11): Grupo MARCO
- Colunas EE-EN (10): Grupo Q1 ANCORA (score e prioridade)

### 6.4 Regras de Formulas

- Todas as formulas devem estar em INGLES quando manipuladas via openpyxl: IF, INDEX, MATCH, IFERROR, VLOOKUP, XLOOKUP, SUM, SUMIF, COUNTIF, SUBTOTAL, LET
- Separador de argumentos: virgula (,), NUNCA ponto-e-virgula (;)
- Funcoes com prefixo `_xlfn.` (XLOOKUP, LET) sao especificas do Excel 365 -- verificar compatibilidade
- IFERROR envolve TODA busca INDEX/MATCH ou XLOOKUP para evitar #N/A
- Headers (linha 3) usam SUBTOTAL(109,...) ou SUM para totais filtrados

### 6.5 Validacao Obrigatoria

Apos qualquer modificacao na CARTEIRA:

1. Zero erros de formula (#REF!, #DIV/0!, #VALUE!, #NAME?)
2. Faturamento total (col AB soma) bate com R$ 2.091.000 (tolerancia 0.5%)
3. Two-Base respeitada (nenhum valor R$ em colunas de LOG)
4. CNPJ sem duplicatas na coluna B
5. Todas as 144 colunas presentes e na ordem correta
6. Testar no Excel real (LibreOffice nao recalcula XLOOKUP e LET corretamente)

---

*Documento gerado a partir de carteira_blueprint.json*
*Fonte primaria: CRM_VITAO360 INTELIGENTE FINAL OK .xlsx*
*Data de referencia: Marco/2026*
