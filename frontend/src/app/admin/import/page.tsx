'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
  uploadImport,
  fetchImportHistory,
  ImportResult,
  ImportHistoryItem,
} from '@/lib/api';

// ---------------------------------------------------------------------------
// Import page — Importacao de dados (.xlsx Mercos / SAP)
// Admin only. LIGHT theme. Verde #00B050.
// ---------------------------------------------------------------------------

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatDateBR(iso: string): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return iso;
  }
}

// ---------------------------------------------------------------------------
// Status badge for history table
// ---------------------------------------------------------------------------

function StatusImportBadge({ status }: { status: ImportHistoryItem['status'] }) {
  const cfg: Record<ImportHistoryItem['status'], { bg: string; text: string; label: string }> = {
    SUCESSO: { bg: '#00B050', text: '#fff', label: 'Sucesso' },
    SUCESSO_COM_ERROS: { bg: '#FFC000', text: '#1a1a1a', label: 'Com erros' },
    FALHA: { bg: '#FF0000', text: '#fff', label: 'Falha' },
  };
  const { bg, text, label } = cfg[status] ?? cfg.FALHA;
  return (
    <span
      className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase"
      style={{ backgroundColor: bg, color: text }}
    >
      {label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Result card shown after a successful import call
// ---------------------------------------------------------------------------

function ImportResultCard({
  result,
  onReset,
}: {
  result: ImportResult;
  onReset: () => void;
}) {
  const isOk = result.status === 'SUCESSO';
  const hasErros = result.erros > 0;

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 space-y-5">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
          style={{ backgroundColor: isOk ? '#D1FAE5' : '#FEF3C7' }}
        >
          {isOk ? (
            <svg className="w-5 h-5" style={{ color: '#00B050' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ) : (
            <svg className="w-5 h-5 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          )}
        </div>
        <div>
          <h3 className="text-sm font-bold text-gray-900">
            {isOk ? 'Importacao concluida com sucesso' : 'Importacao concluida com avisos'}
          </h3>
          <p className="text-xs text-gray-500 mt-0.5">Arquivo: {result.arquivo}</p>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {[
          { label: 'Lidos', value: result.registros_lidos, color: '#2563eb' },
          { label: 'Inseridos', value: result.inseridos, color: '#00B050' },
          { label: 'Atualizados', value: result.atualizados, color: '#7c3aed' },
          { label: 'Ignorados', value: result.ignorados, color: '#6b7280' },
          { label: 'Erros', value: result.erros, color: result.erros > 0 ? '#DC2626' : '#6b7280' },
        ].map(({ label, value, color }) => (
          <div
            key={label}
            className="bg-gray-50 rounded-lg p-3 text-center border border-gray-100"
          >
            <p className="text-2xl font-bold" style={{ color }}>{value.toLocaleString('pt-BR')}</p>
            <p className="text-[11px] text-gray-500 mt-0.5 font-medium uppercase tracking-wide">{label}</p>
          </div>
        ))}
      </div>

      {/* Error list */}
      {hasErros && result.detalhes_erros.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 space-y-1">
          <p className="text-xs font-semibold text-red-700 mb-2">Detalhes dos erros:</p>
          <ul className="space-y-1 max-h-40 overflow-y-auto">
            {result.detalhes_erros.map((msg, i) => (
              <li key={i} className="text-xs text-red-600 flex items-start gap-1.5">
                <span className="flex-shrink-0 mt-0.5 text-red-400">
                  <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </span>
                {msg}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Reset button */}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={onReset}
          className="px-4 py-2 text-sm font-semibold text-white rounded-lg transition-opacity hover:opacity-90"
          style={{ backgroundColor: '#00B050' }}
        >
          Importar outro arquivo
        </button>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// DropZone component
// ---------------------------------------------------------------------------

interface DropZoneProps {
  onFile: (file: File) => void;
  disabled: boolean;
}

function DropZone({ onFile, disabled }: DropZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setDragging(false);
      if (disabled) return;
      const file = e.dataTransfer.files[0];
      if (file) {
        if (!file.name.endsWith('.xlsx')) {
          alert('Apenas arquivos .xlsx sao aceitos.');
          return;
        }
        setSelectedFile(file);
      }
    },
    [disabled]
  );

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
    // Reset so same file can be re-selected
    e.target.value = '';
  }, []);

  const handleImport = useCallback(() => {
    if (selectedFile) onFile(selectedFile);
  }, [selectedFile, onFile]);

  return (
    <div className="space-y-4">
      {/* Drop zone */}
      <div
        role="region"
        aria-label="Zona de upload de arquivo"
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => !disabled && inputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-xl p-8 sm:p-12 text-center
          transition-colors cursor-pointer select-none
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          ${dragging ? 'border-green-500 bg-green-50' : 'border-gray-300 bg-gray-50 hover:border-green-400 hover:bg-green-50/30'}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".xlsx"
          className="sr-only"
          onChange={handleChange}
          disabled={disabled}
          aria-label="Selecionar arquivo .xlsx"
        />

        <div className="flex flex-col items-center gap-3">
          <div
            className="w-14 h-14 rounded-full flex items-center justify-center"
            style={{ backgroundColor: dragging ? '#D1FAE5' : '#F3F4F6' }}
          >
            <svg
              className="w-7 h-7"
              style={{ color: dragging ? '#00B050' : '#9CA3AF' }}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
          </div>

          <div>
            <p className="text-sm font-semibold text-gray-700">
              Arraste e solte o arquivo aqui
            </p>
            <p className="text-xs text-gray-500 mt-1">
              ou{' '}
              <span style={{ color: '#00B050' }} className="font-semibold">
                clique para selecionar
              </span>
            </p>
            <p className="text-xs text-gray-400 mt-2">Apenas arquivos .xlsx (Mercos ou SAP)</p>
          </div>
        </div>
      </div>

      {/* Selected file info */}
      {selectedFile && (
        <div className="flex items-center justify-between gap-3 px-4 py-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2 min-w-0">
            <svg className="w-4 h-4 flex-shrink-0" style={{ color: '#00B050' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div className="min-w-0">
              <p className="text-sm font-semibold text-gray-900 truncate">{selectedFile.name}</p>
              <p className="text-xs text-gray-500">{formatBytes(selectedFile.size)}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setSelectedFile(null);
            }}
            className="flex-shrink-0 p-1 rounded hover:bg-green-100 transition-colors"
            aria-label="Remover arquivo selecionado"
          >
            <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}

      {/* Import button */}
      <button
        type="button"
        onClick={handleImport}
        disabled={!selectedFile || disabled}
        className="w-full sm:w-auto px-6 py-2.5 text-sm font-semibold text-white rounded-lg
                   transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500
                   disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 active:scale-[0.99]"
        style={{ backgroundColor: '#00B050' }}
      >
        {disabled ? (
          <span className="flex items-center gap-2">
            <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
            Processando...
          </span>
        ) : (
          <span className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
            </svg>
            Importar
          </span>
        )}
      </button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// History table
// ---------------------------------------------------------------------------

function HistoryTable({ items, loading }: { items: ImportHistoryItem[]; loading: boolean }) {
  if (loading) {
    return (
      <div className="p-4 space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-4 bg-gray-100 animate-pulse rounded" />
        ))}
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="py-10 text-center text-gray-400 text-sm">
        Nenhum import realizado ainda.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-gray-50">
            {['Data', 'Arquivo', 'Lidos', 'Inseridos', 'Atualizados', 'Erros', 'Status'].map((h) => (
              <th
                key={h}
                className="px-4 py-2.5 text-left text-[11px] font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={item.id}
              className="border-t border-gray-50 hover:bg-gray-50 transition-colors"
            >
              <td className="px-4 py-2.5 text-xs text-gray-600 whitespace-nowrap font-mono">
                {formatDateBR(item.data_import)}
              </td>
              <td className="px-4 py-2.5 text-gray-800 max-w-[200px] truncate" title={item.arquivo}>
                {item.arquivo}
              </td>
              <td className="px-4 py-2.5 text-center text-gray-700 font-mono">
                {item.registros_lidos.toLocaleString('pt-BR')}
              </td>
              <td className="px-4 py-2.5 text-center font-mono font-semibold" style={{ color: '#00B050' }}>
                {item.inseridos.toLocaleString('pt-BR')}
              </td>
              <td className="px-4 py-2.5 text-center font-mono text-purple-700">
                {item.atualizados.toLocaleString('pt-BR')}
              </td>
              <td
                className="px-4 py-2.5 text-center font-mono font-semibold"
                style={{ color: item.erros > 0 ? '#DC2626' : '#6B7280' }}
              >
                {item.erros.toLocaleString('pt-BR')}
              </td>
              <td className="px-4 py-2.5 whitespace-nowrap">
                <StatusImportBadge status={item.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function ImportPage() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const [history, setHistory] = useState<ImportHistoryItem[]>([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);

  const loadHistory = useCallback(() => {
    setHistoryLoading(true);
    setHistoryError(null);
    fetchImportHistory()
      .then((h) => setHistory(h.itens ?? []))
      .catch((e: unknown) => {
        const msg = e instanceof Error ? e.message : 'Erro ao carregar historico';
        setHistoryError(msg);
      })
      .finally(() => setHistoryLoading(false));
  }, []);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  const handleFile = useCallback(
    async (file: File) => {
      setUploading(true);
      setUploadError(null);
      setResult(null);
      try {
        const res = await uploadImport(file);
        setResult(res);
        // Refresh history after successful upload
        loadHistory();
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : 'Erro desconhecido ao importar';
        setUploadError(msg);
      } finally {
        setUploading(false);
      }
    },
    [loadHistory]
  );

  const handleReset = useCallback(() => {
    setResult(null);
    setUploadError(null);
  }, []);

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Header */}
      <div className="pb-3 border-b border-gray-200">
        <div className="flex items-center gap-2 mb-1">
          <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Importacao de Dados</h1>
          <span
            className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase"
            style={{ backgroundColor: '#DBEAFE', color: '#1D4ED8' }}
          >
            Apenas Admin
          </span>
        </div>
        <p className="text-sm text-gray-500">
          Carregue arquivos .xlsx exportados do Mercos ou SAP para atualizar a carteira.
        </p>
      </div>

      {/* Admin notice */}
      <div className="flex items-start gap-3 px-4 py-3 bg-amber-50 border border-amber-200 rounded-lg">
        <svg className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p className="text-xs text-amber-800">
          <span className="font-semibold">Apenas Admin.</span> Aceita arquivos .xlsx do Mercos ou SAP.
          Verifique sempre as datas reais do relatorio (linhas 6-7 do arquivo Mercos) — os nomes podem mentir.
        </p>
      </div>

      {/* Upload area or result */}
      <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
        {result ? (
          <ImportResultCard result={result} onReset={handleReset} />
        ) : (
          <div className="space-y-4">
            <h2 className="text-sm font-semibold text-gray-700">Selecionar arquivo</h2>

            {uploadError && (
              <div className="flex items-start gap-2 px-4 py-3 bg-red-50 border border-red-200 rounded-lg">
                <svg className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-red-700">{uploadError}</p>
              </div>
            )}

            <DropZone onFile={handleFile} disabled={uploading} />
          </div>
        )}
      </div>

      {/* History */}
      <section className="bg-white rounded-lg border border-gray-200 shadow-sm">
        <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-700">Historico de Importacoes</h2>
          <button
            type="button"
            onClick={loadHistory}
            className="p-1.5 rounded hover:bg-gray-100 transition-colors text-gray-400 hover:text-gray-600"
            aria-label="Recarregar historico"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>

        {historyError ? (
          <div className="px-4 py-6 text-center">
            <p className="text-sm text-gray-500">{historyError}</p>
            <button
              type="button"
              onClick={loadHistory}
              className="mt-3 text-xs font-semibold hover:underline"
              style={{ color: '#00B050' }}
            >
              Tentar novamente
            </button>
          </div>
        ) : (
          <HistoryTable items={history} loading={historyLoading} />
        )}
      </section>
    </div>
  );
}
