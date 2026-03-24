# ÍNDICE MESTRE — PROJETO VITAO 360
## GPS DE NAVEGAÇÃO PARA TODAS AS CONVERSAS

**Última atualização:** 16/FEV/2026  
**Total de arquivos:** 139  
**Duplicatas identificadas:** ~22 arquivos  
**Arquivos vigentes (usar):** ~95  
**Arquivos obsoletos (ignorar):** ~44

---

## INSTRUÇÕES PARA O CLAUDE

> **REGRA #1:** Antes de abrir QUALQUER arquivo do projeto, consulte este índice primeiro.  
> **REGRA #2:** Arquivos marcados ❌ OBSOLETO são versões antigas — NUNCA usar como fonte de dados.  
> **REGRA #3:** Arquivos marcados ✅ VIGENTE são a fonte de verdade para aquela categoria.  
> **REGRA #4:** Na dúvida entre dois arquivos similares, usar o de MAIOR tamanho ou data mais recente.  
> **REGRA #5:** CNPJ normalizado (14 dígitos sem pontuação) é a chave primária universal.

---

## CATEGORIA 1: CRM MASTER FILES (Arquivos estruturais — o coração do sistema)

### ✅ VIGENTES — USAR ESTES

| Arquivo | Tamanho | Conteúdo | Quando usar |
|---------|---------|----------|-------------|
| `CRM_INTELIGENTE_VITAO360_V12_2.xlsx` | 3.9MB | **CRM V12 COM DADOS** — 15 abas (SINALEIRO+PROJEÇÃO integrados). CARTEIRA 8.305r×263c, AGENDA 5.000r×30c, DRAFT1 505r×45c, DRAFT2 502r×31c, REGRAS 283r×13c | **ARQUIVO MASTER — referência principal do CRM** |
| `CRM_INTELIGENTE_VITAO360_V12_1.xlsx` | 7.9MB | **CRM V12 TEMPLATE VAZIO** — mesmas 15 abas, 0 registros. Formatação, fórmulas, slicers e validações preservadas | Template para recriar CRM limpo |
| `CONTROLE_FUNIL_JAN2026.xlsx` | 14.2MB | **25 abas operacionais.** LOG (10.484r×42c), REGRAS, DASH, META, bases SAP/Mercos, logs por consultor | Produtividade, atendimentos, funil, LOG histórico |
| `DRAFT1_ATUALIZADO_FEV2026.xlsx` | 166KB | Base master 505r × 45c. Auditado 27/28 PASS | Carteira de clientes vigente |
| `DRAFT2_POPULADO_DADOS_REAIS_VITAO360_3.xlsx` | 1.1MB | **DRAFT 2 REAL** — 6.775r × 31c + RESUMO + RASTREABILIDADE. Pipeline completo (Mercos+Deskrio+Vendas) | DADOS REAIS de atendimentos — PENDENTE integração no V12 |
| `MEGA_CRUZAMENTO_VITAO360_FEV2026.xlsx` | 201KB | 504r × 80c cruzamento completo + resumo mensal + cobertura fontes | Validação cruzada vendas mês a mês |
| `VITAO360_SINALEIRO_POPULADO.xlsx` | 1.1MB | Sinaleiro com dados populados | Análise de penetração por rede |
| `PROJECAO_INTERNO_1566.xlsx` | 1.1MB | Projeção interna 1.566 registros | Metas e projeções internas |
| `Carteira_detalhada_de_clientes_atualizado_janeiro_2026.xlsx` | 117KB | Carteira Mercos atualizada JAN/2026 | Dados Mercos mais recentes |
| `Carteira_detalhada_de_clientes_propects.xlsx` | 1.1MB | 816 prospects franquias | Prospecção de novos clientes |
| `Clientes_PADRONIZADO.xlsx` | 52KB | CNPJs normalizados | Referência de normalização |
| `TUDO_EM_GRAOS_CRUZAMENTO.xlsx` | 12KB | Cruzamento rede Tudo em Grãos | Análise específica desta rede |

### ⚠️ VERSÕES ANTERIORES (manter como backup, não usar como fonte primária)

| Arquivo | Tamanho | Motivo | Substituído por |
|---------|---------|--------|-----------------|
| `CRM_INTELIGENTE_VITAO_360_V11_POPULADO.xlsx` | 3.5MB | V11 com dados (13 abas, sem SINALEIRO/PROJEÇÃO) | V12_2 |
| `CRM_INTELIGENTE_VITAO_360_V11_LIMPO.xlsx` | 3.5MB | V11 template | V12_1 |
| `VITAO360_SINALEIRO_534_INTEGRADO.xlsx` | 451KB | Sinaleiro versão 534 | `VITAO360_SINALEIRO_POPULADO.xlsx` |
| `VITAO360_SINALEIRO_534_INTEGRADO_1.xlsx` | 451KB | Duplicata do 534 | `VITAO360_SINALEIRO_POPULADO.xlsx` |
| `SINALEIRO_INTERNO_VITAO360.xlsx` | 82KB | Versão interna menor | `VITAO360_SINALEIRO_POPULADO.xlsx` |
| `SINALEIRO_INTERNO_VITAO360_1.xlsx` | 82KB | Duplicata | `VITAO360_SINALEIRO_POPULADO.xlsx` |
| `PROJECAO_534_INTEGRADA.xlsx` | 350KB | Projeção versão 534 | `PROJECAO_INTERNO_1566.xlsx` |
| `PROJECAO_534_INTEGRADA_1.xlsx` | 350KB | Duplicata da 534 | `PROJECAO_INTERNO_1566.xlsx` |
| `PROJECAO_INTERNO_1566_1.xlsx` | 1.1MB | Duplicata da 1566 | `PROJECAO_INTERNO_1566.xlsx` |
| `PROJECAO_POPULADA_1566.xlsx` | 917KB | Versão anterior populada | `PROJECAO_INTERNO_1566.xlsx` |

### ❌ OBSOLETOS — NÃO USAR (versões antigas)

| Arquivo | Motivo | Substituído por |
|---------|--------|-----------------|
| `Carteira_detalhada_de_clientes.xls` (247KB) | Formato antigo .xls | `Carteira_..._atualizado_janeiro_2026.xlsx` |
| `Carteira_detalhada_de_clientes.xlsx` (94KB) | Versão sem data, menor | `Carteira_..._atualizado_janeiro_2026.xlsx` |
| `Carteira_detalhada_de_clientes_16_01.xlsx` (69KB) | Superado pela versão JAN/2026 | `Carteira_..._atualizado_janeiro_2026.xlsx` |
| `Carteira_detalhada_de_clientes_16_01.txt` (91KB) | Versão texto da mesma | `Carteira_..._atualizado_janeiro_2026.xlsx` |
| `Atualização_27_01_2025__Carteira_detalhada_de_clientes.xlsx` (121KB) | Data JAN/2025 (1 ano atrás) | `Carteira_..._atualizado_janeiro_2026.xlsx` |
| `DRAFT1_POPULADO_V5_TELEFONES_2.xlsx` (156KB) | Versão V5, superada | `DRAFT1_ATUALIZADO_FEV2026.xlsx` |
| `MEGA_CRUZAMENTO_VITAO360_1.xlsx` (196KB) | Versão anterior | `MEGA_CRUZAMENTO_VITAO360_FEV2026.xlsx` |

---

## CATEGORIA 2: DADOS SAP (4 arquivos — todos vigentes)

| Arquivo | Tamanho | Conteúdo | Quando usar |
|---------|---------|----------|-------------|
| `BASE_SAP__VENDA_MES_A_MES_2025.xlsx` | 60KB | Vendas mês a mês 2025 por cliente | Análise de sazonalidade, tendências |
| `BASE_SAP__META_E_PROJEÇÃO_2026___02__INTERNO__2026.xlsx` | 942KB | Metas e projeções 2026 | Módulo PROJEÇÃO, metas por consultor |
| `BASE_SAP_CLIENTES_SEM_ATENDIMENTO_.xlsx` | 3.0MB | Clientes sem atendimento | Identificar gaps de cobertura |
| `BASE_SAPE__CARTEIRA_CLIENTE_INTERNO_COM_VENDA_.xlsx` | 2.9MB | Carteira SAP com vendas | Cruzamento SAP × Mercos |

---

## CATEGORIA 3: RELATÓRIOS MERCOS — VENDAS MENSAIS (12 meses)

> **Padrão de nomenclatura:** `Relatorio_de_vendas_{Mês}_.xlsx`  
> **Atenção:** Alguns meses têm "elatorio" (sem R) — são válidos, apenas typo no nome.

### ✅ VIGENTES — 1 por mês

| Mês | Arquivo | Tamanho |
|-----|---------|---------|
| MAR/25 | `Relatorio_vendas_março_2025.xlsx` | 11KB |
| ABR/25 | `Relatorio_vendas_ABril_2025.xlsx` | 19KB |
| MAI/25 | `Relatorio_de_vendas_Maio_.xlsx` | 15KB |
| JUN/25 | `Relatorio_de_vendas_Junho_.xlsx` | 18KB |
| JUL/25 | `Relatorio_de_vendas_Julho_.xlsx` | 16KB |
| AGO/25 | `elatorio_de_vendas_Agosto_.xlsx` | 18KB |
| SET/25 | `Relatorio_de_vendas_Setembro_25.xlsx` | 19KB |
| OUT/25 | `Relatorio_de_vendas_de__outubro_.xlsx` | 19KB |
| NOV/25 | `relatorio_de_vendas_novembro_.xlsx` | 18KB |
| DEZ/25 | `Relatorio_de_vendas_dezembro_.xlsx` | 14KB |
| JAN/26 | `Relatorio_vendas_janeiro_2026.xlsx` | 12KB |

### ❌ OBSOLETOS

| Arquivo | Motivo | Substituído por |
|---------|--------|-----------------|
| `elatorio_de_vendas_Maio_.xlsx` (15KB) | Duplicata de Maio com typo | `Relatorio_de_vendas_Maio_.xlsx` |
| `Relatorio_de_vendas_Setembro_.xlsx` (18KB) | Versão anterior de SET | `Relatorio_de_vendas_Setembro_25.xlsx` |
| `RELATORIO_DE_VENDAS_JANEIRO_2026.xlsx` (15KB) | Duplicata MAIÚSCULA de JAN/26 | `Relatorio_vendas_janeiro_2026.xlsx` |
| `Relatorio_de_Vendas_2025.txt` (107KB) | Versão texto consolidada | Usar os .xlsx mensais individuais |

---

## CATEGORIA 4: RELATÓRIOS MERCOS — POSITIVAÇÃO MENSAL (12 meses)

> **Padrão:** `Positivacao_de_Clientes_{Mês}.xlsx`

### ✅ VIGENTES — 1 por mês (todos vigentes, sem duplicatas)

| Mês | Arquivo | Tamanho |
|-----|---------|---------|
| FEV/25 | `Positivacao_de_Clientes_fevereiro_2025.xlsx` | 12KB |
| MAR/25 | `Positivacao_de_Clientes_Março_.xlsx` | 12KB |
| ABR/25 | `Positivacao_de_Clientes_Abril_.xlsx` | 14KB |
| MAI/25 | `Positivacao_de_Clientes_Maio.xlsx` | 17KB |
| JUN/25 | `Positivacao_de_Clientes_Junho.xlsx` | 20KB |
| JUL/25 | `Positivacao_de_Clientes_Julho.xlsx` | 17KB |
| AGO/25 | `Positivacao_de_Clientes_Agosto.xlsx` | 21KB |
| SET/25 | `Positivacao_de_Clientes_Setembro_.xlsx` | 20KB |
| OUT/25 | `Positivacao_de_Clientes_Outubro_.xlsx` | 21KB |
| NOV/25 | `Positivacao_de_Clientes__Novembro_.xlsx` | 22KB |
| DEZ/25 | `Positivacao_de_Clientes_Dezembro_2025.xlsx` | 19KB |
| JAN/26 | `Positivacao_de_Clientes_Janeiro_2026.xlsx` | 14KB |

### ⚠️ POSSÍVEL DUPLICATA

| Arquivo | Motivo |
|---------|--------|
| `POSITIVAÇÃO_DE_CLIENTES_.xlsx` (18KB) | Sem mês no nome — verificar se é consolidado ou duplicata |

---

## CATEGORIA 5: RELATÓRIOS MERCOS — CURVA ABC MENSAL

> **Padrão:** `Curva_ABC_{Mês}.xlsx`

### ✅ VIGENTES — 1 por mês

| Mês | Arquivo | Tamanho |
|-----|---------|---------|
| MAR/25 | `Curva_ABC__Março_2025.xlsx` | 11KB |
| ABR/25 | `Curva_ABC_Abril_.xlsx` | 14KB |
| MAI/25 | `Curva_ABC_Maio.xlsx` | 16KB |
| JUN/25 | `Curva_ABC__Junho_.xlsx` | 18KB |
| JUL/25 | `Curva_ABC_Julho_.xlsx` | 16KB |
| AGO/25 | `Curva_ABC__Agosto_.xlsx` | 19KB |
| SET/25 | `Curva_ABC__Setembro_.xlsx` | 18KB |
| OUT/25 | `Curva_ABC__Outubro_.xlsx` | 19KB |
| NOV/25 | `Curva_ABC_Novembro_.xlsx` | 20KB |
| DEZ/25 | `Curva_ABC__Dezembro_.xlsx` | 13KB |
| JAN/26 | `Curva_ABC__janeiro_2026_.xlsx` | 14KB |
| ANUAL | `Curva_ABC_2025_Anual.xlsx` | 46KB |

### ❌ OBSOLETOS

| Arquivo | Motivo | Substituído por |
|---------|--------|-----------------|
| `Curva_ABC_Março_.xlsx` (11KB) | Duplicata de MAR sem ano | `Curva_ABC__Março_2025.xlsx` |
| `Curva_ABC_janeiro_2026.xlsx` (13KB) | Duplicata de JAN/26 | `Curva_ABC__janeiro_2026_.xlsx` |
| `Curva_ABC.xls` (14KB) | Formato antigo .xls sem mês | Usar os mensais específicos |

---

## CATEGORIA 6: RELATÓRIOS MERCOS — E-COMMERCE / ACESSOS MENSAIS

> **Padrão:** `Acesso_ao_Ecomerce_{Mês}.xlsx`  
> **Atenção:** Typos frequentes — "Acessop" (com P), "Ecomerce" (sem segundo C). São válidos.

### ✅ VIGENTES — 1 por mês

| Mês | Arquivo | Tamanho |
|-----|---------|---------|
| MAR/25 | `Acesso_ao_Ecomerce_Março_.xlsx` | 12KB |
| ABR/25 | `Acessop_ao_Ecomerce_Abril_.xlsx` | 15KB |
| MAI/25 | `Acessop_ao_Ecomerce_Maio.xlsx` | 15KB |
| JUN/25 | `Acesso_ao_Ecomerce_junho.xlsx` | 19KB |
| JUL/25 | `Acesso_ao_Ecomerce_Julho_.xlsx` | 16KB |
| AGO/25 | `Acesso_ao_Ecomerce_Agosto.xlsx` | 18KB |
| SET/25 | `Acesso_ao_Ecomerce_Setembro_.xlsx` | 19KB |
| NOV/25 | `Acesso_ao_Ecomerce_Novembro_.xlsx` | 23KB |
| DEZ/25 | `Acesso_ao_ecomerce_Dezembro_2025.xlsx` | 20KB |
| JAN/26 | `Acesso_ao_ecomerce_janeiro_2026.xlsx` | 16KB |

### ❌ OBSOLETOS

| Arquivo | Motivo | Substituído por |
|---------|--------|-----------------|
| `Acesso_ao_Ecomerce_junho_.xlsx` (15KB) | Duplicata JUN menor | `Acesso_ao_Ecomerce_junho.xlsx` (19KB) |
| `Acesso_ao_Ecomerce_Dezembro_.xlsx` (11KB) | Versão DEZ sem ano | `Acesso_ao_ecomerce_Dezembro_2025.xlsx` |
| `Acessos_ao_Ecomerce_Dezembro_.xlsx` (11KB) | Outra duplicata DEZ | `Acesso_ao_ecomerce_Dezembro_2025.xlsx` |
| `Acessos_ao_Ecomerce_Dezembro_.txt` (1KB) | Versão texto, 1KB apenas | `Acesso_ao_ecomerce_Dezembro_2025.xlsx` |
| `Acesso_ao_ecomerce_Setembro_.txt` (10KB) | Versão texto | `Acesso_ao_Ecomerce_Setembro_.xlsx` |
| `rELATORIO_DE_ACESSOS_NO_ECOMERCE_JANEIRO_2026.xlsx` (19KB) | Nome inconsistente | `Acesso_ao_ecomerce_janeiro_2026.xlsx` |

> **⚠️ OUTUBRO AUSENTE:** Não há arquivo de e-commerce para OUT/25. Verificar com Leandro.

---

## CATEGORIA 7: RELATÓRIOS MERCOS — ATENDIMENTOS

### ✅ VIGENTES

| Arquivo | Tamanho | Conteúdo |
|---------|---------|----------|
| `Relatorio_de_Atendimentos_Mercos_2025.xlsx` | 177KB | Atendimentos consolidado 2025 — FONTE PRINCIPAL |
| `rELATORIO_DE_ATENDIMENTOS_REGISTRADOS_NO_MERCOS_.xlsx` | 38KB | Versão parcial/filtrada |
| `rELATORIO_MERCOS_30_01_2025.xlsx` | 490KB | Snapshot de 30/JAN/2025 |

### ❌ OBSOLETO

| Arquivo | Motivo |
|---------|--------|
| `Relatorio_de_Atendimentos_Mercos_2025.txt` (332KB) | Versão texto do .xlsx de 177KB |

---

## CATEGORIA 8: DADOS DESKRIO / WHATSAPP (12 arquivos)

### ✅ VIGENTES — todos são partes do export do Deskrio

| Arquivo | Tamanho | Conteúdo |
|---------|---------|----------|
| `exporttickets19012026.xlsx` | 69KB | Export principal 19/JAN/2026 |
| `exporttickets19012026_1.xlsx` a `_11.xlsx` | 8-82KB cada | Partes 1 a 11 do mesmo export |

> **NOTA:** São 12 arquivos que juntos formam o export completo de tickets WhatsApp do Deskrio. Precisam ser concatenados para análise completa. Total estimado: ~540KB de dados.

### 📄 COMPLEMENTARES

| Arquivo | Tamanho | Conteúdo |
|---------|---------|----------|
| `PAINEL_DE_ATIVIDADES_ATENDIMENTO_VS_VENDAS.pdf` | 389KB | Dashboard visual Deskrio (77.805 msgs) — APENAS IMAGEM |
| `RELATORIO_COMPLETO_WHATSAPP_2025.md` | 8KB | Documentação do WhatsApp 2025 |

---

## CATEGORIA 9: DOCUMENTAÇÃO CRM (10 arquivos — todos vigentes)

| Arquivo | Tamanho | Função | Prioridade de leitura |
|---------|---------|--------|----------------------|
| `README.md` | 10KB | Visão geral do projeto | 🔴 Ler sempre na 1ª conversa |
| `README_COMPLETO_PROJETO.md` | 20KB | Documentação técnica completa | 🔴 Referência principal |
| `DOCUMENTACAO_COMPLETA_CRM.md` | 21KB | Spec técnica das abas/colunas | 🔴 Antes de mexer no Excel |
| `PRD_COMPLETO_CRM_VITAO.md` | 15KB | Product Requirements Document | 🟡 Requisitos de negócio |
| `USER_GUIDE.md` | 11KB | Manual do usuário | 🟡 Para entender fluxo |
| `INDICE_GERAL_COMPLETO.md` | 11KB | Índice anterior (desatualizado) | 🟢 Referência histórica |
| `Playbook_Vendas_Vitao_2025.docx` | 17KB | Playbook de vendas | 🟡 Regras comerciais |
| `MANUAL_AGENDA_COMERCIAL_VITAO_v3_FINAL.md` | 26KB | Spec da AGENDA (20 colunas) | 🔴 Para trabalhar AGENDA |
| `CONTEXTO_RAPIDO_AGENDA_VITAO_v3.md` | 3KB | Resumo rápido da AGENDA | 🟢 Quick reference |
| `README_APRESENTACAO.md` | 5KB | Context da apresentação JSX | 🟢 Específico |

---

## CATEGORIA 10: AGENDA / PROMPTS (4 arquivos)

| Arquivo | Tamanho | Função |
|---------|---------|--------|
| `PROMPT_PADRAO_AGENDA_COMERCIAL.md` | 4KB | Prompt para gerar agenda semanal (24 colunas A-X) |
| `PROMPT_PADRAO_AGENDA_COMERCIAL.txt` | 3KB | ❌ DUPLICATA em .txt do .md acima |
| `PROMPT_PADRAO_AGENDA_SEMANAL.txt` | 4KB | Variante do prompt semanal |
| `PROMPT_CONTINUAR_AGENDA_COMERCIAL.md` | 6KB | Prompt para continuar agenda existente |

---

## CATEGORIA 11: AUDITORIAS / ANÁLISES (17 arquivos)

### ✅ VIGENTES

| Arquivo | Tamanho | Conteúdo |
|---------|---------|----------|
| `AUDITORIA_GLOBAL_CRM_VITAO360_V11.docx` | 28KB | Auditoria completa V11 — DOCUMENTO PRINCIPAL |
| `AUDITORIA_DRAFT1_FEV2026.docx` | 10KB | Auditoria específica DRAFT1 (27/28 PASS) |
| `DOC_SINALEIRO_COMPLETA.docx` | 39KB | Documentação do SINALEIRO |
| `ARVORE_PROBLEMAS_CRM_COMPLETA.docx` | 13KB | 25 demandas operacionais mapeadas |
| `COMITE_CONFERENCIA_METODOLOGIA.md` | 7KB | Metodologia de auditoria célula-a-célula |
| `CONSOLIDACAO_TODOS_PROBLEMAS_VERIFICADA.md` | 10KB | Lista consolidada de problemas |
| `SUMARIO_PROBLEMAS_CHURN.md` | 8KB | Análise de churn |
| `AJUSTE_FUNIL_POR_STATUS.md` | 12KB | Regras de ajuste de funil |
| `EXTRACAO_COMPLETA_NOTEBOOKLM_VITAO.md` | 17KB | Extração de conhecimento NotebookLM |
| `EXTRACAO_ESTRUTURAL_CONVERSA_CRUZAMENTO.md` | 26KB | Log conversa cruzamento |
| `EXTRACAO_SISTEMATICA_COMITE.md` | 5KB | Extração do comitê |
| `EXTRACAO_VERIFICADA_BLACK_FRIDAY.md` | 5KB | Análise Black Friday |
| `DOCUMENTO_MESTRE_ATENDIMENTOS_VITAO.md` | 42KB | Documento mestre de atendimentos |

### ❌ OBSOLETOS (duplicatas com sufixo __1_, __2_)

| Arquivo | Motivo |
|---------|--------|
| `ANALISE_MOVIMENTACAO_COMPLETA__1_.md` (15KB) | Duplicata do original |
| `ANALISE_MOVIMENTACAO_COMPLETA__2_.md` (15KB) | Duplicata do original |
| `ANALISE_DEFINITIVA_100_COMPLETA__1_.md` (7KB) | Duplicata do original |
| `ANALISE_COMPLETA_CONVERSAS_CRM.docx` (17KB) | Superado pela AUDITORIA_GLOBAL |
| `ANALISE_PROFUNDA_LINHA_POR_LINHA.docx` (8KB) | Superado pela AUDITORIA_GLOBAL |

---

## CATEGORIA 12: OUTROS / CONFIGURAÇÃO

| Arquivo | Tamanho | Conteúdo | Status |
|---------|---------|----------|--------|
| `orchestrator_config.yaml` | 17KB | Config do orquestrador CRM | ✅ Vigente |
| `DADOS_ANO_COMPLETO_AJUSTADO.json` | 3KB | Dados anuais JSON | ✅ Vigente |
| `ApresentacaoVitao.jsx` | 28KB | Apresentação React | ✅ Vigente |
| `CAPACIDADE_VENDA_CONSULTOR_EXECUTIVO_v2.docx` | 27KB | Benchmark de capacidade | ✅ Vigente |
| `Produtos_por_pedidos_2025.xlsx` | 524KB | Mix de produtos por pedido | ✅ Vigente |
| `ATUALIZACAO_DEZEMBRO_2025.md` | 4KB | Log atualização DEZ/25 | ✅ Vigente |
| `RESUMO_FINAL_DADOS_DISPONIVEIS.md` | 10KB | Inventário de dados | ✅ Vigente |
| `produtos_por_pedidos_2025.txt` (776KB) | Versão texto | ❌ Duplicata do .xlsx |
| `relatorio.xls` (34KB) | Nome genérico, sem contexto | ⚠️ Verificar conteúdo |
| `relatorio_1.xls` (22KB) | Nome genérico, sem contexto | ⚠️ Verificar conteúdo |

---

## CATEGORIA 13: LOGS DE CONVERSAS (adicionar conforme gerar)

| Arquivo | Data | Escopo |
|---------|------|--------|
| `LOG_CONVERSA_LAYOUT_UNIFICADO_43COLS.md` | Anterior | Layout unificado 43 colunas |
| `SPEC_LAYOUT_UNIFICADO_DRAFT2_v1.docx` | Anterior | Spec do DRAFT2 |
| `LOG_CONVERSA_DASHBOARD_PRODUTIVIDADE.md` | 16/FEV/2026 | Dashboard V11 + PRODUTIVIDADE + Gap Analysis |

---

## RESUMO DE LIMPEZA RECOMENDADA

### Arquivos que podem ser REMOVIDOS do projeto novo (não migrar):

**Carteiras obsoletas (5):**
1. `Carteira_detalhada_de_clientes.xls`
2. `Carteira_detalhada_de_clientes.xlsx`
3. `Carteira_detalhada_de_clientes_16_01.xlsx`
4. `Carteira_detalhada_de_clientes_16_01.txt`
5. `Atualização_27_01_2025__Carteira_detalhada_de_clientes.xlsx`

**CRM versões anteriores (4):**
6. `CRM_INTELIGENTE_VITAO_360_V11_LIMPO.xlsx` (superado por V12_1)
7. `CRM_INTELIGENTE_VITAO_360_V11_POPULADO.xlsx` (superado por V12_2)
8. `DRAFT1_POPULADO_V5_TELEFONES_2.xlsx` (superado por DRAFT1_FEV2026)
9. `MEGA_CRUZAMENTO_VITAO360_1.xlsx` (superado por FEV2026)

**Sinaleiro/Projeção duplicatas (6):**
10. `VITAO360_SINALEIRO_534_INTEGRADO.xlsx` (superado por SINALEIRO_POPULADO)
11. `VITAO360_SINALEIRO_534_INTEGRADO_1.xlsx` (duplicata)
12. `SINALEIRO_INTERNO_VITAO360.xlsx` (superado por SINALEIRO_POPULADO)
13. `SINALEIRO_INTERNO_VITAO360_1.xlsx` (duplicata)
14. `PROJECAO_534_INTEGRADA.xlsx` (superado por INTERNO_1566)
15. `PROJECAO_534_INTEGRADA_1.xlsx` (duplicata)
16. `PROJECAO_INTERNO_1566_1.xlsx` (duplicata)
17. `PROJECAO_POPULADA_1566.xlsx` (superado por INTERNO_1566)

**Relatórios duplicatas (9):**
18. `elatorio_de_vendas_Maio_.xlsx`
19. `Relatorio_de_vendas_Setembro_.xlsx`
20. `RELATORIO_DE_VENDAS_JANEIRO_2026.xlsx`
21. `Relatorio_de_Vendas_2025.txt`
22. `Relatorio_de_Atendimentos_Mercos_2025.txt`
23. `Curva_ABC_Março_.xlsx`
24. `Curva_ABC_janeiro_2026.xlsx`
25. `Curva_ABC.xls`
26. `rELATORIO_DE_ACESSOS_NO_ECOMERCE_JANEIRO_2026.xlsx`

**E-commerce duplicatas (5):**
27. `Acesso_ao_Ecomerce_junho_.xlsx`
28. `Acesso_ao_Ecomerce_Dezembro_.xlsx`
29. `Acessos_ao_Ecomerce_Dezembro_.xlsx`
30. `Acessos_ao_Ecomerce_Dezembro_.txt`
31. `Acesso_ao_ecomerce_Setembro_.txt`

**Análises/docs duplicadas (4):**
32. `ANALISE_MOVIMENTACAO_COMPLETA__1_.md`
33. `ANALISE_MOVIMENTACAO_COMPLETA__2_.md`
34. `ANALISE_DEFINITIVA_100_COMPLETA__1_.md`
35. `PROMPT_PADRAO_AGENDA_COMERCIAL.txt`

**Outros (2):**
36. `produtos_por_pedidos_2025.txt`
37. `relatorio.xls` / `relatorio_1.xls` (verificar antes)

> **Total: ~37 arquivos removíveis → projeto cairia de 139 para ~102 arquivos**

---

## MAPA RÁPIDO — QUAL ARQUIVO USAR PRA QUÊ?

| Eu preciso de... | Abrir este arquivo |
|-------------------|-------------------|
| CRM completo com dados | `CRM_INTELIGENTE_VITAO360_V12_2.xlsx` (3.9MB, 15 abas) |
| CRM template vazio (fórmulas/slicers) | `CRM_INTELIGENTE_VITAO360_V12_1.xlsx` (7.9MB) |
| Base de clientes atualizada | `DRAFT1_ATUALIZADO_FEV2026.xlsx` |
| DRAFT 2 real populado (6.775r) | `DRAFT2_POPULADO_DADOS_REAIS_VITAO360_3.xlsx` |
| Log de interações/atendimentos | `CONTROLE_FUNIL_JAN2026.xlsx` → aba LOG |
| Vendas mês X | `Relatorio_de_vendas_{Mês}_.xlsx` |
| Positivação mês X | `Positivacao_de_Clientes_{Mês}.xlsx` |
| Curva ABC mês X | `Curva_ABC_{Mês}.xlsx` |
| E-commerce mês X | `Acesso_ao_Ecomerce_{Mês}.xlsx` |
| Metas/projeções 2026 | `BASE_SAP__META_E_PROJEÇÃO_2026.xlsx` |
| Vendas históricas SAP | `BASE_SAP__VENDA_MES_A_MES_2025.xlsx` |
| WhatsApp/Deskrio tickets | `exporttickets19012026*.xlsx` (12 partes) |
| Sinaleiro populado | `VITAO360_SINALEIRO_POPULADO.xlsx` |
| Projeção interna | `PROJECAO_INTERNO_1566.xlsx` |
| Franquias/prospects | `Carteira_detalhada_de_clientes_propects.xlsx` |
| Sinaleiro doc completa | `DOC_SINALEIRO_COMPLETA.docx` |
| Regras de negócio | `DOCUMENTACAO_COMPLETA_CRM.md` |
| Estrutura AGENDA | `MANUAL_AGENDA_COMERCIAL_VITAO_v3_FINAL.md` |
| Gerar agenda semanal | `PROMPT_PADRAO_AGENDA_COMERCIAL.md` |
| Benchmark capacidade | `CAPACIDADE_VENDA_CONSULTOR_EXECUTIVO_v2.docx` |
| Mix de produtos | `Produtos_por_pedidos_2025.xlsx` |
| Auditoria CRM V11 | `AUDITORIA_GLOBAL_CRM_VITAO360_V11.docx` |
| Problemas mapeados | `ARVORE_PROBLEMAS_CRM_COMPLETA.docx` |
| Validação cruzada | `MEGA_CRUZAMENTO_VITAO360_FEV2026.xlsx` |
| Dashboard HTML | Gerar na conversa (arquivo de output, não knowledge) |
