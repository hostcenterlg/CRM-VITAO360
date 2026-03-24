# MOTOR COMPLETO — CRM VITAO360 INTELIGENTE
# Extracão Forense da Planilha FINAL (6.2 MB, 40 abas, 200K+ fórmulas)
# Data: 2026-03-23 | Fonte: Radiografia automatizada + leitura manual

---

# PARTE 1 — INVENTÁRIO GERAL

## 1.1 Arquivo Fonte
- **Nome**: CRM_VITAO360 INTELIGENTE FINAL OK.xlsx
- **Tamanho**: 6.2 MB
- **Abas totais**: 40 (15 visíveis + 25 ocultas)
- **Fórmulas totais estimadas**: ~210.000+
- **Defined Names**: 21 (16 listas de dropdown + 5 slicers)

## 1.2 Mapa de Abas

### VISÍVEIS (15)
| # | Aba | Rows | Cols | Fórmulas | Função |
|---|-----|------|------|----------|--------|
| 15 | OPERACIONAL | 663 | 23 | 1.981 | Cadastro base + CNPJ normalizado |
| 16 | PROJEÇÃO | 662 | 80 | 3.954 | Metas SAP/igualitárias por cliente/mês |
| 17 | RESUMO META | 23 | 17 | 46 | Totalizadores de faturamento mensal |
| 18 | PAINEL SINALEIRO | 55 | 14 | 131 | Dashboard penetração redes/franquias |
| 19 | SINALEIRO | 665 | 26 | 5.785 | Saúde do cliente (dias vs ciclo) |
| 20 | DRAFT 1 | ~566 | ~60 | ~0 | Staging Mercos (vendas, carteira, ABC) |
| 21 | DRAFT 2 | ~4403 | ~40 | ~0 | Staging Atendimentos (LOG operacional) |
| 22 | DRAFT 3 | ~1528 | ~18 | ~0 | Staging SAP (cadastro, vendas) |
| 23 | FUNIL | ~495 | ~14 | ~0 | Classificação funil de vendas |
| 24 | **CARTEIRA** | **1593** | **144** | **180.513** | **MOTOR CENTRAL — cérebro do CRM** |
| 25 | RNC | 2476 | 15 | 0 | Registro Não-Conformidade (manual) |
| 26 | AGENDA | 670 | 18 | 0 | Agenda diária de atendimentos |
| 27 | LARISSA | 13159 | 40 | 3.830 | LOG consultor Larissa |
| 28 | MANU | 13159 | 40 | 3.830 | LOG consultor Manu |
| 29 | JULIO | 13159 | 40 | 3.820 | LOG consultor Julio |
| 30 | DAIANE | 13159 | 40 | 3.820 | LOG consultor Daiane |

### OCULTAS (25) — INTELIGÊNCIA DO SISTEMA
| # | Aba | Rows | Cols | Função |
|---|-----|------|------|--------|
| 1 | CHECKLIST MOTOR (2) | 100 | 16 | Validação das 92 combinações do motor |
| 2 | CHECKLIST REGRAS (2) | 28 | 7 | 25 módulos da aba REGRAS validados |
| 3 | GAPS MOTOR vs MANUAL (2) | 49 | 6 | 45 combinações sem guia operacional |
| 4 | DECISOES PENDENTES (2) | 30 | 8 | Decisões que Leandro precisa tomar |
| 5 | CHECKLIST MOTOR | 100 | 16 | (Duplicata — versão anterior) |
| 6 | CHECKLIST REGRAS | 28 | 7 | (Duplicata) |
| 7 | GAPS MOTOR vs MANUAL | 49 | 6 | (Duplicata) |
| 8 | DECISOES PENDENTES | 30 | 8 | (Duplicata) |
| 9 | ARQUITETURA 9 DIMENSOES | 43 | 7 | Framework conceitual de 9 dimensões |
| 10 | ESTAGIOS DO FUNIL | 27 | 7 | Definição dos estágios do pipeline |
| 11 | FASES ESTRATEGICAS | 12 | 7 | Fases do ciclo comercial |
| 12 | MAPA MOTOR NOVO | 41 | 8 | Mapa completo do motor v4 |
| 13 | CRUZAMENTO MÊS A MÊS | 495 | 80 | 3.944 fórmulas — cruzamento vendas mensais |
| 14 | Venda Mês a Mês | 494 | 55 | Dados brutos vendas mensais |
| 31 | **MOTOR DE REGRAS** | **98** | **12** | **92 combinações SITUAÇÃO × RESULTADO** |
| 32 | **REGRAS** | **496** | **13** | **25 módulos + tabela tbl_MotorV2** |
| 33 | README | 602 | 7 | Documentação interna do sistema |
| 34 | STATUS | 197 | 7 | Status do projeto / decisões |
| 35 | DASHBOARD | 54 | 14 | 169 fórmulas — dashboard gerencial |
| 36 | MANUAL ATENDIMENTO | 381 | 6 | Manual operacional para consultores |
| 37 | REGRAS VISUAL | 532 | 14 | Regras em formato visual/resumido |
| 38 | Claude Log | 540 | 6 | Log de iterações com Claude |
| 39 | REDES v2 | 307 | 12 | 197 fórmulas — redes/franquias expandido |
| 40 | AUDITORIA | 97 | 8 | Resultados de auditoria |

---

# PARTE 2 — MOTOR DE REGRAS (CÉREBRO)

## 2.1 Visão Geral
- **92 combinações**: 7 SITUAÇÃO × ~14 RESULTADO
- **Versão**: Motor v4 (auditado e corrigido)
- **Gerado**: 04/03/2026
- **Source of Truth**: aba "CHECKLIST MOTOR (2)"

## 2.2 Dimensões do Motor (9 saídas por combinação)

Cada combinação SITUAÇÃO + RESULTADO gera automaticamente:

| # | Dimensão | Descrição | Exemplo |
|---|----------|-----------|---------|
| 1 | ESTÁGIO FUNIL | Onde o cliente está no pipeline | PÓS-VENDA, RETENÇÃO, RESGATE |
| 2 | FASE | Ciclo comercial do cliente | PÓS-VENDA, RECUPERAÇÃO, PROSPECÇÃO |
| 3 | TIPO CONTATO | Classificação da interação | ATEND. CLIENTES ATIVOS, FOLLOW UP |
| 4 | AÇÃO FUTURA | Próxima ação concreta | CONFIRMAR FATURAMENTO E EXPEDIÇÃO |
| 5 | TEMPERATURA | Quão quente está o lead | QUENTE, MORNO, FRIO, CRÍTICO, PERDIDO |
| 6 | FOLLOW-UP (dias) | Racional para o prazo | "D+4 confirmar", "FU 7d manter contato" |
| 7 | GRUPO DASH | Agrupamento para dashboard | (classificação interna) |
| 8 | TIPO AÇÃO | Classificação da atividade | (tipo de ação) |
| 9 | CHAVE | Concatenação para lookup | SITUAÇÃO+RESULTADO |

## 2.3 SITUAÇÃO (7 estados do cliente)

| Status | Critério | Cor |
|--------|----------|-----|
| **ATIVO** | Dias sem compra ≤ 50 | #00B050 (verde) |
| **EM RISCO** | 51-60 dias sem compra | #FFC000 (amarelo) |
| **INAT.REC** | 61-90 dias sem compra | #FFC000 (amarelo escuro) |
| **INAT.ANT** | >90 dias sem compra | #FF0000 (vermelho) |
| **PROSPECT** | Sem histórico de compra | ROXO |
| **LEAD** | Lead qualificado sem compra | ROXO |
| **NOVO** | Primeiro pedido recente | VERDE |

**Fórmula SITUAÇÃO (col M):**
```
=IF(B4="","",
  IF(OR(BD4="",BD4=0),"PROSPECT",
    IF(OR(O4="",O4=0),"ATIVO",
      IF(O4<=50,"ATIVO",
        IF(O4<=60,"EM RISCO",
          IF(O4<=90,"INAT.REC","INAT.ANT"))))))
```

## 2.4 RESULTADO (14 tipos de interação)

| # | Resultado | Significado |
|---|-----------|-------------|
| 1 | VENDA / PEDIDO | Pedido efetivado |
| 2 | ORÇAMENTO | Orçamento enviado |
| 3 | PÓS-VENDA | Acompanhamento pós-compra |
| 4 | CS (SUCESSO DO CLIENTE) | Customer Success — sell out + recompra |
| 5 | RELACIONAMENTO | Rapport / nutrição |
| 6 | FOLLOW UP 7 | Follow-up 7 dias |
| 7 | FOLLOW UP 15 | Follow-up 15 dias |
| 8 | EM ATENDIMENTO | Negociação em andamento |
| 9 | SUPORTE | Problema / RNC |
| 10 | NÃO ATENDE | Tentativa sem sucesso (ligação) |
| 11 | NÃO RESPONDE | Tentativa sem sucesso (WhatsApp) |
| 12 | RECUSOU LIGAÇÃO | Rejeitou chamada |
| 13 | CADASTRO | Cadastro/recadastro |
| 14 | PERDA / FECHOU LOJA | Perda definitiva |

## 2.5 Tabela Completa do Motor (92 combinações)

### ATIVO (14 combinações)
| # | RESULTADO | ESTÁGIO FUNIL | FASE | TIPO CONTATO | AÇÃO FUTURA | TEMP |
|---|-----------|---------------|------|-------------|-------------|------|
| 1 | VENDA/PEDIDO | PÓS-VENDA | PÓS-VENDA | PÓS-VENDA/REL. | CONFIRMAR FATURAMENTO E EXPEDIÇÃO | QUENTE |
| 2 | ORÇAMENTO | ORÇAMENTO | EM ATENDIMENTO | NEGOCIAÇÃO | CONFIRMAR ORÇAMENTO ENVIADO | QUENTE |
| 3 | PÓS-VENDA | PÓS-VENDA | PÓS-VENDA | PÓS-VENDA/REL. | FAZER CS (SUCESSO DO CLIENTE) | QUENTE |
| 4 | CS | CS/RECOMPRA | CS | PÓS-VENDA/REL. | VERIFICAR SELL OUT E CRIAR INTENÇÃO RECOMPRA | QUENTE |
| 5 | RELACIONAMENTO | EM ATENDIMENTO | EM ATENDIMENTO | ATEND. CLIENTES ATIVOS | RAPPORT COM CLIENTE | MORNO |
| 6 | FOLLOW UP 7 | CS/RECOMPRA | CS | FOLLOW UP | COBRAR RETORNO DO CLIENTE | MORNO |
| 7 | FOLLOW UP 15 | CS/RECOMPRA | CS | FOLLOW UP | COBRAR RETORNO DO CLIENTE | MORNO |
| 8 | EM ATENDIMENTO | EM ATENDIMENTO | EM ATENDIMENTO | ATEND. CLIENTES ATIVOS | FECHAR NEGOCIAÇÃO EM ANDAMENTO | MORNO |
| 9 | SUPORTE | EM ATENDIMENTO | EM ATENDIMENTO | ATEND. CLIENTES ATIVOS | RESOLVER PROBLEMA INTERNO E ENVIAR SOLUÇÃO | FRIO |
| 10 | NÃO ATENDE | NÃO ATENDE | EM ATENDIMENTO | ATEND. CLIENTES ATIVOS | 2ª TENTATIVA VIA LIGAÇÃO | FRIO |
| 11 | NÃO RESPONDE | NÃO RESPONDE | EM ATENDIMENTO | ATEND. CLIENTES ATIVOS | 2ª TENTATIVA VIA WHATSAPP | FRIO |
| 12 | RECUSOU LIGAÇÃO | NÃO ATENDE | EM ATENDIMENTO | ATEND. CLIENTES ATIVOS | 2ª TENTATIVA VIA WHATSAPP | FRIO |
| 13 | CADASTRO | EM ATENDIMENTO | EM ATENDIMENTO | ATEND. CLIENTES ATIVOS | CONFIRMAR CADASTRO NO SISTEMA | MORNO |
| 14 | PERDA/FECHOU LOJA | PERDA/NUTRIÇÃO | NUTRIÇÃO | PERDA/NUTRIÇÃO | NENHUMA (ENCERRADO) | PERDIDO |

### EM RISCO (14 combinações)
| # | RESULTADO | ESTÁGIO FUNIL | FASE | TIPO CONTATO | AÇÃO FUTURA | TEMP |
|---|-----------|---------------|------|-------------|-------------|------|
| 15 | VENDA/PEDIDO | RETENÇÃO | SALVAMENTO | ATEND. CLIENTES EM RISCO | CONFIRMAR FATURAMENTO E EXPEDIÇÃO | QUENTE |
| 16 | ORÇAMENTO | RETENÇÃO | SALVAMENTO | NEGOCIAÇÃO | CONFIRMAR ORÇAMENTO ENVIADO | QUENTE |
| 17 | PÓS-VENDA | RETENÇÃO | SALVAMENTO | ATEND. CLIENTES EM RISCO | RAPPORT COM CLIENTE APÓS A VENDA ATÉ RECOMPRAR | MORNO |
| 18 | CS | RETENÇÃO | SALVAMENTO | ATEND. CLIENTES EM RISCO | VERIFICAR SELL OUT E CRIAR INTENÇÃO RECOMPRA | MORNO |
| 19 | RELACIONAMENTO | RETENÇÃO | SALVAMENTO | ATEND. CLIENTES EM RISCO | RAPPORT COM CLIENTE APÓS A VENDA ATÉ RECOMPRAR | MORNO |
| 20 | FOLLOW UP 7 | RETENÇÃO | SALVAMENTO | FOLLOW UP | COBRAR RETORNO DO CLIENTE | MORNO |
| 21 | FOLLOW UP 15 | RETENÇÃO | SALVAMENTO | FOLLOW UP | COBRAR RETORNO DO CLIENTE | MORNO |
| 22 | EM ATENDIMENTO | RETENÇÃO | SALVAMENTO | ATEND. CLIENTES EM RISCO | FECHAR NEGOCIAÇÃO EM ANDAMENTO | MORNO |
| 23 | SUPORTE | RETENÇÃO | SALVAMENTO | ATEND. CLIENTES EM RISCO | RESOLVER PROBLEMA INTERNO E ENVIAR SOLUÇÃO | FRIO |
| 24 | NÃO ATENDE | RETENÇÃO | SALVAMENTO | ATEND. CLIENTES EM RISCO | 2ª TENTATIVA VIA LIGAÇÃO | CRÍTICO |
| 25 | NÃO RESPONDE | RETENÇÃO | SALVAMENTO | ATEND. CLIENTES EM RISCO | 2ª TENTATIVA VIA WHATSAPP | CRÍTICO |
| 26 | RECUSOU LIGAÇÃO | RETENÇÃO | SALVAMENTO | ATEND. CLIENTES EM RISCO | 2ª TENTATIVA VIA WHATSAPP | CRÍTICO |
| 27 | CADASTRO | RETENÇÃO | SALVAMENTO | ATEND. CLIENTES EM RISCO | CONFIRMAR CADASTRO NO SISTEMA | MORNO |
| 28 | PERDA/FECHOU LOJA | PERDA/NUTRIÇÃO | NUTRIÇÃO | PERDA/NUTRIÇÃO | NENHUMA (ENCERRADO) | PERDIDO |

### INAT.REC (14 combinações)
- Estágio: REATIVAÇÃO → Fase: SALVAMENTO
- Tipo Contato: ATEND. CLIENTES INATIVOS
- Temperaturas: QUENTE (venda/orçamento), MORNO (CS/rel/FU), FRIO (suporte), CRÍTICO (não atende/responde/recusou)

### INAT.ANT (14 combinações)
- Estágio: RESGATE → Fase: RECUPERAÇÃO
- Tipo Contato: ATEND. CLIENTES INATIVOS
- Temperaturas: similares a INAT.REC mas tudo CRÍTICO nos "não atende/responde"

### PROSPECT (12 combinações)
- Estágio: PROSPECÇÃO → Fase: PROSPECÇÃO
- Tipo Contato: PROSPECÇÃO
- Temperaturas: QUENTE (venda/orçamento), MORNO (atendimento/FU/cadastro/rel.), FRIO (não atende/responde/recusou/suporte)

### LEAD (12 combinações)
- Similar a PROSPECT

### NOVO (13 combinações)
- Estágio: PÓS-VENDA / EM ATENDIMENTO → Fase: PÓS-VENDA / EM ATENDIMENTO / CS
- Foco em CS obrigatório (D+15 pós-venda, D+30 CS)

---

# PARTE 3 — 25 MÓDULOS DA ABA REGRAS

A aba REGRAS contém **496 linhas** organizadas em 25 módulos que alimentam TODOS os dropdowns, validações e fórmulas do sistema.

## 3.1 Módulos e Defined Names

| # | Módulo | Qtd | Named Range | Células |
|---|--------|-----|-------------|---------|
| 1 | RESULTADO | 14 | LISTA_RESULTADO | REGRAS!$B$2:$B$13 |
| 2 | TIPO CONTATO | 7 | LISTA_TIPO_CONTATO | REGRAS!$B$18:$B$24 |
| 3 | MOTIVO | 22 | LISTA_MOTIVO | REGRAS!$B$28:$B$37 |
| 4 | SITUAÇÃO | 7 | LISTA_SITUACAO | REGRAS!$B$41:$B$47 |
| 5 | FASE | 9 | LISTA_FASE | REGRAS!$B$51:$B$59 |
| 6 | TIPO CLIENTE | 7 | LISTA_TIPO_CLIENTE | REGRAS!$B$105:$B$110 |
| 7 | CONSULTOR | 5 | LISTA_CONSULTOR | REGRAS!$A$88:$A$91 |
| 8 | TENTATIVA | 6 | LISTA_TENTATIVA | REGRAS!$B$63:$B$68 |
| 9 | SINALEIRO | 8 | LISTA_SINALEIRO | REGRAS!$A$72:$A$75 |
| 10 | LISTAS SIMPLES | 5 | LISTA_SIM_NAO / LISTA_SIM_NAO_NA | REGRAS!$B$95:$B$99 |
| 11 | TIPO AÇÃO | 6 | — | — |
| 12 | TIPO PROBLEMA | 8 | — | RNC categories |
| 13 | AÇÃO FUTURA | 22 | LISTA_ACAO_FUTURA | REGRAS!$B$114:$B$120 |
| 14 | TAREFA / DEMANDA | 25 | — | — |
| 15 | SINALEIRO META | 4 | — | Atingimento de meta |
| 16 | **SCORE RANKING** | 6 | — | 6 fatores ponderados (0-100) |
| 17 | **MOTOR DE REGRAS** | 9 | — | 92 combinações (ver Parte 2) |
| 18 | PIRÂMIDE P1-P7 | 8 | — | CULTIVAR > CONQUISTAR > RECUPERAR |
| 19 | CADÊNCIA MENSAL | 5 | — | Distribuição estratégica |
| 20 | JORNADA PÓS-VENDA | 4 | — | Datas invioláveis |
| 21 | REGRA DO IGNORADOR | 6 | — | Impacto tentativas no Score |
| 22 | DECISÕES PENDENTES | 7 | — | Itens aguardando Leandro |
| 23 | CURVA ABC | 4 | LISTA_CURVA_ABC | REGRAS!$B$102:$B$104 |
| 24 | DESEMPATE | 4 | — | Quando Score empata |
| 25 | OPERAÇÃO DIÁRIA | 8 | — | 40 contatos, reciclagem, meta B |

## 3.2 Tabela Estruturada: tbl_MotorV2
- **Localização**: REGRAS!A:M (496 rows)
- **Função**: Lookup table para o motor — qualquer combinação SITUAÇÃO+RESULTADO retorna as 9 dimensões
- **Uso**: XLOOKUP / INDEX-MATCH nas abas CARTEIRA e consultores

---

# PARTE 4 — SCORE RANKING (PRIORIZAÇÃO INTELIGENTE)

## 4.1 Os 6 Fatores (= 100%)

| Fator | Peso | Coluna | Fórmula Resumida |
|-------|------|--------|-----------------|
| **URGÊNCIA** | 30% | EG | Baseado em SITUAÇÃO: INAT.ANT=100, INAT.REC=90, EM RISCO=70, PROSPECT=10, LEAD=10, NOVO=30, ATIVO=40 |
| **VALOR** | 25% | EH | Curva ABC + Tipo Cliente: A+FIDELIZADO=100, A=80, B+MADURO=70, B=50, C=30, sem ABC=10 |
| **FOLLOW-UP** | 20% | EI | Dias desde último follow-up via _xlfn.LET: >30d=100, 15-30=75, 7-15=50, <7=25, sem FU=50 |
| **SINAL** | 15% | EJ | Temperatura: CRÍTICO=90, QUENTE+ecommerce=100, QUENTE=80, MORNO+ecommerce=70, MORNO=50, FRIO=20 |
| **TENTATIVA** | 5% | EK | Protocolo: T4+=100, T3=75, T2=50, T1=25, sem tentativa=10 |
| **SITUAÇÃO** | 5% | EL | EM RISCO=80, ATIVO=40, INAT.REC/ANT=20, outros=10 |

## 4.2 Fórmula SCORE (col EM)
```
=ROUND(
  (URGÊNCIA * 0.30) +
  (VALOR * 0.25) +
  (FOLLOW-UP * 0.20) +
  (SINAL * 0.15) +
  (TENTATIVA * 0.05) +
  (SITUAÇÃO * 0.05)
, 0)
```

## 4.3 Pirâmide de Prioridade P1-P7 (col EN)

| Prioridade | Nome | Critério |
|------------|------|----------|
| **P1** | NAMORO NOVO | Novo cliente em pós-venda/CS |
| **P2** | NEGOCIAÇÃO ATIVA | Em atendimento + orçamento |
| **P3** | PROBLEMA | Suporte/RNC ativo |
| **P4** | CULTIVAR | Cliente ativo em manutenção |
| **P5** | CONQUISTAR | Prospect/Lead em prospecção |
| **P6** | RECUPERAR | Inativo em reativação/resgate |
| **P7** | NUTRIÇÃO | Perda, nutrição passiva |

**Mapeamento para PRIORIDADE visual (col N):**
- P1 NAMORO NOVO → CRÍTICO
- P2 NEGOCIAÇÃO ATIVA → URGENTE
- P3 PROBLEMA → URGENTE
- P4-P7 → pelo Score ranking

---

# PARTE 5 — CARTEIRA (MOTOR CENTRAL — 144 COLUNAS)

## 5.1 Estrutura de Super-Grupos

### GRUPO 1: MERCOS (A-AA) — Identidade + Atendimento
| Coluna | Header | Fonte | Tipo |
|--------|--------|-------|------|
| A | NOME FANTASIA | DRAFT 1 via INDEX-MATCH | Fórmula |
| B | CNPJ | Normalizado de CD | Fórmula |
| C | RAZÃO SOCIAL | DRAFT 1 / DRAFT 3 | Fórmula |
| D | UF | DRAFT 1 / OPERACIONAL | Fórmula |
| E | CIDADE | DRAFT 1 | Fórmula |
| F | EMAIL | DRAFT 1 | Fórmula |
| G | TELEFONE | DRAFT 1 | Fórmula |
| H | DATA CADASTRO | DRAFT 1 | Fórmula |
| I | REDE REGIONAL | DRAFT 1 | Fórmula |
| J | ÚLT REGISTRO MERCOS | DRAFT 1!$AX | Fórmula |
| K | CONSULTOR | DRAFT 1 / DRAFT 3 | Fórmula |
| L | VENDEDOR ÚLTIMO PEDIDO | DRAFT 1 / DRAFT 3 | Fórmula |
| M | **SITUAÇÃO** | **Calculado (dias sem compra)** | **Motor** |
| N | **PRIORIDADE** | **Derivado de EN (P1-P7)** | **Motor** |
| O | DIAS SEM COMPRA | DRAFT 1 | Fórmula |
| P | DATA ÚLTIMO PEDIDO | DRAFT 1 | Fórmula |
| Q | VALOR ÚLTIMO PEDIDO | DRAFT 1 | Fórmula |
| R | CICLO MÉDIO | DRAFT 1!$AS | Fórmula |
| S-W | ECOMMERCE (5 cols) | DRAFT 1 (B2B) | Fórmula |
| X-AA | ATENDIMENTO MERCOS (4 cols) | DRAFT 1 / DRAFT 2 | Fórmula |

### GRUPO 2: VENDAS 2025 (AB-AN) — Timeline Financeiro
| Coluna | Header | Fonte |
|--------|--------|-------|
| AB | TOTAL 2025 | =SUM(AC:AN) |
| AC-AN | Jan-Dez 2025 | DRAFT 1 via INDEX-MATCH |

### GRUPO 3: VENDAS 2026 (AO-BA) — Timeline Projetado
| Coluna | Header | Fonte |
|--------|--------|-------|
| AO | TOTAL 2026 | =SUM(AP:BA) |
| AP-BA | Jan-Dez 2026 | DRAFT 1 via INDEX-MATCH |

### GRUPO 4: RECORRÊNCIA (BB-BI) — Perfil de Compra
| Coluna | Header | Fonte |
|--------|--------|-------|
| BB | TICKET MÉDIO | Array Formula |
| BC | TIPO CLIENTE | DRAFT 1!$BD |
| BD | Nº COMPRAS | DRAFT 1!$AT |
| BE | CURVA ABC | DRAFT 1!$AU |
| BF | MESES POSITIVADO | DRAFT 1!$AV |
| BG | MÉDIA MENSAL | DRAFT 1!$BE |
| BH | TICKET MÉDIO | DRAFT 1!$AW |
| BI | MESES LISTA | — |

### GRUPO 5: FUNIL / PIPELINE (BJ-BY) — Estado Comercial
| Coluna | Header | Fonte |
|--------|--------|-------|
| BJ | **ESTÁGIO FUNIL** | **Array Formula (Motor)** |
| BK | PRÓX FOLLOWUP | DRAFT 2 via XLOOKUP |
| BL | DATA ÚLT ATENDIMENTO | DRAFT 2 via XLOOKUP |
| BM | **AÇÃO FUTURA** | **Array Formula (Motor)** |
| BN | ÚLTIMO RESULTADO | DRAFT 2 via XLOOKUP |
| BO | MOTIVO | DRAFT 2 via XLOOKUP |
| BP | TIPO CLIENTE | DRAFT 1!$BD |
| BQ | TENTATIVA | DRAFT 2 via XLOOKUP |
| BR | **FASE** | **Array Formula (Motor)** |
| BS | **ÚLTIMA RECOMPRA** | **Array Formula** |
| BT | **TEMPERATURA** | **Array Formula (Motor)** |
| BU | DIAS ATÉ CONVERSÃO | =BX-BV |
| BV | DATA 1º CONTATO | DRAFT 2 |
| BW | DATA 1º ORÇAMENTO | Array Formula |
| BX | DATA 1ª VENDA | Array Formula |
| BY | TOTAL TENTATIVAS | Array Formula |

### GRUPO 6: AÇÃO / SINAL (BZ-CB)
| Coluna | Header | Fonte |
|--------|--------|-------|
| BZ | **PRÓX AÇÃO** | **Array Formula (Motor)** |
| CA | AÇÃO DETALHADA | XLOOKUP (com #REF! detectado) |
| CB | **SINALEIRO** | **Calculado (SITUAÇÃO + dias + ciclo)** |

### GRUPO 7: SAP (CC-CQ) — Dados Cadastrais
| Coluna | Header | Fonte |
|--------|--------|-------|
| CC | CÓDIGO DO CLIENTE | DRAFT 3 |
| CD | CNPJ (formatado) | Dado direto |
| CE-CQ | Razão, Cadastro, Atendimento, Bloqueio, Grupo, Gerente, Representante, Vend.Interno, Canal, Tipo, Macro/Microregião, Grupo Chave | DRAFT 3 via INDEX-MATCH |

### GRUPO 8: META / PROJEÇÃO (CR-EF) — Acompanhamento Mensal
| Bloco | Colunas | Conteúdo |
|-------|---------|----------|
| ANUAL | CR-CT | META, REALIZADO, % ALCANÇADO |
| Q1 TOTAL | CU-CW | META SAP TRI, META IGUALIT. TRI, % ALCANÇADO TRI |
| JANEIRO | CX-DH | META SAP, META IGUALIT., SEM1-5, REALIZADO, %SAP |
| FEVEREIRO | DI-DS | Mesma estrutura |
| MARÇO | DT-ED | Mesma estrutura |
| Q1 ÂNCORA | EE-EF | REALIZADO TRI, % TRI SAP |

Todas as META buscam via `XLOOKUP(VALUE($B), PROJEÇÃO!$A, PROJEÇÃO!$col)`.

### GRUPO 9: SCORE & PRIORIDADE v2 (EG-EN)
| Coluna | Header | Fórmula |
|--------|--------|---------|
| EG | URGÊNCIA (30%) | Baseado em SITUAÇÃO |
| EH | VALOR (25%) | Baseado em ABC + TIPO CLIENTE |
| EI | FOLLOW-UP (20%) | Dias desde último FU |
| EJ | SINAL (15%) | TEMPERATURA + ecommerce |
| EK | TENTATIVA (5%) | Protocolo T1-T4+ |
| EL | SITUAÇÃO (5%) | Status simplificado |
| EM | **SCORE** | **Ponderado 0-100** |
| EN | **PRIORIDADE v2** | **P1 a P7** |

---

# PARTE 6 — SINALEIRO (SAÚDE DO CLIENTE)

## 6.1 Fórmula Sinaleiro (col CB da CARTEIRA)
```
=IF(B4="","",
  IF(OR(M4="PROSPECT",M4="LEAD"),"ROXO",
    IF(M4="NOVO","VERDE",
      IF(OR(O4="",O4=0),
        IF(M4="ATIVO","VERDE","ROXO"),
        IF(O4<=R4*0.5,"VERDE",
          IF(O4<=R4,"AMARELO",
            IF(O4<=R4*1.5,"LARANJA","VERMELHO")))))))
```

## 6.2 Faixas
| Cor | Significado | Critério |
|-----|-------------|----------|
| ROXO | Sem histórico | Prospect / Lead / sem dados |
| VERDE | Saudável | Dias ≤ 50% do ciclo OU Novo |
| AMARELO | Atenção | 50-100% do ciclo |
| LARANJA | Alerta | 100-150% do ciclo |
| VERMELHO | Crítico | >150% do ciclo |

## 6.3 Aba SINALEIRO (665 rows, 5.785 fórmulas)
- Fórmulas: IF (6446), SUMIF (1322), RANK (497)
- Calcula ranking por consultor + penetração por rede

## 6.4 PAINEL SINALEIRO (dashboard)
- COUNTIFS para contagem por faixa/consultor
- SUM para totalizadores
- 131 fórmulas agregadoras

---

# PARTE 7 — ABAS DOS CONSULTORES (LARISSA, MANU, JULIO, DAIANE)

## 7.1 Estrutura Idêntica (40 colunas, 13.159 rows)
Cada aba de consultor é um **LOG de atendimentos** com fórmulas inteligentes.

## 7.2 Fórmulas Principais (3.830 cada)
- **IF + OR + IFERROR + XLOOKUP**: Cada registro busca dados da CARTEIRA
- **TODAY()**: 766 referências — fórmulas dinâmicas baseadas na data atual
- **10 validações de dados** por aba (dropdowns controlados por REGRAS)

## 7.3 Colunas com Validação (Dropdowns)
Alimentados pelas Named Ranges:
- LISTA_RESULTADO (14 valores)
- LISTA_TIPO_CONTATO (7 valores)
- LISTA_MOTIVO (22 valores)
- LISTA_SITUACAO (7 valores)
- LISTA_FASE (9 valores)
- LISTA_ACAO_FUTURA (22 valores)
- LISTA_TENTATIVA (6 valores)
- LISTA_CONSULTOR (5 valores)
- LISTA_SIM_NAO (2 valores)
- LISTA_SIM_NAO_NA (3 valores)

---

# PARTE 8 — PROJEÇÃO (METAS SAP + IGUALITÁRIAS)

## 8.1 Estrutura (662 rows × 80 cols, 3.954 fórmulas)
- Todas IFERROR + XLOOKUP
- Busca metas do SAP por CNPJ
- Calcula meta igualitária (divisão uniforme)
- Acompanhamento mensal: JAN-MAR (Q1) implementado

## 8.2 Metas Duplas
- **META SAP**: Meta oficial do SAP por cliente
- **META IGUALITÁRIA**: Distribuição uniforme do target entre clientes
- **% ALCANÇADO**: Realizado / Meta

---

# PARTE 9 — OPERACIONAL (BASE DE CNPJ)

## 9.1 Estrutura (663 rows × 23 cols, 1.981 fórmulas)
- Tabela estruturada: Tabela14
- Fórmulas: SUBSTITUTE (1977) + COUNTIFS (1322)
- **Função principal**: Normalização de CNPJ e contagem de ocorrências
- 6 regras de formatação condicional

---

# PARTE 10 — FLUXO DE DADOS ENTRE ABAS

```
FONTES EXTERNAS
    ├── Mercos → DRAFT 1 (566 clientes, vendas, ABC, ecommerce)
    ├── Atendimentos → DRAFT 2 (4.403 registros, LOG operacional)
    ├── SAP → DRAFT 3 (1.528 clientes, cadastro, vendas)
    └── Funil → FUNIL (495 registros)
         │
         ▼
    OPERACIONAL (663 rows — CNPJ normalizado, base cadastral)
         │
         ├──────────────────────────────────────────────┐
         ▼                                              ▼
    CARTEIRA (1.593 × 144 — MOTOR CENTRAL)         PROJEÇÃO (662 × 80)
    ├── Grupo 1: MERCOS ← DRAFT 1/3                ├── META SAP
    ├── Grupo 2: VENDAS 2025 ← DRAFT 1             ├── META IGUALITÁRIA
    ├── Grupo 3: VENDAS 2026 ← DRAFT 1             └── % ALCANÇADO
    ├── Grupo 4: RECORRÊNCIA ← DRAFT 1                   │
    ├── Grupo 5: FUNIL ← DRAFT 2 + MOTOR                 │
    ├── Grupo 6: AÇÃO ← MOTOR                            │
    ├── Grupo 7: SAP ← DRAFT 3                           │
    ├── Grupo 8: META ← PROJEÇÃO ←────────────────────────┘
    └── Grupo 9: SCORE ← Calculado
         │
         ├──────────────┬──────────────┬──────────────┐
         ▼              ▼              ▼              ▼
    LARISSA         MANU          JULIO         DAIANE
    (LOG 13K)       (LOG 13K)     (LOG 13K)     (LOG 13K)
    ← XLOOKUP da CARTEIRA
         │
         ▼
    SINALEIRO (665 rows — saúde clientes)
    PAINEL SINALEIRO (dashboard penetração)
    RESUMO META (totalizadores)
    DASHBOARD (KPIs gerenciais)
    RNC (registro não-conformidade)
    AGENDA (distribuição diária)

    REGRAS (496 rows — alimenta TUDO via Named Ranges)
    MOTOR DE REGRAS (92 combinações — alimenta CARTEIRA Array Formulas)
    REDES v2 (penetração por rede/franquia)
```

---

# PARTE 11 — FORMATAÇÃO CONDICIONAL

## 11.1 CARTEIRA (57 regras)
Principal aba formatada. Regras incluem:
- Cores por SITUAÇÃO (ATIVO verde, EM RISCO amarelo, INAT vermelho)
- Cores por CURVA ABC (A verde, B amarelo, C laranja)
- Cores por SINALEIRO
- Destaque de células com #REF!
- Barras de progresso para % alcançado

## 11.2 Consultores (21 regras cada)
- Cores por resultado de atendimento
- Destaque de follow-ups atrasados
- Temperatura visual

## 11.3 Outros
- SINALEIRO: 0 regras (cores via fórmula)
- OPERACIONAL: 6 regras
- AGENDA: 18 regras
- RNC: 6 regras

---

# PARTE 12 — PROBLEMAS DETECTADOS

## 12.1 #REF! na coluna CA (AÇÃO DETALHADA)
```
=IFERROR(_xlfn.XLOOKUP($B4,#REF!,#REF!,"",0,-1),"")
```
A referência da fonte foi perdida. Precisa reconectar.

## 12.2 Abas duplicadas
- CHECKLIST MOTOR, CHECKLIST REGRAS, GAPS MOTOR vs MANUAL, DECISOES PENDENTES
- Existem em versão "(2)" e sem sufixo — provável migração incompleta

## 12.3 GAPS conhecidos
- 45 combinações do motor NÃO têm instrução no MANUAL ATENDIMENTO
- Consultora não sabe o que fazer nesses cenários

---

# PARTE 13 — BLUEPRINT SaaS (VISÃO PARA MIGRAÇÃO)

## 13.1 Módulos Mapeados

| Módulo Excel | Serviço SaaS | Prioridade |
|-------------|-------------|------------|
| CARTEIRA (144 cols) | **ClienteService** — CRUD + cálculos | P0 |
| MOTOR DE REGRAS (92 combos) | **MotorService** — Rules Engine | P0 |
| SCORE RANKING (6 fatores) | **ScoreService** — Priorização | P0 |
| SINALEIRO | **SinaleiroService** — Health Monitor | P1 |
| PROJEÇÃO | **MetaService** — Targets + Tracking | P1 |
| DRAFT 1/2/3 | **ImportService** — ETL Pipeline | P1 |
| LOG Consultores | **AtendimentoService** — CRM Core | P0 |
| AGENDA | **AgendaService** — Smart Scheduling | P0 |
| RNC | **RNCService** — Quality Management | P2 |
| DASHBOARD | **DashboardService** — Analytics | P1 |
| REGRAS (25 módulos) | **ConfigService** — System Config | P0 |

## 13.2 Integrações Planejadas

| Sistema | Tipo | O que faz |
|---------|------|-----------|
| **WhatsApp** (via Deskrio/API) | Bidirecional | Enviar mensagens, receber tickets, LOG automático |
| **Mercos API** | Import | Pedidos, vendas, carteira, ABC, ecommerce |
| **SAP** | Import | Cadastro, metas, faturamento |
| **Asana** | Bidirecional | Tasks de follow-up, agenda, RNC |

## 13.3 Agentes de IA Necessários

| Agente | Função | Base de Conhecimento |
|--------|--------|---------------------|
| **Agente Priorizador** | Gera agenda diária inteligente | SCORE + Motor + Sinaleiro |
| **Agente Preditor** | Previsão de churn, recompra | Timeline vendas + ciclo médio |
| **Agente CS** | Customer Success automático | Jornada pós-venda + motor |
| **Agente WhatsApp** | Respostas contextuais | LOG + CARTEIRA + REGRAS |
| **Agente Analytics** | Insights e relatórios | Dashboard + Projeção |
| **Agente Funil** | Gestão de pipeline | FUNIL + Motor + Prioridade |

---

*Documento gerado por @architect via radiografia automatizada da planilha FINAL*
*200K+ fórmulas analisadas | 40 abas mapeadas | 92 combinações do motor documentadas*
