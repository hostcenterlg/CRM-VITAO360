import React, { useState } from "react";

const TABS_DATA = [
  {
    id: 1, name: "README", type: "Documentação", color: "#6B7280",
    rows: 175, cols: 5, auto: true,
    desc: "Guia completo do CRM — 8 seções: estrutura, colunas DRAFT 2, funcionalidades, regras, consultores, versões, instruções IA, mapa de dropdowns",
    health: 95, status: "OPERACIONAL",
    blocks: ["Estrutura abas", "31 colunas DRAFT 2", "10 regras IA", "Mapa dropdowns"],
    issues: ["Referência 'REGRAS!B2:B13' desatualizada (agora 16 resultados)"],
    fixes: [],
    category: "GOVERNANÇA"
  },
  {
    id: 2, name: "STATUS", type: "Governança", color: "#7030A0",
    rows: 187, cols: 7, auto: false,
    desc: "Painel de controle do projeto — 11 seções: origem, métricas, equipe, fases F0-F8, viradas estruturais, dívidas técnicas, evolução, roadmap, regras imutáveis, log M-001→M-033, changelog",
    health: 100, status: "NOVO ✨",
    blocks: ["Origem (9 fatos)", "Métricas (13 KPIs)", "Equipe (4 consultores)", "Fases F0-F8", "5 viradas estruturais", "14 dívidas técnicas", "Evolução antes/depois", "Roadmap 5 fases", "12 regras imutáveis", "Log M-001→M-033", "Changelog"],
    issues: [],
    fixes: ["Criado hoje (13/FEV/2026)"],
    category: "GOVERNANÇA"
  },
  {
    id: 3, name: "DRAFT 1", type: "Base de dados", color: "#3B82F6",
    rows: 500, cols: 45, auto: true,
    desc: "Base cadastral — dados Mercos/SAP. Contém CNPJ, nome, UF, SITUAÇÃO, SINALEIRO, dias sem compra, ciclo médio. Alimenta DRAFT 2 via XLOOKUP",
    health: 85, status: "OPERACIONAL",
    blocks: ["CNPJ (chave)", "Identidade (nome, UF, email, tel)", "Status (SITUAÇÃO, PRIORIDADE)", "Compras (dias, ciclo, valor)", "E-commerce (acesso B2B)", "Vendas mês a mês", "Recorrência (ABC, ticket)"],
    issues: ["CNPJ pode ter formato misto (pontuado vs digits-only)", "493 clientes mas CARTEIRA tem 8.305 rows"],
    fixes: [],
    category: "DADOS"
  },
  {
    id: 4, name: "DRAFT 2", type: "Operacional", color: "#F59E0B",
    rows: 502, cols: 31, auto: false,
    desc: "Coração do CRM — registro diário de atendimentos. 31 colunas: 10 manuais + 21 automáticas. Motor de Regras (SITUAÇÃO × RESULTADO → FASE + AÇÃO)",
    health: 90, status: "CORRIGIDO ✅",
    blocks: ["Data + Consultor (manual)", "CNPJ → XLOOKUPs (auto)", "Canais (WhatsApp, Ligação)", "RESULTADO (16 valores)", "Motor de Regras (auto)", "AÇÃO FUTURA (corrigida)", "TEMPERATURA (4 níveis)", "TIPO AÇÃO (6 valores)", "TIPO PROBLEMA RNC (8)", "DEMANDA (25 atividades)"],
    issues: ["Referências Motor $221:$283 — verificar se recalcula no Excel"],
    fixes: ["Fórmulas U+T+I+K+Y atualizadas (2.260 cells)", "AÇÃO FUTURA agora retorna ações concretas"],
    category: "OPERACIONAL"
  },
  {
    id: 5, name: "DRAFT 3", type: "Histórico", color: "#8B5CF6",
    rows: 1526, cols: 16, auto: true,
    desc: "Histórico consolidado de atendimentos passados — ETL automático do Mercos. Base para análises retroativas e validação de dados",
    health: 75, status: "OPERACIONAL",
    blocks: ["SAP CNPJ", "Razão Social", "Status SAP", "Atendimento", "Bloqueio"],
    issues: ["1.526 registros vs 10.634 interações documentadas — cobertura parcial", "Sem validação cruzada com DRAFT 2"],
    fixes: [],
    category: "DADOS"
  },
  {
    id: 6, name: "PROJEÇÃO", type: "Estratégico", color: "#EC4899",
    rows: 504, cols: 80, auto: false,
    desc: "Metas e projeções de venda por consultor/mês — integração SAP + SINALEIRO de atingimento por rede de franquia",
    health: 70, status: "PARCIAL ⚠️",
    blocks: ["Identificação cliente", "SINALEIRO REDE", "META MENSAL (SAP)", "REAL vs META %", "Projeção 2026"],
    issues: ["80 colunas — complexidade alta", "SINALEIRO depende de REDES_FRANQUIAS_v2 (#REF!)", "CNPJ formato incerto"],
    fixes: [],
    category: "ESTRATÉGICO"
  },
  {
    id: 7, name: "LOG", type: "Financeiro", color: "#2563EB",
    rows: 9, cols: 24, auto: true,
    desc: "Registro de vendas e faturamento real — dados SAP. Two-Base Architecture: SOMENTE valores financeiros aqui, NUNCA interações",
    health: 40, status: "SUBUTILIZADO ⚠️",
    blocks: ["DATA", "CONSULTOR", "NOME FANTASIA", "CNPJ", "UF", "REDE", "Valores financeiros"],
    issues: ["Apenas 9 rows com dados — deveria ter 957 vendas de 2025", "Estrutura existe mas alimentação está incompleta", "Two-Base Architecture depende desta aba funcionar"],
    fixes: [],
    category: "FINANCEIRO"
  },
  {
    id: 8, name: "CARTEIRA", type: "Base mestre", color: "#92D050",
    rows: 8305, cols: 263, auto: true,
    desc: "Carteira detalhada — 46 colunas IMUTÁVEIS (layout nunca alterar). Organizada em 7 blocos: Âncora, Identidade, Rede, Equipe, Status, Compra, E-commerce, Vendas, Recorrência, Pipeline",
    health: 80, status: "OPERACIONAL",
    blocks: ["🟣 ÂNCORA (nome fantasia)", "IDENTIDADE (CNPJ, razão, UF, email, tel)", "REDE (regional, tipo cliente)", "EQUIPE (consultor, vendedor)", "STATUS (SITUAÇÃO, prioridade)", "COMPRA (dias, data, valor, ciclo)", "E-COMMERCE (acesso B2B, carrinho)", "VENDAS (mês a mês MAR-JAN)", "RECORRÊNCIA (ABC, ticket, média)", "PIPELINE (followup, último atend.)"],
    issues: ["8.305 rows × 263 cols — muito além das 46 colunas imutáveis", "Formato CNPJ pode ser misto", "Colunas 47-263 são dados expandidos de vendas mensais"],
    fixes: [],
    category: "DADOS"
  },
  {
    id: 9, name: "AGENDA", type: "Operacional", color: "#2563EB",
    rows: 5000, cols: 30, auto: false,
    desc: "Agenda diária do consultor — tarefas priorizadas por score. AÇÃO SUGERIDA automática baseada no RESULTADO do último atendimento",
    health: 92, status: "CORRIGIDO ✅",
    blocks: ["Priorização automática", "AÇÃO SUGERIDA (16 resultados)", "FOLLOW-UP calculado", "Score de urgência"],
    issues: ["5.000 rows pré-alocadas — verificar performance"],
    fixes: ["Fórmula W reescrita: +NUTRIÇÃO, CS corrigido, SUPORTE corrigido, RELACIONAMENTO corrigido", "VLOOKUP range atualizado $B$6:$C$21"],
    category: "OPERACIONAL"
  },
  {
    id: 10, name: "RNC", type: "Qualidade", color: "#EF4444",
    rows: 526, cols: 12, auto: false,
    desc: "Registro de Não Conformidades — problemas de OUTRAS áreas (logística, financeiro, TI) resolvidos pelo comercial. 8 categorias + área responsável",
    health: 85, status: "OPERACIONAL",
    blocks: ["Data abertura", "CNPJ + Cliente", "Consultor", "TIPO PROBLEMA (8 categorias)", "ÁREA RESPONSÁVEL (7 áreas)", "STATUS (5 estados)", "IMPACTO (4 níveis)"],
    issues: ["Sem integração automática com DRAFT 2 (duplicação manual)", "822 ocorrências de cobrança indevida não estão aqui"],
    fixes: [],
    category: "QUALIDADE"
  },
  {
    id: 11, name: "DASH", type: "Gerencial", color: "#2F5496",
    rows: 74, cols: 18, auto: true,
    desc: "Dashboard de indicadores — 6 blocos: KPIs globais, Tipo Contato × Resultado, Canais + Funil, Motivos, Performance consultor, Temperatura + Tipo Ação + Demanda",
    health: 88, status: "OPERACIONAL",
    blocks: ["KPIs: Atendimentos, Vendas, Conversão, Orçamentos, Quentes, Frios", "Matriz TIPO CONTATO × RESULTADO (7×12)", "Canais: WhatsApp, Ligação, Atendida", "Funil: Negociação → Orçamento → Cadastro → Venda", "Motivos não-compra (10 categorias)", "Performance por consultor (4)", "Temperatura (4 níveis)", "Tipo Ação × Consultor (6×4)", "Demanda (25 atividades)"],
    issues: ["Blocos novos (Temperatura, Tipo Ação, Demanda) mostram zeros — normal, precisa de dados"],
    fixes: [],
    category: "GERENCIAL"
  },
  {
    id: 12, name: "REGRAS", type: "Motor", color: "#0D9488",
    rows: 283, cols: 13, auto: true,
    desc: "Motor de regras central — 17 seções: RESULTADO (16), TIPO CONTATO (7), MOTIVO (22), SITUAÇÃO (7), FASE (9), dropdowns, Motor de Regras (63 combinações SITUAÇÃO×RESULTADO)",
    health: 92, status: "CORRIGIDO ✅",
    blocks: ["Seção 1: RESULTADO (16 valores)", "Seção 2-12: Dropdowns e listas", "Seção 13: AÇÃO FUTURA (22 ações)", "Seção 14-16: Tipos e classificações", "Seção 17: Motor de Regras (63 linhas)"],
    issues: ["Validação dropdown README desatualizada (referencia 12 resultados, agora são 16)"],
    fixes: ["CS FU 15→30 dias", "+NUTRIÇÃO como resultado #7", "+4 ações (#19-22)", "Motor col F: 61 linhas reescritas com ações concretas"],
    category: "MOTOR"
  },
  {
    id: 13, name: "Claude Log", type: "Auditoria", color: "#6B7280",
    rows: 72, cols: 6, auto: true,
    desc: "Registro de todas alterações feitas pela IA — Turn #, Data, Request, Action, Details, Outcome. Rastreabilidade 100%",
    health: 100, status: "OPERACIONAL",
    blocks: ["Turn # sequencial", "Data", "User Request", "Action Taken", "Details", "Outcome"],
    issues: [],
    fixes: [],
    category: "GOVERNANÇA"
  }
];

const PENDING_DEBTS = [
  { id: "DT-01", name: "#REF! SINALEIRO REDES", severity: "CRÍTICA", effort: "4-8h", impact: "PROJEÇÃO + REDES_FRANQUIAS_v2 quebrados", next: "Conversa dedicada" },
  { id: "DT-02", name: "Julio fora do Deskrio", severity: "CRÍTICA", effort: "Externo", impact: "Interações invisíveis ao sistema", next: "Decisão gestão" },
  { id: "DT-03", name: "Cobertura licença Manu", severity: "CRÍTICA", effort: "Planejamento", impact: "SC/PR/RS sem consultor", next: "Plano de contingência" },
  { id: "DT-04", name: "Backup automático", severity: "CRÍTICA", effort: "2h", impact: "Risco de perda total", next: "OneDrive/Google Drive sync" },
  { id: "DT-05", name: "CNPJ digits-only global", severity: "ALTA", effort: "2-4h", impact: "VLOOKUPs #N/A silenciosos", next: "Find-replace global" },
  { id: "DT-06", name: "LOG subutilizado (9 rows)", severity: "ALTA", effort: "4h", impact: "Two-Base Architecture incompleta", next: "Popular com 957 vendas SAP" },
  { id: "DT-07", name: "README dropdowns desatualizado", severity: "MÉDIA", effort: "30min", impact: "Instrução incorreta para IA", next: "Atualizar seção 8" },
  { id: "DT-08", name: "DRAFT 3 cobertura parcial", severity: "MÉDIA", effort: "2h", impact: "Histórico incompleto", next: "ETL completo Mercos" },
];

const CATEGORIES = {
  "GOVERNANÇA": { icon: "🏛️", color: "#7030A0" },
  "DADOS": { icon: "🗄️", color: "#3B82F6" },
  "OPERACIONAL": { icon: "⚡", color: "#F59E0B" },
  "ESTRATÉGICO": { icon: "🎯", color: "#EC4899" },
  "FINANCEIRO": { icon: "💰", color: "#2563EB" },
  "QUALIDADE": { icon: "🛡️", color: "#EF4444" },
  "GERENCIAL": { icon: "📊", color: "#2F5496" },
  "MOTOR": { icon: "⚙️", color: "#0D9488" },
};

function HealthBar({ value, size = "normal" }) {
  const color = value >= 90 ? "#22C55E" : value >= 70 ? "#F59E0B" : value >= 50 ? "#F97316" : "#EF4444";
  const h = size === "small" ? "h-1.5" : "h-2.5";
  return (
    <div className={`w-full bg-gray-200 rounded-full ${h}`}>
      <div className={`${h} rounded-full transition-all duration-500`} style={{ width: `${value}%`, backgroundColor: color }} />
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    "OPERACIONAL": "bg-green-100 text-green-800 border-green-300",
    "CORRIGIDO ✅": "bg-blue-100 text-blue-800 border-blue-300",
    "NOVO ✨": "bg-purple-100 text-purple-800 border-purple-300",
    "PARCIAL ⚠️": "bg-yellow-100 text-yellow-800 border-yellow-300",
    "SUBUTILIZADO ⚠️": "bg-orange-100 text-orange-800 border-orange-300",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${colors[status] || "bg-gray-100 text-gray-700"}`}>
      {status}
    </span>
  );
}

export default function RaioXCRM() {
  const [view, setView] = useState("overview");
  const [selectedTab, setSelectedTab] = useState(null);
  const [showOption, setShowOption] = useState("A");

  const avgHealth = Math.round(TABS_DATA.reduce((a, t) => a + t.health, 0) / TABS_DATA.length);
  const totalFixes = TABS_DATA.reduce((a, t) => a + t.fixes.length, 0);
  const totalIssues = TABS_DATA.reduce((a, t) => a + t.issues.length, 0);
  const criticalDebts = PENDING_DEBTS.filter(d => d.severity === "CRÍTICA").length;

  return (
    <div style={{ fontFamily: "'DM Sans', 'Segoe UI', sans-serif" }} className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet" />

      {/* Header */}
      <div className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg flex items-center justify-center text-white font-bold text-sm" style={{ background: "linear-gradient(135deg, #0D9488, #2563EB)" }}>V11</div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">RAIO-X — CRM VITAO 360</h1>
                  <p className="text-xs text-gray-500">13 abas · 16.492 rows · 583 colunas · Auditoria 13/FEV/2026</p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-center px-3 py-1 rounded-lg bg-gray-50">
                <div className="text-2xl font-bold" style={{ color: avgHealth >= 80 ? "#22C55E" : "#F59E0B" }}>{avgHealth}%</div>
                <div className="text-xs text-gray-500">saúde média</div>
              </div>
            </div>
          </div>

          <div className="flex gap-1 mt-3 overflow-x-auto pb-1">
            {[
              { id: "overview", label: "📋 Visão Geral", desc: "13 abas" },
              { id: "detail", label: "🔍 Detalhamento", desc: "por aba" },
              { id: "fixed", label: "✅ O que Corrigimos", desc: "hoje" },
              { id: "debts", label: "🚨 Pendências", desc: `${PENDING_DEBTS.length} itens` },
              { id: "committee", label: "🏛️ Comitê", desc: "decisão" },
            ].map(v => (
              <button key={v.id} onClick={() => setView(v.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap ${
                  view === v.id ? "bg-gray-900 text-white shadow-md" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}>
                {v.label} <span className="text-xs opacity-60">{v.desc}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-6">

        {/* ===== VISÃO GERAL ===== */}
        {view === "overview" && (
          <div>
            {/* KPI Cards */}
            <div className="grid grid-cols-2 gap-3 mb-6" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))" }}>
              {[
                { label: "Abas", value: "13", sub: "3 novas/corrigidas", color: "#2563EB" },
                { label: "Rows", value: "16.5K", sub: "dados + fórmulas", color: "#0D9488" },
                { label: "Correções Hoje", value: totalFixes, sub: "aplicadas", color: "#22C55E" },
                { label: "Pendências", value: totalIssues, sub: `${criticalDebts} críticas`, color: "#EF4444" },
                { label: "Nota Auditoria", value: "7.8", sub: "era 7.3", color: "#7030A0" },
                { label: "Meta", value: "9+", sub: "resolver DTs", color: "#F59E0B" },
              ].map((k, i) => (
                <div key={i} className="bg-white rounded-xl border p-4 shadow-sm">
                  <div className="text-xs font-medium text-gray-500 mb-1">{k.label}</div>
                  <div className="text-2xl font-bold" style={{ color: k.color }}>{k.value}</div>
                  <div className="text-xs text-gray-400">{k.sub}</div>
                </div>
              ))}
            </div>

            {/* Tab Grid */}
            <h2 className="font-bold text-gray-800 mb-3">Estrutura Completa — 13 Abas</h2>
            <div className="grid gap-3" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))" }}>
              {TABS_DATA.map(tab => {
                const cat = CATEGORIES[tab.category];
                return (
                  <div key={tab.id}
                    onClick={() => { setSelectedTab(tab); setView("detail"); }}
                    className="bg-white rounded-xl border p-4 cursor-pointer hover:shadow-md hover:border-gray-300 transition-all group">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-xs font-bold"
                          style={{ backgroundColor: tab.color }}>
                          {tab.id}
                        </div>
                        <div>
                          <div className="font-bold text-gray-800 text-sm group-hover:text-blue-700 transition-colors">{tab.name}</div>
                          <div className="text-xs text-gray-400">{tab.rows.toLocaleString()}r × {tab.cols}c</div>
                        </div>
                      </div>
                      <StatusBadge status={tab.status} />
                    </div>
                    <p className="text-xs text-gray-500 mb-2 line-clamp-2" style={{ display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                      {tab.desc}
                    </p>
                    <div className="flex items-center gap-2">
                      <HealthBar value={tab.health} size="small" />
                      <span className="text-xs font-medium text-gray-600 whitespace-nowrap">{tab.health}%</span>
                    </div>
                    {(tab.fixes.length > 0 || tab.issues.length > 0) && (
                      <div className="flex gap-2 mt-2">
                        {tab.fixes.length > 0 && <span className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded">✅ {tab.fixes.length} fix</span>}
                        {tab.issues.length > 0 && <span className="text-xs bg-red-50 text-red-700 px-2 py-0.5 rounded">⚠️ {tab.issues.length} pendência</span>}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Category Legend */}
            <div className="flex flex-wrap gap-2 mt-4">
              {Object.entries(CATEGORIES).map(([name, { icon, color }]) => (
                <span key={name} className="text-xs px-2 py-1 rounded-full border bg-white" style={{ borderColor: color, color }}>
                  {icon} {name}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ===== DETALHAMENTO ===== */}
        {view === "detail" && (
          <div>
            <div className="flex flex-wrap gap-1 mb-4">
              {TABS_DATA.map(t => (
                <button key={t.id} onClick={() => setSelectedTab(t)}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                    selectedTab?.id === t.id ? "text-white shadow-md" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}
                  style={selectedTab?.id === t.id ? { backgroundColor: t.color } : {}}>
                  {t.id}. {t.name}
                </button>
              ))}
            </div>

            {selectedTab ? (
              <div className="bg-white rounded-xl border shadow-sm overflow-hidden">
                <div className="p-6 border-b" style={{ borderBottomColor: selectedTab.color + "40" }}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 rounded-xl flex items-center justify-center text-white text-lg font-bold"
                        style={{ backgroundColor: selectedTab.color }}>
                        {selectedTab.id}
                      </div>
                      <div>
                        <h2 className="text-xl font-bold text-gray-900">{selectedTab.name}</h2>
                        <p className="text-sm text-gray-500">{selectedTab.type} · {selectedTab.rows.toLocaleString()} rows × {selectedTab.cols} cols · {selectedTab.auto ? "Automático" : "Manual + Fórmulas"}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-3xl font-bold" style={{ color: selectedTab.health >= 90 ? "#22C55E" : selectedTab.health >= 70 ? "#F59E0B" : "#EF4444" }}>
                        {selectedTab.health}%
                      </div>
                      <StatusBadge status={selectedTab.status} />
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mt-3">{selectedTab.desc}</p>
                  <HealthBar value={selectedTab.health} />
                </div>

                <div className="grid grid-cols-1 gap-0 divide-y" style={{ gridTemplateColumns: selectedTab.fixes.length > 0 || selectedTab.issues.length > 0 ? "1fr 1fr" : "1fr" }}>
                  <div className="p-5">
                    <h3 className="font-bold text-sm text-gray-700 mb-3">📦 Blocos de Dados ({selectedTab.blocks.length})</h3>
                    <div className="flex flex-wrap gap-1.5">
                      {selectedTab.blocks.map((b, i) => (
                        <span key={i} className="text-xs px-2.5 py-1 rounded-full border bg-gray-50 text-gray-700">{b}</span>
                      ))}
                    </div>
                  </div>

                  {selectedTab.fixes.length > 0 && (
                    <div className="p-5 bg-green-50">
                      <h3 className="font-bold text-sm text-green-800 mb-2">✅ Corrigido Hoje ({selectedTab.fixes.length})</h3>
                      {selectedTab.fixes.map((f, i) => (
                        <div key={i} className="text-sm text-green-700 flex items-start gap-2 mb-1">
                          <span className="mt-0.5">•</span>{f}
                        </div>
                      ))}
                    </div>
                  )}

                  {selectedTab.issues.length > 0 && (
                    <div className="p-5 bg-red-50">
                      <h3 className="font-bold text-sm text-red-800 mb-2">⚠️ Pendências ({selectedTab.issues.length})</h3>
                      {selectedTab.issues.map((f, i) => (
                        <div key={i} className="text-sm text-red-700 flex items-start gap-2 mb-1">
                          <span className="mt-0.5">•</span>{f}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-white rounded-xl border p-12 text-center text-gray-400">
                Clique em uma aba acima para ver o detalhamento
              </div>
            )}
          </div>
        )}

        {/* ===== O QUE CORRIGIMOS ===== */}
        {view === "fixed" && (
          <div>
            <div className="bg-white rounded-xl border p-6 mb-4">
              <h2 className="text-lg font-bold text-gray-800 mb-1">Correções Aplicadas — 13/FEV/2026</h2>
              <p className="text-sm text-gray-500">Sessão de auditoria + correção de inconsistências RESULTADO → AÇÃO SUGERIDA</p>
            </div>

            <div className="space-y-4">
              {[
                {
                  title: "1. Aba STATUS criada (NOVA)",
                  target: "STATUS",
                  color: "#7030A0",
                  items: [
                    "11 seções de documentação do projeto inteiro",
                    "Origem, métricas (13 KPIs), equipe, fases F0-F8",
                    "Log de 33 modificações (M-001 → M-033) com ANTES/DEPOIS",
                    "14 dívidas técnicas priorizadas",
                    "Roadmap de 5 fases até SaaS",
                    "12 regras imutáveis",
                    "187 rows, 7 colunas"
                  ]
                },
                {
                  title: "2. REGRAS Seção 1 — Lista RESULTADO corrigida",
                  target: "REGRAS",
                  color: "#0D9488",
                  items: [
                    "CS (SUCESSO DO CLIENTE): follow-up 15 → 30 dias",
                    "NUTRIÇÃO adicionado como resultado #7 (não existia!)",
                    "RELACIONAMENTO reposicionado como resultado separado",
                    "Total: 15 → 16 resultados válidos"
                  ]
                },
                {
                  title: "3. REGRAS Seção 13 — 4 novas AÇÕES FUTURAS",
                  target: "REGRAS",
                  color: "#0D9488",
                  items: [
                    "#19: VERIFICAR SELL OUT E CRIAR INTENÇÃO RECOMPRA (para CS)",
                    "#20: NUTRIR ENVIANDO CAMPANHAS, PROMOÇÕES E NOVIDADES (para NUTRIÇÃO)",
                    "#21: RESOLVER PROBLEMA INTERNO E ENVIAR SOLUÇÃO (para SUPORTE)",
                    "#22: RAPPORT COM CLIENTE APÓS A VENDA ATÉ RECOMPRAR (para RELACIONAMENTO)",
                    "Total: 18 → 22 ações cadastradas"
                  ]
                },
                {
                  title: "4. Motor de Regras — 61 linhas reescritas",
                  target: "REGRAS",
                  color: "#0D9488",
                  items: [
                    "Coluna AÇÃO FUTURA usava nomes de FASE genéricos (RECOMPRA, SALVAMENTO...)",
                    "Substituídas por ações concretas (FECHAR NEGOCIAÇÃO, CONFIRMAR ORÇAMENTO...)",
                    "DRAFT 2 agora retorna ações úteis via INDEX/MATCH",
                    "61 de 64 linhas alteradas"
                  ]
                },
                {
                  title: "5. AGENDA fórmula AÇÃO SUGERIDA — 4 correções",
                  target: "AGENDA",
                  color: "#2563EB",
                  items: [
                    "NUTRIÇÃO: vazio → NUTRIR ENVIANDO CAMPANHAS, PROMOÇÕES E NOVIDADES",
                    "CS: COBRAR RETORNO → VERIFICAR SELL OUT E CRIAR INTENÇÃO RECOMPRA",
                    "SUPORTE: COBRAR RETORNO → RESOLVER PROBLEMA INTERNO E ENVIAR SOLUÇÃO",
                    "RELACIONAMENTO: NUTRIR/NOVO CONTATO → RAPPORT COM CLIENTE APÓS A VENDA",
                    "4.996 linhas atualizadas"
                  ]
                },
                {
                  title: "6. DRAFT 2 — Referências atualizadas",
                  target: "DRAFT 2",
                  color: "#F59E0B",
                  items: [
                    "Colunas T, U, I, K, Y: ranges $220:$282 → $221:$283",
                    "VLOOKUP ranges $B$6:$C$20 → $B$6:$C$21",
                    "2.260 células corrigidas em 500 rows",
                    "Fórmulas verificadas: parênteses balanceados, 0 referências quebradas"
                  ]
                },
              ].map((fix, i) => (
                <div key={i} className="bg-white rounded-xl border overflow-hidden">
                  <div className="px-5 py-3 border-b flex items-center gap-3" style={{ borderLeftWidth: 4, borderLeftColor: fix.color }}>
                    <h3 className="font-bold text-gray-800 text-sm">{fix.title}</h3>
                    <span className="text-xs px-2 py-0.5 rounded text-white" style={{ backgroundColor: fix.color }}>{fix.target}</span>
                  </div>
                  <div className="px-5 py-3">
                    {fix.items.map((item, j) => (
                      <div key={j} className="text-sm text-gray-700 flex items-start gap-2 py-0.5">
                        <span className="text-green-500 mt-0.5 flex-shrink-0">✓</span>{item}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ===== PENDÊNCIAS ===== */}
        {view === "debts" && (
          <div>
            <div className="bg-white rounded-xl border p-6 mb-4">
              <h2 className="text-lg font-bold text-gray-800 mb-1">Dívidas Técnicas Pendentes</h2>
              <p className="text-sm text-gray-500">
                {criticalDebts} críticas · {PENDING_DEBTS.filter(d => d.severity === "ALTA").length} altas · {PENDING_DEBTS.filter(d => d.severity === "MÉDIA").length} médias
              </p>
              <div className="flex gap-2 mt-3">
                <div className="flex-1 bg-red-50 rounded-lg p-3 text-center border border-red-200">
                  <div className="text-2xl font-bold text-red-600">{criticalDebts}</div>
                  <div className="text-xs text-red-500">CRÍTICAS</div>
                </div>
                <div className="flex-1 bg-yellow-50 rounded-lg p-3 text-center border border-yellow-200">
                  <div className="text-2xl font-bold text-yellow-600">{PENDING_DEBTS.filter(d => d.severity === "ALTA").length}</div>
                  <div className="text-xs text-yellow-500">ALTAS</div>
                </div>
                <div className="flex-1 bg-blue-50 rounded-lg p-3 text-center border border-blue-200">
                  <div className="text-2xl font-bold text-blue-600">{PENDING_DEBTS.filter(d => d.severity === "MÉDIA").length}</div>
                  <div className="text-xs text-blue-500">MÉDIAS</div>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              {PENDING_DEBTS.map((d, i) => {
                const sevColor = d.severity === "CRÍTICA" ? "#EF4444" : d.severity === "ALTA" ? "#F59E0B" : "#3B82F6";
                return (
                  <div key={i} className="bg-white rounded-xl border overflow-hidden" style={{ borderLeftWidth: 4, borderLeftColor: sevColor }}>
                    <div className="p-4">
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs px-2 py-0.5 rounded text-white font-bold" style={{ backgroundColor: sevColor }}>{d.severity}</span>
                          <span className="font-bold text-gray-800 text-sm">{d.id}: {d.name}</span>
                        </div>
                        <span className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600">⏱ {d.effort}</span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">Impacto: {d.impact}</p>
                      <div className="text-sm font-medium" style={{ color: sevColor }}>→ {d.next}</div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ===== COMITÊ ===== */}
        {view === "committee" && (
          <div>
            <div className="bg-white rounded-xl border p-6 mb-6">
              <h2 className="text-lg font-bold text-gray-800 mb-1">Decisão para o Comitê</h2>
              <p className="text-sm text-gray-500">Como apresentar as mudanças: manter original e adicionar, ou reorganizar?</p>
            </div>

            <div className="flex gap-2 mb-4">
              {[
                { id: "A", label: "Opção A: Manter + Adicionar", emoji: "➕" },
                { id: "B", label: "Opção B: Reorganizar", emoji: "🔄" },
                { id: "C", label: "Comparação", emoji: "⚖️" },
              ].map(o => (
                <button key={o.id} onClick={() => setShowOption(o.id)}
                  className={`flex-1 px-4 py-3 rounded-xl text-sm font-medium transition-all border ${
                    showOption === o.id ? "bg-gray-900 text-white border-gray-900 shadow-lg" : "bg-white text-gray-600 hover:bg-gray-50"}`}>
                  {o.emoji} {o.label}
                </button>
              ))}
            </div>

            {showOption === "A" && (
              <div className="space-y-4">
                <div className="bg-green-50 rounded-xl border border-green-200 p-5">
                  <h3 className="font-bold text-green-800 mb-2">✅ OPÇÃO A: Manter estrutura original + Adicionar novas abas</h3>
                  <p className="text-sm text-green-700 mb-4">Menor risco. As 13 abas atuais ficam intactas. Melhorias entram como abas ADICIONAIS.</p>

                  <div className="bg-white rounded-lg p-4 mb-3">
                    <h4 className="font-bold text-sm text-gray-700 mb-2">Abas existentes (sem mudança visual):</h4>
                    <div className="flex flex-wrap gap-1.5">
                      {TABS_DATA.map(t => (
                        <span key={t.id} className="text-xs px-2 py-1 rounded border bg-gray-50 text-gray-600">
                          {t.id}. {t.name} {t.fixes.length > 0 ? "🔧" : ""}
                        </span>
                      ))}
                    </div>
                    <p className="text-xs text-gray-500 mt-2">🔧 = correções internas nas fórmulas (invisível para o usuário)</p>
                  </div>

                  <div className="bg-white rounded-lg p-4">
                    <h4 className="font-bold text-sm text-gray-700 mb-2">Novas abas propostas:</h4>
                    {[
                      { name: "MEGA CRUZAMENTO", desc: "Cruzamento 6 fontes unificado — visão 360° por CNPJ", status: "DEFINIÇÃO" },
                      { name: "ALERTAS", desc: "45/60/90 dias sem compra — triggers automáticos para o time", status: "CONSTRUÇÃO" },
                      { name: "BACKUP LOG", desc: "Registro automático de versões com data/hora/alteração", status: "DEFINIÇÃO" },
                    ].map((n, i) => (
                      <div key={i} className="flex items-center justify-between py-2 border-b last:border-0">
                        <div>
                          <span className="font-medium text-sm text-gray-800">{n.name}</span>
                          <span className="text-xs text-gray-500 ml-2">{n.desc}</span>
                        </div>
                        <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded">{n.status}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="bg-white rounded-xl border p-4">
                  <h4 className="font-bold text-sm mb-2">Prós e Contras:</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-green-700 font-medium text-xs mb-1">PRÓS</div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>• Zero risco de quebrar o que funciona</div>
                        <div>• Time não precisa reaprender nada</div>
                        <div>• Correções invisíveis (fórmulas internas)</div>
                        <div>• Rollback fácil: deleta aba nova e pronto</div>
                      </div>
                    </div>
                    <div>
                      <div className="text-red-700 font-medium text-xs mb-1">CONTRAS</div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>• Arquivo fica mais pesado (mais abas)</div>
                        <div>• Duplicação potencial (MEGA × CARTEIRA)</div>
                        <div>• Sem oportunidade de limpar estrutura</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {showOption === "B" && (
              <div className="space-y-4">
                <div className="bg-yellow-50 rounded-xl border border-yellow-200 p-5">
                  <h3 className="font-bold text-yellow-800 mb-2">🔄 OPÇÃO B: Reorganizar estrutura</h3>
                  <p className="text-sm text-yellow-700 mb-4">Maior impacto. Reorganiza abas por função, elimina subutilizadas, integra novas funcionalidades.</p>

                  <div className="bg-white rounded-lg p-4 mb-3">
                    <h4 className="font-bold text-sm text-gray-700 mb-2">Estrutura proposta (15 abas, reordenadas):</h4>
                    <div className="space-y-2">
                      {[
                        { num: "1", name: "README", change: "MANTÉM", color: "#22C55E", note: "Atualizar referências" },
                        { num: "2", name: "STATUS", change: "MANTÉM", color: "#22C55E", note: "Novo (criado hoje)" },
                        { num: "3", name: "CARTEIRA", change: "⬆️ PROMOVIDO", color: "#F59E0B", note: "Base mestre sobe para posição 3 (antes era 8)" },
                        { num: "4", name: "DRAFT 1", change: "⬇️ RENOMEAR", color: "#F59E0B", note: "→ 'CADASTRO MERCOS' (nome mais claro)" },
                        { num: "5", name: "DRAFT 2", change: "⬇️ RENOMEAR", color: "#F59E0B", note: "→ 'ATENDIMENTOS' (o time já chama assim)" },
                        { num: "6", name: "AGENDA", change: "MANTÉM", color: "#22C55E", note: "Corrigida hoje" },
                        { num: "7", name: "PROJEÇÃO", change: "MANTÉM", color: "#22C55E", note: "Corrigir SINALEIRO" },
                        { num: "8", name: "DASH", change: "MANTÉM", color: "#22C55E", note: "Automático" },
                        { num: "9", name: "RNC", change: "MANTÉM", color: "#22C55E", note: "Qualidade" },
                        { num: "10", name: "LOG", change: "🔧 POPULAR", color: "#EF4444", note: "Precisa das 957 vendas (hoje só 9 rows)" },
                        { num: "11", name: "MEGA CRUZAMENTO", change: "🆕 NOVA", color: "#7030A0", note: "Cruzamento 6 fontes unificado" },
                        { num: "12", name: "ALERTAS", change: "🆕 NOVA", color: "#7030A0", note: "45/60/90 dias triggers" },
                        { num: "13", name: "REGRAS", change: "MANTÉM", color: "#22C55E", note: "Motor (corrigido hoje)" },
                        { num: "14", name: "Claude Log", change: "MANTÉM", color: "#22C55E", note: "Auditoria" },
                        { num: "—", name: "DRAFT 3", change: "❌ ABSORVIDO", color: "#EF4444", note: "Dados migram para LOG + MEGA" },
                      ].map((t, i) => (
                        <div key={i} className="flex items-center gap-3 py-1.5 border-b last:border-0">
                          <span className="text-xs font-mono w-6 text-gray-400 text-right">{t.num}</span>
                          <span className="font-bold text-sm text-gray-800 w-40">{t.name}</span>
                          <span className="text-xs px-2 py-0.5 rounded text-white flex-shrink-0" style={{ backgroundColor: t.color }}>{t.change}</span>
                          <span className="text-xs text-gray-500 flex-1">{t.note}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="bg-white rounded-xl border p-4">
                  <h4 className="font-bold text-sm mb-2">Prós e Contras:</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-green-700 font-medium text-xs mb-1">PRÓS</div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>• Nomes intuitivos (ATENDIMENTOS vs DRAFT 2)</div>
                        <div>• Base mestre (CARTEIRA) em posição de destaque</div>
                        <div>• DRAFT 3 eliminado (reduz confusão)</div>
                        <div>• Estrutura mais profissional para apresentar</div>
                      </div>
                    </div>
                    <div>
                      <div className="text-red-700 font-medium text-xs mb-1">CONTRAS</div>
                      <div className="text-sm text-gray-600 space-y-1">
                        <div>• RISCO: fórmulas entre abas podem quebrar</div>
                        <div>• Time precisa reaprender posição das abas</div>
                        <div>• Documentação toda precisa ser refeita</div>
                        <div>• Renomear abas invalida Named Ranges</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {showOption === "C" && (
              <div>
                <div className="bg-white rounded-xl border overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-gray-800 text-white">
                        <th className="px-4 py-3 text-left">Critério</th>
                        <th className="px-4 py-3 text-center">Opção A (Adicionar)</th>
                        <th className="px-4 py-3 text-center">Opção B (Reorganizar)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {[
                        { criteria: "Risco de quebrar", a: "🟢 Zero", b: "🔴 Alto" },
                        { criteria: "Impacto visual", a: "🟡 Baixo", b: "🟢 Alto" },
                        { criteria: "Curva de aprendizado", a: "🟢 Nenhuma", b: "🟡 Média" },
                        { criteria: "Limpeza estrutural", a: "🔴 Não", b: "🟢 Sim" },
                        { criteria: "Tempo de implementação", a: "🟢 1-2h", b: "🔴 8-16h" },
                        { criteria: "Compatibilidade fórmulas", a: "🟢 100%", b: "🟡 Precisa testar" },
                        { criteria: "Apresentação para comitê", a: "🟡 Incremental", b: "🟢 Profissional" },
                        { criteria: "Reversibilidade", a: "🟢 Fácil", b: "🔴 Difícil" },
                        { criteria: "Preparação para DB", a: "🟡 Parcial", b: "🟢 Melhor base" },
                      ].map((row, i) => (
                        <tr key={i} className={i % 2 === 0 ? "bg-gray-50" : ""}>
                          <td className="px-4 py-2 font-medium text-gray-700">{row.criteria}</td>
                          <td className="px-4 py-2 text-center">{row.a}</td>
                          <td className="px-4 py-2 text-center">{row.b}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 bg-blue-50 rounded-xl border border-blue-200 p-5">
                  <h3 className="font-bold text-blue-800 mb-2">💡 Recomendação Técnica</h3>
                  <p className="text-sm text-blue-700 mb-3">
                    <strong>Opção A agora, Opção B quando migrar para banco de dados.</strong>
                  </p>
                  <p className="text-sm text-gray-600">
                    O CRM tem 16 meses de construção com fórmulas interdependentes. Reorganizar no Excel
                    é arriscado e o benefício é temporário — quando migrar para Supabase/PostgreSQL (Roadmap Fase 4),
                    a estrutura será redesenhada de qualquer forma. Melhor investir energia nas correções do
                    SINALEIRO (#REF!), popular o LOG com as 957 vendas, e padronizar CNPJ globalmente.
                    Isso sobe a nota de 7.8 para 9+ sem risco.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
