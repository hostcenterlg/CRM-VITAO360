// frontend/src/components/ui/index.ts
// Barrel export — UI components + typography system
// Usage: import { Badge, StatusPill, Heading, Text, Label, ... } from '@/components/ui';

// Typography system (Wave 1 — design tokens)
export * from './typography';

// Display primitives
export { Badge } from './Badge';
export type { BadgeProps, BadgeVariant, BadgeSize } from './Badge';

// Status pills (semantic wrappers)
export { StatusPill } from './StatusPill';
export type { StatusPillProps, CrmStatus } from './StatusPill';

export { CurvaPill } from './CurvaPill';
export type { CurvaPillProps, Curva } from './CurvaPill';

export { PriorityPill } from './PriorityPill';
export type { PriorityPillProps, Prioridade } from './PriorityPill';

// Bars
export { ScoreBar } from './ScoreBar';
export type { ScoreBarProps } from './ScoreBar';

export { ProgressBar } from './ProgressBar';
export type { ProgressBarProps } from './ProgressBar';

// Navigation / interactive
export { Tabs } from './Tabs';
export type { TabsProps, TabItem } from './Tabs';

export { FilterGroup } from './FilterGroup';
export type {
  FilterGroupProps,
  FilterField,
  FilterFieldType,
  FilterState,
  SearchField,
  SelectField,
  PillToggleField,
  DateRangeField,
  NumberRangeField,
} from './FilterGroup';

export { SearchInput } from './SearchInput';
export type { SearchInputProps } from './SearchInput';

// Side widgets
export { MetaWidget } from './MetaWidget';
export type { MetaWidgetProps } from './MetaWidget';

// Density elements
export { Sinaleiro } from './Sinaleiro';
export type { SinaleiroProps, SinaleiroCor } from './Sinaleiro';
