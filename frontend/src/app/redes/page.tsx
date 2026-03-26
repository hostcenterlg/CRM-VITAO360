'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { fetchJson } from '@/lib/api-internal';
import { formatBRL } from '@/lib/api';

// ---------------------------------------------------------------------------
// Tela Redes — sinaleiro por rede/franquia com accordion drill-down
// Acesso: admin + gerente
// ---------------------------------------------------------------------------

interface LojaRede {
  cnpj: string;
  nome: string;
  cidade: string;
  uf: string;
  fat_real: number;
  meta: number;
  pct_ating: number;
  cor: string;
}

interface RedeItem {
  nome: string;
  consultor: string;
  total_lojas: number;
  fat_real: number;
  meta: number;
  pct_ating: number;
  gap: number;
  cor: string;
  distribuicao: { VERDE: number; AMARELO: number; VERMELHO: number; ROXO: number };
  lojas: LojaRede[];
}

interface RedesResponse {
  total_redes: number;
  total_lojas: number;
  redes: RedeItem[];
}

// ---------------------------------------------------------------------------
// Mock data
// ---------------------------------------------------------------------------

function getMockRedes(): RedesResponse {
  const fitlandLojas: LojaRede[] = [
    { cnpj: '12345678000101', nome: 'Fitland SP 01', cidade: 'Sao Paulo', uf: 'SP', fat_real: 8500, meta: 12000, pct_ating: 71, cor: 'AMARELO' },
    { cnpj: '12345678000202', nome: 'Fitland SP 02', cidade: 'Campinas',  uf: 'SP', fat_real: 2100, meta: 12000, pct_ating: 18, cor: 'VERMELHO' },
    { cnpj: '12345678000303', nome: 'Fitland RJ 01', cidade: 'Rio de Janeiro', uf: 'RJ', fat_real: 9800, meta: 10000, pct_ating: 98, cor: 'VERDE' },
    { cnpj: '12345678000404', nome: 'Fitland PR 01', cidade: 'Curitiba', uf: 'PR', fat_real: 0, meta: 12000, pct_ating: 0, cor: 'ROXO' },
    { cnpj: '12345678000505', nome: 'Fitland MG 01', cidade: 'Belo Horizonte', uf: 'MG', fat_real: 5200, meta: 10000, pct_ating: 52, cor: 'AMARELO' },
    { cnpj: '12345678000606', nome: 'Fitland RS 01', cidade: 'Porto Alegre', uf: 'RS', fat_real: 11000, meta: 12000, pct_ating: 92, cor: 'VERDE' },
    { cnpj: '12345678000707', nome: 'Fitland SC 01', cidade: 'Florianopolis', uf: 'SC', fat_real: 1500, meta: 10000, pct_ating: 15, cor: 'VERMELHO' },
    { cnpj: '12345678000808', nome: 'Fitland BA 01', cidade: 'Salvador', uf: 'BA', fat_real: 7800, meta: 10000, pct_ating: 78, cor: 'AMARELO' },
  ];

  const ciaSaudeLojas: LojaRede[] = [
    { cnpj: '98765432000101', nome: 'Cia Saude SP 01', cidade: 'Sao Paulo', uf: 'SP', fat_real: 4500, meta: 11000, pct_ating: 41, cor: 'VERMELHO' },
    { cnpj: '98765432000202', nome: 'Cia Saude SP 02', cidade: 'Santos', uf: 'SP', fat_real: 800, meta: 11000, pct_ating: 7, cor: 'VERMELHO' },
    { cnpj: '98765432000303', nome: 'Cia Saude RJ 01', cidade: 'Rio de Janeiro', uf: 'RJ', fat_real: 0, meta: 10900, pct_ating: 0, cor: 'ROXO' },
    { cnpj: '98765432000404', nome: 'Cia Saude MG 01', cidade: 'Uberlandia', uf: 'MG', fat_real: 12000, meta: 10900, pct_ating: 110, cor: 'VERDE' },
    { cnpj: '98765432000505', nome: 'Cia Saude PR 01', cidade: 'Curitiba', uf: 'PR', fat_real: 3200, meta: 10900, pct_ating: 29, cor: 'VERMELHO' },
  ];

  const calcDist = (lojas: LojaRede[]) => ({
    VERDE: lojas.filter(l => l.cor === 'VERDE').length,
    AMARELO: lojas.filter(l => l.cor === 'AMARELO').length,
    VERMELHO: lojas.filter(l => l.cor === 'VERMELHO').length,
    ROXO: lojas.filter(l => l.cor === 'ROXO').length,
  });

  const fatFitland = fitlandLojas.reduce((s, l) => s + l.fat_real, 0);
  const metaFitland = 58 * 10700;
  const fatCia = ciaSaudeLojas.reduce((s, l) => s + l.fat_real, 0);
  const metaCia = 72 * 10880;

  return {
    total_redes: 2,
    total_lojas: 130,
    redes: [
      {
        nome: 'FITLAND',
        consultor: 'JULIO',
        total_lojas: 58,
        fat_real: fatFitland,
        meta: metaFitland,
        pct_ating: Math.round((fatFitland / metaFitland) * 100 * 10) / 10,
        gap: fatFitland - metaFitland,
        cor: 'VERMELHO',
        distribuicao: calcDist(fitlandLojas),
        lojas: fitlandLojas,
      },
      {
        nome: 'CIA SAUDE',
        consultor: 'JULIO',
        total_lojas: 72,
        fat_real: fatCia,
        meta: metaCia,
        pct_ating: Math.round((fatCia / metaCia) * 100 * 10) / 10,
        gap: fatCia - metaCia,
        cor: 'VERMELHO',
        distribuicao: calcDist(ciaSaudeLojas),
        lojas: ciaSaudeLojas,
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// Helpers visuais
// ---------------------------------------------------------------------------

const COR_COLORS: Record<string, { bg: string; text: string; sigla: string }> = {
  VERDE:    { bg: '#00B050', text: '#fff',    sigla: 'V' },
  AMARELO:  { bg: '#FFC000', text: '#1a1a1a', sigla: 'A' },
  VERMELHO: { bg: '#FF0000', text: '#fff',    sigla: 'Vm' },
  ROXO:     { bg: '#7030A0', text: '#fff',    sigla: 'Rx' },
};

function CorBadge({ cor }: { cor: string }) {
  const cfg = COR_COLORS[cor] ?? { bg: '#e5e7eb', text: '#374151', sigla: '?' };
  return (
    <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded uppercase"
      style={{ backgroundColor: cfg.bg, color: cfg.text }}>
      {cor}
    </span>
  );
}

function ProgressBar({ pct }: { pct: number }) {
  const color = pct >= 100 ? '#00B050' : pct >= 80 ? '#FFC000' : pct >= 50 ? '#FF6600' : '#FF0000';
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all"
          style={{ width: `${Math.min(pct, 100)}%`, backgroundColor: color }}
        />
      </div>
      <span className="text-[10px] font-semibold tabular-nums" style={{ color }}>
        {pct.toFixed(1)}%
      </span>
    </div>
  );
}

function DistribuicaoMini({ dist }: { dist: RedeItem['distribuicao'] }) {
  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {Object.entries(dist).map(([cor, qtd]) => {
        if (qtd === 0) return null;
        const cfg = COR_COLORS[cor];
        return (
          <span key={cor} className="flex items-center gap-0.5">
            <span className="inline-block w-2 h-2 rounded-full" style={{ backgroundColor: cfg.bg }} />
            <span className="text-[10px] text-gray-600">{qtd}{cfg.sigla}</span>
          </span>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pagina
// ---------------------------------------------------------------------------

export default function RedesPage() {
  const router = useRouter();
  const [data, setData] = useState<RedesResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandida, setExpandida] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetchJson<RedesResponse>('/api/redes');
      setData(res);
    } catch {
      setData(getMockRedes());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  function toggleRede(nome: string) {
    setExpandida(prev => prev === nome ? null : nome);
  }

  const redes = data?.redes ?? [];
  const criticas = redes.filter(r => r.pct_ating < 40);

  return (
    <div className="space-y-5">
      {/* Titulo */}
      <div>
        <h1 className="text-lg font-bold text-gray-900">Redes e Franquias</h1>
        <p className="text-xs text-gray-500 mt-0.5">
          {data?.total_redes ?? 0} redes | {data?.total_lojas ?? 0} lojas
        </p>
      </div>

      {/* Alerta redes criticas */}
      {criticas.length > 0 && (
        <div className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
          <svg className="w-4 h-4 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          <p className="text-xs font-semibold text-red-800">
            {criticas.length} rede{criticas.length > 1 ? 's' : ''} critica{criticas.length > 1 ? 's' : ''} (abaixo de 40%):
            {' '}{criticas.map(r => r.nome).join(', ')}
          </p>
        </div>
      )}

      {/* Tabela principal */}
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-5 h-5 border-2 border-gray-300 border-t-green-600 rounded-full animate-spin" />
          </div>
        ) : redes.length === 0 ? (
          <div className="flex items-center justify-center py-16">
            <p className="text-xs text-gray-400">Nenhuma rede cadastrada.</p>
          </div>
        ) : (
          <div>
            {/* Header tabela */}
            <div className="border-b border-gray-200 bg-gray-50 px-4 py-2.5 grid grid-cols-9 gap-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wide">
              <span className="col-span-2">Rede</span>
              <span>Consultor</span>
              <span className="text-right">Lojas</span>
              <span className="text-right">Fat Real</span>
              <span className="text-right">Meta</span>
              <span className="col-span-2">% Ating</span>
              <span className="text-right">Gap</span>
            </div>

            {redes.map(rede => {
              const isExpanded = expandida === rede.nome;
              const isCritica = rede.pct_ating < 40;

              return (
                <div key={rede.nome}>
                  {/* Linha da rede */}
                  <button
                    type="button"
                    onClick={() => toggleRede(rede.nome)}
                    className="w-full px-4 py-3 grid grid-cols-9 gap-3 items-center hover:bg-gray-50 transition-colors text-left focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-inset"
                    style={{ backgroundColor: isCritica ? '#FEF2F2' : undefined }}
                    aria-expanded={isExpanded}
                    aria-controls={`rede-lojas-${rede.nome}`}
                  >
                    {/* Nome + chevron */}
                    <div className="col-span-2 flex items-center gap-2">
                      <svg
                        className="w-3.5 h-3.5 text-gray-400 flex-shrink-0 transition-transform"
                        style={{ transform: isExpanded ? 'rotate(90deg)' : 'rotate(0deg)' }}
                        fill="none" stroke="currentColor" viewBox="0 0 24 24"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                      <div>
                        <span className="text-xs font-semibold text-gray-900">{rede.nome}</span>
                        {isCritica && (
                          <span className="ml-1.5 text-[10px] font-bold text-red-600">CRITICA</span>
                        )}
                      </div>
                    </div>

                    <span className="text-xs text-gray-600">{rede.consultor}</span>
                    <span className="text-xs text-gray-700 text-right tabular-nums">{rede.total_lojas}</span>
                    <span className="text-xs text-gray-900 font-medium text-right tabular-nums">{formatBRL(rede.fat_real)}</span>
                    <span className="text-xs text-gray-600 text-right tabular-nums">{formatBRL(rede.meta)}</span>

                    {/* Barra progresso */}
                    <div className="col-span-2">
                      <ProgressBar pct={rede.pct_ating} />
                    </div>

                    {/* Gap */}
                    <span
                      className="text-xs text-right tabular-nums font-medium"
                      style={{ color: rede.gap >= 0 ? '#00B050' : '#DC2626' }}
                    >
                      {rede.gap >= 0 ? '+' : ''}{formatBRL(rede.gap)}
                    </span>
                  </button>

                  {/* Distribuicao por cor (mini-barras) */}
                  <div className="px-4 pb-2 flex items-center gap-2">
                    <span className="text-[10px] text-gray-400">Distribuicao:</span>
                    <DistribuicaoMini dist={rede.distribuicao} />
                    <div className="ml-auto">
                      <CorBadge cor={rede.cor} />
                    </div>
                  </div>

                  {/* Accordion — lista de lojas */}
                  {isExpanded && (
                    <div
                      id={`rede-lojas-${rede.nome}`}
                      className="border-t border-gray-100 bg-gray-50"
                    >
                      {/* Header lojas */}
                      <div className="px-10 py-2 grid grid-cols-8 gap-3 text-[10px] font-semibold text-gray-400 uppercase tracking-wide">
                        <span className="col-span-2">CNPJ</span>
                        <span className="col-span-2">Nome Loja</span>
                        <span>Cidade</span>
                        <span className="text-right">Fat Real</span>
                        <span className="text-right">Meta</span>
                        <span>% / Cor</span>
                      </div>

                      {rede.lojas.map(loja => (
                        <button
                          key={loja.cnpj}
                          type="button"
                          onClick={() => router.push(`/clientes/${loja.cnpj}`)}
                          className="w-full px-10 py-2 grid grid-cols-8 gap-3 items-center hover:bg-white transition-colors text-left focus:outline-none focus:ring-1 focus:ring-green-500 focus:ring-inset cursor-pointer"
                        >
                          <span className="col-span-2 text-[10px] font-mono text-gray-500">{loja.cnpj}</span>
                          <span className="col-span-2 text-xs text-gray-800">{loja.nome}</span>
                          <span className="text-xs text-gray-600">{loja.cidade}/{loja.uf}</span>
                          <span className="text-xs text-gray-900 text-right tabular-nums">{formatBRL(loja.fat_real)}</span>
                          <span className="text-xs text-gray-500 text-right tabular-nums">{formatBRL(loja.meta)}</span>
                          <div className="flex items-center gap-2">
                            <span
                              className="text-[10px] font-semibold tabular-nums"
                              style={{
                                color: loja.pct_ating >= 100 ? '#00B050'
                                  : loja.pct_ating >= 80 ? '#FFC000'
                                  : loja.pct_ating >= 50 ? '#FF6600'
                                  : '#FF0000'
                              }}
                            >
                              {loja.pct_ating}%
                            </span>
                            <CorBadge cor={loja.cor} />
                          </div>
                        </button>
                      ))}

                      {/* Rodape distribuicao */}
                      <div className="px-10 py-2 border-t border-gray-100 flex items-center gap-2">
                        <span className="text-[10px] text-gray-400">Total lojas: {rede.total_lojas}</span>
                        <span className="text-[10px] text-gray-300">|</span>
                        <DistribuicaoMini dist={rede.distribuicao} />
                      </div>
                    </div>
                  )}

                  <div className="border-b border-gray-100" />
                </div>
              );
            })}
          </div>
        )}
      </div>

      <p className="text-[10px] text-gray-400">
        Click numa rede para expandir a lista de lojas. Click numa loja para abrir a ficha do cliente.
        Redes com % atingimento abaixo de 40% sao destacadas como CRITICAS.
      </p>
    </div>
  );
}
