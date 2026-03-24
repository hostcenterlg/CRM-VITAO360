// API client for CRM VITAO360 — all functions typed, BRL-ready

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    cache: 'no-store',
    headers: { 'Content-Type': 'application/json' },
  });

  if (!res.ok) {
    throw new Error(`API error ${res.status} on ${path}`);
  }

  return res.json() as Promise<T>;
}

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
  meta_q1: number;
  pct_alcancado: number;
  baseline_2025: number;
  projecao_2026: number;
}

export interface ProjecaoConsultor {
  consultor: string;
  faturamento: number;
  meta: number;
  pct_alcancado: number;
}

export interface Projecao {
  resumo: ProjecaoResumo;
  por_consultor: ProjecaoConsultor[];
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
  faturamento_total?: number;
  cidade?: string;
  uf?: string;
  segmento?: string;
  ultima_compra?: string;
  dias_sem_compra?: number;
  ticket_medio?: number;
  meta_mensal?: number;
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
  return fetchJson<Projecao>('/api/dashboard/projecao');
}

// ---------------------------------------------------------------------------
// Clientes endpoints
// ---------------------------------------------------------------------------

export interface ClientesParams {
  consultor?: string;
  situacao?: string;
  sinaleiro?: string;
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
  qs.set('limit', String(params.limit ?? 50));
  qs.set('offset', String(params.offset ?? 0));

  return fetchJson<ClientesResponse>(`/api/clientes?${qs.toString()}`);
}

export async function fetchCliente(cnpj: string): Promise<ClienteRegistro> {
  return fetchJson<ClienteRegistro>(`/api/clientes/${cnpj}`);
}

// ---------------------------------------------------------------------------
// Agenda endpoint
// ---------------------------------------------------------------------------

export async function fetchAgenda(consultor: string): Promise<AgendaItem[]> {
  return fetchJson<AgendaItem[]>(`/api/agenda/${encodeURIComponent(consultor)}`);
}
