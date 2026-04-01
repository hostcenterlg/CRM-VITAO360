# Estrutura: Abas LICITAÇÕES + FOODSERVICE — CRM VITAO360

> Documento de planejamento. Aprovação Leandro necessária antes de implementar.
> Data: 2026-03-31

---

## 1. ABA LICITAÇÕES — Mapeamento Nacional Diário

### Visão
Monitorar TODAS as licitações públicas do Brasil (prefeituras, estados, federal) onde a Vitão pode participar com seus produtos. Fluxo diário automatizado que varre o país inteiro: pregões, editais, dispensas de licitação, chamadas públicas PNAE.

### Fonte de Dados Principal
**PNCP — Portal Nacional de Contratações Públicas**
- API pública com Swagger: https://pncp.gov.br/api/consulta/swagger-ui/index.html
- Endpoints de consulta SEM autenticação (acesso livre)
- Formato JSON, UTF-8
- Filtrável por: descrição de item, CNAE, UF, município, data, modalidade
- Documentação: https://www.gov.br/pncp/pt-br/acesso-a-informacao/dados-abertos

**Fontes complementares:**
- ComprasNet (federal): comprasnet.gov.br
- Portais estaduais (BEC-SP, Banrisul-RS, etc.)
- Diários Oficiais (via busca textual)
- Plataformas privadas: Alerta Licitação, Licitanet, BLL

### Fluxo Diário Proposto

```
06:00  → Robô varre PNCP (API) por palavras-chave dos produtos Vitão
07:00  → Classifica relevância (ML simples ou regras)
07:30  → Notificação no CRM: "X novas licitações encontradas"
08:00  → Equipe comercial/licitações analisa e decide participar ou não
       → Muda status: ANALISAR → PARTICIPAR → EM ANDAMENTO → GANHO/PERDIDO
```

### Palavras-Chave para Monitoramento (Produtos Vitão)
```
CATEGORIA 1 — CEREAIS E GRÃOS:
  granola, aveia, flocos de aveia, farelo de aveia, cereal matinal,
  cereal integral, müsli, quinoa, chia, linhaça, gergelim

CATEGORIA 2 — BARRAS E SNACKS:
  barra de cereal, barra de proteína, cookies integral, biscoito integral,
  snack saudável, mix de nuts, castanha

CATEGORIA 3 — FARINHAS E INGREDIENTES:
  farinha integral, farinha de trigo integral, farinha de aveia,
  farinha de linhaça, gérmen de trigo, fibra de trigo

CATEGORIA 4 — ALIMENTAÇÃO ESCOLAR (PNAE):
  merenda escolar, alimentação escolar, gêneros alimentícios,
  alimentos naturais, alimentos integrais, programa alimentação

CATEGORIA 5 — INSTITUCIONAL:
  alimentos saudáveis, produtos naturais, produtos orgânicos,
  alimentação saudável, nutrição
```

### Estrutura da Aba (Campos)

| # | Campo | Tipo | Descrição |
|---|-------|------|-----------|
| 1 | ID_LICITACAO | text | ID único (PNCP ou sequencial) |
| 2 | DATA_PUBLICACAO | date | Data de publicação do edital |
| 3 | DATA_ABERTURA | date | Data de abertura dos envelopes/sessão |
| 4 | DATA_LIMITE | date | Prazo final para participar |
| 5 | MODALIDADE | dropdown | Pregão Eletrônico / Pregão Presencial / Concorrência / Dispensa / Chamada Pública |
| 6 | ORGAO | text | Órgão licitante (Prefeitura de X, Secretaria de Y) |
| 7 | UF | dropdown | Estado (2 letras) |
| 8 | MUNICIPIO | text | Cidade |
| 9 | OBJETO | text | Descrição do objeto da licitação |
| 10 | ITENS_RELEVANTES | text | Itens que batem com produtos Vitão |
| 11 | VALOR_ESTIMADO | currency | Valor estimado da licitação (R$) |
| 12 | RELEVANCIA | dropdown | ALTA / MÉDIA / BAIXA (classificação automática) |
| 13 | STATUS | dropdown | NOVA → ANALISANDO → PARTICIPAR → PROPOSTA ENVIADA → AGUARDANDO → GANHO → PERDIDO → DESCARTADA |
| 14 | RESPONSAVEL | dropdown | Quem está cuidando (MANU/LARISSA/DAIANE/JULIO/LEANDRO) |
| 15 | LINK_EDITAL | url | Link para o edital completo |
| 16 | LINK_PNCP | url | Link no Portal PNCP |
| 17 | PRODUTOS_VITAO | text | Quais produtos Vitão se encaixam |
| 18 | VALOR_PROPOSTA | currency | Valor da proposta Vitão (se participar) |
| 19 | RESULTADO | text | Resultado (ganhamos? perdemos? para quem?) |
| 20 | OBSERVACOES | text | Notas livres |
| 21 | CREATED_AT | timestamp | Data de inserção no CRM |
| 22 | UPDATED_AT | timestamp | Última atualização |

### KPIs do Dashboard Licitações

```
CARDS PRINCIPAIS:
  - Licitações Novas Hoje
  - Licitações em Análise
  - Propostas Enviadas (mês)
  - Taxa de Conversão (ganho/total participado)
  - Valor Total Ganho (mês/ano)
  - Valor em Disputa (propostas ativas)

GRÁFICOS:
  - Mapa do Brasil: licitações por UF (heat map)
  - Funil: NOVA → ANALISANDO → PARTICIPAR → GANHO
  - Timeline: licitações com prazos próximos
  - Top 10 Órgãos por valor
  - Distribuição por categoria de produto
```

### Automação Técnica

```
OPÇÃO A — n8n + PNCP API (RECOMENDADA):
  - Workflow n8n roda 2x/dia (06:00 e 14:00)
  - Chama PNCP API com palavras-chave
  - Filtra por relevância (regex + scoring)
  - Insere no banco (Neon PostgreSQL)
  - Notifica via WhatsApp/Slack

OPÇÃO B — Python Script + Cron:
  - Script Python chama PNCP API
  - Classificação via embeddings (similaridade com catálogo Vitão)
  - Insere no banco
  - Cron executa 2x/dia

OPÇÃO C — Serviço externo (Alerta Licitação):
  - Contrata plataforma que já faz o monitoramento
  - API de integração para puxar para o CRM
  - Custo: ~R$ 200-500/mês
```

---

## 2. ABA FOODSERVICE — Grandes Contas / Private Label

### Visão
Gerenciar relacionamento com grandes contas do segmento foodservice: redes de restaurantes, hospitais, cozinhas industriais, catering, hotéis que compram matéria-prima, terceirização de produção, industrialização e private label da Vitão.

### Diferença do B2B Tradicional
```
B2B DISTRIBUIÇÃO (já existe):
  → Vende PRODUTO ACABADO (caixa de granola, pacote de aveia)
  → Milhares de clientes, ticket médio baixo
  → Volume alto, margem padrão

FOODSERVICE (NOVO):
  → Vende MATÉRIA-PRIMA (aveia a granel, granola em bag 10kg)
  → Terceirização (faz o produto com marca do cliente)
  → Industrialização (processa ingrediente para outro fabricante)
  → Private Label (embala com marca do cliente)
  → Dezenas de clientes, ticket ALTÍSSIMO
  → Volume enorme, margem negociada caso a caso
```

### Estrutura da Aba (Campos)

| # | Campo | Tipo | Descrição |
|---|-------|------|-----------|
| 1 | ID_CONTA | text | ID único |
| 2 | RAZAO_SOCIAL | text | Razão social |
| 3 | NOME_FANTASIA | text | Nome fantasia |
| 4 | CNPJ | text(14) | CNPJ normalizado |
| 5 | SEGMENTO | dropdown | Restaurante / Hospital / Hotel / Catering / Indústria / Rede de Fast Food / Cozinha Industrial / Padaria Industrial |
| 6 | PORTE | dropdown | GRANDE / MÉDIO |
| 7 | UF | dropdown | Estado |
| 8 | CIDADE | text | Cidade |
| 9 | TIPO_NEGOCIO | dropdown | MATÉRIA-PRIMA / TERCEIRIZAÇÃO / INDUSTRIALIZAÇÃO / PRIVATE LABEL / MISTO |
| 10 | PRODUTOS_INTERESSE | text | Quais produtos/ingredientes |
| 11 | VOLUME_MENSAL_KG | number | Volume mensal estimado em kg |
| 12 | VALOR_MENSAL | currency | Faturamento mensal estimado (R$) |
| 13 | CONTATO_NOME | text | Nome do decisor |
| 14 | CONTATO_CARGO | text | Cargo |
| 15 | CONTATO_TELEFONE | text | Telefone |
| 16 | CONTATO_EMAIL | text | Email |
| 17 | STATUS_PIPELINE | dropdown | PROSPECT → CONTATO INICIAL → AMOSTRA ENVIADA → NEGOCIAÇÃO → CONTRATO → ATIVO → PERDIDO → INATIVO |
| 18 | RESPONSAVEL | dropdown | DAIANE / LEANDRO / MANU / LARISSA |
| 19 | DATA_PRIMEIRO_CONTATO | date | Quando começou a relação |
| 20 | DATA_ULTIMA_INTERACAO | date | Último contato |
| 21 | TEMPERATURA | dropdown | QUENTE / MORNO / FRIO |
| 22 | VALOR_CONTRATO_ANUAL | currency | Valor anual do contrato (R$) |
| 23 | MARGEM_ESTIMADA | percent | % margem negociada |
| 24 | CONCORRENTE_ATUAL | text | Quem fornece hoje |
| 25 | DIFERENCIAL_VITAO | text | Por que escolher Vitão |
| 26 | NECESSIDADES_ESPECIAIS | text | Certificações, laudos, ficha técnica |
| 27 | OBSERVACOES | text | Notas livres |
| 28 | CREATED_AT | timestamp | Data de inserção |
| 29 | UPDATED_AT | timestamp | Última atualização |

### KPIs do Dashboard Foodservice

```
CARDS PRINCIPAIS:
  - Contas Ativas
  - Pipeline Total (R$ em negociação)
  - Faturamento Mensal Foodservice
  - Volume Mensal (toneladas)
  - Margem Média (%)
  - Contas Novas (mês)

GRÁFICOS:
  - Funil: PROSPECT → CONTATO → AMOSTRA → NEGOCIAÇÃO → CONTRATO → ATIVO
  - Mix por tipo: Matéria-Prima vs Terceirização vs Private Label
  - Top 10 contas por faturamento
  - Mapa: distribuição geográfica
  - Timeline: contratos com vencimento próximo
```

### Processo Comercial Foodservice

```
FASE 1 — PROSPECÇÃO:
  ↳ Identificar grandes contas potenciais
  ↳ Pesquisar: quem são, o que compram, de quem compram
  ↳ Classificar: QUENTE / MORNO / FRIO

FASE 2 — ABORDAGEM:
  ↳ Contato inicial (ligação/email/visita)
  ↳ Apresentação institucional Vitão
  ↳ Levantamento de necessidades

FASE 3 — AMOSTRA:
  ↳ Enviar amostras dos produtos/ingredientes
  ↳ Ficha técnica + laudos de qualidade
  ↳ Acompanhar teste na produção do cliente

FASE 4 — NEGOCIAÇÃO:
  ↳ Proposta comercial (preço, volume, prazo)
  ↳ Negociar margem e condições
  ↳ Alinhar logística (frete, embalagem, frequência)

FASE 5 — CONTRATO:
  ↳ Formalizar contrato/pedido de compra
  ↳ Definir programação de entregas
  ↳ Ativar no sistema (Mercos/SAP)

FASE 6 — GESTÃO:
  ↳ Acompanhamento mensal
  ↳ Revisão de preços (trimestral)
  ↳ Upsell: novos produtos, novos SKUs
  ↳ Renovação de contrato
```

---

## 3. IMPLEMENTAÇÃO NO CRM SaaS

### Onde encaixar no frontend
```
SIDEBAR ATUAL:
  Dashboard
  Clientes
  Vendas
  Metas
  Conversas
  ---
  NOVO → Licitações    ← ícone: FileText ou Gavel
  NOVO → Foodservice   ← ícone: ChefHat ou Building2
```

### Tabelas no Banco (Neon PostgreSQL)

```sql
-- Licitações
CREATE TABLE licitacoes (
  id SERIAL PRIMARY KEY,
  id_licitacao TEXT UNIQUE,
  data_publicacao DATE,
  data_abertura DATE,
  data_limite DATE,
  modalidade TEXT,
  orgao TEXT,
  uf CHAR(2),
  municipio TEXT,
  objeto TEXT,
  itens_relevantes TEXT,
  valor_estimado DECIMAL(15,2),
  relevancia TEXT DEFAULT 'MEDIA',
  status TEXT DEFAULT 'NOVA',
  responsavel TEXT,
  link_edital TEXT,
  link_pncp TEXT,
  produtos_vitao TEXT,
  valor_proposta DECIMAL(15,2),
  resultado TEXT,
  observacoes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Foodservice
CREATE TABLE foodservice (
  id SERIAL PRIMARY KEY,
  razao_social TEXT,
  nome_fantasia TEXT,
  cnpj CHAR(14) UNIQUE,
  segmento TEXT,
  porte TEXT,
  uf CHAR(2),
  cidade TEXT,
  tipo_negocio TEXT,
  produtos_interesse TEXT,
  volume_mensal_kg DECIMAL(12,2),
  valor_mensal DECIMAL(15,2),
  contato_nome TEXT,
  contato_cargo TEXT,
  contato_telefone TEXT,
  contato_email TEXT,
  status_pipeline TEXT DEFAULT 'PROSPECT',
  responsavel TEXT,
  data_primeiro_contato DATE,
  data_ultima_interacao DATE,
  temperatura TEXT DEFAULT 'FRIO',
  valor_contrato_anual DECIMAL(15,2),
  margem_estimada DECIMAL(5,2),
  concorrente_atual TEXT,
  diferencial_vitao TEXT,
  necessidades_especiais TEXT,
  observacoes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Prioridade de Implementação

```
FASE IMEDIATA (esta semana):
  1. Criar tabelas no Neon
  2. Criar páginas básicas no frontend (listagem + formulário)
  3. Endpoints CRUD no backend

FASE AUTOMAÇÃO (próxima semana):
  4. Script PNCP que busca licitações diariamente
  5. Classificador de relevância por palavras-chave
  6. Notificação WhatsApp de novas licitações

FASE INTELIGÊNCIA (futuro):
  7. ML para scoring de relevância (quais licitações temos chance)
  8. Análise de preços de mercado (histórico de licitações anteriores)
  9. Alerta de vencimento de contratos foodservice
```

---

## 4. DECISÕES PENDENTES (Leandro)

- [ ] Quem será responsável pela área de licitações? (novo cargo ou equipe atual?)
- [ ] Vitão já participou de licitações antes? Tem histórico?
- [ ] Quais certificações a Vitão tem (orgânico, glúten-free, etc.)?
- [ ] Foodservice: já tem alguma conta ativa nesse modelo?
- [ ] Budget para ferramentas de monitoramento de licitações?
- [ ] Prioridade: começar por licitações ou foodservice?
