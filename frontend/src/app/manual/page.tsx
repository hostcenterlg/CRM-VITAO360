import { redirect } from 'next/navigation';

/**
 * /manual → /docs
 *
 * O manual real está em /docs. Este redirect cobre URLs digitadas
 * manualmente ou bookmarks legados que esperam /manual.
 */
export default function ManualRedirect() {
  redirect('/docs');
}
