import { redirect } from 'next/navigation';

/**
 * /dashboard → /
 *
 * O Dashboard real é a homepage (/). Este redirect garante que
 * bookmarks ou URLs digitadas como /dashboard cheguem ao destino certo.
 */
export default function DashboardRedirect() {
  redirect('/');
}
