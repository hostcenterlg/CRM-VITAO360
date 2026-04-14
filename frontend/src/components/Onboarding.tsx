'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

// ---------------------------------------------------------------------------
// Onboarding — tour guiado no primeiro login
// Exibe apenas uma vez (localStorage crm_onboarding_done)
// Steps: Boas-vindas → Agenda → IA → Pronto
// ---------------------------------------------------------------------------

const ONBOARDING_KEY = 'crm_onboarding_done';

interface Step {
  title: string;
  description: string;
  highlight?: string; // nav label to visually hint
  icon: React.ReactNode;
  action?: React.ReactNode;
}

const STEPS: Step[] = [
  {
    title: 'Bem-vindo ao CRM VITAO360',
    description:
      'Sistema de inteligencia comercial da VITAO Alimentos. Gerencie sua carteira, agenda de contatos, ' +
      'pipeline de vendas e conversas WhatsApp em um unico lugar.',
    icon: (
      <svg className="w-12 h-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" />
      </svg>
    ),
  },
  {
    title: 'Sua Agenda Diaria',
    description:
      'A Agenda e gerada automaticamente pelo Motor de IA. Ela lista os 40 clientes mais prioritarios ' +
      'para contato hoje, ordenados por urgencia. Comece sempre por ela ao iniciar o dia.',
    highlight: 'Agenda',
    icon: (
      <svg className="w-12 h-12 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
    action: (
      <Link
        href="/agenda"
        className="inline-flex items-center gap-1.5 text-sm text-blue-600 font-medium hover:underline"
      >
        Ir para a Agenda
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </Link>
    ),
  },
  {
    title: 'Central de IA',
    description:
      'Antes de ligar para um cliente, use o agente "Briefing de Visita" na Central de IA. ' +
      'Ele consolida historico de compras, ultima interacao, produtos favoritos e alertas de churn ' +
      'em um texto pronto para leitura rapida.',
    highlight: 'Inteligencia IA',
    icon: (
      <svg className="w-12 h-12 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    action: (
      <Link
        href="/ia"
        className="inline-flex items-center gap-1.5 text-sm text-purple-600 font-medium hover:underline"
      >
        Explorar Central de IA
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </Link>
    ),
  },
  {
    title: 'Tudo pronto!',
    description:
      'Voce ja pode comecar a usar o CRM VITAO360. Se tiver duvidas, acesse o Manual no menu ' +
      'lateral (icone de livro). Boas vendas!',
    icon: (
      <svg className="w-12 h-12 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
          d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z" />
      </svg>
    ),
  },
];

// ---------------------------------------------------------------------------
// Step indicator dots
// ---------------------------------------------------------------------------

function StepDots({ total, current }: { total: number; current: number }) {
  return (
    <div className="flex items-center gap-1.5">
      {Array.from({ length: total }).map((_, i) => (
        <span
          key={i}
          className={`rounded-full transition-all duration-200 ${
            i === current
              ? 'w-5 h-2 bg-green-500'
              : i < current
              ? 'w-2 h-2 bg-green-300'
              : 'w-2 h-2 bg-gray-200'
          }`}
        />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

export default function Onboarding() {
  const [visible, setVisible] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    try {
      const done = localStorage.getItem(ONBOARDING_KEY);
      if (!done) {
        // Small delay so the page renders first
        const timer = setTimeout(() => setVisible(true), 600);
        return () => clearTimeout(timer);
      }
    } catch {
      // localStorage unavailable — skip onboarding silently
    }
  }, []);

  function handleDismiss() {
    try {
      localStorage.setItem(ONBOARDING_KEY, 'true');
    } catch {
      // ignore
    }
    setVisible(false);
  }

  function handleNext() {
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      handleDismiss();
    }
  }

  function handlePrev() {
    if (step > 0) setStep((s) => s - 1);
  }

  if (!visible) return null;

  const current = STEPS[step];
  const isLast = step === STEPS.length - 1;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
        onClick={handleDismiss}
        aria-modal="true"
        role="dialog"
        aria-label="Tour de boas-vindas"
      >
        {/* Card — stop click propagation so overlay click doesn't close when clicking card */}
        <div
          className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Progress bar */}
          <div className="h-1 bg-gray-100">
            <div
              className="h-full bg-green-500 transition-all duration-300"
              style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
            />
          </div>

          {/* Content */}
          <div className="px-6 pt-6 pb-4 text-center">
            {/* Icon */}
            <div className="flex justify-center mb-4">
              {current.icon}
            </div>

            {/* Title */}
            <h2 className="text-lg font-bold text-gray-900 mb-2">{current.title}</h2>

            {/* Description */}
            <p className="text-sm text-gray-600 leading-relaxed mb-4">{current.description}</p>

            {/* Highlight hint */}
            {current.highlight && (
              <div className="inline-flex items-center gap-2 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-xs text-gray-700 mb-4">
                <svg className="w-3.5 h-3.5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14" />
                </svg>
                Encontre no menu lateral:
                <span className="font-semibold text-gray-900">{current.highlight}</span>
              </div>
            )}

            {/* Optional action link */}
            {current.action && (
              <div className="mb-4">{current.action}</div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between px-6 py-4 bg-gray-50 border-t border-gray-100">
            {/* Step dots */}
            <StepDots total={STEPS.length} current={step} />

            {/* Navigation */}
            <div className="flex items-center gap-2">
              {/* Pular — always show unless last step */}
              {!isLast && (
                <button
                  type="button"
                  onClick={handleDismiss}
                  className="text-xs text-gray-400 hover:text-gray-600 transition-colors px-2 py-1.5"
                >
                  Pular
                </button>
              )}

              {/* Anterior */}
              {step > 0 && (
                <button
                  type="button"
                  onClick={handlePrev}
                  className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-200
                             rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Anterior
                </button>
              )}

              {/* Proximo / Entrar */}
              <button
                type="button"
                onClick={handleNext}
                className="px-4 py-1.5 text-sm font-semibold text-white rounded-lg transition-colors"
                style={{ backgroundColor: '#00B050' }}
              >
                {isLast ? 'Entrar no CRM' : step === 0 ? 'Comecar' : 'Proximo'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
