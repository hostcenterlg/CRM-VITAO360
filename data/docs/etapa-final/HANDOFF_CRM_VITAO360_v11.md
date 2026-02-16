# HANDOFF — CRM VITAO360 v11 SINALEIRO
## Documento de Transferência para Nova Conversa
**Data:** 15/02/2026 | **Autor:** Claude (sessão anterior) | **Responsável:** Leandro (AI Solutions Engineer)

---

## 1. CONTEXTO DO PROJETO

O CRM JARVIS/VITAO360 é um sistema Excel que gerencia 489 clientes B2B da VITAO Alimentos (Curitiba). A aba PROJEÇÃO tinha 18.180 fórmulas que foram perdidas (zeradas) quando o arquivo foi salvo sem recalcular. A missão era reconstruir as fórmulas, corrigir dados de faturamento, e consolidar múltiplos arquivos num CRM único.

---

## 2. ARQUIVOS FONTE (verdade dos dados)

Cada arquivo contribui uma parte. Nenhum é completo sozinho.

### SINALEIRO_INTERNO_CONFIAVEL.xlsx (149 KB)
- **O que é:** Base confiável do Interno com SLICERS FUNCIONANDO no Excel
- **Abas:** Resumo, Historico, Interno (663×23, Tabela1), Status Clientes, Ciclo do Cliente
- **Slicers:** 5 slicers no Interno: UF_Grupo, Consultor, Semaforo, Tipo_Carteira, Rede
- **CRÍTICO:** Este é o ÚNICO arquivo onde os slicers funcionam nativamente no Excel. Os slicers estão conectados a Tabela1 (tableId=1) via XML nativo.

### SINALEIRO_REDES_VITAO.xlsx (21 KB)
- **O que é:** Sinaleiro de penetração das redes de franquias (923 lojas)
- **Abas:** PAINEL (68 fórmulas), PARAMETROS (5 fórmulas), SINALEIRO (94 fórmulas), PLANO_ACAO (48 fórmulas), CADENCIA (5 fórmulas)
- **CRÍTICO:** Tem 220 fórmulas ativas com referências cross-sheet entre SINALEIRO↔PARAMETROS↔PAINEL
- **ATENÇÃO:** Quando copiado para arquivo consolidado, as referências precisam ser atualizadas (ex: "SINALEIRO!" → "SINALEIRO_REDES!" se a aba for renomeada)

### SINALEIRO_v10_AUDITADO.xlsx (165 KB)
- **O que é:** Versão mais completa com Motor de Inteligência e Regras
- **Abas:** PAINEL, Historico, OPERACIONAL (=Interno, dados idênticos), Status Clientes, Ciclo do Cliente, PROJEÇÃO (vazia, 1×1), MOTOR (144×8), REGRAS (53×6), LEIA-ME (53×2)
- **Contribui:** MOTOR, REGRAS e LEIA-ME (documentação do sistema)
- **Nota:** OPERACIONAL é 100% idêntico ao Interno do CONFIAVEL

### VITAO360_SINALEIRO_FINAL.xlsx (332 KB)
- **O que é:** O arquivo base original com a PROJEÇÃO zerada
- **Abas:** PROJEÇÃO (504×80, ZERO fórmulas), Resumo, Historico, Interno (663×23, Tabela1 + slicers), Status Clientes, Ciclo do Cliente
- **PROJEÇÃO:** Contém apenas dados estáticos de janeiro. Faturamento total: R$ 87.374,93 (só JAN)

### PROJEÇAO_SOMENTE_ABA_SEPARA.xlsx (227 KB)
- **O que é:** Exportação da aba PROJEÇÃO isolada
- **PROJEÇÃO:** 504×80, ZERO fórmulas, mesmos dados estáticos do VITAO360_FINAL

---

## 3. ESTADO ATUAL DO OUTPUT (CRM_VITAO360_v11_FINAL.xlsx)

### O que FOI feito:
- 14 abas consolidadas num arquivo único (522 KB)
- 18.400 fórmulas totais (18.180 na PROJEÇÃO + 220 nas abas REDES)
- 0 erros de fórmula no recalc do LibreOffice
- Referências cross-sheet corrigidas (SINALEIRO! → SINALEIRO_REDES!)
- Dados de faturamento combinados: Mercos primário + SAP complemento
- XML surgery: arquivos de slicer injetados (slicerCache1-5.xml, slicer1.xml, drawing1.xml)

### PROBLEMAS CONHECIDOS (não resolvidos):

#### PROBLEMA 1: Slicers NÃO funcionam
Os slicers foram injetados via XML surgery (copiando arquivos XML do CONFIAVEL para o novo arquivo). Isso NÃO garante que funcionem no Excel porque:
- O openpyxl destrói a infraestrutura de slicers ao salvar
- A cirurgia XML reconstrói os arquivos mas o Excel pode precisar "reparar" na abertura
- Na prática, os slicers podem aparecer quebrados ou não aparecer

**SOLUÇÃO RECOMENDADA:** Não tentar via Python/openpyxl. Abrir o INTERNO_CONFIAVEL no Excel, copiar manualmente as abas que faltam (PROJEÇÃO, REDES, etc.) para dentro dele, preservando os slicers nativos.

#### PROBLEMA 2: Faturamento com divergências
Os dados de faturamento vieram de duas fontes combinadas:

| Mês | Meu Output | PAINEL (correto) | Diferença |
|-----|-----------|-----------------|-----------|
| JAN | R$ 43.265 | R$ 80.000 | -R$ 36.735 |
| FEV | R$ 38.004 | R$ 95.000 | -R$ 56.996 |
| MAR | R$ 120.928 | R$ 110.000 | +R$ 10.928 |
| ABR | R$ 217.224 | R$ 150.000 | +R$ 67.224 |
| MAI | R$ 206.347 | R$ 180.000 | +R$ 26.347 |
| JUN | R$ 253.590 | R$ 220.000 | +R$ 33.590 |
| JUL | R$ 174.049 | R$ 200.000 | -R$ 25.951 |
| AGO | R$ 235.033 | R$ 230.000 | +R$ 5.033 |
| SET | R$ 234.690 | R$ 210.000 | +R$ 24.690 |
| OUT | R$ 260.195 | R$ 280.000 | -R$ 19.805 |
| NOV | R$ 196.016 | R$ 260.000 | -R$ 63.984 |
| DEZ | R$ 170.043 | R$ 141.179 | +R$ 28.864 |
| **TOTAL** | **R$ 2.149.389** | **R$ 2.156.179** | **-R$ 6.790** |

O total está 99.7% correto mas a distribuição mensal está errada. Causa: os Relatórios de Vendas Mercos tinham datas sobrepostas e alguns pedidos foram alocados no mês errado. Jan e Fev estão especialmente baixos porque não existem relatórios Mercos pra esses meses (só SAP parcial).

**FONTES UTILIZADAS:**
- Mercos (primário): 12 relatórios mensais de vendas com pedidos por Nome Fantasia/Razão Social
- SAP (complemento): BASE_SAP_VENDA_MES_A_MES_2025.xlsx com Código SAP + Faturado
- Mapeamento SAP: BASE_SAPE_CARTEIRA_CLIENTE_INTERNO_COM_VENDA (1.698 códigos SAP→CNPJ)
- 337 clientes matched via Mercos, 478 via SAP, 486 clientes com algum faturamento
- 91 pedidos Mercos não mapearam (R$ 303k — clientes fora da carteira de 500)

#### PROBLEMA 3: Aba UPDATE_LOG ausente
A aba UPDATE_LOG (65 linhas, documentação das 14 etapas de reconstrução) existia no arquivo intermediário VITAO360_SINALEIRO_CORRIGIDO.xlsx mas NÃO foi copiada para o CRM_v11_FINAL. Erro meu.

#### PROBLEMA 4: Formatação/estilos perdidos
O openpyxl copia células e estilos básicos mas pode perder:
- Conditional formatting avançado
- Data validation com dropdowns
- Comentários
- Imagens embutidas
- Formatação de tabela (TableStyleInfo)

---

## 4. ESTRUTURA DA ABA PROJEÇÃO (18.180 fórmulas)

### Layout: 504 linhas × 83 colunas (A1:CE503)

**Linha 1:** Título "PROJEÇÃO — META SAP + SINALEIRO DE ATINGIMENTO"
**Linha 2:** Agrupadores (IDENTIFICAÇÃO, SINALEIRO REDE, META MENSAL, REALIZADO, etc.)
**Linha 3:** Headers das colunas
**Linhas 4-503:** 500 clientes

### Colunas:

| Bloco | Colunas | Conteúdo |
|-------|---------|----------|
| IDENTIFICAÇÃO | A-E | CNPJ, Nome, Rede/Grupo, Consultor, (vazio) |
| SINALEIRO REDE | F-J | Total Lojas, Sinaleiro %, Cor, Maturidade, Ação Rede |
| META MENSAL (SAP) | L-X | Meta Anual (L), Meta Jan-Dez (M-X) |
| REALIZADO | Z-AL | Real Anual (Z=SUM), Real Jan-Dez (AA-AL = dados) |
| KPIs | AN-AQ | %YTD (AN), Sinal Meta (AO), GAP (AP), Ranking (AQ) |
| SINALEIRO REDES | AS-AZ | Tabela lateral: Rede, Lojas, Sinaleiro%, Cor, Maturidade, Ação, Fat.Real, Gap |
| META DISTRIBUÍDA | BB-BN | Dist Anual (BB), Dist Jan-Dez (BC-BN) |
| META COMPENSADA | BP-CB | Comp Anual (BP), Comp Jan-Dez (BQ-CB) |

### Fórmulas-chave (exemplos row 4):

```
Z4  = SUM(AA4:AL4)                           → Real Anual
AN4 = IF(L4=0,0,Z4/L4)                       → % YTD
AO4 = IF(AN4>=1,"🟢",IF(AN4>=0.7,"🟡",IF(AN4>=0.4,"🟠","🔴")))  → Sinal Meta
AP4 = L4-Z4                                   → GAP
AQ4 = RANK(Z4,$Z$4:$Z$503,0)                 → Ranking

Sinaleiro Rede (F-J): VLOOKUP no CNPJ contra tabela de redes
Meta Distribuída (BB-BN): Proporção mensal da meta anual
Meta Compensada (BP-CB): Redistribui gap dos meses passados pros meses futuros
```

### Table: SinaleiroPROJECAO
- Range: A3:CE503
- Tabela Excel para permitir filtros/slicers futuros

---

## 5. FATURAMENTO CORRETO (PAINEL DE ATIVIDADES)

Fonte: PAINEL_DE_ATIVIDADES_ATENDIMENTO_VS_VENDAS.pdf (na verdade é um ZIP de imagens JPEG)

```
VITAO ALIMENTOS - Dashboard Executivo 2025
Período: Janeiro a Dezembro 2025

FATURAMENTO TOTAL: R$ 2.156.179 (R$ 2,15M)
VENDAS TOTAIS: 902 pedidos
CAC: R$ 532
ROI ANUAL: 347%

Mês    Faturamento   Atendimentos  Vendas  Carteira  Positivados  %Posit  ROI    Ticket
JAN    R$  80.000    156           15      28        28           100%    100%   R$ 5.333
FEV    R$  95.000    269           25      64        50            78%    138%   R$ 3.800
MAR    R$ 110.000    442           40      125       73            58%    175%   R$ 2.750
ABR    R$ 150.000    596           53      186       102           55%    275%   R$ 2.830
MAI    R$ 180.000    862           78      243       77            32%    350%   R$ 2.308
JUN    R$ 220.000    1.203         111     298       106           36%    450%   R$ 1.982
JUL    R$ 200.000    958           84      320       101           32%    400%   R$ 2.381
AGO    R$ 230.000    1.244         113     342       119           35%    475%   R$ 2.035
SET    R$ 210.000    1.185         104     394       125           32%    425%   R$ 2.019
OUT    R$ 280.000    1.395         123     454       140           31%    600%   R$ 2.276
NOV    R$ 260.000    1.528         133     530       130           25%    550%   R$ 1.955
DEZ    R$ 141.179    796           78      648       486           75%    253%   R$ 1.810
TOTAL  R$ 2.156.179  10.634        902     648       1.537         -      349%   R$ 2.389
```

---

## 6. MAPEAMENTO DE DADOS (como preencher REALIZADO por cliente)

### Relatórios Mercos disponíveis:
- Março a Dezembro 2025 + Janeiro 2026
- Colunas: Data Emissão, Pedido, Tag, Nome Fantasia, Razão Social, Representada, Colaborador, Rede, Valor vendido
- **ATENÇÃO:** Datas são STRINGS ("22/12/2025"), não datetime objects
- **ATENÇÃO:** Relatório "Abril" tem range 01/04 a 31/05 (inclui maio inteiro)
- **ATENÇÃO:** Relatório "Setembro" duplicado com Outubro
- **ATENÇÃO:** Relatório "Novembro" na verdade é Set (verificar Data final no header)
- **NÃO TEM:** Janeiro e Fevereiro 2025 (só SAP)

### Relatórios SAP:
- BASE_SAP_VENDA_MES_A_MES_2025.xlsx: 12 abas (Jan-Dez), Col A = "COD_SAP - NOME", Col E = Faturado
- Mapeamento COD_SAP→CNPJ: BASE_SAPE_CARTEIRA_CLIENTE_INTERNO_COM_VENDA (Col 2=Código, Col 8=CNPJ)
- 1.698 mapeamentos disponíveis
- SAP tem dados de TODOS os 12 meses mas valores são metade do faturamento real (SAP ≈ 50% do PAINEL)

### Problema do GAP de faturamento:
O total SAP (todos os meses somados) = R$ 1.838.044. O total Mercos+SAP combinado = R$ 2.149.389. O PAINEL diz R$ 2.156.179. O gap de R$ 6.790 provavelmente são clientes que existem no Mercos mas não mapearam pra nenhum CNPJ na carteira de 500.

### Matching de clientes:
- PROJEÇÃO usa CNPJ (14 dígitos sem pontuação) como chave primária
- Mercos NÃO tem CNPJ — só Nome Fantasia e Razão Social
- Match é feito por nome (fuzzy): Razão Social Mercos ↔ Nome na PROJEÇÃO
- SAP tem Código SAP que mapeia pra CNPJ via base CARTEIRA

---

## 7. CONSULTORES E REGIÕES

```
MANU DITZEL:    SC, PR, RS (Sul) — 32.5% do faturamento, licença maternidade próxima
LARISSA PADILHA: Restante do Brasil (exceto redes Julio e Daiane)
JULIO:          Cia Saúde + Fitland (exclusivamente)
DAIANE:         Franquias: Divina Terra, Biomundo, Mundo Verde, Vida Leve, Tudo em Grãos
```

---

## 8. REGRAS DO SINALEIRO

```
COR         FAIXA       MATURIDADE     OBJETIVO          CADÊNCIA
ROXO        < 1%        PROSPECÇÃO     Primeiro pedido   1x/semana WA+Ligação
VERMELHO    1% a 40%    ATIVAÇÃO       Recorrência       2x/semana Lig+WA+Visita
AMARELO     40% a 70%   CRESCIMENTO    Mix + Volume      1x/semana WA+Oferta
VERDE       > 70%       CONSOLIDAÇÃO   JBP               Mensal estratégico
```

---

## 9. PADRÕES IMUTÁVEIS DO CRM

- **CNPJ:** 14 dígitos sem pontuação, chave primária universal
- **Layout PROJEÇÃO:** 504 linhas × 80+ colunas, NÃO ALTERAR ordem/posição
- **Cores:** ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000
- **Two-Base Architecture:** BASE_VENDAS (valores) separada de LOG (interações) — NUNCA misturar
- **Tema:** Light mode exclusivamente, padrão VITAO verde
- **Fórmulas:** Português (SOMA, SE, PROCV, CLASSIFICAR)

---

## 10. O QUE FAZER NA PRÓXIMA CONVERSA

### Prioridade 1: Dados de faturamento corretos
O faturamento por cliente precisa bater com o PAINEL (R$ 2.156.179). A melhor abordagem seria:
1. Usar os dados SAP como base (tem TODOS os 12 meses)
2. Complementar com Mercos onde SAP não tem
3. Validar totais mensais contra o PAINEL
4. Aceitar que vai ter um gap de ~R$ 6k por clientes não mapeados

### Prioridade 2: Slicers funcionando
NÃO TENTAR via openpyxl/XML surgery. A abordagem que funciona:
1. Abrir SINALEIRO_INTERNO_CONFIAVEL.xlsx no Excel (tem slicers nativos)
2. Copiar as abas que faltam PARA DENTRO dele via Excel (não via Python)
3. Ou: criar slicers novos diretamente no Excel sobre a Tabela1/SinaleiroPROJECAO

### Prioridade 3: Consolidar arquivo único
Garantir que todas as 14 abas estejam presentes com fórmulas funcionando:
PROJEÇÃO, Resumo, Historico, Interno, Status Clientes, Ciclo do Cliente,
SINALEIRO_REDES, PAINEL_REDES, PARAMETROS, PLANO_ACAO, CADENCIA,
MOTOR, REGRAS, LEIA-ME

### Prioridade 4: UPDATE_LOG
Incluir aba de documentação com histórico de alterações.

---

## 11. ARQUIVOS PARA UPLOAD NA NOVA CONVERSA

Enviar para a nova conversa:
1. **SINALEIRO_INTERNO_CONFIAVEL.xlsx** — base do Interno com slicers
2. **SINALEIRO_REDES_VITAO.xlsx** — sinaleiro de franquias com fórmulas
3. **SINALEIRO_v10_AUDITADO.xlsx** — MOTOR + REGRAS + LEIA-ME
4. **VITAO360_SINALEIRO_FINAL.xlsx** — arquivo original com PROJEÇÃO zerada
5. **Este documento HANDOFF** — contexto completo
6. **BASE_SAP_VENDA_MES_A_MES_2025.xlsx** — faturamento SAP (12 meses)
7. **PAINEL_DE_ATIVIDADES** — valores corretos de faturamento mensal

---

## 12. LIÇÕES APRENDIDAS (erros a NÃO repetir)

1. **NÃO usar openpyxl para slicers** — ele destrói a infraestrutura XML. Slicers só funcionam criados/preservados no Excel nativo.
2. **NÃO combinar Mercos + SAP sem validar por mês** — os relatórios Mercos têm ranges de data sobrepostos e nomes inconsistentes.
3. **SEMPRE validar totais contra o PAINEL** antes de entregar.
4. **NUNCA entregar sem a aba UPDATE_LOG** — documentação é obrigatória.
5. **Testar o arquivo no Excel real** antes de declarar sucesso — o recalc do LibreOffice não é igual ao do Excel.
6. **Os dados do Relatorio de Vendas Mercos têm armadilhas:** "Abril" cobre Abr+Mai, "Setembro 25" é na verdade Outubro, "Novembro" é na verdade Setembro. Sempre conferir "Data inicial/Data final" nas linhas 6-7 de cada relatório.
