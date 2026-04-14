// Helper de exportacao CSV client-side — sem dependencias externas
// Gera arquivo UTF-8 BOM para Excel BR abrir corretamente com acentos

export interface ExportColumn<T> {
  /** Cabecalho da coluna no CSV */
  label: string;
  /** Funcao que extrai o valor bruto da linha */
  value: (row: T) => string | number | null | undefined;
  /** Se true, formata como texto ="valor" para evitar conversao pelo Excel */
  forceText?: boolean;
}

/**
 * Exporta um array de dados para CSV e dispara download no navegador.
 *
 * @param data     Linhas de dados tipadas
 * @param columns  Definicoes de colunas (cabecalho + extrator de valor)
 * @param filename Nome do arquivo sem extensao (ex: "carteira_2026-04-13")
 */
export function exportToCSV<T>(
  data: T[],
  columns: ExportColumn<T>[],
  filename: string
): void {
  const cabecalho = columns.map((c) => `"${c.label}"`).join(';');

  const linhas = data.map((row) =>
    columns
      .map((col) => {
        const raw = col.value(row);
        if (raw == null) return '';
        const str = String(raw).replace(/"/g, '""');
        if (col.forceText) {
          // Prefixo ="..." forca Excel a tratar como texto
          return `="${str}"`;
        }
        // Strings com virgula, ponto-e-virgula ou aspas precisam de quoting
        if (typeof raw === 'string' && (str.includes(';') || str.includes('"') || str.includes('\n'))) {
          return `"${str}"`;
        }
        return str;
      })
      .join(';')
  );

  const csvContent = [cabecalho, ...linhas].join('\r\n');

  // UTF-8 BOM garante que Excel BR reconheca acentos
  const BOM = '\uFEFF';
  const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}.csv`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
