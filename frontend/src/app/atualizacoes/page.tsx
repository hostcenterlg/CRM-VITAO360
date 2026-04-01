'use client';

import { useState } from 'react';

// ---------------------------------------------------------------------------
// Atualizações & Pendências — CRM VITAO360
// Rastreamento completo de tudo que foi pedido, feito e falta
// ---------------------------------------------------------------------------

type Status = 'done' | 'partial' | 'pending' | 'blocked';
type Category = 'feature' | 'fix' | 'infra' | 'data' | 'integration';

interface Item {
  id: string;
  pedido: string;
  descricao: string;
  status: Status;
  categoria: Category;
  sessao: string;
  detalhes: string;
  commits?: string[];
}

const STATUS_CONFIG: Record<Status, { label: string; bg: string; text: string; icon: string }> = {
  done:    { label: 'Concluído',  bg: 'bg-green-50 border-green-200',  text: 'text-green-700',  icon: '✓' },
  partial: { label: 'Parcial',    bg: 'bg-yellow-50 border-yellow-200', text: 'text-yellow-700', icon: '◐' },
  pending: { label: 'Pendente',   bg: 'bg-red-50 border-red-200',      text: 'text-red-700',    icon: '○' },
  blocked: { label: 'Bloqueado',  bg: 'bg-gray-50 border-gray-200',    text: 'text-gray-600',   icon: '⊘' },
};

const CAT_CONFIG: Record<Category, { label: string; color: string }> = {
  feature:     { label: 'Feature',     color: 'bg-blue-100 text-blue-700' },
  fix:         { label: 'Fix',         color: 'bg-orange-100 text-orange-700' },
  infra:       { label: 'Infra',       color: 'bg-purple-100 text-purple-700' },
  data:        { label: 'Dados',       color: 'bg-teal-100 text-teal-700' },
  integration: { label: 'Integração',  color: 'bg-pink-100 text-pink-700' },
};

// ---------------------------------------------------------------------------
// DADOS — Tudo que foi pedido e o estado real
// ---------------------------------------------------------------------------

const ITEMS: Item[] = [
  // ═══ SESSÃO 31/MAR/2026 ═══

  // PEDIDO: Organizar working tree (9 commits pendentes)
  {
    id: 'S1-001',
    pedido: 'Organizar working tree — commits atômicos',
    descricao: '20 arquivos modificados + 22 untracked estavam sem commit. Organizar em commits atômicos por feature.',
    status: 'done',
    categoria: 'infra',
    sessao: '31/Mar/2026',
    detalhes: '9 commits atômicos criados e pushados. Backend resilience, Vercel entry, UI foundations, Sidebar, Inbox, Pipeline, Tarefas, page redesigns, docs.',
    commits: ['c22d0e1', 'da8e97f', '1c05437', '81c8bff', 'e5e3aa8', '860a1e1', 'ffc5b9e', '6804718', '34629a3'],
  },
  {
    id: 'S1-002',
    pedido: 'QA — Validar build frontend + backend',
    descricao: 'Rodar build Next.js e verificar import do backend FastAPI.',
    status: 'done',
    categoria: 'fix',
    sessao: '31/Mar/2026',
    detalhes: 'Frontend: 16 rotas, 0 erros TS, 0 warnings. Backend: 62 rotas carregam sem erro. Pre-commit hooks: 45/45 passaram.',
  },
  {
    id: 'S1-003',
    pedido: 'Fix segurança — traceback exposto em produção',
    descricao: 'Global exception handler retornava traceback completo ao cliente.',
    status: 'done',
    categoria: 'fix',
    sessao: '31/Mar/2026',
    detalhes: 'Corrigido: retorna "Erro interno do servidor" ao cliente, loga traceback internamente.',
    commits: ['c22d0e1'],
  },
  {
    id: 'S1-004',
    pedido: 'Fix segurança — proteger dados sensíveis no gitignore',
    descricao: 'data/*.json com CNPJs de clientes reais não estavam protegidos.',
    status: 'done',
    categoria: 'fix',
    sessao: '31/Mar/2026',
    detalhes: 'Adicionado ao .gitignore: data/*.json, deskrio_*.json, mercos_*.json, sales_hunter CSVs.',
    commits: ['da8e97f'],
  },

  // PEDIDO: Deskrio — mensagens reais no Inbox
  {
    id: 'S1-005',
    pedido: 'Inbox — espelho real do Deskrio (mensagens WA)',
    descricao: 'Inbox mostrava apenas atendimentos CRM. Pedido: ver mensagens reais do WhatsApp como no Deskrio.',
    status: 'partial',
    categoria: 'integration',
    sessao: '31/Mar/2026',
    detalhes: 'Backend: 3 novos métodos no deskrio_service + 2 endpoints (/conversa/{cnpj}, /mensagens/{ticket_id}). Frontend: Inbox busca WA real com fallback CRM. PORÉM: Deskrio API está 503 (fora do ar no lado DELES) e token de produção retorna 0 conexões.',
    commits: ['29d60b0', 'e32320a'],
  },
  {
    id: 'S1-006',
    pedido: 'Inbox — webhook tempo real do Deskrio',
    descricao: 'Para ver mensagens em tempo real sem precisar recarregar.',
    status: 'pending',
    categoria: 'integration',
    sessao: '31/Mar/2026',
    detalhes: 'API Deskrio não suporta webhooks — é polling only. Precisaria implementar polling periódico ou SSE no backend.',
  },
  {
    id: 'S1-007',
    pedido: 'Inbox — mídia (imagens, áudios, docs)',
    descricao: 'Deskrio suporta mídia mas Inbox só mostra texto.',
    status: 'pending',
    categoria: 'feature',
    sessao: '31/Mar/2026',
    detalhes: 'Campo media_url existe no schema mas frontend não renderiza. Precisa adicionar preview de imagens e player de áudio.',
  },

  // PEDIDO: Dashboard CEO v2 (8 abas + recharts)
  {
    id: 'S1-008',
    pedido: 'Dashboard CEO — 8 abas com gráficos recharts',
    descricao: 'Replicar dashboard_vitao360_v2.jsx no nosso sistema com dados reais das APIs.',
    status: 'done',
    categoria: 'feature',
    sessao: '31/Mar/2026',
    detalhes: '8 abas implementadas: Resumo, Operacional, Funil+Canais, Performance, Saúde, Redes+Sinaleiro, Motivos+RNC, Produtividade. Recharts (AreaChart, BarChart, PieChart). Dados de APIs reais. Seções sem API mostram "Em breve".',
    commits: ['4d1e14f'],
  },

  // PEDIDO: Deploy + configuração
  {
    id: 'S1-009',
    pedido: 'Deploy atualizado no Vercel',
    descricao: 'Código novo não estava deployado. Forçar redeploy.',
    status: 'done',
    categoria: 'infra',
    sessao: '31/Mar/2026',
    detalhes: 'Redeploy forçado do frontend + backend no Vercel. Build passou com 16 rotas. URL: intelligent-crm360.vercel.app',
  },
  {
    id: 'S1-010',
    pedido: 'Configurar Deskrio em produção',
    descricao: 'DESKRIO_API_TOKEN não estava nas env vars do Vercel.',
    status: 'done',
    categoria: 'infra',
    sessao: '31/Mar/2026',
    detalhes: 'DESKRIO_API_TOKEN adicionado ao Vercel backend. configurado=true em produção. Porém API Deskrio retorna 503 (problema deles).',
  },

  // PEDIDO: Recalcular Motor + Dados
  {
    id: 'S1-011',
    pedido: 'Recalcular Motor de Regras nos 1.581 clientes',
    descricao: 'Clientes no banco sem Score, Temperatura, Fase, Sinaleiro corretos.',
    status: 'done',
    categoria: 'data',
    sessao: '31/Mar/2026',
    detalhes: '1.581 clientes recalculados com Motor V4. Score, Temperatura (QUENTE/MORNO/FRIO), Sinaleiro (5 cores), Fase, Estágio, Prioridade atualizados no PostgreSQL Neon.',
  },
  {
    id: 'S1-012',
    pedido: 'Regenerar Agenda completa (40/consultor)',
    descricao: 'Agenda tinha 140 itens genéricos. Gerar 40 priorizados por Score para cada consultor.',
    status: 'done',
    categoria: 'data',
    sessao: '31/Mar/2026',
    detalhes: '160 itens gerados (40 MANU + 40 LARISSA + 40 DAIANE + 40 JULIO). Ordenados por Score DESC, excluindo PROSPECTs.',
  },

  // ═══ PENDÊNCIAS IDENTIFICADAS ═══

  {
    id: 'P-001',
    pedido: 'Importar LOG completo de atendimentos',
    descricao: 'Banco tem apenas 475 registros de LOG (5 dias). Deveria ter 10.000+. Sem LOG: Agenda genérica, Tarefas vazia, Pipeline sem estágios.',
    status: 'pending',
    categoria: 'data',
    sessao: 'Pendência',
    detalhes: 'Precisa rodar pipeline de import com dados do CONTROLE_FUNIL (10.484 registros) + tickets Deskrio (5.329) + LOG histórico. Fonte: data/output/phase04/log_final_validated.json (20.830 registros).',
  },
  {
    id: 'P-002',
    pedido: 'Importar dados Mercos completos (6.429 clientes)',
    descricao: 'Extração Mercos completou 6.429 clientes mas nunca foi importada no PostgreSQL de produção.',
    status: 'pending',
    categoria: 'data',
    sessao: 'Pendência',
    detalhes: 'data/mercos_clientes_completo.json tem referência. Precisa consolidar e importar via pipeline de import ou script direto.',
  },
  {
    id: 'P-003',
    pedido: 'Pipeline Kanban — enriquecer com estágios reais',
    descricao: 'Pipeline mostra só 4 estágios (PROSPECÇÃO 1151, RESGATE 277, PÓS-VENDA 104, REATIVAÇÃO 49). Motor tem 14 estágios.',
    status: 'pending',
    categoria: 'feature',
    sessao: 'Pendência',
    detalhes: 'Precisa de mais LOG/atendimentos para clientes terem resultado registrado. Sem resultado, Motor gera só estágio genérico por situação.',
  },
  {
    id: 'P-004',
    pedido: 'Tarefas — popular com dados reais',
    descricao: 'Página de Tarefas vazia. 0 RNCs, follow-ups dependem de LOG.',
    status: 'pending',
    categoria: 'data',
    sessao: 'Pendência',
    detalhes: 'Depende de P-001 (importar LOG). Com LOG populado, follow-ups e tarefas são gerados automaticamente.',
  },
  {
    id: 'P-005',
    pedido: 'RNC — cadastrar registros reais',
    descricao: '0 RNCs no banco. Página funciona mas está vazia.',
    status: 'pending',
    categoria: 'data',
    sessao: 'Pendência',
    detalhes: 'RNCs precisam ser cadastrados manualmente ou importados de fonte externa. Não existe histórico digital de RNCs na VITAO.',
  },
  {
    id: 'P-006',
    pedido: 'Deskrio — resolver 503 / conexões vazias',
    descricao: 'API Deskrio retorna 503 (fora do ar) e 0 conexões WA em produção.',
    status: 'blocked',
    categoria: 'integration',
    sessao: 'Pendência',
    detalhes: 'Problema no lado do Deskrio. Token está configurado corretamente. Quando voltar, testar GET /v1/api/connections. Se continuar vazio, pode ser que o token de produção é diferente do local.',
  },
  {
    id: 'P-007',
    pedido: 'Definir plataforma: Railway vs Vercel',
    descricao: 'Código suporta Railway E Vercel. Precisa decidir e limpar o que não usar.',
    status: 'pending',
    categoria: 'infra',
    sessao: 'Pendência',
    detalhes: 'Atualmente: Frontend no Vercel (intelligent-crm360.vercel.app), Backend no Vercel (crm-vitao360.vercel.app), DB no Neon PostgreSQL. Railway tem config mas não está ativo.',
  },
  {
    id: 'P-008',
    pedido: 'Supabase em vez de Neon',
    descricao: 'Leandro perguntou por que não usa Supabase PostgreSQL no Vercel.',
    status: 'pending',
    categoria: 'infra',
    sessao: '31/Mar/2026',
    detalhes: 'Neon foi criado automaticamente pelo Vercel. Migrar para Supabase é possível — basta trocar DATABASE_URL. Dashboard Supabase é melhor. Não afeta funcionamento.',
  },
  {
    id: 'P-009',
    pedido: 'Cache do browser impedindo ver mudanças',
    descricao: 'Leandro vê versão antiga mesmo após deploy. Precisa limpar cache ou abrir anônima.',
    status: 'pending',
    categoria: 'fix',
    sessao: '31/Mar/2026',
    detalhes: 'Solução: Ctrl+Shift+Delete (limpar cache) ou aba anônima (Ctrl+Shift+N). Pode ser resolvido adicionando cache-busting headers no Vercel.',
  },
  {
    id: 'P-010',
    pedido: 'DAIANE com 1.164 clientes (1.066 prospects lixo)',
    descricao: '72% da base são PROSPECTs atribuídos à DAIANE sem dados. Polui todas as métricas.',
    status: 'pending',
    categoria: 'data',
    sessao: 'Pendência',
    detalhes: 'Os 1.066 prospects da DAIANE são provavelmente clientes de redes/franquias sem atribuição correta. Precisa redistribuir ou reclassificar.',
  },
];

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

type FilterStatus = 'all' | Status;
type FilterCat = 'all' | Category;

function StatusBadge({ status }: { status: Status }) {
  const cfg = STATUS_CONFIG[status];
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 text-xs font-bold rounded-full border ${cfg.bg} ${cfg.text}`}>
      <span>{cfg.icon}</span> {cfg.label}
    </span>
  );
}

function CatBadge({ cat }: { cat: Category }) {
  const cfg = CAT_CONFIG[cat];
  return (
    <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-bold rounded ${cfg.color}`}>
      {cfg.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

export default function AtualizacoesPage() {
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all');
  const [filterCat, setFilterCat] = useState<FilterCat>('all');
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  const filtered = ITEMS.filter((item) => {
    if (filterStatus !== 'all' && item.status !== filterStatus) return false;
    if (filterCat !== 'all' && item.categoria !== filterCat) return false;
    return true;
  });

  const counts = {
    done: ITEMS.filter((i) => i.status === 'done').length,
    partial: ITEMS.filter((i) => i.status === 'partial').length,
    pending: ITEMS.filter((i) => i.status === 'pending').length,
    blocked: ITEMS.filter((i) => i.status === 'blocked').length,
  };

  function toggleExpand(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Atualizações & Pendências</h1>
        <p className="text-sm text-gray-500 mt-1">
          Rastreamento de tudo que foi pedido, implementado e falta fazer.
        </p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {([['done', 'Concluídos', '#00B050'], ['partial', 'Parciais', '#F59E0B'], ['pending', 'Pendentes', '#EF4444'], ['blocked', 'Bloqueados', '#6B7280']] as const).map(([key, label, color]) => (
          <button
            key={key}
            type="button"
            onClick={() => setFilterStatus(filterStatus === key ? 'all' : key)}
            className={`p-4 rounded-xl border text-center transition-all ${filterStatus === key ? 'ring-2 ring-offset-1' : ''}`}
            style={{ borderLeftColor: color, borderLeftWidth: 4, ...(filterStatus === key ? { ringColor: color } : {}) }}
          >
            <div className="text-3xl font-black" style={{ color, fontFamily: 'monospace' }}>
              {counts[key]}
            </div>
            <div className="text-xs font-semibold text-gray-600 mt-1">{label}</div>
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        <span className="text-xs font-semibold text-gray-500 self-center mr-1">Categoria:</span>
        {(['all', ...Object.keys(CAT_CONFIG)] as (FilterCat)[]).map((cat) => (
          <button
            key={cat}
            type="button"
            onClick={() => setFilterCat(filterCat === cat ? 'all' : cat)}
            className={`px-3 py-1 text-xs font-semibold rounded-full border transition-all
              ${filterCat === cat
                ? 'bg-gray-900 text-white border-gray-900'
                : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
              }`}
          >
            {cat === 'all' ? 'Todas' : CAT_CONFIG[cat as Category].label}
          </button>
        ))}
        {(filterStatus !== 'all' || filterCat !== 'all') && (
          <button
            type="button"
            onClick={() => { setFilterStatus('all'); setFilterCat('all'); }}
            className="px-3 py-1 text-xs font-semibold text-red-600 bg-red-50 border border-red-200 rounded-full hover:bg-red-100"
          >
            Limpar filtros
          </button>
        )}
      </div>

      {/* Progress bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs font-semibold text-gray-600">
            Progresso geral: {counts.done}/{ITEMS.length} concluídos
          </span>
          <span className="text-xs font-bold" style={{ color: '#00B050' }}>
            {Math.round((counts.done / ITEMS.length) * 100)}%
          </span>
        </div>
        <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden flex">
          <div className="h-full bg-green-500" style={{ width: `${(counts.done / ITEMS.length) * 100}%` }} />
          <div className="h-full bg-yellow-400" style={{ width: `${(counts.partial / ITEMS.length) * 100}%` }} />
          <div className="h-full bg-red-400" style={{ width: `${(counts.pending / ITEMS.length) * 100}%` }} />
          <div className="h-full bg-gray-300" style={{ width: `${(counts.blocked / ITEMS.length) * 100}%` }} />
        </div>
      </div>

      {/* Items list */}
      <div className="space-y-2">
        {filtered.map((item) => {
          const isOpen = expanded.has(item.id);
          return (
            <div
              key={item.id}
              className={`bg-white rounded-xl border transition-all ${isOpen ? 'shadow-md border-gray-300' : 'border-gray-200 hover:border-gray-300'}`}
            >
              <button
                type="button"
                onClick={() => toggleExpand(item.id)}
                className="w-full flex items-start gap-3 px-4 py-3 text-left"
              >
                {/* Status icon */}
                <span className={`mt-0.5 w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 ${STATUS_CONFIG[item.status].bg} ${STATUS_CONFIG[item.status].text}`} style={{ border: '1px solid' }}>
                  {STATUS_CONFIG[item.status].icon}
                </span>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-sm font-semibold text-gray-900">{item.pedido}</span>
                    <StatusBadge status={item.status} />
                    <CatBadge cat={item.categoria} />
                  </div>
                  <p className="text-xs text-gray-500 mt-0.5 line-clamp-1">{item.descricao}</p>
                </div>

                {/* Session + expand */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="text-[10px] font-medium text-gray-400 bg-gray-50 px-2 py-0.5 rounded">
                    {item.sessao}
                  </span>
                  <svg
                    className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`}
                    fill="none" viewBox="0 0 24 24" stroke="currentColor"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </button>

              {/* Expanded details */}
              {isOpen && (
                <div className="px-4 pb-4 pt-0 ml-9 border-t border-gray-100 mt-0">
                  <p className="text-xs text-gray-700 leading-relaxed mt-3">{item.detalhes}</p>
                  {item.commits && item.commits.length > 0 && (
                    <div className="mt-2 flex items-center gap-1 flex-wrap">
                      <span className="text-[10px] font-semibold text-gray-500">Commits:</span>
                      {item.commits.map((c) => (
                        <code key={c} className="text-[10px] font-mono bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                          {c}
                        </code>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="mt-8 mb-4 p-4 bg-gray-50 rounded-xl border border-gray-200 text-center">
        <p className="text-xs text-gray-500">
          CRM VITAO360 — Última atualização: 01/Abr/2026 — {ITEMS.length} itens rastreados
        </p>
      </div>
    </div>
  );
}
