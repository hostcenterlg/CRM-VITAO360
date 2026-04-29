'use client';

import {
  createContext,
  useContext,
  useEffect,
  useState,
  useMemo,
  useCallback,
  type ReactNode,
} from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { fetchMeusCanais, type Canal } from '@/lib/api';

// ---------------------------------------------------------------------------
// CanalContext — propaga o canal selecionado pelo CanalSelector
//
// - admin: pode escolher "Todos" (canalId = null) ou um canal especifico
// - nao-admin com 1 canal: canal eh fixo (auto-select), sem dropdown
// - nao-admin com N canais: pode trocar entre os permitidos
//
// Persistencia: localStorage (chave 'crm_canal_id') — preserva escolha entre
// reloads. Cookie httpOnly nao foi usado porque o backend ja resolve o filtro
// via JWT + tabela usuario_canal; o canalId aqui eh apenas refinamento
// opcional (admin focando em um canal).
// ---------------------------------------------------------------------------

const STORAGE_KEY = 'crm_canal_id';

interface CanalContextType {
  /** id do canal selecionado; null = "Todos" (apenas admin). */
  canalId: number | null;
  /** Atualiza o canal selecionado (persistido em localStorage). */
  setCanalId: (id: number | null) => void;
  /** Lista de canais que o usuario pode acessar (vinda de GET /api/canais/meus). */
  canaisDisponiveis: Canal[];
  /** True enquanto o fetch inicial nao retornou. */
  carregando: boolean;
  /** Mensagem de erro (caso o fetch falhe). */
  erro: string | null;
}

const CanalContext = createContext<CanalContextType | null>(null);

function lerCanalSalvo(): number | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (raw === null || raw === '' || raw === 'null') return null;
    const parsed = Number(raw);
    return Number.isFinite(parsed) ? parsed : null;
  } catch {
    return null;
  }
}

function gravarCanalSalvo(id: number | null): void {
  if (typeof window === 'undefined') return;
  try {
    if (id === null) {
      window.localStorage.removeItem(STORAGE_KEY);
    } else {
      window.localStorage.setItem(STORAGE_KEY, String(id));
    }
  } catch {
    // silencioso — privacidade ou quota
  }
}

export function CanalProvider({ children }: { children: ReactNode }) {
  const { user, loading: authLoading } = useAuth();

  const [canaisDisponiveis, setCanaisDisponiveis] = useState<Canal[]>([]);
  const [canalId, setCanalIdState] = useState<number | null>(() => lerCanalSalvo());
  const [carregando, setCarregando] = useState<boolean>(true);
  const [erro, setErro] = useState<string | null>(null);

  // Atualiza canal e persiste
  const setCanalId = useCallback((id: number | null) => {
    setCanalIdState(id);
    gravarCanalSalvo(id);
  }, []);

  // Buscar canais disponiveis ao logar (ou ao re-autenticar)
  useEffect(() => {
    let mounted = true;

    if (authLoading) {
      // ainda nao sabemos quem eh o user
      return;
    }

    if (!user) {
      // sem auth: limpa
      setCanaisDisponiveis([]);
      setCarregando(false);
      setErro(null);
      return;
    }

    setCarregando(true);
    setErro(null);

    fetchMeusCanais()
      .then(canais => {
        if (!mounted) return;
        // Defensivo: garante array mesmo se fetchMeusCanais retornar valor inesperado
        const lista = Array.isArray(canais) ? canais : [];
        setCanaisDisponiveis(lista);

        // Reconciliacao do canal selecionado:
        //  - se admin: aceita null (Todos) ou um id valido
        //  - se nao-admin com 1 canal: trava nesse canal
        //  - se canal salvo nao consta na lista: limpa
        const ehAdmin = user.role === 'admin';
        const ids = lista.map(c => c.id);
        const salvo = lerCanalSalvo();

        if (!ehAdmin && lista.length === 1) {
          const unico = lista[0]!.id;
          setCanalIdState(unico);
          gravarCanalSalvo(unico);
        } else if (salvo !== null && !ids.includes(salvo)) {
          setCanalIdState(null);
          gravarCanalSalvo(null);
        } else {
          setCanalIdState(salvo);
        }
      })
      .catch(e => {
        if (!mounted) return;
        setErro(e instanceof Error ? e.message : 'Erro ao carregar canais');
        setCanaisDisponiveis([]);
      })
      .finally(() => {
        if (mounted) setCarregando(false);
      });

    return () => {
      mounted = false;
    };
  }, [user, authLoading]);

  const value = useMemo<CanalContextType>(
    () => ({ canalId, setCanalId, canaisDisponiveis, carregando, erro }),
    [canalId, setCanalId, canaisDisponiveis, carregando, erro],
  );

  return <CanalContext.Provider value={value}>{children}</CanalContext.Provider>;
}

/**
 * Hook publico para consumir o CanalContext.
 *
 * Lanca erro se usado fora do <CanalProvider/>.
 */
export function useCanal(): CanalContextType {
  const ctx = useContext(CanalContext);
  if (!ctx) throw new Error('useCanal deve ser usado dentro de CanalProvider');
  return ctx;
}
