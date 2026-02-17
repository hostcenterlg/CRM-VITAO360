---
phase: 04-log-completo
plan: 03
status: complete
started: 2026-02-17T03:20:00
completed: 2026-02-17T03:45:00
---

## Summary

Synthetic generator SAP-anchored criado e executado com sucesso. 6,156 registros sintéticos gerados a partir de 1,182 vendas SAP reais como âncoras, reconstruindo o funil completo (pré-venda + pós-venda) para 889 vendas que não tinham cobertura no CONTROLE_FUNIL.

## Key Results

- **Gap negativo**: CONTROLE_FUNIL (10,442) + Deskrio (4,471) = 14,913 já excedia target de 11,758
- **Foco em qualidade**: Geração focada em completude do funil (ORCAMENTO obrigatório antes de VENDA)
- **6,156 registros sintéticos** com 200+ templates de notas em 11 categorias
- **Todas as 9 validações PASS**: zero weekends, capacidade OK, VENDA→ORCAMENTO OK, timelines consultores OK
- **Combined total**: 10,442 + 4,471 + 6,156 = 21,069 registros (dedup no Plan 04-04 reduzirá)

## Tasks

| # | Task | Status |
|---|------|--------|
| 1 | Load SAP + templates + capacity tracker | ✓ Complete |
| 2 | Generate journeys A-F for sales + non-sale | ✓ Complete |
| 3 | Validate + save JSON | ✓ Complete |

## Commits

| Hash | Message |
|------|---------|
| 1a948b0 | feat(04-03): synthetic generator SAP-anchored - 6,156 records |

## Key Files

### Created
- `scripts/phase04_log_completo/03_generate_synthetic.py` — Complete synthetic generator
- `data/output/phase04/synthetic_generated.json` — 6,156 synthetic records (4.8 MB)

## Deviations

1. **Gap negativo**: Plan esperava gap positivo de ~3,155. Realidade: gap = -3,155 (existentes já excedem target). Ajustado para focar em qualidade do funil em vez de volume.
2. **1,182 vendas SAP** (não 866): O JSON sap_mercos_merged.json contém 537 clientes com 1,182 sale-months individuais, não 866.
3. **Execução direta**: Agente gsd-executor não conseguiu permissão de Bash; script executado diretamente no contexto principal.

## Validation

| Check | Result |
|-------|--------|
| Zero weekends | ✓ PASS (0) |
| Capacity ≤40/day/consultant | ✓ PASS (0 violations) |
| VENDA has ORCAMENTO | ✓ PASS (0 missing) |
| Helder ≤ Aug/2025 | ✓ PASS (0 after) |
| Julio ≥ Sep/2025 | ✓ PASS (0 before) |
| CNPJ 14 digits | ✓ PASS (0 bad) |
| All SINTETICO | ✓ PASS (0 non-synth) |
| Zero financial | ✓ PASS (0 found) |
| Seed 42 | ✓ Reproducible |

## Self-Check: PASSED
