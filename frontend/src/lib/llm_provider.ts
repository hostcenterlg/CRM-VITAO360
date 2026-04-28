/**
 * LLM Provider — Camada TypeScript provider-agnostic (reutilizável)
 * =================================================================
 *
 * ORIGEM: US County Radar (testado em produção no Vercel)
 * ADAPTADO PARA: CRM360 ou qualquer projeto Node/Vercel/Next
 *
 * Cascata: DeepInfra → Groq → Anthropic → OpenAI
 * Usa quem tiver key configurada. Zero dependência de SDK externo (só fetch).
 *
 * ENV VARS (configurar no Vercel/Railway/etc):
 *   DEEPINFRA_API_KEY  (preferencial — $0.13/$0.40 por 1M tokens)
 *   GROQ_API_KEY       (secondary — latência <500ms)
 *   ANTHROPIC_API_KEY   (premium — mais caro)
 *   OPENAI_API_KEY      (fallback universal)
 *
 * USO:
 *   import { resolveLLMProvider, callLLM } from './llm_provider';
 *
 *   const provider = resolveLLMProvider();
 *   if (!provider) throw new Error('Nenhum LLM configurado');
 *
 *   const reply = await callLLM({
 *     provider,
 *     systemPrompt: 'Você é um assistente de CRM...',
 *     messages: [{ role: 'user', content: 'Resuma este lead' }],
 *     maxTokens: 1024,
 *   });
 *   console.log(reply.text, reply.provider);
 */

// ============================================================================
// Types
// ============================================================================

export interface LLMProvider {
  name: 'deepinfra' | 'groq' | 'anthropic' | 'openai';
  apiKey: string;
  model: string;
  endpoint: string;
  isAnthropicNative: boolean;
}

export interface LLMMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface CallLLMOptions {
  provider: LLMProvider;
  systemPrompt: string;
  messages: LLMMessage[];
  maxTokens?: number;
  temperature?: number;
}

export interface LLMResult {
  text: string;
  provider: string;
  model: string;
}

// ============================================================================
// Provider Resolution (cascata)
// ============================================================================

export function resolveLLMProvider(): LLMProvider | null {
  // 1. DeepInfra — primary cheap ($0.13/$0.40 por 1M)
  const deepinfraKey = (process.env.DEEPINFRA_API_KEY || '').trim();
  if (deepinfraKey.length > 10) {
    return {
      name: 'deepinfra',
      apiKey: deepinfraKey,
      model: 'Qwen/Qwen2.5-72B-Instruct',
      endpoint: 'https://api.deepinfra.com/v1/openai/chat/completions',
      isAnthropicNative: false,
    };
  }

  // 2. Groq — fast tier (latência <500ms)
  const groqKey = (process.env.GROQ_API_KEY || '').trim();
  if (groqKey.length > 10) {
    return {
      name: 'groq',
      apiKey: groqKey,
      model: 'llama-3.3-70b-versatile',
      endpoint: 'https://api.groq.com/openai/v1/chat/completions',
      isAnthropicNative: false,
    };
  }

  // 3. Anthropic — premium (mais caro, melhor qualidade)
  const anthropicKey = (process.env.ANTHROPIC_API_KEY || '').trim();
  if (anthropicKey.length > 10) {
    return {
      name: 'anthropic',
      apiKey: anthropicKey,
      model: 'claude-sonnet-4-6',
      endpoint: 'https://api.anthropic.com/v1/messages',
      isAnthropicNative: true,
    };
  }

  // 4. OpenAI — fallback universal
  const openaiKey = (process.env.OPENAI_API_KEY || '').trim();
  if (openaiKey.length > 10) {
    return {
      name: 'openai',
      apiKey: openaiKey,
      model: 'gpt-4o-mini',
      endpoint: 'https://api.openai.com/v1/chat/completions',
      isAnthropicNative: false,
    };
  }

  return null;
}

// ============================================================================
// LLM Caller (unified)
// ============================================================================

export async function callLLM(opts: CallLLMOptions): Promise<LLMResult> {
  const { provider, systemPrompt, messages, maxTokens = 1024, temperature = 0.3 } = opts;

  if (provider.isAnthropicNative) {
    // ── Anthropic native API ─────────────────────────────────────────────
    const resp = await fetch(provider.endpoint, {
      method: 'POST',
      headers: {
        'x-api-key': provider.apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
      },
      body: JSON.stringify({
        model: provider.model,
        max_tokens: maxTokens,
        system: systemPrompt,
        messages: messages.map(m => ({ role: m.role, content: m.content })),
      }),
    });

    if (!resp.ok) {
      const errText = await resp.text().catch(() => '');
      throw new Error(`anthropic ${resp.status}: ${errText.slice(0, 200)}`);
    }

    const data = await resp.json() as {
      content?: Array<{ type: string; text?: string }>;
    };
    const text = (data.content ?? [])
      .filter(b => b.type === 'text')
      .map(b => b.text ?? '')
      .join('\n')
      .trim() || 'Resposta não disponível';

    return { text, provider: provider.name, model: provider.model };
  } else {
    // ── OpenAI-compatible (DeepInfra/Groq/OpenAI) ─────────────────────
    const resp = await fetch(provider.endpoint, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${provider.apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: provider.model,
        messages: [
          { role: 'system', content: systemPrompt },
          ...messages.map(m => ({ role: m.role, content: m.content })),
        ],
        max_tokens: maxTokens,
        temperature,
      }),
    });

    if (!resp.ok) {
      const errText = await resp.text().catch(() => '');
      throw new Error(`${provider.name} ${resp.status}: ${errText.slice(0, 200)}`);
    }

    const data = await resp.json() as {
      choices?: Array<{ message?: { content?: string } }>;
    };
    const text = (data.choices?.[0]?.message?.content ?? '').trim() || 'Resposta não disponível';

    return { text, provider: provider.name, model: provider.model };
  }
}

// ============================================================================
// Example: Vercel API Route usage
// ============================================================================

/*
import { resolveLLMProvider, callLLM } from './llm_provider';

export default async function handler(req, res) {
  const provider = resolveLLMProvider();
  if (!provider) {
    return res.status(500).json({
      error: 'Nenhum LLM configurado. Configure: DEEPINFRA_API_KEY, GROQ_API_KEY, ANTHROPIC_API_KEY ou OPENAI_API_KEY'
    });
  }

  const result = await callLLM({
    provider,
    systemPrompt: 'Você é um assistente de CRM especializado em vendas B2B...',
    messages: [{ role: 'user', content: req.body.message }],
    maxTokens: 1024,
  });

  return res.status(200).json({
    reply: result.text,
    provider: result.provider,
    model: result.model,
  });
}
*/
