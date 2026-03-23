# DECISIONS.md — Knowledge Base Forense do CRM VITAO360
# 15 decisoes tecnicas acumuladas | Atualizado: 2026-03-23

---

### D-01: Two-Base Architecture
**Data:** 2024-12 | **Status:** ACTIVE | **Impacto:** CRITICO
**Decisao:** Separar ABSOLUTAMENTE dados financeiros (VENDA=R$) de interacoes (LOG=R$0.00)
**Contexto:** ChatGPT duplicava valor da venda em cada interacao. R$664K virou R$3.62M (742%)
**Alternativas:** Nenhuma — qualquer mistura causa inflacao catastrofica
**Consequencias:** Toda formula, script e cruzamento DEVE respeitar a separacao

### D-02: CNPJ como Chave Primaria
**Data:** 2024-12 | **Status:** ACTIVE | **Impacto:** CRITICO
**Decisao:** CNPJ normalizado (14 digitos, string, zero-padded) como chave universal
**Contexto:** CNPJ como float perdia zeros a esquerda. Cruzamentos falhavam silenciosamente
**Alternativas:** ID interno, Razao Social — ambos ambiguos entre sistemas
**Consequencias:** `re.sub(r'\D', '', str(val)).zfill(14)` em TODO cruzamento

### D-03: Faturamento Baseline Corrigido
**Data:** 2026-03-23 | **Status:** ACTIVE (supersede anterior) | **Impacto:** ALTO
**Decisao:** Baseline 2025 = R$ 2.091.000 (PAINEL CEO DEFINITIVO, auditoria 68 arquivos)
**Contexto:** Valor anterior R$ 2.156.179 (PAINEL ATIVIDADES) divergia em R$65K
**Alternativas:** R$2.101M, R$1.997M — descartados na aba CONFLITOS RESOLVIDOS
**Consequencias:** Toda validacao de faturamento usa R$ 2.091.000. Tolerancia 0.5%

### D-04: openpyxl Destroi Slicers
**Data:** 2025-06 | **Status:** ACTIVE | **Impacto:** ALTO
**Decisao:** Slicers NUNCA via openpyxl — usar XML Surgery (zipfile + lxml)
**Contexto:** openpyxl remove infraestrutura XML dos slicers ao salvar
**Alternativas:** Nenhuma funcional — openpyxl nao suporta slicers
**Consequencias:** Qualquer operacao com slicers = manipulacao XML direta

### D-05: Mercos Report Names MENTEM
**Data:** 2025-02 | **Status:** ACTIVE | **Impacto:** ALTO
**Decisao:** SEMPRE verificar Data Inicial/Final nas linhas 6-7 dos relatorios Mercos
**Contexto:** "Abril" continha Abr+Mai. "Set25" era Out. "Nov" era Set
**Alternativas:** Confiar no nome do arquivo — ERRADO, causa dados duplicados
**Consequencias:** ETL de Mercos DEVE ler metadados internos, nao nome do arquivo

### D-06: 558 Registros ALUCINACAO
**Data:** 2025-02 | **Status:** ACTIVE | **Impacto:** CRITICO
**Decisao:** 558 registros do CONTROLE_FUNIL classificados como ALUCINACAO — NUNCA integrar
**Contexto:** ChatGPT fabricou dados em 100+ iteracoes. CNPJs invalidos, nomes ficticios
**Alternativas:** Tentar limpar — REJEITADO (impossivel separar real de fabricado)
**Consequencias:** Classificacao 3-tier OBRIGATORIA: REAL / SINTETICO / ALUCINACAO

### D-07: Formulas em INGLES no openpyxl
**Data:** 2025-01 | **Status:** ACTIVE | **Impacto:** ALTO
**Decisao:** Formulas openpyxl SEMPRE em ingles (IF, VLOOKUP, SUMIF). Separador virgula
**Contexto:** Formulas em portugues (SE, PROCV, SOMASE) QUEBRAM no openpyxl
**Alternativas:** Nenhuma — openpyxl so aceita ingles
**Consequencias:** Toda formula gerada por script usa nomenclatura inglesa

### D-08: 46 Colunas CARTEIRA Imutaveis
**Data:** 2025-01 | **Status:** ACTIVE | **Impacto:** ALTO
**Decisao:** As 46 colunas originais (A-AT) da CARTEIRA NAO MUDAM
**Contexto:** Expansao via Blueprint v2 adiciona colunas via grupos [+], nao substitui
**Alternativas:** Refazer CARTEIRA — REJEITADO (quebraria tudo)
**Consequencias:** L3 obrigatorio para qualquer alteracao nas 46 originais

### D-09: CARTEIRA Real tem 144 Colunas
**Data:** 2026-03-23 | **Status:** ACTIVE | **Impacto:** INFORMATIVO
**Decisao:** A CARTEIRA expandida tem 144 colunas (A-EN), 180.513 formulas, 9 super-grupos
**Contexto:** Radiografia automatizada revelou expansao muito alem do Blueprint v2 (81)
**Alternativas:** N/A — dado de radiografia
**Consequencias:** SaaS precisa modelar 144 colunas, nao 46 nem 81

### D-10: Motor de Regras = 92 Combinacoes
**Data:** 2026-03-23 | **Status:** ACTIVE | **Impacto:** CRITICO
**Decisao:** Motor v4 tem 92 combinacoes (7 SITUACAO x ~14 RESULTADO) gerando 9 dimensoes
**Contexto:** Documentacao anterior dizia 63 combinacoes — eram menos estados
**Alternativas:** N/A — dado auditado da planilha FINAL
**Consequencias:** Todo SaaS/motor Python deve implementar TODAS as 92

### D-11: Score Ranking = 6 Fatores Ponderados
**Data:** 2026-03-23 | **Status:** ACTIVE | **Impacto:** ALTO
**Decisao:** URGENCIA 30% + VALOR 25% + FOLLOWUP 20% + SINAL 15% + TENTATIVA 5% + SITUACAO 5%
**Contexto:** Extraido das formulas EG-EM da CARTEIRA
**Alternativas:** Pesos diferentes — pode ajustar com dados reais futuramente
**Consequencias:** Score 0-100 gera Piramide P1-P7 que prioriza agenda

### D-12: Deskrio API Conectada
**Data:** 2026-03-23 | **Status:** ACTIVE | **Impacto:** ALTO
**Decisao:** API Deskrio validada: 15.468 contatos, 26 endpoints, CNPJ como campo extra
**Contexto:** Token admin JWT, companyId 38, 3 conexoes WhatsApp (2 ativas)
**Alternativas:** WhatsApp Business API direta — mais complexo, menos dados existentes
**Consequencias:** Integracao WhatsApp via Deskrio e plug-and-play na Fase 3

### D-13: Estrategia SaaS em 3 Fases
**Data:** 2026-03-23 | **Status:** ACTIVE | **Impacto:** ESTRATEGICO
**Decisao:** F1: Motor Python local → F2: Scripts Siga-me SAP/Mercos → F3: APIs Deskrio/Asana
**Contexto:** Leandro quer valor imediato. API/integracoes sao Fase 2-3
**Alternativas:** Big Bang (rejeitado), Strangler Fig (lento demais)
**Consequencias:** Motor funciona com dados atuais ANTES de qualquer integracao

### D-14: Churn 80% = Maior Risco Estrutural
**Data:** 2026-03-23 | **Status:** ACTIVE | **Impacto:** CRITICO
**Decisao:** Churn real de 80% (8 de 10 nao recompram). 57% compraram 1x so
**Contexto:** ULTRA_FINAL + DOC MESTRE confirmam. Q1 2026 real: 83%
**Alternativas:** Meta com Pos-Venda Q3: reduzir para 50%
**Consequencias:** Pos-Venda e a contratacao MAIS CRITICA. LTV sobe de R$2.850 para R$7.200

### D-15: Q1 2026 Validou Modelo
**Data:** 2026-03-23 | **Status:** ACTIVE | **Impacto:** ALTO
**Decisao:** 4 de 5 premissas confirmadas pelo real Q1 (R$459K, 178 clientes)
**Contexto:** Ticket R$1.569 (+4.6%), 59 novos/mes SEM equipe (+168%), churn 83%
**Alternativas:** N/A — dados reais SAP
**Consequencias:** Modelo CONSERVADOR funciona. Projecao 2026 R$3.377M tem base solida
