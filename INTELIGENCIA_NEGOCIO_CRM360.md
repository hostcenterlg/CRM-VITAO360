# INTELIGENCIA DO NEGOCIO - CRM VITAO360
**Gerado em: 17/02/2026 | 10 fases completas | 154.302 formulas**

---

## ONDE ESTA CADA COISA

### 1. CEREBRO DO PROJETO (decisoes e regras)
| Arquivo | O que contem |
|---------|-------------|
| `.planning/STATE.md` | **250+ decisoes tecnicas**, todas as regras de negocio, contexto acumulado |
| `.planning/ROADMAP.md` | Roadmap com 10 fases, 43 requisitos, criterios de sucesso |
| `.planning/PROJECT.md` | Visao geral do projeto, stakeholders, objetivos |

### 2. PESQUISA E ANALISE (por fase)
| Fase | Pesquisa | O que descobriu |
|------|----------|----------------|
| 01-projecao | `01-RESEARCH.md` | 19.224 formulas intactas no V12, estrutura PROJECAO |
| 02-faturamento | `02-RESEARCH.md` | SAP vs Mercos, 11 armadilhas Mercos, merge strategy |
| 03-timeline-mensal | `03-RESEARCH.md` | DRAFT 1 structure, ABC classification, INDEX/MATCH |
| 04-log-completo | `04-RESEARCH.md` | CONTROLE_FUNIL + Deskrio + sinteticos, 20.830 records |
| 05-dashboard | `05-RESEARCH.md` | 3 blocos compactos, KPIs, COUNTIFS |
| 06-e-commerce | `06-RESEARCH.md` | Mercos B2B portal, 1.075 records, 64.6% match rate |
| 07-redes-franquias | `07-RESEARCH.md` | 20 redes + SEM GRUPO, SAP Cadastro, VLOOKUP F:J |
| 08-comite-metas | `08-RESEARCH.md` | Metas 2026, RATEIO, COMITE formulas |
| 09-blueprint-v2 | `09-RESEARCH.md` | 263 colunas CARTEIRA, 6 super-grupos, motor inteligencia |
| 10-validacao-final | `10-RESEARCH.md` | Audit clean, V31 comparison, layout analysis |

**Caminho**: `.planning/phases/{fase}/{num}-RESEARCH.md`

### 3. DADOS PROCESSADOS (JSONs intermediarios)
| Arquivo | Conteudo |
|---------|----------|
| `data/output/phase01/sap_data_extracted.json` | Dados SAP extraidos (metas, vendas, clientes) |
| `data/output/phase02/sap_vendas.json` | Vendas SAP mês a mês |
| `data/output/phase02/mercos_vendas.json` | Vendas Mercos mês a mês |
| `data/output/phase02/sap_mercos_merged.json` | **MERGE FINAL** SAP+Mercos (537 clientes) |
| `data/output/phase03/abc_classification.json` | Classificacao ABC dos clientes |
| `data/output/phase04/controle_funil_classified.json` | LOG classificado (10.434 registros) |
| `data/output/phase04/deskrio_normalized.json` | Deskrio normalizado (4.240 tickets) |
| `data/output/phase04/log_final_validated.json` | **LOG FINAL** validado (20.830 registros) |
| `data/output/phase06/ecommerce_raw.json` | E-commerce bruto (1.075 acessos) |
| `data/output/phase06/ecommerce_matched.json` | E-commerce cruzado com clientes |
| `data/output/phase09/v12_formula_audit.json` | Auditoria formulas V12 (263 colunas) |
| `data/output/phase09/carteira_column_spec.json` | Spec completa CARTEIRA |
| `data/output/phase10/confronto_v13_v31.json` | Confronto V13 vs V31 (CNPJs, clientes) |
| `data/output/phase10/delivery_report.json` | Relatorio entrega final |

### 4. SCRIPTS COM LOGICA DE NEGOCIO
| Script | Logica que contem |
|--------|-------------------|
| `scripts/phase01/` | Extracao SAP, validacao PROJECAO |
| `scripts/phase02/` | ETL Mercos, merge SAP-First, armadilhas |
| `scripts/phase03/` | DRAFT 1 population, ABC, INDEX/MATCH |
| `scripts/phase04/` | LOG integration, dedup, Deskrio normalize |
| `scripts/phase05/` | DASH formulas, KPIs, COUNTIFS |
| `scripts/phase06/` | E-commerce ETL, 5-level matching |
| `scripts/phase07/` | Redes/Franquias, VLOOKUP population |
| `scripts/phase08/` | COMITE metas, RATEIO toggle |
| `scripts/phase09/` | CARTEIRA 134K formulas, motor inteligencia, AGENDA, SCORE |
| `scripts/phase10/` | Audit, confronto, layout fix, V14 generation |

### 5. DOCUMENTOS EXTERNOS (auditoria V31)
**Local**: `Area de Trabalho/auditoria conversas sobre agenda atendimento draft 2/`
| Documento | Conteudo |
|-----------|----------|
| `ANATOMIA_ATENDIMENTO_VITAO360` | 1 venda = 13 contatos + 47 tasks + 3h43 |
| `BLUEPRINT_FORENSE_REGRAS_VITAO360` | 63 combinacoes regras, 5 jornadas templates |
| `EXTRACAO_FORENSE_CRM_VITAO360` | 94.4% completude dados, mapeamento campos |
| `LOG_AUDITORIA_V12_REBUILD` | 129.199 formulas em 15 tabs, trio columns |
| `PLAYBOOK_EXCELENCIA_100_DRAFT_AGENDA` | 30+ tentativas falhas, metodologia |
| `CRM_V12_POPULADO_V31` | Versao referencia com layout superior |

---

## REGRAS DE NEGOCIO PRINCIPAIS

### REGRA #1: AGENDA DIARIA INTELIGENTE
O CRM existe para gerar 40-60 atendimentos priorizados por consultor por dia.
- Gestor (Leandro) passa agenda de manha
- Consultor devolve no fim do dia com resultados
- Resultados alimentam ciclo do dia seguinte

### REGRA #2: TWO-BASE ARCHITECTURE
- Valores financeiros (R$) APENAS na aba DRAFT 1 / VENDAS
- LOG e DRAFT 2 SEMPRE R$ 0.00
- CARTEIRA puxa via INDEX/MATCH, nunca duplica valores

### REGRA #3: SCORE RANKING (6 fatores = 100%)
| Fator | Peso | Fonte |
|-------|------|-------|
| URGENCIA | 30% | Dias sem comprar vs ciclo medio |
| VALOR | 25% | Faturamento real do cliente |
| FOLLOWUP | 20% | Dias desde ultimo contato |
| SINAL | 15% | Sinaleiro (ROXO/VERMELHO/AMARELO/VERDE) |
| TENTATIVA | 5% | Numero de tentativas de contato |
| SITUACAO | 5% | Fase do funil atual |

### REGRA #4: MOTOR DE REGRAS
- 63 combinacoes: SITUACAO (9) x RESULTADO (7)
- Gera automaticamente: ACAO FUTURA, TIPO CONTATO, PROX FOLLOWUP
- Tab REGRAS: linhas 6-20 (followup), 221-283 (SITUACAO x RESULTADO)

### REGRA #5: SINALEIRO (penetracao %)
| Cor | Significado |
|-----|-------------|
| ROXO | Penetracao 0% (inativo total) |
| VERMELHO | Penetracao < 30% |
| AMARELO | Penetracao 30-70% |
| VERDE | Penetracao > 70% |

### REGRA #6: CARTEIRA 6 SUPER-GRUPOS
1. MERCOS (B-R) - dados cadastrais Mercos
2. FUNIL (S-AQ) - classificacao funil, tipo, consultor
3. ATENDIMENTO (AR-BI) - historico contatos
4. SAP (BJ-BY) - dados SAP cadastro
5. FATURAMENTO (BZ-JC) - 12 meses x 15 sub-colunas
6. INTELIGENCIA (JD-JI) - SCORE, TEMPERATURA, COVERAGE, ALERTA, ACAO, FOLLOWUP

### REGRA #7: CONSULTORES
| Consultor | Clientes | Notas |
|-----------|----------|-------|
| LARISSA | 224 | Principal |
| HEMANUELE (MANU) | 170+10 | Dual-name: MANU DITZEL alias |
| JULIO GADRET | 66 | 100% fora do sistema |
| DAIANE STAVICKI | 62 | Canonical (nao CENTRAL-DAIANE) |

### REGRA #8: FONTES DE DADOS
| Sistema | Dados | Prioridade |
|---------|-------|------------|
| SAP | Vendas mensais, metas, cadastro | PRIMARIO (fonte da verdade) |
| Mercos | Carteira, complemento vendas, e-commerce | COMPLEMENTO |
| Deskrio | Tickets suporte (chat proprio) | COMPLEMENTO |
| CONTROLE_FUNIL | Log atendimentos (manual) | COMPLEMENTO |

---

## NUMEROS-CHAVE DO PROJETO

| Metrica | Valor |
|---------|-------|
| Total formulas | 154.302 |
| Abas | 13 |
| Clientes (CNPJs) | 554 |
| Registros LOG | 20.830 |
| Redes/Franquias | 20 + SEM GRUPO |
| Consultores | 4 ativos + 3 esporadicos |
| Fases executadas | 10 |
| Planos executados | 33 |
| Requisitos atendidos | 43 |

---

## LIMITACOES CONHECIDAS

1. **Cobertura limitada**: V13 tem 554 CNPJs (V31 tem 5.460) — V13 foi construido com dataset filtrado SAP+Mercos merge
2. **Faturamento PAINEL**: R$ 2.156.179 (PAINEL DE ATIVIDADES — SUPERSEDED) nao batia com nenhuma fonte unica (SAP -3.08%, Mercos -12%, Merged +15.65%). Baseline corrigido para R$ 2.091.000 (CORRIGIDO 2026-03-23, auditoria forense 68 arquivos — diferença de R$ 65K resolvida na aba CONFLITOS)
3. **E-commerce**: Outubro e Maio 2025 AUSENTES (sem arquivo encontrado)
4. **Julio Gadret**: 100% fora do sistema — dados muito limitados
5. **558 registros ALUCINACAO**: do CONTROLE_FUNIL — descartados
6. **openpyxl nao recalcula**: formulas precisam ser recalculadas no Excel real

---

*Documento gerado automaticamente pelo pipeline CRM-VITAO360*
*Para detalhes completos, consultar STATE.md (250+ decisoes tecnicas)*
