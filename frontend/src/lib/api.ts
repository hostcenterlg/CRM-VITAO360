// API client para CRM VITAO360 — tipado, auth via JWT, BRL-ready

import { getToken } from '@/lib/auth';

const BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

// ---------------------------------------------------------------------------
// Helpers internos
// ---------------------------------------------------------------------------

async function fetchJson<T>(path: string, options?: RequestInit): Promise<T> {
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
  method: 'POST' | 'PUT' | 'DELETE',
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
}

export interface AtendimentoResponse {
  id: number;
  cnpj: string;
  resultado: string;
  descricao: string;
  data_registro: string;
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
