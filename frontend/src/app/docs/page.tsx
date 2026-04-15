'use client';

import { useState } from 'react';

// ---------------------------------------------------------------------------
// /docs — Manual do CRM VITAO360
// 3 tabs por role: Consultor, Gerente, Admin
// ---------------------------------------------------------------------------

type Role = 'consultor' | 'gerente' | 'admin';

interface Section {
  title: string;
  icon: React.ReactNode;
  content: React.ReactNode;
}

// ---------------------------------------------------------------------------
// Icons inline
// ---------------------------------------------------------------------------

function IconDashboard() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    </svg>
  );
}

function IconAgenda() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  );
}

function IconCarteira() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

function IconPipeline() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
    </svg>
  );
}

function IconInbox() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
    </svg>
  );
}

function IconIA() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
    </svg>
  );
}

function IconProjecao() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
    </svg>
  );
}

function IconRedes() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
    </svg>
  );
}

function IconImport() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
    </svg>
  );
}

function IconMotor() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}

function IconUsuarios() {
  return (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
        d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Accordion item
// ---------------------------------------------------------------------------

function AccordionItem({ section, defaultOpen = false }: { section: Section; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <div className={`border rounded-xl overflow-hidden transition-all ${open ? 'border-green-200 shadow-sm' : 'border-gray-200'}`}>
      <button
        type="button"
        onClick={() => setOpen((p) => !p)}
        className={`w-full flex items-center gap-3 px-4 py-3 min-h-[44px] text-left transition-colors
          ${open ? 'bg-green-50' : 'bg-white hover:bg-gray-50'}`}
      >
        <span className={`flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center
          ${open ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
          {section.icon}
        </span>
        <span className={`flex-1 text-sm font-semibold ${open ? 'text-green-800' : 'text-gray-800'}`}>
          {section.title}
        </span>
        <svg
          className={`w-4 h-4 flex-shrink-0 transition-transform text-gray-400 ${open ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="px-4 pb-4 pt-3 bg-white border-t border-gray-100 text-sm text-gray-700 leading-relaxed space-y-2">
          {section.content}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Tip box
// ---------------------------------------------------------------------------

function Tip({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex gap-2 p-3 bg-blue-50 border border-blue-100 rounded-lg text-xs text-blue-800">
      <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>{children}</span>
    </div>
  );
}

function Warning({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex gap-2 p-3 bg-amber-50 border border-amber-100 rounded-lg text-xs text-amber-800">
      <svg className="w-4 h-4 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
      </svg>
      <span>{children}</span>
    </div>
  );
}

function ScreenPlaceholder({ label }: { label: string }) {
  return (
    <div className="w-full rounded-lg border-2 border-dashed border-gray-200 bg-gray-50 py-6 flex flex-col items-center justify-center text-gray-400 text-xs gap-1">
      <svg className="w-6 h-6 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
      <span>{label}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Section content builders
// ---------------------------------------------------------------------------

const SECTIONS_CONSULTOR: Section[] = [
  {
    title: 'Agenda Diaria',
    icon: <IconAgenda />,
    content: (
      <>
        <p>
          A agenda diaria e gerada automaticamente pelo Motor de Regras. Ela mostra os 40 clientes
          mais prioritarios para contato hoje, ordenados por score de urgencia.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li>Clientes em vermelho = sem compra ha mais de 90 dias. Prioridade maxima.</li>
          <li>Clientes em amarelo = em risco. Entre em contato esta semana.</li>
          <li>Clientes em verde = saudaveis. Mantenha o relacionamento.</li>
          <li>Clique em um cliente para ver o historico completo e registrar atendimento.</li>
        </ul>
        <Tip>Use a agenda como roteiro diario. Nao pule clientes vermelhos — eles sao os mais propensos a cancelar.</Tip>
        <ScreenPlaceholder label="Tela: Agenda Diaria com lista de clientes priorizados" />
      </>
    ),
  },
  {
    title: 'Registrar Atendimento',
    icon: <IconInbox />,
    content: (
      <>
        <p>
          Para registrar um atendimento, abra o cliente na Carteira ou Agenda e clique em
          &quot;Registrar Atendimento&quot;. Preencha o tipo (ligacao, visita, WhatsApp), resultado e observacoes.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li><strong>Tipo:</strong> Ligacao, Visita Presencial, WhatsApp, E-mail</li>
          <li><strong>Resultado:</strong> Positivo (comprou ou vai comprar), Neutro, Negativo (recusou)</li>
          <li><strong>Observacoes:</strong> O que foi discutido, proximos passos, objecoes</li>
        </ul>
        <Warning>
          Atendimentos sem resultado preenchido nao contam para o score do cliente. Preencha sempre.
        </Warning>
        <ScreenPlaceholder label="Tela: Modal de registro de atendimento" />
      </>
    ),
  },
  {
    title: 'Carteira de Clientes',
    icon: <IconCarteira />,
    content: (
      <>
        <p>
          A carteira contem todos os seus clientes ativos e inativos. Use os filtros para segmentar
          por situacao, UF, rede, classificacao ABC e ultimo contato.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li>Classificacao ABC: A = top 20% faturamento, B = 30%, C = restante</li>
          <li>Sinaleiro: VERDE (ativo), AMARELO (em risco), VERMELHO (inativo recente), ROXO (prospect)</li>
          <li>Clique no cliente para ver detalhe completo: historico, compras, score, timeline</li>
          <li>Use Ctrl+K para busca rapida por nome ou CNPJ</li>
        </ul>
        <Tip>Filtre por &quot;Sinaleiro VERMELHO&quot; para identificar quem precisa de atencao urgente.</Tip>
        <ScreenPlaceholder label="Tela: Carteira com filtros ativos e lista de clientes" />
      </>
    ),
  },
  {
    title: 'Pipeline de Vendas',
    icon: <IconPipeline />,
    content: (
      <>
        <p>
          O pipeline mostra seus clientes em cada estagio do funil comercial. Arraste os cards
          para mover entre estagios. Use os swimlanes para ver por vendedor ou situacao.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li>Estagios: Prospect → Primeiro Contato → Proposta → Negociacao → Ganho / Perdido</li>
          <li>Arraste com o mouse (ou toque longo no mobile) para mover entre colunas</li>
          <li>Clique no card para abrir detalhes e editar estagio + observacoes</li>
          <li>Atalho N = novo lead, I = ver indicadores do pipeline</li>
        </ul>
        <Tip>Mantenha o pipeline atualizado. O Motor usa o estagio para calcular o score de oportunidade.</Tip>
        <ScreenPlaceholder label="Tela: Pipeline Kanban com estagios e cards de clientes" />
      </>
    ),
  },
  {
    title: 'Inbox WhatsApp',
    icon: <IconInbox />,
    content: (
      <>
        <p>
          O Inbox espelha em tempo real as conversas WhatsApp do Deskrio. Clique em um contato
          para ver o historico completo de mensagens. As mensagens atualizam automaticamente a cada 30 segundos.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li>Mensagens de texto, imagens, audios, videos e documentos sao exibidos inline</li>
          <li>Clique na imagem para ampliar (lightbox). Audio tem player integrado.</li>
          <li>Botao de refresh manual no topo direito da conversa</li>
          <li>O numero de contato e vinculado automaticamente ao cliente na carteira</li>
        </ul>
        <Warning>
          O Inbox e apenas leitura. Para enviar mensagens, use o WhatsApp diretamente.
          O CRM registra o historico recebido do Deskrio.
        </Warning>
        <ScreenPlaceholder label="Tela: Inbox com lista de conversas e mensagens" />
      </>
    ),
  },
  {
    title: 'Central de IA',
    icon: <IconIA />,
    content: (
      <>
        <p>
          A Central de IA analisa cada cliente individualmente e gera recomendacoes personalizadas.
          Acesse via menu lateral &quot;Inteligencia IA&quot; ou pela pagina de detalhe do cliente.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li><strong>Briefing de Visita:</strong> resumo completo do cliente antes de ligar</li>
          <li><strong>Mensagem WhatsApp:</strong> sugestao de mensagem personalizada para o contato</li>
          <li><strong>Analise de Churn:</strong> probabilidade de cancelamento e motivos principais</li>
          <li><strong>Recomendacao de Produto:</strong> produtos mais propensos a comprar agora</li>
          <li><strong>Resumo de Interacoes:</strong> consolidado dos ultimos atendimentos</li>
          <li><strong>Analise de Sentimento:</strong> tom geral das conversas recentes</li>
        </ul>
        <Tip>
          Use o Briefing ANTES de ligar para o cliente. Ele consolida historico, ultima compra,
          produtos favoritos e alertas em um texto pronto para leitura rapida.
        </Tip>
        <ScreenPlaceholder label="Tela: Central de IA com 9 cards de agentes" />
      </>
    ),
  },
];

const SECTIONS_GERENTE: Section[] = [
  ...SECTIONS_CONSULTOR,
  {
    title: 'Dashboard CEO',
    icon: <IconDashboard />,
    content: (
      <>
        <p>
          O dashboard mostra KPIs em tempo real. Use os filtros de mes, ano e vendedor para
          segmentar a visao. As 8 abas cobrem diferentes perspectivas do negocio.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li><strong>Resumo:</strong> faturamento total, ticket medio, positivacao, churn</li>
          <li><strong>Operacional:</strong> atividades por tipo e resultado por consultor</li>
          <li><strong>Funil:</strong> clientes em cada estagio do pipeline</li>
          <li><strong>Performance:</strong> ranking de consultores por faturamento e positivacao</li>
          <li><strong>Saude:</strong> distribuicao VERDE/AMARELO/VERMELHO/ROXO da carteira</li>
          <li><strong>Redes:</strong> desempenho por rede/franquia (BIOMUNDO, MUNDO VERDE, etc.)</li>
          <li><strong>Indicadores Mercos:</strong> evolucao de vendas, positivacao diaria, curva ABC</li>
          <li><strong>Produtividade:</strong> esforco vs resultado por consultor</li>
        </ul>
        <Tip>O widget &quot;Insight do Dia&quot; no topo do dashboard e gerado pela IA com base nos dados mais recentes.</Tip>
        <ScreenPlaceholder label="Tela: Dashboard CEO com 8 abas e graficos" />
      </>
    ),
  },
  {
    title: 'Projecao Comercial',
    icon: <IconProjecao />,
    content: (
      <>
        <p>
          A pagina de projecao calcula o forecast do mes atual e do ano com base nas metas SAP
          e no ritmo de vendas atual. Atualiza automaticamente quando novos dados sao importados.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li>Progresso vs meta por vendedor e consolidado</li>
          <li>Projecao linear do mes com base nos dias uteis restantes</li>
          <li>Alerta automatico se projecao for abaixo de 80% da meta</li>
          <li>Historico mensal para comparacao ano a ano</li>
        </ul>
        <ScreenPlaceholder label="Tela: Projecao com barras de progresso vs meta" />
      </>
    ),
  },
  {
    title: 'Redes e Franquias',
    icon: <IconRedes />,
    content: (
      <>
        <p>
          A pagina de Redes agrupa os clientes que fazem parte de franquias e redes de lojas
          (BIOMUNDO, MUNDO VERDE, EMPORIO, etc.). Permite visao consolidada por grupo.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li>Faturamento consolidado por rede</li>
          <li>Penetracao: quantas unidades da rede sao clientes ativos</li>
          <li>Oportunidade: unidades que ainda nao compram</li>
          <li>Responsavel DAIANE para Key Accounts de redes</li>
        </ul>
        <Warning>
          Clientes de rede sao gerenciados pela DAIANE. Consultores nao devem abordar diretamente
          sem alinhamento previo.
        </Warning>
        <ScreenPlaceholder label="Tela: Redes com grupos, unidades e faturamento" />
      </>
    ),
  },
  {
    title: 'Redistribuicao de Carteira',
    icon: <IconUsuarios />,
    content: (
      <>
        <p>
          A ferramenta de redistribuicao permite transferir clientes entre consultores de forma
          controlada. Cada movimentacao gera log de auditoria automatico.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li>Selecione os clientes pelo filtro de UF, rede ou situacao</li>
          <li>Escolha o consultor de origem e destino</li>
          <li>Confirme a operacao — ela e reversivel ate o proximo recalculo do Motor</li>
          <li>Log completo disponivel no historico do cliente</li>
        </ul>
        <Warning>
          Esta operacao requer aprovacao L3 (Leandro). Consulte antes de redistribuir carteiras grandes.
        </Warning>
        <ScreenPlaceholder label="Tela: Redistribuicao com seletor de consultores" />
      </>
    ),
  },
];

const SECTIONS_ADMIN: Section[] = [
  ...SECTIONS_GERENTE,
  {
    title: 'Import de Dados',
    icon: <IconImport />,
    content: (
      <>
        <p>
          Faca upload de planilhas Mercos ou SAP para atualizar os dados automaticamente.
          O sistema processa o arquivo, valida o schema e insere os registros no banco.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li><strong>Mercos:</strong> relatórios de vendas e indicadores exportados do app.mercos.com</li>
          <li><strong>SAP:</strong> extratos de faturamento e metas do ERP corporativo</li>
          <li>Formato aceito: XLSX. Tamanho maximo: 50 MB</li>
          <li>O import e idempotente — rodar duas vezes nao duplica dados</li>
          <li>Erros de validacao sao exibidos linha a linha no relatorio pos-upload</li>
        </ul>
        <Warning>
          Relatórios Mercos MENTEM no nome do arquivo. Sempre verifique as datas reais
          nas linhas 6-7 do relatório antes de importar.
        </Warning>
        <ScreenPlaceholder label="Tela: Import com drag-and-drop e historico de imports" />
      </>
    ),
  },
  {
    title: 'Motor de Regras',
    icon: <IconMotor />,
    content: (
      <>
        <p>
          O Motor de Regras recalcula o score, temperatura, sinaleiro e agenda de todos os clientes.
          Execute manualmente ou aguarde o recalculo automatico diario (meia-noite).
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li>Clique em &quot;Recalcular Agora&quot; para forcar o recalculo imediato</li>
          <li>Acompanhe o progresso em tempo real — 1.581 clientes em ~2 minutos</li>
          <li>Edite as regras de pontuacao na tabela inferior (aprovacao L3 necessaria)</li>
          <li>Historico de recalculos com timestamp e metricas de resultado</li>
        </ul>
        <Tip>
          Apos importar novos dados (Mercos ou SAP), execute o Motor manualmente para
          atualizar agenda e scores antes que os consultores comecem o dia.
        </Tip>
        <ScreenPlaceholder label="Tela: Motor com status de recalculo e lista de regras" />
      </>
    ),
  },
  {
    title: 'Gestao de Usuarios',
    icon: <IconUsuarios />,
    content: (
      <>
        <p>
          Crie, edite e desative usuarios do sistema. Cada usuario tem um role que define
          o que pode visualizar e editar.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li><strong>Admin (roxo):</strong> acesso total. Motor, Import, Usuarios, Pipeline</li>
          <li><strong>Gerente (azul):</strong> Dashboard completo, Projecao, Redes, Redistribuicao</li>
          <li><strong>Consultor (verde):</strong> sua carteira, Agenda, Pipeline, Inbox, IA</li>
          <li><strong>Consultor Externo (cinza):</strong> apenas leitura da propria carteira</li>
        </ul>
        <Warning>
          Sempre vincule o usuario ao consultor correto no campo &quot;Consultor Nome&quot;.
          Sem esse vinculo, o sistema nao filtra a carteira corretamente.
        </Warning>
        <ScreenPlaceholder label="Tela: Lista de usuarios com roles e status" />
      </>
    ),
  },
  {
    title: 'Pipeline de Dados',
    icon: <IconPipeline />,
    content: (
      <>
        <p>
          O Pipeline de Dados monitora o fluxo automatico de sincronizacao entre Deskrio,
          Mercos e o banco de dados. Exibe historico de execucoes e alertas de falha.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li>Sync Deskrio: roda a cada 6 horas, atualiza contatos e logs de Kanban</li>
          <li>Sync Mercos: manual ou agendado, importa indicadores e pedidos ativos</li>
          <li>Webhook Deskrio: recebe eventos em tempo real (nova mensagem WA, mudanca de etapa)</li>
          <li>Alertas de falha enviados para o sino de notificacoes do admin</li>
        </ul>
        <ScreenPlaceholder label="Tela: Pipeline com status de cada sync e historico" />
      </>
    ),
  },
  {
    title: 'Central de IA (Admin)',
    icon: <IconIA />,
    content: (
      <>
        <p>
          Alem dos 9 agentes disponiveis para todos os usuarios, o admin tem acesso a dois
          agentes extras para analise de carteira e gestao de equipe.
        </p>
        <ul className="list-disc list-inside space-y-1 text-sm text-gray-600 mt-2">
          <li><strong>Coach de Vendas:</strong> identifica padroes de performance e sugere acoes para cada consultor</li>
          <li><strong>Oportunidade de Expansao:</strong> clientes com potencial de crescimento de ticket medio</li>
          <li><strong>Previsao de Faturamento:</strong> modelo preditivo para o mes corrente</li>
          <li>Todos os outputs sao baseados em dados reais — zero fabricacao</li>
        </ul>
        <Tip>
          Use o agente de Coach semanalmente para identificar consultores que precisam
          de suporte ou treinamento com base em dados objetivos.
        </Tip>
        <ScreenPlaceholder label="Tela: Central de IA com 9 cards interativos" />
      </>
    ),
  },
];

// ---------------------------------------------------------------------------
// Role tab config
// ---------------------------------------------------------------------------

const ROLE_CONFIG: Record<Role, { label: string; subtitle: string; color: string; sections: Section[] }> = {
  consultor: {
    label: 'Consultor',
    subtitle: 'MANU, LARISSA, JULIO',
    color: 'text-green-700 border-green-500 bg-green-50',
    sections: SECTIONS_CONSULTOR,
  },
  gerente: {
    label: 'Gerente',
    subtitle: 'DAIANE',
    color: 'text-blue-700 border-blue-500 bg-blue-50',
    sections: SECTIONS_GERENTE,
  },
  admin: {
    label: 'Admin',
    subtitle: 'LEANDRO',
    color: 'text-purple-700 border-purple-500 bg-purple-50',
    sections: SECTIONS_ADMIN,
  },
};

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function DocsPage() {
  const [activeRole, setActiveRole] = useState<Role>('consultor');
  const cfg = ROLE_CONFIG[activeRole];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1">
          <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
          </svg>
          <h1 className="text-xl font-bold text-gray-900">Manual do CRM VITAO360</h1>
        </div>
        <p className="text-sm text-gray-500">
          Guia completo por perfil de usuario. Selecione seu role para ver as instrucoes relevantes.
        </p>
      </div>

      {/* Role tabs */}
      <div className="flex gap-2 mb-6">
        {(Object.entries(ROLE_CONFIG) as [Role, typeof ROLE_CONFIG[Role]][]).map(([role, c]) => (
          <button
            key={role}
            type="button"
            onClick={() => setActiveRole(role)}
            className={`flex-1 sm:flex-none min-h-[44px] px-4 py-3 rounded-xl border-2 text-left transition-all
              ${activeRole === role
                ? `${c.color} border-current`
                : 'bg-white border-gray-200 text-gray-600 hover:border-gray-300 hover:bg-gray-50'
              }`}
          >
            <div className="text-sm font-bold">{c.label}</div>
            <div className="text-[10px] opacity-70 mt-0.5">{c.subtitle}</div>
          </button>
        ))}
      </div>

      {/* Sections accordion */}
      <div className="space-y-2">
        {cfg.sections.map((section, idx) => (
          <AccordionItem
            key={`${activeRole}-${section.title}`}
            section={section}
            defaultOpen={idx === 0}
          />
        ))}
      </div>

      {/* Footer */}
      <div className="mt-8 mb-4 p-4 bg-gray-50 rounded-xl border border-gray-200 text-center">
        <p className="text-xs text-gray-500">
          CRM VITAO360 — Manual v1.0 — Atualizado: 13/Abr/2026
        </p>
        <p className="text-xs text-gray-400 mt-1">
          Duvidas? Contate Leandro ou abra um RNC no sistema.
        </p>
      </div>
    </div>
  );
}
