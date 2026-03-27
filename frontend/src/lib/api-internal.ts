// api-internal — re-exporta fetchJson de api.ts
// Mantido por compatibilidade com imports existentes (redes/page.tsx).
// Usa o mesmo BASE_URL e auth logic de api.ts — sem duplicacao.

export { fetchJson } from '@/lib/api';
