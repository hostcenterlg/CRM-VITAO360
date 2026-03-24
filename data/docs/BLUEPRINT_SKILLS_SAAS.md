# BLUEPRINT DE SKILLS — CRM VITAO360 SaaS
# Mapeamento Motor Excel → Serviços/Skills do SaaS
# Data: 2026-03-23

---

# ARQUITETURA GERAL

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React/Next.js)                  │
│  Dashboard │ Agenda │ Carteira │ Pipeline │ Sinaleiro │ RNC │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST API / WebSocket
┌───────────────────────┴─────────────────────────────────────┐
│                    API GATEWAY                               │
│              Auth │ Rate Limit │ Routing                     │
└───────┬───────┬───────┬───────┬───────┬───────┬─────────────┘
        │       │       │       │       │       │
   ┌────┴──┐ ┌──┴───┐ ┌┴────┐ ┌┴────┐ ┌┴────┐ ┌┴─────┐
   │Cliente│ │Motor │ │Score│ │Aten-│ │Agen-│ │Import│
   │Service│ │Regras│ │Rank │ │dimen│ │da   │ │Pipe  │
   └───────┘ └──────┘ └─────┘ │to   │ │Intel│ │line  │
                               └─────┘ └─────┘ └──────┘
        │       │       │       │       │       │
   ┌────┴───────┴───────┴───────┴───────┴───────┴─────────────┐
   │                    DATABASE (PostgreSQL)                    │
   │  clientes │ atendimentos │ regras │ metas │ vendas │ rnc  │
   └───────────────────────────────────────────────────────────┘
        │               │               │
   ┌────┴────┐    ┌─────┴─────┐   ┌─────┴─────┐
   │ AI Layer│    │ Integraçõe│   │ Event Bus │
   │ (Claude)│    │ s Externas│   │ (Redis)   │
   └─────────┘    └───────────┘   └───────────┘
```

---

# SKILL 1: ClienteService (CARTEIRA)

## Origem Excel
- Aba CARTEIRA: 1.593 rows × 144 colunas
- 180.513 fórmulas → 100% substituídas por lógica de backend

## Entidades

### Cliente
```typescript
interface Cliente {
  // GRUPO 1: IDENTIDADE (A-H)
  id: string;                    // UUID
  cnpj: string;                  // 14 dígitos, zero-padded, UNIQUE
  nomeFantasia: string;
  razaoSocial: string;
  uf: string;
  cidade: string;
  email: string;
  telefone: string;
  dataCadastro: Date;

  // GRUPO 1: REDE (I-J)
  redeRegional: string | null;
  ultRegistroMercos: Date | null;

  // GRUPO 1: EQUIPE (K-L)
  consultor: Consultor;          // ENUM: LARISSA, MANU, JULIO, DAIANE
  vendedorUltimoPedido: string | null;

  // GRUPO 1: STATUS (M-N) — CALCULADOS
  situacao: Situacao;            // CALCULADO pelo motor
  prioridade: string;            // CALCULADO pelo score

  // GRUPO 1: COMPRA (O-R)
  diasSemCompra: number | null;
  dataUltimoPedido: Date | null;
  valorUltimoPedido: number | null;
  cicloMedio: number | null;

  // GRUPO 1: ECOMMERCE (S-W)
  acessoB2B: boolean;
  acessosPortal: number;
  itensCarrinho: number;
  valorB2B: number;
  oportunidade: boolean;

  // GRUPO 4: RECORRÊNCIA (BB-BI)
  ticketMedio: number | null;
  tipoCliente: TipoCliente;     // NOVO, EM DESENVOLVIMENTO, RECORRENTE, FIDELIZADO, MADURO
  nCompras: number;
  curvaABC: 'A' | 'B' | 'C' | null;
  mesesPositivado: number;
  mediaMensal: number | null;

  // SAP (CC-CQ)
  codigoClienteSAP: string | null;
  cnpjSAP: string | null;
  razaoSocialSAP: string | null;
  statusCadastroSAP: string | null;
  statusAtendimentoSAP: string | null;
  bloqueioSAP: string | null;
  grupoClienteSAP: string | null;
  gerenteNacionalSAP: string | null;
  representanteSAP: string | null;
  vendedorInternoSAP: string | null;
  canalSAP: string | null;
  tipoClienteSAP: string | null;
  macroregiaoSAP: string | null;
  microregiaoSAP: string | null;
  grupoChaveSAP: string | null;
}
```

### Enums
```typescript
enum Situacao {
  ATIVO = 'ATIVO',           // dias <= 50
  EM_RISCO = 'EM RISCO',     // 51-60 dias
  INAT_REC = 'INAT.REC',     // 61-90 dias
  INAT_ANT = 'INAT.ANT',     // >90 dias
  PROSPECT = 'PROSPECT',      // sem compra
  LEAD = 'LEAD',              // lead qualificado
  NOVO = 'NOVO',              // primeiro pedido
}

enum Consultor {
  LARISSA = 'LARISSA',
  MANU = 'MANU',
  JULIO = 'JULIO',
  DAIANE = 'DAIANE',
}

enum TipoCliente {
  NOVO = 'NOVO',
  EM_DESENVOLVIMENTO = 'EM DESENVOLVIMENTO',
  RECORRENTE = 'RECORRENTE',
  FIDELIZADO = 'FIDELIZADO',
  MADURO = 'MADURO',
}

enum Temperatura {
  QUENTE = 'QUENTE',
  MORNO = 'MORNO',
  FRIO = 'FRIO',
  CRITICO = 'CRÍTICO',
  PERDIDO = 'PERDIDO',
}

enum Sinaleiro {
  ROXO = 'ROXO',       // sem histórico
  VERDE = 'VERDE',     // saudável
  AMARELO = 'AMARELO', // atenção
  LARANJA = 'LARANJA', // alerta
  VERMELHO = 'VERMELHO', // crítico
}
```

## Lógica Calculada (substitui fórmulas)
```typescript
// SITUAÇÃO (col M) — substitui fórmula Excel
function calcularSituacao(cliente: Cliente): Situacao {
  if (!cliente.nCompras || cliente.nCompras === 0) return Situacao.PROSPECT;
  if (!cliente.diasSemCompra || cliente.diasSemCompra === 0) return Situacao.ATIVO;
  if (cliente.diasSemCompra <= 50) return Situacao.ATIVO;
  if (cliente.diasSemCompra <= 60) return Situacao.EM_RISCO;
  if (cliente.diasSemCompra <= 90) return Situacao.INAT_REC;
  return Situacao.INAT_ANT;
}

// SINALEIRO (col CB) — substitui fórmula Excel
function calcularSinaleiro(cliente: Cliente): Sinaleiro {
  if ([Situacao.PROSPECT, Situacao.LEAD].includes(cliente.situacao)) return Sinaleiro.ROXO;
  if (cliente.situacao === Situacao.NOVO) return Sinaleiro.VERDE;
  if (!cliente.diasSemCompra || !cliente.cicloMedio) return Sinaleiro.ROXO;

  const ratio = cliente.diasSemCompra / cliente.cicloMedio;
  if (ratio <= 0.5) return Sinaleiro.VERDE;
  if (ratio <= 1.0) return Sinaleiro.AMARELO;
  if (ratio <= 1.5) return Sinaleiro.LARANJA;
  return Sinaleiro.VERMELHO;
}
```

---

# SKILL 2: MotorRegrasService (MOTOR DE REGRAS)

## Origem Excel
- Aba MOTOR DE REGRAS: 92 combinações × 12 colunas
- Aba REGRAS: 496 rows com tabela tbl_MotorV2

## Interface
```typescript
interface RegraMotor {
  id: number;
  situacao: Situacao;
  resultado: Resultado;
  estagioFunil: string;
  fase: string;
  tipoContato: string;
  acaoFutura: string;
  temperatura: Temperatura;
  followUpRacional: string;
  grupoDash: string;
  tipoAcao: string;
  chave: string;                // SITUACAO+RESULTADO
}

// Lookup: dado SITUAÇÃO + RESULTADO → retorna as 9 dimensões
function aplicarMotor(situacao: Situacao, resultado: Resultado): RegraMotor {
  return regras.find(r => r.situacao === situacao && r.resultado === resultado);
}
```

## Dados: 92 regras hardcoded (source of truth)
Cada atendimento registrado pelo consultor dispara automaticamente o motor que preenche:
1. Estágio do funil
2. Fase comercial
3. Tipo de contato
4. Ação futura recomendada
5. Temperatura do lead
6. Racional do follow-up
7. Grupo de dashboard
8. Tipo de ação
9. Chave de lookup

---

# SKILL 3: ScoreService (PRIORIZAÇÃO)

## Origem Excel
- Colunas EG-EN da CARTEIRA

## Interface
```typescript
interface ScoreResult {
  urgencia: number;      // 0-100, peso 30%
  valor: number;         // 0-100, peso 25%
  followUp: number;      // 0-100, peso 20%
  sinal: number;         // 0-100, peso 15%
  tentativa: number;     // 0-100, peso 5%
  situacaoScore: number; // 0-100, peso 5%
  scoreTotal: number;    // 0-100 ponderado
  prioridade: Prioridade; // P1-P7
}

enum Prioridade {
  P1_NAMORO_NOVO = 'P1 — NAMORO NOVO',
  P2_NEGOCIACAO_ATIVA = 'P2 — NEGOCIAÇÃO ATIVA',
  P3_PROBLEMA = 'P3 — PROBLEMA',
  P4_CULTIVAR = 'P4 — CULTIVAR',
  P5_CONQUISTAR = 'P5 — CONQUISTAR',
  P6_RECUPERAR = 'P6 — RECUPERAR',
  P7_NUTRICAO = 'P7 — NUTRIÇÃO',
}

function calcularScore(cliente: ClienteComHistorico): ScoreResult {
  const urgencia = calcularUrgencia(cliente.situacao);
  const valor = calcularValor(cliente.curvaABC, cliente.tipoCliente);
  const followUp = calcularFollowUp(cliente.diasDesdeUltimoFU);
  const sinal = calcularSinal(cliente.temperatura, cliente.temEcommerce);
  const tentativa = calcularTentativa(cliente.protocoloTentativa);
  const situacaoScore = calcularSituacaoScore(cliente.situacao);

  const scoreTotal = Math.round(
    urgencia * 0.30 +
    valor * 0.25 +
    followUp * 0.20 +
    sinal * 0.15 +
    tentativa * 0.05 +
    situacaoScore * 0.05
  );

  const prioridade = calcularPrioridade(cliente);

  return { urgencia, valor, followUp, sinal, tentativa, situacaoScore, scoreTotal, prioridade };
}
```

---

# SKILL 4: AtendimentoService (LOG Consultores)

## Origem Excel
- Abas LARISSA, MANU, JULIO, DAIANE (13.159 rows × 40 cols cada)
- DRAFT 2 (4.403 registros)

## Interface
```typescript
interface Atendimento {
  id: string;
  data: Date;
  cnpj: string;
  consultor: Consultor;
  resultado: Resultado;
  tipoContato: string;
  motivo: string | null;
  descricao: string;
  tentativa: string;           // T1, T2, T3, T4+

  // CALCULADOS PELO MOTOR (automáticos)
  estagioFunil: string;        // via MotorRegrasService
  fase: string;                // via MotorRegrasService
  acaoFutura: string;          // via MotorRegrasService
  temperatura: Temperatura;    // via MotorRegrasService
  proxFollowUp: Date;          // via MotorRegrasService + regras de prazo
}

// TWO-BASE ARCHITECTURE: INVIOLÁVEL
// Atendimento.valorFinanceiro = SEMPRE R$ 0.00
// Valor só existe na entidade Venda (separada)
```

---

# SKILL 5: AgendaService (AGENDA INTELIGENTE)

## Origem Excel
- Aba AGENDA (670 rows × 18 cols)
- Regra: 40-60 atendimentos/consultor/dia

## Interface
```typescript
interface AgendaDiaria {
  data: Date;
  consultor: Consultor;
  atendimentos: AgendaItem[];   // ordenados por SCORE desc
  totalAtendimentos: number;    // max 40-60
}

interface AgendaItem {
  posicao: number;              // 1 a N
  cnpj: string;
  nomeFantasia: string;
  score: number;
  prioridade: Prioridade;
  situacao: Situacao;
  sinaleiro: Sinaleiro;
  temperatura: Temperatura;
  acaoSugerida: string;         // do Motor
  diasSemCompra: number;
  telefone: string;
  email: string;
}

// Gera agenda priorizando:
// 1. P1 (NAMORO NOVO) primeiro
// 2. P2 (NEGOCIAÇÃO ATIVA) segundo
// 3. P3 (PROBLEMA/SUPORTE) terceiro
// 4. Depois por SCORE descendente
// 5. Desempate: CURVA ABC → A primeiro
function gerarAgenda(consultor: Consultor, data: Date): AgendaDiaria {
  // 1. Filtrar clientes do consultor
  // 2. Calcular SCORE para todos
  // 3. Aplicar MOTOR para ação sugerida
  // 4. Ordenar por PRIORIDADE → SCORE
  // 5. Limitar a 40-60
  // 6. Retornar agenda formatada
}
```

---

# SKILL 6: MetaService (PROJEÇÃO)

## Origem Excel
- Aba PROJEÇÃO (662 × 80, 3.954 fórmulas XLOOKUP)
- Aba RESUMO META (totalizadores)
- Colunas CR-EF da CARTEIRA

## Interface
```typescript
interface MetaCliente {
  cnpj: string;
  metaAnual: number;           // META SAP anual
  realizadoAnual: number;
  percentualAnual: number;

  trimestres: MetaTrimestre[];
  meses: MetaMensal[];
}

interface MetaMensal {
  mes: number;                  // 1-12
  ano: number;
  metaSAP: number;
  metaIgualitaria: number;
  realizado: number;
  percentualSAP: number;
  percentualIgualitario: number;
  semanas: number[];            // vendas por semana do mês
  dataPedido: Date | null;
  justificativa: string | null;
}
```

---

# SKILL 7: SinaleiroService (PENETRAÇÃO REDES)

## Origem Excel
- Aba SINALEIRO (665 × 26, 5.785 fórmulas)
- Aba PAINEL SINALEIRO (dashboard)
- Aba REDES v2 (307 × 12)

## Interface
```typescript
interface PenetracaoRede {
  rede: string;
  totalLojas: number;
  lojasAtivas: number;
  faturamentoReal: number;
  potencialMaximo: number;     // lojas × R$525/mês × 11 meses
  percentualPenetracao: number;
  corSinaleiro: 'ROXO' | 'VERMELHO' | 'AMARELO' | 'VERDE';
  meta6Meses: number;
  cadencia: string;            // frequência de contato recomendada
}
```

---

# SKILL 8: ImportPipelineService (ETL)

## Origem Excel
- DRAFT 1 (Mercos), DRAFT 2 (Atendimentos), DRAFT 3 (SAP)

## Integrações

### Mercos API
```typescript
interface MercosImport {
  endpoint: 'pedidos' | 'clientes' | 'carteira' | 'abc';
  frequencia: 'diaria';
  transformacoes: {
    // CUIDADO: nomes de relatórios MENTEM nas datas
    // SEMPRE conferir Data Inicial / Data Final
    normalizarCNPJ: boolean;     // sempre true
    deParaVendedores: Map<string, Consultor>;
    filtrarDuplicatas: boolean;
  };
}
```

### SAP Import
```typescript
interface SAPImport {
  endpoint: 'cadastro' | 'vendas_mes_a_mes' | 'metas' | 'clientes_sem_atendimento';
  frequencia: 'semanal';
  chave: 'cnpj';
}
```

### WhatsApp (Deskrio / API direta)
```typescript
interface WhatsAppIntegration {
  modo: 'bidirecional';
  entrada: {
    // Receber mensagens → gerar ticket → LOG automático
    ticketParaAtendimento: boolean;
    classificacaoAutomatica: boolean;  // IA classifica RESULTADO
  };
  saida: {
    // Enviar mensagens a partir da AGENDA
    templateMessages: boolean;
    followUpAutomatico: boolean;
  };
}
```

### Asana
```typescript
interface AsanaIntegration {
  modo: 'bidirecional';
  // Follow-ups do Motor → Tasks no Asana
  // Conclusão no Asana → atualizar LOG no CRM
  sincronizacao: {
    followUpParaTask: boolean;
    rncParaTask: boolean;
    agendaParaTask: boolean;
  };
}
```

---

# SKILL 9: ConfigService (25 MÓDULOS REGRAS)

## Origem Excel
- Aba REGRAS (496 rows, tabela tbl_MotorV2)
- 21 Named Ranges (dropdowns)

## Interface
```typescript
interface ConfiguracaoSistema {
  listas: {
    resultado: string[];         // 14 valores
    tipoContato: string[];       // 7 valores
    motivo: string[];            // 22 valores
    situacao: string[];          // 7 valores
    fase: string[];              // 9 valores
    tipoCliente: string[];       // 7 valores
    consultor: string[];         // 5 valores
    tentativa: string[];         // 6 valores
    sinaleiro: string[];         // 8 valores
    acaoFutura: string[];        // 22 valores
    curvaABC: string[];          // 3 valores
    simNao: string[];            // 2 valores
    grupoDash: string[];         // 3 valores
  };

  motorRegras: RegraMotor[];     // 92 combinações

  scoreConfig: {
    pesoUrgencia: number;        // 0.30
    pesoValor: number;           // 0.25
    pesoFollowUp: number;        // 0.20
    pesoSinal: number;           // 0.15
    pesoTentativa: number;       // 0.05
    pesoSituacao: number;        // 0.05
  };
}
```

---

# SKILL 10: RNCService (QUALIDADE)

## Origem Excel
- Aba RNC (2.476 rows × 15 cols)

## Interface
```typescript
interface RegistroNaoConformidade {
  id: string;
  data: Date;
  cnpj: string;
  consultor: Consultor;
  tipoProblema: string;        // 8 categorias
  descricao: string;
  status: 'ABERTO' | 'EM_ANDAMENTO' | 'RESOLVIDO' | 'ENCERRADO';
  prazoResolucao: Date;
  responsavel: string;
}
```

---

# SKILL 11: DashboardService (ANALYTICS)

## Origem Excel
- Aba DASHBOARD (169 fórmulas)
- Aba PAINEL SINALEIRO (131 fórmulas)
- Aba RESUMO META (46 fórmulas)

## KPIs Principais
```typescript
interface DashboardKPIs {
  // FATURAMENTO
  faturamentoTotal: number;      // baseline: R$ 2.156.179
  faturamentoMesAtual: number;
  metaMesAtual: number;
  percentualMeta: number;

  // CARTEIRA
  totalClientes: number;
  clientesAtivos: number;
  clientesEmRisco: number;
  clientesInativos: number;
  prospects: number;

  // OPERACIONAL
  atendimentosHoje: number;
  atendimentosMes: number;
  vendasMes: number;
  ticketMedio: number;
  taxaConversao: number;

  // SINALEIRO
  distribuicaoSinaleiro: Record<Sinaleiro, number>;
  penetracaoRedes: PenetracaoRede[];

  // POR CONSULTOR
  metricsConsultor: Record<Consultor, ConsultorMetrics>;
}
```

---

# SKILL 12: AIAgentService (INTELIGÊNCIA ARTIFICIAL)

## 6 Agentes Planejados

### Agente 1: Priorizador (Agenda Inteligente)
- **Input**: Carteira + Score + Motor + Sinaleiro
- **Output**: Agenda diária otimizada por consultor
- **IA**: Preditiva — ajusta prioridades baseado em padrões de sucesso
- **Integração**: Gera tasks no Asana, envia via WhatsApp

### Agente 2: Preditor (Churn + Recompra)
- **Input**: Timeline vendas + ciclo médio + dias sem compra
- **Output**: Probabilidade de churn, data estimada de recompra
- **IA**: ML supervisionado — treina com histórico de vendas
- **Ação**: Alerta antecipado quando probabilidade de churn > 70%

### Agente 3: CS (Customer Success)
- **Input**: Jornada pós-venda + motor de regras
- **Output**: Checklist CS automático (D+4 faturamento, D+15 CS, D+30 recompra)
- **IA**: Generativa — sugere mensagens personalizadas
- **Integração**: WhatsApp automático nos marcos da jornada

### Agente 4: WhatsApp (Comunicação Contextual)
- **Input**: LOG + CARTEIRA + REGRAS + contexto da conversa
- **Output**: Respostas sugeridas, classificação automática de resultado
- **IA**: Generativa — RAG sobre histórico do cliente
- **Integração**: API WhatsApp Business

### Agente 5: Analytics (Insights)
- **Input**: Dashboard + Projeção + Tendências
- **Output**: Relatórios automáticos, anomalias, insights
- **IA**: Preditiva + Generativa — detecta padrões e explica em linguagem natural
- **Ação**: Report semanal para Leandro

### Agente 6: Funil (Pipeline Manager)
- **Input**: FUNIL + Motor + Prioridade
- **Output**: Gestão automatizada de pipeline
- **IA**: Otimização — sugere melhor momento para cada ação
- **Ação**: Move leads entre estágios automaticamente

---

# STACK TECNOLÓGICA RECOMENDADA

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| Frontend | Next.js 14+ (App Router) | SSR, performance, React Server Components |
| UI | Tailwind + shadcn/ui | Tema LIGHT (regra visual), componentes prontos |
| Backend | Node.js + tRPC ou Fastify | Type-safe, performance |
| Database | PostgreSQL + Prisma | Relacional (CNPJ como chave), ORM tipado |
| Cache | Redis | Scores calculados, sessões, filas |
| Auth | NextAuth.js / Clerk | Multi-tenant futuro |
| AI | Claude API (Anthropic) | Agentes inteligentes, RAG |
| Fila | BullMQ (Redis) | ETL async, importações, agentes |
| WhatsApp | API oficial / Deskrio | Mensagens bidirecionais |
| Mercos | REST API | Import de vendas/carteira |
| Asana | REST API | Tasks de follow-up |
| Deploy | Vercel + Railway/Fly.io | Frontend + Backend separados |
| Monitoring | Sentry + Posthog | Erros + Analytics produto |

---

*Blueprint gerado por @architect + @aiox-master*
*Baseado na radiografia forense de 40 abas e 200K+ fórmulas*
