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

/**
 * Formata uma string ISO (yyyy-mm-dd ou yyyy-mm-ddTHH:MM:SS) para dd/mm/yyyy.
 * Retorna '—' se o valor for nulo, undefined ou invalido.
 */
export function formatDateBR(dateStr?: string | null): string {
  if (!dateStr) return '—';
  const datePart = dateStr.split('T')[0];
  const parts = datePart.split('-');
  if (parts.length !== 3) return dateStr;
  const [year, month, day] = parts;
  if (!year || !month || !day) return dateStr;
  return `${day}/${month}/${year}`;
}

/**
 * Formata um numero com separador de milhar em pt-BR (ex: 1.234.567).
 * Util para contagens e quantidades (sem cifrao).
 */
export function formatNumber(value: number, decimals = 0): string {
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
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
  followups_vencidos: number;
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
  valor_ultimo_pedido?: number;
  n_compras?: number;
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

export interface TendenciaMensal {
  mes: string;          // "YYYY-MM" ex.: "2025-01"
  faturamento: number;
  vendas_qtd: number;
  clientes_ativos: number;
  ticket_medio: number;
}

export interface TendenciasResponse {
  meses: TendenciaMensal[];
}

export async function fetchTendencias(): Promise<TendenciasResponse> {
  return fetchJson<TendenciasResponse>('/api/dashboard/tendencias');
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
  if (params.abc) qs.set('curva_abc', params.abc);
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

export async function atualizarEstagioCliente(
  cnpj: string,
  estagio_funil: string
): Promise<ClienteRegistro> {
  return mutateJson<ClienteRegistro>(`/api/clientes/${cnpj}`, 'PATCH', { estagio_funil });
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
  followup_dias?: number | null;
  grupo_dash: string | null;
  tipo_acao: string | null;
  chave: string;
}

interface MotorRegrasResponse {
  total: number;
  regras: RegraMotor[];
}

export async function fetchMotorRegras(): Promise<RegraMotor[]> {
  const data = await fetchJson<MotorRegrasResponse>('/api/motor/regras');
  return (data.regras ?? []).map(r => ({
    ...r,
    follow_up_dias: r.follow_up_dias ?? r.followup_dias ?? null,
  }));
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
  data_import: string | null;
  arquivo: string | null;
  registros_lidos: number;
  inseridos: number;
  atualizados: number;
  ignorados: number;
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

// ---------------------------------------------------------------------------
// Redistribuicao de Carteira (FR-022)
// ---------------------------------------------------------------------------

export interface ConsultorResumo {
  consultor: string;
  total: number;
  faturamento: number;
}

export interface RedistribuirResponse {
  total_processados: number;
  total_atualizados: number;
  erros: string[];
}

export async function fetchConsultorResumo(): Promise<ConsultorResumo[]> {
  return fetchJson<ConsultorResumo[]>('/api/clientes/por-consultor');
}

export async function redistribuirCarteira(
  cnpjs: string[],
  novo_consultor: string
): Promise<RedistribuirResponse> {
  return mutateJson<RedistribuirResponse>('/api/clientes/redistribuir', 'PATCH', {
    cnpjs,
    novo_consultor,
  });
}

// ---------------------------------------------------------------------------
// WhatsApp — Integracao Deskrio
// ---------------------------------------------------------------------------

export interface ConexaoWA {
  id: number | null;
  nome: string;
  status: string;
  status_legivel: string;
}

export interface WhatsAppStatus {
  configurado: boolean;
  conexoes: ConexaoWA[];
  alguma_conectada: boolean;
  total_conexoes: number;
}

export interface WhatsAppContatoResponse {
  encontrado: boolean;
  numero: string | null;
  nome: string | null;
  deskrio_id: number | null;
  cnpj: string | null;
}

export interface WhatsAppEnviarResponse {
  enviado: boolean;
  mensagem_id: string | null;
  numero: string | null;
  erro: string | null;
}

export interface TicketWA {
  id: number | null;
  status: string | null;
  criado_em: string | null;
  atualizado_em: string | null;
  contact_id: number | null;
}

export interface WhatsAppTicketsResponse {
  cnpj: string | null;
  numero: string | null;
  total: number;
  tickets: TicketWA[];
}

export async function fetchWhatsAppStatus(): Promise<WhatsAppStatus> {
  return fetchJson<WhatsAppStatus>('/api/whatsapp/status');
}

export async function buscarContatoWhatsApp(cnpj: string): Promise<WhatsAppContatoResponse> {
  return fetchJson<WhatsAppContatoResponse>(`/api/whatsapp/contato/${cnpj}`);
}

export async function enviarWhatsApp(
  cnpj: string,
  mensagem: string
): Promise<WhatsAppEnviarResponse> {
  return mutateJson<WhatsAppEnviarResponse>('/api/whatsapp/enviar', 'POST', { cnpj, mensagem });
}

export async function fetchWhatsAppTickets(
  cnpj: string,
  dias = 7
): Promise<WhatsAppTicketsResponse> {
  return fetchJson<WhatsAppTicketsResponse>(
    `/api/whatsapp/tickets?cnpj=${cnpj}&dias=${dias}`
  );
}

export async function fetchWhatsAppConexoes(): Promise<ConexaoWA[]> {
  return fetchJson<ConexaoWA[]>('/api/whatsapp/conexoes');
}

// ---------------------------------------------------------------------------
// Atividades — dados reais de contato por tipo/resultado (substitui mock data)
// ---------------------------------------------------------------------------

export interface AtividadePorTipo {
  tipo: string;
  quantidade: number;
}

export interface AtividadePorResultado {
  resultado: string;
  quantidade: number;
}

export interface AtividadePorConsultor {
  consultor: string;
  quantidade: number;
  tipos: Record<string, number>;
}

export interface AtividadesResponse {
  total: number;
  por_tipo: AtividadePorTipo[];
  por_resultado: AtividadePorResultado[];
  por_consultor: AtividadePorConsultor[];
  por_mes: { mes: string; quantidade: number }[];
  periodo: {
    inicio: string;
    fim: string;
  };
}

export interface AtividadesParams {
  consultor?: string;
  data_inicio?: string;
  data_fim?: string;
}

export async function fetchAtividades(
  params?: AtividadesParams
): Promise<AtividadesResponse> {
  const searchParams = new URLSearchParams();
  if (params?.consultor) searchParams.set('consultor', params.consultor);
  if (params?.data_inicio) searchParams.set('data_inicio', params.data_inicio);
  if (params?.data_fim) searchParams.set('data_fim', params.data_fim);
  const query = searchParams.toString();
  return fetchJson<AtividadesResponse>(
    `/api/dashboard/atividades${query ? `?${query}` : ''}`
  );
}

// ---------------------------------------------------------------------------
// Positivacao — clientes que compraram no periodo (substitui mock data)
// ---------------------------------------------------------------------------

export interface PositivacaoPorSituacao {
  situacao: string;
  quantidade: number;
  pct: number;
}

export interface PositivacaoPorConsultor {
  consultor: string;
  total_carteira: number;
  positivados: number;
  pct_positivacao: number;
}

export interface PositivacaoResponse {
  total_carteira: number;
  total_positivados: number;
  pct_positivacao: number;
  por_situacao: PositivacaoPorSituacao[];
  por_consultor: PositivacaoPorConsultor[];
  mes_referencia: string;
}

export interface PositivacaoParams {
  mes?: number;
  ano?: number;
  consultor?: string;
}

export async function fetchPositivacao(
  params?: PositivacaoParams
): Promise<PositivacaoResponse> {
  const searchParams = new URLSearchParams();
  if (params?.mes !== undefined) searchParams.set('mes', String(params.mes));
  if (params?.ano !== undefined) searchParams.set('ano', String(params.ano));
  if (params?.consultor) searchParams.set('consultor', params.consultor);
  const query = searchParams.toString();
  return fetchJson<PositivacaoResponse>(
    `/api/dashboard/positivacao${query ? `?${query}` : ''}`
  );
}

// ---------------------------------------------------------------------------
// Produtos endpoints
// ---------------------------------------------------------------------------

export interface ProdutoItem {
  id: number;
  codigo: string;
  nome: string;
  categoria: string;
  unidade: string;
  preco_tabela: number;
  comissao_pct: number;
  ativo: boolean;
  descricao?: string;
  peso_liquido?: number;
  validade_dias?: number;
  precos_regionais?: { regiao: string; preco: number }[];
}

export interface ProdutosResponse {
  total: number;
  limit: number;
  offset: number;
  itens: ProdutoItem[];
}

export interface ProdutosParams {
  busca?: string;
  categoria?: string;
  ativo?: boolean;
  limit?: number;
  offset?: number;
}

export async function fetchProdutos(
  params?: ProdutosParams
): Promise<ProdutosResponse> {
  const qs = new URLSearchParams();
  if (params?.busca) qs.set('busca', params.busca);
  if (params?.categoria) qs.set('categoria', params.categoria);
  if (params?.ativo !== undefined) qs.set('ativo', String(params.ativo));
  qs.set('limit', String(params?.limit ?? 50));
  qs.set('offset', String(params?.offset ?? 0));
  return fetchJson<ProdutosResponse>(`/api/produtos?${qs.toString()}`);
}

export async function fetchProdutoCategorias(): Promise<string[]> {
  return fetchJson<string[]>('/api/produtos/categorias');
}

export async function fetchProdutosMaisVendidos(
  params?: { consultor?: string; limit?: number }
): Promise<ProdutoItem[]> {
  const qs = new URLSearchParams();
  if (params?.consultor) qs.set('consultor', params.consultor);
  qs.set('limit', String(params?.limit ?? 5));
  return fetchJson<ProdutoItem[]>(`/api/produtos/mais-vendidos?${qs.toString()}`);
}

export async function fetchProduto(id: number): Promise<ProdutoItem> {
  return fetchJson<ProdutoItem>(`/api/produtos/${id}`);
}

// ---------------------------------------------------------------------------
// Vendas (pedidos) endpoints
// ---------------------------------------------------------------------------

export interface VendaPedidoItem {
  id: number;
  numero_pedido: string;
  consultor: string;
  cliente_cnpj: string;
  cliente_nome: string;
  status: 'DIGITADO' | 'LIBERADO' | 'FATURADO' | 'ENTREGUE' | 'CANCELADO';
  valor_total: number;
  condicao_pagamento: string;
  data_pedido: string;
  data_atualizacao?: string;
  itens_qtd?: number;
}

export interface VendasPorStatusResponse {
  total: number;
  itens: VendaPedidoItem[];
  resumo_status: Record<string, number>;
}

export interface VendasParams {
  status?: string;
  consultor?: string;
  data_inicio?: string;
  data_fim?: string;
  busca?: string;
  limit?: number;
  offset?: number;
}

// Busca ultimas vendas/pedidos de um cliente especifico por CNPJ
export async function fetchVendasCliente(
  cnpj: string,
  limit = 5
): Promise<VendaPedidoItem[]> {
  const qs = new URLSearchParams({ busca: cnpj, limit: String(limit) });
  const res = await fetchJson<VendasPorStatusResponse>(`/api/vendas?${qs.toString()}`);
  // Filtrar pelo CNPJ exato para garantir que nao retorne outros clientes
  return (res.itens ?? []).filter((v) => v.cliente_cnpj === cnpj).slice(0, limit);
}

export async function fetchVendasPorStatus(
  params?: VendasParams
): Promise<VendasPorStatusResponse> {
  const qs = new URLSearchParams();
  if (params?.status) qs.set('status', params.status);
  if (params?.consultor) qs.set('consultor', params.consultor);
  if (params?.data_inicio) qs.set('data_inicio', params.data_inicio);
  if (params?.data_fim) qs.set('data_fim', params.data_fim);
  if (params?.busca) qs.set('busca', params.busca);
  qs.set('limit', String(params?.limit ?? 100));
  qs.set('offset', String(params?.offset ?? 0));
  return fetchJson<VendasPorStatusResponse>(`/api/vendas?${qs.toString()}`);
}

export async function transicionarStatusVenda(
  id: number,
  novoStatus: string
): Promise<VendaPedidoItem> {
  return mutateJson<VendaPedidoItem>(`/api/vendas/${id}/status`, 'PATCH', {
    novo_status: novoStatus,
  });
}

// ---------------------------------------------------------------------------
// Relatorios endpoints
// ---------------------------------------------------------------------------

export interface RelatorioInfo {
  tipo: string;
  titulo: string;
  descricao: string;
  filtros: string[];
}

export async function fetchRelatorioCatalogo(): Promise<RelatorioInfo[]> {
  return fetchJson<RelatorioInfo[]>('/api/relatorios/catalogo');
}

export async function downloadRelatorio(
  tipo: string,
  params: Record<string, string>
): Promise<Blob> {
  const token = getToken();
  const query = new URLSearchParams(params).toString();
  const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? '';
  const res = await fetch(
    `${BASE_URL}/api/relatorios/${tipo}${query ? `?${query}` : ''}`,
    {
      cache: 'no-store',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    }
  );
  if (res.status === 401) {
    if (typeof window !== 'undefined') window.location.href = '/login';
    throw new Error('Sessao expirada');
  }
  if (!res.ok) {
    const body = await res.json().catch(() => ({})) as Record<string, unknown>;
    throw new Error((body.detail as string) || `API error ${res.status}`);
  }
  return res.blob();
}

// ---------------------------------------------------------------------------
// Indicadores Mercos — novos endpoints
// ---------------------------------------------------------------------------

// Parametros comuns para filtros globais de mes/ano/consultor
export interface FiltroMesAnoConsultor {
  mes?: number;
  ano?: number;
  consultor?: string;
}

// Helper interno para montar URLSearchParams a partir de filtros comuns
function buildFiltroQS(params: FiltroMesAnoConsultor): URLSearchParams {
  const qs = new URLSearchParams();
  if (params.mes !== undefined) qs.set('mes', String(params.mes));
  if (params.ano !== undefined) qs.set('ano', String(params.ano));
  if (params.consultor) qs.set('consultor', params.consultor);
  return qs;
}

// --- Evolucao Vendas ---

export interface EvolucaoVendasSerie {
  dia: number;
  mes_atual: number;
  mes_anterior: number;
  ano_anterior: number;
}

export interface EvolucaoVendasResponse {
  mes_referencia: string;
  consultor?: string;
  serie: EvolucaoVendasSerie[];
}

export async function fetchEvolucaoVendas(
  params: FiltroMesAnoConsultor = {}
): Promise<EvolucaoVendasResponse> {
  const qs = buildFiltroQS(params);
  return fetchJson<EvolucaoVendasResponse>(
    `/api/dashboard/evolucao-vendas${qs.toString() ? `?${qs.toString()}` : ''}`
  );
}

// --- Positivacao Diaria ---

export interface PositivacaoDiariaItem {
  dia: number;
  positivados: number;
  objetivo: number;
}

export interface PositivacaoDiariaResponse {
  mes_referencia: string;
  objetivo_diario: number;
  itens: PositivacaoDiariaItem[];
}

export async function fetchPositivacaoDiaria(
  params: FiltroMesAnoConsultor = {}
): Promise<PositivacaoDiariaResponse> {
  const qs = buildFiltroQS(params);
  return fetchJson<PositivacaoDiariaResponse>(
    `/api/dashboard/positivacao-diaria${qs.toString() ? `?${qs.toString()}` : ''}`
  );
}

// --- Positivacao por Vendedor ---

export interface PositivacaoVendedorItem {
  consultor: string;
  positivados: number;
  objetivo: number;
  pct: number;
}

export interface PositivacaoVendedorResponse {
  mes_referencia: string;
  itens: PositivacaoVendedorItem[];
}

export async function fetchPositivacaoVendedor(
  params: Pick<FiltroMesAnoConsultor, 'mes' | 'ano'> = {}
): Promise<PositivacaoVendedorResponse> {
  const qs = new URLSearchParams();
  if (params.mes !== undefined) qs.set('mes', String(params.mes));
  if (params.ano !== undefined) qs.set('ano', String(params.ano));
  return fetchJson<PositivacaoVendedorResponse>(
    `/api/dashboard/positivacao-vendedor${qs.toString() ? `?${qs.toString()}` : ''}`
  );
}

// --- Atendimentos Diarios ---

export interface AtendimentoDiarioItem {
  dia: number;
  mes_atual: number;
  mes_anterior: number;
  objetivo: number;
}

export interface AtendimentosDiariosResponse {
  mes_referencia: string;
  objetivo_diario: number;
  itens: AtendimentoDiarioItem[];
}

export async function fetchAtendimentosDiarios(
  params: FiltroMesAnoConsultor = {}
): Promise<AtendimentosDiariosResponse> {
  const qs = buildFiltroQS(params);
  return fetchJson<AtendimentosDiariosResponse>(
    `/api/dashboard/atendimentos-diarios${qs.toString() ? `?${qs.toString()}` : ''}`
  );
}

// --- Curva ABC Detalhe ---

export interface CurvaABCDetalheItem {
  curva: string;
  total_clientes: number;
  faturamento: number;
  pct_clientes: number;
  pct_faturamento: number;
}

export interface CurvaABCDetalheResponse {
  consultor?: string;
  total_clientes: number;
  total_faturamento: number;
  itens: CurvaABCDetalheItem[];
}

export async function fetchCurvaABCDetalhe(
  params: Pick<FiltroMesAnoConsultor, 'consultor'> = {}
): Promise<CurvaABCDetalheResponse> {
  const qs = new URLSearchParams();
  if (params.consultor) qs.set('consultor', params.consultor);
  return fetchJson<CurvaABCDetalheResponse>(
    `/api/dashboard/curva-abc-detalhe${qs.toString() ? `?${qs.toString()}` : ''}`
  );
}

// --- E-commerce ---

export interface EcommerceResponse {
  mes_referencia: string;
  total_clientes_ecommerce: number;
  pct_do_total: number;
  total_pedidos: number;
  valor_total: number;
}

export async function fetchEcommerce(
  params: Pick<FiltroMesAnoConsultor, 'mes' | 'ano'> = {}
): Promise<EcommerceResponse> {
  const qs = new URLSearchParams();
  if (params.mes !== undefined) qs.set('mes', String(params.mes));
  if (params.ano !== undefined) qs.set('ano', String(params.ano));
  return fetchJson<EcommerceResponse>(
    `/api/dashboard/ecommerce${qs.toString() ? `?${qs.toString()}` : ''}`
  );
}

// ---------------------------------------------------------------------------
// IA Central — endpoints avancados de inteligencia artificial
// ---------------------------------------------------------------------------

export interface BriefingIAResponse {
  cnpj: string;
  nome_cliente: string;
  situacao: string;
  score: number;
  prioridade: string;
  temperatura: string;
  ultimas_compras: Array<{ data: string; valor: number; produtos?: string }>;
  ultimo_contato: { data: string; resultado: string; canal: string } | null;
  sugestao_abordagem: string;
  script_venda: string;
}

export interface MensagemWAResponse {
  mensagem: string;
  tom: string;
  contexto: string;
}

export interface ResumoSemanalIAResponse {
  consultor: string;
  periodo: string;
  clientes_contactados: number;
  vendas_fechadas: number;
  valor_vendas: number;
  pipeline: Array<{ estagio: string; qtd: number }>;
  top_clientes: Array<{ cnpj: string; nome: string; score: number; motivo: string }>;
}

export interface ChurnRiskResponse {
  cnpj: string;
  risco_pct: number;
  nivel: 'BAIXO' | 'MEDIO' | 'ALTO' | 'CRITICO';
  fatores: string[];
  recomendacao: string;
}

export interface SugestaoProdutoResponse {
  cnpj: string;
  produtos_sugeridos: Array<{ id: number; nome: string; categoria: string; motivo: string }>;
  estrategia: string;
}

export async function fetchBriefingIA(cnpj: string): Promise<BriefingIAResponse> {
  return fetchJson<BriefingIAResponse>(`/api/ia/briefing/${encodeURIComponent(cnpj)}`);
}

export async function fetchMensagemWA(cnpj: string): Promise<MensagemWAResponse> {
  return fetchJson<MensagemWAResponse>(`/api/ia/mensagem-wa/${encodeURIComponent(cnpj)}`);
}

export async function fetchResumoSemanalIA(consultor: string): Promise<ResumoSemanalIAResponse> {
  return fetchJson<ResumoSemanalIAResponse>(`/api/ia/resumo-semanal/${encodeURIComponent(consultor)}`);
}

export async function fetchChurnRisk(cnpj: string): Promise<ChurnRiskResponse> {
  return fetchJson<ChurnRiskResponse>(`/api/ia/churn-risk/${encodeURIComponent(cnpj)}`);
}

export async function fetchSugestaoProduto(cnpj: string): Promise<SugestaoProdutoResponse> {
  return fetchJson<SugestaoProdutoResponse>(`/api/ia/sugestao-produto/${encodeURIComponent(cnpj)}`);
}

// ---------------------------------------------------------------------------
// Notificacoes
// ---------------------------------------------------------------------------

export interface Alerta {
  tipo: 'CHURN' | 'FOLLOWUP_VENCIDO' | 'SINALEIRO_VERMELHO' | 'META_RISCO';
  prioridade: 'ALTA' | 'MEDIA' | 'BAIXA';
  cnpj: string;
  nome: string;
  mensagem: string;
  acao: string;
}

export interface NotificacoesResponse {
  total: number;
  alertas: Alerta[];
}

export async function fetchNotificacoes(): Promise<NotificacoesResponse> {
  return fetchJson<NotificacoesResponse>('/api/notificacoes');
}

// ---------------------------------------------------------------------------
// Pipeline admin
// ---------------------------------------------------------------------------

export interface PipelineStatus {
  ultimo_run: string | null;
  duracao_ms: number | null;
  resultado: string | null;
  proximo_agendado: string | null;
}

export interface PipelineEtapa {
  nome: string;
  status: string;
  duracao_ms: number;
  detalhes?: string;
}

export interface PipelineRunResult {
  status: string;
  etapas: PipelineEtapa[];
  duracao_total_ms: number;
}

export interface PipelineLogEntry {
  timestamp: string;
  nivel: string;
  mensagem: string;
}

export async function fetchPipelineStatus(): Promise<PipelineStatus> {
  return fetchJson<PipelineStatus>('/api/pipeline/status');
}

export async function runPipeline(): Promise<PipelineRunResult> {
  return mutateJson<PipelineRunResult>('/api/pipeline/run', 'POST');
}

export async function fetchPipelineLogs(): Promise<PipelineLogEntry[]> {
  return fetchJson<PipelineLogEntry[]>('/api/pipeline/logs');
}
