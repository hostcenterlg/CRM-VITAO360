import { redirect } from 'next/navigation';

/**
 * /docs -> /manual
 *
 * O manual real esta em /manual. Este redirect cobre URLs digitadas
 * manualmente, bookmarks legados e links internos antigos.
 *
 * Motivo da inversao: o nome /docs colidia com a rota declarada no
 * vercel.json da raiz do monorepo (que mapeia /docs para o backend
 * FastAPI em /api/index.py). Esse conflito resultava em 404 cacheado
 * pelo Vercel no deploy do frontend (intelligent-crm360.vercel.app).
 *
 * Manter este shim aqui evita quebrar bookmarks, ate que todos os
 * links tenham migrado.
 */
export default function DocsRedirect() {
  redirect('/manual');
}
