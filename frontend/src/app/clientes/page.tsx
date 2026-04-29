// /clientes — alias permanente de /carteira (Briefing 29-Abr-2026)
// Decisao tatica: next.config.mjs tem redirect server-side para /carteira.
// Este componente serve como fallback client-side para garantir compatibilidade
// com builds de desenvolvimento e navegacao direta pelo App Router.

import { redirect } from 'next/navigation';

export default function ClientesPage() {
  redirect('/carteira');
}
