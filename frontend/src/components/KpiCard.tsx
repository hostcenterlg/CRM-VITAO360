'use client';

// ---------------------------------------------------------------------------
// KpiCard — reusable metric card
// ---------------------------------------------------------------------------

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  accentColor?: string; // hex color for left border accent
  loading?: boolean;
}

export default function KpiCard({
  title,
  value,
  subtitle,
  accentColor = '#2563eb',
  loading = false,
}: KpiCardProps) {
  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-4 flex flex-col gap-1 shadow-sm"
      style={{ borderLeftColor: accentColor, borderLeftWidth: '4px' }}
    >
      <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {title}
      </p>
      {loading ? (
        <div className="h-7 w-28 bg-gray-100 animate-pulse rounded" />
      ) : (
        <p className="text-2xl font-bold text-gray-900 leading-tight">{value}</p>
      )}
      {subtitle && (
        <p className="text-xs text-gray-400 mt-0.5">{subtitle}</p>
      )}
    </div>
  );
}
