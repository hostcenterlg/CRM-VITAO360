# BRIEFING COMPLETO — CRM VITAO360
# Transferência Total de Conhecimento para Construção
# Data: 15/02/2026 | Fonte: 19 documentos + 32 sessões + 88 arquivos Excel

---

# PARTE 1 — HISTÓRIA E CONTEXTO

## 1.1 O que é a VITAO Alimentos
Distribuidora B2B de alimentos naturais embalados, sediada em Curitiba/PR. Vende para lojas de produtos naturais, franquias e redes em todo o Brasil. Opera com 4 consultores comerciais internos + 1 RCA externo.

## 1.2 O problema original (Outubro/2024)
O CRM anterior (ExactSales, SaaS) foi encerrado. Consequências:
- Perda TOTAL do histórico de atendimentos de 354 clientes
- 60-90 dias de dados de contato perdidos
- Dados preservados: vendas, ciclo médio, positivações, acesso e-commerce, cadastros

## 1.3 Primeira tentativa fracassada (Nov/2024)
Leandro tentou reconstruir com ChatGPT: mais de 100 iterações, dados fabricados (alucinações massivas), valores inflados em 742% por duplicação. Resultado: lixo.

## 1.4 Virada para Claude (Dez/2024)
Migrou para Claude. Reduziu de 100+ iterações para 5-8 por entrega. Inventou a "Two-Base Architecture" que eliminou a duplicação de 742%.

## 1.5 Construção incremental (Jan/2025 — Fev/2026)
16 meses de trabalho em 8 fases, tudo via claude.ai (sem Claude Code). O problema: a janela de contexto resetava a cada conversa, forçando recriação constante. Em 32 sessões entre 06-12/Fev/2026, o sistema atingiu a versão 11. Mas nunca ficou 100% — sempre faltava algo porque o contexto acabava.

## 1.6 Estado atual (15/Fev/2026)
CRM v11 existe e opera parcialmente. Partes funcionam, partes estão quebradas ou incompletas. Este briefing é a transferência completa de tudo que existe para um novo ambiente (Claude Code/DEUS) finalmente terminar o projeto.

---

# PARTE 2 — EQUIPE COMERCIAL

| CONSULTOR | TIPO | TERRITÓRIO | % FAT | STATUS | OBSERVAÇÕES |
|-----------|------|-----------|-------|--------|-------------|
| MANU DITZEL | Interno | SC/PR/RS | 32.5% | Ativa | Licença maternidade próxima. Cobertura pendente. |
| LARISSA PADILHA | Interno | Resto do Brasil (sem redes) | ~45% | Ativa | Sobrecarga: 291 clientes (~58/dia, máx é 50). Opera canal "Mais Granel" com Rodrigo. |
| JULIO GADRET | RCA Externo | Brasil (presencial) | ~10% | 100% FORA do sistema | Opera via WhatsApp pessoal. Cia Saúde + Fitland exclusivo. Zero no Deskrio/Mercos. |
| DAIANE STAVICKI | Gerente + Key Account | Brasil | ~12.5% | Ativa | Foco redes/franquias: Divina Terra, Biomundo, Mundo Verde, Vida Leve, Tudo em Grãos |

**IMPORTANTE:** No sistema Deskrio, "Rodrigo" aparece com 952 tickets (17.9% do total). Rodrigo NÃO é vendedor — é operador do canal "Mais Granel 🧡" que pertence à Larissa. RODRIGO = LARISSA no CRM.

---

# PARTE 3 — ARQUITETURA DO SISTEMA

## 3.1 Fluxo de dados
```
FONTES EXTERNAS (exports manuais)
    |
    v
MERCOS (ERP: vendas, positivação, ABC, e-commerce, carteira, atendimentos)
SAP (cadastro, vendas mês a mês, metas 2026, clientes sem atendimento)
DESKRIO (WhatsApp Business: 77.805 mensagens, 5.425 conversas)
    |
    v
DRAFT 1 (Mercos) + DRAFT 2 (Agenda) + DRAFT 3 (SAP)
    |
    v
CARTEIRA (46 colunas — motor central, 489 clientes)
    |
    +-----+------+-------+--------+
    |     |      |       |        |
    v     v      v       v        v
  AGENDA  LOG  PROJEÇÃO  DASH   SINALEIRO
                                (923 lojas)
```

## 3.2 Two-Base Architecture (regra fundamental)
Separação absoluta entre dados financeiros e interações:
- **BASE_VENDAS**: Registros tipo VENDA carregam valor R$ real
- **LOG**: Registros de interação (ligação, WhatsApp, visita, etc.) SEMPRE com R$ 0.00
- Motivo: antes da separação, cada interação duplicava o valor da venda. Resultado: R$ 664K virava R$ 3.62M (inflação de 742%)
- Regra: valor financeiro APENAS no registro tipo VENDA. NUNCA em outro tipo de interação.

## 3.3 Chave primária
CNPJ normalizado: 14 dígitos sem pontuação, sem espaços. Exemplo: `04351343000169`
Todo cruzamento entre sistemas usa CNPJ como âncora.

---

# PARTE 4 — NÚMEROS DE REFERÊNCIA (VERDADE ABSOLUTA)

Fonte: PAINEL DE ATIVIDADES (Dashboard Executivo 2025). Estes são os números corretos.

## 4.1 Faturamento mensal
```
JAN: R$  80.000    FEV: R$  95.000    MAR: R$ 110.000    ABR: R$ 150.000
MAI: R$ 180.000    JUN: R$ 220.000    JUL: R$ 200.000    AGO: R$ 230.000
SET: R$ 210.000    OUT: R$ 280.000    NOV: R$ 260.000    DEZ: R$ 141.179
TOTAL: R$ 2.156.179
```

## 4.2 Métricas operacionais
```
Vendas totais 2025:      957 pedidos (902 no PAINEL — divergência conhecida de fonte)
Atendimentos 2025:       10.634
Mensagens WhatsApp 2025: 77.805 (Deskrio)
Conversas únicas:        5.425
Orçamentos:              1.419 (67.4% converteram em venda)
Follow-ups:              1.610 (1.7 por venda)
Clientes carteira:       489 (105 ativos + 80 inat.recentes + 304 inat.antigos)
Redes franquias:         8 redes, 923 lojas (107 carteira ativa + 816 prospects)
Taxa recompra:           20.3%
CAC:                     R$ 532
ROI anual:               347%
Ticket médio:            R$ 2.389
Pipeline real:           10 contatos/venda, 17 dias, 78 mensagens/jornada
Capacidade estimada:     3 vendas/dia/consultor
```

## 4.3 Sinaleiro de penetração por rede
```
REDE              | LOJAS | SINALEIRO% | COR       | META 6M
FIT LAND          | 89    | 29.8%      | VERMELHO  | 10%
DIVINA TERRA      | 85    | 10.0%      | VERMELHO  | 5%
VIDA LEVE         | 81    | 8.0%       | VERMELHO  | 3%
TUDO EM GRÃOS     | 25    | 6.2%       | VERMELHO  | 10%
CIA DA SAÚDE      | 163   | 2.6%       | VERMELHO  | 3%
BIOMUNDO          | 167   | 1.4%       | VERMELHO  | 2%
MUNDO VERDE       | 199   | 1.4%       | VERMELHO  | 2%
ARMAZÉM FITSTORE  | 114   | 0%         | ROXO      | 1%

Fórmula: Sinaleiro% = Fat.Real / (Total_Lojas × R$525/mês × 11 meses) × 100
Faixas: ROXO (<1%) → VERMELHO (1-40%) → AMARELO (40-60%) → VERDE (>60%)
Cadência: ROXO=1x/sem WA+Lig | VERMELHO=2x/sem | AMARELO=1x/sem | VERDE=Mensal
```

## 4.4 Projeção 2026
```
Vendas projetadas:     3.168 (+231%)
Faturamento projetado: R$ 5.7M (+164%)
Vendas/dia/consultor:  3 (vs ~1 em 2025)
```

---

# PARTE 5 — O QUE JÁ FOI CONSTRUÍDO E FUNCIONA

## 5.1 CARTEIRA (Fase 1) ✅ OPERACIONAL
- Motor central do CRM
- 46 colunas IMUTÁVEIS, 489 clientes
- Blocos: Identificação(8) → Atribuição(2) → Status(7) → Último Pedido(4) → Performance(4) → Fat.Mensal(12) → E-commerce(4) → Classificações(6) → CRM/Funil(3) → Acompanhamento(3)
- Classificação ABC: A >= R$2.000/mês, B >= R$500, C < R$500
- Tipo cliente: NOVO / EM DESENVOLVIMENTO / RECORRENTE / FIDELIZADO
- Regras de roteamento por consultor implementadas

## 5.2 LOG (Fase 2) ⚠️ PARCIALMENTE OPERACIONAL
- Sistema append-only (nunca deletar, apenas adicionar)
- Chave composta: DATA + CNPJ + RESULTADO (dedup)
- 1.581 registros de 11.758 esperados (13.4% populado)
- Faltam: logs antigos do CONTROLE_FUNIL (10.484 registros) e tickets Deskrio (5.329)
- 3.540 contatos históricos foram gerados retroativamente para cobrir os 60-90 dias perdidos
- Julio 100% fora do sistema

## 5.3 DRAFT 2 — Agenda/Quarentena (Fase 3) ✅ OPERACIONAL
- Staging area funcional: Draft 1 (Mercos), Draft 2 (operacional), Draft 3 (SAP)
- Regra: nunca modificar dados diretamente no CRM — sempre via DRAFT → validação → LOG

## 5.4 DASH (Fase 4) ❌ PRECISA REDESIGN
- Layout atual: 8 blocos, 164 rows × 19 cols — chamado de "Frankenstein"
- Decisão: APAGAR e reconstruir com 3 blocos compactos (~45 rows)

## 5.5 AGENDA (Fase 6) ✅ OPERACIONAL
- 20 colunas, distribuição territorial automática
- Limite 40 atendimentos/dia por consultor
- Manual v3 FINAL documentado

## 5.6 SINALEIRO (Fase 8) ✅ OPERACIONAL
- 13.216 fórmulas com 0 erros validados
- 923 lojas, 8 redes

## 5.7 SINALEIRO INTERNO ✅ OPERACIONAL
- 661 clientes, 5 slicers reais via XML Surgery

---

# PARTE 6 — O QUE ESTÁ QUEBRADO OU INCOMPLETO

## 6.1 PROJEÇÃO ZERADA (CRÍTICO)
18.180 fórmulas PERDIDAS. Só tem dados estáticos de janeiro.

## 6.2 DIVERGÊNCIA DE FATURAMENTO
Gap de R$ 6.790 (~0.3%) entre dados combinados e PAINEL.

## 6.3 TIMELINE MENSAL VAZIA
Vendas mês a mês por cliente não preenchidas.

## 6.4 LOG INCOMPLETO
1.581 de 11.758 registros (13.4%).

## 6.5 E-COMMERCE PARCIAL
Dados existem mas não integrados na CARTEIRA.

## 6.6 #REF! NAS REDES_FRANQUIAS_v2

## 6.7 REDE/REGIONAL VAZIA

---

# PARTE 7 — FONTES DE DADOS DISPONÍVEIS (88+ ARQUIVOS)

## 7.1 Relatórios de vendas Mercos (12 arquivos)
- Header na LINHA 10 (skiprows=9)
- NÃO TEM CNPJ — match por Nome Fantasia/Razão Social

### ARMADILHAS CRÍTICAS:
```
ARQUIVO                              | CONTÉM REALMENTE  | AÇÃO
Relatorio_vendas_ABril_2025.xlsx     | Abril + Maio      | Filtrar SOMENTE month==4
elatorio_de_vendas_Maio_.xlsx        | Duplicata exata   | DESCARTAR
Relatorio_de_vendas_Setembro_25.xlsx | OUTUBRO           | DESCARTAR
relatorio_de_vendas_novembro_.xlsx   | SETEMBRO          | DESCARTAR
Relatorio_vendas_janeiro_2026.xlsx   | Até 19/01 (35)    | DESCARTAR
RELATORIO_DE_VENDAS_JANEIRO_2026.xlsx| Até 29/01 (78)    | USAR ESTE
```

## 7.2-7.9 (Positivação, ABC, E-commerce, Deskrio, SAP, CONTROLE_FUNIL, outros)
Ver briefing completo para detalhes de cada fonte.

---

# PARTE 8 — BLUEPRINT v2 DA CARTEIRA (81 colunas, 8 grupos)

Expandiu de 46 para 81 colunas com grupos expansíveis [+].
10 fixas (A-J) + 8 grupos: Identificação, Vida Comercial, Timeline Mensal, Jornada, Ecommerce, SAP, Operacional, Comitê.

---

# PARTE 9 — MOTOR DE MATCHING

Cascata: CNPJ Exato (100%) → Telefone (85%) → Nome Fuzzy/rapidfuzz (70-100%) → Padrão de Rede/regex (75-90%).

DE-PARA vendedores:
```
MANU: Manu, Manu Vitao, Manu Ditzel → MANU
LARISSA: Larissa, Lari, Larissa Vitao, Mais Granel, Rodrigo → LARISSA
DAIANE: Daiane, Central Daiane, Daiane Vitao → DAIANE
JULIO: Julio, Julio Gadret → JULIO
```

---

# PARTE 10 — REGRAS DE NEGÓCIO INVIOLÁVEIS

1. CNPJ = 14 dígitos, chave primária universal
2. Two-Base Architecture: R$ APENAS em VENDA
3. CARTEIRA 46 colunas IMUTÁVEL
4. Zero fabricação de dados
5. Cores por status: ATIVO=#00B050, INAT.REC=#FFC000, INAT.ANT=#FF0000
6-17. Ver briefing completo.

---

# PARTE 12 — ENTREGAS PRIORIZADAS

1. PROJEÇÃO reconstruída (18.180 fórmulas) — CRÍTICO
2. Dados de faturamento corretos (R$ 2.156.179)
3. Timeline mensal populada
4. LOG completo (~11.758 registros)
5. DASH redesenhada (3 blocos)
6. E-commerce cruzado
7. REDE/REGIONAL preenchido
8. #REF! corrigidos
9. COMITÊ com metas
10. Validação final (0 erros)

---

# PARTE 13 — LIÇÕES APRENDIDAS

1. Openpyxl destrói slicers → XML Surgery
2. Relatórios Mercos mentem nos nomes
3. Fórmulas openpyxl em INGLÊS
4. CNPJ como float perde precisão → string zfill(14)
5-14. Ver briefing completo.

---

**FIM DO BRIEFING**
**16 meses. 32 sessões. 88+ arquivos. Transferência completa.**
