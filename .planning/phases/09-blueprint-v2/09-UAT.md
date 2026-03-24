---
status: testing
phase: 09-blueprint-v2
source: 09-01-SUMMARY.md, 09-02-SUMMARY.md, 09-03-SUMMARY.md, 09-04-SUMMARY.md, 09-05-SUMMARY.md, 09-06-SUMMARY.md
started: 2026-02-17T22:00:00Z
updated: 2026-02-17T22:00:00Z
---

## Current Test

number: 1
name: V13 abre no Excel sem erros
expected: |
  Abra o arquivo data/output/CRM_VITAO360_V13_PROJECAO.xlsx no Excel.
  O arquivo deve abrir sem mensagens de erro ou corrupção.
  Deve ter 13 abas visíveis na barra inferior: PROJECAO, LOG, DASH, REDES_FRANQUIAS_v2, COMITE, REGRAS, DRAFT 1, DRAFT 2, CARTEIRA, AGENDA LARISSA, AGENDA DAIANE, AGENDA MANU, AGENDA JULIO.
awaiting: user response

## Tests

### 1. V13 abre no Excel sem erros
expected: Abra o arquivo data/output/CRM_VITAO360_V13_PROJECAO.xlsx no Excel. O arquivo deve abrir sem mensagens de erro ou corrupção. Deve ter 13 abas na barra inferior.
result: [pending]

### 2. CARTEIRA tem 263+ colunas com agrupamento funcional
expected: Na aba CARTEIRA, role para a direita -- deve haver colunas ate pelo menos JC (col 263). Verifique os botoes [+]/[-] no topo das colunas -- ao clicar, super-grupos devem expandir/recolher (MERCOS, FUNIL, SAP, FATURAMENTO).
result: [pending]

### 3. CARTEIRA headers e clientes visiveis
expected: Na aba CARTEIRA, linhas 1-3 sao headers (super-grupo, sub-grupo, nome coluna). A partir da linha 4, voce deve ver 554 clientes com CNPJ na coluna B e NOME FANTASIA na coluna A. Os dados devem ser reais (nomes de clientes que voce reconhece).
result: [pending]

### 4. Formulas MERCOS calculam valores reais
expected: Na CARTEIRA, colunas C ate AQ (bloco MERCOS) devem mostrar dados puxados dos clientes: RAZAO SOCIAL, UF, CIDADE, DIAS SEM COMPRA, CICLO MEDIO, CURVA ABC, etc. NAO deve haver #REF!, #VALUE! ou celulas vazias em massa.
result: [pending]

### 5. Formulas FUNIL mostram dados de atendimento
expected: Na CARTEIRA, colunas AR ate BJ (bloco FUNIL) devem mostrar dados de atendimento: ESTAGIO FUNIL, DATA ULT ATENDIMENTO, ULTIMO RESULTADO, TEMPERATURA, SINALEIRO. A coluna TEMPERATURA deve ter valores como QUENTE/MORNO/FRIO.
result: [pending]

### 6. FATURAMENTO mostra META vs REALIZADO por mes
expected: Na CARTEIRA, a partir da coluna BZ, voce deve ver blocos mensais (JAN, FEV, MAR...). Cada mes tem META MES (valor mensal), REALIZADO MES (venda do mes), %MES (percentual), e colunas de JUSTIFICATIVA (S1-S4). Os percentuais devem ser numeros razoaveis (0% a 200%+).
result: [pending]

### 7. SCORE de prioridade funciona
expected: Na CARTEIRA coluna O, cada cliente deve ter um SCORE numerico (0-100+). Clientes com mais urgencia (muitos dias sem compra, curva A, follow-up vencido) devem ter scores mais altos. Role ate a coluna JD para ver o RANK (posicao 1 a 554).
result: [pending]

### 8. Conditional formatting visivel
expected: Na CARTEIRA, as colunas de TEMPERATURA devem ter cores (vermelho/amarelo/azul). As colunas de %MES no FATURAMENTO devem ter semaforo (verde >=100%, amarelo 70-99%, vermelho <70%). A coluna ALERTA (JH) deve ter cores por severidade.
result: [pending]

### 9. REGRAS tem motor de regras completo
expected: Na aba REGRAS, voce deve ver 17 secoes com dados de referencia. No final (linhas 219-283), o MOTOR DE REGRAS mostra 63 combinacoes de SITUACAO x RESULTADO com a TEMPERATURA resultante. A secao SCORE RANKING (linhas 209-216) deve ter 6 fatores com pesos somando 100%.
result: [pending]

### 10. AGENDA mostra tarefas priorizadas por consultor
expected: Abra a aba AGENDA LARISSA. Deve mostrar uma lista de clientes da Larissa ordenados por prioridade (SCORE mais alto primeiro). As colunas incluem DATA, NOME, CNPJ, SCORE, ESTAGIO, TEMPERATURA, SINALEIRO. As colunas RESULTADO e MOTIVO (verdes) devem ter dropdown ao clicar.
result: [pending]

### 11. AGENDA MANU funciona com dois nomes
expected: Na aba AGENDA MANU, deve mostrar clientes de "MANU DITZEL" e "HEMANUELE DITZEL (MANU)" juntos, ordenados por SCORE. Devem aparecer pelo menos 10 clientes.
result: [pending]

### 12. Dropdowns de RESULTADO e MOTIVO funcionam
expected: Em qualquer aba AGENDA, clique na celula de RESULTADO (coluna verde). Um dropdown deve aparecer com opcoes como: EM ATENDIMENTO, ORCAMENTO, CADASTRO, VENDA/PEDIDO, etc. Clique na celula de MOTIVO -- outro dropdown com: AINDA TEM ESTOQUE, NAO TEM DEMANDA, FORA DE ROTA, etc.
result: [pending]

### 13. PROJECAO preservada com formulas intactas
expected: Na aba PROJECAO, as formulas devem estar funcionando normalmente (SUM, IF, VLOOKUP, RANK). Verifique se a coluna Z (TOTAL) calcula a soma das colunas mensais. Os valores devem bater com o que voce conhece do CRM.
result: [pending]

## Summary

total: 13
passed: 0
issues: 0
pending: 13
skipped: 0

## Gaps

[none yet]
