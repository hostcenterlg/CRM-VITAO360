import React, { useState, useMemo } from "react";

// ═══════════════════════════════════════════════════════════════
// DASHBOARD VITAO 360 — VERSÃO FINAL CONSOLIDADA
// Fonte: CRM INTELIGENTE V11 (DRAFT 1 + DRAFT 2)
// 14 blocos: 9 originais + 5 estratégicos
// Data: 16/FEV/2026
// ═══════════════════════════════════════════════════════════════

const COLORS = {
  vitao: "#00854A", vitaoLight: "#E8F5EF", vitaoDark: "#004D2C",
  ativo: "#00B050", inatRec: "#FFC000", inatAnt: "#FF0000",
  risco: "#FF6600", novo: "#7030A0", prospect: "#3B82F6",
  bg: "#F7F8FA", card: "#FFFFFF", text: "#1A1D23", sub: "#6B7280",
  accent: "#00854A", border: "#E5E7EB", headerBg: "#0F1419",
};

// ═══ DADOS REAIS EXTRAÍDOS DO CRM V11 ═══
const DATA = {
  totalClientes: 471,
  totalAtendimentos: 441,
  totalVendas: 48,
  totalOrcamentos: 53,
  convGeral: 10.9,

  situacao: { ATIVO: 152, "INAT.ANT": 82, "EM RISCO": 66, NOVO: 55, "INAT.REC": 52, PROSPECT: 34 },

  consultores: [
    { nome: "MANU DITZEL", cont: 133, vend: 16, orc: 11, cad: 5, fup: 18, sup: 12, terr: "SC/PR/RS" },
    { nome: "LARISSA PADILHA", cont: 111, vend: 14, orc: 22, cad: 6, fup: 15, sup: 10, terr: "Resto BR" },
    { nome: "DAIANE STAVICKI", cont: 111, vend: 10, orc: 10, cad: 4, fup: 12, sup: 11, terr: "Franquias" },
    { nome: "JULIO GADRET", cont: 86, vend: 8, orc: 10, cad: 3, fup: 8, sup: 8, terr: "Cia/Fitland" },
  ],

  canais: { wpp: 308, ligou: 201, atendida: 118, nAtend: 83 },

  tipoContato: [
    { tipo: "ATEND. CLIENTES ATIVOS", total: 123 },
    { tipo: "PÓS-VENDA / RELAC.", total: 96 },
    { tipo: "PROSPECÇÃO", total: 52 },
    { tipo: "ATEND. CLIENTES INATIVOS", total: 50 },
    { tipo: "FOLLOW UP", total: 49 },
    { tipo: "NEGOCIAÇÃO", total: 40 },
    { tipo: "PERDA / NUTRIÇÃO", total: 31 },
  ],

  resultado: [
    { res: "RELACIONAMENTO", qtd: 58 }, { res: "ORÇAMENTO", qtd: 53 },
    { res: "VENDA / PEDIDO", qtd: 48 }, { res: "EM ATENDIMENTO", qtd: 47 },
    { res: "FOLLOW UP 7", qtd: 43 }, { res: "NÃO ATENDE", qtd: 42 },
    { res: "SUPORTE", qtd: 41 }, { res: "NÃO RESPONDE", qtd: 35 },
    { res: "FOLLOW UP 15", qtd: 26 }, { res: "CADASTRO", qtd: 18 },
    { res: "RECUSOU LIGAÇÃO", qtd: 16 }, { res: "PERDA / FECHOU", qtd: 14 },
  ],

  matrix: {
    "PROSPECÇÃO":      { CAD: 12, "EM AT": 13, FU15: 0, FU7: 0, "Ñ AT": 7, "Ñ RE": 9, ORC: 4, PERD: 0, REC: 4, REL: 2, SUP: 0, VEND: 1 },
    "NEGOCIAÇÃO":      { CAD: 3, "EM AT": 11, FU15: 0, FU7: 2, "Ñ AT": 1, "Ñ RE": 0, ORC: 16, PERD: 0, REC: 0, REL: 0, SUP: 0, VEND: 7 },
    "FOLLOW UP":       { CAD: 0, "EM AT": 8, FU15: 1, FU7: 10, "Ñ AT": 5, "Ñ RE": 4, ORC: 12, PERD: 0, REC: 0, REL: 3, SUP: 4, VEND: 2 },
    "ATEND. ATIVOS":   { CAD: 0, "EM AT": 8, FU15: 9, FU7: 17, "Ñ AT": 10, "Ñ RE": 0, ORC: 13, PERD: 0, REC: 0, REL: 26, SUP: 14, VEND: 26 },
    "ATEND. INATIVOS": { CAD: 3, "EM AT": 6, FU15: 3, FU7: 3, "Ñ AT": 7, "Ñ RE": 11, ORC: 2, PERD: 4, REC: 9, REL: 0, SUP: 0, VEND: 2 },
    "PÓS-VENDA":      { CAD: 0, "EM AT": 0, FU15: 10, FU7: 11, "Ñ AT": 5, "Ñ RE": 6, ORC: 6, PERD: 0, REC: 0, REL: 27, SUP: 21, VEND: 10 },
    "PERDA / NUTRIÇÃO":{ CAD: 0, "EM AT": 1, FU15: 3, FU7: 0, "Ñ AT": 7, "Ñ RE": 5, ORC: 0, PERD: 10, REC: 3, REL: 0, SUP: 2, VEND: 0 },
  },

  motivos: [
    { motivo: "AINDA TEM ESTOQUE", qtd: 43 },
    { motivo: "PROBLEMA LOGÍSTICO / ENTREGA", qtd: 33 },
    { motivo: "SÓ QUER COMPRAR GRANEL", qtd: 20 },
    { motivo: "PRODUTO NÃO VENDEU / SEM GIRO", qtd: 19 },
    { motivo: "SEM INTERESSE NO MOMENTO", qtd: 18 },
    { motivo: "PROPRIETÁRIO / INDISPONÍVEL", qtd: 12 },
    { motivo: "PROBLEMA FINANCEIRO / CRÉDITO", qtd: 11 },
    { motivo: "PRIMEIRO CONTATO / SEM RESPOSTA", qtd: 9 },
    { motivo: "LOJA ANEXO/PRÓXIMO - SM", qtd: 9 },
    { motivo: "FECHANDO / FECHOU LOJA", qtd: 2 },
  ],

  redes: [
    { nome: "DEMAIS CLIENTES", atend: 155 },
    { nome: "MUNDO VERDE", atend: 62 },
    { nome: "CIA DA SAÚDE", atend: 42 },
    { nome: "DIVINA TERRA", atend: 42 },
    { nome: "VIDA LEVE", atend: 40 },
    { nome: "FIT LAND", atend: 35 },
    { nome: "BIOMUNDO", atend: 34 },
    { nome: "TUDO EM GRÃOS", atend: 30 },
  ],

  // NOVOS — dados DRAFT 1
  curvaABC: { A: 190, B: 155, C: 113 },
  recompra: { "1 COMPRA": 213, "2-3 COMPRAS": 117, "4-6 COMPRAS": 46, "7+ COMPRAS": 8 },
  alertas: { ate45: 84, de45a59: 19, de60a89: 90, acima90: 275 },
  sinaleiro: [
    { rede: "FIT LAND", total: 43, clientes: 35, pct: 81 },
    { rede: "VIDA LEVE", total: 67, clientes: 40, pct: 60 },
    { rede: "CIA DA SAÚDE", total: 156, clientes: 42, pct: 27 },
    { rede: "DIVINA TERRA", total: 78, clientes: 42, pct: 54 },
    { rede: "BIOMUNDO", total: 89, clientes: 34, pct: 38 },
    { rede: "MUNDO VERDE", total: 300, clientes: 62, pct: 21 },
    { rede: "TUDO EM GRÃOS", total: 120, clientes: 30, pct: 25 },
  ],
  ticketMedio: 2236,
  ufTop: [
    { uf: "SC", qtd: 119 }, { uf: "PR", qtd: 77 }, { uf: "SP", qtd: 68 },
    { uf: "RS", qtd: 48 }, { uf: "MG", qtd: 29 }, { uf: "RJ", qtd: 21 },
    { uf: "GO", qtd: 17 }, { uf: "PE", qtd: 16 }, { uf: "MT", qtd: 15 }, { uf: "BA", qtd: 14 },
  ],
};

const matrixCols = ["CAD","EM AT","FU7","FU15","ORC","VEND","REL","SUP","Ñ AT","Ñ RE","REC","PERD"];

// ═══ COMPONENTES ═══

function KPICard({ icon, value, label, sub, color, small }) {
  return (
    <div style={{
      background: COLORS.card, borderRadius: 14, padding: small ? "14px 16px" : "20px 24px",
      border: `1px solid ${COLORS.border}`, borderLeft: `4px solid ${color}`,
      display: "flex", flexDirection: "column", gap: 4,
      boxShadow: "0 1px 3px rgba(0,0,0,0.04)",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{ fontSize: small ? 16 : 20 }}>{icon}</span>
        <span style={{ fontSize: 11, fontWeight: 700, color: COLORS.sub, textTransform: "uppercase", letterSpacing: 0.5 }}>{label}</span>
      </div>
      <div style={{ fontSize: small ? 24 : 32, fontWeight: 900, color, lineHeight: 1, fontFamily: "'DM Sans', sans-serif" }}>{value}</div>
      {sub && <span style={{ fontSize: 11, color: COLORS.sub }}>{sub}</span>}
    </div>
  );
}

function SectionHeader({ title, icon, tag, tagColor }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12, marginTop: 8 }}>
      <span style={{ fontSize: 18 }}>{icon}</span>
      <span style={{ fontSize: 15, fontWeight: 800, color: COLORS.text, fontFamily: "'DM Sans', sans-serif" }}>{title}</span>
      {tag && (
        <span style={{
          fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 20,
          background: tagColor || "#E8F5EF", color: tagColor ? "#fff" : COLORS.vitao,
        }}>{tag}</span>
      )}
      <div style={{ flex: 1, height: 1, background: COLORS.border, marginLeft: 8 }} />
    </div>
  );
}

function DataTable({ headers, rows, highlightCol, compact }) {
  return (
    <div style={{ borderRadius: 10, overflow: "hidden", border: `1px solid ${COLORS.border}` }}>
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: compact ? 11 : 12 }}>
        <thead>
          <tr style={{ background: COLORS.headerBg }}>
            {headers.map((h, i) => (
              <th key={i} style={{
                padding: compact ? "6px 8px" : "8px 10px", color: "#fff", fontWeight: 700,
                textAlign: i === 0 ? "left" : "center", fontSize: 10, letterSpacing: 0.3,
                whiteSpace: "nowrap", borderBottom: "2px solid #00854A"
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, ri) => {
            const isTotal = ri === rows.length - 1 && rows.length > 2;
            return (
              <tr key={ri} style={{
                background: isTotal ? "#F0FDF4" : ri % 2 === 0 ? "#fff" : "#FAFBFC",
                fontWeight: isTotal ? 800 : 400,
                borderTop: isTotal ? `2px solid ${COLORS.vitao}` : "none",
              }}>
                {row.map((c, ci) => (
                  <td key={ci} style={{
                    padding: compact ? "5px 8px" : "7px 10px",
                    textAlign: ci === 0 ? "left" : "center",
                    color: highlightCol?.includes(ci) ? COLORS.vitao : ci === 0 ? COLORS.text : COLORS.sub,
                    fontWeight: highlightCol?.includes(ci) || ci === 0 ? 700 : 400,
                    borderBottom: `1px solid ${COLORS.border}`,
                    fontSize: compact ? 10 : 11,
                  }}>{c}</td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

function BarMini({ value, max, color, height = 6 }) {
  const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
  return (
    <div style={{ width: "100%", height, background: "#E5E7EB", borderRadius: height / 2, overflow: "hidden" }}>
      <div style={{ width: `${pct}%`, height: "100%", background: color || COLORS.vitao, borderRadius: height / 2, transition: "width 0.6s ease" }} />
    </div>
  );
}

function PctBadge({ value, invert }) {
  const v = parseFloat(value);
  const c = invert ? (v > 50 ? "#EF4444" : v > 30 ? "#F59E0B" : "#22C55E") : (v >= 15 ? "#22C55E" : v >= 8 ? "#F59E0B" : "#EF4444");
  return <span style={{ fontSize: 10, fontWeight: 800, color: c }}>{value}%</span>;
}

// ═══ MAIN DASHBOARD ═══

export default function DashboardVitao360() {
  const [activeTab, setActiveTab] = useState("resumo");

  const tabs = [
    { id: "resumo", label: "RESUMO EXECUTIVO", icon: "🏠" },
    { id: "operacional", label: "OPERACIONAL", icon: "📋" },
    { id: "funil", label: "FUNIL + CANAIS", icon: "📞" },
    { id: "performance", label: "PERFORMANCE", icon: "👤" },
    { id: "saude", label: "SAÚDE DA BASE", icon: "💚" },
    { id: "redes", label: "REDES + SINALEIRO", icon: "🚦" },
    { id: "motivos", label: "MOTIVOS + RNC", icon: "📝" },
  ];

  const show = (id) => activeTab === id;

  // Computed values
  const totalMotivos = DATA.motivos.reduce((a, m) => a + m.qtd, 0);
  const totalRecompra = Object.values(DATA.recompra).reduce((a, b) => a + b, 0);

  return (
    <div style={{ minHeight: "100vh", background: COLORS.bg, fontFamily: "'DM Sans', -apple-system, sans-serif" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700;900&display=swap" rel="stylesheet" />

      {/* ═══ HEADER ═══ */}
      <div style={{
        background: `linear-gradient(135deg, ${COLORS.headerBg} 0%, #1A2332 100%)`,
        color: "#fff", position: "sticky", top: 0, zIndex: 50,
        borderBottom: `3px solid ${COLORS.vitao}`,
      }}>
        <div style={{ maxWidth: 1280, margin: "0 auto", padding: "14px 24px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{
                  background: COLORS.vitao, padding: "4px 12px", borderRadius: 6,
                  fontSize: 14, fontWeight: 900, letterSpacing: 1.5,
                }}>VITAO</div>
                <span style={{ fontSize: 16, fontWeight: 800, letterSpacing: 0.5 }}>DASHBOARD CRM · 360</span>
              </div>
              <div style={{ fontSize: 11, color: "#8899AA", marginTop: 4 }}>
                Fonte: DRAFT 2 ({DATA.totalAtendimentos} registros) + DRAFT 1 ({DATA.totalClientes} clientes) · CRM V11 · 16/FEV/2026
              </div>
            </div>
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 22, fontWeight: 900, color: COLORS.vitao }}>{DATA.totalAtendimentos}</div>
                <div style={{ fontSize: 9, color: "#8899AA", textTransform: "uppercase" }}>Atendimentos</div>
              </div>
              <div style={{ width: 1, height: 36, background: "#334155" }} />
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 22, fontWeight: 900, color: "#F59E0B" }}>{DATA.totalVendas}</div>
                <div style={{ fontSize: 9, color: "#8899AA", textTransform: "uppercase" }}>Vendas</div>
              </div>
              <div style={{ width: 1, height: 36, background: "#334155" }} />
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 22, fontWeight: 900, color: "#3B82F6" }}>{DATA.convGeral}%</div>
                <div style={{ fontSize: 9, color: "#8899AA", textTransform: "uppercase" }}>Conversão</div>
              </div>
            </div>
          </div>

          {/* Tabs */}
          <div style={{ display: "flex", gap: 4, marginTop: 12, flexWrap: "wrap" }}>
            {tabs.map(t => (
              <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
                padding: "6px 14px", borderRadius: 6, border: "none", cursor: "pointer",
                fontSize: 11, fontWeight: 700, letterSpacing: 0.3, transition: "all 0.2s",
                background: activeTab === t.id ? COLORS.vitao : "rgba(255,255,255,0.08)",
                color: activeTab === t.id ? "#fff" : "#8899AA",
              }}>
                <span style={{ marginRight: 4 }}>{t.icon}</span>{t.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ═══ CONTENT ═══ */}
      <div style={{ maxWidth: 1280, margin: "0 auto", padding: "20px 24px" }}>

        {/* ═══ TAB: RESUMO EXECUTIVO ═══ */}
        {show("resumo") && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

            {/* KPIs Principais */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12 }}>
              <KPICard icon="📋" value={DATA.totalAtendimentos} label="Atendimentos" sub="Contatos registrados" color="#3B82F6" />
              <KPICard icon="💰" value={DATA.totalVendas} label="Vendas" sub={`${DATA.convGeral}% conversão`} color={COLORS.vitao} />
              <KPICard icon="📄" value={DATA.totalOrcamentos} label="Orçamentos" sub="Em pipeline" color="#F59E0B" />
              <KPICard icon="🏢" value={DATA.totalClientes} label="Base Total" sub="DRAFT 1" color="#7030A0" />
              <KPICard icon="💲" value={`R$ ${DATA.ticketMedio.toLocaleString("pt-BR")}`} label="Ticket Médio" sub="Por pedido" color="#EC4899" />
            </div>

            {/* Saúde + Recompra lado a lado */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

              {/* Saúde da Base */}
              <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
                <SectionHeader title="SAÚDE DA BASE" icon="💚" tag="ESTRATÉGICO" />
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
                  {[
                    { l: "ATIVO", v: 152, c: COLORS.ativo, p: "34.5%" },
                    { l: "INAT.REC", v: 52, c: COLORS.inatRec, p: "11.8%" },
                    { l: "INAT.ANT", v: 82, c: COLORS.inatAnt, p: "18.6%" },
                    { l: "EM RISCO", v: 66, c: COLORS.risco, p: "15.0%" },
                    { l: "NOVO", v: 55, c: COLORS.novo, p: "12.5%" },
                    { l: "PROSPECT", v: 34, c: COLORS.prospect, p: "7.7%" },
                  ].map((s, i) => (
                    <div key={i} style={{
                      padding: "10px 12px", borderRadius: 8,
                      borderTop: `3px solid ${s.c}`, background: "#FAFBFC",
                      textAlign: "center",
                    }}>
                      <div style={{ fontSize: 22, fontWeight: 900, color: s.c }}>{s.v}</div>
                      <div style={{ fontSize: 10, fontWeight: 700, color: COLORS.sub }}>{s.l}</div>
                      <div style={{ fontSize: 10, color: COLORS.sub }}>{s.p}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Recompra */}
              <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
                <SectionHeader title="TAXA DE RECOMPRA" icon="🔁" tag="B2B CRÍTICO" />
                {[
                  { l: "1 COMPRA (não recomprou)", v: 213, c: "#EF4444" },
                  { l: "2-3 COMPRAS (início)", v: 117, c: "#F59E0B" },
                  { l: "4-6 COMPRAS (recorrente)", v: 46, c: "#22C55E" },
                  { l: "7+ COMPRAS (fidelizado)", v: 8, c: "#3B82F6" },
                ].map((r, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
                    <div style={{ width: 80, textAlign: "right" }}>
                      <span style={{ fontSize: 16, fontWeight: 900, color: r.c }}>{r.v}</span>
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 10, fontWeight: 600, color: COLORS.text, marginBottom: 2 }}>{r.l}</div>
                      <BarMini value={r.v} max={totalRecompra} color={r.c} height={8} />
                    </div>
                    <span style={{ fontSize: 10, fontWeight: 700, color: COLORS.sub, width: 40, textAlign: "right" }}>
                      {((r.v / totalRecompra) * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
                <div style={{ marginTop: 8, padding: "8px 12px", background: "#FEF2F2", borderRadius: 8, border: "1px solid #FECACA" }}>
                  <span style={{ fontSize: 10, color: "#B91C1C", fontWeight: 700 }}>
                    ⚠️ {((213 / totalRecompra) * 100).toFixed(0)}% da base não recomprou — oportunidade de retenção
                  </span>
                </div>
              </div>
            </div>

            {/* Alertas de Inatividade */}
            <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
              <SectionHeader title="ALERTAS DE INATIVIDADE" icon="⏰" tag="AÇÃO IMEDIATA" />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
                {[
                  { l: "ATIVOS (<45 dias)", v: DATA.alertas.ate45, c: COLORS.ativo, icon: "✅", acao: "Manter ritmo" },
                  { l: "ALERTA (45-59 dias)", v: DATA.alertas.de45a59, c: "#F59E0B", icon: "⚠️", acao: "Contato urgente" },
                  { l: "RISCO (60-89 dias)", v: DATA.alertas.de60a89, c: "#FF6600", icon: "🔶", acao: "Oferta especial" },
                  { l: "INATIVOS (90+ dias)", v: DATA.alertas.acima90, c: COLORS.inatAnt, icon: "🔴", acao: "Campanha reativação" },
                ].map((a, i) => (
                  <div key={i} style={{
                    padding: 16, borderRadius: 12, textAlign: "center",
                    borderTop: `4px solid ${a.c}`, background: "#FAFBFC",
                  }}>
                    <div style={{ fontSize: 24 }}>{a.icon}</div>
                    <div style={{ fontSize: 28, fontWeight: 900, color: a.c, marginTop: 4 }}>{a.v}</div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: COLORS.text, marginTop: 4 }}>{a.l}</div>
                    <div style={{ fontSize: 9, color: COLORS.sub, marginTop: 2 }}>Ação: {a.acao}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Curva ABC + UF */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
                <SectionHeader title="CURVA ABC" icon="📊" tag="PRIORIZAÇÃO" />
                <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
                  {[
                    { curva: "A", v: DATA.curvaABC.A, d: "80% da receita", c: "#22C55E", bg: "#F0FDF4" },
                    { curva: "B", v: DATA.curvaABC.B, d: "15% da receita", c: "#F59E0B", bg: "#FFFBEB" },
                    { curva: "C", v: DATA.curvaABC.C, d: "5% da receita", c: "#EF4444", bg: "#FEF2F2" },
                  ].map((ab, i) => (
                    <div key={i} style={{
                      padding: 16, borderRadius: 12, textAlign: "center",
                      background: ab.bg, border: `2px solid ${ab.c}20`,
                    }}>
                      <div style={{ fontSize: 36, fontWeight: 900, color: ab.c }}>{ab.curva}</div>
                      <div style={{ fontSize: 18, fontWeight: 800, color: COLORS.text }}>{ab.v} clientes</div>
                      <div style={{ fontSize: 10, color: COLORS.sub }}>{ab.d}</div>
                      <div style={{ fontSize: 10, color: COLORS.sub, marginTop: 4 }}>
                        {((ab.v / (DATA.curvaABC.A + DATA.curvaABC.B + DATA.curvaABC.C)) * 100).toFixed(0)}% da base
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
                <SectionHeader title="DISTRIBUIÇÃO POR UF" icon="🗺️" tag="TOP 10" />
                {DATA.ufTop.map((u, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 5 }}>
                    <span style={{ fontSize: 11, fontWeight: 700, color: COLORS.text, width: 24 }}>{u.uf}</span>
                    <div style={{ flex: 1 }}><BarMini value={u.qtd} max={119} color={i < 3 ? COLORS.vitao : "#94A3B8"} height={10} /></div>
                    <span style={{ fontSize: 11, fontWeight: 700, color: COLORS.sub, width: 28, textAlign: "right" }}>{u.qtd}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ═══ TAB: OPERACIONAL ═══ */}
        {show("operacional") && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <SectionHeader title="MATRIZ TIPO CONTATO × RESULTADO" icon="📋" tag="BLOCO ORIGINAL" />
            <DataTable
              headers={["TIPO CONTATO", "TOTAL", ...matrixCols]}
              rows={[
                ...Object.entries(DATA.matrix).map(([tc, vals]) => {
                  const total = Object.values(vals).reduce((a, b) => a + b, 0);
                  return [tc, total, ...matrixCols.map(c => vals[c] || 0)];
                }),
                ["TOTAL", DATA.totalAtendimentos, ...matrixCols.map(c =>
                  Object.values(DATA.matrix).reduce((a, row) => a + (row[c] || 0), 0)
                )],
              ]}
              highlightCol={[1, 6]}
              compact
            />

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div>
                <SectionHeader title="POR TIPO DE CONTATO" icon="📞" />
                {DATA.tipoContato.map((tc, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <span style={{ fontSize: 10, fontWeight: 600, color: COLORS.text, width: 170, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{tc.tipo}</span>
                    <div style={{ flex: 1 }}><BarMini value={tc.total} max={123} color={COLORS.vitao} height={10} /></div>
                    <span style={{ fontSize: 11, fontWeight: 800, color: COLORS.text, width: 32, textAlign: "right" }}>{tc.total}</span>
                    <span style={{ fontSize: 10, color: COLORS.sub, width: 40, textAlign: "right" }}>
                      {((tc.total / DATA.totalAtendimentos) * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>

              <div>
                <SectionHeader title="POR RESULTADO" icon="🎯" />
                {DATA.resultado.map((r, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <span style={{ fontSize: 10, fontWeight: 600, color: COLORS.text, width: 140, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{r.res}</span>
                    <div style={{ flex: 1 }}><BarMini value={r.qtd} max={58} color={
                      r.res.includes("VENDA") ? COLORS.vitao : r.res.includes("PERDA") ? "#EF4444" : "#3B82F6"
                    } height={10} /></div>
                    <span style={{ fontSize: 11, fontWeight: 800, color: COLORS.text, width: 28, textAlign: "right" }}>{r.qtd}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ═══ TAB: FUNIL + CANAIS ═══ */}
        {show("funil") && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

            {/* Canais */}
            <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
              <SectionHeader title="CANAIS DE CONTATO" icon="📞" />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
                {[
                  { l: "WHATSAPP", v: DATA.canais.wpp, c: "#25D366", icon: "💬", pct: ((DATA.canais.wpp / DATA.totalAtendimentos) * 100).toFixed(0) },
                  { l: "LIGOU", v: DATA.canais.ligou, c: "#3B82F6", icon: "📱", pct: ((DATA.canais.ligou / DATA.totalAtendimentos) * 100).toFixed(0) },
                  { l: "ATENDIDA", v: DATA.canais.atendida, c: "#22C55E", icon: "✅", pct: DATA.canais.ligou > 0 ? ((DATA.canais.atendida / DATA.canais.ligou) * 100).toFixed(0) : 0 },
                  { l: "Ñ ATENDIDA", v: DATA.canais.nAtend, c: "#EF4444", icon: "❌", pct: DATA.canais.ligou > 0 ? ((DATA.canais.nAtend / DATA.canais.ligou) * 100).toFixed(0) : 0 },
                ].map((ch, i) => (
                  <div key={i} style={{
                    padding: 16, borderRadius: 12, textAlign: "center",
                    background: "#FAFBFC", borderLeft: `4px solid ${ch.c}`,
                  }}>
                    <div style={{ fontSize: 20 }}>{ch.icon}</div>
                    <div style={{ fontSize: 28, fontWeight: 900, color: ch.c }}>{ch.v}</div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: COLORS.text }}>{ch.l}</div>
                    <div style={{ fontSize: 10, color: COLORS.sub }}>{ch.pct}%{i < 2 ? " dos atendimentos" : " das ligações"}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Funil Visual */}
            <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
              <SectionHeader title="FUNIL DE VENDA" icon="📈" />
              <div style={{ display: "flex", flexDirection: "column", gap: 6, maxWidth: 600, margin: "0 auto" }}>
                {[
                  { etapa: "EM ATENDIMENTO", v: 47, c: "#6366F1" },
                  { etapa: "ORÇAMENTO", v: 53, c: "#F59E0B" },
                  { etapa: "CADASTRO", v: 18, c: "#8B5CF6" },
                  { etapa: "VENDA / PEDIDO", v: 48, c: COLORS.vitao },
                ].map((f, i) => {
                  const maxW = 100 - (i * 8);
                  return (
                    <div key={i} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                      <span style={{ fontSize: 10, fontWeight: 700, width: 130, textAlign: "right", color: COLORS.text }}>{f.etapa}</span>
                      <div style={{ flex: 1, display: "flex", justifyContent: "center" }}>
                        <div style={{
                          width: `${maxW}%`, height: 36, background: f.c, borderRadius: 6,
                          display: "flex", alignItems: "center", justifyContent: "center",
                          color: "#fff", fontWeight: 900, fontSize: 14,
                        }}>{f.v}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
              <div style={{ textAlign: "center", marginTop: 12, padding: "8px 16px", background: "#F0FDF4", borderRadius: 8 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: COLORS.vitao }}>
                  Conv. Orçamento→Venda: {((48 / 53) * 100).toFixed(0)}% · Conv. Geral: {DATA.convGeral}%
                </span>
              </div>
            </div>

            {/* Contatos por Rede */}
            <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
              <SectionHeader title="ATENDIMENTOS POR REDE" icon="🏪" />
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
                {DATA.redes.map((r, i) => (
                  <div key={i} style={{
                    padding: "10px 12px", borderRadius: 8, background: "#FAFBFC",
                    borderLeft: `3px solid ${i === 0 ? "#94A3B8" : COLORS.vitao}`,
                  }}>
                    <div style={{ fontSize: 10, fontWeight: 700, color: COLORS.text, marginBottom: 4 }}>{r.nome}</div>
                    <div style={{ fontSize: 20, fontWeight: 900, color: i === 0 ? "#64748B" : COLORS.vitao }}>{r.atend}</div>
                    <BarMini value={r.atend} max={155} color={i === 0 ? "#94A3B8" : COLORS.vitao} />
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ═══ TAB: PERFORMANCE ═══ */}
        {show("performance") && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <SectionHeader title="PERFORMANCE POR CONSULTOR" icon="👤" />

            <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 16 }}>
              {DATA.consultores.map((c, i) => {
                const conv = c.cont > 0 ? ((c.vend / c.cont) * 100).toFixed(1) : 0;
                return (
                  <div key={i} style={{
                    background: COLORS.card, borderRadius: 14, padding: 20,
                    border: `1px solid ${COLORS.border}`, borderTop: `4px solid ${[COLORS.vitao, "#3B82F6", "#F59E0B", "#8B5CF6"][i]}`,
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
                      <div>
                        <div style={{ fontSize: 14, fontWeight: 800, color: COLORS.text }}>{c.nome}</div>
                        <div style={{ fontSize: 10, color: COLORS.sub }}>Território: {c.terr}</div>
                      </div>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: 20, fontWeight: 900, color: [COLORS.vitao, "#3B82F6", "#F59E0B", "#8B5CF6"][i] }}>{conv}%</div>
                        <div style={{ fontSize: 9, color: COLORS.sub }}>CONVERSÃO</div>
                      </div>
                    </div>
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 6 }}>
                      {[
                        { l: "CONT", v: c.cont, c: "#64748B" },
                        { l: "VEND", v: c.vend, c: COLORS.vitao },
                        { l: "ORÇAM", v: c.orc, c: "#F59E0B" },
                        { l: "FUP", v: c.fup, c: "#3B82F6" },
                        { l: "SUP", v: c.sup, c: "#8B5CF6" },
                      ].map((m, j) => (
                        <div key={j} style={{ textAlign: "center", padding: "6px 4px", background: "#FAFBFC", borderRadius: 6 }}>
                          <div style={{ fontSize: 16, fontWeight: 900, color: m.c }}>{m.v}</div>
                          <div style={{ fontSize: 9, fontWeight: 600, color: COLORS.sub }}>{m.l}</div>
                        </div>
                      ))}
                    </div>
                    <div style={{ marginTop: 8 }}>
                      <BarMini value={c.cont} max={133} color={[COLORS.vitao, "#3B82F6", "#F59E0B", "#8B5CF6"][i]} height={6} />
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Ranking table */}
            <DataTable
              headers={["CONSULTOR", "CONTATOS", "VENDAS", "ORÇAM", "CADASTRO", "%CONV", "FUP", "SUPORTE"]}
              rows={[
                ...DATA.consultores.map(c => [
                  c.nome, c.cont, c.vend, c.orc, c.cad,
                  `${(c.cont > 0 ? (c.vend / c.cont * 100) : 0).toFixed(1)}%`,
                  c.fup, c.sup
                ]),
                ["TOTAL",
                  DATA.consultores.reduce((a, c) => a + c.cont, 0),
                  DATA.consultores.reduce((a, c) => a + c.vend, 0),
                  DATA.consultores.reduce((a, c) => a + c.orc, 0),
                  DATA.consultores.reduce((a, c) => a + c.cad, 0),
                  `${DATA.convGeral}%`,
                  DATA.consultores.reduce((a, c) => a + c.fup, 0),
                  DATA.consultores.reduce((a, c) => a + c.sup, 0),
                ],
              ]}
              highlightCol={[2, 5]}
            />
          </div>
        )}

        {/* ═══ TAB: SAÚDE DA BASE ═══ */}
        {show("saude") && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

            {/* Distribuição completa */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(6, 1fr)", gap: 12 }}>
              {[
                { l: "ATIVO", v: 152, c: COLORS.ativo, icon: "✅" },
                { l: "EM RISCO", v: 66, c: COLORS.risco, icon: "⚠️" },
                { l: "INAT.REC", v: 52, c: COLORS.inatRec, icon: "🟡" },
                { l: "INAT.ANT", v: 82, c: COLORS.inatAnt, icon: "🔴" },
                { l: "NOVO", v: 55, c: COLORS.novo, icon: "🆕" },
                { l: "PROSPECT", v: 34, c: COLORS.prospect, icon: "🔵" },
              ].map((s, i) => (
                <div key={i} style={{
                  background: COLORS.card, borderRadius: 12, padding: 16,
                  border: `1px solid ${COLORS.border}`, borderTop: `4px solid ${s.c}`,
                  textAlign: "center",
                }}>
                  <div style={{ fontSize: 20 }}>{s.icon}</div>
                  <div style={{ fontSize: 30, fontWeight: 900, color: s.c }}>{s.v}</div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.text }}>{s.l}</div>
                  <div style={{ fontSize: 10, color: COLORS.sub }}>
                    {((s.v / DATA.totalAtendimentos) * 100).toFixed(1)}% dos atend.
                  </div>
                </div>
              ))}
            </div>

            {/* Curva ABC detalhada */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
                <SectionHeader title="CURVA ABC — DISTRIBUIÇÃO" icon="📊" />
                {[
                  { curva: "A", v: 190, d: "Responsáveis por ~80% da receita", c: "#22C55E" },
                  { curva: "B", v: 155, d: "Responsáveis por ~15% da receita", c: "#F59E0B" },
                  { curva: "C", v: 113, d: "Responsáveis por ~5% da receita", c: "#EF4444" },
                ].map((ab, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10, padding: "10px 12px", background: "#FAFBFC", borderRadius: 8 }}>
                    <div style={{ width: 40, height: 40, borderRadius: 8, background: ab.c, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 900, fontSize: 18 }}>{ab.curva}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.text }}>{ab.v} clientes ({((ab.v / 458) * 100).toFixed(0)}%)</div>
                      <div style={{ fontSize: 10, color: COLORS.sub }}>{ab.d}</div>
                      <BarMini value={ab.v} max={190} color={ab.c} height={6} />
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
                <SectionHeader title="TAXA DE RECOMPRA — DETALHADO" icon="🔁" />
                {[
                  { l: "1 COMPRA", v: 213, c: "#EF4444", pct: ((213 / totalRecompra) * 100).toFixed(1) },
                  { l: "2-3 COMPRAS", v: 117, c: "#F59E0B", pct: ((117 / totalRecompra) * 100).toFixed(1) },
                  { l: "4-6 COMPRAS", v: 46, c: "#22C55E", pct: ((46 / totalRecompra) * 100).toFixed(1) },
                  { l: "7+ COMPRAS", v: 8, c: "#3B82F6", pct: ((8 / totalRecompra) * 100).toFixed(1) },
                ].map((r, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 10, padding: "10px 12px", background: "#FAFBFC", borderRadius: 8 }}>
                    <div style={{ width: 40, textAlign: "center" }}>
                      <div style={{ fontSize: 18, fontWeight: 900, color: r.c }}>{r.v}</div>
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.text }}>{r.l} ({r.pct}%)</div>
                      <BarMini value={r.v} max={213} color={r.c} height={8} />
                    </div>
                  </div>
                ))}
                <div style={{ marginTop: 8, fontSize: 10, color: COLORS.sub, textAlign: "center" }}>
                  Taxa recompra (2+ compras): <b style={{ color: COLORS.vitao }}>{((totalRecompra - 213) / totalRecompra * 100).toFixed(1)}%</b> — Meta: 40%+
                </div>
              </div>
            </div>

            {/* Alertas */}
            <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
              <SectionHeader title="PIPELINE DE INATIVIDADE — DIAS SEM COMPRA" icon="⏰" />
              <div style={{ display: "flex", gap: 0, borderRadius: 10, overflow: "hidden", height: 60 }}>
                {[
                  { l: "< 45d", v: DATA.alertas.ate45, c: COLORS.ativo, t: "SAUDÁVEL" },
                  { l: "45-59d", v: DATA.alertas.de45a59, c: "#F59E0B", t: "ALERTA" },
                  { l: "60-89d", v: DATA.alertas.de60a89, c: "#FF6600", t: "RISCO" },
                  { l: "90+ d", v: DATA.alertas.acima90, c: COLORS.inatAnt, t: "INATIVO" },
                ].map((s, i) => {
                  const total = DATA.alertas.ate45 + DATA.alertas.de45a59 + DATA.alertas.de60a89 + DATA.alertas.acima90;
                  const pct = (s.v / total) * 100;
                  return (
                    <div key={i} style={{
                      width: `${pct}%`, background: s.c, display: "flex",
                      flexDirection: "column", alignItems: "center", justifyContent: "center",
                      color: "#fff", minWidth: pct > 5 ? 60 : 30,
                    }}>
                      <div style={{ fontSize: 16, fontWeight: 900 }}>{s.v}</div>
                      <div style={{ fontSize: 8, fontWeight: 600 }}>{s.t}</div>
                    </div>
                  );
                })}
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: 6 }}>
                <span style={{ fontSize: 9, color: COLORS.sub }}>← Saudável</span>
                <span style={{ fontSize: 9, color: COLORS.sub }}>Inativo →</span>
              </div>
            </div>
          </div>
        )}

        {/* ═══ TAB: REDES + SINALEIRO ═══ */}
        {show("redes") && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <SectionHeader title="SINALEIRO DE PENETRAÇÃO — REDES DE FRANQUIA" icon="🚦" tag="923 LOJAS · 7 REDES" />
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 }}>
              {DATA.sinaleiro.sort((a, b) => b.pct - a.pct).map((r, i) => {
                const emoji = r.pct >= 50 ? "🟢" : r.pct >= 25 ? "🟡" : "🔴";
                return (
                  <div key={i} style={{
                    background: COLORS.card, borderRadius: 12, padding: 16,
                    border: `1px solid ${COLORS.border}`,
                    borderLeft: `4px solid ${r.pct >= 50 ? "#22C55E" : r.pct >= 25 ? "#F59E0B" : "#EF4444"}`,
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                      <span style={{ fontSize: 12, fontWeight: 800, color: COLORS.text }}>{r.rede}</span>
                      <span style={{ fontSize: 16 }}>{emoji}</span>
                    </div>
                    <div style={{ fontSize: 24, fontWeight: 900, color: COLORS.text }}>
                      {r.clientes}<span style={{ fontSize: 14, fontWeight: 400, color: COLORS.sub }}>/{r.total}</span>
                    </div>
                    <BarMini value={r.pct} max={100} color={r.pct >= 50 ? "#22C55E" : r.pct >= 25 ? "#F59E0B" : "#EF4444"} height={8} />
                    <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.sub, marginTop: 4 }}>{r.pct}% penetração</div>
                    <div style={{ fontSize: 9, color: COLORS.sub }}>Oportunidade: {r.total - r.clientes} lojas</div>
                  </div>
                );
              })}
            </div>

            {/* Resumo Redes */}
            <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
              <SectionHeader title="ATENDIMENTOS POR REDE — DETALHADO" icon="🏪" />
              <DataTable
                headers={["REDE", "ATENDIMENTOS", "% DO TOTAL", "BARRA"]}
                rows={[
                  ...DATA.redes.map(r => [
                    r.nome, r.atend, `${((r.atend / DATA.totalAtendimentos) * 100).toFixed(1)}%`, ""
                  ]),
                  ["TOTAL", DATA.totalAtendimentos, "100%", ""],
                ]}
                highlightCol={[1]}
              />
            </div>
          </div>
        )}

        {/* ═══ TAB: MOTIVOS + RNC ═══ */}
        {show("motivos") && (
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>

              {/* Motivos */}
              <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
                <SectionHeader title="MOTIVOS DE NÃO COMPRA" icon="📝" />
                {DATA.motivos.map((m, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                    <span style={{ fontSize: 10, fontWeight: 600, color: COLORS.text, width: 200, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{m.motivo}</span>
                    <div style={{ flex: 1 }}><BarMini value={m.qtd} max={43} color={i < 3 ? "#EF4444" : "#F59E0B"} height={8} /></div>
                    <span style={{ fontSize: 11, fontWeight: 800, color: COLORS.text, width: 28, textAlign: "right" }}>{m.qtd}</span>
                    <span style={{ fontSize: 10, color: COLORS.sub, width: 36, textAlign: "right" }}>
                      {((m.qtd / totalMotivos) * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
                <div style={{ marginTop: 12, padding: "8px 12px", background: "#FEF2F2", borderRadius: 8 }}>
                  <span style={{ fontSize: 10, fontWeight: 700, color: "#B91C1C" }}>
                    Top 3 motivos = {((DATA.motivos[0].qtd + DATA.motivos[1].qtd + DATA.motivos[2].qtd) / totalMotivos * 100).toFixed(0)}% das recusas
                  </span>
                </div>
              </div>

              {/* RNC */}
              <div style={{ background: COLORS.card, borderRadius: 14, padding: 20, border: `1px solid ${COLORS.border}` }}>
                <SectionHeader title="RNC — REGISTRO DE NÃO CONFORMIDADES" icon="🚨" />
                {[
                  { prob: "ATRASO ENTREGA", area: "TRANSPORTADORA", icon: "🚛" },
                  { prob: "PRODUTO AVARIADO", area: "FÁBRICA/TRANSPORTE", icon: "📦" },
                  { prob: "ERRO SEPARAÇÃO", area: "EXPEDIÇÃO", icon: "🏭" },
                  { prob: "ERRO NOTA FISCAL", area: "FATURAMENTO", icon: "📄" },
                  { prob: "DIVERGÊNCIA PREÇO", area: "FATURAMENTO", icon: "💲" },
                  { prob: "COBRANÇA INDEVIDA", area: "FINANCEIRO", icon: "🏦" },
                  { prob: "RUPTURA ESTOQUE", area: "PCP", icon: "📋" },
                ].map((r, i) => (
                  <div key={i} style={{
                    display: "flex", alignItems: "center", gap: 10, padding: "8px 10px",
                    marginBottom: 4, background: "#FAFBFC", borderRadius: 8,
                    borderLeft: `3px solid ${i < 2 ? "#EF4444" : i < 4 ? "#F59E0B" : "#94A3B8"}`,
                  }}>
                    <span style={{ fontSize: 16 }}>{r.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 11, fontWeight: 700, color: COLORS.text }}>{r.prob}</div>
                      <div style={{ fontSize: 9, color: COLORS.sub }}>Área: {r.area}</div>
                    </div>
                    <span style={{
                      fontSize: 9, fontWeight: 700, padding: "2px 8px", borderRadius: 10,
                      background: i < 2 ? "#FEE2E2" : "#F3F4F6", color: i < 2 ? "#B91C1C" : "#6B7280",
                    }}>
                      {i < 2 ? "CRÍTICO" : "MONITORAR"}
                    </span>
                  </div>
                ))}
                <div style={{ marginTop: 12, padding: "8px 12px", background: "#FFFBEB", borderRadius: 8 }}>
                  <span style={{ fontSize: 10, fontWeight: 700, color: "#92400E" }}>
                    ⚠️ RNCs são problemas de OUTRAS áreas resolvidos pelo comercial — impactam retenção
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ═══ FOOTER ═══ */}
        <div style={{
          marginTop: 24, padding: "12px 20px", background: COLORS.card,
          borderRadius: 10, border: `1px solid ${COLORS.border}`,
          display: "flex", justifyContent: "space-between", alignItems: "center",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <div style={{ background: COLORS.vitao, padding: "2px 8px", borderRadius: 4, color: "#fff", fontSize: 11, fontWeight: 900 }}>VITAO 360</div>
            <span style={{ fontSize: 10, color: COLORS.sub }}>CRM INTELIGENTE V11 · Dashboard Final Consolidado</span>
          </div>
          <div style={{ fontSize: 10, color: COLORS.sub }}>
            14 blocos (9 originais + 5 estratégicos) · Dados: DRAFT 1 + DRAFT 2 · 16/FEV/2026
          </div>
        </div>
      </div>
    </div>
  );
}
