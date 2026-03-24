# CRM VITAO360 — Inteligência Comercial

Sistema de CRM inteligente para VITAO Alimentos — distribuidora B2B de alimentos naturais.

## Identidade
- Nome: CRM VITAO360
- Propósito: CRM Excel inteligente com 14 abas, automação Python, e inteligência comercial
- Operador: Solo developer + Claude Code
- Idioma: Sempre Português Brasileiro
- Python: `python` (ambiente padrão)

## Motor Duplo

### AIOX-Core (Arsenal)
- Agentes especializados: @pm, @architect, @dev, @qa, @data-engineer, @analyst, @ux
- Tasks reutilizáveis para cada operação do pipeline
- Quality gates em 3 camadas
- Local: `.claude/` (agents, commands, skills)

### GSD (Motor de Execução)
- Ciclo forçado: research -> plan -> execute -> verify
- Commits atômicos por task
- Verificação goal-backward
- Local: `~/.claude/get-shit-done/`

## Domínio: Excel/Python + CRM Comercial B2B

### Fontes de Dados
- **Mercos**: Relatórios de vendas (CUIDADO: nomes de relatórios MENTEM nas datas)
- **SAP**: ERP corporativo — faturamento, produtos, clientes
- **Deskrio**: CRM legado — histórico de atendimentos
- **Excel**: 88+ arquivos históricos, 32 sessões de desenvolvimento

### Equipe Comercial
- MANU DITZEL: SC/PR/RS, 32.5% faturamento
- LARISSA PADILHA: Resto do Brasil, ~45% faturamento, 291 clientes
- JULIO GADRET: RCA externo, 100% FORA do sistema
- DAIANE STAVICKI: Gerente + Key Account, redes/franquias

## Regras Invioláveis

### R1 — Two-Base Architecture (SAGRADA)
- Valor R$ APENAS em registro tipo VENDA
- LOG/interações = SEMPRE R$ 0.00
- Violação causa inflação de 742% (JÁ ACONTECEU)
- NUNCA misturar vendas com log no mesmo cálculo

### R2 — CNPJ = Chave Primária
- 14 dígitos, sem pontuação, zero-padded
- NUNCA armazenar como float (perde precisão)
- Todo cruzamento entre sistemas usa CNPJ normalizado

### R3 — CARTEIRA 46 colunas = IMUTÁVEL
- Não adicionar, não remover, não reordenar as 46 originais
- Blueprint v2 expande para 81 via grupos [+], mantendo as 46 intactas

### R4 — Fórmulas openpyxl em INGLÊS
- CORRETO: =IF(A1>0,"sim","não")
- ERRADO: =SE(A1>0;"sim";"não") ← QUEBRA no openpyxl
- Separador de argumentos: VÍRGULA (não ponto-e-vírgula)

### R5 — NUNCA openpyxl para slicers
- Openpyxl DESTRÓI infraestrutura XML de slicers
- Slicers = XML Surgery (zipfile + lxml) ou manual no Excel

### R6 — Relatórios Mercos MENTEM nos nomes
- SEMPRE conferir "Data inicial" e "Data final" nas linhas 6-7
- "Abril" = Abr+Mai, "Set25" = Out, "Nov" = Set

### R7 — Faturamento = R$ 2.091.000 (CORRIGIDO 2026-03-23)
- Baseline: R$ 2.091.000 (PAINEL CEO DEFINITIVO — auditoria forense 68 arquivos)
- ANTERIOR R$ 2.156.179 SUPERSEDED (diferença de R$ 65K resolvida em CONFLITOS)
- Projeção 2026: R$ 3.377.120 (+69%)
- Q1 2026 real: R$ 459.465
- Qualquer divergência > 0.5% = investigar imediatamente

### R8 — Zero fabricação de dados
- Dados sintéticos classificados em 3 tiers: REAL / SINTÉTICO / ALUCINAÇÃO
- 558 registros já classificados como ALUCINAÇÃO (NUNCA integrar)
- Dados do ChatGPT = ALUCINAÇÃO por padrão (inflação de 742%)

### R9 — Visual LIGHT exclusivamente
- NUNCA dark mode
- Fonte Arial 9pt dados, 10pt headers
- Cores status: ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000
- Cores ABC: A=#00B050, B=#FFFF00, C=#FFC000

### R10 — Validação pós-build obrigatória
- 0 erros de fórmula (#REF!, #DIV/0!, #VALUE!, #NAME?)
- Faturamento total bate com R$ 2.091.000
- Two-Base Architecture respeitada
- CNPJ sem duplicatas
- 14 abas presentes e funcionais
- Testar no Excel real (LibreOffice recalc ≠ Excel recalc)

### R11 — COMMITS ATÔMICOS
- 1 task = 1 commit. Mensagem descritiva em inglês. NUNCA git push (só @devops)

### R12 — NÍVEIS DE DECISÃO
- L1 (autônomo): fix lint, retry, log
- L2 (informar): refactor, novo script, mudança de fórmula
- L3 (LEANDRO APROVA): mudar estrutura de abas, alterar Two-Base, deletar dados, arquivo novo
- Na dúvida → L3

## DE-PARA Vendedores (DECORAR)
- MANU: Manu, Manu Vitao, Manu Ditzel → MANU
- LARISSA: Larissa, Lari, Larissa Vitao, Mais Granel, Rodrigo → LARISSA
- DAIANE: Daiane, Central Daiane, Daiane Vitao → DAIANE
- JULIO: Julio, Julio Gadret → JULIO
- LEGADO: Bruno Gretter, Jeferson Vitao, Patric, Gabriel, Sergio, Ive, Ana → LEGADO

## ENFORCEMENT MECÂNICO [.claude/rules/000-coleira-suprema.md — AUTO-LOADED]

BOOT SEQUENCE OBRIGATÓRIO (NA ORDEM, SEM PULAR):
  1. python scripts/session_boot.py
  2. python scripts/compliance_gate.py
  3. LER docs que compliance_gate.py lista
  4. DECLARAR contexto: "Li N docs. Abas: X. Bloqueadores: Y. Pronto."

COLEIRA SUPREMA: .claude/rules/000-coleira-suprema.md
  Carrega AUTOMATICAMENTE. NÃO PODE IGNORAR. 12 regras + enforcement completo.

## Stack
- Automação: Python 3.12+ (openpyxl, pandas, rapidfuzz)
- Dados: Excel (.xlsx) + JSON intermediário
- Validação: Scripts Python de auditoria
- Slicers: XML Surgery (zipfile + lxml)
- Visualização: HTML dashboards (opcional)

## Configuração GSD
- Mode: YOLO (auto-approve)
- Depth: Standard (5-8 fases)
- Execution: Parallel
- Git Tracking: Yes
- Research: Yes
- Plan Check: Yes
- Verifier: Yes
- AI Models: Quality (Opus para planejamento)

## Documentação de Inteligência
ARQUIVO OBRIGATÓRIO: `BACKUP_DOCUMENTACAO_ANTIGA.md`
Contém TUDO que foi feito antes: briefing, inteligência de negócio, auditoria, roadmap anterior.
SE NÃO LER = vai redescobrir bugs que já foram diagnosticados.
