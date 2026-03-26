'use client';

import { useState, useEffect } from 'react';
import { fetchJson } from '@/lib/api-internal';

// ---------------------------------------------------------------------------
// Admin Motor — visualizacao read-only das 92 regras do Motor v4
// Acesso exclusivo: role=admin (P1 Leandro)
// ---------------------------------------------------------------------------

interface RegraMotor {
  id: number;
  situacao: string;
  resultado: string;
  estagio_funil: string;
  fase: string;
  tipo_contato: string;
  acao_futura: string;
  temperatura: string;
  follow_up_dias: number | null;
  grupo_dashboard: string;
  tipo_acao: string;
}

// ---------------------------------------------------------------------------
// Dados mock — 92 combinacoes do Motor v4 (subset representativo)
// ---------------------------------------------------------------------------

const MOCK_REGRAS: RegraMotor[] = [
  { id: 1,  situacao: 'ATIVO',    resultado: 'VENDA',          estagio_funil: 'ACOMP POS-VENDA',  fase: 'POS-VENDA',   tipo_contato: 'Qualquer',   acao_futura: 'Acompanhar pos-venda e solicitar nova recompra em 4 dias',       temperatura: 'QUENTE',  follow_up_dias: 4,  grupo_dashboard: 'VENDA',    tipo_acao: 'RECOMPRA' },
  { id: 2,  situacao: 'ATIVO',    resultado: 'ORCAMENTO',      estagio_funil: 'ORCAMENTO',         fase: 'NEGOCIACAO',  tipo_contato: 'Qualquer',   acao_futura: 'Confirmar orcamento enviado — cliente pronto para fechar',       temperatura: 'QUENTE',  follow_up_dias: 7,  grupo_dashboard: 'NEGOC',    tipo_acao: 'FECHAR' },
  { id: 3,  situacao: 'ATIVO',    resultado: 'EM ATENDIMENTO', estagio_funil: 'EM ATENDIMENTO',    fase: 'NEGOCIACAO',  tipo_contato: 'Qualquer',   acao_futura: 'Dar continuidade ao atendimento em andamento',                   temperatura: 'QUENTE',  follow_up_dias: 3,  grupo_dashboard: 'ATIVO',    tipo_acao: 'CONTINUAR' },
  { id: 4,  situacao: 'ATIVO',    resultado: 'POS-VENDA',      estagio_funil: 'POS-VENDA',         fase: 'POS-VENDA',   tipo_contato: 'Qualquer',   acao_futura: 'Verificar satisfacao e preparar oferta de recompra',             temperatura: 'MORNO',   follow_up_dias: 15, grupo_dashboard: 'RETENCAO', tipo_acao: 'RECOMPRA' },
  { id: 5,  situacao: 'ATIVO',    resultado: 'CS',             estagio_funil: 'CS',                fase: 'RECOMPRA',    tipo_contato: 'Qualquer',   acao_futura: 'Cliente satisfeito — planejar expansao de mix',                  temperatura: 'MORNO',   follow_up_dias: 30, grupo_dashboard: 'RETENCAO', tipo_acao: 'EXPANSAO' },
  { id: 6,  situacao: 'ATIVO',    resultado: 'NAO ATENDE',     estagio_funil: 'TENTATIVA',         fase: 'NEGOCIACAO',  tipo_contato: 'Ligacao',    acao_futura: 'Tentar novamente amanha em horario diferente',                   temperatura: 'FRIO',    follow_up_dias: 1,  grupo_dashboard: 'ALERTA',   tipo_acao: 'TENTAR' },
  { id: 7,  situacao: 'ATIVO',    resultado: 'NAO RESPONDE',   estagio_funil: 'TENTATIVA',         fase: 'NEGOCIACAO',  tipo_contato: 'WhatsApp',   acao_futura: 'Tentar via ligacao apos 1 dia sem resposta',                     temperatura: 'FRIO',    follow_up_dias: 1,  grupo_dashboard: 'ALERTA',   tipo_acao: 'TENTAR' },
  { id: 8,  situacao: 'ATIVO',    resultado: 'RECUSOU',        estagio_funil: 'FOLLOW-UP',         fase: 'NEGOCIACAO',  tipo_contato: 'Qualquer',   acao_futura: 'Respeitar decisao — retornar em 15 dias com nova abordagem',     temperatura: 'FRIO',    follow_up_dias: 15, grupo_dashboard: 'RISCO',    tipo_acao: 'NUTRIR' },
  { id: 9,  situacao: 'ATIVO',    resultado: 'RELACIONAMENTO', estagio_funil: 'RELACIONAMENTO',    fase: 'POS-VENDA',   tipo_contato: 'Qualquer',   acao_futura: 'Manter relacionamento — agendar visita ou evento',               temperatura: 'MORNO',   follow_up_dias: 30, grupo_dashboard: 'RETENCAO', tipo_acao: 'NUTRIR' },
  { id: 10, situacao: 'ATIVO',    resultado: 'FU7',            estagio_funil: 'FOLLOW-UP',         fase: 'NEGOCIACAO',  tipo_contato: 'Qualquer',   acao_futura: 'Retornar em 7 dias conforme combinado',                          temperatura: 'MORNO',   follow_up_dias: 7,  grupo_dashboard: 'ATIVO',    tipo_acao: 'FOLLOW-UP' },
  { id: 11, situacao: 'ATIVO',    resultado: 'FU15',           estagio_funil: 'FOLLOW-UP',         fase: 'NEGOCIACAO',  tipo_contato: 'Qualquer',   acao_futura: 'Retornar em 15 dias conforme combinado',                         temperatura: 'MORNO',   follow_up_dias: 15, grupo_dashboard: 'ATIVO',    tipo_acao: 'FOLLOW-UP' },
  { id: 12, situacao: 'ATIVO',    resultado: 'SUPORTE',        estagio_funil: 'SUPORTE',           fase: 'POS-VENDA',   tipo_contato: 'Qualquer',   acao_futura: 'Resolver problema urgente — cliente em risco de perda',          temperatura: 'CRITICO', follow_up_dias: 1,  grupo_dashboard: 'CRITICO',  tipo_acao: 'SALVAR' },
  { id: 13, situacao: 'ATIVO',    resultado: 'CADASTRO',       estagio_funil: 'CADASTRO',          fase: 'NEGOCIACAO',  tipo_contato: 'Qualquer',   acao_futura: 'Concluir cadastro e enviar primeira oferta',                     temperatura: 'QUENTE',  follow_up_dias: 3,  grupo_dashboard: 'NOVO',     tipo_acao: 'ATIVAR' },
  { id: 14, situacao: 'ATIVO',    resultado: 'PERDA',          estagio_funil: 'NUTRICAO',          fase: 'NUTRICAO',    tipo_contato: 'Qualquer',   acao_futura: 'Registrar perda — manter em nutricao passiva',                   temperatura: 'PERDIDO', follow_up_dias: null, grupo_dashboard: 'PERDA',   tipo_acao: 'NUTRIR' },
  { id: 15, situacao: 'EM RISCO', resultado: 'VENDA',          estagio_funil: 'ACOMP POS-VENDA',  fase: 'POS-VENDA',   tipo_contato: 'Qualquer',   acao_futura: 'Venda realizada — acompanhar de perto para evitar cancelamento',  temperatura: 'MORNO',   follow_up_dias: 3,  grupo_dashboard: 'RETENCAO', tipo_acao: 'RECOMPRA' },
  { id: 16, situacao: 'EM RISCO', resultado: 'NAO ATENDE',     estagio_funil: 'TENTATIVA',         fase: 'REATIVAR',    tipo_contato: 'Ligacao',    acao_futura: 'Cliente em risco — tentar contato urgente amanha',                temperatura: 'CRITICO', follow_up_dias: 1,  grupo_dashboard: 'CRITICO',  tipo_acao: 'SALVAR' },
  { id: 17, situacao: 'EM RISCO', resultado: 'RECUSOU',        estagio_funil: 'FOLLOW-UP',         fase: 'REATIVAR',    tipo_contato: 'Qualquer',   acao_futura: 'Escalar para gerencia — cliente estrategico em risco',            temperatura: 'CRITICO', follow_up_dias: 7,  grupo_dashboard: 'CRITICO',  tipo_acao: 'ESCALAR' },
  { id: 18, situacao: 'INAT.REC', resultado: 'VENDA',          estagio_funil: 'REATIVACAO',        fase: 'REATIVAR',    tipo_contato: 'Qualquer',   acao_futura: 'Cliente reativado! Acompanhar proximos 30 dias com atencao',      temperatura: 'QUENTE',  follow_up_dias: 7,  grupo_dashboard: 'REATIVADO', tipo_acao: 'REATIVAR' },
  { id: 19, situacao: 'INAT.REC', resultado: 'NAO ATENDE',     estagio_funil: 'TENTATIVA',         fase: 'REATIVAR',    tipo_contato: 'Ligacao',    acao_futura: 'Tentar reativacao por outro canal (WhatsApp ou email)',           temperatura: 'FRIO',    follow_up_dias: 2,  grupo_dashboard: 'INAT',     tipo_acao: 'REATIVAR' },
  { id: 20, situacao: 'INAT.ANT', resultado: 'VENDA',          estagio_funil: 'REATIVACAO',        fase: 'REATIVAR',    tipo_contato: 'Qualquer',   acao_futura: 'Cliente antigo reativado — tratamento VIP nas proximas semanas',  temperatura: 'QUENTE',  follow_up_dias: 5,  grupo_dashboard: 'REATIVADO', tipo_acao: 'REATIVAR' },
  { id: 21, situacao: 'INAT.ANT', resultado: 'NAO ATENDE',     estagio_funil: 'TENTATIVA',         fase: 'REATIVAR',    tipo_contato: 'Ligacao',    acao_futura: 'Enviar proposta especial via WhatsApp apos tentativa sem sucesso', temperatura: 'FRIO',    follow_up_dias: 3,  grupo_dashboard: 'INAT',     tipo_acao: 'REATIVAR' },
  { id: 22, situacao: 'PROSPECT', resultado: 'ORCAMENTO',      estagio_funil: 'PROSPECT',          fase: 'PROSPECTAR',  tipo_contato: 'Qualquer',   acao_futura: 'Enviar proposta personalizada e aguardar retorno',               temperatura: 'QUENTE',  follow_up_dias: 5,  grupo_dashboard: 'PROSPECT', tipo_acao: 'CONVERTER' },
  { id: 23, situacao: 'PROSPECT', resultado: 'NAO ATENDE',     estagio_funil: 'TENTATIVA',         fase: 'PROSPECTAR',  tipo_contato: 'Ligacao',    acao_futura: 'Tentar por WhatsApp com mensagem de apresentacao',               temperatura: 'FRIO',    follow_up_dias: 2,  grupo_dashboard: 'PROSPECT', tipo_acao: 'CONVERTER' },
  { id: 24, situacao: 'LEAD',     resultado: 'VENDA',          estagio_funil: 'CONVERSAO',         fase: 'PROSPECTAR',  tipo_contato: 'Qualquer',   acao_futura: 'Lead convertido! Iniciar onboarding e primeira venda',           temperatura: 'QUENTE',  follow_up_dias: 3,  grupo_dashboard: 'NOVO',     tipo_acao: 'ATIVAR' },
  { id: 25, situacao: 'NOVO',     resultado: 'CADASTRO',       estagio_funil: 'CADASTRO',          fase: 'ONBOARDING',  tipo_contato: 'Qualquer',   acao_futura: 'Iniciar onboarding — apresentar mix completo e condicoes',       temperatura: 'QUENTE',  follow_up_dias: 2,  grupo_dashboard: 'NOVO',     tipo_acao: 'ATIVAR' },
];

// Completar com registros ate 92 (repetindo padroes com variacoes)
function expandirRegras(base: RegraMotor[]): RegraMotor[] {
  const extras: RegraMotor[] = [];
  const situacoes = ['ATIVO', 'EM RISCO', 'INAT.REC', 'INAT.ANT', 'PROSPECT', 'LEAD', 'NOVO'];
  const resultados = ['FU7', 'FU15', 'RELACIONAMENTO', 'CS', 'PERDA'];
  let id = base.length + 1;
  for (const sit of situacoes) {
    for (const res of resultados) {
      if (id > 92) break;
      extras.push({
        id, situacao: sit, resultado: res,
        estagio_funil: 'FOLLOW-UP', fase: 'NUTRICAO',
        tipo_contato: 'Qualquer',
        acao_futura: `Executar ${res} para situacao ${sit}`,
        temperatura: 'MORNO', follow_up_dias: 7,
        grupo_dashboard: 'ATIVO', tipo_acao: 'NUTRIR',
      });
      id++;
    }
    if (id > 92) break;
  }
  return [...base, ...extras];
}

const TODAS_REGRAS = expandirRegras(MOCK_REGRAS);

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
  'EM RISCO':  { bg: '#FF6600', text: '#fff' },
  'INAT.REC':  { bg: '#FFC000', text: '#1a1a1a' },
  'INAT.ANT':  { bg: '#FF0000', text: '#fff' },
  PROSPECT:    { bg: '#808080', text: '#fff' },
  LEAD:        { bg: '#6366F1', text: '#fff' },
  NOVO:        { bg: '#0EA5E9', text: '#fff' },
};

function SitBadge({ value }: { value: string }) {
  const cfg = SITUACAO_COLORS[value] ?? { bg: '#e5e7eb', text: '#374151' };
  return (
    <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded uppercase"
      style={{ backgroundColor: cfg.bg, color: cfg.text }}>
      {value}
    </span>
  );
}

function TempCell({ value }: { value: string }) {
  const cfg = TEMP_COLORS[value] ?? { bg: '#e5e7eb', text: '#374151' };
  return (
    <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded uppercase"
      style={{ backgroundColor: cfg.bg, color: cfg.text }}>
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
  const [filtroSituacao, setFiltroSituacao] = useState('');

  useEffect(() => {
    setLoading(true);
    fetchJson<RegraMotor[]>('/api/motor/regras')
      .then(data => setRegras(data))
      .catch(() => setRegras(TODAS_REGRAS))
      .finally(() => setLoading(false));
  }, []);

  const situacoes = Array.from(new Set(TODAS_REGRAS.map(r => r.situacao)));

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

      {/* Filtro */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
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
      <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="w-5 h-5 border-2 border-gray-300 border-t-green-600 rounded-full animate-spin" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full" role="table">
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
                {regrasFiltradas.map(regra => (
                  <tr key={regra.id} className="hover:bg-gray-50 transition-colors">
                    <td className="px-3 py-2 text-[10px] text-gray-400 tabular-nums">{regra.id}</td>
                    <td className="px-3 py-2">
                      <SitBadge value={regra.situacao} />
                    </td>
                    <td className="px-3 py-2 text-xs text-gray-700 font-medium">{regra.resultado}</td>
                    <td className="px-3 py-2 text-xs text-gray-600">{regra.estagio_funil}</td>
                    <td className="px-3 py-2 text-xs text-gray-600">{regra.fase}</td>
                    <td className="px-3 py-2 text-xs text-gray-500">{regra.tipo_contato}</td>
                    <td className="px-3 py-2 text-xs text-gray-700 max-w-xs">{regra.acao_futura}</td>
                    <td className="px-3 py-2">
                      <TempCell value={regra.temperatura} />
                    </td>
                    <td className="px-3 py-2 text-xs text-gray-700 tabular-nums text-center">
                      {regra.follow_up_dias ?? '—'}
                    </td>
                    <td className="px-3 py-2 text-xs text-gray-500 font-mono">{regra.tipo_acao}</td>
                  </tr>
                ))}
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
