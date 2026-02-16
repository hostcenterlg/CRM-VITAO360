# CRM VITAO360 — Projeto gerado pelo DEUS-AIOS

## Identidade
Projeto de CRM Excel para VITAO Alimentos (distribuidora B2B de alimentos naturais, Curitiba/PR).
16 meses de desenvolvimento, 32 sessões, 88+ arquivos Excel. Este é o rebuild definitivo.
Comunicação: SEMPRE em Português Brasileiro.

## Motor de Execução: GSD
- `/gsd:new-project --auto @BRIEFING-COMPLETO.md` → Já executado com briefing completo
- `/gsd:discuss-phase N` → Discutir fase antes de planejar
- `/gsd:plan-phase N` → Planos atômicos
- `/gsd:execute-phase N` → Execução paralela
- `/gsd:verify-work N` → Verificação automática
- `/gsd:set-profile quality` → Usar Opus (projeto crítico)

## Domínio: Excel/Python + CRM Comercial B2B

### Agentes necessários neste projeto:
- `@data-engineer` → Cruzamento de dados entre Mercos/SAP/Deskrio
- `@python-pro` → Scripts openpyxl, pandas, rapidfuzz
- `@business-analyst` → Regras de negócio CRM/vendas
- `@qa-expert` → Validação de fórmulas e dados
- `@excel-specialist` → Fórmulas, formatação, slicers (custom)

## REGRAS INVIOLÁVEIS DO PROJETO

### 1. Two-Base Architecture
- Valor R$ APENAS em registro tipo VENDA
- LOG/interações = SEMPRE R$ 0.00
- Violação causa inflação de 742% (já aconteceu)

### 2. CNPJ = Chave Primária
```python
cnpj = re.sub(r'\D', '', str(val)).zfill(14)  # 14 dígitos, sem pontuação
```
- NUNCA armazenar como float (perde precisão)
- Todo cruzamento entre sistemas usa CNPJ

### 3. CARTEIRA 46 colunas = IMUTÁVEL
- Não adicionar, não remover, não reordenar as 46 originais
- Blueprint v2 expande para 81 via grupos [+], mantendo as 46 intactas

### 4. Fórmulas openpyxl em INGLÊS
```python
# CORRETO: =IF(A1>0,"sim","não")
# ERRADO: =SE(A1>0;"sim";"não")  ← QUEBRA
```

### 5. NUNCA openpyxl para slicers
- Openpyxl DESTRÓI infraestrutura XML de slicers
- Slicers = XML Surgery (zipfile + lxml) ou manual no Excel

### 6. Relatórios Mercos MENTEM nos nomes
- SEMPRE conferir "Data inicial" e "Data final" nas linhas 6-7
- "Abril" = Abr+Mai, "Set25" = Out, "Nov" = Set

### 7. Faturamento = R$ 2.156.179
- Validar SEMPRE contra o PAINEL DE ATIVIDADES 2025
- Qualquer divergência > 0.5% = investigar

### 8. Zero fabricação de dados
- Dados sintéticos do CONTROLE_FUNIL: classificação 3-tier obrigatória
- REAL / SINTÉTICO / ALUCINAÇÃO — segregar antes de integrar
- 558 registros já classificados como ALUCINAÇÃO (não integrar)

### 9. Visual
- Tema LIGHT exclusivamente. NUNCA dark mode.
- Fonte Arial 9pt dados, 10pt headers
- Cores status: ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000 (texto branco)
- Cores ABC: A=#00B050, B=#FFFF00, C=#FFC000

### 10. Validação obrigatória pós-build
- 0 erros de fórmula (#REF!, #DIV/0!, #VALUE!, #NAME?)
- Faturamento total bate com R$ 2.156.179
- Two-Base Architecture respeitada
- CNPJ sem duplicatas
- 14 abas presentes e funcionais
- Testar no Excel real (LibreOffice recalc ≠ Excel recalc)

## DE-PARA Vendedores
```
MANU: Manu, Manu Vitao, Manu Ditzel → MANU
LARISSA: Larissa, Lari, Larissa Vitao, Mais Granel, Rodrigo → LARISSA
DAIANE: Daiane, Central Daiane, Daiane Vitao → DAIANE
JULIO: Julio, Julio Gadret → JULIO
LEGADO: Bruno Gretter, Jeferson Vitao, Patric, Gabriel, Sergio, Ive, Ana → LEGADO
```

## Entregas priorizadas
1. PROJEÇÃO reconstruída (18.180 fórmulas) — CRÍTICO
2. Dados de faturamento corretos
3. Timeline mensal populada
4. LOG completo (~11.758 registros)
5. DASH redesenhada (3 blocos)
6. E-commerce cruzado
7. REDE/REGIONAL preenchido
8. #REF! corrigidos
9. COMITÊ com metas
10. Validação final

## Briefing completo
Ver `BRIEFING-COMPLETO.md` na raiz do projeto — contém TUDO (14 partes, 88+ arquivos documentados).
