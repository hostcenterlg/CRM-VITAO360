'use client';

// ---------------------------------------------------------------------------
// /projecao — standalone page que renderiza ProjecaoView
// O mesmo conteudo tambem aparece como tab interna em /dashboard (tab "projecao").
// ---------------------------------------------------------------------------

import { ProjecaoView } from '@/components/dashboard/ProjecaoView';

export default function ProjecaoPage() {
  return (
    <div className="space-y-6">
      {/* Page heading — apenas no standalone, ProjecaoView tem seu proprio h2 */}
      <ProjecaoView />
    </div>
  );
}
