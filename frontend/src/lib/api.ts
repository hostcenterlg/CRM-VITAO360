// API client para CRM VITAO360 — tipado, auth via JWT, BRL-ready

import { getToken } from '@/lib/auth';

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? '';

// ---------------------------------------------------------------------------
// Helpers internos
// ---------------------------------------------------------------------------

export async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
  const token = getToken();

  const baseHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };

  const res = await fetch(`${BASE_URL}${path}`, {
    cache: 'no-store',
    ...options,
    headers: {
      ...baseHeaders,
      ...(options?.headers as Record<string, string> | undefined),
    },
  });

  // Token expirado — redireciona para login
  if (res.status === 401) {
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
    }
    throw new Error('Sessao expirada');
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as Record<string, unknown>;
    throw new Error((body.detail as string) || `API error ${res.status}`);
  }

  return res.json() as Promise<T>;
}

async function mutateJson<T>(
  path: string,
  method: 'POST' | 'PUT' | 'PATCH' | 'DELETE',
  body?: unknown
): Promise<T> {
  return fetchJson<T>(path, {
    method,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
}

// ---------------------------------------------------------------------------
// Utilitarios de formatacao
// ---------------------------------------------------------------------------

export function formatBRL(value: number): string {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  }).format(value);
}

export function formatPercent(value: number, decimals = 1): string {
  return `${value.toFixed(decimals)}%`;
}

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface KPIs {
  total_clientes: number;
  total_ativos: number;
  total_prospects: number;
  total_inativos: number;
  faturamento_total: number;
  media_score: number;
  clientes_alerta: number;
  clientes_criticos: number;
}

export interface DistribuicaoItem {
  label: string;
  count: number;
  pct: number;
}

export interface Distribuicao {
  por_situacao: DistribuicaoItem[];
  por_sinaleiro: DistribuicaoItem[];
  por_prioridade: DistribuicaoItem[];
  por_consultor: DistribuicaoItem[];
}

export interface Top10Cliente {
  cnpj: string;
  nome_fantasia: string;
  consultor: string;
  faturamento_total: number;
  score: number;
  prioridade: string;
  sinaleiro: string;
}

export interface ProjecaoResumo {
  faturamento_realizado: number;
  baseline_2025: number;
  projecao_2026: number;
  q1_2026_real: number;
  pct_projecao: number;
  fonte_dados: string;
}

export interface ProjecaoConsultor {
  consultor: string;
  faturamento: number;
  meta: number;
  pct_alcancado: number;
  total_vendas: number;
}

export interface Projecao {
  resumo: ProjecaoResumo;
  por_consultor: ProjecaoConsultor[];
}

// Performance por consultor (dashboard bloco 2)
export interface PerformanceConsultor {
  consultor: string;
  territorio: string;
  total_clientes: number;
  faturamento_real: number;
  meta_2026: number;
  pct_atingimento: number;
  status: 'BOM' | 'ALERTA' | 'CRITICO';
}

// Sinaleiro carteira
export interface SinaleiroItem {
  cnpj: string;
  nome_fantasia: string;
  uf: string;
  consultor: string;
  rede: string;
  meta_anual: number;
  realizado: number;
  pct_atingimento: number;
  gap: number;
  cor: string;
  maturidade: string;
  acao_recomendada: string;
}

export interface SinaleiroResumo {
  cor: string;
  count: number;
  pct: number;
  faturamento: number;
}

export interface SinaleiroResponse {
  total: number;
  resumo: SinaleiroResumo[];
  itens: SinaleiroItem[];
}

// Projecao por mes (grafico barras) — retornado por /api/projecao/{consultor}
export interface ProjecaoMes {
  mes_referencia: string;
  faturamento: number;
  meta: number;
  total_vendas: number;
}

export interface ProjecaoClienteItem {
  cnpj: string;
  nome_fantasia: string;
  consultor: string;
  meta_anual: number;
  realizado: number;
  pct_atingimento: number;
  gap: number;
  status_meta: string;
}

// Detalhe mensal de um consultor
export interface ProjecaoConsultorDetalhe {
  consultor: string;
  faturamento_total: number;
  meta_total: number;
  pct_alcancado: number;
  mensal: ProjecaoMes[];
}

export interface ScoreBreakdown {
  urgencia: number;
  valor: number;
  follow_up: number;
  sinal: number;
  tentativa: number;
  situacao: number;
}

export interface VendaMensal {
  mes: string;
  valor: number;
}

export interface ClienteRegistro {
  cnpj: string;
  nome_fantasia: string;
  razao_social?: string;
  consultor: string;
  situacao: string;
  sinaleiro: string;
  prioridade: string;
  curva_abc?: string;
  score?: number;
  score_breakdown?: ScoreBreakdown;
  faturamento_total?: number;
  faturamento_2026?: number;
  meta_anual?: number;
  vendas_mensais?: VendaMensal[];
  cidade?: string;
  uf?: string;
  email?: string;
  telefone?: string;
  data_cadastro?: string;
  rede_grupo?: string;
  segmento?: string;
  ultima_compra?: string;
  dias_sem_compra?: number;
  ticket_medio?: number;
  meta_mensal?: number;
  ciclo_medio?: number;
  temperatura?: string;
  fase?: string;
  estagio_funil?: string;
  tipo_cliente?: string;
  [key: string]: unknown;
}

export interface ClientesResponse {
  total: number;
  limit: number;
  offset: number;
  registros: ClienteRegistro[];
}

export interface AgendaItem {
  cnpj: string;
  nome_fantasia: string;
  posicao: number;
  score: number;
  prioridade: string;
  acao: string;
  // Campos extras que o backend pode retornar
  sinaleiro?: string;
  situacao?: string;
  uf?: string;
  consultor?: string;
  dias_sem_compra?: number;
  ciclo_medio?: number;
  temperatura?: string;
  tentativa?: string;
  follow_up?: string;
  curva_abc?: string;
}

export interface AtendimentoMotorFeedback {
  estagio_funil?: string;
  temperatura?: string;
  fase?: string;
  acao_futura?: string;
  follow_up?: string;
}

// ---------------------------------------------------------------------------
// Dashboard endpoints
// ---------------------------------------------------------------------------

export async function fetchKPIs(): Promise<KPIs> {
  return fetchJson<KPIs>('/api/dashboard/kpis');
}

export async function fetchDistribuicao(): Promise<Distribuicao> {
  return fetchJson<Distribuicao>('/api/dashboard/distribuicao');
}

export async function fetchTop10(): Promise<Top10Cliente[]> {
  return fetchJson<Top10Cliente[]>('/api/dashboard/top10');
}

export async function fetchProjecao(): Promise<Projecao> {
  return fetchJson<Projecao>('/api/projecao');
}

export async function fetchPerformance(): Promise<PerformanceConsultor[]> {
  return fetchJson<PerformanceConsultor[]>('/api/dashboard/performance');
}

// ---------------------------------------------------------------------------
// Sinaleiro endpoints
// ---------------------------------------------------------------------------

export interface SinaleiroParams {
  cor?: string;
  consultor?: string;
  rede?: string;
  limit?: number;
  offset?: number;
}

export async function fetchSinaleiro(
  params: SinaleiroParams = {}
): Promise<SinaleiroResponse> {
  const qs = new URLSearchParams();
  if (params.cor) qs.set('cor', params.cor);
  if (params.consultor) qs.set('consultor', params.consultor);
  if (params.rede) qs.set('rede', params.rede);
  qs.set('limit', String(params.limit ?? 100));
  qs.set('offset', String(params.offset ?? 0));
  return fetchJson<SinaleiroResponse>(`/api/sinaleiro?${qs.toString()}`);
}

// ---------------------------------------------------------------------------
// Projecao por mes (detalhe de um consultor)
// ---------------------------------------------------------------------------

export async function fetchProjecaoConsultorDetalhe(
  consultor: string
): Promise<ProjecaoConsultorDetalhe> {
  return fetchJson<ProjecaoConsultorDetalhe>(`/api/projecao/${encodeURIComponent(consultor)}`);
}

// ---------------------------------------------------------------------------
// Clientes endpoints
// ---------------------------------------------------------------------------

export interface ClientesParams {
  consultor?: string;
  situacao?: string;
  sinaleiro?: string;
  abc?: string;
  temperatura?: string;
  prioridade?: string;
  uf?: string;
  busca?: string;
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
}

export async function fetchClientes(
  params: ClientesParams = {}
): Promise<ClientesResponse> {
  const qs = new URLSearchParams();
  if (params.consultor) qs.set('consultor', params.consultor);
  if (params.situacao) qs.set('situacao', params.situacao);
  if (params.sinaleiro) qs.set('sinaleiro', params.sinaleiro);
  if (params.abc) qs.set('abc', params.abc);
  if (params.temperatura) qs.set('temperatura', params.temperatura);
  if (params.prioridade) qs.set('prioridade', params.prioridade);
  if (params.uf) qs.set('uf', params.uf);
  if (params.busca) qs.set('busca', params.busca);
  if (params.sort_by) qs.set('sort_by', params.sort_by);
  if (params.sort_dir) qs.set('sort_dir', params.sort_dir);
  qs.set('limit', String(params.limit ?? 50));
  qs.set('offset', String(params.offset ?? 0));

  return fetchJson<ClientesResponse>(`/api/clientes?${qs.toString()}`);
}

export interface AtendimentoHistoricoItem {
  id: number;
  cnpj: string;
  consultor?: string;
  resultado: string;
  descricao: string;
  data_registro: string;
  via_whatsapp?: boolean;
  via_ligacao?: boolean;
  acao_futura?: string;
}

export interface AtendimentosHistoricoResponse {
  total: number;
  page: number;
  page_size: number;
  itens: AtendimentoHistoricoItem[];
}

export async function fetchAtendimentosHistorico(
  cnpj: string,
  page = 1,
  page_size = 20
): Promise<AtendimentosHistoricoResponse> {
  const qs = new URLSearchParams({ cnpj, page: String(page), page_size: String(page_size) });
  return fetchJson<AtendimentosHistoricoResponse>(`/api/atendimentos?${qs.toString()}`);
}

export async function fetchCliente(cnpj: string): Promise<ClienteRegistro> {
  return fetchJson<ClienteRegistro>(`/api/clientes/${cnpj}`);
}

export interface ScoreFator {
  valor: number;
  peso: number;
  contribuicao: number;
}

export interface ClienteScoreResponse {
  cnpj: string;
  score_total: number;
  prioridade: string;
  fatores: {
    urgencia: ScoreFator;
    valor: ScoreFator;
    followup: ScoreFator;
    sinal: ScoreFator;
    tentativa: ScoreFator;
    situacao: ScoreFator;
  };
}

export async function fetchClienteScore(cnpj: string): Promise<ClienteScoreResponse> {
  return fetchJson<ClienteScoreResponse>(`/api/clientes/${cnpj}/score`);
}

// ---------------------------------------------------------------------------
// Agenda endpoints
// ---------------------------------------------------------------------------

interface AgendaConsultorResponse {
  consultor: string;
  data_agenda: string;
  total: number;
  itens: AgendaItem[];
}

export async function fetchAgenda(consultor: string): Promise<AgendaItem[]> {
  const res = await fetchJson<AgendaConsultorResponse>(
    `/api/agenda/${encodeURIComponent(consultor)}`
  );
  return res.itens;
}

export async function gerarAgenda(): Promise<{ message: string }> {
  return mutateJson<{ message: string }>('/api/agenda/gerar', 'POST');
}

// ---------------------------------------------------------------------------
// Atendimentos (registros de log — Two-Base: R$ SEMPRE 0.00)
// ---------------------------------------------------------------------------

export interface AtendimentoPayload {
  cnpj: string;
  resultado: string;
  descricao: string;
  via_whatsapp?: boolean;
  via_ligacao?: boolean;
  tipo_contato?: string;
}

export interface AtendimentoResponse {
  id: number;
  cnpj: string;
  resultado: string;
  descricao: string;
  data_registro: string;
  // Saidas do Motor (calculadas pelo backend apos registrar)
  motor?: {
    estagio_funil?: string;
    temperatura?: string;
    fase?: string;
    acao_futura?: string;
    follow_up?: string;
  };
}

export async function registrarAtendimento(
  data: AtendimentoPayload
): Promise<AtendimentoResponse> {
  return mutateJson<AtendimentoResponse>('/api/atendimentos', 'POST', data);
}

// ---------------------------------------------------------------------------
// Vendas (registros de venda — Two-Base: tem valor R$)
// ---------------------------------------------------------------------------

export interface VendaPayload {
  cnpj: string;
  data_pedido: string;
  valor_pedido: number;
  numero_pedido?: string;
}

export interface VendaResponse {
  id: number;
  cnpj: string;
  data_pedido: string;
  valor_pedido: number;
  numero_pedido: string | null;
  data_registro: string;
}

export async function registrarVenda(
  data: VendaPayload
): Promise<VendaResponse> {
  return mutateJson<VendaResponse>('/api/vendas', 'POST', data);
}

// ---------------------------------------------------------------------------
// RNC endpoints
// ---------------------------------------------------------------------------

export interface RNCItem {
  id: number;
  data_abertura: string;
  cliente_nome: string;
  cliente_cnpj: string;
  tipo_problema: string;
  area_responsavel: string;
  status: 'ABERTO' | 'EM_ANDAMENTO' | 'RESOLVIDO' | 'ENCERRADO';
  dias_aberto: number;
  sla_status: 'DENTRO' | 'ATENCAO' | 'VIOLADO';
  descricao: string;
  consultor?: string;
}

export interface RNCResumo {
  total: number;
  resolvido: number;
  resolvido_pct: number;
  em_andamento: number;
  em_andamento_pct: number;
  pendente: number;
  pendente_pct: number;
}

export interface RNCResponse {
  resumo: RNCResumo;
  itens: RNCItem[];
}

export interface RNCPayload {
  cliente_cnpj: string;
  cliente_nome?: string;
  tipo_problema: string;
  descricao: string;
}

export async function fetchRNC(params: { status?: string; tipo?: string; consultor?: string } = {}): Promise<RNCResponse> {
  const qs = new URLSearchParams();
  if (params.status) qs.set('status', params.status);
  if (params.tipo) qs.set('tipo', params.tipo);
  if (params.consultor) qs.set('consultor', params.consultor);
  return fetchJson<RNCResponse>(`/api/rnc?${qs.toString()}`);
}

export async function criarRNC(data: RNCPayload): Promise<RNCItem> {
  return mutateJson<RNCItem>('/api/rnc', 'POST', data);
}

export async function patchRNC(id: number, data: { status: string }): Promise<RNCItem> {
  return mutateJson<RNCItem>(`/api/rnc/${id}`, 'PATCH', data);
}

// ---------------------------------------------------------------------------
// Motor de Regras endpoints
// ---------------------------------------------------------------------------

export interface RegraMotor {
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

export async function fetchMotorRegras(): Promise<RegraMotor[]> {
  return fetchJson<RegraMotor[]>('/api/motor/regras');
}

// ---------------------------------------------------------------------------
// Usuarios endpoints
// ---------------------------------------------------------------------------

export interface UsuarioAdmin {
  id: number;
  nome: string;
  email: string;
  role: 'admin' | 'gerente' | 'consultor' | 'consultor_externo';
  // O backend usa consultor_nome (DE-PARA: MANU, LARISSA, DAIANE, JULIO)
  consultor_nome: string | null;
  ativo: boolean;
  // ultimo_login nao e retornado pelo schema atual do backend
  ultimo_login?: string | null;
}

export async function fetchUsuarios(): Promise<UsuarioAdmin[]> {
  return fetchJson<UsuarioAdmin[]>('/api/auth/users');
}

export async function criarUsuario(data: Omit<UsuarioAdmin, 'id' | 'ultimo_login'> & { senha: string; consultor_nome?: string | null }): Promise<UsuarioAdmin> {
  return mutateJson<UsuarioAdmin>('/api/auth/users', 'POST', data);
}

export async function atualizarUsuario(id: number, data: Partial<UsuarioAdmin> & { senha?: string }): Promise<UsuarioAdmin> {
  return mutateJson<UsuarioAdmin>(`/api/auth/users/${id}`, 'PATCH', data);
}

// ---------------------------------------------------------------------------
// Redes endpoints
// ---------------------------------------------------------------------------

export interface LojaRede {
  cnpj: string;
  nome: string;
  cidade: string;
  uf: string;
  fat_real: number;
  meta: number;
  pct_ating: number;
  cor: string;
}

export interface RedeItem {
  nome: string;
  consultor: string;
  total_lojas: number;
  fat_real: number;
  meta: number;
  pct_ating: number;
  gap: number;
  cor: string;
  distribuicao: { VERDE: number; AMARELO: number; LARANJA: number; VERMELHO: number; ROXO: number };
  lojas: LojaRede[];
}

export interface RedesResponse {
  total_redes: number;
  total_lojas: number;
  redes: RedeItem[];
}

export async function fetchRedes(): Promise<RedesResponse> {
  return fetchJson<RedesResponse>('/api/redes');
}

// ---------------------------------------------------------------------------
// Import endpoints
// ---------------------------------------------------------------------------

export interface ImportResult {
  arquivo: string;
  registros_lidos: number;
  inseridos: number;
  atualizados: number;
  ignorados: number;
  erros: number;
  detalhes_erros: string[];
  status: 'SUCESSO' | 'SUCESSO_COM_ERROS' | 'FALHA';
}

export interface ImportHistoryItem {
  id: number;
  data_import: string;
  arquivo: string;
  registros_lidos: number;
  inseridos: number;
  atualizados: number;
  erros: number;
  status: 'SUCESSO' | 'SUCESSO_COM_ERROS' | 'FALHA';
}

export interface ImportHistory {
  total: number;
  itens: ImportHistoryItem[];
}

export async function uploadImport(file: File): Promise<ImportResult> {
  const formData = new FormData();
  formData.append('file', file);
  const token = getToken();
  const res = await fetch(`${BASE_URL}/api/import/upload`, {
    method: 'POST',
    headers: { ...(token ? { Authorization: `Bearer ${token}` } : {}) },
    body: formData,
  });
  if (res.status === 401) {
    if (typeof window !== 'undefined') window.location.href = '/login';
    throw new Error('Sessao expirada');
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as Record<string, unknown>;
    throw new Error((body.detail as string) || `API error ${res.status}`);
  }
  return res.json() as Promise<ImportResult>;
}

export async function fetchImportHistory(): Promise<ImportHistory> {
  return fetchJson<ImportHistory>('/api/import/history');
}

// ---------------------------------------------------------------------------
// IA — Inteligencia Artificial
// ---------------------------------------------------------------------------

export interface BriefingResponse {
  cnpj: string;
  nome_cliente: string;
  briefing: string;
  tokens_usados: number;
  cached: boolean;
  ia_configurada: boolean;
}

export interface MensagemWhatsAppResponse {
  cnpj: string;
  nome_cliente: string;
  mensagem: string;
  tokens_usados: number;
  ia_configurada: boolean;
}

export interface MetricasSemanais {
  total_carteira: number;
  vendas_semana_qtd: number;
  vendas_semana_volume: number;
  clientes_em_risco: number;
  followups_vencidos: number;
}

export interface ResumoSemanalResponse {
  consultor: string;
  periodo: string;
  resumo: string;
  tokens_usados: number;
  metricas: MetricasSemanais;
  ia_configurada: boolean;
}

export async function getBriefing(cnpj: string): Promise<BriefingResponse> {
  return fetchJson<BriefingResponse>(`/api/ia/briefing/${cnpj}`);
}

export async function gerarMensagemWhatsApp(
  cnpj: string,
  objetivo: string
): Promise<MensagemWhatsAppResponse> {
  return mutateJson<MensagemWhatsAppResponse>(`/api/ia/mensagem/${cnpj}`, 'POST', { objetivo });
}

export async function getResumoSemanal(consultor: string): Promise<ResumoSemanalResponse> {
  return fetchJson<ResumoSemanalResponse>(`/api/ia/resumo-semanal/${consultor}`);
}
