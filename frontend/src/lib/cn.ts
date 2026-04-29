// frontend/src/lib/cn.ts
// Minimal class merger — no external deps, no tailwind-merge
// Usage: cn(BASE, VARIANT_CLASSES[v], SIZE_CLASSES[s], className)

export type ClassValue = string | number | null | false | undefined | ClassValue[];

export function cn(...args: ClassValue[]): string {
  const out: string[] = [];
  for (const a of args) {
    if (!a) continue;
    if (Array.isArray(a)) {
      const inner = cn(...a);
      if (inner) out.push(inner);
    } else {
      out.push(String(a));
    }
  }
  return out.join(' ');
}
