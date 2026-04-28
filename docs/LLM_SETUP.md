# LLM Infra Provider-Agnostic — Setup CRM360

**Origem:** US County Radar (testado em produção, 60K+ chamadas)  
**Data:** 2026-04-28

---

## O que é

2 arquivos que dão LLM ao seu projeto sem depender de nenhum provider específico:

| Arquivo | Linguagem | Onde usar |
|---------|-----------|----------|
| `llm_client.py` | Python | Backend, scripts, batches, workers |
| `llm_provider.ts` | TypeScript | APIs Vercel, Next.js, Node.js |

Ambos implementam a mesma lógica: **cascata de fallback automática**.

---

## Cascata de Providers

```
DeepInfra (Qwen 72B) → Groq (Llama 70B) → Anthropic (Claude) → OpenAI (GPT-4o)
   $0.13/$0.40           $0.59/$0.79         $3/$15              $2.50/$10
   ← mais barato                                          mais caro →
```

Se DeepInfra cair, tenta Groq. Se Groq cair, tenta Anthropic. Etc.  
Basta ter **1 key** configurada pra funcionar.

---

## Setup Rápido

### 1. Env vars (adicionar no `.env` e no Vercel/Railway)

```bash
# Pelo menos UMA é obrigatória
DEEPINFRA_API_KEY=di_xxxxxxxxxxxx     # Recomendado — mais barato
GROQ_API_KEY=gsk_xxxxxxxxxxxx         # Opcional — mais rápido
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx # Opcional — melhor qualidade
OPENAI_API_KEY=sk-xxxxxxxxxxxx        # Opcional — fallback universal
```

### 2. Python (backend)

```bash
pip install httpx
```

```python
from llm_client import LLMClient, generate

# Simples (sem logging)
resp = generate("Resuma este lead em 3 linhas")
print(resp.text)        # texto gerado
print(resp.cost_usd)    # custo em USD
print(resp.provider)    # "deepinfra", "groq", etc.

# Com logging em PostgreSQL
import psycopg2
conn = psycopg2.connect("postgresql://...")
client = LLMClient(conn=conn)
resp = client.generate(
    "Classifique este ticket",
    system_prompt="Você é um classificador de tickets de suporte...",
    model_tier="cheap",      # "cheap" | "fast" | "premium"
    use_case="ticket_classification",
    entity_id="uuid-do-ticket",
)
```

### 3. TypeScript (API Vercel/Next)

```typescript
import { resolveLLMProvider, callLLM } from './llm_provider';

const provider = resolveLLMProvider();
if (!provider) throw new Error('Sem LLM configurado');

const result = await callLLM({
  provider,
  systemPrompt: 'Você é um assistente de CRM...',
  messages: [{ role: 'user', content: 'Qual o status desse deal?' }],
  maxTokens: 1024,
});

console.log(result.text);     // resposta
console.log(result.provider); // "deepinfra"
```

---

## Tabela de Logging (opcional)

Se quiser rastrear custos e uso no banco:

```sql
CREATE TABLE llm_calls (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now(),
  provider TEXT NOT NULL,
  model TEXT NOT NULL,
  tier TEXT,
  prompt_hash TEXT,
  prompt_preview TEXT,
  tokens_input INT DEFAULT 0,
  tokens_output INT DEFAULT 0,
  cost_usd NUMERIC(10,6) DEFAULT 0,
  duration_ms INT DEFAULT 0,
  cached BOOLEAN DEFAULT false,
  success BOOLEAN DEFAULT true,
  error TEXT,
  use_case TEXT,
  entity_id UUID,
  user_id UUID
);

-- Index pra queries de custo
CREATE INDEX idx_llm_calls_use_case ON llm_calls(use_case);
CREATE INDEX idx_llm_calls_created ON llm_calls(created_at);
```

Query de custo:
```sql
SELECT 
  use_case,
  provider,
  COUNT(*) as calls,
  SUM(cost_usd) as total_cost,
  AVG(duration_ms) as avg_latency_ms
FROM llm_calls
WHERE created_at > now() - interval '7 days'
GROUP BY 1, 2
ORDER BY total_cost DESC;
```

---

## Custos Reais (validados em produção)

| Operação | DeepInfra | Anthropic | Economia |
|----------|-----------|-----------|----------|
| 1 pergunta (~1K tokens) | $0.0002 | $0.007 | **35x** |
| 100 perguntas/dia | $0.02/dia | $0.70/dia | $0.68/dia |
| 1 mês (3K queries) | $0.60/mês | $20.70/mês | **$20/mês** |

Com **$30 no DeepInfra**, o CRM roda **~150.000 interações**.

---

## Model Tiers

| Tier | Quando usar | Default |
|------|------------|---------|
| `cheap` | Maioria dos casos (classificação, resumo, Q&A) | DeepInfra Qwen 72B |
| `fast` | Latência crítica (<500ms, chat real-time) | Groq Llama 70B |
| `premium` | Análise complexa, raciocínio longo | Anthropic Claude |

---

## Features

- [x] Cascata de fallback automática (5 providers)
- [x] Retry com exponential backoff (3 tentativas)
- [x] Memo cache em memória (500 entries, custo $0 em cache hit)
- [x] Logging de cada chamada (provider, custo, tokens, latência)
- [x] Suporte a visão (imagens) — DeepInfra, OpenAI, Anthropic
- [x] Zero dependência de SDK (só httpx/fetch)
- [x] Preços atualizados 04/2026
