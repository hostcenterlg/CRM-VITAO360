import React, { useState } from "react";

const TC = ["PROSPECÇÃO","NEGOCIAÇÃO","FOLLOW UP","ATEND. CLIENTES ATIVOS","ATEND. CLIENTES INATIVOS","PÓS-VENDA / RELACIONAMENTO","PERDA / NUTRIÇÃO"];
const RES = ["ORÇAM","CADAST","RELAC","ATEND","SUPORTE","VENDA","Ñ ATEND","RECUS","Ñ RESP","PERDA","FUP 7","FUP 15"];
const CAN = ["WPP","LIGOU","ATENDIDA","Ñ ATEND"];
const FUN = ["EM ATEND","ORÇAM","CADAST","VENDA","FUP","SUPORTE","Ñ VENDA","PERDA"];
const MOT = ["AINDA TEM ESTOQUE","PRODUTO NÃO VENDEU / SEM GIRO","LOJA ANEXO / PRÓXIMO SM","SÓ QUER COMPRAR GRANEL","PROBLEMA LOGÍSTICO / ENTREGA","PROBLEMA FINANCEIRO / CRÉDITO","PROPRIETÁRIO INDISPONÍVEL","FECHANDO / FECHOU LOJA","SEM INTERESSE NO MOMENTO","PRIMEIRO CONTATO / SEM RESPOSTA"];
const CON = ["LARISSA PADILHA","MANU DITZEL","JULIO GADRET","DAIANE STAVICKI"];
const TAC = ["VENDA","PRÉ-VENDA","PÓS-VENDA","RESOLUÇÃO DE PROBLEMA","PROSPECÇÃO","ADMINISTRATIVO"];
const RNC = ["ATRASO ENTREGA (TRANSPORTADORA)","PRODUTO AVARIADO (FÁBRICA/TRANSPORTE)","ERRO SEPARAÇÃO (EXPEDIÇÃO)","ERRO NOTA FISCAL (FATURAMENTO)","DIVERGÊNCIA PREÇO (FATURAMENTO)","COBRANÇA INDEVIDA (FINANCEIRO)","RUPTURA ESTOQUE (FÁBRICA/PCP)"];
const DEM = ["PROSPECÇÃO - BASE GRANEL","PROSPECÇÃO - PESQUISA GOOGLE","RESPONDER LEADS COM DÚVIDAS","CONTATO LEADS DO SITE","ATENDIMENTO ATIVOS/INATIVOS","MONTAR ORÇAMENTO (CURVA ABC)","RESPOSTAS GRUPO ALINHAMENTO","LIGAÇÕES DA BASE","LIGAÇÕES PROSPECT","FAZER RASTREIOS","COBRANÇA DE TÍTULOS","DIGITAÇÃO DE PEDIDOS","SOLICITAÇÃO DE NF (SEM SAP)","SOLICITAÇÃO DE BOLETOS","RESOLUÇÃO DE NFD","SUPORTE PCV - DÚVIDAS PEDIDOS","AJUSTE DE BOLETOS","SUPORTE PRODUTO (LAUDOS)","SOLICITAR LINK CARTÃO","SOLICITAR VALORES PIX","CADASTRO NO ASANA","SOLICITAR MATERIAL TRADE","PREENCHER FOLLOW-UP","ENVIAR ANÁLISE DE CRÉDITO","CONSULTAR ESTOQUE (SEM SAP)"];

function Tbl({ h, rows, hlc, first = 220 }) {
  return (
    <div className="bg-white rounded-lg border border-gray-200 overflow-x-auto">
      <table className="w-full text-xs border-collapse">
        <thead>
          <tr className="bg-slate-800">
            {h.map((x, i) => (
              <th key={i} className={`py-2 px-3 text-white font-semibold whitespace-nowrap ${i === 0 ? "text-left" : "text-center"}`}
                style={i === 0 ? { minWidth: first } : { minWidth: 52 }}>{x}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, ri) => {
            const isLast = ri === rows.length - 1 && rows.length > 2;
            return (
              <tr key={ri} className={`${isLast ? "bg-gray-100 font-bold border-t-2 border-gray-300" : ri % 2 === 0 ? "bg-white" : "bg-gray-50"}`}>
                {r.map((c, ci) => (
                  <td key={ci} className={`py-2 px-3 border-b border-gray-100 ${ci === 0 ? "text-left text-gray-700" : "text-center text-gray-500"} ${hlc?.includes(ci) ? "text-green-600 font-bold" : ""}`}>{c}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function Badge({ t }) {
  const c = { ORIGINAL: "bg-blue-50 text-blue-700", NOVO: "bg-green-50 text-green-700", MELHORADO: "bg-amber-50 text-amber-700", REDUNDANTE: "bg-red-50 text-red-600 line-through" };
  return <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${c[t] || "bg-gray-100 text-gray-500"}`}>{t}</span>;
}

function Head({ title, emoji, badge, note }) {
  return (
    <div className="flex items-center justify-between mb-2">
      <div className="flex items-center gap-2">
        <span className="text-base">{emoji}</span>
        <span className="text-sm font-bold text-gray-800">{title}</span>
        <Badge t={badge} />
      </div>
      {note && <span className="text-xs text-gray-400 italic">{note}</span>}
    </div>
  );
}

function Nota({ on, children }) {
  if (!on) return null;
  return <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 mb-2 text-xs text-blue-800 leading-relaxed">{children}</div>;
}

export default function Dash() {
  const [tab, setTab] = useState("all");
  const [an, setAn] = useState(true);
  const z = n => Array(n).fill(0);
  const ok = id => tab === "all" || tab === id;

  const tabs = [
    { id: "all", l: "COMPLETO" }, { id: "kpi", l: "KPIs" }, { id: "matriz", l: "MATRIZ" },
    { id: "canais", l: "CANAIS + FUNIL" }, { id: "motivos", l: "MOTIVOS" }, { id: "perf", l: "PERFORMANCE" },
    { id: "temp", l: "TEMPERATURA" }, { id: "acao", l: "TIPO AÇÃO" },
    { id: "rnc", l: "RNC" }, { id: "demanda", l: "DEMANDA" }, { id: "novos", l: "🆕 NOVOS" },
  ];

  return (
    <div className="min-h-screen bg-gray-50" style={{ fontFamily: "system-ui, -apple-system, sans-serif" }}>

      {/* HEADER */}
      <div className="bg-slate-800 text-white sticky top-0 z-20 px-5 py-3">
        <div className="flex justify-between items-center max-w-7xl mx-auto">
          <div>
            <div className="text-base font-bold tracking-wide">📊 DASHBOARD CRM · VITAO 360</div>
            <div className="text-xs text-slate-400 mt-0.5">Fonte: DRAFT 2 · 9 blocos originais + 5 novos · 13/FEV/2026</div>
          </div>
          <label className="flex items-center gap-2 cursor-pointer text-xs text-slate-400">
            <input type="checkbox" checked={an} onChange={() => setAn(!an)} className="rounded" />
            Anotações
          </label>
        </div>
        <div className="flex gap-1 mt-2 max-w-7xl mx-auto flex-wrap">
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`px-3 py-1 rounded text-xs font-semibold transition-all ${
                tab === t.id ? "bg-white text-slate-800" : "bg-slate-700 text-slate-300 hover:bg-slate-600"
              }`}>{t.l}</button>
          ))}
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-5 py-4 space-y-6">

        {/* ═══ 1. KPIs ═══ */}
        {ok("kpi") && (
          <div>
            <Head title="KPIs GLOBAIS" emoji="📊" badge="MELHORADO" note="Excel R3-R5 · Reorganizado" />
            <Nota on={an}>💡 <b>Mudança:</b> VENDAS saiu do destaque (já existe no BI). 3 grandes = <b>ATENDIMENTOS × DEMANDAS × CONVERSÃO</b> — esforço operacional vs resultado.</Nota>

            {/* 3 Big */}
            <div className="grid grid-cols-3 gap-3 mb-3">
              {[
                { i: "📋", v: 0, l: "ATENDIMENTOS", d: "Contatos registrados", c: "text-blue-600 border-blue-200" },
                { i: "⏱️", v: 0, l: "DEMANDAS", d: "Tarefas operacionais (25 tipos)", c: "text-orange-500 border-orange-200" },
                { i: "📈", v: "0%", l: "% CONVERSÃO", d: "Atendimentos → venda", c: "text-violet-600 border-violet-200" },
              ].map((k, i) => (
                <div key={i} className={`bg-white rounded-xl border-2 ${k.c} p-5 text-center`}>
                  <div className="text-3xl">{k.i}</div>
                  <div className={`text-4xl font-black mt-1 ${k.c.split(" ")[0]}`}>{k.v}</div>
                  <div className="text-xs font-bold text-gray-600 mt-2 tracking-wide">{k.l}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{k.d}</div>
                </div>
              ))}
            </div>

            {/* Ratio */}
            <div className="bg-white rounded-lg border border-gray-200 px-4 py-2.5 flex justify-between items-center mb-3">
              <div className="flex items-center gap-3">
                <span className="text-xs font-bold text-gray-600">RATIO DEMANDAS / ATENDIMENTOS</span>
                <span className="text-sm font-black text-orange-500">0%</span>
              </div>
              <div className="flex gap-4 text-xs text-gray-400">
                <span>🟢 &lt;30% vendendo</span>
                <span>🟡 30-50% equilibrado</span>
                <span>🔴 &gt;50% apagando incêndio</span>
              </div>
            </div>

            {/* 7 Small */}
            <div className="grid grid-cols-7 gap-2">
              {[
                { i: "💰", v: 0, l: "VENDAS", c: "text-green-600" },
                { i: "📄", v: 0, l: "ORÇAMENTOS", c: "text-amber-500" },
                { i: "🔥", v: 0, l: "QUENTES", c: "text-red-500" },
                { i: "❄️", v: 0, l: "FRIOS", c: "text-cyan-500" },
                { i: "🚨", v: 0, l: "RNC", c: "text-red-600" },
                { i: "🔍", v: 0, l: "PROSPECÇÕES", c: "text-purple-500" },
                { i: "🔄", v: 0, l: "FOLLOW-UPS", c: "text-teal-500" },
              ].map((k, i) => (
                <div key={i} className="bg-white rounded-lg border border-gray-200 py-2.5 text-center">
                  <div className="text-base">{k.i}</div>
                  <div className={`text-xl font-bold mt-0.5 ${k.c}`}>{k.v}</div>
                  <div className="text-xs text-gray-400 mt-0.5">{k.l}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ═══ 2. MATRIZ ═══ */}
        {ok("matriz") && (
          <div>
            <Head title="TIPO CONTATO × RESULTADO" emoji="📋" badge="ORIGINAL" note="Excel R7-R16 · 7×12" />
            <Tbl h={["TIPO CONTATO", "TOTAL", ...RES]}
              rows={[...TC.map(t => [t, 0, ...z(12)]), ["TOTAL", 0, ...z(12)]]}
              hlc={[6]} />
          </div>
        )}

        {/* ═══ 3. CANAIS ═══ */}
        {ok("canais") && (
          <div>
            <Head title="CANAIS DE CONTATO" emoji="📞" badge="ORIGINAL" note="Excel R18-R28 · Canais" />
            <Tbl h={["TIPO CONTATO", "TOTAL", ...CAN]}
              rows={[...TC.map(t => [t, 0, ...z(4)]), ["TOTAL", 0, ...z(4)]]} />
          </div>
        )}

        {/* ═══ 3b. FUNIL ═══ */}
        {ok("canais") && (
          <div>
            <Head title="FUNIL DE VENDA" emoji="🔽" badge="ORIGINAL" note="Excel R18-R28 · Funil" />
            <Tbl h={["TIPO CONTATO", ...FUN]}
              rows={[...TC.map(t => [t, ...z(8)]), ["TOTAL", ...z(8)]]}
              hlc={[4]} />
          </div>
        )}

        {/* ═══ 4. MOTIVOS ═══ */}
        {ok("motivos") && (
          <div>
            <Head title="MOTIVOS DE NÃO COMPRA" emoji="📝" badge="ORIGINAL" note="Excel R30-R42 · 10 motivos × SITUAÇÃO" />
            <Tbl h={["MOTIVO", "QTD", "%", "PROSPECT", "ATIVO", "INATIVO", "OUTROS"]}
              rows={[...MOT.map(m => [m, 0, "0%", 0, 0, 0, 0]), ["TOTAL", 0, "100%", 0, 0, 0, 0]]}
              first={260} />
          </div>
        )}

        {/* ═══ 5. PERFORMANCE ═══ */}
        {ok("perf") && (
          <div>
            <Head title="PERFORMANCE POR CONSULTOR" emoji="👤" badge="ORIGINAL" note="Excel R30-R36 · 4 consultores" />
            <Tbl h={["CONSULTOR", "CONTATOS", "VENDAS", "ORÇAM", "CADAST", "% CONV", "Ñ ATENDE", "PERDA", "% MERCOS"]}
              rows={[...CON.map(c => [c, 0, 0, 0, 0, "0%", 0, 0, "0%"]), ["TOTAL", 0, 0, 0, 0, "0%", 0, 0, "0%"]]}
              hlc={[2]} first={180} />
          </div>
        )}

        {/* ═══ 6. TEMPERATURA ═══ */}
        {ok("temp") && (
          <div>
            <Head title="TEMPERATURA" emoji="🌡️" badge="ORIGINAL" note="Excel R38-R43" />
            <div className="grid grid-cols-4 gap-3">
              {[
                { e: "🔥", l: "QUENTE", d: "Perto de fechar", c: "border-red-300 bg-red-50 text-red-600" },
                { e: "🟡", l: "MORNO", d: "Em andamento", c: "border-amber-300 bg-amber-50 text-amber-600" },
                { e: "❄️", l: "FRIO", d: "Sem resposta", c: "border-cyan-300 bg-cyan-50 text-cyan-600" },
                { e: "💀", l: "PERDIDO", d: "Saiu da base", c: "border-gray-300 bg-gray-50 text-gray-500" },
              ].map((t, i) => (
                <div key={i} className={`rounded-xl border-2 ${t.c} p-4 text-center`}>
                  <div className="text-2xl">{t.e}</div>
                  <div className={`text-3xl font-black mt-1`}>0</div>
                  <div className="text-xs font-bold mt-1">{t.l}</div>
                  <div className="text-xs opacity-60 mt-0.5">{t.d}</div>
                  <div className="text-xs opacity-40 mt-0.5">0%</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ═══ 7. TIPO AÇÃO ═══ */}
        {ok("acao") && (
          <div>
            <Head title="TIPO AÇÃO × CONSULTOR" emoji="🎯" badge="ORIGINAL" note="Excel R45-R53 · 6×4" />
            <Nota on={an}>⚠️ <b>Redundância removida:</b> Excel tinha este bloco duplicado (R43-44 preview + R45-53 completo). Mantido apenas o completo.</Nota>
            <Tbl h={["TIPO AÇÃO", "TOTAL", "LARISSA", "MANU", "JULIO", "DAIANE", "%"]}
              rows={[...TAC.map(t => [t, 0, 0, 0, 0, 0, "0%"]), ["TOTAL", 0, 0, 0, 0, 0, "100%"]]}
              hlc={[1]} first={220} />
          </div>
        )}

        {/* ═══ 8. RNC ═══ */}
        {ok("rnc") && (
          <div>
            <Head title="RNC POR ÁREA RESPONSÁVEL" emoji="🚨" badge="ORIGINAL" note="Excel R42-R51 · 7 tipos" />
            <Nota on={an}>✅ <b>Melhoria:</b> Nomes completos sem abreviação. Área responsável visível no nome do problema.</Nota>
            <Tbl h={["TIPO PROBLEMA", "QTD", "%"]}
              rows={[...RNC.map(r => [r, 0, "0%"]), ["TOTAL", 0, "100%"]]}
              first={300} />
          </div>
        )}

        {/* ═══ 9. DEMANDA ═══ */}
        {ok("demanda") && (
          <div>
            <Head title="DEMANDA — 25 ATIVIDADES" emoji="⏱️" badge="ORIGINAL" note="Excel R54-R67" />
            <Nota on={an}>💡 <b>Melhoria:</b> No Excel são 2 tabelas lado a lado. Aqui unificamos em tabela única com coluna TIPO para agrupar.</Nota>
            <Tbl h={["#", "ATIVIDADE", "TIPO", "QTD", "%"]}
              rows={[
                ...DEM.map((d, i) => [i + 1, d, i < 13 ? "COMERCIAL" : "SUPORTE/ADM", 0, "0%"]),
                ["—", "TOTAL DEMANDAS", "—", 0, "100%"]
              ]}
              first={30} />
          </div>
        )}

        {/* ═══════════════════════════════ */}
        {/* ═══ BLOCOS NOVOS ═══ */}
        {/* ═══════════════════════════════ */}
        {ok("novos") && (
          <div className="space-y-5">
            <div className="bg-gradient-to-r from-green-50 to-emerald-50 rounded-xl border-2 border-green-300 px-5 py-3">
              <div className="text-sm font-bold text-green-800">🆕 BLOCOS NOVOS — Propostas para o Comitê</div>
              <div className="text-xs text-green-600 mt-0.5">Não existem no DASH original. Lacunas identificadas na auditoria.</div>
            </div>

            {/* NOVO 10: Saúde da Base */}
            <div>
              <Head title="SAÚDE DA BASE (SITUAÇÃO)" emoji="🏥" badge="NOVO" />
              <Nota on={an}>O DASH não mostra composição ATIVO vs INATIVO. Gestor precisa pra priorizar ações.</Nota>
              <div className="grid grid-cols-5 gap-3">
                {[
                  { l: "ATIVO", v: 105, p: "21%", c: "border-green-400 text-green-600" },
                  { l: "INAT.REC", v: 80, p: "16%", c: "border-amber-400 text-amber-600" },
                  { l: "INAT.ANT", v: 304, p: "62%", c: "border-red-400 text-red-600" },
                  { l: "PROSPECT", v: 0, p: "0%", c: "border-purple-400 text-purple-600" },
                  { l: "TOTAL", v: 489, p: "100%", c: "border-gray-400 text-gray-700" },
                ].map((s, i) => (
                  <div key={i} className={`bg-white rounded-lg border-t-4 ${s.c} border border-gray-200 p-3 text-center`}>
                    <div className={`text-2xl font-black ${s.c.split(" ").pop()}`}>{s.v}</div>
                    <div className="text-xs font-bold text-gray-600 mt-1">{s.l}</div>
                    <div className="text-xs text-gray-400">{s.p}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* NOVO 11: Recompra */}
            <div>
              <Head title="TAXA DE RECOMPRA" emoji="🔁" badge="NOVO" />
              <Nota on={an}>KPI #1 para B2B. Hoje 20.3% — deveria ser 40%+. Invisível no DASH original.</Nota>
              <div className="grid grid-cols-4 gap-3">
                {[
                  { l: "1 COMPRA", v: 389, p: "79.7%", c: "border-red-400 text-red-600", d: "Não recomprou" },
                  { l: "2-3 COMPRAS", v: 62, p: "12.7%", c: "border-amber-400 text-amber-600", d: "Início" },
                  { l: "4-6 COMPRAS", v: 24, p: "4.9%", c: "border-green-400 text-green-600", d: "Recorrente" },
                  { l: "7+ COMPRAS", v: 14, p: "2.7%", c: "border-blue-400 text-blue-600", d: "Fidelizado" },
                ].map((r, i) => (
                  <div key={i} className={`bg-white rounded-lg border-t-4 ${r.c} border border-gray-200 p-3 text-center`}>
                    <div className={`text-2xl font-black ${r.c.split(" ").pop()}`}>{r.v}</div>
                    <div className="text-xs font-bold text-gray-600 mt-1">{r.l}</div>
                    <div className="text-xs text-gray-400">{r.d}</div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5 mt-2">
                      <div className="h-1.5 rounded-full bg-current" style={{ width: r.p }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* NOVO 12: Sinaleiro */}
            <div>
              <Head title="SINALEIRO PENETRAÇÃO — REDES" emoji="🚦" badge="NOVO" note="923 lojas · 8 redes" />
              <Nota on={an}>Gestor precisa ver de relance quais redes estão penetradas. Hoje só na PROJEÇÃO (80 colunas, impossível ler rápido).</Nota>
              <div className="grid grid-cols-4 gap-3">
                {[
                  { r: "MUNDO VERDE", t: 300, a: 45 }, { r: "BIOMUNDO", t: 89, a: 12 },
                  { r: "CIA SAÚDE", t: 156, a: 28 }, { r: "FIT LAND", t: 43, a: 8 },
                  { r: "DIVINA TERRA", t: 78, a: 5 }, { r: "VIDA LEVE", t: 67, a: 3 },
                  { r: "TUDO EM GRÃOS", t: 120, a: 4 }, { r: "ARMAZ. FITSTORE", t: 70, a: 2 },
                ].map((n, i) => {
                  const pct = Math.round((n.a / n.t) * 100);
                  return (
                    <div key={i} className="bg-white rounded-lg border border-gray-200 p-3">
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-xs font-bold text-gray-700">{n.r}</span>
                        <span>{pct >= 20 ? "🟢" : pct >= 10 ? "🟡" : "🔴"}</span>
                      </div>
                      <div className="text-lg font-black text-gray-800">{n.a}<span className="text-sm font-normal text-gray-400">/{n.t}</span></div>
                      <div className="w-full bg-gray-100 rounded-full h-1.5 mt-2">
                        <div className="h-1.5 rounded-full bg-blue-500" style={{ width: `${pct}%` }} />
                      </div>
                      <div className="text-xs text-gray-400 mt-1">{pct}% penetração</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* NOVO 13: Alertas */}
            <div>
              <Head title="ALERTAS DE INATIVIDADE" emoji="⏰" badge="NOVO" />
              <Nota on={an}>Triggers automáticos 45/60/90 dias evitam perda de clientes antes que aconteça.</Nota>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { f: "45-59 DIAS", a: "CONTATO URGENTE", c: "border-amber-400 text-amber-500", e: "⚠️" },
                  { f: "60-89 DIAS", a: "OFERTA ESPECIAL", c: "border-orange-400 text-orange-500", e: "🔶" },
                  { f: "90+ DIAS", a: "REATIVAÇÃO", c: "border-red-400 text-red-500", e: "🔴" },
                ].map((al, i) => (
                  <div key={i} className={`bg-white rounded-xl border-t-4 ${al.c} border border-gray-200 p-5 text-center`}>
                    <div className="text-2xl">{al.e}</div>
                    <div className={`text-3xl font-black mt-2 ${al.c.split(" ").pop()}`}>?</div>
                    <div className="text-xs font-bold text-gray-600 mt-2">{al.f}</div>
                    <div className="text-xs text-gray-400 mt-0.5">Ação: {al.a}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* NOVO 14: Curva ABC */}
            <div>
              <Head title="CURVA ABC — RESUMO" emoji="📊" badge="NOVO" />
              <Nota on={an}>Curva A = 80% receita. Sem isso no DASH o time não sabe quem priorizar.</Nota>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { curva: "A", d: "80% da receita", c: "bg-green-50 border-green-400 text-green-600" },
                  { curva: "B", d: "15% da receita", c: "bg-amber-50 border-amber-400 text-amber-600" },
                  { curva: "C", d: "5% da receita", c: "bg-red-50 border-red-400 text-red-600" },
                ].map((ab, i) => (
                  <div key={i} className={`rounded-xl border-t-4 border border-gray-200 p-5 text-center ${ab.c}`}>
                    <div className={`text-4xl font-black`}>{ab.curva}</div>
                    <div className="text-lg font-bold text-gray-700 mt-2">? clientes</div>
                    <div className="text-xs text-gray-500 mt-1">{ab.d}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* RESUMO */}
            <div className="bg-white rounded-xl border border-gray-200 p-5">
              <div className="text-sm font-bold text-gray-800 mb-3">RESUMO: ORIGINAL vs PROPOSTA</div>
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <div className="text-xs font-bold text-gray-600 mb-2">DASH ORIGINAL (9 blocos)</div>
                  {["1. KPIs Globais","2. Matriz Tipo Contato × Resultado","3. Canais + Funil de Venda","4. Motivos de Não Compra","5. Performance Consultor","6. Temperatura","7. Tipo Ação × Consultor","8. RNC por Área","9. Demanda (25 atividades)"].map((b, i) => (
                    <div key={i} className="text-xs text-gray-600 py-0.5 flex items-center gap-2">
                      <span className="text-green-500">✅</span>{b}
                    </div>
                  ))}
                  <div className="text-xs text-red-500 py-0.5 flex items-center gap-2 mt-1">
                    <span>❌</span>Tipo Ação preview (R43-44) — <Badge t="REDUNDANTE" />
                  </div>
                </div>
                <div>
                  <div className="text-xs font-bold text-green-700 mb-2">NOVOS PROPOSTOS (+5 blocos)</div>
                  {["10. Saúde da Base (SITUAÇÃO)","11. Taxa de Recompra","12. Sinaleiro Penetração Redes","13. Alertas Inatividade (45/60/90d)","14. Curva ABC Resumo"].map((b, i) => (
                    <div key={i} className="text-xs text-green-700 py-0.5 flex items-center gap-2">
                      <span>🆕</span>{b}
                    </div>
                  ))}
                  <div className="text-xs text-gray-500 mt-3 bg-gray-50 rounded-lg px-3 py-2">
                    Total proposto: <b>14 blocos</b> (9 originais + 5 novos − 1 redundante)
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
