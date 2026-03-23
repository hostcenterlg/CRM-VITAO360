# RESEARCH SUMMARY — CRM VITAO360

## Identidade
- **Nome**: CRM VITAO360 — Inteligencia Comercial
- **Empresa**: VITAO Alimentos, distribuidora B2B de alimentos naturais, Curitiba/PR
- **Operador**: Leandro Garcia (Gerente Comercial) + Claude Code
- **Historico**: 16 meses, 32 sessoes, 88+ arquivos, migrou de ChatGPT (fracasso) para Claude (sucesso)

## Metricas Chave (2025 Real Auditado)
| Metrica | Valor | Fonte |
|---------|-------|-------|
| Faturamento 2025 | R$ 2.091.000 | PAINEL CEO DEFINITIVO |
| Churn mensal | 80% | CRM + SAP |
| Clientes com compra | 488 | CRM |
| Ticket medio | R$ 4.285/ano | Calculado |
| LTV estimado | R$ 2.792 | 1.9 meses x ticket |
| CAC | R$ 433 | Custo equipe / novos |
| ROI projetado 2026 | 10.3x | Motor auditado |
| Conversao funil | 4.5% | 22 contatos → 1 venda |

## Projecao 2026
| Metrica | Valor |
|---------|-------|
| Faturamento | R$ 3.377.120 (+69%) |
| Q1 real | R$ 459.465 |
| Clientes ativos P12 | 207 |
| Investimento equipe | R$ 300.000 |
| Sobra acumulada | R$ 3.077.120 |

## Arquitetura (Planilha FINAL)
- **40 abas** (15 visiveis + 25 ocultas)
- **~210.000 formulas**
- **CARTEIRA**: 1.593 rows x 144 colunas x 180.513 formulas
- **Motor de Regras**: 92 combinacoes (7 SITUACAO x 14 RESULTADO)
- **Score Ranking**: 6 fatores ponderados (0-100)
- **Piramide**: P1-P7 (NAMORO NOVO → NUTRICAO)
- **25 modulos** na aba REGRAS
- **4 abas consultores**: 13.159 rows x 40 cols cada

## Fontes de Dados
| Sistema | Dados | Status |
|---------|-------|--------|
| SAP | Vendas, metas, cadastro | PRIMARIO |
| Mercos | Carteira, vendas, ABC, ecommerce | COMPLEMENTO |
| Deskrio | WhatsApp (15.468 contatos, API aberta) | CONECTADO |
| Sales Hunter | Prospecao | A INTEGRAR |
| CONTROLE_FUNIL | Log atendimentos (manual) | PARCIAL (558 ALUCINACAO) |

## Equipe 2026
- LARISSA: Brasil Interior, ATIVA, 22 novos/mes
- JULIO: Cia Saude + Fitland, ATIVO
- DAIANE: Gerente Redes + Food Channel, NOVA ATRIBUICAO
- MANU: LICENCA MATERNIDADE Q2 — 165 clientes descobertos
- NOVA REP: Contratar Q2
- POS-VENDA/CS: Contratar Q3 (CRITICO — churn 80% → 50%)

## Riscos Conhecidos
1. **Churn 80%** — Maior risco. PV Q3 e a solucao
2. **Manu sai Q2** — 165 clientes / R$778K descobertos
3. **558 ALUCINACAO** — Dados fabricados pelo ChatGPT, NUNCA integrar
4. **Mercos mente** — Nomes de relatorios nao batem com datas reais
5. **openpyxl + slicers** — Destroi infraestrutura XML
6. **JULIO fora do sistema** — 100% via WhatsApp pessoal

## Documentos de Referencia
1. `BRIEFING-COMPLETO.md` — Transferencia total de conhecimento
2. `INTELIGENCIA_NEGOCIO_CRM360.md` — Regras de negocio extraidas
3. `BACKUP_DOCUMENTACAO_ANTIGA.md` — Historico completo
4. `data/docs/MOTOR_COMPLETO_CRM_VITAO360.md` — Motor inteiro documentado
5. `data/docs/BLUEPRINT_SKILLS_SAAS.md` — Blueprint do SaaS
6. `.planning/DECISIONS.md` — 15 decisoes tecnicas
7. `.cache/deskrio_api_spec.json` — Spec completa API Deskrio
8. `.cache/radiografia_completa.json` — Radiografia da planilha FINAL
