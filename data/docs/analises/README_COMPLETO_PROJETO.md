# 📊 VITÃO ALIMENTOS - ANÁLISE CRM & DATA ANALYTICS
## Sistema de Análise e Gestão de Relacionamento com Clientes

[![Status](https://img.shields.io/badge/Status-Em%20Desenvolvimento-yellow)]()
[![Versão](https://img.shields.io/badge/Versão-2.0-blue)]()
[![Python](https://img.shields.io/badge/Python-3.12-green)]()
[![License](https://img.shields.io/badge/License-MIT-red)]()

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Arquitetura de Dados](#arquitetura-de-dados)
3. [Instalação e Setup](#instalação-e-setup)
4. [Estrutura do Projeto](#estrutura-do-projeto)
5. [Análises Disponíveis](#análises-disponíveis)
6. [APIs e Integrações](#apis-e-integrações)
7. [Dashboards](#dashboards)
8. [Contribuindo](#contribuindo)
9. [FAQ](#faq)
10. [Contato](#contato)

---

## 🎯 Visão Geral

Sistema completo de análise de CRM para Vitão Alimentos, desenvolvido após perda de dados do CRM anterior (ExactSales). Processa e analisa:

- **867 vendas** em 2025
- **444 clientes únicos**
- **R$ 3.603.246,14** em receita
- **10 meses** de dados (FEV-DEZ/2025)

### Principais Funcionalidades

✅ **Análise de Carteira Completa** - Tracking de todos os clientes mês a mês  
✅ **Segmentação RFM** - Classificação automática por Recency, Frequency, Monetary  
✅ **Cálculo de LTV** - Lifetime Value por cliente e segmento  
✅ **Análise de Churn** - Taxa de perda mensal de clientes  
✅ **Taxa de Recompra** - Monitoramento de retenção  
✅ **Performance por Consultor** - Métricas individuais de vendas  
✅ **Alertas Automáticos** - Clientes em risco de inativação  
✅ **Previsões** - Projeções de carteira e receita

---

## 🏗️ Arquitetura de Dados

### Fluxo de Dados

```
┌─────────────────┐
│  FONTE DE DADOS │
└────────┬────────┘
         │
         ├──> Relatorio_Vendas_2025.txt (867 vendas)
         ├──> Positivacao_de_Clientes_XX.txt (10 arquivos)
         └──> Carteira_detalhada_de_clientes_70.xls
         │
         ▼
┌─────────────────┐
│  PROCESSAMENTO  │
└────────┬────────┘
         │
         ├──> Python/Pandas (ETL)
         ├──> Cálculo de status (Ativo/Inativo)
         ├──> Segmentação RFM
         └──> Agregações e métricas
         │
         ▼
┌─────────────────┐
│  DADOS FINAIS   │
└────────┬────────┘
         │
         ├──> analise_rfm.csv
         ├──> lifetime_value.csv
         ├──> carteira_completa_mensal.csv
         ├──> top_50_clientes.csv
         ├──> performance_por_consultor.csv
         └──> performance_por_rede.csv
         │
         ▼
┌─────────────────┐
│   VISUALIZAÇÃO  │
└─────────────────┘
         │
         ├──> Dashboard (PowerBI/Tableau)
         ├──> Relatórios MD
         └──> Alertas automáticos
```

### Schema de Dados

#### Tabela: `vendas`
```sql
Data_Emissao       DATETIME
Pedido             INTEGER
Tag_Cliente        VARCHAR
Nome_Fantasia      VARCHAR
Razao_Social       VARCHAR (PK)
Colaborador        VARCHAR
Rede               VARCHAR
Valor_Vendido      DECIMAL(10,2)
Mes                PERIOD
Trimestre          PERIOD
Dia_Semana         VARCHAR
```

#### Tabela: `carteira_mensal`
```sql
Mes                VARCHAR (PK)
Data_Ref           DATE
Carteira_Total     INTEGER
Ativos_Total       INTEGER
Inativos_Rec_Total INTEGER
Inativos_Ant_Total INTEGER
Positivaram_Mes    INTEGER
Nao_Positivaram    INTEGER
```

#### Tabela: `rfm_segmentacao`
```sql
Razao_Social       VARCHAR (PK)
Recency            INTEGER  # dias desde última compra
Frequency          INTEGER  # número de compras
Monetary           DECIMAL(10,2)  # valor total
Segmento           VARCHAR  # CAMPEÕES, FIÉIS, etc.
```

---

## 🚀 Instalação e Setup

### Requisitos

- Python 3.12+
- Pandas 2.0+
- NumPy
- OpenPyXL (para Excel)
- Jupyter Notebook (opcional, para análises interativas)

### Instalação

```bash
# Clone o repositório
git clone https://github.com/vitao-alimentos/crm-analytics.git
cd crm-analytics

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt
```

### Arquivo `requirements.txt`

```txt
pandas==2.2.0
numpy==1.26.0
openpyxl==3.1.2
matplotlib==3.8.0
seaborn==0.13.0
jupyter==1.0.0
plotly==5.18.0
xlrd==2.0.1
```

### Configuração Inicial

```bash
# Crie estrutura de diretórios
mkdir -p data/raw data/processed data/outputs
mkdir -p notebooks scripts dashboards

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações
```

### Arquivo `.env.example`

```bash
# Diretórios
RAW_DATA_DIR=data/raw
PROCESSED_DATA_DIR=data/processed
OUTPUTS_DIR=data/outputs

# Configurações de análise
DATA_REFERENCIA=2025-12-15
ALERTA_DIAS_INATIVO=45
CHURN_DIAS=180

# Segmentação RFM
RFM_RECENCY_ALTO=30
RFM_RECENCY_MEDIO=60
RFM_RECENCY_BAIXO=180
RFM_FREQUENCY_ALTO=3
RFM_MONETARY_ALTO=5000
RFM_MONETARY_MEDIO=2000
```

---

## 📁 Estrutura do Projeto

```
crm-analytics/
│
├── data/
│   ├── raw/                          # Dados originais
│   │   ├── Relatorio_Vendas_2025.txt
│   │   ├── Positivacao_de_Clientes_41.txt
│   │   └── ... (demais arquivos)
│   │
│   ├── processed/                    # Dados processados
│   │   ├── analise_rfm.csv
│   │   ├── lifetime_value.csv
│   │   ├── carteira_completa_mensal.csv
│   │   └── ...
│   │
│   └── outputs/                      # Relatórios e análises
│       ├── PRD_COMPLETO_CRM_VITAO.md
│       ├── ANALISE_DEFINITIVA_100_COMPLETA.md
│       └── ...
│
├── scripts/                          # Scripts Python
│   ├── etl/
│   │   ├── extract_vendas.py
│   │   ├── extract_positivacao.py
│   │   └── transform_carteira.py
│   │
│   ├── analysis/
│   │   ├── rfm_segmentation.py
│   │   ├── ltv_calculation.py
│   │   ├── churn_analysis.py
│   │   └── cohort_analysis.py
│   │
│   └── automation/
│       ├── alertas_automaticos.py
│       ├── relatorios_mensais.py
│       └── backup_dados.py
│
├── notebooks/                        # Jupyter Notebooks
│   ├── 01_exploratory_analysis.ipynb
│   ├── 02_rfm_segmentation.ipynb
│   ├── 03_churn_prediction.ipynb
│   └── 04_dashboard_development.ipynb
│
├── dashboards/                       # Dashboards e visualizações
│   ├── powerbi/
│   │   └── CRM_Dashboard.pbix
│   ├── streamlit/
│   │   └── app.py
│   └── templates/
│       └── relatorio_mensal.html
│
├── docs/                             # Documentação
│   ├── PRD_COMPLETO_CRM_VITAO.md
│   ├── ANALISE_DEFINITIVA_100_COMPLETA.md
│   ├── API_DOCUMENTATION.md
│   └── USER_GUIDE.md
│
├── tests/                            # Testes unitários
│   ├── test_etl.py
│   ├── test_rfm.py
│   └── test_ltv.py
│
├── .env.example                      # Exemplo de variáveis de ambiente
├── .gitignore
├── requirements.txt
├── setup.py
└── README.md
```

---

## 📊 Análises Disponíveis

### 1. Análise de Carteira Completa

**Script:** `scripts/analysis/carteira_completa.py`

```python
from scripts.analysis import calcular_carteira_mensal

# Processar dados
carteira = calcular_carteira_mensal(
    arquivo_vendas='data/raw/Relatorio_Vendas_2025.txt',
    data_referencia='2025-12-15'
)

# Output: carteira_completa_mensal.csv
print(carteira.head())
```

**Métricas calculadas:**
- Carteira total mês a mês
- Status de cada cliente (Ativo/Inativo Rec/Inativo Ant)
- Taxa de positivação mensal
- Crescimento da carteira

### 2. Segmentação RFM

**Script:** `scripts/analysis/rfm_segmentation.py`

```python
from scripts.analysis import segmentar_rfm

# Calcular RFM
rfm = segmentar_rfm(
    vendas_df,
    data_referencia='2025-12-15',
    config={
        'recency_alto': 30,
        'recency_medio': 60,
        'frequency_alto': 3,
        'monetary_alto': 5000
    }
)

# Output: analise_rfm.csv
# Segmentos: CAMPEÕES, FIÉIS, POTENCIAL, etc.
```

**Segmentos identificados:**
- CAMPEÕES (6.8%) - Melhores clientes
- CLIENTES FIÉIS (11.7%) - Base sólida
- POTENCIAL FIDELIZAÇÃO (9.9%) - Oportunidade
- NOVOS PROMISSORES (23.0%) - Crescimento
- PRECISA ATENÇÃO (14.6%) - Risco médio
- CLIENTES EM RISCO (7.7%) - Risco alto
- PRESTES A PERDER (2.7%) - Crítico
- HIBERNANDO (23.6%) - Dormentes

### 3. Cálculo de LTV

**Script:** `scripts/analysis/ltv_calculation.py`

```python
from scripts.analysis import calcular_ltv

# Calcular LTV
ltv = calcular_ltv(vendas_df)

# Categorias automáticas
# VIP: R$10k+, GOLD: R$5k-10k, SILVER: R$2k-5k, BRONZE: <R$2k

print(ltv[['Categoria_LTV', 'Valor_Total', 'Qtd_Compras', 'Ticket_Medio']])
```

**Insights:**
- 41 clientes VIP (9.2%) geram 44.8% da receita
- LTV médio: R$ 8.115
- Ticket médio: R$ 4.156

### 4. Análise de Churn

**Script:** `scripts/analysis/churn_analysis.py`

```python
from scripts.analysis import analisar_churn

# Calcular churn mensal
churn = analisar_churn(carteira_df)

print(f"Churn médio: {churn['taxa_media']:.1f}%")
print(f"Clientes perdidos/mês: {churn['clientes_mes']:.0f}")
```

**Resultados:**
- Churn médio: 18% dos ativos/mês
- ~30 clientes perdidos/mês
- Pico em AGO/2025: 46 clientes

### 5. Taxa de Recompra

**Script:** `scripts/analysis/recompra_analysis.py`

```python
from scripts.analysis import calcular_taxa_recompra

# Taxa de recompra mês a mês
recompra = calcular_taxa_recompra(vendas_df)

# Taxa média: 21.9%
# Melhor mês: AGO/2025 (27.9%)
```

### 6. Performance por Consultor

**Script:** `scripts/analysis/performance_consultor.py`

```python
from scripts.analysis import analisar_consultores

# Performance individual
perf = analisar_consultores(vendas_df)

# Ranking automático
# KPIs: valor total, vendas, clientes, ticket médio
```

### 7. Alertas Automáticos

**Script:** `scripts/automation/alertas_automaticos.py`

```python
from scripts.automation import gerar_alertas

# Gerar alertas diários
alertas = gerar_alertas(
    carteira_df,
    vendas_df,
    alertas_config={
        'dias_inativo_alerta': 45,
        'dias_inativo_critico': 60,
        'dias_churn': 90
    }
)

# Envia por email/WhatsApp
alertas.enviar(destinatarios=['consultor@vitao.com.br'])
```

**Tipos de alertas:**
- 🟡 Cliente há 45 dias sem comprar
- 🟠 Cliente em risco (60 dias)
- 🔴 Cliente prestes a churnar (90 dias)
- 🟢 Oportunidade de up-sell (cliente ativo com baixo ticket)

---

## 🔌 APIs e Integrações

### API REST do CRM

**Endpoint base:** `https://api.vitao-crm.com.br/v1`

#### Autenticação

```bash
# Login
curl -X POST https://api.vitao-crm.com.br/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'

# Response
{
  "token": "eyJhbGc...",
  "expires_in": 3600
}
```

#### Endpoints Principais

```bash
# GET /clientes - Lista todos os clientes
GET /clientes?status=ativo&segmento=CAMPEOES

# GET /clientes/{id} - Detalhe de um cliente
GET /clientes/12345

# GET /clientes/{id}/historico - Histórico de compras
GET /clientes/12345/historico?data_inicio=2025-01-01

# POST /alertas - Criar alerta manual
POST /alertas
{
  "cliente_id": 12345,
  "tipo": "REATIVACAO",
  "prioridade": "ALTA",
  "mensagem": "Cliente há 60 dias sem comprar"
}

# GET /metricas - Métricas em tempo real
GET /metricas?periodo=mes_atual

# GET /relatorios - Gerar relatório
GET /relatorios/rfm?formato=json
```

### Webhooks

```python
# Webhook de nova venda
@app.route('/webhooks/nova_venda', methods=['POST'])
def webhook_nova_venda():
    data = request.json
    
    # Processar venda
    processar_venda(data)
    
    # Atualizar status do cliente
    atualizar_status_cliente(data['cliente_id'])
    
    # Verificar alertas
    verificar_alertas(data['cliente_id'])
    
    return {'status': 'ok'}
```

### Integração com ERP Mercos

```python
from integrations import MercosAPI

# Conectar
mercos = MercosAPI(api_key=os.getenv('MERCOS_API_KEY'))

# Sincronizar vendas
vendas_novas = mercos.get_vendas(data_inicio='2025-12-01')

# Atualizar CRM
crm.sync_vendas(vendas_novas)
```

### Integração com WhatsApp Business API

```python
from integrations import WhatsAppAPI

# Enviar alerta
whatsapp = WhatsAppAPI(token=os.getenv('WHATSAPP_TOKEN'))

whatsapp.send_message(
    to='+5541999999999',
    template='alerta_cliente_inativo',
    params=['João Silva', '60 dias']
)
```

---

## 📈 Dashboards

### Dashboard Principal (PowerBI)

**Arquivo:** `dashboards/powerbi/CRM_Dashboard.pbix`

**KPIs Principais:**
- Taxa de Positivação Mensal
- Churn Rate
- LTV por Segmento
- Performance por Consultor
- Pipeline de Vendas

**Páginas:**
1. **Overview** - Visão geral do negócio
2. **Clientes** - Análise detalhada da carteira
3. **Vendas** - Performance de vendas
4. **Churn** - Análise de perda de clientes
5. **RFM** - Segmentação e oportunidades
6. **Consultores** - Performance individual

### Dashboard Web (Streamlit)

**Arquivo:** `dashboards/streamlit/app.py`

```bash
# Rodar dashboard local
streamlit run dashboards/streamlit/app.py
```

**Funcionalidades:**
- Filtros interativos
- Exportação de relatórios
- Alertas em tempo real
- Busca de clientes
- Drill-down em métricas

**URL:** `http://localhost:8501`

### Exemplo de Dashboard Streamlit

```python
import streamlit as st
import pandas as pd
import plotly.express as px

# Carregar dados
@st.cache_data
def load_data():
    carteira = pd.read_csv('data/processed/carteira_completa_mensal.csv')
    rfm = pd.read_csv('data/processed/analise_rfm.csv')
    return carteira, rfm

carteira, rfm = load_data()

# Título
st.title('🎯 CRM Dashboard - Vitão Alimentos')

# Métricas principais
col1, col2, col3, col4 = st.columns(4)
col1.metric("Carteira Total", f"{carteira['Carteira_Total'].iloc[-1]}")
col2.metric("Taxa Positivação", f"{carteira['Positivaram_Mes'].iloc[-1] / carteira['Carteira_Total'].iloc[-1] * 100:.1f}%")
col3.metric("Ativos", f"{carteira['Ativos_Total'].iloc[-1]}")
col4.metric("Churn Mês", "30 clientes")

# Gráfico de evolução
fig = px.line(carteira, x='Mes', y='Carteira_Total', title='Evolução da Carteira')
st.plotly_chart(fig)

# Segmentação RFM
st.subheader('Segmentação RFM')
seg_counts = rfm['Segmento'].value_counts()
fig2 = px.pie(values=seg_counts.values, names=seg_counts.index)
st.plotly_chart(fig2)
```

---

## 🤝 Contribuindo

### Como Contribuir

1. **Fork** o repositório
2. Crie uma **branch** para sua feature (`git checkout -b feature/NovaAnalise`)
3. **Commit** suas mudanças (`git commit -m 'Add: Nova análise de cohort'`)
4. **Push** para a branch (`git push origin feature/NovaAnalise`)
5. Abra um **Pull Request**

### Padrões de Código

```python
# PEP 8 compliant
# Docstrings obrigatórias
# Type hints recomendadas

def calcular_ltv(vendas: pd.DataFrame, 
                 cliente_id: str) -> float:
    """
    Calcula o Lifetime Value de um cliente.
    
    Args:
        vendas: DataFrame com histórico de vendas
        cliente_id: ID do cliente
        
    Returns:
        Valor total do LTV
        
    Example:
        >>> ltv = calcular_ltv(df, 'CLI001')
        >>> print(f"LTV: R$ {ltv:,.2f}")
    """
    cliente_vendas = vendas[vendas['cliente_id'] == cliente_id]
    return cliente_vendas['valor'].sum()
```

### Testes

```bash
# Rodar todos os testes
pytest tests/

# Rodar com coverage
pytest --cov=scripts tests/

# Rodar teste específico
pytest tests/test_rfm.py
```

---

## ❓ FAQ

### P: Como atualizar os dados mensalmente?

R: Execute o script de ETL:
```bash
python scripts/etl/update_monthly.py --mes 2025-12
```

### P: Como adicionar um novo consultor?

R: Edite `data/config/consultores.json` e rode:
```bash
python scripts/admin/sync_consultores.py
```

### P: Como gerar relatório customizado?

R: Use o notebook template:
```bash
jupyter notebook notebooks/template_relatorio_custom.ipynb
```

### P: Onde estão os backups?

R: Backups automáticos em `data/backups/` (diário às 00:00)

### P: Como resetar os dados de teste?

R:
```bash
python scripts/admin/reset_test_data.py --confirm
```

---

## 📞 Contato

**Desenvolvedor:** Leandro  
**Email:** leandro@vitao.com.br  
**Slack:** @leandro  

**Equipe CRM:**
- Product Owner: [Nome]
- Tech Lead: Leandro
- Data Analyst: [Nome]
- Consultores: Manu, Larissa, Helder, Daiane, Julio

---

## 📄 Licença

Este projeto é propriedade da Vitão Alimentos e está sob licença MIT.

```
MIT License

Copyright (c) 2025 Vitão Alimentos

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 🎉 Agradecimentos

- Equipe de vendas pela coleta de dados
- Consultores pelo feedback contínuo
- Diretoria pelo apoio ao projeto

---

## 📚 Recursos Adicionais

- [PRD Completo](docs/PRD_COMPLETO_CRM_VITAO.md)
- [Análise Técnica](docs/ANALISE_DEFINITIVA_100_COMPLETA.md)
- [Guia do Usuário](docs/USER_GUIDE.md)
- [API Documentation](docs/API_DOCUMENTATION.md)

---

**Última atualização:** 15/12/2025  
**Versão:** 2.0  
**Build:** Estável
