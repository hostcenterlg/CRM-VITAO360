'use client';

import { useState, useEffect } from 'react';
import { fetchMotorRegras, RegraMotor } from '@/lib/api';

// ---------------------------------------------------------------------------
// Admin Motor — visualizacao read-only das regras do Motor v4
// Acesso exclusivo: role=admin (P1 Leandro)
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Cores temperatura
// ---------------------------------------------------------------------------

const TEMP_COLORS: Record<string, { bg: string; text: string }> = {
  QUENTE:  { bg: '#EF4444', text: '#fff' },
  MORNO:   { bg: '#F97316', text: '#fff' },
  FRIO:    { bg: '#60A5FA', text: '#fff' },
  CRITICO: { bg: '#7030A0', text: '#fff' },
  PERDIDO: { bg: '#6B7280', text: '#fff' },
};

const SITUACAO_COLORS: Record<string, { bg: string; text: string }> = {
  ATIVO:       { bg: '#00B050', text: '#fff' },
  'EM RISCO':  { bg: '#F97316', text: '#fff' },
  'INAT.REC':  { bg: '#FFC000', text: '#1a1a1a' },
  'INAT.ANT':  { bg: '#FF0000', text: '#fff' },
  PROSPECT:    { bg: '#3B82F6', text: '#fff' },
  LEAD:        { bg: '#8B5CF6', text: '#fff' },
  NOVO:        { bg: '#06B6D4', text: '#fff' },
};

function SitBadge({ value }: { value: string }) {
  const cfg = SITUACAO_COLORS[value] ?? { bg: '#e5e7eb', text: '#374151' };
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded uppercase"
      style={{ backgroundColor: cfg.bg, color: cfg.text }}
    >
      {value}
    </span>
  );
}

function TempCell({ value }: { value: string }) {
  const cfg = TEMP_COLORS[value] ?? { bg: '#e5e7eb', text: '#374151' };
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded uppercase"
      style={{ backgroundColor: cfg.bg, color: cfg.text }}
    >
      {value}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Pagina
// ---------------------------------------------------------------------------

export default function AdminMotorPage() {
  const [regras, setRegras] = useState<RegraMotor[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filtroSituacao, setFiltroSituacao] = useState('');

  useEffect(() => {
    setLoading(true);
    setError(null);
    fetchMotorRegras()
      .then(data => setRegras(data))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const situacoes = Array.from(new Set(regras.map(r => r.situacao))).sort();

  const regrasFiltradas = filtroSituacao
    ? regras.filter(r => r.situacao === filtroSituacao)
    : regras;

  return (
    <div className="space-y-5">
      {/* Titulo */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-lg font-bold text-gray-900">Motor de Regras v4</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            {regras.length} combinacoes — visualizacao somente leitura
          </p>
        </div>
        <span className="px-3 py-1.5 text-[10px] font-bold text-gray-600 bg-gray-100 border border-gray-200 rounded uppercase tracking-wide">
          READ ONLY
        </span>
      </div>

      {/* Aviso L3 */}
      <div className="flex items-start gap-3 p-4 bg-amber-50 border border-amber-200 rounded-lg">
        <svg className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <div>
          <p className="text-xs font-semibold text-amber-800">Somente Leitura — Decisao L3</p>
          <p className="text-xs text-amber-700 mt-0.5">
            Alteracoes no Motor requerem aprovacao de Leandro (nivel L3).
            Esta tela exibe as regras atuais. Para propor mudancas, abrir chamado formal.
          </p>
        </div>
      </div>

      {/* Erro */}
      {error && (
        <div role="alert" className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
          Erro ao carregar regras: {error}
        </div>
      )}

      {/* Filtro */}
      <div className="bg-white rounded-xl border border-gray-200 p-4">
        <div className="flex items-center gap-3">
          <select
            value={filtroSituacao}
            onChange={e => setFiltroSituacao(e.target.value)}
            aria-label="Filtrar por situacao"
            className={`h-8 px-3 text-xs border rounded focus:outline-none focus:ring-2 focus:ring-green-500 bg-white ${filtroSituacao ? 'border-green-500 bg-green-50' : 'border-gray-300'}`}
          >
            <option value="">Todas as situacoes</option>
            {situacoes.map(s => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
          {filtroSituacao && (
            <button
              type="button"
              onClick={() => setFiltroSituacao('')}
              className="text-xs text-gray-500 hover:text-gray-900"
            >
              Limpar
            </button>
          )}
          <span className="text-xs text-gray-400 ml-auto">
            {regrasFiltradas.length} regras exibidas
          </span>
        </div>
      </div>

      {/* Tabela */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-5 h-5 border-2 border-gray-300 border-t-green-600 rounded-full animate-spin" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full" role="table">
              <caption className="sr-only">
                {regras.length} regras do Motor de Inteligencia Comercial
              </caption>
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th scope="col" className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide w-8">#</th>
                  <th scope="col" className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Situacao</th>
                  <th scope="col" className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Resultado</th>
                  <th scope="col" className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Estagio Funil</th>
                  <th scope="col" className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Fase</th>
                  <th scope="col" className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Tipo Contato</th>
                  <th scope="col" className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide min-w-[200px]">Acao Futura</th>
                  <th scope="col" className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Temp.</th>
                  <th scope="col" className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">FU (dias)</th>
                  <th scope="col" className="px-3 py-2.5 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wide">Tipo Acao</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {regrasFiltradas.length === 0 ? (
                  <tr>
                    <td colSpan={10} className="px-4 py-10 text-center text-xs text-gray-400">
                      {error ? 'Erro ao carregar regras.' : 'Nenhuma regra encontrada.'}
                    </td>
                  </tr>
                ) : (
                  regrasFiltradas.map(regra => (
                    <tr key={regra.id} className="hover:bg-green-50/40 transition-colors">
                      <td className="px-3 py-2 text-[10px] text-gray-400 tabular-nums">{regra.id}</td>
                      <td className="px-3 py-2">
                        <SitBadge value={regra.situacao} />
                      </td>
                      <td className="px-3 py-2 text-xs text-gray-700 font-medium">{regra.resultado}</td>
                      <td className="px-3 py-2 text-xs text-gray-600">{regra.estagio_funil}</td>
                      <td className="px-3 py-2 text-xs text-gray-600">{regra.fase}</td>
                      <td className="px-3 py-2 text-xs text-gray-500">{regra.tipo_contato}</td>
                      <td className="px-3 py-2 text-xs text-gray-700 max-w-xs break-words whitespace-normal">{regra.acao_futura}</td>
                      <td className="px-3 py-2">
                        <TempCell value={regra.temperatura} />
                      </td>
                      <td className="px-3 py-2 text-xs text-gray-700 tabular-nums text-center">
                        {regra.follow_up_dias ?? '—'}
                      </td>
                      <td className="px-3 py-2 text-xs text-gray-500 font-mono">{regra.tipo_acao}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
            <div className="px-4 py-3 border-t border-gray-100 text-xs text-gray-500">
              {regrasFiltradas.length} de {regras.length} regras exibidas
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
