---
name: data-pipeline
description: "Skill do @data-engineer — Import xlsx, normalização CNPJ, cruzamento Mercos/SAP/Deskrio, DE-PARA vendedores, classificação 3-tier."
allowed-tools: Read Write Edit Glob Grep Bash(python:*) Bash(pip:*) Bash(git:add) Bash(git:commit) Bash(ls:*) Bash(mkdir:*)
argument-hint: [*import|*cnpj|*mercos|*sap|*deskrio|*depara|*cruzar|*validate]
---

# @data-engineer — Pipeline de Dados CRM VITAO360

## Quick Commands

| Comando | Ação |
|---------|------|
| `*import` | Importar planilha FINAL (40 abas) → DataFrames |
| `*cnpj` | Normalizar e validar CNPJs na base |
| `*mercos` | Processar relatórios Mercos (CUIDADO: nomes mentem) |
| `*sap` | Processar dados SAP (cadastro, vendas, metas) |
| `*deskrio` | Extrair dados via API Deskrio (15.468 contatos) |
| `*depara` | Aplicar DE-PARA vendedores |
| `*cruzar` | Cruzar fontes por CNPJ (cascata 5 níveis) |
| `*validate` | Validar integridade de dados importados |

## CNPJ — Chave Primária Universal

```python
import re

def normalizar_cnpj(val):
    """14 dígitos, string, zero-padded. NUNCA float."""
    if val is None or str(val).strip() == "":
        return None
    return re.sub(r'\D', '', str(val)).zfill(14)
```

**Regras:**
- SEMPRE string, NUNCA float/int
- 14 dígitos com zero-pad à esquerda
- Todo cruzamento entre sistemas usa CNPJ normalizado
- 0 duplicatas permitidas na base final

## DE-PARA Vendedores

```python
DE_PARA = {
    "MANU": ["Manu", "Manu Vitao", "Manu Ditzel", "HEMANUELE DITZEL (MANU)", "HEMANUELE"],
    "LARISSA": ["Larissa", "Lari", "Larissa Vitao", "Mais Granel", "Rodrigo"],
    "DAIANE": ["Daiane", "Central Daiane", "Daiane Vitao", "CENTRAL - DAIANE"],
    "JULIO": ["Julio", "Julio Gadret"],
    "LEGADO": ["Bruno Gretter", "Jeferson Vitao", "Patric", "Gabriel", "Sergio", "Ive", "Ana", "Lorrany", "Leandro"],
}

def normalizar_vendedor(nome):
    if not nome: return None
    nome_upper = str(nome).strip().upper()
    for canonical, aliases in DE_PARA.items():
        for alias in aliases:
            if alias.upper() in nome_upper or nome_upper in alias.upper():
                return canonical
    return "LEGADO"
```

## Motor de Matching (Cascata 5 Níveis)

1. **CNPJ exato** (100% confiança)
2. **Prefixo CNPJ** (primeiros 8 dígitos)
3. **Nome exato normalizado** (upper, strip, sem acentos)
4. **Nome parcial** (contains)
5. **Nome parcial normalizado** (rapidfuzz, threshold 70%)

**Fontes de lookup:** Mercos Carteira (497) + DRAFT 1 (502) + SAP Cadastro (1.698) = 3.699 entradas

## Classificação 3-Tier (OBRIGATÓRIA)

| Tier | Significado | Pode usar? |
|------|-------------|------------|
| REAL | Rastreável a Mercos, SAP, Deskrio | SIM |
| SINTÉTICO | Derivado de dados REAL por fórmula/cálculo | SIM (com flag) |
| ALUCINAÇÃO | ChatGPT fabricou, sem fonte, CONTROLE_FUNIL rejeitado | **NUNCA** |

- 558 registros catalogados como ALUCINAÇÃO — EXCLUIR automaticamente
- Dados sem classificação = SUSPEITOS

## Fontes de Dados

| Sistema | Tipo | Dados | Prioridade |
|---------|------|-------|------------|
| SAP | ERP corporativo | Vendas mensais, metas 2026, cadastro | **PRIMÁRIO** |
| Mercos | Plataforma vendas | Carteira, vendas, ABC, ecommerce | COMPLEMENTO |
| Deskrio | Chat WhatsApp | 15.468 contatos, API aberta, CNPJ campo extra | COMPLEMENTO |
| Sales Hunter | Prospecção | Pedidos manuais | COMPLEMENTO |

## Armadilhas Mercos (11 documentadas)

- Header na LINHA 10 (skiprows=9)
- NÃO TEM CNPJ — match por Nome Fantasia
- "Abril" = Abr+Mai (filtrar month==4)
- "Set25" = Outubro (DESCARTAR)
- "Nov" = Setembro (DESCARTAR)
- Maio duplicata exata (DESCARTAR)
- Janeiro: usar RELATORIO (78 rows), não relatorio (35 rows)
- 27 valores negativos SAP = notas de crédito (zerar)

## Deskrio API

- Token: `.env` (DESKRIO_API_TOKEN)
- Base: `https://appapi.deskrio.com.br`
- 26 endpoints: contatos, tickets, mensagens, kanban, extrainfo
- Conexões ativas: "Mais Granel" + "Central Vitao"
- Campo CNPJ disponível como extrainfo
- Spec completa: `.cache/deskrio_api_spec.json`

## Thresholds

| Métrica | Mínimo | Bloqueante |
|---------|--------|------------|
| CNPJ como float | 0 | > 0 |
| CNPJ duplicatas | 0 | > 0 |
| Coverage clientes | >90% | < 80% |
| Coverage faturamento | >95% | < 90% |
| ALUCINAÇÃO integrados | 0 | > 0 |
| DE-PARA não mapeado | <5% | > 10% |
| Faturamento vs R$2.091M | ±0.5% | > 0.5% |
