# CRM VITAO360

## What This Is

Sistema CRM completo em Excel para a VITAO Alimentos, distribuidora B2B de alimentos naturais sediada em Curitiba/PR. O CRM gerencia 489 clientes, 4 consultores comerciais, 8 redes de franquias (923 lojas), e integra dados de 3 sistemas externos (Mercos, SAP, Deskrio). Este é o rebuild definitivo de 16 meses de trabalho incremental que nunca atingiu 100% devido a limitações de contexto.

## Current Milestone: v2.0 Motor Operacional SaaS

**Goal:** Extrair toda inteligência do Excel (92 regras, Score, Sinaleiro, Agenda) para Python funcional que roda local com dados reais.

**Target features:**
- Motor de Regras Python (92 combinações SITUAÇÃO × RESULTADO → 9 dimensões)
- Score Ranking (6 fatores ponderados → 0-100 + Pirâmide P1-P7)
- Sinaleiro (saúde do cliente: dias sem compra vs ciclo médio)
- Agenda Inteligente (40-60 atendimentos/consultor/dia priorizados por Score)
- Import de dados (xlsx → base unificada Python)
- Export (base processada → xlsx atualizado)
- Projeção vs Meta (SAP + igualitária por cliente/mês)

## Core Value

O CRM deve cruzar dados de vendas, atendimentos e prospecção de múltiplas fontes em uma CARTEIRA unificada que permite aos consultores comerciais operar com visibilidade total — sem fabricar dados, sem duplicar valores financeiros, sem perder histórico.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

- ✓ CARTEIRA com 46 colunas e 489 clientes — existing (Fase 1)
- ✓ Two-Base Architecture: separação VENDA (R$) vs LOG (R$ 0.00) — existing
- ✓ CNPJ normalizado como chave primária (14 dígitos, zfill) — existing
- ✓ DRAFT 2 (Agenda/Quarentena) como staging area — existing (Fase 3)
- ✓ AGENDA com 20 colunas e distribuição territorial automática — existing (Fase 6)
- ✓ SINALEIRO REDES com 923 lojas, 8 redes, 13.216 fórmulas — existing (Fase 8)
- ✓ SINALEIRO INTERNO com 661 clientes e 5 slicers via XML Surgery — existing
- ✓ Motor de Matching cascata: CNPJ → Telefone → Nome Fuzzy → Padrão Rede — existing
- ✓ Classificação ABC: A >= R$2.000/mês, B >= R$500, C < R$500 — existing
- ✓ Roteamento de consultores por território — existing
- ✓ DE-PARA vendedores (Manu/Larissa/Daiane/Julio/Legado) — existing

### Active

<!-- Current scope. Building toward these. -->

- [ ] PROJEÇÃO reconstruída com 18.180 fórmulas dinâmicas (CRÍTICO)
- [ ] Faturamento mensal validado contra R$ 2.091.000 (PAINEL 2025)
- [ ] Timeline mensal por cliente populada (Jan-Dez 2025)
- [ ] LOG completo com ~11.758 registros (atualmente 13.4%)
- [ ] DASH redesenhada com 3 blocos compactos (~45 rows)
- [ ] E-commerce cruzado e integrado na CARTEIRA
- [ ] REDE/REGIONAL preenchido para todos os clientes
- [ ] #REF! corrigidos nas REDES_FRANQUIAS_v2
- [ ] COMITÊ com metas 2026 integradas
- [ ] Validação final: 0 erros de fórmula em todas as abas
- [ ] Blueprint v2 da CARTEIRA expandida para 81 colunas (8 grupos)
- [ ] Integração dos 3.540 contatos históricos retroativos
- [ ] Integração dos 10.484 registros do CONTROLE_FUNIL
- [ ] Integração dos 5.329 tickets Deskrio no LOG
- [ ] Julio Gadret integrado no sistema (atualmente 100% fora)

### Out of Scope

- (REMOVIDO 2026-04-25) ~~Migração para software web/SaaS — sistema permanece em Excel com Python para processamento~~ — SaaS está em PROD desde Mar/2026 em crm-vitao360.vercel.app. Ver MASTER_PLAN.md
- Dashboard em tempo real — operação é batch (exports manuais dos sistemas)
- Automação de exports do Mercos/SAP/Deskrio — dependem de acesso que não temos
- Mobile app — consultores usam Excel no desktop
- Integração com ExactSales — sistema foi descontinuado (Out/2024)
- Dark mode — tema LIGHT exclusivamente por decisão do Leandro

## Context

- **16 meses de desenvolvimento** (Jan/2025 — Fev/2026) em 32 sessões via claude.ai
- **Primeira tentativa** com ChatGPT fracassou: alucinações massivas, inflação de 742%
- **Two-Base Architecture** inventada para eliminar duplicação de R$ 664K → R$ 3.62M
- **CRM v11** existe e opera parcialmente — partes funcionam, partes quebradas
- **88+ arquivos Excel** como fontes de dados, agora organizados em `data/sources/`
- **873 arquivos totais** copiados e organizados por categoria
- **Relatórios Mercos mentem nos nomes** — "Abril" contém Abril+Maio, "Set25" contém Outubro
- **Openpyxl destrói slicers** — usar XML Surgery (zipfile + lxml) para preservar
- **Fórmulas openpyxl devem ser em INGLÊS** (IF, SUMIF, VLOOKUP, não SE, SOMASE, PROCV)
- **CNPJ nunca como float** — perde precisão. Sempre string com zfill(14)
- **558 registros classificados como ALUCINAÇÃO** — não integrar no sistema
- **Mercos não tem CNPJ** nos relatórios de vendas — match por Nome Fantasia/Razão Social

## Constraints

- **Tech Stack**: Python (openpyxl, pandas, rapidfuzz) + Excel — sistema é planilha, não software
- **Fórmulas**: Devem ser em INGLÊS para openpyxl (IF, SUMIF, VLOOKUP)
- **Slicers**: NUNCA usar openpyxl — apenas XML Surgery (zipfile + lxml)
- **Dados**: Zero fabricação. Classificação 3-tier obrigatória (REAL / SINTÉTICO / ALUCINAÇÃO)
- **Faturamento**: Validar SEMPRE contra R$ 2.091.000 (PAINEL 2025). Divergência > 0.5% = investigar
- **Visual**: Tema LIGHT, Arial 9pt dados, 10pt headers. Cores: ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000
- **CARTEIRA**: 46 colunas IMUTÁVEIS — Blueprint v2 expande via grupos [+], não altera as 46
- **Header Mercos**: Linha 10 (skiprows=9)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Two-Base Architecture | Eliminar inflação de 742% por duplicação de valores em interações | ✓ Good |
| CNPJ como chave primária (string 14 dígitos) | Único identificador confiável entre Mercos, SAP e Deskrio | ✓ Good |
| XML Surgery para slicers | Openpyxl destrói infraestrutura XML ao salvar | ✓ Good |
| RODRIGO = LARISSA no CRM | Rodrigo opera canal "Mais Granel" que pertence à Larissa | ✓ Good |
| Rebuild completo via Claude Code/DEUS | Contexto infinito resolve o problema de perda entre sessões | — Pending |
| Blueprint v2 (81 colunas em 8 grupos) | Expandir sem quebrar as 46 originais | — Pending |
| DASH redesign (3 blocos vs 8 "Frankenstein") | Layout atual ilegível com 164 rows × 19 cols | — Pending |

---
*Last updated: 2026-02-15 after initialization via DEUS-AIOS*
