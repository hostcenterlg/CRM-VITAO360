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
  {
    id: 'S1-001',
    pedido: 'Organizar working tree — commits atômicos',
    descricao: '20 arquivos modificados + 22 untracked organizados em commits atômicos por feature.',
    status: 'done',
    categoria: 'infra',
    sessao: '31/Mar/2026',
    detalhes: '9 commits atômicos criados e pushados. Backend resilience, Vercel entry, UI foundations, Sidebar, Inbox, Pipeline, Tarefas, page redesigns, docs.',
    commits: ['c22d0e1', 'da8e97f', '1c05437', '81c8bff', 'e5e3aa8', '860a1e1', 'ffc5b9e', '6804718', '34629a3'],
  },
  {
    id: 'S1-002',
    pedido: 'QA — Validar build frontend + backend',
    descricao: 'Build Next.js + import FastAPI validados.',
    status: 'done',
    categoria: 'fix',
    sessao: '31/Mar/2026',
    detalhes: 'Frontend: 16 rotas, 0 erros. Backend: 62 rotas OK. Pre-commit: 45/45.',
  },
  {
    id: 'S1-003',
    pedido: 'Fix segurança — traceback + gitignore',
    descricao: 'Traceback exposto corrigido + dados sensíveis protegidos no .gitignore.',
    status: 'done',
    categoria: 'fix',
    sessao: '31/Mar/2026',
    detalhes: 'Global exception handler seguro. .gitignore protege data/*.json, deskrio_*.json, mercos_*.json.',
    commits: ['c22d0e1', 'da8e97f'],
  },
  {
    id: 'S1-004',
    pedido: 'Dashboard CEO — 8 abas com gráficos recharts',
    descricao: '8 abas: Resumo, Operacional, Funil, Performance, Saúde, Redes, Motivos, Produtividade.',
    status: 'done',
    categoria: 'feature',
    sessao: '31/Mar/2026',
    detalhes: 'Recharts (AreaChart, BarChart, PieChart). Dados de APIs reais.',
    commits: ['4d1e14f'],
  },
  {
    id: 'S1-005',
    pedido: 'Inbox — espelho real do Deskrio (mensagens WA)',
    descricao: 'Backend Deskrio service + endpoints. Frontend busca WA real com fallback CRM.',
    status: 'done',
    categoria: 'integration',
    sessao: '31/Mar/2026',
    detalhes: '3 métodos deskrio_service + 2 endpoints. Retry com backoff exponencial + cache TTL 5min. Fallback gracioso quando API indisponível.',
    commits: ['29d60b0', 'e32320a', '4ded6df'],
  },
  {
    id: 'S1-006',
    pedido: 'Deploy + Motor + Agenda recalculados',
    descricao: 'Deploy Vercel, Motor V4 em 1.581 clientes, Agenda 160 itens.',
    status: 'done',
    categoria: 'infra',
    sessao: '31/Mar/2026',
    detalhes: 'Frontend: intelligent-crm360.vercel.app. Motor: Score, Temperatura, Sinaleiro, Fase. Agenda: 40/consultor.',
  },

  // ═══ SESSÃO 01/ABR/2026 ═══

  {
    id: 'S2-001',
    pedido: 'Segurança — rate limiting + headers + Deskrio retry',
    descricao: 'Rate limiting 100/min (10/min login), 6 security headers, Deskrio retry com cache.',
    status: 'done',
    categoria: 'fix',
    sessao: '01/Abr/2026',
    detalhes: 'RateLimitMiddleware (429 com Retry-After), SecurityHeadersMiddleware (HSTS, X-Frame-Options, etc.), Deskrio TTLCache 5min + backoff 1s/2s/4s. env.example atualizado.',
    commits: ['4ded6df'],
  },
  {
    id: 'S2-002',
    pedido: 'Testes automatizados — 509 testes',
    descricao: '138 testes novos: auth, clientes, Two-Base, motor, score, CNPJ.',
    status: 'done',
    categoria: 'fix',
    sessao: '01/Abr/2026',
    detalhes: 'pytest + TestClient. In-memory SQLite. Cobertura: auth (13), clientes (16), two-base (12), motor (15), score (44), cnpj (16). 509 total passando.',
    commits: ['16f0c5e'],
  },
  {
    id: 'S2-003',
    pedido: 'Banco de dados populado — 1.581 clientes, 1.231 vendas',
    descricao: 'Script populate_saas_db.py enriqueceu DB com dados reais das fontes.',
    status: 'done',
    categoria: 'data',
    sessao: '01/Abr/2026',
    detalhes: '1.581 clientes, 1.231 vendas, 6.384 metas, 1.581 score_historico. Faturamento R$2.102.419 (0.55% do baseline). Two-Base PASS. Zero ALUCINACAO.',
    commits: ['31b9176'],
  },
  {
    id: 'S2-004',
    pedido: 'Alembic migrations + scripts deprecated arquivados',
    descricao: 'Alembic configurado com migration inicial (12 tabelas). 11 scripts movidos para _archive/.',
    status: 'done',
    categoria: 'infra',
    sessao: '01/Abr/2026',
    detalhes: 'alembic.ini + env.py + initial migration. Scripts _agent3, _agent4, _bootstrap, etc. arquivados.',
    commits: ['ef5d3db', '9a47532'],
  },
  {
    id: 'S2-005',
    pedido: 'Dashboard — ZERO mock data (tudo real)',
    descricao: 'Removidos TODOS os Math.round(kpis * X) fabricados. Dados reais do banco.',
    status: 'done',
    categoria: 'feature',
    sessao: '01/Abr/2026',
    detalhes: 'TabOperacional, TabFunil, TabSaude, TabRedes, TabProdutividade — tudo usa endpoints reais. fetchAtividades() e fetchPositivacao() adicionados.',
    commits: ['d0062da', '1bde8b3'],
  },
  {
    id: 'S2-006',
    pedido: 'Positivação + Atividades + Status Pedido endpoints',
    descricao: 'GET /dashboard/positivacao, GET /dashboard/atividades, PATCH /vendas/{id}/status.',
    status: 'done',
    categoria: 'feature',
    sessao: '01/Abr/2026',
    detalhes: 'Positivação: taxa por situação e consultor. Atividades: por tipo, resultado, consultor, mês. Status: DIGITADO>LIBERADO>FATURADO>ENTREGUE>CANCELADO com audit log.',
    commits: ['69c0e2e'],
  },
  {
    id: 'S2-007',
    pedido: 'Produto + VendaItem + PrecoRegional — fundação Mercos',
    descricao: '3 novos modelos SQLAlchemy + 6 endpoints de Produtos.',
    status: 'done',
    categoria: 'feature',
    sessao: '01/Abr/2026',
    detalhes: 'Produto (codigo, nome, categoria, fabricante, preco_tabela), VendaItem (venda>produto link), PrecoRegional (preco por UF). API: list, categorias, mais-vendidos, detail, create, update.',
    commits: ['12aa0ef'],
  },
  {
    id: 'S2-008',
    pedido: 'Relatórios server-side XLSX — 5 reports',
    descricao: 'Engine openpyxl com headers VITAO verde, auto-filter, formatação R$.',
    status: 'done',
    categoria: 'feature',
    sessao: '01/Abr/2026',
    detalhes: 'GET /relatorios/{vendas|positivacao|atividades|clientes-inativos|metas}. StreamingResponse xlsx. Two-Base respeitada.',
    commits: ['3fef5ca'],
  },
  {
    id: 'S2-009',
    pedido: 'Edição expandida de clientes + Churn + Reativação + Positivação UF',
    descricao: 'PATCH clientes: telefone, email, cidade, uf. 3 novos indicadores dashboard.',
    status: 'done',
    categoria: 'feature',
    sessao: '01/Abr/2026',
    detalhes: 'Edição com audit log. Churn: clientes perdidos entre períodos. Reativação: reativados após 3 meses. Positivação por UF.',
    commits: ['81dac22', '215af84'],
  },
  {
    id: 'S2-010',
    pedido: '3 novas páginas: Pedidos, Produtos, Relatórios + Sidebar',
    descricao: '/pedidos (gestão com status), /produtos (catálogo), /relatorios (central xlsx). Sidebar atualizada.',
    status: 'done',
    categoria: 'feature',
    sessao: '01/Abr/2026',
    detalhes: 'Pedidos: cards agrupados por data, 5 status badges, transição por role. Produtos: busca, categorias, mais vendidos. Relatórios: 5 downloads xlsx com filtros contextuais. Sidebar: 3 novos itens.',
    commits: ['0902777'],
  },
  {
    id: 'S2-011',
    pedido: 'Spec Mercos completa documentada',
    descricao: '29 indicadores + 19 relatórios + Pedidos + Produtos + E-commerce + Tarefas mapeados.',
    status: 'done',
    categoria: 'feature',
    sessao: '01/Abr/2026',
    detalhes: 'MERCOS_SPEC_COMPLETA_SAAS.md: mapeamento direto do app.mercos.com/399424. Gap analysis: 70% paridade alcançada.',
    commits: ['c74fbb7'],
  },
  {
    id: 'S2-012',
    pedido: 'Fix schema mismatch AtividadesResponse + deprecated 422',
    descricao: 'Backend e frontend desalinhados no schema de atividades. HTTP 422 deprecated corrigido.',
    status: 'done',
    categoria: 'fix',
    sessao: '01/Abr/2026',
    detalhes: 'Backend: adicionado por_resultado + periodo. Frontend: types alinhados. Mensagens misleading removidas. HTTP_422_UNPROCESSABLE_ENTITY > CONTENT.',
    commits: ['1bde8b3'],
  },

  // ═══ SESSÃO 13/ABR/2026 ═══
  { id: 'S3-001', pedido: 'Fix 80 vendas DESCONHECIDO', descricao: '80 vendas (R$183K) reclassificadas: LARISSA 60, DAIANE 11, MANU 8, JULIO 1.', status: 'done', categoria: 'data', sessao: '13/Abr/2026', detalhes: 'Script fix_vendas_desconhecido.py. JOIN vendas↔clientes. Zero DESCONHECIDO restante.', commits: ['631b0fd'] },
  { id: 'S3-002', pedido: 'Metas 2026 distribuídas mensalmente', descricao: '488 metas anuais (mes=0) convertidas em 5.856 mensais. Projeção funcional.', status: 'done', categoria: 'data', sessao: '13/Abr/2026', detalhes: 'fix_metas_2026.py. Distribuição proporcional (meta_sap/12). Conservação R$0.00 diferença.', commits: ['631b0fd'] },
  { id: 'S3-003', pedido: 'Sync Deskrio → DB', descricao: '15.590 contatos processados. 2.711 matches, 248 telefones atualizados, 40 logs Kanban.', status: 'done', categoria: 'integration', sessao: '13/Abr/2026', detalhes: 'sync_deskrio_to_db.py. Match por telefone + fuzzy nome. Two-Base respeitada. Idempotente.', commits: ['631b0fd'] },
  { id: 'S3-004', pedido: 'Sync Mercos → DB', descricao: 'Indicadores + pedidos ativos. 3 telefones atualizados, 2 pedidos inseridos.', status: 'done', categoria: 'integration', sessao: '13/Abr/2026', detalhes: 'sync_mercos_to_db.py. Dados Mercos são sumários — extraiu máximo possível.', commits: ['ce581e6'] },
  { id: 'S3-005', pedido: 'VendaItens — 3.621 registros', descricao: 'Itens de pedido populados. Two-Base: sum(itens)=sum(vendas) diff R$0.00.', status: 'done', categoria: 'data', sessao: '13/Abr/2026', detalhes: 'populate_venda_itens.py. 1.233 vendas cobertas. Escala proporcional com absorção residual.', commits: ['ce581e6'] },
  { id: 'S3-006', pedido: 'Preços regionais — 6.534 registros', descricao: '242 produtos × 27 UFs. SUL base, SUDESTE +5%, NE +8%, CO +7%, NORTE +10%.', status: 'done', categoria: 'data', sessao: '13/Abr/2026', detalhes: 'populate_precos_regionais.py. Constraint UNIQUE(produto,uf) respeitada.', commits: ['ce581e6'] },
  { id: 'S3-007', pedido: 'Import UI end-to-end', descricao: '5 bugs schema mismatch corrigidos. Upload xlsx → process → DB funcional.', status: 'done', categoria: 'fix', sessao: '13/Abr/2026', detalhes: 'Status mapping CONCLUIDO→SUCESSO, items→itens, detalhes_erros, data_import, null safety.', commits: ['203fdc8'] },
  { id: 'S3-008', pedido: 'Recalcular Motor+Score+Sinaleiro+Agenda', descricao: '1.581 clientes recalculados. 140 agenda items. VERDE 82, AMARELO 41, VERMELHO 296, ROXO 1.151.', status: 'done', categoria: 'feature', sessao: '13/Abr/2026', detalhes: 'recalculate_all.py. Usa services do backend. Batch 500. Idempotente.', commits: ['7556f41'] },
  { id: 'S3-009', pedido: 'Dashboard Indicadores Mercos — 6 gráficos + filtros', descricao: 'Nova aba INDICADORES: Evolução Vendas, Positivação Diária, por Vendedor, Atendimentos, Curva ABC, E-commerce.', status: 'done', categoria: 'feature', sessao: '13/Abr/2026', detalhes: '6 endpoints backend + 56 testes. Frontend: Recharts charts + filtros globais mês/ano/vendedor.', commits: ['f2ceb68', 'dfc00b2'] },
  { id: 'S3-010', pedido: 'Central de IA — 9 agentes inteligentes', descricao: 'Página /ia com 9 cards: Briefing, Mensagem WA, Churn, Produto, Resumo, Sentimento, Previsão, Coach, Oportunidade.', status: 'done', categoria: 'feature', sessao: '13/Abr/2026', detalhes: '10 endpoints IA backend + 137 testes. Frontend: 9 cards interativos. Widget Insight do Dia no dashboard.', commits: ['884565c', '27eef1d', '3073f6e', '99df1ee'] },
  { id: 'S3-011', pedido: 'Pipeline automático + Notificações + Webhook', descricao: 'Orchestrator sync, sino de alertas, /admin/pipeline, webhook Deskrio.', status: 'done', categoria: 'infra', sessao: '13/Abr/2026', detalhes: 'PipelineService thread-safe. 4 tipos alerta. Webhook público Two-Base. 35 testes.', commits: ['9676c7f', 'a31ca1d'] },
  { id: 'S3-012', pedido: 'Mobile-first + Sidebar colapsável', descricao: 'Sidebar icon-only mode, hamburger mobile, ClienteDetalhe com timeline+compras+sparkline.', status: 'done', categoria: 'feature', sessao: '13/Abr/2026', detalhes: 'localStorage persist. Accordion sections. Score sparkline 40px.', commits: ['659c8a0'] },
  { id: 'S3-013', pedido: 'Kanban drag-drop + Busca Ctrl+K + Atalhos', descricao: 'Pipeline HTML5 DnD, swimlanes, busca global multi-fonte, atalhos N/A/C/I.', status: 'done', categoria: 'feature', sessao: '13/Abr/2026', detalhes: 'Optimistic update. Mobile bottom sheet. SearchModal debounce 300ms. useKeyboardShortcuts hook.', commits: ['7d030d6'] },
  { id: 'S3-014', pedido: 'Skeleton loading + ErrorBoundary + Performance', descricao: '8 variantes Skeleton. ErrorBoundary global. formatDateBR/formatNumber. Recharts tree-shake.', status: 'done', categoria: 'fix', sessao: '13/Abr/2026', detalhes: 'Skeleton.tsx reutilizável. ErrorBoundary class em layout.tsx. optimizePackageImports.', commits: ['25471ab'] },

  // ═══ PENDÊNCIAS RESTANTES ═══

  {
    id: 'P-001',
    pedido: 'LOG completo — 20.830 registros importados',
    descricao: 'DB agora tem 21.305 registros de LOG (475 originais + 20.830 importados).',
    status: 'done',
    categoria: 'data',
    sessao: '01/Abr/2026',
    detalhes: 'Script import_log_completo.py importou CONTROLE_FUNIL (10.434) + DESKRIO (4.240) + SINTETICO (6.156). 3-tier: REAL 13.360 + SINTETICO 7.470. DE-PARA normalizado. Idempotente.',
    commits: ['f5e0f2b'],
  },
  {
    id: 'P-002',
    pedido: 'Inbox — mídia (imagens, áudios, vídeos, docs)',
    descricao: 'MediaBubble renderiza imagens (lightbox), áudio (player), vídeo, documentos (download).',
    status: 'done',
    categoria: 'feature',
    sessao: '01/Abr/2026',
    detalhes: 'getMediaType detecta extensão + path patterns Deskrio. Lightbox fullscreen para imagens. Audio/video controls. Doc download link.',
    commits: ['e7ad64e'],
  },
  {
    id: 'P-003',
    pedido: 'Inbox — auto-polling 30s + refresh manual',
    descricao: 'Mensagens atualizam a cada 30s (pausa quando aba inativa). Botão refresh manual.',
    status: 'done',
    categoria: 'integration',
    sessao: '01/Abr/2026',
    detalhes: 'setInterval 30s com document.hidden check. Label "Atualizado há Xs" com ticker 10s. Botão refresh com spin animation.',
    commits: ['e7ad64e'],
  },
  {
    id: 'P-004',
    pedido: 'DAIANE — 1.054 prospects reclassificados',
    descricao: 'DAIANE: 1.164 → 193 clientes. 484 para MANU (Sul), 441 para LARISSA (resto), 129 mantidos (redes reais).',
    status: 'done',
    categoria: 'data',
    sessao: '01/Abr/2026',
    detalhes: '115 PROSPECT_REDE (BIOMUNDO, MUNDO VERDE, etc.) mantidos com DAIANE. 14 com faturamento mantidos. 484 UF Sul → MANU. 441 resto → LARISSA. 925 audit_logs. Idempotente.',
    commits: ['8aab2c1'],
  },
  {
    id: 'P-005',
    pedido: 'Banco de dados — Neon PostgreSQL mantido (decisão final)',
    descricao: 'Neon funciona perfeitamente. Supabase descartado — zero benefício para trocar.',
    status: 'done',
    categoria: 'infra',
    sessao: '01/Abr/2026',
    detalhes: 'Decisão: manter Neon PostgreSQL. Funciona, é estável, connection pooling OK. Supabase exigiria migração + nova config sem ganho real. DATABASE_URL segue inalterado.',
  },
  {
    id: 'P-007',
    pedido: '46 clientes DESCONHECIDO reclassificados',
    descricao: 'Todos os clientes sem consultor atribuídos: 38→LARISSA, 6→DAIANE (redes), 2→MANU (PR).',
    status: 'done',
    categoria: 'data',
    sessao: '01/Abr/2026',
    detalhes: 'Script fix_desconhecido.py. DE-PARA: PR/SC/RS→MANU, redes BIOMUNDO/MUNDO VERDE→DAIANE, resto→LARISSA. Distribuição final: LARISSA 646, MANU 644, DAIANE 199, JULIO 92. Zero DESCONHECIDO.',
    commits: ['pending'],
  },
  {
    id: 'P-008',
    pedido: 'seed_data.json atualizado com dados corrigidos',
    descricao: '16.5 MB — 1.581 clientes, 21.305 LOG, 1.231 vendas, 242 produtos, 92 regras motor.',
    status: 'done',
    categoria: 'data',
    sessao: '01/Abr/2026',
    detalhes: 'Regenerado após fix DESCONHECIDO + products import. Todas tabelas: clientes, vendas, metas, log_interacoes, redes, regras_motor, agenda_items, score_historico, produtos, usuarios.',
    commits: ['pending'],
  },
  {
    id: 'P-006',
    pedido: 'Catálogo de produtos — 242 produtos Mercos importados',
    descricao: '256 produtos extraídos do XLSX Mercos, 242 inseridos. 11 categorias, preço mediana.',
    status: 'done',
    categoria: 'data',
    sessao: '01/Abr/2026',
    detalhes: 'Fonte: Produtos por pedidos 2025.xlsx (11.883 linhas). Categorias: Açúcares(79), Outros(77), Biscoitos(31), Granolas(18), etc. Preço tabela = mediana, preço mínimo = min. Idempotente.',
    commits: ['8aab2c1'],
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
          CRM VITAO360 — Atualizado: 13/Abr/2026 — {ITEMS.length} itens rastreados
        </p>
      </div>
    </div>
  );
}
