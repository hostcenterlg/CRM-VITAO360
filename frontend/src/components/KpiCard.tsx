'use client';

// ---------------------------------------------------------------------------
// KpiCard — reusable metric card with optional SVG icon
// ---------------------------------------------------------------------------

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  accentColor?: string; // hex color for left border accent
  loading?: boolean;
  icon?: React.ReactNode; // SVG icon element
}

export default function KpiCard({
  title,
  value,
  subtitle,
  accentColor = '#2563eb',
  loading = false,
  icon,
}: KpiCardProps) {
  return (
    <div
      className="bg-white rounded-lg border border-gray-200 p-4 flex flex-col gap-1 shadow-sm"
      style={{ borderLeftColor: accentColor, borderLeftWidth: '4px' }}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
          {title}
        </p>
        {icon && (
          <span
            className="flex-shrink-0 w-7 h-7 rounded flex items-center justify-center"
            style={{ backgroundColor: accentColor + '18', color: accentColor }}
            aria-hidden="true"
          >
            {icon}
          </span>
        )}
      </div>
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
