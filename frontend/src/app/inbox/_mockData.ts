// MOCK DATA — apenas para preview demo da diretoria (Missao B10).
// Mensagens sao ficticias. Dados Mercos (ticket, ciclo) sao ilustrativos.
// Sera removido / substituido quando Fase 2a real conectar com Deskrio + banco.
// CNPJs aqui sao reais (clientes da carteira VITAO) mas mensagens NAO foram trocadas.
// Classificacao 3-tier: CNPJs = REAL | valores Mercos = SINTETICO | mensagens = DEMO

import type { InboxTicket, DeskrioMensagem, ClienteRegistro } from '@/lib/api';

// ---------------------------------------------------------------------------
// Tipos auxiliares
// ---------------------------------------------------------------------------

export interface DadosMercosMock extends Pick<
  ClienteRegistro,
  'cnpj' | 'nome_fantasia' | 'curva_abc' | 'ticket_medio' | 'faturamento_total' | 'sinaleiro'
> {
  ciclo_medio_dias: number;
  ultima_compra: string;
  dias_sem_compra: number;
  temperatura: string;
  consultor: string;
  produtos_foco: ProdutoFocoMock[];
  tarefas: TarefaMock[];
}

export interface ProdutoFocoMock {
  nome: string;
  caixas_mes: number;
  ultima_compra_label: string;
  recompra_proxima: boolean;
}

export interface TarefaMock {
  id: number;
  titulo: string;
  prazo_label: string;
  atrasada: boolean;
}

// ---------------------------------------------------------------------------
// Conversas mock (InboxTicket-compatible)
// ---------------------------------------------------------------------------

export const MOCK_CONVERSAS: InboxTicket[] = [
  {
    ticket_id: 1001,
    status: 'open',
    contato_nome: 'MEGAMIX DISTRIBUIDORA LTDA',
    contato_numero: '5547991234567',
    cnpj: '07537007000188',
    atendente_nome: 'Larissa - Vitao',
    ultima_mensagem: 'Pode mandar o orçamento por aqui mesmo, tá bom.',
    ultima_mensagem_data: new Date(Date.now() - 18 * 60 * 1000).toISOString(),
    ultima_msg_cliente_data: new Date(Date.now() - 18 * 60 * 1000).toISOString(),
    mensagens_nao_lidas: 3,
    origem: 'WhatsApp',
    aguardando_resposta: true,
  },
  {
    ticket_id: 1002,
    status: 'open',
    contato_nome: 'COMPANHIA DA TERRA COMERCIO',
    contato_numero: '5511987654321',
    cnpj: '10389839000159',
    atendente_nome: 'Manu - Vitao',
    ultima_mensagem: 'Recebi a NF, obrigado! Vou conferir o estoque.',
    ultima_mensagem_data: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
    ultima_msg_cliente_data: new Date(Date.now() - 45 * 60 * 1000).toISOString(),
    mensagens_nao_lidas: 0,
    origem: 'WhatsApp',
    aguardando_resposta: false,
  },
  {
    ticket_id: 1003,
    status: 'open',
    contato_nome: 'MMC INDUSTRIA E COMERCIO LTDA',
    contato_numero: '5541988771234',
    cnpj: '05574668000103',
    atendente_nome: 'Larissa - Vitao',
    ultima_mensagem: 'Qual o prazo de entrega pra Curitiba mesmo?',
    ultima_mensagem_data: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    ultima_msg_cliente_data: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
    mensagens_nao_lidas: 1,
    origem: 'WhatsApp',
    aguardando_resposta: true,
  },
  {
    ticket_id: 1004,
    status: 'open',
    contato_nome: 'DACOLONIA COMERCIO DE ALIMENTOS',
    contato_numero: '5548991112222',
    cnpj: '08731801000175',
    atendente_nome: 'Daiane - Vitao',
    ultima_mensagem: 'Vou conferir e te respondo até amanhã cedo.',
    ultima_mensagem_data: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    ultima_msg_cliente_data: new Date(Date.now() - 3 * 60 * 60 * 1000).toISOString(),
    mensagens_nao_lidas: 0,
    origem: 'WhatsApp',
    aguardando_resposta: false,
  },
  {
    ticket_id: 1005,
    status: 'open',
    contato_nome: 'EMPREENDIMENTOS PAGUE MENOS',
    contato_numero: '5585999334455',
    cnpj: '06626253000151',
    atendente_nome: 'Larissa - Vitao',
    ultima_mensagem: 'Preciso de 20 caixas da granola até sexta.',
    ultima_mensagem_data: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    ultima_msg_cliente_data: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
    mensagens_nao_lidas: 2,
    origem: 'WhatsApp',
    aguardando_resposta: true,
  },
  {
    ticket_id: 1006,
    status: 'open',
    contato_nome: 'NATURAL LIFE DISTRIBUIDORA',
    contato_numero: '5521997556677',
    cnpj: '12345600000100',
    atendente_nome: 'Manu - Vitao',
    ultima_mensagem: 'Tabela de preços atualizada recebida. Vou analisar.',
    ultima_mensagem_data: new Date(Date.now() - 22 * 60 * 60 * 1000).toISOString(),
    ultima_msg_cliente_data: new Date(Date.now() - 22 * 60 * 60 * 1000).toISOString(),
    mensagens_nao_lidas: 0,
    origem: 'WhatsApp',
    aguardando_resposta: false,
  },
  {
    ticket_id: 1007,
    status: 'open',
    contato_nome: 'SAUDE & SABOR COMERCIO LTDA',
    contato_numero: '5519988223344',
    cnpj: '98765400000100',
    atendente_nome: 'Manu - Vitao',
    ultima_mensagem: 'Tem algo novo na linha de snacks? Cliente perguntou.',
    ultima_mensagem_data: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    ultima_msg_cliente_data: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
    mensagens_nao_lidas: 0,
    origem: 'WhatsApp',
    aguardando_resposta: false,
  },
  {
    ticket_id: 1008,
    status: 'closed',
    contato_nome: 'ORGÂNICOS DO VALE LTDA',
    contato_numero: '5562977889900',
    cnpj: '11223300000100',
    atendente_nome: 'Larissa - Vitao',
    ultima_mensagem: 'Pedido #14521 confirmado. Obrigado!',
    ultima_mensagem_data: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    ultima_msg_cliente_data: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
    mensagens_nao_lidas: 0,
    origem: 'WhatsApp',
    aguardando_resposta: false,
  },
];

// ---------------------------------------------------------------------------
// Mensagens mock por ticket (conversa simulada)
// ---------------------------------------------------------------------------

function isoMinsAgo(mins: number): string {
  return new Date(Date.now() - mins * 60 * 1000).toISOString();
}

export const MOCK_MENSAGENS: Record<number, DeskrioMensagem[]> = {
  1001: [
    { id: 10010, texto: 'Oi Larissa! Tudo bem? Precisava falar sobre o pedido de granola.', de_cliente: true, timestamp: isoMinsAgo(90), tipo: 'chat' },
    { id: 10011, texto: 'Oi! Tudo ótimo! Claro, me conta. Tem interesse em quanto?', de_cliente: false, timestamp: isoMinsAgo(85), tipo: 'chat', nome_contato: 'Larissa - Vitao' },
    { id: 10012, texto: 'Pensei em umas 50 caixas da Granola Premium 1kg. Qual o melhor prazo?', de_cliente: true, timestamp: isoMinsAgo(80), tipo: 'chat' },
    { id: 10013, texto: 'Para 50 caixas consigo em 5 dias úteis. Posso fazer um preço especial também — vou montar um orçamento.', de_cliente: false, timestamp: isoMinsAgo(75), tipo: 'chat', nome_contato: 'Larissa - Vitao' },
    { id: 10014, texto: 'Ótimo! E a pasta de amendoim, tem estoque?', de_cliente: true, timestamp: isoMinsAgo(30), tipo: 'chat' },
    { id: 10015, texto: 'Sim! A Pasta de Amendoim 1kg está com estoque normal. Incluo no orçamento?', de_cliente: false, timestamp: isoMinsAgo(25), tipo: 'chat', nome_contato: 'Larissa - Vitao' },
    { id: 10016, texto: 'Pode mandar o orçamento por aqui mesmo, tá bom.', de_cliente: true, timestamp: isoMinsAgo(18), tipo: 'chat' },
  ],
  1002: [
    { id: 10020, texto: 'Bom dia! A NF 4521 chegou aqui.', de_cliente: true, timestamp: isoMinsAgo(120), tipo: 'chat' },
    { id: 10021, texto: 'Bom dia! Que bom, chegou dentro do prazo então.', de_cliente: false, timestamp: isoMinsAgo(115), tipo: 'chat', nome_contato: 'Manu - Vitao' },
    { id: 10022, texto: 'Chegou sim. Vou abrir os volumes agora para conferir.', de_cliente: true, timestamp: isoMinsAgo(100), tipo: 'chat' },
    { id: 10023, texto: 'Pode conferir com calma. Qualquer divergência me chama!', de_cliente: false, timestamp: isoMinsAgo(95), tipo: 'chat', nome_contato: 'Manu - Vitao' },
    { id: 10024, texto: 'Recebi a NF, obrigado! Vou conferir o estoque.', de_cliente: true, timestamp: isoMinsAgo(45), tipo: 'chat' },
  ],
  1003: [
    { id: 10030, texto: 'Oi! Queria saber sobre o prazo de entrega para Curitiba.', de_cliente: true, timestamp: isoMinsAgo(180), tipo: 'chat' },
    { id: 10031, texto: 'Oi! Para Curitiba o prazo é 4 a 6 dias úteis. Está precisando para alguma data específica?', de_cliente: false, timestamp: isoMinsAgo(175), tipo: 'chat', nome_contato: 'Larissa - Vitao' },
    { id: 10032, texto: 'Preciso até dia 10. Pedido hoje daria?', de_cliente: true, timestamp: isoMinsAgo(160), tipo: 'chat' },
    { id: 10033, texto: 'Sim, confirmando hoje até as 14h já entra no lote de amanhã. Vai dar certo!', de_cliente: false, timestamp: isoMinsAgo(155), tipo: 'chat', nome_contato: 'Larissa - Vitao' },
    { id: 10034, texto: 'Qual o prazo de entrega pra Curitiba mesmo?', de_cliente: true, timestamp: isoMinsAgo(120), tipo: 'chat' },
  ],
  1004: [
    { id: 10040, texto: 'Daiane, vi que tem promoção no mix de oleaginosas essa semana?', de_cliente: true, timestamp: isoMinsAgo(240), tipo: 'chat' },
    { id: 10041, texto: 'Oi! Sim, 10% no Mix Castanhas 500g até sexta. Interesse?', de_cliente: false, timestamp: isoMinsAgo(230), tipo: 'chat', nome_contato: 'Daiane - Vitao' },
    { id: 10042, texto: 'Tenho interesse sim. Me manda os detalhes que repasso pro comprador.', de_cliente: true, timestamp: isoMinsAgo(220), tipo: 'chat' },
    { id: 10043, texto: 'Enviei a tabela por e-mail também. Qualquer dúvida estou aqui!', de_cliente: false, timestamp: isoMinsAgo(215), tipo: 'chat', nome_contato: 'Daiane - Vitao' },
    { id: 10044, texto: 'Vou conferir e te respondo até amanhã cedo.', de_cliente: true, timestamp: isoMinsAgo(180), tipo: 'chat' },
  ],
  1005: [
    { id: 10050, texto: 'Bom dia Larissa! Fechamento de mês chegou hehe', de_cliente: true, timestamp: isoMinsAgo(360), tipo: 'chat' },
    { id: 10051, texto: 'Bom dia! Vamos nessa. O que você precisa?', de_cliente: false, timestamp: isoMinsAgo(355), tipo: 'chat', nome_contato: 'Larissa - Vitao' },
    { id: 10052, texto: 'Preciso de 20 caixas da granola até sexta. Vai rolar?', de_cliente: true, timestamp: isoMinsAgo(300), tipo: 'chat' },
    { id: 10053, texto: 'Vou verificar estoque e te confirmo em 1h!', de_cliente: false, timestamp: isoMinsAgo(295), tipo: 'chat', nome_contato: 'Larissa - Vitao' },
    { id: 10054, texto: 'Preciso de 20 caixas da granola até sexta.', de_cliente: true, timestamp: isoMinsAgo(300), tipo: 'chat' },
  ],
  1006: [
    { id: 10060, texto: 'Manu, chegou a tabela de preços atualizada de abril?', de_cliente: true, timestamp: isoMinsAgo(1440), tipo: 'chat' },
    { id: 10061, texto: 'Enviando agora pelo WhatsApp mesmo!', de_cliente: false, timestamp: isoMinsAgo(1430), tipo: 'chat', nome_contato: 'Manu - Vitao' },
    { id: 10062, texto: 'Tabela de preços atualizada recebida. Vou analisar.', de_cliente: true, timestamp: isoMinsAgo(1320), tipo: 'chat' },
  ],
  1007: [
    { id: 10070, texto: 'Tem algo novo na linha de snacks saudáveis? Meu cliente perguntou sobre snacks proteicos.', de_cliente: true, timestamp: isoMinsAgo(2880), tipo: 'chat' },
    { id: 10071, texto: 'Boa pergunta! Temos o Mix Power com whey isolado chegando semana que vem. Posso te mandar o pre-lançamento.', de_cliente: false, timestamp: isoMinsAgo(2870), tipo: 'chat', nome_contato: 'Manu - Vitao' },
    { id: 10072, texto: 'Tem algo novo na linha de snacks? Cliente perguntou.', de_cliente: true, timestamp: isoMinsAgo(2880), tipo: 'chat' },
  ],
  1008: [
    { id: 10080, texto: 'Larissa, pode confirmar o pedido #14521?', de_cliente: true, timestamp: isoMinsAgo(4320), tipo: 'chat' },
    { id: 10081, texto: 'Confirmado! Saiu hoje para entrega.', de_cliente: false, timestamp: isoMinsAgo(4310), tipo: 'chat', nome_contato: 'Larissa - Vitao' },
    { id: 10082, texto: 'Pedido #14521 confirmado. Obrigado!', de_cliente: true, timestamp: isoMinsAgo(4300), tipo: 'chat' },
  ],
};

// ---------------------------------------------------------------------------
// Dados Mercos mock por cliente
// ---------------------------------------------------------------------------

export const MOCK_DADOS_MERCOS: Record<number, DadosMercosMock> = {
  1001: {
    cnpj: '07537007000188',
    nome_fantasia: 'MEGAMIX DISTRIBUIDORA',
    curva_abc: 'A',
    ticket_medio: 18750,
    faturamento_total: 187500,
    sinaleiro: 'ATIVO',
    ciclo_medio_dias: 21,
    ultima_compra: '2026-04-07',
    dias_sem_compra: 22,
    temperatura: 'Quente',
    consultor: 'LARISSA',
    produtos_foco: [
      { nome: 'Granola Premium 1kg', caixas_mes: 18, ultima_compra_label: 'há 22 dias', recompra_proxima: true },
      { nome: 'Mix Castanhas 500g', caixas_mes: 10, ultima_compra_label: 'há 22 dias', recompra_proxima: false },
      { nome: 'Pasta Amendoim 1kg', caixas_mes: 7, ultima_compra_label: 'há 22 dias', recompra_proxima: false },
    ],
    tarefas: [
      { id: 1, titulo: 'Enviar orçamento granola (50 cx)', prazo_label: 'Hoje', atrasada: false },
      { id: 2, titulo: 'Confirmar pedido #15021', prazo_label: 'Em 2 dias', atrasada: false },
    ],
  },
  1002: {
    cnpj: '10389839000159',
    nome_fantasia: 'COMPANHIA DA TERRA',
    curva_abc: 'A',
    ticket_medio: 12450,
    faturamento_total: 149400,
    sinaleiro: 'ATIVO',
    ciclo_medio_dias: 18,
    ultima_compra: '2026-04-11',
    dias_sem_compra: 18,
    temperatura: 'Quente',
    consultor: 'MANU',
    produtos_foco: [
      { nome: 'Granola Premium 1kg', caixas_mes: 12, ultima_compra_label: 'há 18 dias', recompra_proxima: true },
      { nome: 'Mix Castanhas 500g', caixas_mes: 8, ultima_compra_label: 'há 25 dias', recompra_proxima: false },
      { nome: 'Pasta Amendoim 1kg', caixas_mes: 5, ultima_compra_label: 'há 12 dias', recompra_proxima: false },
    ],
    tarefas: [
      { id: 3, titulo: 'Enviar tabela atualizada', prazo_label: 'Hoje', atrasada: false },
      { id: 4, titulo: 'Confirmar pedido #12345', prazo_label: 'Em 3 dias', atrasada: false },
    ],
  },
  1003: {
    cnpj: '05574668000103',
    nome_fantasia: 'MMC INDUSTRIA E COMERCIO',
    curva_abc: 'B',
    ticket_medio: 8900,
    faturamento_total: 89000,
    sinaleiro: 'ATIVO',
    ciclo_medio_dias: 30,
    ultima_compra: '2026-03-30',
    dias_sem_compra: 30,
    temperatura: 'Morno',
    consultor: 'LARISSA',
    produtos_foco: [
      { nome: 'Aveia em Flocos 500g', caixas_mes: 15, ultima_compra_label: 'há 30 dias', recompra_proxima: true },
      { nome: 'Granola Premium 1kg', caixas_mes: 6, ultima_compra_label: 'há 30 dias', recompra_proxima: false },
    ],
    tarefas: [
      { id: 5, titulo: 'Responder sobre prazo entrega Curitiba', prazo_label: 'Hoje', atrasada: false },
    ],
  },
  1004: {
    cnpj: '08731801000175',
    nome_fantasia: 'DACOLONIA ALIMENTOS',
    curva_abc: 'B',
    ticket_medio: 6200,
    faturamento_total: 74400,
    sinaleiro: 'ATIVO',
    ciclo_medio_dias: 25,
    ultima_compra: '2026-04-04',
    dias_sem_compra: 25,
    temperatura: 'Morno',
    consultor: 'DAIANE',
    produtos_foco: [
      { nome: 'Mix Castanhas 500g', caixas_mes: 10, ultima_compra_label: 'há 25 dias', recompra_proxima: true },
      { nome: 'Amendoim Torrado 500g', caixas_mes: 8, ultima_compra_label: 'há 25 dias', recompra_proxima: false },
    ],
    tarefas: [
      { id: 6, titulo: 'Aguardar resposta promoção oleaginosas', prazo_label: 'Amanha', atrasada: false },
    ],
  },
  1005: {
    cnpj: '06626253000151',
    nome_fantasia: 'PAGUE MENOS',
    curva_abc: 'A',
    ticket_medio: 22000,
    faturamento_total: 264000,
    sinaleiro: 'ATIVO',
    ciclo_medio_dias: 15,
    ultima_compra: '2026-04-14',
    dias_sem_compra: 15,
    temperatura: 'Quente',
    consultor: 'LARISSA',
    produtos_foco: [
      { nome: 'Granola Premium 1kg', caixas_mes: 25, ultima_compra_label: 'há 15 dias', recompra_proxima: true },
      { nome: 'Barra Proteica Caixa 12un', caixas_mes: 18, ultima_compra_label: 'há 15 dias', recompra_proxima: false },
      { nome: 'Whey Vegano 500g', caixas_mes: 12, ultima_compra_label: 'há 20 dias', recompra_proxima: false },
    ],
    tarefas: [
      { id: 7, titulo: 'Confirmar disponibilidade 20cx granola', prazo_label: 'Hoje', atrasada: false },
      { id: 8, titulo: 'Enviar contrato renovacao 2026', prazo_label: 'Atrasada 2 dias', atrasada: true },
    ],
  },
  1006: {
    cnpj: '12345600000100',
    nome_fantasia: 'NATURAL LIFE',
    curva_abc: 'C',
    ticket_medio: 4500,
    faturamento_total: 36000,
    sinaleiro: 'INAT.REC',
    ciclo_medio_dias: 45,
    ultima_compra: '2026-03-15',
    dias_sem_compra: 45,
    temperatura: 'Frio',
    consultor: 'MANU',
    produtos_foco: [
      { nome: 'Aveia Flocos 500g', caixas_mes: 5, ultima_compra_label: 'há 45 dias', recompra_proxima: true },
    ],
    tarefas: [
      { id: 9, titulo: 'Reativar cliente — ligacao de boas-vindas', prazo_label: 'Atrasada 5 dias', atrasada: true },
    ],
  },
  1007: {
    cnpj: '98765400000100',
    nome_fantasia: 'SAUDE E SABOR',
    curva_abc: 'B',
    ticket_medio: 7800,
    faturamento_total: 62400,
    sinaleiro: 'ATIVO',
    ciclo_medio_dias: 28,
    ultima_compra: '2026-04-01',
    dias_sem_compra: 28,
    temperatura: 'Morno',
    consultor: 'MANU',
    produtos_foco: [
      { nome: 'Mix Castanhas 500g', caixas_mes: 9, ultima_compra_label: 'há 28 dias', recompra_proxima: true },
      { nome: 'Snack Vegano 30g', caixas_mes: 14, ultima_compra_label: 'há 28 dias', recompra_proxima: false },
    ],
    tarefas: [
      { id: 10, titulo: 'Enviar informacoes Mix Power (lancamento)', prazo_label: 'Em 3 dias', atrasada: false },
    ],
  },
  1008: {
    cnpj: '11223300000100',
    nome_fantasia: 'ORGANICOS DO VALE',
    curva_abc: 'B',
    ticket_medio: 9100,
    faturamento_total: 109200,
    sinaleiro: 'ATIVO',
    ciclo_medio_dias: 20,
    ultima_compra: '2026-04-26',
    dias_sem_compra: 3,
    temperatura: 'Quente',
    consultor: 'LARISSA',
    produtos_foco: [
      { nome: 'Granola Organica 500g', caixas_mes: 20, ultima_compra_label: 'há 3 dias', recompra_proxima: false },
      { nome: 'Quinoa 500g', caixas_mes: 8, ultima_compra_label: 'há 3 dias', recompra_proxima: false },
    ],
    tarefas: [],
  },
};

// ---------------------------------------------------------------------------
// Status WhatsApp mock (demo — conexoes ativas)
// ---------------------------------------------------------------------------

export const MOCK_WA_STATUS = {
  configurado: true,
  alguma_conectada: true,
  total_conexoes: 3,
  conexoes: [
    { id: 1, nome: 'Mais Granel', status: 'CONNECTED', status_legivel: 'Conectado' },
    { id: 2, nome: 'Central Vitao', status: 'CONNECTED', status_legivel: 'Conectado' },
    { id: 3, nome: 'Vitao Alimentos', status: 'CONNECTING', status_legivel: 'Reconectando' },
  ],
};

// ---------------------------------------------------------------------------
// Helper: temperatura para badge
// ---------------------------------------------------------------------------

export function getTemperaturaBadge(temperatura: string | undefined): {
  label: string;
  classes: string;
} {
  const t = (temperatura ?? '').toLowerCase();
  if (t === 'quente') return { label: 'Quente', classes: 'bg-green-100 text-green-700' };
  if (t === 'morno') return { label: 'Morno', classes: 'bg-yellow-100 text-yellow-700' };
  return { label: 'Frio', classes: 'bg-gray-100 text-gray-600' };
}

export function getTemperaturaAvatarBg(temperatura: string | undefined): string {
  const t = (temperatura ?? '').toLowerCase();
  if (t === 'quente') return 'bg-vitao-green';
  if (t === 'morno') return 'bg-vitao-orange';
  return 'bg-gray-400';
}
