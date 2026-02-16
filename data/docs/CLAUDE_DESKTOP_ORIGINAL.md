# JARVIS CRM — Projeto de Construção do Excel Central

## Contexto
CRM operacional em Excel (.xlsx) para VITAO Alimentos — distribuidora B2B de alimentos naturais com 4 consultores e ~500 clientes. O arquivo final se chama JARVIS_CRM_CENTRAL.xlsx e fica em `output/`.

## Documentação
A especificação completa está em `docs/DOCUMENTO_MESTRE.md`. SEMPRE leia esse arquivo antes de executar qualquer tarefa.

## Regras obrigatórias
1. Output SEMPRE em .xlsx (nunca .csv, .html ou outro formato)
2. Usar openpyxl para criar/editar os arquivos Excel
3. Fonte Arial 10 em todo o arquivo
4. Headers: negrito + fundo cinza #D9D9D9 + borda fina
5. Tema claro (nunca dark mode)
6. NUNCA inventar dados — usar apenas o que está no DOCUMENTO_MESTRE.md
7. Named Ranges são obrigatórias (servem de fonte para dropdowns das outras abas)
8. Sempre salvar em output/JARVIS_CRM_CENTRAL.xlsx
9. Após criar, rodar recalc se houver fórmulas

## Estrutura do Excel (7 abas, construídas em sequência)
1. **REGRAS** — Tabelas de validação e Named Ranges
2. **CARTEIRA** — 81 colunas (10 fixas + 8 grupos [+] expansíveis)
3. **LOG** — 20 colunas, append-only, zero valores financeiros
4. **DRAFT 1** — Quarentena dados Mercos
5. **DRAFT 2** — Quarentena atendimentos consultores
6. **DASH** — 7 seções verticais de dashboard
7. **AGENDA** — Template 24 colunas exportável por consultor

## Equipe comercial
- MANU DITZEL → SC, PR, RS (regional)
- LARISSA PADILHA → Resto do Brasil (regional)
- JULIO GADRET → CIA DA SAUDE + FIT LAND (rede)
- DAIANE STAVICKI → Outras redes de franquia (rede + central)
